"""
This file is part of Giswater 3
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
from PyQt4.QtGui import QCheckBox, QRadioButton, QAction, QWidget, QComboBox, QLineEdit,QPushButton, QTableView, QAbstractItemView, QTextEdit, QProgressDialog, QProgressBar, QApplication
from PyQt4.QtCore import QSettings, Qt

import os
import sys
import re
from functools import partial

import utils_giswater
from giswater.actions.parent import ParentAction
from giswater.ui_manager import Readsql, InfoShowInfo, ReadsqlCreateProject, ReadsqlRename, ReadsqlShowInfo


class UpdateSQL(ParentAction):

    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class to control toolbar 'om_ws' """
        
        # Initialize instance attributes
        ParentAction.__init__(self, iface, settings, controller, plugin_dir)
        self.giswater_version = "3.1"
        self.iface = iface
        self.settings = settings
        self.controller = controller
        self.plugin_dir = plugin_dir
        self.schema_name = self.controller.schema_name
        self.project_type = controller.get_project_type()

        
    def init_sql(self):
        """ Button 100: Execute SQL. Info show info """
        
        # Get last database connection from controller
        self.last_connection = self.get_last_connection()

        if self.project_type is not None:
            self.info_show_info()
            return
            
        # Create the dialog and signals
        self.dlg_readsql = Readsql()
        self.load_settings(self.dlg_readsql)
        self.dlg_readsql.btn_close.clicked.connect(partial(self.close_dialog, self.dlg_readsql))

        # Check if user have dev permisions
        self.dev_user = self.settings.value('system_variables/devoloper_mode').upper()
        self.read_all_updates = self.settings.value('system_variables/read_all_updates').upper()

        # Get plugin version
        self.plugin_version = self.get_plugin_version()
        self.project_data_schema_version = '0'

        # Get widgets from form
        self.cmb_connection = self.dlg_readsql.findChild(QComboBox, 'cmb_connection')
        self.btn_update_schema = self.dlg_readsql.findChild(QPushButton, 'btn_update_schema')
        self.btn_update_api = self.dlg_readsql.findChild(QPushButton, 'btn_update_api')

        # Checkbox SCHEMA & API
        self.chk_schema_view = self.dlg_readsql.findChild(QCheckBox, 'chk_schema_view')
        self.chk_schema_fk = self.dlg_readsql.findChild(QCheckBox, 'chk_schema_fk')
        self.chk_schema_funcion = self.dlg_readsql.findChild(QCheckBox, 'chk_schema_funcion')
        self.chk_schema_trigger = self.dlg_readsql.findChild(QCheckBox, 'chk_schema_trigger')
        self.chk_api_view = self.dlg_readsql.findChild(QCheckBox, 'chk_api_view')
        self.chk_api_fk = self.dlg_readsql.findChild(QCheckBox, 'chk_api_fk')
        self.chk_api_funcion = self.dlg_readsql.findChild(QCheckBox, 'chk_api_funcion')
        self.chk_api_trigger = self.dlg_readsql.findChild(QCheckBox, 'chk_api_trigger')
        self.software_version_info = self.dlg_readsql.findChild(QTextEdit, 'software_version_info')

        btn_info = self.dlg_readsql.findChild(QPushButton, 'btn_info')
        self.set_icon(btn_info, '73')

        self.message_update = ''

        #Declare error counter variable
        self.error_count = 0

        # Get locale of QGIS application
        self.locale = QSettings().value('locale/userLocale').lower()
        if self.locale == 'es_es':
            self.locale = 'ES'
        elif self.locale == 'es_ca':
            self.locale = 'CA'
        elif self.locale == 'en_us':
            self.locale = 'EN'

        self.filter_srid_value = self.controller.plugin_settings_value('srid')
        self.schema = None

        # Get metadata version
        self.version_metadata = self.get_plugin_version()

        # Get version if not new project
        self.version = None
        if self.controller.schema_name is not None:
            sql = ("SELECT giswater from " + self.controller.schema_name + ".version")
            row = self.controller.get_row(sql)
            self.version = row[0]
            if self.version.replace('.','') >= self.plugin_version.replace('.',''):
                self.btn_update_schema.setEnabled(False)
                self.btn_update_api.setEnabled(False)
        if self.dev_user != 'TRUE':
            utils_giswater.remove_tab_by_tabName(self.dlg_readsql.tab_main, "schema_manager")
            utils_giswater.remove_tab_by_tabName(self.dlg_readsql.tab_main, "api_manager")
            utils_giswater.remove_tab_by_tabName(self.dlg_readsql.tab_main, "custom")
            self.project_types = self.settings.value('system_variables/project_types')
        else:
            self.project_types = self.settings.value('system_variables/project_types_dev')

        # Declare sql directory
        self.sql_dir = os.path.normpath(os.path.normpath(os.path.dirname(os.path.abspath(__file__)) + os.sep + os.pardir)) + '\sql'
        if not os.path.exists(self.sql_dir):
            self.controller.show_message("The sql folder was not found in the Giwsater repository.", 1)
            return        

        # Populate combo types
        self.cmb_project_type = self.dlg_readsql.findChild(QComboBox, 'cmb_project_type')
        for type in self.project_types:
            self.cmb_project_type.addItem(str(type))
        self.change_project_type(self.cmb_project_type)

        self.populate_data_schema_name(self.cmb_project_type)
        self.set_info_project()

        # Declare all file variables
        self.file_pattern_tablect = "tablect"
        self.file_pattern_ddl = "ddl"
        self.file_pattern_dml = "dml"
        self.file_pattern_fct = "fct"
        self.file_pattern_trg = "trg"
        self.file_pattern_ftrg = "ftrg"
        self.file_pattern_ddlview = "ddlview"
        self.file_pattern_ddlrule = "ddlrule"

        # Declare all directorys
        if self.schema_name is not None and self.project_type is not None:
            self.folderSoftware = self.sql_dir + os.sep + self.project_type + os.sep
        self.folderLocale = self.sql_dir + os.sep + 'i18n' + os.sep + str(self.locale) + os.sep
        self.folderUtils = self.sql_dir + os.sep + 'utils' + os.sep
        self.folderUpdates = self.sql_dir + os.sep + 'updates' + os.sep
        self.folderExemple = self.sql_dir + os.sep + 'example' + os.sep
        self.folderPath = ''

        # Declare all directorys api
        self.folderUpdatesApi = self.sql_dir + os.sep + 'api' + os.sep + 'updates' + os.sep
        self.folderApi = self.sql_dir + os.sep + 'api' + os.sep

        # Populate combo connections
        s = QSettings()
        s.beginGroup("PostgreSQL/connections")
        connections = s.childGroups()
        list_connections = []
        for con in connections:
            elem = [con, con]
            list_connections.append(elem)

        s.endGroup()
        utils_giswater.set_item_data(self.cmb_connection, list_connections, 1)

        # Set Listeners
        self.dlg_readsql.btn_schema_create.clicked.connect(partial(self.open_create_project))
        self.dlg_readsql.btn_api_create.clicked.connect(partial(self.implement_api))

        #TODO:: QGIS project file (hidden)
        # self.dlg_readsql.btn_qgis_project_create.clicked.connect(partial(self.load_custom_sql_files, self.dlg_readsql, "path_folder"))

        self.dlg_readsql.btn_custom_load_file.clicked.connect(partial(self.load_custom_sql_files, self.dlg_readsql, "custom_path_folder"))
        self.dlg_readsql.btn_update_schema.clicked.connect(partial(self.load_updates, self.project_type_selected))
        self.dlg_readsql.btn_update_api.clicked.connect(partial(self.update_api))
        self.dlg_readsql.btn_schema_file_to_db.clicked.connect(partial(self.schema_file_to_db))
        self.dlg_readsql.btn_api_file_to_db.clicked.connect(partial(self.api_file_to_db))
        btn_info.clicked.connect(partial(self.show_info))
        self.dlg_readsql.project_schema_name.currentIndexChanged.connect(partial(self.set_info_project))
        self.cmb_project_type.currentIndexChanged.connect(partial(self.populate_data_schema_name, self.cmb_project_type))
        self.cmb_project_type.currentIndexChanged.connect(partial(self.change_project_type, self.cmb_project_type))
        self.cmb_project_type.currentIndexChanged.connect(partial(self.set_info_project))
        self.dlg_readsql.btn_custom_select_file.clicked.connect(partial(self.get_folder_dialog, self.dlg_readsql, "custom_path_folder"))
        self.cmb_connection.currentIndexChanged.connect(partial(self.event_change_connection))
        self.cmb_connection.currentIndexChanged.connect(partial(self.set_info_project))

        # Put current info into software version info widget
        if self.version is None:
            self.version = '0'
            self.software_version_info.setText('Plugin version: ' + self.plugin_version + '\n' +
                                               'Database version: ' + self.version + '\n \n' +
                                               'Project data schema version:' + self.project_data_schema_version)

        # Set last connection for default
        utils_giswater.set_combo_itemData(self.cmb_connection, str(self.last_connection), 1)

        # Open dialog
        self.dlg_readsql.show()

            
    """ Declare all read sql process """

    def load_base(self, project_type=False):

        status = True
        if str(project_type) == 'ws' or str(project_type) == 'ud':
            if self.process_folder(self.folderUtils, self.file_pattern_ddl + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_ddl), self.folderUtils + self.file_pattern_ddl)
                if status is False:
                    return False
            if self.process_folder(self.folderUtils, self.file_pattern_dml + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_dml), self.folderUtils + self.file_pattern_dml)
                if status is False:
                    return False
            if self.process_folder(self.folderUtils, self.file_pattern_fct + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_fct), self.folderUtils + self.file_pattern_fct)
                if status is False:
                    return False
            if self.process_folder(self.folderUtils, self.file_pattern_ftrg + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_ftrg), self.folderUtils + self.file_pattern_ftrg)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_ddl + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_ddl), self.folderSoftware + self.file_pattern_ddl)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_ddlrule + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_ddlrule), self.folderSoftware + self.file_pattern_ddlrule)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_dml + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_dml), self.folderSoftware + self.file_pattern_dml)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_tablect + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_tablect), self.folderSoftware + self.file_pattern_tablect)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_fct + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_fct), self.folderSoftware + self.file_pattern_fct)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_ftrg + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_ftrg), self.folderSoftware + self.file_pattern_ftrg)
                if status is False:
                    return False
            if self.process_folder(self.folderUtils, self.file_pattern_tablect + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_tablect), self.folderUtils + self.file_pattern_tablect)
                if status is False:
                    return False
            if self.process_folder(self.folderUtils, self.file_pattern_ddlrule + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_ddlrule), self.folderUtils + self.file_pattern_ddlrule)
                if status is False:
                    return False

            if self.process_folder(self.folderLocale, '') is False:
                if self.process_folder(self.sql_dir + os.sep + 'i18n' + os.sep, 'EN') is False:
                    status = False
                else:
                    status = self.executeFiles(os.listdir(self.sql_dir + os.sep + 'i18n' + os.sep + 'EN'),
                                               self.sql_dir + os.sep + 'i18n' + os.sep + 'EN', True)
                    if status is False:
                        status = False
            else:
                status = self.executeFiles(os.listdir(self.folderLocale), self.folderLocale, True)
                if status is False:
                    status = False
                    
        else:
            if self.process_folder(str(project_type) + os.sep, self.file_pattern_ddl + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(str(project_type) + os.sep + self.file_pattern_ddl), str(project_type) + os.sep + self.file_pattern_ddl)
                if status is False:
                    return False
            if self.process_folder(str(project_type) + os.sep, self.file_pattern_ddlrule + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(str(project_type) + os.sep + self.file_pattern_ddlrule), str(project_type) + os.sep + self.file_pattern_ddlrule)
                if status is False:
                    return False
            if self.process_folder(str(project_type) + os.sep, self.file_pattern_dml + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(str(project_type) + os.sep + self.file_pattern_dml), str(project_type) + os.sep + self.file_pattern_dml)
                if status is False:
                    return False
            if self.process_folder(str(project_type) + os.sep, self.file_pattern_fct + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(str(project_type) + os.sep + self.file_pattern_fct), str(project_type) + os.sep + self.file_pattern_fct)
                if status is False:
                    return False
            if self.process_folder(str(project_type) + os.sep, self.file_pattern_ftrg + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(str(project_type) + os.sep + self.file_pattern_ftrg), str(project_type) + os.sep + self.file_pattern_ftrg)
                if status is False:
                    return False
            if self.process_folder(str(project_type) + os.sep, self.file_pattern_tablect + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(str(project_type) + os.sep + self.file_pattern_tablect), str(project_type) + os.sep + self.file_pattern_tablect)
                if status is False:
                    return False
            if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + utils_giswater.getWidgetText(self.dlg_readsql, self.cmb_locale) + os.sep, '') is False:
                if self.process_folder(self.sql_dir + os.sep + 'i18n' + os.sep, 'EN') is False:
                    return False
                else:
                    status = self.executeFiles(os.listdir(
                        self.sql_dir + os.sep + str(project_type) + os.sep + 'i18n' + os.sep + 'EN'), self.sql_dir + os.sep + str(project_type) + os.sep + 'i18n' + os.sep + 'EN', True)
                    if status is False:
                        return False
            else:
                status = self.executeFiles(os.listdir(self.sql_dir + os.sep + str(project_type) + os.sep + utils_giswater.getWidgetText(self.dlg_readsql, self.cmb_locale) + os.sep), self.sql_dir + os.sep + str(project_type) + os.sep + utils_giswater.getWidgetText(self.dlg_readsql, self.cmb_locale) + os.sep, True)
                if status is False:
                    return False

        return True
        

    def load_base_no_ct(self, project_type):

        status = True
        if str(project_type) == 'ws' or str(project_type) == 'ud':
            if self.process_folder(self.folderUtils, self.file_pattern_ddl + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_ddl), self.folderUtils + self.file_pattern_ddl)
                if status is False:
                    return False
            if self.process_folder(self.folderUtils, self.file_pattern_dml + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_dml), self.folderUtils + self.file_pattern_dml)
                if status is False:
                    return False
            if self.process_folder(self.folderUtils, self.file_pattern_fct + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_fct), self.folderUtils + self.file_pattern_fct)
                if status is False:
                    return False
            if self.process_folder(self.folderUtils, self.file_pattern_ftrg + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_ftrg), self.folderUtils + self.file_pattern_ftrg)
                if status is False:
                    return False					
            if self.process_folder(self.folderSoftware, self.file_pattern_ddl + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_ddl), self.folderSoftware + self.file_pattern_ddl)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_ddlrule + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_ddlrule), self.folderSoftware + self.file_pattern_ddlrule)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_dml + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_dml), self.folderSoftware + self.file_pattern_dml)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_fct + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_fct), self.folderSoftware + self.file_pattern_fct)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_ftrg + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_ftrg), self.folderSoftware + self.file_pattern_ftrg)
                if status is False:
                    return False
            if self.process_folder(self.folderUtils, self.file_pattern_ddlrule + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_ddlrule), self.folderUtils + self.file_pattern_ddlrule)
                if status is False:
                    return False
            if self.process_folder(self.folderLocale, '') is False:
                if self.process_folder(self.sql_dir + os.sep + 'i18n' + os.sep, 'EN') is False:
                    return False
                else:
                    status = self.executeFiles(os.listdir(
                        self.sql_dir + os.sep + 'i18n' + os.sep + 'EN'), self.sql_dir + os.sep + 'i18n' + os.sep + 'EN', True)
                    if status is False:
                        return False
            else:
                status = self.executeFiles(os.listdir(self.folderLocale), self.folderLocale, True)
                if status is False:
                    return False
                    
        else:
            if self.process_folder(str(project_type) + os.sep, self.file_pattern_ddl + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(str(project_type) + os.sep + self.file_pattern_ddl), str(project_type) + os.sep + self.file_pattern_ddl)
                if status is False:
                    return False
            if self.process_folder(str(project_type) + os.sep, self.file_pattern_ddlrule + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(str(project_type) + os.sep + self.file_pattern_ddlrule), str(project_type) + os.sep + self.file_pattern_ddlrule)
                if status is False:
                    return False
            if self.process_folder(str(project_type) + os.sep, self.file_pattern_dml + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(str(project_type) + os.sep + self.file_pattern_dml), str(project_type) + os.sep + self.file_pattern_dml)
                if status is False:
                    return False
            if self.process_folder(str(project_type) + os.sep, self.file_pattern_fct + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(str(project_type) + os.sep + self.file_pattern_fct), str(project_type) + os.sep + self.file_pattern_fct)
                if status is False:
                    return False
            if self.process_folder(str(project_type) + os.sep, self.file_pattern_ftrg + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(str(project_type) + os.sep + self.file_pattern_ftrg), str(project_type) + os.sep + self.file_pattern_ftrg)
                if status is False:
                    return False
            if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + utils_giswater.getWidgetText(self.dlg_readsql, self.cmb_locale) + os.sep, '') is False:
                if self.process_folder(self.sql_dir + os.sep + 'i18n' + os.sep, 'EN') is False:
                    return False
                else:
                    status = self.executeFiles(os.listdir(
                        self.sql_dir + os.sep + str(project_type) + os.sep + 'i18n' + os.sep + 'EN'), self.sql_dir + os.sep + str(project_type) + os.sep + 'i18n' + os.sep + 'EN', True)
                    if status is False:
                        return False
            else:
                status = self.executeFiles(os.listdir(self.sql_dir + os.sep + str(project_type) + os.sep + utils_giswater.getWidgetText(self.dlg_readsql, self.cmb_locale) + os.sep), self.sql_dir + os.sep + str(project_type) + os.sep + utils_giswater.getWidgetText(self.dlg_readsql, self.cmb_locale) + os.sep, True)
                if status is False:
                    return False

        return True

        
    def update_31to39(self, new_project=False, project_type=False, no_ct=False):

        status = True

        if str(project_type) == 'ws' or str(project_type) == 'ud':
            if not os.path.exists(self.folderUpdates):
                self.controller.show_message("The update folder was not found in sql folder.", 1)
                self.error_count = self.error_count + 1
                return
            folders = os.listdir(self.folderUpdates + '')
            for folder in folders:
                sub_folders = os.listdir(self.folderUpdates + folder)
                for sub_folder in sub_folders:
                    if new_project:
                        if self.read_all_updates == 'TRUE':
                            if str(sub_folder) > '31100':
                                if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder, os.sep + 'utils' + os.sep) is False:
                                    status=False
                                else:
                                    status = self.load_sql(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep)
                                    if status is False:
                                        status=False
                                if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder + os.sep + project_type + os.sep,'') is False:
                                    status=False
                                else:
                                    status = self.load_sql(self.folderUpdates + folder + os.sep + sub_folder + os.sep + project_type + os.sep)
                                    if status is False:
                                        status=False
                                if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep), '') is False:
                                    if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep, 'EN') is False:
                                        status=False
                                    else:
                                        status = self.executeFiles(os.listdir(
                                            self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN'),
                                            self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN' + os.sep, True)
                                        if status is False:
                                            status=False
                                else:
                                    status = self.executeFiles(os.listdir(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep)), self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep))
                                    if status is False:
                                        status=False

                        else:
                            if str(sub_folder) > '31100' and str(sub_folder) <= str(self.version_metadata).replace('.', ''):
                                if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder,
                                                       os.sep + 'utils' + os.sep) is False:
                                    status=False
                                else:
                                    status = self.load_sql(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep, no_ct=no_ct)
                                    if status is False:
                                        status=False
                                if self.process_folder(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + project_type + os.sep,
                                        '') is False:
                                    status=False
                                else:
                                    status = self.load_sql(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + project_type + os.sep, no_ct=no_ct)
                                    if status is False:
                                        status=False
                                if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep), '') is False:
                                    if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep, 'EN') is False:
                                        status=False
                                    else:
                                        status = self.executeFiles(os.listdir(
                                            self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN'),
                                            self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN', True)
                                        if status is False:
                                            status=False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                            self.locale + os.sep)),
                                            self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                            self.locale + os.sep), True)
                                    if status is False:
                                        status=False
                    else:
                        if self.read_all_updates == 'TRUE':
                            if str(sub_folder) > str(self.project_data_schema_version).replace('.', '') and str(sub_folder) > '31100':
                                if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder, os.sep + 'utils' + os.sep) is False:
                                    status=False
                                else:
                                    status = self.load_sql(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep)
                                    if status is False:
                                        status=False
                                if self.process_folder(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + self.project_type_selected + os.sep,
                                        '') is False:
                                    status=False
                                else:
                                    status = self.load_sql(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + self.project_type_selected + os.sep)
                                    if status is False:
                                        status=False
                                if self.process_folder(
                                        self.sql_dir + os.sep + str(
                                            project_type) + os.sep + 'updates' + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                            self.locale + os.sep),
                                        '') is False:
                                    if self.process_folder(self.sql_dir + os.sep + str(
                                            project_type) + os.sep + 'updates' + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep,
                                                           'EN') is False:
                                        status = False
                                    else:
                                        status = self.executeFiles(os.listdir(
                                            self.sql_dir + os.sep + str(
                                                project_type) + os.sep + 'updates' + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN'),
                                            self.sql_dir + os.sep + str(
                                                project_type) + os.sep + 'updates' + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN' + os.sep,
                                            True)
                                        if status is False:
                                            status = False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.sql_dir + os.sep + str(
                                            project_type) + os.sep + 'updates' + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                            self.locale + os.sep)),
                                        self.sql_dir + os.sep + str(
                                            project_type) + os.sep + 'updates' + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                            self.locale + os.sep))
                                    if status is False:
                                        status = False
                        else:
                            if str(sub_folder) > str(self.project_data_schema_version).replace('.', '') and str(sub_folder) > '31100' and str(sub_folder) <= str(self.version_metadata).replace('.', ''):
                                if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder, os.sep + 'utils' + os.sep) is False:
                                    status=False
                                else:
                                    status = self.load_sql(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep)
                                    if status is False:
                                        status=False
                                if self.process_folder(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + self.project_type_selected + os.sep,
                                        '') is False:
                                    status=False
                                else:
                                    status = self.load_sql(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + self.project_type_selected + os.sep)
                                    if status is False:
                                        status=False
                                if self.process_folder(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep),
                                        '') is False:
                                    if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep, 'EN') is False:
                                        status=False
                                    else:
                                        status = self.executeFiles(os.listdir(
                                            self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN'),
                                            self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN', True)
                                        if status is False:
                                            status=False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep)),
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep))
                                    if status is False:
                                        status=False

        else:
            if not os.path.exists(self.sql_dir + os.sep + str(project_type) + os.sep + ''):
                self.controller.show_message("The project_type folder was not found in sql folder.", 1)
                self.error_count = self.error_count + 1
                return
            folders = os.listdir(self.sql_dir + os.sep + str(project_type) + os.sep + '')
            for folder in folders:
                sub_folders = os.listdir(self.sql_dir + os.sep + str(project_type) + os.sep + folder)
                for sub_folder in sub_folders:
                    if new_project:
                        if self.read_all_updates == 'TRUE':
                            if str(sub_folder) > '31100':
                                if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder,
                                                       '') is False:
                                    status=False
                                else:
                                    status = self.load_sql(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder)
                                    if status is False:
                                        status=False
                                if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep), '') is False:
                                    if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep, 'EN') is False:
                                        status=False
                                    else:
                                        status = self.executeFiles(os.listdir(
                                            self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN'),
                                            self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN', True)
                                        if status is False:
                                            status=False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                            self.locale + os.sep)), self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep))
                                    if status is False:
                                        status=False
                        else:
                            if str(sub_folder) > '31100' and str(sub_folder) <= str(self.version_metadata).replace('.',''):
                                if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder,
                                                       '') is False:
                                    status=False
                                else:
                                    status = self.load_sql(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder)
                                    if status is False:
                                        status=False
                                if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep), '') is False:
                                    if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep, 'EN') is False:
                                        status=False
                                    else:
                                        status = self.executeFiles(os.listdir(
                                            self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN'),
                                            self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN', True)
                                        if status is False:
                                            status=False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                            self.locale + os.sep)), self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep))
                                    if status is False:
                                        status=False
                    else:
                        if self.read_all_updates == 'TRUE':
                            if str(sub_folder) > str(self.project_data_schema_version).replace('.', '') and str(sub_folder) > '31100':
                                if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder, os.sep + 'utils' + os.sep) is False:
                                    status=False
                                else:
                                    status = self.load_sql(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep)
                                    if status is False:
                                        status=False
                                if self.process_folder(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + self.project_type + os.sep,
                                        '') is False:
                                    status=False
                                else:
                                    status = self.load_sql(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + self.project_type + os.sep)
                                    if status is False:
                                        status=False
                                if self.process_folder(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep),
                                        '') is False:
                                    if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep, 'EN') is False:
                                        status=False
                                    else:
                                        status = self.executeFiles(os.listdir(
                                            self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN'),
                                            self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN', True)
                                        if status is False:
                                            status=False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep)),
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                            self.locale + os.sep))
                                    if status is False:
                                        status=False
                        else:
                            if str(sub_folder) > str(self.project_data_schema_version).replace('.', '') and str(sub_folder) > '31100' and str(sub_folder) <= str(self.version_metadata).replace('.', ''):
                                if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder, os.sep + 'utils' + os.sep) is False:
                                    status=False
                                else:
                                    status = self.load_sql(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep)
                                    if status is False:
                                        status=False
                                if self.process_folder(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + self.project_type + os.sep,
                                        '') is False:
                                    status=False
                                else:
                                    status = self.load_sql(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + self.project_type + os.sep)
                                    if status is False:
                                        status=False
                                if self.process_folder(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep),
                                        '') is False:
                                    if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep, 'EN') is False:
                                        status=False
                                    else:
                                        status = self.executeFiles(os.listdir(
                                            self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN'),
                                            self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN', True)
                                        if status is False:
                                            status=False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep)),
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                            self.locale + os.sep))
                                    if status is False:
                                        status=False
        return True
        

    def load_views(self, project_type=False):

        status = True

        if str(project_type) == 'ws' or str(project_type) == 'ud':
            if self.process_folder(self.folderSoftware, self.file_pattern_ddlview + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_ddlview), self.folderSoftware + self.file_pattern_ddlview)
                if status is False:
                    return False
            if self.process_folder(self.folderUtils, self.file_pattern_ddlview + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_ddlview),
                                           self.folderUtils + self.file_pattern_ddlview)
                if status is False:
                    return False
        else:
            if self.process_folder(str(project_type) + os.sep, self.file_pattern_ddlview + os.sep) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(str(project_type) + os.sep + self.file_pattern_ddlview),
                                           str(project_type) + os.sep + self.file_pattern_ddlview)
                if status is False:
                    return False
        return True

        
    def update_30to31(self, new_project=False, project_type=False):
    
        status = True

        if str(project_type) == 'ws' or str(project_type) == 'ud':
            if not os.path.exists(self.folderUpdates):
                self.controller.show_message("The update folder was not found in sql folder.", 1)
                self.error_count = self.error_count + 1
                return
            folders = os.listdir(self.folderUpdates + '')
            for folder in folders:
                sub_folders = os.listdir(self.folderUpdates + folder)
                for sub_folder in sub_folders:
                    if new_project:
                        if str(sub_folder) <= '31100':
                            if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder, os.sep + 'utils' + os.sep) is False:
                                status=False
                            else:
                                status = self.load_sql(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep)
                                if status is False:
                                    status=False
                            if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder + os.sep + project_type + os.sep, '') is False:
                                status=False
                            else:
                                status = self.load_sql(self.folderUpdates + folder + os.sep + sub_folder + os.sep + project_type + os.sep)
                                if status is False:
                                    status=False
                            if self.process_folder(
                                    self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep),
                                    '') is False:
                                if self.process_folder(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep,
                                        'EN') is False:
                                    status = False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN'),
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN',
                                        True)
                                    if status is False:
                                        status = False
                            else:
                                status = self.executeFiles(os.listdir(
                                    self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep)),
                                    self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep))
                                if status is False:
                                    status = False
                    else:
                        if str(sub_folder) > str(self.project_data_schema_version).replace('.', '') and str(sub_folder) <= '31100':
                            if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder, os.sep + 'utils' + os.sep) is False:
                                status=False
                            else:
                                status = self.load_sql(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep)
                                if status is False:
                                    status=False
                            if self.process_folder(
                                    self.folderUpdates + folder + os.sep + sub_folder + os.sep + self.project_type_selected + os.sep,
                                    '') is False:
                                status=False
                            else:
                                status = self.load_sql(
                                    self.folderUpdates + folder + os.sep + sub_folder + os.sep + self.project_type_selected + os.sep)
                                if status is False:
                                    status=False
                            if self.process_folder(
                                    self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep),
                                    '') is False:
                                if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN', '') is False:
                                    status=False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN'),
                                        self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN', True)
                                    if status is False:
                                        status=False
                            else:
                                status = self.executeFiles(os.listdir(
                                    self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep)),
                                                           self.folderUpdates + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                                               self.locale + os.sep))
                                if status is False:
                                    status=False

        else:
            if not os.path.exists(self.sql_dir + os.sep + str(project_type) + os.sep + ''):
                self.controller.show_message("The project_type folder was not found in sql folder.", 1)
                self.error_count = self.error_count + 1
                return
            folders = os.listdir(self.sql_dir + os.sep + str(project_type) + os.sep + '')
            for folder in folders:
                sub_folders = os.listdir(self.sql_dir + os.sep + str(project_type) + os.sep + folder)
                for sub_folder in sub_folders:
                    if new_project:
                        if str(sub_folder) <= '31100':
                            if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder, '') is False:
                                status=False
                            else:
                                status = self.load_sql(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + '')
                                if status is False:
                                    status=False
                            if self.process_folder(
                                    self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep),
                                    '') is False:
                                if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep, 'EN') is False:
                                    status=False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.sql_dir + os.sep + str(
                                            project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN'),
                                        self.sql_dir + os.sep + str(
                                            project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN' + os.sep, True)
                                    if status is False:
                                        status=False
                            else:
                                status = self.executeFiles(os.listdir(
                                    self.sql_dir + os.sep + str(
                                        project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep)),
                                    self.sql_dir + os.sep + str(
                                        project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep))
                                if status is False:
                                    status=False
                    else:
                        if str(sub_folder) > str(self.project_data_schema_version).replace('.', '') and str(sub_folder) <= '31100':
                            if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder, '') is False:
                                status=False
                            else:
                                status = self.load_sql(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + '')
                                if status is False:
                                    status=False
                            if self.process_folder(
                                    self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep),
                                    '') is False:
                                if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep, 'EN') is False:
                                    status=False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.sql_dir + os.sep + str(
                                            project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN'),
                                        self.sql_dir + os.sep + str(
                                            project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + 'EN' + os.sep, True)
                                    if status is False:
                                        status=False
                            else:
                                status = self.executeFiles(os.listdir(
                                    self.sql_dir + os.sep + str(
                                        project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep)),
                                    self.sql_dir + os.sep + str(
                                        project_type) + os.sep + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep))
                                if status is False:
                                    status=False
        return True

        
    def load_sample_data(self, project_type=False):

        status = True
        if str(project_type) == 'ws' or str(project_type) == 'ud':
            if self.process_folder(self.folderExemple, 'user' + os.sep+ project_type) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderExemple + 'user' + os.sep+ project_type), self.folderExemple + 'user' + os.sep+ project_type)
                if status is False:
                    return False
        else:
            if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + 'example' + os.sep + 'user' + os.sep, '') is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.sql_dir + os.sep + str(project_type) + os.sep + 'example' + os.sep + 'user' + os.sep),
                                           self.sql_dir + os.sep + str(project_type) + os.sep + 'example' + os.sep + 'user' + os.sep)
                if status is False:
                    return False

        return True

        
    def load_dev_data(self, project_type=False):

        status = True
        if str(project_type) == 'ws' or str(project_type) == 'ud':
            if self.process_folder(self.folderExemple, 'dev' + os.sep + project_type) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderExemple + 'dev' + os.sep + project_type), self.folderExemple + 'dev' + os.sep + project_type)
                if status is False:
                    return False
        else:
            if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep + 'example' + os.sep + 'dev' + os.sep, '') is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.sql_dir + os.sep + str(project_type) + os.sep + 'example' + os.sep + 'dev' + os.sep),
                                           self.sql_dir + os.sep + str(project_type) + os.sep + 'example' + os.sep + 'dev' + os.sep)
                if status is False:
                    return False

        return True

        
    def load_fct_ftrg(self, project_type=False):

        status = True
        if str(project_type) == 'ws' or str(project_type) == 'ud':
            if self.process_folder(self.folderUtils, self.file_pattern_fct) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_fct), self.folderUtils + self.file_pattern_fct)
                if status is False:
                    return False
            if self.process_folder(self.folderUtils, self.file_pattern_ftrg) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_ftrg), self.folderUtils + self.file_pattern_ftrg)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_fct) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_fct), self.folderSoftware + self.file_pattern_fct)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_ftrg) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_ftrg), self.folderSoftware + self.file_pattern_ftrg)
                if status is False:
                    return False
        else:
            if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep, self.file_pattern_fct) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.sql_dir + os.sep + str(project_type) + os.sep + self.file_pattern_fct),
                                           self.sql_dir + os.sep + str(project_type) + os.sep + self.file_pattern_fct)
                if status is False:
                    return False
            if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep, self.file_pattern_ftrg) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.sql_dir + os.sep + str(project_type) + os.sep + self.file_pattern_ftrg),
                                           self.sql_dir + os.sep + str(project_type) + os.sep + self.file_pattern_ftrg)
                if status is False:
                    return False

        return True

        
    def load_tablect(self, project_type=False):

        status = True
        if str(project_type) == 'ws' or str(project_type) == 'ud':
            if self.process_folder(self.folderSoftware, self.file_pattern_tablect) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_tablect), self.folderSoftware + self.file_pattern_tablect)
                if status is False:
                    return False
            if self.process_folder(self.folderUtils, self.file_pattern_tablect) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_tablect),
                                           self.folderUtils + self.file_pattern_tablect)
                if status is False:
                    return False
        else:
            if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep, self.file_pattern_tablect) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.sql_dir + os.sep + str(project_type) + os.sep + self.file_pattern_tablect),
                                           self.sql_dir + os.sep + str(project_type) + os.sep + self.file_pattern_tablect)
                if status is False:
                    return False

        return True

        
    def load_trg(self, project_type=False):

        status = True
        if str(project_type) == 'ws' or str(project_type) == 'ud':
            if self.process_folder(self.folderUtils, self.file_pattern_trg) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderUtils + self.file_pattern_trg), self.folderUtils + self.file_pattern_trg)
                if status is False:
                    return False
            if self.process_folder(self.folderSoftware, self.file_pattern_trg) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.folderSoftware + self.file_pattern_trg), self.folderSoftware + self.file_pattern_trg)
                if status is False:
                    return False
        else:
            if self.process_folder(self.sql_dir + os.sep + str(project_type) + os.sep, self.file_pattern_trg) is False:
                return False
            else:
                status = self.executeFiles(os.listdir(self.sql_dir + os.sep + str(project_type) + os.sep + self.file_pattern_trg), self.sql_dir + os.sep + str(project_type) + os.sep + self.file_pattern_trg)
                if status is False:
                    return False

        return True

        
    def load_sql(self, path_folder, no_ct=False):
    
        for (path, ficheros, archivos) in os.walk(path_folder):
            status = self.executeFiles(archivos, path, no_ct=no_ct)
            if status is False:
                return False
        return True
        

    def api(self, new_api=False, project_type=False):

        status = True
        if self.process_folder(self.folderApi, self.file_pattern_ftrg) is False:
            status=False
        else:
            status = self.executeFiles(os.listdir(self.folderApi + self.file_pattern_ftrg), self.folderApi + self.file_pattern_ftrg)
            if status is False:
                status = False
        if self.process_folder(self.folderApi, self.file_pattern_fct) is False:
            status = False
        else:
            status = self.executeFiles(os.listdir(self.folderApi + self.file_pattern_fct), self.folderApi + self.file_pattern_fct)
            if status is False:
                status = False
        if not os.path.exists(self.folderUpdatesApi):
            self.controller.show_message("The api folder was not found in sql folder.", 1)
            self.error_count = self.error_count + 1
            return
        folders = os.listdir(self.folderUpdatesApi + '')
        for folder in folders:
            sub_folders = os.listdir(self.folderUpdatesApi + folder)
            for sub_folder in sub_folders:
                if new_api:
                    if self.read_all_updates == 'TRUE':
                        if self.process_folder(self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep, '') is False:
                            status=False
                        else:
                            status = self.executeFiles(os.listdir(self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep + ''),
                                                      self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep + '')
                            if status is False:
                                status=False
                        if self.process_folder(
                                self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep),
                                '') is False:
                            if self.process_folder(self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep, 'EN') is False:
                                status=False
                            else:
                                status = self.executeFiles(os.listdir(
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + self.locale),
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + self.locale + os.sep, True)
                                if status is False:
                                    status=False
                        else:
                            status = self.executeFiles(os.listdir(
                                self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep)),
                                self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep))
                            if status is False:
                                status=False
                        if self.process_folder(self.sql_dir + os.sep + 'api' + os.sep, self.file_pattern_trg) is False:
                            status=False
                        else:
                            status = self.executeFiles(os.listdir(self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_trg),
                                                    self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_trg)
                            if status is False:
                                status=False
                        if self.process_folder(self.sql_dir + os.sep + 'api' + os.sep, self.file_pattern_tablect) is False:
                            status=False
                        else:
                            status = self.executeFiles(os.listdir(self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_tablect),
                                                        self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_tablect)
                            if status is False:
                                status=False
                    else:
                        if str(sub_folder) <= str(self.version_metadata).replace('.', ''):
                            if self.process_folder(self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep,
                                                   '') is False:
                                status=False
                            else:
                                status = self.executeFiles(
                                    os.listdir(self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep + ''),
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep + '')
                                if status is False:
                                    status=False
                            if self.process_folder(
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep),
                                    '') is False:
                                if self.process_folder(self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep,
                                                       'EN') is False:
                                    status=False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + self.locale),
                                        self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + self.locale + os.sep,
                                        True)
                                    if status is False:
                                        status=False
                            else:
                                status = self.executeFiles(os.listdir(
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep)),
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep))
                                if status is False:
                                    status=False
                            if self.process_folder(self.sql_dir + os.sep + 'api' + os.sep, self.file_pattern_trg) is False:
                                status=False
                            else:
                                status = self.executeFiles(
                                    os.listdir(self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_trg),
                                    self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_trg)
                                if status is False:
                                    status=False

                            if self.process_folder(self.sql_dir + os.sep + 'api' + os.sep, self.file_pattern_tablect) is False:
                                status = False
                            else:
                                status = self.executeFiles(
                                    os.listdir(self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_tablect),
                                    self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_tablect)
                                if status is False:
                                    status=False
                else:
                    if self.read_all_updates == 'TRUE':
                        if str(sub_folder) > str(self.project_data_schema_version).replace('.', ''):
                            if self.process_folder(self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep, '') is False:
                                status=False
                            else:
                                status = self.executeFiles(os.listdir(self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep + ''),
                                                           self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep + '')
                                if status is False:
                                    status=False
                            if self.process_folder(
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep),
                                    '') is False:
                                if self.process_folder(self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep, 'EN') is False:
                                    status=False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + self.locale),
                                        self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + self.locale + os.sep, True)
                                    if status is False:
                                        status=False
                            else:
                                status = self.executeFiles(os.listdir(
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep)),
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(self.locale + os.sep))
                                if status is False:
                                    status=False
                            if self.process_folder(self.sql_dir + os.sep + 'api' + os.sep, self.file_pattern_trg) is False:
                                status=False
                            else:
                                status = self.executeFiles(os.listdir(self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_trg),
                                                           self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_trg)
                                if status is False:
                                    status=False
                            if self.process_folder(self.sql_dir + os.sep + 'api' + os.sep, self.file_pattern_tablect) is False:
                                status=False
                            else:
                                status = self.executeFiles(os.listdir(self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_tablect),
                                                           self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_tablect)
                                if status is False:
                                    status=False
                    else:
                        if str(sub_folder) > str(self.project_data_schema_version).replace('.', '') and str(sub_folder) <= str(self.version_metadata).replace('.', ''):
                            if self.process_folder(self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep,
                                                   '') is False:
                                status=False
                            else:
                                status = self.executeFiles(
                                    os.listdir(self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep + ''),
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'utils' + os.sep + '')
                                if status is False:
                                    status=False
                            if self.process_folder(
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep),
                                    '') is False:
                                if self.process_folder(self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep,
                                                       'EN') is False:
                                    status=False
                                else:
                                    status = self.executeFiles(os.listdir(
                                        self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + self.locale),
                                        self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + self.locale + os.sep,
                                        True)
                                    if status is False:
                                        status=False
                            else:
                                status = self.executeFiles(os.listdir(
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep)),
                                    self.folderUpdatesApi + folder + os.sep + sub_folder + os.sep + 'i18n' + os.sep + str(
                                        self.locale + os.sep))
                                if status is False:
                                    status=False
                            if self.process_folder(self.sql_dir + os.sep + 'api' + os.sep, self.file_pattern_trg) is False:
                                status=False
                            else:
                                status = self.executeFiles(os.listdir(self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_trg),
                                                           self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_trg)
                                if status is False:
                                    status=False
                            if self.process_folder(self.sql_dir + os.sep + 'api' + os.sep, self.file_pattern_tablect) is False:
                                status=False
                            else:
                                status = self.executeFiles(
                                    os.listdir(self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_tablect),
                                    self.sql_dir + os.sep + 'api' + os.sep + self.file_pattern_tablect)
                                if status is False:
                                    status=False

        return True

    """ Functions execute process """

    def execute_import_data(self):
        #TODO:: This functions are comment at the moment. We dont enable this function until 3.2
        return
        # Execute import data
        sql = ("SELECT " + self.schema_name + ".gw_fct_utils_csv2pg_import_epa_inp()")
        self.controller.execute_sql(sql, commit=False)

        
    def execute_last_process(self, new_project=False, schema_name='', schema_type='', locale=False):
        # Execute last process function
        if new_project is True:
            extras = '"isNewProject":"' + str('TRUE') + '", '
        else:
            extras = '"isNewProject":"' + str('FALSE') + '", '
        extras += '"gwVersion":"' + str(self.version_metadata) + '", '
        extras += '"projectType":"' + str(schema_type).upper() + '", '
        extras += '"epsg":' + str(self.filter_srid_value).replace('"', '')
        if new_project is True:
            if str(self.title) != 'null':
                extras += ', ' + '"title":"' + str(self.title) + '"'
            if str(self.author) != 'null':
                extras += ', ' + '"author":"' + str(self.author) + '"'
            if str(self.date) != 'null':
                extras += ', ' + '"date":"' + str(self.date) + '"'

        self.schema_name = schema_name

        #Get current locale
        if locale:
            locale = ''
        else:
            locale = utils_giswater.getWidgetText(self.dlg_readsql_create_project,
                                                  self.dlg_readsql_create_project.cmb_locale)

        client = '"client":{"device":9, "lang":"'+locale+'"}, '
        data = '"data":{' + extras + '}'
        body = "" + client + data
        sql = ("SELECT " + self.schema_name + ".gw_fct_admin_schema_lastprocess($${" + body + "}$$)::text")
        status = self.controller.execute_sql(sql, commit=False)
        if status is False:
            self.error_count = self.error_count + 1
        return

        
    """ Buttons calling functions """

    def create_project_data_schema(self):
    
        self.title = utils_giswater.getWidgetText(self.dlg_readsql_create_project, self.project_title)
        self.author = utils_giswater.getWidgetText(self.dlg_readsql_create_project, self.project_author)
        self.date = utils_giswater.getWidgetText(self.dlg_readsql_create_project, self.project_date)
        project_name = str(utils_giswater.getWidgetText(self.dlg_readsql_create_project, self.project_name))
        schema_type = utils_giswater.getWidgetText(self.dlg_readsql_create_project, self.dlg_readsql_create_project.cmb_create_project_type)
        self.filter_srid_value = utils_giswater.getWidgetText(self.dlg_readsql_create_project, self.dlg_readsql_create_project.srid_id)
        if project_name == 'null':
            msg = "The 'Project_name' field is required."
            result = self.controller.show_info_box(msg, "Info")
            return
        elif any(c.isupper() for c in project_name) is True:
            msg = "The 'Project_name' field require only lower caracters"
            result = self.controller.show_info_box(msg, "Info")
            return
        elif (bool(re.match('^[a-z0-9_]*$', project_name))) is False:
            msg = "The 'Project_name' field have invalid character"
            result = self.controller.show_info_box(msg, "Info")
            return
        if self.title == 'null':
            msg = "The 'Title' field is required."
            result = self.controller.show_info_box(msg, "Info")
            return
        sql = ("SELECT schema_name, schema_name FROM information_schema.schemata")
        rows = self.controller.get_rows(sql)
        for row in rows:
            if str(project_name) == str(row[0]):
                msg = "This 'Project_name' is already exist."
                result = self.controller.show_info_box(msg, "Info")
                return

        self.schema = utils_giswater.getWidgetText(self.dlg_readsql_create_project, 'project_name')
        project_type = utils_giswater.getWidgetText(self.dlg_readsql_create_project, 'cmb_create_project_type')

        # Get value from combo locale
        self.locale = utils_giswater.getWidgetText(self.dlg_readsql_create_project,
                                                   self.dlg_readsql_create_project.cmb_locale)
        self.setWaitCursor()
        if self.rdb_import_data.isChecked():
            self.load_base_no_ct(project_type=project_type)
            self.update_30to31(new_project=True, project_type=project_type)
            self.load_views(project_type=project_type)
            self.load_trg(project_type=project_type)
            self.update_31to39(new_project=True, project_type=project_type)
            self.execute_import_data()
            self.api(project_type=project_type)
            self.execute_last_process(new_project=True, schema_name=project_name, schema_type=schema_type)
            
        elif self.rdb_no_ct.isChecked():
            self.load_base_no_ct(project_type=project_type)
            self.update_30to31(new_project=True, project_type=project_type)
            self.load_views(project_type=project_type)
            self.update_31to39(new_project=True, project_type=project_type, no_ct=True)
            self.api(project_type=project_type)
            self.execute_last_process(new_project=True, schema_name=project_name, schema_type=schema_type)
            
        elif self.rdb_sample.isChecked():
            if utils_giswater.getWidgetText(self.dlg_readsql_create_project, self.dlg_readsql_create_project.cmb_locale) != 'EN':
                self.setArrowCursor()
                msg = "This functionality is only allowed with the locality 'EN'. Do you want to changed it to 'EN' and continue?"
                result = self.controller.ask_question(msg, "Info Message")
                if result:
                    utils_giswater.setWidgetText(self.dlg_readsql_create_project, self.cmb_locale, 'EN')
                    self.setWaitCursor()
                else:
                    self.setArrowCursor()
                    return

            self.load_base(project_type=project_type)
            self.update_30to31(new_project=True, project_type=project_type)
            self.load_views(project_type=project_type)
            self.load_trg(project_type=project_type)
            self.update_31to39(new_project=True, project_type=project_type)
            self.api(project_type=project_type)
            self.execute_last_process(new_project=True, schema_name=project_name, schema_type=schema_type)
            self.load_sample_data(project_type=project_type)

        elif self.rdb_sample_dev.isChecked():
            if utils_giswater.getWidgetText(self.dlg_readsql_create_project, self.dlg_readsql_create_project.cmb_locale) != 'EN':
                msg = "This functionality is only allowed with the locality 'EN'. Do you want change it and continue?"
                result = self.controller.ask_question(msg, "Info Message")
                if result:
                    utils_giswater.setWidgetText(self.dlg_readsql_create_project, self.cmb_locale, 'EN')
                else:
                    self.setArrowCursor()
                    return

            self.load_base(project_type=project_type)
            self.update_30to31(new_project=True, project_type=project_type)
            self.load_views(project_type=project_type)
            self.load_trg(project_type=project_type)
            self.update_31to39(new_project=True, project_type=project_type)
            self.api(project_type=project_type)
            self.execute_last_process(new_project=True, schema_name=project_name, schema_type=schema_type)
            self.load_sample_data(project_type=project_type)
            self.load_dev_data(project_type=project_type)


        elif self.rdb_data.isChecked():

            self.load_base(project_type=project_type)
            self.update_30to31(new_project=True, project_type=project_type)
            self.load_views(project_type=project_type)
            self.load_trg(project_type=project_type)
            self.update_31to39(new_project=True, project_type=project_type)
            self.api(project_type=project_type)
            self.execute_last_process(new_project=True, schema_name=project_name, schema_type=schema_type)
        self.setArrowCursor()

        # Show message if process executed correctly
        if self.error_count == 0:
            self.controller.dao.commit()
            msg = "The project has been created correctly."
            result = self.controller.show_info_box(msg, "Info")
            self.close_dialog(self.dlg_readsql_create_project)
        else:
            self.controller.dao.rollback()
            msg = "Some errors has occurred. Process has not been executed."
            result = self.controller.show_info_box(msg, "Info")

        # Reset count error variable to 0
        self.error_count = 0

        # Referesh data main dialog
        self.event_change_connection()
        self.set_info_project()

        
    def rename_project_data_schema(self):
    
        self.setWaitCursor()
        self.schema = utils_giswater.getWidgetText(self.dlg_readsql_rename,self.dlg_readsql_rename.schema_rename)
        self.load_fct_ftrg(project_type=self.project_type_selected)
        self.execute_last_process(schema_name=self.schema, locale=True)
        self.setArrowCursor()

        
    def update_api(self):
    
        self.setWaitCursor()
        self.api(False)
        self.setArrowCursor()

        # Show message if precess execute correctly
        if self.error_count == 0:
            self.controller.dao.commit()
            msg = "Api has been updated correctly."
            result = self.controller.show_info_box(msg, "Info")

        else:
            self.controller.dao.rollback()
            msg = "Some error has occurred while the api updated process was running."
            result = self.controller.show_info_box(msg, "Info")

        # Reset count error variable to 0
        self.error_count = 0

        
    def implement_api(self):
    
        self.setWaitCursor()
        self.api(True)
        self.setArrowCursor()

        
    def load_custom_sql_files(self, dialog, widget):
    
        folder_path = utils_giswater.getWidgetText(dialog, widget)
        self.setWaitCursor()
        self.load_sql(folder_path)
        self.setArrowCursor()

        # Show message if precess execute correctly
        if self.error_count == 0:
            self.controller.dao.commit()
            msg = "The process has been executed correctly."
            result = self.controller.show_info_box(msg, "Info")

        else:
            self.controller.dao.rollback()
            msg = "Some error has occurred while the process was running."
            result = self.controller.show_info_box(msg, "Info")

        # Reset count error variable to 0
        self.error_count = 0

        
    #TODO:Rename this function => Update all versions from changelog file.
    def update(self, project_type):
    
        msg = "Are you sure to update the project schema to lastest version?"
        result = self.controller.ask_question(msg, "Info")
        if result:
            self.setWaitCursor()
            self.load_updates(project_type, update_changelog=True)
            self.set_info_project()
            self.setArrowCursor()
        else:
            return

        # Show message if precess execute correctly
        if self.error_count == 0:
            self.controller.dao.commit()
            msg = "The update has been executed correctly."
            result = self.controller.show_info_box(msg, "Info")

            # Close dialog when process has been execute correctly
            self.close_dialog(self.dlg_readsql_show_info)
        else:
            self.controller.dao.rollback()
            msg = "Some error has occurred while the update process was running."
            result = self.controller.show_info_box(msg, "Info")

        # Reset count error variable to 0
        self.error_count = 0

        
    """ Checkbox calling functions """

    def load_updates(self, project_type, update_changelog=False):
    
        # Get current schema selected
        schema_name = utils_giswater.getWidgetText(self.dlg_readsql, self.dlg_readsql.project_schema_name)

        self.setWaitCursor()
        self.load_fct_ftrg(project_type=project_type)
        self.update_30to31(project_type=project_type)
        self.update_31to39(project_type=project_type)
        self.api(project_type=project_type)
        self.execute_last_process(schema_name=schema_name, locale=True)
        self.setArrowCursor()

        if update_changelog is False:
            # Show message if precess execute correctly
            if self.error_count == 0:
                self.controller.dao.commit()
                msg = "The update has been executed correctly."
                result = self.controller.show_info_box(msg, "Info")
            else:
                self.controller.dao.rollback()
                msg = "Some error has occurred while the update process was running."
                result = self.controller.show_info_box(msg, "Info")

            # Reset count error variable to 0
            self.error_count = 0

            
    def reload_tablect(self, project_type=False):
        self.load_tablect(project_type=project_type)

        
    def reload_fct_ftrg(self, project_type=False):
        self.load_fct_ftrg(project_type=project_type)

        
    def reload_trg(self, project_type=False):
        self.load_trg(project_type)

        
    """ Create new connection when change combo connections """

    def event_change_connection(self):

        connection_name = str(utils_giswater.getWidgetText(self.dlg_readsql, self.cmb_connection))

        credentials = {'db': None, 'host': None, 'port': None, 'user': None, 'password': None}

        settings = QSettings()
        settings.beginGroup("PostgreSQL/connections/" + connection_name)

        credentials['host'] = settings.value('host')
        credentials['port'] = settings.value('port')
        credentials['db'] = settings.value('database')
        credentials['user'] = settings.value('username')
        credentials['password'] = settings.value('password')

        settings.endGroup()

        self.logged = self.controller.connect_to_database(credentials['host'], credentials['port'],
                                               credentials['db'], credentials['user'],
                                               credentials['password'])

        self.populate_data_schema_name(self.cmb_project_type)

        self.set_last_connection(connection_name)


    def set_last_connection(self, connection_name):
        settings = QSettings()
        settings.beginGroup("PostgreSQL/connections")
        settings.setValue('selected', connection_name)
        settings.endGroup()

    def get_last_connection(self):
        settings = QSettings()
        settings.beginGroup("PostgreSQL/connections")
        connection_name = settings.value('selected')
        settings.endGroup()
        return connection_name

    """ Other functions """

    def show_info(self):
    
        # Create dialog
        self.dlg_readsql_show_info = ReadsqlShowInfo()
        self.load_settings(self.dlg_readsql_show_info)

        info_updates = self.dlg_readsql_show_info.findChild(QTextEdit, 'info_updates')
        self.message_update = ''

        self.read_info_version()

        info_updates.setText(self.message_update)

        if str(self.message_update) == '':
            self.dlg_readsql_show_info.btn_update.setEnabled(False)

        #Set listeners
        self.dlg_readsql_show_info.btn_close.clicked.connect(partial(self.close_dialog, self.dlg_readsql_show_info))
        self.dlg_readsql_show_info.btn_update.clicked.connect(partial(self.update, self.project_type_selected))

        # Open dialog
        self.dlg_readsql_show_info.show()

        
    def read_info_version(self):
    
        status = True
        if not os.path.exists(self.folderUpdates):
            self.controller.show_message("The updates folder was not found in sql folder.", 1)
            return
        folders = os.listdir(self.folderUpdates + '')
        for folder in folders:
            sub_folders = os.listdir(self.folderUpdates + folder)
            for sub_folder in sub_folders:
                if str(sub_folder) > str(self.project_data_schema_version).replace('.',''):

                    if self.process_folder(self.folderUpdates + folder + os.sep + sub_folder, '') is False:
                        status=False
                    else:
                        status = self.readFiles(
                            os.listdir(self.folderUpdates + folder + os.sep + sub_folder + ''), self.folderUpdates + folder + os.sep + sub_folder + '')
                        if status is False:
                            status=False
                else:
                    status = False
        return True

        
    def close_dialog(self, dlg=None):

        """ Close dialog """

        if dlg is None or type(dlg) is bool:
            dlg = self.dlg
        try:
            self.save_settings(dlg)
            dlg.close()
            map_tool = self.canvas.mapTool()
            # If selected map tool is from the plugin, set 'Pan' as current one
            if map_tool.toolName() == '':
                self.iface.actionPan().trigger()
        except AttributeError:
            pass

        self.schema = None

        
    def update_locale(self):

        self.folderLocale = self.sql_dir + os.sep + utils_giswater.getWidgetText(self.dlg_readsql, self.cmb_locale) + os.sep

        
    def enable_datafile(self):
    
        if self.rdb_import_data.isChecked() is True:
            self.data_file.setEnabled(True)
            self.btn_push_file.setEnabled(True)
        else:
            self.data_file.setEnabled(False)
            self.btn_push_file.setEnabled(False)

            
    def populate_data_schema_name(self, widget):

        # Get filter
        filter = str(utils_giswater.getWidgetText(self.dlg_readsql, widget))
        result_list = []

        # Populate Project data schema Name
        sql = ("SELECT schema_name FROM information_schema.schemata")
        rows = self.controller.get_rows(sql)
        if rows is None:
            return
        for row in rows:
            sql = ("SELECT EXISTS(SELECT * FROM information_schema.tables WHERE table_schema = '" + str(row[0]) + "' "
                                                                                                                  " AND table_name = 'version')")
            exists = self.controller.get_row(sql)
            if str(exists[0]) == 'True':
                sql = ("SELECT wsoftware FROM " + str(row[0]) + ".version")
                result = self.controller.get_row(sql)
                if result is not None and result[0] == filter.upper():
                    elem = [row[0], row[0]]
                    result_list.append(elem)
        utils_giswater.set_item_data(self.dlg_readsql.project_schema_name, result_list, 1)

        
    def filter_srid_changed(self):
    
        filter_value = utils_giswater.getWidgetText(self.dlg_readsql_create_project, self.filter_srid)
        if filter_value is 'null':
            filter_value = ''
        sql = "SELECT substr(srtext, 1, 6) as "+'"Type"'+", srid as "+'"SRID"'+", substr(split_part(srtext, ',', 1), 9) as "
        sql += '"Description"'+" FROM public.spatial_ref_sys WHERE CAST(srid AS TEXT) LIKE '"+str(filter_value)
        sql += "%' ORDER BY substr(srtext, 1, 6), srid"
        
        # Populate Table
        self.fill_table_by_query(self.tbl_srid, sql)

        
    def set_info_project(self):
    
        schema_name = utils_giswater.getWidgetText(self.dlg_readsql, self.dlg_readsql.project_schema_name)

        if schema_name is None:
            utils_giswater.setWidgetText(self.dlg_readsql,
                                         self.dlg_readsql.project_schema_title, '')
            utils_giswater.setWidgetText(self.dlg_readsql,
                                         self.dlg_readsql.project_schema_author, '')
            utils_giswater.setWidgetText(self.dlg_readsql,
                                         self.dlg_readsql.project_schema_last_update, '')
            schema_name = 'Nothing to select'
            self.project_data_schema_version = "Version not found"
        else:
            sql = "SELECT title, author FROM " + schema_name + ".inp_project_id"
            row = self.controller.get_row(sql)
            if row is None:
                utils_giswater.setWidgetText(self.dlg_readsql,
                                             self.dlg_readsql.project_schema_title, '')
                utils_giswater.setWidgetText(self.dlg_readsql,
                                             self.dlg_readsql.project_schema_author, '')
            else:
                utils_giswater.setWidgetText(self.dlg_readsql,
                                             self.dlg_readsql.project_schema_title, str(row[0]))
                utils_giswater.setWidgetText(self.dlg_readsql,
                                             self.dlg_readsql.project_schema_author, str(row[1]))
            sql = "SELECT giswater, date::date FROM " + schema_name + ".version order by id desc LIMIT 1"
            row = self.controller.get_row(sql)
            if row is not None:
                self.project_data_schema_version = str(row[0])
                utils_giswater.setWidgetText(self.dlg_readsql,
                                            self.dlg_readsql.project_schema_last_update, str(row[1]))
        if self.version is None:
            self.version = '0'
        self.software_version_info.setText('Plugin version: ' + self.plugin_version + '\n' +
                                           'Database version: ' + self.version + '\n \n' +
                                           'Schema name: ' + schema_name + '\n' +
                                           'Schema version: ' + self.project_data_schema_version)


    def process_folder(self, folderPath, filePattern):
    
        status = True
        try:
            self.controller.log_info(str(os.listdir(folderPath + filePattern)))
            return status
        except Exception as e:
            status = False
            self.controller.log_info(str(e))

        return status

        
    def schema_file_to_db(self):

        if self.chk_schema_fk.isChecked():
            self.setWaitCursor()
            self.reload_tablect(self.project_type_selected)
            self.setArrowCursor()

        if self.chk_schema_funcion.isChecked():
            self.setWaitCursor()
            self.reload_fct_ftrg(self.project_type_selected)
            self.setArrowCursor()

        if self.chk_schema_trigger.isChecked():
            self.setWaitCursor()
            self.reload_trg(self.project_type_selected)
            self.setArrowCursor()

        # Show message if precess execute correctly
        if self.error_count == 0:
            self.controller.dao.commit()
            msg = "The reload has been executed correctly."
            result = self.controller.show_info_box(msg, "Info")

        else:
            self.controller.dao.rollback()
            msg = "Some error has occurred while the reload process was running."
            result = self.controller.show_info_box(msg, "Info")

        # Reset count error variable to 0
        self.error_count = 0

        
    def api_file_to_db(self):

        if self.chk_api_fk.isChecked():
            self.setWaitCursor()
            self.reload_tablect('api')
            self.setArrowCursor()
        if self.chk_api_funcion.isChecked():
            self.setWaitCursor()
            self.reload_fct_ftrg('api')
            self.setArrowCursor()
        if self.chk_api_trigger.isChecked():
            self.setWaitCursor()
            self.reload_trg('api')
            self.setArrowCursor()

        # Show message if precess execute correctly
        if self.error_count == 0:
            self.controller.dao.commit()
            msg = "The reload has been executed correctly."
            result = self.controller.show_info_box(msg, "Info")

        else:
            self.controller.dao.rollback()
            msg = "Some error has occurred while the reload process was running."
            result = self.controller.show_info_box(msg, "Info")

        # Reset count error variable to 0
        self.error_count = 0

        
    def open_create_project(self):
        
        # Create dialog
        self.dlg_readsql_create_project = ReadsqlCreateProject()
        self.load_settings(self.dlg_readsql_create_project)

        # Find Widgets in form
        self.project_name = self.dlg_readsql_create_project.findChild(QLineEdit, 'project_name')
        self.project_title = self.dlg_readsql_create_project.findChild(QLineEdit, 'project_title')
        self.project_author = self.dlg_readsql_create_project.findChild(QLineEdit, 'author')
        self.project_date = self.dlg_readsql_create_project.findChild(QLineEdit, 'date')

        self.rdb_no_ct = self.dlg_readsql_create_project.findChild(QRadioButton, 'rdb_no_ct')
        self.rdb_sample = self.dlg_readsql_create_project.findChild(QRadioButton, 'rdb_sample')
        self.rdb_sample_dev = self.dlg_readsql_create_project.findChild(QRadioButton, 'rdb_sample_dev')
        self.rdb_data = self.dlg_readsql_create_project.findChild(QRadioButton, 'rdb_data')
        self.rdb_import_data = self.dlg_readsql_create_project.findChild(QRadioButton, 'rdb_import_data')

        self.data_file = self.dlg_readsql_create_project.findChild(QLineEdit, 'data_file')
        #TODO:: do and call listener for buton + table -> temp_csv2pg
        self.btn_push_file = self.dlg_readsql_create_project.findChild(QPushButton, 'btn_push_file')
                
        if self.dev_user != 'TRUE':
            self.rdb_no_ct.setEnabled(False)
            self.rdb_sample_dev.setEnabled(False)

        self.filter_srid = self.dlg_readsql_create_project.findChild(QLineEdit, 'srid_id')
        utils_giswater.setWidgetText(self.dlg_readsql_create_project, 'srid_id', str(self.filter_srid_value))
        self.tbl_srid = self.dlg_readsql_create_project.findChild(QTableView, 'tbl_srid')
        self.tbl_srid.setSelectionBehavior(QAbstractItemView.SelectRows)
        sql = "SELECT substr(srtext, 1, 6) as "+'"Type"'+", srid as "+'"SRID"'+", substr(split_part(srtext, ',', 1), 9) as "+'"Description"'+" FROM public.spatial_ref_sys WHERE CAST(srid AS TEXT) LIKE '"+str(self.filter_srid_value)+"%' ORDER BY substr(srtext, 1, 6), srid"

        # Populate Table
        self.fill_table_by_query(self.tbl_srid, sql)

        self.cmb_create_project_type = self.dlg_readsql_create_project.findChild(QComboBox, 'cmb_create_project_type')
        for type in self.project_types:
            self.cmb_create_project_type.addItem(str(type))
        utils_giswater.setWidgetText(self.dlg_readsql_create_project, self.cmb_create_project_type, utils_giswater.getWidgetText(self.dlg_readsql, self.dlg_readsql.cmb_project_type))
        self.change_project_type(self.cmb_create_project_type)

        # enable_disable data file widgets
        self.enable_datafile()

        #Get combo locale
        self.cmb_locale = self.dlg_readsql_create_project.findChild(QComboBox, 'cmb_locale')

        # Set listeners
        self.dlg_readsql_create_project.btn_accept.clicked.connect(partial(self.create_project_data_schema))
        self.dlg_readsql_create_project.btn_close.clicked.connect(partial(self.close_dialog, self.dlg_readsql_create_project))
        self.cmb_create_project_type.currentIndexChanged.connect(partial(self.change_project_type, self.cmb_create_project_type))
        self.cmb_locale.currentIndexChanged.connect(partial(self.update_locale))
        self.rdb_import_data.toggled.connect(partial(self.enable_datafile))
        self.filter_srid.textChanged.connect(partial(self.filter_srid_changed))

        # Populate combo with all locales
        locales = os.listdir(self.sql_dir + os.sep + 'i18n' + os.sep)
        for locale in locales:
            self.cmb_locale.addItem(locale)
            if locale == 'EN':
                utils_giswater.setWidgetText(self.dlg_readsql_create_project, self.cmb_locale, 'EN')


        # Open dialog
        self.dlg_readsql_create_project.show()

        
    def open_rename(self):
    
        # Create dialog
        self.dlg_readsql_rename = ReadsqlRename()
        self.load_settings(self.dlg_readsql_rename)

        # Set listeners
        self.dlg_readsql_rename.btn_accept.clicked.connect(partial(self.rename_project_data_schema))
        self.dlg_readsql_rename.btn_cancel.clicked.connect(partial(self.close_dialog, self.dlg_readsql_rename))

        # Open dialog
        self.dlg_readsql_rename.show()

        
    def executeFiles(self, filelist, filedir, i18n=False, no_ct=False):
    
        if not filelist:
            return
            
        if self.schema is None:
            if self.schema_name is None:
                schema_name = utils_giswater.getWidgetText(self.dlg_readsql, self.dlg_readsql.project_schema_name)
                schema_name = schema_name.replace('"', '')
            else:
                schema_name = self.schema_name.replace('"','')
        else:
            schema_name = self.schema.replace('"', '')
        filter_srid_value = str(self.filter_srid_value).replace('"', '')
        if i18n:
            for file in filelist:
                if "utils.sql" in file :
                    self.controller.log_info(str(filedir + os.sep + 'utils.sql'))
                    self.read_execute_file(filedir, os.sep + 'utils.sql', schema_name, filter_srid_value)
                elif str(self.project_type_selected) + ".sql" in file:
                    self.controller.log_info(str(filedir + os.sep + str(self.project_type_selected) + '.sql'))
                    self.read_execute_file(filedir, os.sep + str(self.project_type_selected) + '.sql', schema_name,
                                           filter_srid_value)
        else:
            for file in filelist:
                self.controller.log_info(str(filedir + os.sep + file))
                if ".sql" in file:
                    if (no_ct is True and "tablect.sql" not in file) or no_ct is False:
                        self.controller.log_info(str(filedir + os.sep + file))
                        self.read_execute_file(filedir, file, schema_name, filter_srid_value)

        return True

        
    def read_execute_file(self, filedir, file, schema_name, filter_srid_value):
    
        try:
            f = open(filedir + os.sep + file, 'r')
            if f:
                f_to_read = str(
                    f.read().replace("SCHEMA_NAME", schema_name).replace("SRID_VALUE", filter_srid_value)).decode(
                    str('utf-8-sig'))

                status = self.controller.execute_sql(str(f_to_read), commit=False)

                if status is False:
                    self.error_count = self.error_count + 1
                    self.controller.log_info(str("Error to execute"))
                    self.controller.log_info(str('Message: ' + str(self.controller.last_error)))
                    return False

        except Exception as e:
            self.error_count = self.error_count + 1
            self.controller.log_info(str("Error to execute"))
            self.controller.log_info(str('Message: ' + str(self.controller.last_error)))
            return False

            
    def readFiles(self, filelist, filedir):

        if "changelog.txt" in filelist:
            try:
                f = open(filedir + os.sep + 'changelog.txt', 'r')
                if f:
                    f_to_read = str(f.read()).decode(str('utf-8-sig'))
                    f_to_read = f_to_read + '\n \n'
                    self.message_update = self.message_update + '\n' + str(f_to_read)
                else:
                    return False
            except Exception as e:
                return False
        return True


    def setWaitCursor(self):
        QApplication.instance().setOverrideCursor(Qt.WaitCursor)
        
        
    def setArrowCursor(self):
        QApplication.instance().setOverrideCursor(Qt.ArrowCursor)


    """ Take current project type changed """

    def change_project_type(self, widget):
        self.project_type_selected = utils_giswater.getWidgetText(self.dlg_readsql, widget)
        self.folderSoftware = self.sql_dir + os.sep + self.project_type_selected + os.sep

        
    """ Info basic """
    def info_show_info(self):
        """ Button 36: Info show info, open giswater and visit web page """

        # Create form
        self.dlg_info = InfoShowInfo()
        self.load_settings(self.dlg_info)

        # Get Plugin, Giswater, PostgreSQL and Postgis version
        postgresql_version = self.controller.get_postgresql_version()
        postgis_version = self.controller.get_postgis_version()
        plugin_version = self.get_plugin_version()
        (giswater_file_path, giswater_build_version) = self.get_giswater_jar()  #@UnusedVariable
        project_version = self.controller.get_project_version()

        message = ("Plugin version:     " + str(plugin_version) + "\n"
                   "Project version:    " + str(project_version) + "\n"                    
                   "Giswater version:   " + str(giswater_build_version) + "\n" 
                   "PostgreSQL version: " + str(postgresql_version) + "\n" 
                   "Postgis version:    " + str(postgis_version))
        utils_giswater.setWidgetText(self.dlg_info, self.dlg_info.txt_info, message)

        # Set signals
        self.dlg_info.btn_open_giswater.clicked.connect(self.open_giswater)
        self.dlg_info.btn_open_web.clicked.connect(partial(self.open_web_browser, self.dlg_info, None))
        self.dlg_info.btn_close.clicked.connect(partial(self.close_dialog, self.dlg_info))

        # Open dialog
        self.open_dialog(self.dlg_info, maximize_button=False)

        
    def open_giswater(self):
        """ Open giswater.jar with last opened .gsw file """

        if 'nt' in sys.builtin_module_names:
            self.execute_giswater("ed_giswater_jar")
        else:
            self.controller.show_info("Function not supported in this Operating System")
            
            
