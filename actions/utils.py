"""
This file is part of Giswater 3.1
The program is free software: you can redistribute it and/or modify it under the terms of the GNU 
General Public License as published by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
from PyQt4.QtCore import QDate
from PyQt4.QtGui import QDateEdit, QFileDialog, QStandardItem, QStandardItemModel, QCheckBox, QDoubleSpinBox

import os
import csv
import operator
from functools import partial
from encodings.aliases import aliases

import utils_giswater
from giswater.actions.parent import ParentAction
from giswater.actions.manage_visit import ManageVisit
from giswater.ui_manager import ConfigUtils
from giswater.ui_manager import Toolbox
from giswater.ui_manager import Csv2Pg


class Utils(ParentAction):

    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class to control toolbar 'om_ws' """
        ParentAction.__init__(self, iface, settings, controller, plugin_dir)
        self.manage_visit = ManageVisit(iface, settings, controller, plugin_dir)


    def set_project_type(self, project_type):
        self.project_type = project_type


    def utils_arc_topo_repair(self):
        """ Button 19: Topology repair """

        # Create dialog to check wich topology functions we want to execute
        self.dlg_toolbox = Toolbox()
        self.load_settings(self.dlg_toolbox)
        project_type = self.controller.get_project_type()

        # Remove tab WS or UD
        if project_type == 'ws':
            utils_giswater.remove_tab_by_tabName(self.dlg_toolbox.tabWidget_3, "tab_edit_ud")
        elif project_type == 'ud':
            utils_giswater.remove_tab_by_tabName(self.dlg_toolbox.tabWidget_3, "tab_edit_ws")

        role_admin = self.controller.check_role_user("role_admin")
        role_master = self.controller.check_role_user("role_master")
        role_edit = self.controller.check_role_user("role_edit")
        
        # Manage user 'postgres'
        if self.controller.user == 'postgres' or self.controller.user == 'gisadmin':
            role_admin = True

        # Remove tab for role
        if role_admin:
            pass
        elif role_master:
            utils_giswater.remove_tab_by_tabName(self.dlg_toolbox.Admin, "tab_admin")
        elif role_edit:
            utils_giswater.remove_tab_by_tabName(self.dlg_toolbox.Admin, "tab_admin")
            utils_giswater.remove_tab_by_tabName(self.dlg_toolbox.Admin, "tab_master")

        # Set signals
        self.dlg_toolbox.btn_accept.clicked.connect(self.utils_arc_topo_repair_accept)
        self.dlg_toolbox.btn_cancel.clicked.connect(partial(self.close_dialog, self.dlg_toolbox))
        self.dlg_toolbox.rejected.connect(partial(self.close_dialog, self.dlg_toolbox))

        # Open dialog
        self.open_dialog(self.dlg_toolbox, dlg_name='toolbox', maximize_button=False)  
        

    def utils_arc_topo_repair_accept(self):
        """ Button 19: Executes functions that are selected """

        # Delete previous values for current user
        tablename = "selector_audit"        
        sql = ("DELETE FROM " + self.schema_name + "." + tablename + ""
               " WHERE cur_user = current_user;\n")
        self.controller.execute_sql(sql)
        
        # Edit - Utils - Check project / data
        if self.dlg_toolbox.check_qgis_project.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_audit_check_project(1);")
            self.controller.execute_sql(sql)
            self.insert_selector_audit(1)
        if self.dlg_toolbox.check_user_vdefault_parameters.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_audit_check_project(19);")
            self.controller.execute_sql(sql)
            self.insert_selector_audit(19)

        # Edit - Utils - Topology Builder
        if self.dlg_toolbox.check_create_nodes_from_arcs.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_built_nodefromarc();")
            self.controller.execute_sql(sql)

        # Edit - Utils - Topology review
        if self.dlg_toolbox.check_node_orphan.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_anl_node_orphan();")
            self.controller.execute_sql(sql)
        if self.dlg_toolbox.check_node_duplicated.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_anl_node_duplicated();")
            self.controller.execute_sql(sql)
        if self.dlg_toolbox.check_topology_coherence.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_anl_node_topological_consistency();")
            self.controller.execute_sql(sql)
        if self.dlg_toolbox.check_arc_same_start_end.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_anl_arc_same_startend();")
            self.controller.execute_sql(sql)
        if self.dlg_toolbox.check_arcs_without_nodes_start_end.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_anl_arc_no_startend_node();")
            self.controller.execute_sql(sql)
        if self.dlg_toolbox.check_connec_duplicated.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_anl_connec_duplicated();")
            self.controller.execute_sql(sql)
        if self.dlg_toolbox.check_mincut_data.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_edit_audit_check_data(25);")
            self.controller.execute_sql(sql)
            self.insert_selector_audit(25)
        if self.dlg_toolbox.check_profile_tool_data.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_edit_audit_check_data(26);")
            self.controller.execute_sql(sql)
            self.insert_selector_audit(26)

        # Edit - Utils - Topology Repair
        if self.dlg_toolbox.check_arc_searchnodes.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_repair_arc_searchnodes();")
            self.controller.execute_sql(sql)

        # Edit - UD
        if self.dlg_toolbox.check_node_sink.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_anl_node_sink();")
            self.controller.execute_sql(sql)
        if self.dlg_toolbox.check_node_flow_regulator.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_anl_node_flowregulator();")
            self.controller.execute_sql(sql)
        if self.dlg_toolbox.check_node_exit_upper_node_entry.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_anl_node_exit_upper_intro();")
            self.controller.execute_sql(sql)
        if self.dlg_toolbox.check_arc_intersection_without_node.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_anl_arc_intersection();")
            self.controller.execute_sql(sql)
        if self.dlg_toolbox.check_inverted_arcs.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_anl_arc_inverted();")
            self.controller.execute_sql(sql)
            
        # Master - Prices
        if self.dlg_toolbox.check_reconstruction_price.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_plan_audit_check_data(15);")
            self.controller.execute_sql(sql)
            self.insert_selector_audit(15)
        if self.dlg_toolbox.check_rehabilitation_price.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_plan_audit_check_data(16);")
            self.controller.execute_sql(sql)
            self.insert_selector_audit(16)

        # Master - Advanced_topology_review
        if self.dlg_toolbox.check_arc_multi_psector.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_plan_anl_topology(20);")
            self.controller.execute_sql(sql)
            self.insert_selector_audit(20)
        if self.dlg_toolbox.check_node_multi_psector.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_plan_anl_topology(21);")
            self.controller.execute_sql(sql)
            self.insert_selector_audit(21)
        if self.dlg_toolbox.check_node_orphan_2.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_plan_anl_topology(22);")
            self.controller.execute_sql(sql)
            self.insert_selector_audit(22)
        if self.dlg_toolbox.check_node_duplicated_2.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_plan_anl_topology(23);")
            self.controller.execute_sql(sql)
            self.insert_selector_audit(23)
        if self.dlg_toolbox.check_arcs_without_nodes_start_end_2.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_plan_anl_topology(24);")
            self.controller.execute_sql(sql)
            self.insert_selector_audit(24)

        # Admin - Check data
        if self.dlg_toolbox.check_schema_data.isChecked():
            sql = ("SELECT "+self.schema_name+".gw_fct_audit_check_project(2);")
            self.controller.execute_sql(sql)
            self.insert_selector_audit(2)

        # Close the dialog
        self.close_dialog(self.dlg_toolbox)

        # Refresh map canvas
        self.refresh_map_canvas()


    def utils_config(self):
        """ Button 99: Config utils """

        # Create the dialog and signals
        self.dlg_config = ConfigUtils()
        self.load_settings(self.dlg_config)

        self.dlg_config.btn_accept.clicked.connect(self.utils_config_accept)
        self.dlg_config.btn_cancel.clicked.connect(partial(self.close_dialog, self.dlg_config))
        self.dlg_config.rejected.connect(partial(self.save_settings, self.dlg_config))
        self.project_type = self.controller.get_project_type()

        # Manage roles
        role_admin = self.controller.check_role_user("role_admin")
        role_master = self.controller.check_role_user("role_master")
        role_epa = self.controller.check_role_user("role_epa")
        role_edit = self.controller.check_role_user("role_edit")
        role_om = self.controller.check_role_user("role_om")
        role_basic = self.controller.check_role_user("role_basic")

        # Manage user 'postgres'
        if self.controller.user == 'postgres' or self.controller.user == 'gisadmin':
            role_admin = True

        if role_admin:
            pass
        elif role_master:
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_admin")
        elif role_epa:
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_master")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_admin")
        elif role_edit:
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_epa")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_master")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_admin")
        elif role_om:
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_edit")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_cad")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_epa")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_master")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_admin")
        elif role_basic:
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_om")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_edit")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_cad")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_epa")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_master")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_admin")

        # Hide empty tabs
        utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_basic")
        utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_config_epa, "tab_epa_utils")
        utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_config_epa, "tab_epa_ws")
        utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_config_epa, "tab_27")
        utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_config_epa, "tab_28")
        utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_config_admin, "tab_2")

        # Fill combo boxes of the form and related events
        self.dlg_config.exploitation_vdefault.currentIndexChanged.connect(partial(self.filter_dma_vdefault))
        self.dlg_config.state_vdefault.currentIndexChanged.connect(partial(self.filter_statetype_vdefault))
        self.dlg_config.elementtype_vdefault.currentIndexChanged.connect(partial(self.filter_elementcat_vdefault))

        # Set signals check box

        self.dlg_config.chk_elementcat_vdefault.stateChanged.connect(partial(
            self.check_child_to_parent, self.dlg_config.chk_elementcat_vdefault, self.dlg_config.chk_elementtype_vdefault))
        self.dlg_config.chk_elementtype_vdefault.stateChanged.connect(partial(
            self.check_parent_to_child, self.dlg_config.chk_elementtype_vdefault, self.dlg_config.chk_elementcat_vdefault))
        self.dlg_config.chk_statetype_vdefault.stateChanged.connect(partial(
            self.check_child_to_parent, self.dlg_config.chk_statetype_vdefault, self.dlg_config.chk_state_vdefault))
        self.dlg_config.chk_state_vdefault.stateChanged.connect(partial(
            self.check_parent_to_child, self.dlg_config.chk_state_vdefault, self.dlg_config.chk_statetype_vdefault))

        # Populate General combo boxes
        # Om

        # Utils
        sql = "SELECT id, name FROM " + self.schema_name + ".om_visit_cat ORDER BY name"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.visitcat_vdefault, rows, 1)
        sql = "SELECT DISTINCT(id), id FROM " + self.schema_name + ".om_visit_parameter_type ORDER BY id"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.om_param_type_vdefault, rows, 1)
        self.populate_cmb_templates(self.dlg_config.composer_om_vdefault)

        # Edit
        sql = "SELECT DISTINCT(id), name FROM " + self.schema_name + ".value_state ORDER BY name"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.state_vdefault, rows, 1)
        sql = ("SELECT DISTINCT(id), name FROM " + self.schema_name + ".value_state_type "
               "WHERE state = '" + str(utils_giswater.get_item_data(self.dlg_config, self.dlg_config.state_vdefault)) + "'")
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.statetype_vdefault, rows, 1)
        sql = "SELECT id, name FROM " + self.schema_name + ".value_state_type WHERE state=0 ORDER BY name"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.statetype_end_vdefault, rows, 1)
        sql = "SELECT id, id FROM " + self.schema_name + ".cat_work ORDER BY id"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.workcat_vdefault, rows, 1)
        sql = "SELECT id, id FROM " + self.schema_name + ".value_verified ORDER BY id"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.verified_vdefault, rows, 1)
        sql = "SELECT id, id FROM " + self.schema_name + ".cat_arc ORDER BY id"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.arccat_vdefault, rows, 1)
        sql = "SELECT id, id FROM " + self.schema_name + ".cat_node ORDER BY id"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.nodecat_vdefault, rows, 1)
        sql = "SELECT id, id FROM " + self.schema_name + ".cat_connec ORDER BY id"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.connecat_vdefault, rows, 1)
        sql = "SELECT DISTINCT(elementtype_id), elementtype_id FROM " + self.schema_name + ".cat_element ORDER BY elementtype_id"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.elementtype_vdefault, rows, 1)
        sql = ("SELECT id, id FROM " + self.schema_name + ".cat_element "
               " WHERE elementtype_id = '" + str(utils_giswater.get_item_data(self.dlg_config, self.dlg_config.elementtype_vdefault)) + "'")
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.elementcat_vdefault, rows, 1)
        sql = "SELECT expl_id, name FROM " + self.schema_name + ".exploitation ORDER BY name"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.exploitation_vdefault, rows, 1)
        sql = "SELECT DISTINCT(muni_id),name FROM " + self.schema_name + ".ext_municipality ORDER BY name"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.municipality_vdefault, rows, 1)
        sql = "SELECT sector_id, name FROM " + self.schema_name + ".sector ORDER BY name"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.sector_vdefault, rows, 1)
        sql = "SELECT DISTINCT(id), id FROM " + self.schema_name + ".cat_pavement ORDER BY id"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.pavementcat_vdefault, rows, 1)
        sql = "SELECT DISTINCT(id), id FROM " + self.schema_name + ".cat_soil ORDER BY id"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.soilcat_vdefault, rows, 1)
        sql = ("SELECT value FROM " + self.schema_name + ".config_param_user "
               " WHERE cur_user = current_user AND parameter = 'dim_tooltip'")
        row = self.controller.get_row(sql)
        if row:
            utils_giswater.setChecked(self.dlg_config, self.dlg_config.chk_dim_tooltip, row)
        sql = ("SELECT value FROM " + self.schema_name + ".config_param_user "
               " WHERE cur_user = current_user AND parameter = 'edit_arc_division_dsbl'")
        row = self.controller.get_row(sql)
        if row:
            utils_giswater.setChecked(self.dlg_config, self.dlg_config.chk_edit_arc_division_dsbl, row)

        sql = ("SELECT value FROM " + self.schema_name + ".config_param_user "
               " WHERE cur_user = current_user AND parameter = 'cf_keep_opened_edition'")
        row = self.controller.get_row(sql)
        if row:
            utils_giswater.setChecked(self.dlg_config, self.dlg_config.chk_cf_keep_opened_edition, row)

        sql = ("SELECT DISTINCT(dma_id),name FROM " + self.schema_name + ".dma"
               " WHERE expl_id = '" + str(utils_giswater.get_item_data(self.dlg_config, self.dlg_config.exploitation_vdefault, 0)) + "'")
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.dma_vdefault, rows, 1)

        layers = self.iface.mapCanvas().layers()
        layers_list = []
        for layer in layers:
            layers_list.append(str(layer.name()))
        layers_list = sorted(layers_list, key=operator.itemgetter(0))
        utils_giswater.fillComboBoxList(self.dlg_config, "cad_tools_base_layer_vdefault_1", layers_list, False)

        # MasterPlan
        sql = "SELECT psector_id, name FROM" + self.schema_name + ".plan_psector ORDER BY name"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.psector_vdefault, rows, 1)
        sql = "SELECT id, name FROM" + self.schema_name + ".value_state_type WHERE state=2"
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.statetype_plan_vdefault, rows, 1)
        sql = ("SELECT value FROM " + self.schema_name + ".config_param_user "
               " WHERE cur_user = current_user AND parameter = 'plan_arc_vdivision_dsbl'")
        row = self.controller.get_row(sql)
        if row:
            utils_giswater.setChecked(self.dlg_config, self.dlg_config.chk_plan_arc_vdivision_dsbl, row)
        self.populate_cmb_templates(self.dlg_config.composer_plan_vdefault)

        if self.controller.get_project_type() == 'ws':

            self.dlg_config.exploitation_vdefault.currentIndexChanged.connect(partial(self.filter_presszone_vdefault))
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_config_edit, "tab_edit_ud")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tabWidget, "tab_epa")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_config_epa, "tab_epa_ud")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_admin_topology, "tab_admin_topology_ud")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_admin_review, "tab_admin_review_ud")

            # Edit WS
            self.populate_combo_ws(self.dlg_config.wtpcat_vdefault, "WTP")
            self.populate_combo_ws(self.dlg_config.hydrantcat_vdefault, "HYDRANT")
            self.populate_combo_ws(self.dlg_config.filtercat_vdefault, "FILTER")
            self.populate_combo_ws(self.dlg_config.pumpcat_vdefault, "PUMP")
            self.populate_combo_ws(self.dlg_config.waterwellcat_vdefault, "WATERWELL")
            self.populate_combo_ws(self.dlg_config.metercat_vdefault, "METER")
            self.populate_combo_ws(self.dlg_config.tankcat_vdefault, "TANK")
            self.populate_combo_ws(self.dlg_config.manholecat_vdefault, "MANHOLE")
            self.populate_combo_ws(self.dlg_config.valvecat_vdefault, "VALVE")
            self.populate_combo_ws(self.dlg_config.registercat_vdefault, "REGISTER")
            self.populate_combo_ws(self.dlg_config.sourcecat_vdefault, "SOURCE")
            self.populate_combo_ws(self.dlg_config.junctioncat_vdefault, "JUNCTION")
            self.populate_combo_ws(self.dlg_config.expansiontankcat_vdefault, "EXPANSIONTANK")
            self.populate_combo_ws(self.dlg_config.netwjoincat_vdefault, "NETWJOIN")
            self.populate_combo_ws(self.dlg_config.reductioncat_vdefault, "REDUCTION")
            self.populate_combo_ws(self.dlg_config.netelementcat_vdefault, "NETELEMENT")
            self.populate_combo_ws(self.dlg_config.netsamplepointcat_vdefault, "NETSAMPLEPOINT")
            self.populate_combo_ws(self.dlg_config.flexunioncat_vdefault, "FLEXUNION")

            sql = ("SELECT cat_arc.id, cat_arc.id FROM " + self.schema_name + ".cat_arc"
                   " INNER JOIN " + self.schema_name + ".arc_type ON cat_arc.arctype_id = arc_type.id"
                   " WHERE arc_type.type = 'PIPE'")
            rows = self.controller.get_rows(sql)
            utils_giswater.set_item_data(self.dlg_config.pipecat_vdefault, rows, 1)
            sql = ("SELECT cat_connec.id, cat_connec.id FROM " + self.schema_name + ".cat_connec"
                   " INNER JOIN " + self.schema_name + ".connec_type ON cat_connec.connectype_id = connec_type.id"
                   " WHERE connec_type.type = 'WJOIN'")
            rows = self.controller.get_rows(sql)
            utils_giswater.set_item_data(self.dlg_config.wjoincat_vdefault, rows, 1)
            sql = ("SELECT cat_connec.id, cat_connec.id FROM " + self.schema_name + ".cat_connec"
                   " INNER JOIN " + self.schema_name + ".connec_type ON cat_connec.connectype_id = connec_type.id"
                   " WHERE connec_type.type = 'GREENTAP'")
            rows = self.controller.get_rows(sql)
            utils_giswater.set_item_data(self.dlg_config.greentapcat_vdefault, rows, 1)
            sql = ("SELECT cat_connec.id, cat_connec.id FROM " + self.schema_name + ".cat_connec"
                    " INNER JOIN " + self.schema_name + ".connec_type ON cat_connec.connectype_id = connec_type.id"
                    " WHERE connec_type.type = 'FOUNTAIN'")
            rows = self.controller.get_rows(sql)
            utils_giswater.set_item_data(self.dlg_config.fountaincat_vdefault, rows, 1)
            sql = ("SELECT cat_connec.id, cat_connec.id FROM " + self.schema_name + ".cat_connec"
                    " INNER JOIN " + self.schema_name + ".connec_type ON cat_connec.connectype_id = connec_type.id"
                    " WHERE connec_type.type = 'TAP'")
            rows = self.controller.get_rows(sql)
            utils_giswater.set_item_data(self.dlg_config.tapcat_vdefault, rows, 1)
            sql = ("SELECT DISTINCT(id), id FROM " + self.schema_name + ".cat_presszone"
                   " WHERE expl_id = '" + str(utils_giswater.get_item_data(self.dlg_config, self.dlg_config.exploitation_vdefault, 0)) + "'")
            rows = self.controller.get_rows(sql)
            utils_giswater.set_item_data(self.dlg_config.presszone_vdefault, rows, 1)


        elif self.controller.get_project_type() == 'ud':

            utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_config_edit, "tab_edit_ws")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_config_epa, "tab_epa_ws")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_admin_topology, "tab_admin_topology_ws")
            utils_giswater.remove_tab_by_tabName(self.dlg_config.tab_admin_review, "tab_admin_review_ws")

            # Epa
            sql = "SELECT id, id FROM" + self.schema_name + ".inp_typevalue_outfall"
            rows = self.controller.get_rows(sql)
            utils_giswater.set_item_data(self.dlg_config.epa_outfall_type_vdefault, rows, 1)

            # Edit UD
            sql = "SELECT id, id FROM " + self.schema_name + ".node_type ORDER BY id"
            rows = self.controller.get_rows(sql)
            utils_giswater.set_item_data(self.dlg_config.nodetype_vdefault, rows, 1)
            sql = "SELECT id, id FROM " + self.schema_name + ".arc_type ORDER BY id"
            rows = self.controller.get_rows(sql)
            utils_giswater.set_item_data(self.dlg_config.arctype_vdefault, rows, 1)
            sql = "SELECT id, id FROM " + self.schema_name + ".connec_type ORDER BY id"
            rows = self.controller.get_rows(sql)
            utils_giswater.set_item_data(self.dlg_config.connectype_vdefault, rows, False)
            sql = "SELECT id, id FROM " + self.schema_name + ".cat_grate ORDER BY id"
            rows = self.controller.get_rows(sql)
            utils_giswater.set_item_data(self.dlg_config.gratecat_vdefault, rows, False)

        # Get current values from 'config_param_user'
        sql = ("SELECT parameter, value FROM " + self.schema_name + ".config_param_user"
               " WHERE cur_user = current_user")
        rows = self.controller.get_rows(sql)
        if rows:
            for row in rows:
                widget = utils_giswater.getWidget(self.dlg_config, str(row[0]))
                if widget is not None:
                    if type(widget) == QDateEdit:
                        date = QDate.fromString(row[1], 'yyyy-MM-dd')
                        utils_giswater.setCalendarDate(self.dlg_config, widget, date)
                    else:
                        if widget.objectName() == 'cad_tools_base_layer_vdefault_1':
                            utils_giswater.setWidgetText(self.dlg_config, str(row[0]), str(row[1]))
                        elif widget.objectName() == 'composer_plan_vdefault' or widget.objectName() == 'composer_om_vdefault':
                            utils_giswater.set_combo_itemData(widget, row[1], 1)
                        elif type(widget) == QDoubleSpinBox:
                            utils_giswater.setWidgetText(self.dlg_config, str(row[0]), str(row[1]))
                        else:
                            utils_giswater.set_combo_itemData(widget, row[1], 0)
                    utils_giswater.setChecked(self.dlg_config, "chk_" + str(row[0]), True)


        # Get current values from 'config_param_system'
        sql = ("SELECT parameter, value FROM " + self.schema_name + ".config_param_system")
        rows = self.controller.get_rows(sql)
        if rows:
            for row in rows:
                utils_giswater.setWidgetText(self.dlg_config, str(row[0]), str(row[1]))
                utils_giswater.setChecked(self.dlg_config, "chk_" + str(row[0]), True)

        # Get columns name in order of the table
        sql = ("SELECT column_name FROM information_schema.columns"
               " WHERE table_name = '" + "config'"
               " AND table_schema = '" + self.schema_name.replace('"', '') + "'"
               " ORDER BY ordinal_position")
        column_name = self.controller.get_rows(sql)
        sql = ("SELECT * FROM " + self.schema_name + ".config")
        row_config = self.controller.get_row(sql)
        for row in column_name:
            widget_name = str(row[0])
            widget = utils_giswater.getWidget(self.dlg_config, widget_name)
            if widget:
                if type(widget) is QDoubleSpinBox:
                    if row_config[row[0]]:
                        utils_giswater.setWidgetText(self.dlg_config, widget, str(row_config[row[0]]))
                        utils_giswater.setChecked(self.dlg_config, widget_name + "_control", True)
                    else:
                        utils_giswater.setChecked(self.dlg_config, widget_name + "_control", False)
                elif type(widget) is QCheckBox:
                    if row_config[row[0]]:
                        utils_giswater.setChecked(self.dlg_config, widget, True)
                    else:
                        utils_giswater.setChecked(self.dlg_config, widget, False)

        # Open dialog
        self.open_dialog(self.dlg_config, maximize_button=False)


    def utils_config_accept(self):

        # Edit - Utils
        self.manage_config_param_user("state_vdefault")
        self.manage_config_param_user("statetype_vdefault")
        self.manage_config_param_user("statetype_end_vdefault")
        self.manage_config_param_user("workcat_vdefault")
        self.manage_config_param_user("verified_vdefault")
        self.manage_config_param_user("builtdate_vdefault")
        self.manage_config_param_user("enddate_vdefault")
        self.manage_config_param_user("arccat_vdefault")
        self.manage_config_param_user("nodecat_vdefault")
        self.manage_config_param_user("connecat_vdefault")
        self.manage_config_param_user("elementtype_vdefault")
        self.manage_config_param_user("elementcat_vdefault")
        self.manage_config_param_user("exploitation_vdefault")
        self.manage_config_param_user("municipality_vdefault")
        self.manage_config_param_user("sector_vdefault")
        self.manage_config_param_user("pavementcat_vdefault")
        self.manage_config_param_user("soilcat_vdefault")
        self.manage_config_param_user("dma_vdefault")
        self.manage_config_param_user("dim_tooltip", True)
        self.manage_config_param_user("edit_arc_division_dsbl", True)
        self.manage_config_param_user("cf_keep_opened_edition", True)
        self.manage_config_param_user("plan_arc_vdivision_dsbl", True)
        self.manage_config_param_user("cad_tools_base_layer_vdefault_1")

        # MasterPlan
        self.manage_config_param_user("psector_vdefault")
        self.manage_config_param_user("statetype_plan_vdefault")
        self.manage_config_param_user("psector_scale_tol")
        self.manage_config_param_user("psector_rotation_tol")
        self.manage_config_param_user("psector_gexpenses_tol")
        self.manage_config_param_user("psector_vat_tol")
        self.manage_config_param_user("psector_other_tol")
        self.manage_config_param_user("psector_measurament_tol")
        self.manage_config_param_user("composer_plan_vdefault")

        # OM
        self.manage_config_param_user("visitcat_vdefault")
        self.manage_config_param_user("om_param_type_vdefault")
        self.manage_config_param_user("composer_om_vdefault")

        # Admin - Topology - Utils
        widget_list = self.dlg_config.tab_admin_topology.findChildren(QDoubleSpinBox)
        for widget in widget_list:
            self.update_config(widget.objectName())

        # Manage QCheckBoxes
        self.update_config("arc_searchnodes_control")
        self.update_config("samenode_init_end_control")
        self.update_config("node_proximity_control")
        self.update_config("connec_proximity_control")
        self.update_config("insert_double_geometry")
        self.update_config("orphannode_delete")
        self.update_config("nodeinsert_arcendpoint")
        self.manage_config_param_system("state_topo", True)
        self.manage_config_param_system("link_search_buffer")
        self.upsert_config_param_system("proximity_buffer")

        # Admin - Analysis
        self.update_config("node_duplicated_tolerance")
        self.update_config("connec_duplicated_tolerance")

        if self.controller.get_project_type() == 'ws':

            # Edit - WS
            self.manage_config_param_user("presszone_vdefault")
            self.manage_config_param_user("wtpcat_vdefault")
            self.manage_config_param_user("netsamplepointcat_vdefault")
            self.manage_config_param_user("netelementcat_vdefault")
            self.manage_config_param_user("flexunioncat_vdefault")
            self.manage_config_param_user("tankcat_vdefault")
            self.manage_config_param_user("hydrantcat_vdefault")
            self.manage_config_param_user("junctioncat_vdefault")
            self.manage_config_param_user("pumpcat_vdefault")
            self.manage_config_param_user("reductioncat_vdefault")
            self.manage_config_param_user("valvecat_vdefault")
            self.manage_config_param_user("manholecat_vdefault")
            self.manage_config_param_user("metercat_vdefault")
            self.manage_config_param_user("sourcecat_vdefault")
            self.manage_config_param_user("waterwellcat_vdefault")
            self.manage_config_param_user("filtercat_vdefault")
            self.manage_config_param_user("registercat_vdefault")
            self.manage_config_param_user("netwjoincat_vdefault")
            self.manage_config_param_user("expansiontankcat_vdefault")
            self.manage_config_param_user("pipecat_vdefault")
            self.manage_config_param_user("wjoincat_vdefault")
            self.manage_config_param_user("greentapcat_vdefault")
            self.manage_config_param_user("fountaincat_vdefault")
            self.manage_config_param_user("tapcat_vdefault")

            # Admin - Review - WS
            self.manage_config_param_system("rev_nod_elev_tol")
            self.manage_config_param_system("rev_nod_depth_tol")

            # Admin - WS
            self.update_config("node2arc")

        elif self.controller.get_project_type() == 'ud':

            # Edit - UD
            if utils_giswater.isChecked(self.dlg_config, "chk_nodetype_vdefault"):
                sql = ("SELECT name FROM " + self.schema_name + ".value_state WHERE id::text = "
                       "(SELECT value FROM " + self.schema_name + ".config_param_user"
                       " WHERE cur_user = current_user AND parameter = 'exploitation_vdefault')::text")
                row = self.controller.get_row(sql)
                if row:
                    utils_giswater.setWidgetText(self.dlg_config, "exploitation_vdefault", str(row[0]))
                self.upsert_config_param_user("nodetype_vdefault")
            else:
                self.delete_config_param_user("nodetype_vdefault")
            self.manage_config_param_user("arctype_vdefault")
            self.manage_config_param_user("connectype_vdefault")
            self.manage_config_param_user("gratecat_vdefault")

            # Epa - UD
            self.manage_config_param_user("epa_outfall_type_vdefault")
            self.manage_config_param_user("epa_conduit_q0_tol")
            self.manage_config_param_user("epa_junction_y0_tol")
            self.manage_config_param_user("epa_rgage_scf_tol")

            # Admin - Review - UD
            self.manage_config_param_system("rev_arc_y1_tol")
            self.manage_config_param_system("rev_arc_y2_tol")
            self.manage_config_param_system("rev_arc_geom1_tol")
            self.manage_config_param_system("rev_arc_geom2_tol")
            self.manage_config_param_system("rev_nod_telev_tol")
            self.manage_config_param_system("rev_nod_ymax_tol")
            self.manage_config_param_system("rev_nod_geom1_tol")
            self.manage_config_param_system("rev_nod_geom2_tol")
            self.manage_config_param_system("rev_con_y1_tol")
            self.manage_config_param_system("rev_con_y2_tol")
            self.manage_config_param_system("rev_con_geom1_tol")
            self.manage_config_param_system("rev_con_geom2_tol")
            self.manage_config_param_system("rev_gul_topelev_tol")
            self.manage_config_param_system("rev_gul_ymax_tol")
            self.manage_config_param_system("rev_gul_sandbox_tol")
            self.manage_config_param_system("rev_gul_geom1_tol")
            self.manage_config_param_system("rev_gul_geom2_tol")
            self.manage_config_param_system("rev_gul_units_tol")

            # Admin - Topology - UD
            self.manage_config_param_system("slope_arc_direction", True)

        message = "Values has been updated"
        self.controller.show_info(message)
        self.close_dialog(self.dlg_config)


    def utils_import_csv(self):
        """ Button 83: Import CSV """

        self.dlg_csv = Csv2Pg()
        self.load_settings(self.dlg_csv)
        roles = self.controller.get_rolenames()

        temp_tablename = 'temp_csv2pg'
        self.populate_cmb_unicodes(self.dlg_csv.cmb_unicode_list)
        self.populate_combos(self.dlg_csv.cmb_import_type, 'id', 'name_i18n, csv_structure', 'sys_csv2pg_cat', roles, False)

        self.dlg_csv.lbl_info.setWordWrap(True)
        utils_giswater.setWidgetText(self.dlg_csv, self.dlg_csv.cmb_unicode_list, 'utf8')
        self.dlg_csv.rb_comma.setChecked(False)
        self.dlg_csv.rb_semicolon.setChecked(True)

        # Signals
        self.dlg_csv.btn_cancel.clicked.connect(partial(self.close_dialog, self.dlg_csv))
        self.dlg_csv.rejected.connect(partial(self.close_dialog, self.dlg_csv))
        self.dlg_csv.btn_accept.clicked.connect(partial(self.write_csv, self.dlg_csv, temp_tablename))
        self.dlg_csv.cmb_import_type.currentIndexChanged.connect(partial(self.update_info, self.dlg_csv))
        self.dlg_csv.cmb_import_type.currentIndexChanged.connect(partial(self.disable_import_label, self.dlg_csv))
        self.dlg_csv.btn_file_csv.clicked.connect(partial(self.select_file_csv))
        self.dlg_csv.cmb_unicode_list.currentIndexChanged.connect(partial(self.preview_csv, self.dlg_csv))
        self.dlg_csv.rb_comma.clicked.connect(partial(self.preview_csv, self.dlg_csv))
        self.dlg_csv.rb_semicolon.clicked.connect(partial(self.preview_csv, self.dlg_csv))
        self.disable_import_label(self.dlg_csv)
        self.load_settings_values()

        if str(utils_giswater.getWidgetText(self.dlg_csv, self.dlg_csv.txt_file_csv)) != 'null':
            self.preview_csv(self.dlg_csv)
        self.dlg_csv.progressBar.setVisible(False)

        # Open dialog
        self.open_dialog(self.dlg_csv, maximize_button=False)


    def disable_import_label(self, dialog):
        csv2pgcat_id_aux = utils_giswater.get_item_data(dialog, dialog.cmb_import_type, 0)
        if csv2pgcat_id_aux == 4:
            dialog.txt_import.setEnabled(False)
            dialog.txt_import.setReadOnly(True)
        else:
            dialog.txt_import.setEnabled(True)
            dialog.txt_import.setReadOnly(False)


    def populate_cmb_unicodes(self, combo):
        """ Populate combo with full list of codes """

        unicode_list = []
        for item in aliases.items():
            unicode_list.append(str(item[0]))
            sorted_list = sorted(unicode_list, key=str.lower)
        utils_giswater.set_autocompleter(combo, sorted_list)


    def update_info(self, dialog):
        """ Update the tag according to item selected from cmb_import_type """
        dialog.lbl_info.setText(utils_giswater.get_item_data(self.dlg_csv, self.dlg_csv.cmb_import_type, 2))


    def load_settings_values(self):
        """ Load QGIS settings related with csv options """

        cur_user = self.controller.get_current_user()
        utils_giswater.setWidgetText(self.dlg_csv, self.dlg_csv.txt_file_csv,
            self.controller.plugin_settings_value('Csv2Pg_txt_file_csv_' + cur_user))
        utils_giswater.setWidgetText(self.dlg_csv, self.dlg_csv.cmb_unicode_list,
            self.controller.plugin_settings_value('Csv2Pg_cmb_unicode_list_' + cur_user))
        if self.controller.plugin_settings_value('Csv2Pg_rb_comma_' + cur_user).title() == 'True':
            self.dlg_csv.rb_comma.setChecked(True)
        else:
            self.dlg_csv.rb_semicolon.setChecked(True)


    def save_settings_values(self):
        """ Save QGIS settings related with csv options """

        cur_user = self.controller.get_current_user()
        self.controller.plugin_settings_set_value("Csv2Pg_txt_file_csv_" + cur_user,
            utils_giswater.getWidgetText(self.dlg_csv, 'txt_file_csv'))
        self.controller.plugin_settings_set_value("Csv2Pg_cmb_unicode_list_" + cur_user,
            utils_giswater.getWidgetText(self.dlg_csv, 'cmb_unicode_list'))
        self.controller.plugin_settings_set_value("Csv2Pg_rb_comma_" + cur_user,
            bool(self.dlg_csv.rb_comma.isChecked()))
        self.controller.plugin_settings_set_value("Csv2Pg_rb_semicolon_" + cur_user,
            bool(self.dlg_csv.rb_semicolon.isChecked()))


    def validate_params(self, dialog):
        """ Validate if params are valids """

        label_aux = utils_giswater.getWidgetText(dialog, dialog.txt_import)
        path = self.get_path(dialog)
        self.preview_csv(dialog)
        if path is None or path == 'null':
            return False
        csv2pgcat_id_aux = utils_giswater.get_item_data(dialog, dialog.cmb_import_type, 0)
        if csv2pgcat_id_aux != 4:
            if label_aux is None or label_aux == 'null':
                message = "Please put a import label"
                self.controller.show_warning(message)
                return False

        return True


    def get_path(self, dialog):
        """ Take the file path if exist. AND if not exit ask it """

        path = utils_giswater.getWidgetText(dialog, dialog.txt_file_csv)
        if path is None or path == 'null' or not os.path.exists(path):
            message = "Please choose a valid path"
            self.controller.show_warning(message)
            return None
        if path.find('.csv') == -1:
            message = "Please choose a csv file"
            self.controller.show_warning(message)
            return None

        return path


    def get_delimiter(self, dialog):

        delimiter = ';'
        if dialog.rb_semicolon.isChecked():
            delimiter = ';'
        elif dialog.rb_comma.isChecked():
            delimiter = ','
        return delimiter


    def preview_csv(self, dialog):
        """ Show current file in QTableView acorrding to selected delimiter and unicode """

        path = self.get_path(dialog)
        if path is None:
            return

        delimiter = self.get_delimiter(dialog)
        model = QStandardItemModel()
        _unicode = utils_giswater.getWidgetText(dialog, dialog.cmb_unicode_list)
        dialog.tbl_csv.setModel(model)
        dialog.tbl_csv.horizontalHeader().setStretchLastSection(True)

        try:
            with open(path, "rb") as file_input:
                rows = csv.reader(file_input, delimiter=delimiter)
                for row in rows:
                    unicode_row = [x.decode(str(_unicode)) for x in row]
                    items = [QStandardItem(field)for field in unicode_row]
                    model.appendRow(items)
        except Exception as e:
            self.controller.show_warning(str(e))


    def delete_table_csv(self, temp_tablename, csv2pgcat_id_aux):
        """ Delete records from temp_csv2pg for current user and selected cat """
        sql = ("DELETE FROM " + self.schema_name + "." + temp_tablename + " "
               " WHERE csv2pgcat_id = '" + str(csv2pgcat_id_aux) + "' AND user_name = current_user")
        self.controller.execute_sql(sql, log_sql=True)


    def write_csv(self, dialog, temp_tablename):
        """ Write csv in postgre and call gw_fct_utils_csv2pg function """

        if not self.validate_params(dialog):
            return

        csv2pgcat_id_aux = utils_giswater.get_item_data(dialog, dialog.cmb_import_type, 0)
        self.delete_table_csv(temp_tablename, csv2pgcat_id_aux)
        path = utils_giswater.getWidgetText(dialog, dialog.txt_file_csv)
        label_aux = utils_giswater.getWidgetText(dialog, dialog.txt_import)
        delimiter = self.get_delimiter(dialog)
        _unicode = utils_giswater.getWidgetText(dialog, dialog.cmb_unicode_list)
        cabecera = True
        fields = "csv2pgcat_id, "
        progress = 0
        dialog.progressBar.setVisible(True)
        dialog.progressBar.setValue(progress)

        try:
            with open(path, 'rb') as csvfile:
                # counts rows in csvfile, using var "row_count" to do progresbar
                row_count = sum(1 for rows in csvfile)  #@UnusedVariable
                if row_count > 20:
                    row_count -= 20
                dialog.progressBar.setMaximum(row_count)  # -20 for see 100% complete progress
                csvfile.seek(0)  # Position the cursor at position 0 of the file
                reader = csv.reader(csvfile, delimiter=delimiter)
                for row in reader:
                    values = "'" + str(csv2pgcat_id_aux)+"', '"
                    progress += 1

                    for x in range(0, len(row)):
                        row[x] = row[x].replace("'", "''")
                    if cabecera:
                        for x in range(1, len(row)+1):
                            fields += 'csv' + str(x)+", "
                        cabecera = False
                        fields = fields[:-2]
                    else:
                        for value in row:
                            if len(value) != 0:
                                values += str(value.decode(str(_unicode))) + "', '"
                            else:
                                values = values[:-1]
                                values += "null, '"
                        values = values[:-3]
                        sql = ("INSERT INTO " + self.controller.schema_name + "." + temp_tablename + " ("
                               + str(fields) + ") VALUES (" + str(values) + ")")

                        status = self.controller.execute_sql(sql)
                        if not status:
                            return
                        dialog.progressBar.setValue(progress)

        except Exception as e:
            self.controller.show_warning(str(e))
            return

        sql = ("SELECT " + self.schema_name + ".gw_fct_utils_csv2pg("
               + str(csv2pgcat_id_aux) + ", '" + str(label_aux) + "')")
        status = self.controller.execute_sql(sql, log_sql=False)
        self.save_settings_values()
        if status:
            message = "Import has been satisfactory"
            self.controller.show_info_box(message)
            self.close_dialog(self.dlg_csv)
        else:
            message = "Import failed"
            self.controller.show_info_box(message)





    def populate_combos(self, combo, field_id, fields, table_name, roles, allow_nulls=True):

        if roles is None:
            return

        sql = ("SELECT DISTINCT(" + field_id + "), " + fields + ""
               " FROM " + self.schema_name + "." + table_name + ""
               " WHERE sys_role IN " + roles + "")
        rows = self.controller.get_rows(sql)
        if not rows:
            message = "You do not have permission to execute this application"
            self.dlg_csv.lbl_info.setText(self.controller.tr(message))
            self.dlg_csv.lbl_info.setStyleSheet("QLabel{color: red;}")
            self.dlg_csv.setEnabled(False)
            return

        combo.blockSignals(True)
        combo.clear()
        if allow_nulls:
            combo.addItem("", "")
        records_sorted = sorted(rows, key=operator.itemgetter(1))
        for record in records_sorted:
            combo.addItem(record[1], record)
        combo.blockSignals(False)

        self.update_info(self.dlg_csv)


    def select_file_csv(self):
        """ Select CSV file """

        file_csv = utils_giswater.getWidgetText(self.dlg_csv, 'txt_file_csv')
        # Set default value if necessary
        if file_csv is None or file_csv == '':
            file_csv = self.plugin_dir
        # Get directory of that file
        folder_path = os.path.dirname(file_csv)
        if not os.path.exists(folder_path):
            folder_path = os.path.dirname(__file__)
        os.chdir(folder_path)
        message = self.controller.tr("Select CSV file")
        file_csv = QFileDialog.getOpenFileName(None, message, "", '*.csv')
        self.dlg_csv.txt_file_csv.setText(file_csv)
        self.save_settings_values()
        self.preview_csv(self.dlg_csv)


    def populate_combo_ws(self, widget, node_type):


        sql = ("SELECT cat_node.id, cat_node.id FROM " + self.schema_name + ".cat_node"
               " INNER JOIN " + self.schema_name + ".node_type ON cat_node.nodetype_id = node_type.id"
               " WHERE node_type.type = '" + node_type + "'")
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(widget, rows, 1)


    def upsert_config_param_system(self, parameter,add_check=False):
        """ Insert or update value of @parameter in table 'config_param_user' with current_user control """

        if add_check:
            widget = utils_giswater.getWidget(self.dlg_config, 'chk_'+str(parameter))
        else:
            widget = utils_giswater.getWidget(self.dlg_config, parameter)

        if widget is None:
            message = "Widget not found"
            self.controller.log_info(message, parameter=parameter)
            return

        tablename = "config_param_system"
        sql = ("SELECT parameter FROM " + self.schema_name + "." + tablename + ""
               " WHERE parameter = '" + str(parameter) + "'")
        exist_param = self.controller.get_row(sql)
        sql = None
        if type(widget) == QDateEdit:
            _date = widget.dateTime().toString('yyyy-MM-dd')
            if exist_param:
                sql = ("UPDATE " + self.schema_name + "." + tablename + ""
                       " SET value = '" + str(_date) + "'"
                       " WHERE parameter = '" + parameter + "'")
            else:
                sql = ("INSERT INTO " + self.schema_name + "." + tablename + "(parameter, value)"
                       " VALUES ('" + parameter + "', '" + _date + "')")

        elif type(widget) == QCheckBox:
            value = utils_giswater.isChecked(self.dlg_config, widget)
            if exist_param:
                sql = ("UPDATE " + self.schema_name + "." + tablename + ""
                       " SET value = '" + str(value) + "'"
                       " WHERE parameter = '" + parameter + "'")
            else:
                sql = ("INSERT INTO " + self.schema_name + "." + tablename + "(parameter, value)"
                       " VALUES ('" + parameter + "', '" + str(value) + "')")

        else:
            value = utils_giswater.getWidgetText(self.dlg_config, widget)
            if value == "":
                return
            if value == 'null':
                value = "0.000"
            if exist_param:
                sql = "UPDATE " + self.schema_name + "." + tablename + " SET value = "
                if widget.objectName() == 'state_vdefault':
                    sql += ("(SELECT id FROM " + self.schema_name + ".value_state"
                            " WHERE name = '" + str(value) + "')"
                            " WHERE parameter = 'state_vdefault'")
                elif widget.objectName() == 'exploitation_vdefault':
                    sql += ("(SELECT expl_id FROM " + self.schema_name + ".exploitation"
                        " WHERE name = '" + str(value) + "')"
                        " WHERE parameter = 'exploitation_vdefault'")
                elif widget.objectName() == 'municipality_vdefault':
                    sql += ("(SELECT muni_id FROM " + self.schema_name + ".ext_municipality"
                            " WHERE name = '" + str(value) + "')"
                            " WHERE parameter = 'municipality_vdefault'")
                elif widget.objectName() == 'visitcat_vdefault':
                    sql += ("(SELECT id FROM " + self.schema_name + ".om_visit_cat"
                            " WHERE name = '" + str(value) + "')"
                            " WHERE parameter = 'visitcat_vdefault'")
                else:
                    sql += ("'" + str(value) + "' WHERE parameter = '" + parameter + "'")
            else:
                sql = "INSERT INTO " + self.schema_name + "." + tablename + "(parameter, value)"
                if widget.objectName() == 'state_vdefault':
                    sql += (" VALUES ('" + parameter + "',"
                            " (SELECT id FROM " + self.schema_name + ".value_state"
                            " WHERE name = '" + str(value) + "'))")
                elif widget.objectName() == 'exploitation_vdefault':
                    sql += (" VALUES ('" + parameter + "',"
                            " (SELECT expl_id FROM " + self.schema_name + ".exploitation"
                            " WHERE name = '" + str(utils_giswater.getWidgetText(self.dlg_config, widget)) + "'))")
                elif widget.objectName() == 'municipality_vdefault':
                    sql += (" VALUES ('" + parameter + "',"
                            " (SELECT muni_id FROM " + self.schema_name + ".ext_municipality"
                            " WHERE name = '" + str(value) + "'))")
                elif widget.objectName() == 'visitcat_vdefault':
                    sql += (" VALUES ('" + parameter + "',"
                            " (SELECT id FROM " + self.schema_name + ".om_visit_cat"
                            " WHERE name ='" + str(value) + "'))")
                else:
                    sql += (" VALUES ('" + parameter + "', '" + str(value) + "')")


        if sql:
            self.controller.execute_sql(sql)


    def update_config(self, columnname):
        """ Update value of @parameter in table 'config' """

        widget = utils_giswater.getWidget(self.dlg_config, columnname)
        if widget is None:
            message = "Widget not found"
            self.controller.log_info(message, parameter=columnname)
            return

        tablename = "config"
        if not self.controller.check_column(tablename, columnname):
            message = "Column not found"
            self.controller.log_info(message, parameter=columnname)
            return

        if type(widget) is QDoubleSpinBox:
            set_value = " = 0.000"
            value = utils_giswater.getWidgetText(self.dlg_config, columnname)
            if value == 'null':
                set_value = " = 0.000"
            elif value:
                set_value = " = '" + str(value) + "'"
            else:
                return

        elif type(widget) is QCheckBox:
            if utils_giswater.isChecked(self.dlg_config, widget):
                set_value = " = True"
            else:
                set_value = " = False"

        if columnname == "node_duplicated_tolerance" and utils_giswater.isChecked(self.dlg_config, str(columnname) + "_control") == False:
            set_value = " = 0.000"
        elif columnname == "connec_duplicated_tolerance" and utils_giswater.isChecked(self.dlg_config, str(columnname) + "_control") == False:
            set_value = " = 0.000"
        elif columnname == "node2arc" and utils_giswater.isChecked(self.dlg_config, str(columnname) + "_control") == False:
            set_value = " = 0.000"

        sql = ("UPDATE " + self.schema_name + "." + tablename + ""
               " SET " + columnname + set_value)
        self.controller.execute_sql(sql)


    def upsert_config_param_user(self, parameter, add_check=False):
        """ Insert or update value of @parameter in table 'config_param_user' with current_user control """

        if add_check:
            widget = utils_giswater.getWidget(self.dlg_config, 'chk_' + str(parameter))
        else:
            widget = utils_giswater.getWidget(self.dlg_config, parameter)

        if widget is None:
            message = "Widget not found"
            self.controller.log_info(message, parameter=parameter)
            return

        tablename = "config_param_user"
        sql = ("SELECT parameter FROM " + self.schema_name + "." + tablename + ""
               " WHERE cur_user = current_user AND parameter = '" + str(parameter) + "'")
        exist_param = self.controller.get_row(sql)

        sql = None
        if type(widget) == QDateEdit:
            _date = widget.dateTime().toString('yyyy-MM-dd')
            if exist_param:
                sql = ("UPDATE " + self.schema_name + "." + tablename + ""
                       " SET value = '" + str(_date) + "'"
                       " WHERE parameter = '" + parameter + "' AND cur_user = current_user")
            else:
                sql = ("INSERT INTO " + self.schema_name + "." + tablename + "(parameter, value, cur_user)"
                       " VALUES ('" + parameter + "', '" + _date + "', current_user)")

        elif type(widget) == QCheckBox:
            value = utils_giswater.isChecked(self.dlg_config, widget)
            if exist_param:
                sql = ("UPDATE " + self.schema_name + "." + tablename + ""
                       " SET value = '" + str(value) + "'"
                       " WHERE parameter = '" + parameter + "' AND cur_user = current_user")
            else:
                sql = ("INSERT INTO " + self.schema_name + "." + tablename + "(parameter, value, cur_user)"
                       " VALUES ('" + parameter + "', '" + str(value) + "', current_user)")

        else:
            value = utils_giswater.getWidgetText(self.dlg_config, widget)
            if value == '':
                return
            if value == 'null':
                value = "0.000"
            if exist_param:
                sql = "UPDATE " + self.schema_name + "." + tablename + " SET value = "
                if widget.objectName() == 'composer_plan_vdefault' or widget.objectName() == 'composer_om_vdefault':
                    sql += (" '" + str(utils_giswater.get_item_data(self.dlg_config, widget, 1)) + "' "
                        " WHERE parameter = '" + widget.objectName() + "' AND cur_user = current_user")
                elif widget.objectName() == 'cad_tools_base_layer_vdefault_1':
                    sql += ("'" + str(value) + "' WHERE cur_user = current_user AND parameter = '" + parameter + "'")
                elif type(widget) == QDoubleSpinBox:
                    sql += ("'" + str(value) + "' WHERE cur_user = current_user AND parameter = '" + parameter + "'")
                else:
                    sql += (" '" + str(utils_giswater.get_item_data(self.dlg_config, widget, 0)) + "' "
                            " WHERE parameter = '" + widget.objectName() + "' AND cur_user = current_user")

            else:
                sql = "INSERT INTO " + self.schema_name + "." + tablename + "(parameter, value, cur_user)"
                if widget.objectName() == 'state_vdefault':
                    sql += (" VALUES ('" + parameter + "', '" + str(
                        utils_giswater.get_item_data(self.dlg_config, widget, 0)) + "', current_user)")
                elif widget.objectName() == 'municipality_vdefault':
                    sql += (" VALUES ('" + parameter + "',"
                            " (SELECT muni_id FROM " + self.schema_name + ".ext_municipality"
                            " WHERE name ='" + str(value) + "'), current_user)")
                elif widget.objectName() == 'composer_plan_vdefault' or widget.objectName() == 'composer_om_vdefault':
                    sql += (" VALUES ('" + parameter + "', '" + str(utils_giswater.get_item_data(self.dlg_config, widget, 1)) + "', current_user)")
                elif widget.objectName() == 'cad_tools_base_layer_vdefault_1':
                    sql += (" VALUES ('" + parameter + "', '" + str(value) + "', current_user)")
                elif type(widget) == QDoubleSpinBox:
                    sql += (" VALUES ('" + parameter + "', '" + str(value) + "', current_user)")
                else:
                    sql += (" VALUES ('" + parameter + "', '" + str(
                        utils_giswater.get_item_data(self.dlg_config, widget, 0)) + "', current_user)")

        if sql:
            self.controller.execute_sql(sql)


    def delete_config_param_user(self, parameter):
        """ Delete value of @parameter in table 'config_param_user' with current_user control """

        tablename = "config_param_user"
        sql = ("DELETE FROM " + self.schema_name + "." + tablename + ""
               " WHERE cur_user = current_user AND parameter = '" + parameter + "'")
        self.controller.execute_sql(sql)


    def insert_selector_audit(self, fprocesscat_id):
        """ Insert @fprocesscat_id for current_user in table 'selector_audit' """

        tablename = "selector_audit"
        sql = ("SELECT * FROM " + self.schema_name + "." + tablename + ""
               " WHERE fprocesscat_id = " + str(fprocesscat_id) + " AND cur_user = current_user;")
        row = self.controller.get_row(sql)
        if not row:
            sql = ("INSERT INTO " + self.schema_name + "." + tablename + " (fprocesscat_id, cur_user)"
                   " VALUES (" + str(fprocesscat_id) + ", current_user);")
        self.controller.execute_sql(sql)


    def delete_config_param_system(self, parameter):
        """ Delete value of @parameter in table 'config_param_user' with current_user control """

        tablename = "config_param_system"
        sql = ("DELETE FROM " + self.schema_name + "." + tablename + ""
               " WHERE parameter = '" + parameter + "'")
        self.controller.execute_sql(sql)


    def manage_config_param_user(self, parameter, add_check=False):
        """ Manage @parameter in table 'config_param_user' """

        chk_widget = "chk_" + str(parameter)
        if utils_giswater.isChecked(self.dlg_config, chk_widget):
            self.upsert_config_param_user(parameter, add_check)
        else:
            self.delete_config_param_user(parameter)


    def manage_config_param_system(self, parameter, add_check=False):
        """ Manage @parameter in table 'config_param_system' """

        chk_widget = "chk_" + str(parameter)
        if utils_giswater.isChecked(self.dlg_config, chk_widget):
            self.upsert_config_param_system(parameter,add_check)
        else:
            self.delete_config_param_system(parameter)


    def filter_dma_vdefault(self):
        """ Filter QComboBox @dma_vdefault according QComboBox @exploitation_vdefault """

        sql = ("SELECT DISTINCT(dma_id),name FROM " + self.schema_name + ".dma"
               " WHERE expl_id = '" + str(utils_giswater.get_item_data(self.dlg_config, self.dlg_config.exploitation_vdefault, 0)) + "'")
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.dma_vdefault, rows, 1)


    def filter_presszone_vdefault(self):
        """ Filter QComboBox @presszone_vdefault according QComboBox @exploitation_vdefault """

        sql = ("SELECT DISTINCT(id), id FROM " + self.schema_name + ".cat_presszone"
               " WHERE expl_id = '" + str(utils_giswater.get_item_data(self.dlg_config, self.dlg_config.exploitation_vdefault, 0)) + "'")
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.presszone_vdefault, rows, False)


    def filter_statetype_vdefault(self):
        """ Filter QComboBox @statetype_vdefault according  @state_vdefault """
        sql = ("SELECT DISTINCT(id), name FROM " + self.schema_name + ".value_state_type"
               " WHERE state = '" + str(utils_giswater.get_item_data(self.dlg_config, self.dlg_config.state_vdefault)) + "'")
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.statetype_vdefault, rows, 1)

    def filter_elementcat_vdefault(self):
        """ Filter QComboBox @elementcat_vdefault according  @elementtype_vdefault """
        sql = ("SELECT id, id FROM " + self.schema_name + ".cat_element"
               " WHERE elementtype_id = '" + str(utils_giswater.get_item_data(self.dlg_config, self.dlg_config.elementtype_vdefault)) + "'")
        rows = self.controller.get_rows(sql)
        utils_giswater.set_item_data(self.dlg_config.elementcat_vdefault, rows, 1)

    def check_child_to_parent(self, widget_child, widget_parent):
        if widget_child.isChecked():
            widget_parent.setChecked(True)

    def check_parent_to_child(self, widget_parent, widget_child):
        if widget_parent.isChecked() == False:
            widget_child.setChecked(False)

    def populate_cmb_templates(self, combo):

        composers = self.iface.activeComposers()
        index = 0
        records = []
        for comp_view in composers:
            elem = [index, comp_view.composerWindow().windowTitle()]
            records.append(elem)
            index = index +1
        utils_giswater.set_item_data(combo, records, 1)
