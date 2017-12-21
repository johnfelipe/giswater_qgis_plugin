"""
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU
General Public License as published by the Free Software Foundation, either version 3 of the License,
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
from PyQt4.QtCore import Qt, QDate
from PyQt4.QtGui import QCompleter, QLineEdit, QTableView, QStringListModel, QPushButton, QComboBox
from PyQt4.QtSql import QSqlTableModel        

import os
import sys

plugin_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(plugin_path)
import utils_giswater

from ui.event_standard import EventStandard             # @UnresolvedImport
from ui.event_ud_arc_standard import EventUDarcStandard # @UnresolvedImport
from ui.event_ud_arc_rehabit import EventUDarcRehabit   # @UnresolvedImport
from ui.add_visit import AddVisit                       # @UnresolvedImport
from actions.parent_manage import ParentManage


class ManageVisit(ParentManage):

    def __init__(self, iface, settings, controller, plugin_dir):
        """ Class to control 'Add visit' of toolbar 'edit' """
        ParentManage.__init__(self, iface, settings, controller, plugin_dir)
        
 
    def manage_visit(self):
        """ Button 64. Add visit """
        
        # Create the dialog and signals
        self.dlg_visit = AddVisit()
        utils_giswater.setDialog(self.dlg_visit)

        # Show future id of visit
        sql = "SELECT MAX(id) FROM " + self.schema_name + ".om_visit"
        row = self.controller.get_row(sql)
        if row:
            visit_id = row[0] + 1
            self.dlg_visit.visit_id.setText(str(visit_id))
        
        # Set icons
        self.set_icon(self.dlg_visit.btn_relation_delete, "112")
        self.set_icon(self.dlg_visit.btn_relation_snapping, "137")
        self.set_icon(self.dlg_visit.btn_doc_insert, "111")
        self.set_icon(self.dlg_visit.btn_doc_delete, "112")
        self.set_icon(self.dlg_visit.btn_doc_new, "134")
        self.set_icon(self.dlg_visit.btn_open_doc, "170")     
        
        # Tab 'Data'
        self.visit_id = self.dlg_visit.findChild(QLineEdit, "visit_id")
        self.ext_code = self.dlg_visit.findChild(QLineEdit, "ext_code")
        self.visitcat_id = self.dlg_visit.findChild(QComboBox, "visitcat_id")
        self.btn_accept = self.dlg_visit.findChild(QPushButton, "btn_accept")
        self.btn_cancel = self.dlg_visit.findChild(QPushButton, "btn_cancel")

        #self.event_id = self.dlg_visit.findChild(QLineEdit, "event_id")
        self.tbl_event = self.dlg_visit.findChild(QTableView, "tbl_event")
        
        # Set current date and time
        current_date = QDate.currentDate()
        self.dlg_visit.startdate.setDate(current_date)     
        self.dlg_visit.enddate.setDate(current_date)     

        # Set signals
        self.dlg_visit.btn_event_insert.pressed.connect(self.event_insert)
        self.dlg_visit.btn_event_delete.pressed.connect(self.event_delete)
        self.dlg_visit.btn_event_update.pressed.connect(self.event_update)
                
        # Tab 'Document'
        self.doc_id = self.dlg_visit.findChild(QLineEdit, "doc_id")
        self.tbl_document = self.dlg_visit.findChild(QTableView, "tbl_document") 
            
        # Set signals
        self.dlg_visit.btn_doc_insert.pressed.connect(self.document_insert)
        self.dlg_visit.btn_doc_delete.pressed.connect(self.document_delete)
        self.dlg_visit.btn_doc_new.pressed.connect(self.manage_document)
        self.dlg_visit.btn_open_doc.pressed.connect(self.document_open)  
        
        # Fill combo boxes of the form
        self.fill_combos()

        # Set autocompleters of the form
        self.set_completers()
                
        # Open the dialog
        self.dlg_visit.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.dlg_visit.show()
       
    
    def fill_combos(self):
        """ Fill combo boxes of the form """
        
        # Fill ComboBox visitcat_id
        sql = ("SELECT name"
               " FROM " + self.schema_name + ".om_visit_cat"
               " ORDER BY name")
        rows = self.controller.get_rows(sql)
        utils_giswater.fillComboBox("visitcat_id", rows) 
              
        # Fill ComboBox parameter_type_id
        sql = ("SELECT id"
               " FROM " + self.schema_name + ".om_visit_parameter_type"
               " ORDER BY id")
        rows = self.controller.get_rows(sql)
        utils_giswater.fillComboBox("parameter_type_id", rows)   
            
        # Fill ComboBox parameter_id
        sql = ("SELECT id"
               " FROM " + self.schema_name + ".om_visit_parameter"
               " ORDER BY id")
        rows = self.controller.get_rows(sql)
        utils_giswater.fillComboBox("parameter_id", rows)   
                    
    
    def set_completers(self):
        """ Set autocompleters of the form """
                
        # Adding auto-completion to a QLineEdit - visit_id
        self.completer = QCompleter()
        self.dlg_visit.visit_id.setCompleter(self.completer)
        model = QStringListModel()

        sql = "SELECT DISTINCT(id) FROM " + self.schema_name + ".om_visit"
        rows = self.controller.get_rows(sql)
        values = []
        for row in rows:
            values.append(str(row[0]))

        model.setStringList(values)
        self.completer.setModel(model)
        self.dlg_visit.visit_id.textChanged.connect(self.check_visit_exist)
                
        # Adding auto-completion to a QLineEdit - document_id
        self.completer = QCompleter()
        self.dlg_visit.doc_id.setCompleter(self.completer)
        model = QStringListModel()
                
        sql = "SELECT DISTINCT(id) FROM " + self.schema_name + ".doc"
        rows = self.controller.get_rows(sql)
        values = []
        for row in rows:
            values.append(str(row[0]))

        model.setStringList(values)
        self.completer.setModel(model)
                      

    def manage_document(self):
        """ TODO: Execute action of button 34 """
        pass      
#         manage_document = ManageDocument(self.iface, self.settings, self.controller, self.plugin_dir)          
#         manage_document.manage_document()
#         self.set_completer_object(self.table_object)   
                

    def fill_table_visit(self, widget, table_name, filter_):
        """ Set a model with selected filter. Attach that model to selected table """

        # Set model
        model = QSqlTableModel();
        model.setTable(table_name)
        model.setEditStrategy(QSqlTableModel.OnManualSubmit)
        model.setFilter(filter_)
        model.select()

        # Check for errors
        if model.lastError().isValid():
            self.controller.show_warning(model.lastError().text())

        # Attach model to table view
        widget.setModel(model)
        widget.show()


    def check_visit_exist(self):

        # Tab event
        # Check if we already have data with selected visit_id
        visit_id = self.dlg_visit.visit_id.text()
        sql = ("SELECT DISTINCT(id) FROM " + self.schema_name + ".om_visit"
               " WHERE id = '" + str(visit_id) + "'")
        row = self.controller.get_row(sql)
        if not row:
            return
        
        # If element exist: load data ELEMENT
        sql = ("SELECT * FROM " + self.schema_name + ".om_visit" 
               " WHERE id = '" + str(visit_id) + "'")
        row = self.controller.get_row(sql)
        if not row:
            return        

        # Set data
        self.dlg_visit.ext_code.setText(str(row['ext_code']))

        # TODO: join
        if str(row['visitcat_id']) == '1':
            visitcat_id = "Test"

        utils_giswater.setWidgetText("visitcat_id", str(visitcat_id))
        self.dlg_visit.descript.setText(str(row['descript']))

        # Fill table event depending of visit_id
        visit_id = self.visit_id.text()
        self.filter = "visit_id = '" + str(visit_id) + "'"
        self.fill_table_visit(self.tbl_event, self.schema_name+".om_visit_event", self.filter)

        # Tab document
        self.fill_table_visit(self.tbl_document, self.schema_name + ".v_ui_doc_x_visit", self.filter)


    def event_insert(self):

        event_id = self.dlg_visit.event_id.text()
        if event_id != '':
            sql = ("SELECT form_type FROM " + self.schema_name + ".om_visit_parameter"
                   " WHERE id = '" + str(event_id) + "'")
            row = self.controller.get_row(sql)
            form_type = str(row[0])
        else:
            message = "You need to enter id"
            self.controller.show_info_box(message)
            return

        if form_type == 'event_ud_arc_standard':
            self.dlg_event = EventUDarcStandard()
        if form_type == 'event_ud_arc_rehabit':
            self.dlg_event = EventUDarcRehabit()
        if form_type == 'event_standard':
            self.dlg_event = EventStandard()

        utils_giswater.setDialog(self.dlg_event)
        self.dlg_event.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.dlg_event.exec_()


    def event_update(self):

        # Get selected rows
        selected_list = self.dlg_visit.tbl_event.selectionModel().selectedRows()
        if len(selected_list) == 0:
            message = "Any record selected"
            self.controller.show_info_box(message)
            return

        elif len(selected_list) > 1:
            message = "More then one event selected. Select just one event."
            self.controller.show_warning(message)
            return
        
        row = selected_list[0].row()
        parameter_id = self.dlg_visit.tbl_event.model().record(row).value("parameter_id")
        event_id = self.dlg_visit.tbl_event.model().record(row).value("id")

        sql = ("SELECT form_type FROM " + self.schema_name + ".om_visit_parameter"
               " WHERE id = '" + str(parameter_id) + "'")
        row = self.controller.get_row(sql)
        if not row:
            return
        form_type = str(row[0])

        sql = ("SELECT * FROM " + self.schema_name + ".om_visit_event"
               " WHERE id = '" + str(event_id) + "'")
        row = self.controller.get_row(sql)
        if not row:
            return            

        if form_type == 'event_ud_arc_standard':
            self.dlg_event = EventUDarcStandard()
            # Force fill data
            # TODO set parameter id
            #self.dlg_event.parameter_id
            self.dlg_event.value.setText(str(row['value']))
            self.dlg_event.position_id.setText(str(row['position_id']))
            self.dlg_event.position_value.setText(str(row['position_value']))
            self.dlg_event.text.setText(str(row['text']))

        elif form_type == 'event_ud_arc_rehabit':
            self.dlg_event = EventUDarcRehabit()
            # Force fill data
            # self.dlg_event.parameter_id
            self.dlg_event.position_id.setText(str(row['position_id']))
            self.dlg_event.position_value.setText(str(row['position_value']))
            self.dlg_event.text.setText(str(row['text']))
            self.dlg_event.value1.setText(str(row['value1']))
            self.dlg_event.value2.setText(str(row['value2']))
            self.dlg_event.geom1.setText(str(row['geom1']))
            self.dlg_event.geom2.setText(str(row['geom2']))
            self.dlg_event.geom3.setText(str(row['geom3']))

        elif form_type == 'event_standard':
            self.dlg_event = EventStandard()
            # Force fill data
            # self.dlg_event.parameter_id
            self.dlg_event.value.setText(str(row['value']))
            self.dlg_event.text.setText(str(row['text']))

        utils_giswater.setDialog(self.dlg_event)
        self.dlg_event.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.dlg_event.exec_()


    def event_delete(self):

        # Get selected rows
        selected_list = self.dlg_visit.tbl_event.selectionModel().selectedRows()
        if len(selected_list) == 0:
            message = "Any record selected"
            self.controller.show_info_box(message)
            return
        selected_id = []
        inf_text = ""
        list_id = ""
        for i in range(0, len(selected_list)):
            row = selected_list[i].row()
            event_id = self.dlg_visit.tbl_event.model().record(row).value("id")
            selected_id.append(str(event_id))
            inf_text += str(event_id) + ", "
            list_id = list_id + "'" + str(event_id) + "', "
        inf_text = inf_text[:-2]
        list_id = list_id[:-2]
        message = "Are you sure you want to delete these records?"
        answer = self.controller.ask_question(message, "Delete records", inf_text)
        if answer:
            for el in selected_id:
                sql = ("DELETE FROM " + self.schema_name + ".om_visit_event"
                       " WHERE id = '" + str(el) + "'")
                status = self.controller.execute_sql(sql)
                if not status:
                    message = "Error deleting data"
                    self.controller.show_warning(message)
                    return
                elif status:
                    message = "Event deleted"
                    self.controller.show_info(message)
                    self.dlg_visit.tbl_event.model().select()


    def document_open(self):

        # Get selected rows
        selected_list = self.dlg_visit.tbl_document.selectionModel().selectedRows()
        if len(selected_list) == 0:
            message = "Any record selected"
            self.controller.show_info_box(message)
            return
        elif len(selected_list) > 1:
            message = "More then one document selected. Select just one document."
            self.controller.show_warning(message)
            return
        else:
            row = selected_list[0].row()
            path = self.dlg_visit.tbl_document.model().record(row).value('path')
            # Check if file exist
            if not os.path.exists(path):
                message = "File not found"
                self.controller.show_warning(message)
            else:
                # Open the document
                os.startfile(path)


    def document_delete(self):

        # Get selected rows
        selected_list = self.dlg_visit.tbl_document.selectionModel().selectedRows()
        if len(selected_list) == 0:
            message = "Any record selected"
            self.controller.show_info_box(message)
            return
        
        selected_id = []
        inf_text = ""
        list_id = ""
        for i in range(0, len(selected_list)):
            row = selected_list[i].row()
            doc_id = self.dlg_visit.tbl_document.model().record(row).value("id")
            selected_id.append(str(doc_id))
            inf_text += str(doc_id) + ", "
            list_id = list_id + "'" + str(doc_id) + "', "
        inf_text = inf_text[:-2]
        list_id = list_id[:-2]
        message = "Are you sure you want to delete these records?"
        answer = self.controller.ask_question(message, "Delete records", inf_text)
        if answer:
            for el in selected_id:
                sql = ("DELETE FROM " + self.schema_name + ".doc_x_visit"
                       " WHERE id = '" + str(el) + "'")
                status = self.controller.execute_sql(sql)
                if not status:
                    message = "Error deleting data"
                    self.controller.show_warning(message)
                    return
                else:
                    message = "Event deleted"
                    self.controller.show_info(message)
                    self.dlg_visit.tbl_document.model().select()


    def document_insert(self):

        doc_id = self.doc_id.text()
        visit_id = self.visit_id.text()
        if doc_id == 'null':
            message = "You need to insert doc_id"
            self.controller.show_warning(message)
            return
        if visit_id == 'null':
            message = "You need to insert visit_id"
            self.controller.show_warning(message)
            return

        # Insert into new table
        sql = ("INSERT INTO " + self.schema_name + ".doc_x_visit (doc_id, visit_id)"
               " VALUES (" + str(doc_id) + "," + str(visit_id) + ")")
        status = self.controller.execute_sql(sql)
        if status:
            message = "Document inserted successfully"
            self.controller.show_info(message)

        self.dlg_visit.tbl_document.model().select()         
            