"""
This file is part of Giswater 2.0
The program is free software: you can redistribute it and/or modify it under the terms of the GNU 
General Public License as published by the Free Software Foundation, either version 3 of the License, 
or (at your option) any later version.
"""

# -*- coding: utf-8 -*-
from qgis.core import QgsPoint, QgsFeatureRequest
from PyQt4.QtCore import QPoint, Qt
from PyQt4.Qt import QDate

from functools import partial
from datetime import datetime

import utils_giswater
from map_tools.parent import ParentMapTool
from ui_manager import UDcatalog
from ui_manager import WScatalog
from ui_manager import NodeReplace


class ReplaceNodeMapTool(ParentMapTool):
    """ Button 44: User select one node. Execute SQL function: 'gw_fct_node_replace' """

    def __init__(self, iface, settings, action, index_action):
        """ Class constructor """

        # Call ParentMapTool constructor
        super(ReplaceNodeMapTool, self).__init__(iface, settings, action, index_action)


    def init_replace_node_form(self, feature):
        
        # Create the dialog and signals
        self.dlg_nodereplace = NodeReplace()
        utils_giswater.setDialog(self.dlg_nodereplace)
        self.load_settings(self.dlg_nodereplace)

        sql = ("SELECT id FROM " + self.schema_name + ".cat_work ORDER BY id")
        rows = self.controller.get_rows(sql)
        if rows:
            utils_giswater.fillComboBox(self.dlg_nodereplace.workcat_id_end, rows)
            utils_giswater.set_autocompleter(self.dlg_nodereplace.workcat_id_end)

        sql = ("SELECT value FROM " + self.schema_name + ".config_param_user"
               " WHERE cur_user = current_user AND parameter = 'workcat_vdefault'")
        row = self.controller.get_row(sql)
        if row:
            self.dlg_nodereplace.workcat_id_end.setCurrentIndex(self.dlg_nodereplace.workcat_id_end.findText(row[0]))

        sql = ("SELECT value FROM " + self.schema_name + ".config_param_user"
               " WHERE cur_user = current_user AND parameter = 'enddate_vdefault'")
        row = self.controller.get_row(sql)
        if row:
            self.enddate_aux = datetime.strptime(row[0], '%Y-%m-%d').date()
        else:
            self.enddate_aux = datetime.strptime(QDate.currentDate().toString('yyyy-MM-dd'), '%Y-%m-%d').date()

            self.dlg_nodereplace.enddate.setDate(self.enddate_aux)

        # Get nodetype_id from current node
        project_type = self.controller.get_project_type()
        if project_type == 'ws':
            node_type = feature.attribute('nodetype_id')
        if project_type == 'ud':
            node_type = feature.attribute('node_type')
            sql = "SELECT DISTINCT(id) FROM " + self.schema_name + ".cat_node ORDER BY id"
            rows = self.controller.get_rows(sql)
            utils_giswater.fillComboBox("node_nodecat_id", rows, allow_nulls=False)

        self.dlg_nodereplace.node_node_type.setText(node_type)
        self.dlg_nodereplace.node_node_type_new.currentIndexChanged.connect(self.edit_change_elem_type_get_value)
        self.dlg_nodereplace.btn_catalog.pressed.connect(partial(self.open_catalog_form, project_type, 'node'))

        # Fill 1st combo boxes-new system node type
        sql = "SELECT DISTINCT(id) FROM " + self.schema_name + ".node_type ORDER BY id"
        rows = self.controller.get_rows(sql)
        utils_giswater.fillComboBox("node_node_type_new", rows)

        self.dlg_nodereplace.btn_accept.pressed.connect(partial(self.get_values, self.dlg_nodereplace))
        self.dlg_nodereplace.btn_cancel.pressed.connect(partial(self.close_dialog, self.dlg_nodereplace))

        # Open dialog
        self.open_dialog(self.dlg_nodereplace, maximize_button=False)


        
    def get_values(self, dialog):

        self.workcat_id_end_aux = utils_giswater.getWidgetText(dialog.workcat_id_end)
        self.enddate_aux = dialog.enddate.date().toString('yyyy-MM-dd')

        project_type = self.controller.get_project_type()
        node_node_type_new = utils_giswater.getWidgetText(dialog.node_node_type_new)
        node_nodecat_id = utils_giswater.getWidgetText(dialog.node_nodecat_id)
        layer = self.controller.get_layer_by_nodetype(node_node_type_new, log_info=True)

        if node_node_type_new != "null" and node_nodecat_id != "null":
            
            # Ask question before executing
            message = "Are you sure you want to replace selected node with a new one?"
            answer = self.controller.ask_question(message, "Replace node")
            if answer:
                # Execute SQL function and show result to the user
                function_name = "gw_fct_node_replace"
                sql = ("SELECT " + self.schema_name + "." + function_name + "('"
                       + str(self.node_id) + "', '" + str(self.workcat_id_end_aux) + "', '" + str(self.enddate_aux) + "', '"
                       + str(utils_giswater.isChecked("keep_elements")) + "');")
                new_node_id = self.controller.get_row(sql, commit=True)
                if new_node_id:
                    message = "Node replaced successfully"
                    self.controller.show_info(message)
                    self.iface.setActiveLayer(layer)
                    self.force_active_layer = False
                else:
                    message = "Error replacing node"
                    self.controller.show_warning(message)

                # Force user to manage with state = 1 features
                current_user = self.controller.get_project_user()
                sql = ("DELETE FROM " + self.schema_name + ".selector_state"
                       " WHERE state_id = 1 AND cur_user='" + str(current_user) + "';")
                self.controller.execute_sql(sql)
                sql = ("\nINSERT INTO " + self.schema_name + ".selector_state (state_id, cur_user)"
                       "VALUES (1, '" + str(current_user) + "');")
                self.controller.execute_sql(sql)

                # Update field 'nodecat_id'
                sql = ("UPDATE " + self.schema_name + ".v_edit_node"
                       " SET nodecat_id = '" + str(node_nodecat_id) + "'"
                       " WHERE node_id = '" + str(new_node_id[0]) + "'")
                self.controller.execute_sql(sql)

                if project_type == 'ud':
                    sql = ("UPDATE " + self.schema_name + ".v_edit_node"
                           " SET node_type = '" + str(node_node_type_new) + "'"
                           " WHERE node_id = '" + str(new_node_id[0]) + "'")
                    self.controller.execute_sql(sql)

                sql = ("SELECT man_table FROM " + self.schema_name + ".node_type"
                       " WHERE id = '" + str(node_node_type_new) + "'")
                row = self.controller.get_row(sql)
                if not row:
                    return

                # Set active layer
                viewname = "v_edit_" + str(row[0])
                layer = self.controller.get_layer_by_tablename(viewname)
                if layer:
                    self.iface.setActiveLayer(layer)
                    
                message = "Values has been updated"
                self.controller.show_info(message)

                # Refresh canvas
                self.refresh_map_canvas()

                # Open custom form
                self.open_custom_form(layer, new_node_id)

            # Deactivate map tool
            self.deactivate()
            self.set_action_pan()

        self.close_dialog(dialog, set_action_pan=False)


    """ QgsMapTools inherited event functions """

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel_map_tool()
            return


    def canvasReleaseEvent(self, event):
        
        if event.button() == Qt.RightButton:
            self.cancel_map_tool()
            return

        # Get the click
        x = event.pos().x()
        y = event.pos().y()
        event_point = QPoint(x, y)
        snapped_feat = None

        # Snapping
        (retval, result) = self.snapper.snapToCurrentLayer(event_point, 2)  # @UnusedVariable
                
        if result:
            # Get the first feature
            snapped_feat = result[0]
            point = QgsPoint(snapped_feat.snappedVertex)   #@UnusedVariable
            snapped_feat = next(snapped_feat.layer.getFeatures(QgsFeatureRequest().setFilterFid(result[0].snappedAtGeometry)))                

        if snapped_feat:

            # Get 'node_id' and 'nodetype'
            self.node_id = snapped_feat.attribute('node_id')
            if self.project_type == 'ws':
                nodetype_id = snapped_feat.attribute('nodetype_id')
            elif self.project_type == 'ud':
                nodetype_id = snapped_feat.attribute('node_type')
            layer = self.controller.get_layer_by_nodetype(nodetype_id, log_info=True) 
            if not layer:
                return

            self.init_replace_node_form(snapped_feat)


    def open_custom_form(self, layer, node_id):
        """ Open custom form from selected @layer and @node_id """
                                
        # Get feature with selected node_id
        expr_filter = "node_id = "
        expr_filter += "'" + str(node_id[0]) + "'"
        (is_valid, expr) = self.check_expression(expr_filter, True)   #@UnusedVariable       
        if not is_valid:
            return     
  
        # Get a featureIterator from this expression:     
        it = layer.getFeatures(QgsFeatureRequest(expr))
        id_list = [i for i in it]
        if id_list:
            self.iface.openFeatureForm(layer, id_list[0])


    def activate(self):

        # Check button
        self.action().setChecked(True)

        # Store user snapping configuration
        self.snapper_manager.store_snapping_options()

        # Clear snapping
        self.snapper_manager.clear_snapping()

        # Set active layer to 'v_edit_node'
        self.layer_node = self.controller.get_layer_by_tablename("v_edit_node")
        self.iface.setActiveLayer(self.layer_node)   
        self.force_active_layer = True           

        # Change cursor
        self.canvas.setCursor(self.cursor)
        
        self.project_type = self.controller.get_project_type()         

        # Show help message when action is activated
        if self.show_help:
            message = "Select the node inside a pipe by clicking on it and it will be replaced"
            self.controller.show_info(message)


    def deactivate(self):
          
        # Call parent method     
        ParentMapTool.deactivate(self)


    def edit_change_elem_type_get_value(self, index):
        """ Just select item to 'real' combo 'nodecat_id' (that is hidden) """

        if index == -1:
            return

        # Get selected value from 2nd combobox
        node_node_type_new = utils_giswater.getWidgetText("node_node_type_new")

        # When value is selected, enabled 3rd combo box
        if node_node_type_new != 'null':
            project_type = self.controller.get_project_type()
            if project_type == 'ws':
                # Fill 3rd combo_box-catalog_id
                utils_giswater.setWidgetEnabled(self.dlg_nodereplace.node_nodecat_id, True)
                sql = ("SELECT DISTINCT(id)"
                       " FROM " + self.schema_name + ".cat_node"
                       " WHERE nodetype_id = '" + str(node_node_type_new) + "'")
                rows = self.controller.get_rows(sql)
                utils_giswater.fillComboBox(self.dlg_nodereplace.node_nodecat_id, rows)
    

    def open_catalog_form(self, wsoftware, geom_type):
        """ Set dialog depending water software """

        node_type = utils_giswater.getWidgetText("node_node_type_new")
        if node_type == 'null':
            message = "Select a Custom node Type"
            self.controller.show_warning(message)
            return

        if wsoftware == 'ws':
            self.dlg_cat = WScatalog()
            self.field2 = 'pnom'
            self.field3 = 'dnom'
        elif wsoftware == 'ud':
            self.dlg_cat = UDcatalog()
            self.field2 = 'shape'
            self.field3 = 'geom1'
        utils_giswater.setDialog(self.dlg_cat)
        self.load_settings(self.dlg_cat)

        self.node_type_text = None
        if wsoftware == 'ws' and geom_type == 'node':
            self.node_type_text = node_type

        sql = ("SELECT DISTINCT(matcat_id) as matcat_id "
               " FROM " + self.schema_name + ".cat_" + geom_type)
        if wsoftware == 'ws' and geom_type == 'node':
            sql += " WHERE " + geom_type + "type_id = '" + self.node_type_text + "'"
        sql += " ORDER BY matcat_id"
        rows = self.controller.get_rows(sql)
        utils_giswater.fillComboBox(self.dlg_cat.matcat_id, rows)

        sql = ("SELECT DISTINCT(" + self.field2 + ")"
               " FROM " + self.schema_name + ".cat_" + geom_type)
        if wsoftware == 'ws' and geom_type == 'node':
            sql += " WHERE " + geom_type + "type_id = '" + self.node_type_text + "'"
        sql += " ORDER BY " + self.field2
        rows = self.controller.get_rows(sql)
        utils_giswater.fillComboBox(self.dlg_cat.filter2, rows)

        self.fill_filter3(wsoftware, geom_type)

        # Set signals and open dialog
        self.dlg_cat.btn_ok.pressed.connect(self.fill_geomcat_id)
        self.dlg_cat.btn_cancel.pressed.connect(partial(self.close_dialog, self.dlg_cat))
        self.dlg_cat.rejected.connect(partial(self.close_dialog, self.dlg_cat))
        self.dlg_cat.matcat_id.currentIndexChanged.connect(partial(self.fill_catalog_id, wsoftware, geom_type))
        self.dlg_cat.matcat_id.currentIndexChanged.connect(partial(self.fill_filter2, wsoftware, geom_type))
        self.dlg_cat.matcat_id.currentIndexChanged.connect(partial(self.fill_filter3, wsoftware, geom_type))
        self.dlg_cat.filter2.currentIndexChanged.connect(partial(self.fill_catalog_id, wsoftware, geom_type))
        self.dlg_cat.filter2.currentIndexChanged.connect(partial(self.fill_filter3, wsoftware, geom_type))
        self.dlg_cat.filter3.currentIndexChanged.connect(partial(self.fill_catalog_id, wsoftware, geom_type))
        self.dlg_cat.open()


    def fill_geomcat_id(self):

        catalog_id = utils_giswater.getWidgetText(self.dlg_cat.id)

        utils_giswater.setDialog(self.dlg_nodereplace)
        utils_giswater.setWidgetEnabled(self.dlg_nodereplace.node_nodecat_id, True)
        utils_giswater.setWidgetText(self.dlg_nodereplace.node_nodecat_id, catalog_id)

        self.close_dialog(self.dlg_cat)


    def fill_filter2(self, wsoftware, geom_type):

        # Get values from filters
        mats = utils_giswater.getWidgetText(self.dlg_cat.matcat_id)

        # Set SQL query
        sql_where = ""
        sql = ("SELECT DISTINCT(" + self.field2 + ")"
               " FROM " + self.schema_name + ".cat_" + geom_type)

        # Build SQL filter
        if mats != "null":
            if sql_where == "":
                sql_where = " WHERE"
            sql_where += " matcat_id = '" + mats + "'"
        if wsoftware == 'ws' and self.node_type_text is not None:
            if sql_where == "":
                sql_where = " WHERE"
            else:
                sql_where += " AND"
            sql_where += " " + geom_type + "type_id = '" + self.node_type_text + "'"
        sql += sql_where + " ORDER BY " + self.field2

        rows = self.controller.get_rows(sql)
        utils_giswater.fillComboBox(self.dlg_cat.filter2, rows)
        self.fill_filter3(wsoftware, geom_type)


    def fill_filter3(self, wsoftware, geom_type):

        # Get values from filters
        mats = utils_giswater.getWidgetText(self.dlg_cat.matcat_id)
        filter2 = utils_giswater.getWidgetText(self.dlg_cat.filter2)

        # Set SQL query
        sql_where = ""
        if wsoftware == 'ws' and geom_type != 'connec':
            sql = "SELECT " + self.field3
            sql += " FROM (SELECT DISTINCT(regexp_replace(trim(' nm' FROM " + self.field3 + "),'-','', 'g')) as x, " + self.field3
        elif wsoftware == 'ws' and geom_type == 'connec':
            sql = "SELECT DISTINCT(TRIM(TRAILING ' ' from " + self.field3 + ")) as " + self.field3
        else:
            sql = "SELECT DISTINCT(" + self.field3 + ")"
        sql += " FROM " + self.schema_name + ".cat_" + geom_type

        # Build SQL filter
        if wsoftware == 'ws' and self.node_type_text is not None:
            sql_where = " WHERE " + geom_type + "type_id = '" + self.node_type_text + "'"

        if mats != "null":
            if sql_where == "":
                sql_where = " WHERE"
            else:
                sql_where += " AND"
            sql_where += " matcat_id = '" + mats + "'"

        if filter2 != "null":
            if sql_where == "":
                sql_where = " WHERE"
            else:
                sql_where += " AND"
            sql_where += " " + self.field2 + " = '" + filter2 + "'"
        if wsoftware == 'ws' and geom_type != 'connec':
            sql += sql_where + " ORDER BY x) AS " + self.field3
        else:
            sql += sql_where + " ORDER BY " + self.field3

        rows = self.controller.get_rows(sql)
        utils_giswater.fillComboBox(self.dlg_cat.filter3, rows)

        self.fill_catalog_id(wsoftware, geom_type)


    def fill_catalog_id(self, wsoftware, geom_type):

        # Get values from filters
        mats = utils_giswater.getWidgetText(self.dlg_cat.matcat_id)
        filter2 = utils_giswater.getWidgetText(self.dlg_cat.filter2)
        filter3 = utils_giswater.getWidgetText(self.dlg_cat.filter3)

        # Set SQL query
        sql_where = ""
        sql = ("SELECT DISTINCT(id) as id"
               " FROM " + self.schema_name + ".cat_" + geom_type)

        if wsoftware == 'ws' and self.node_type_text is not None:
            sql_where = " WHERE " + geom_type + "type_id = '" + self.node_type_text + "'"
        if mats != "null":
            if sql_where == "":
                sql_where = " WHERE"
            else:
                sql_where += " AND"
            sql_where += " matcat_id = '" + mats + "'"
        if filter2 != "null":
            if sql_where == "":
                sql_where = " WHERE"
            else:
                sql_where += " AND"
            sql_where += " " + self.field2 + " = '" + filter2 + "'"
        if filter3 != "null":
            if sql_where == "":
                sql_where = " WHERE"
            else:
                sql_where += " AND"
            sql_where += " " + self.field3 + " = '" + filter3 + "'"
        sql += sql_where + " ORDER BY id"

        rows = self.controller.get_rows(sql)
        utils_giswater.fillComboBox(self.dlg_cat.id, rows)
