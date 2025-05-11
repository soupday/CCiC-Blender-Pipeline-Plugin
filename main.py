# Copyright (C) 2023 Victor Soupday
# This file is part of CC/iC-Blender-Pipeline-Plugin <https://github.com/soupday/CCiC-Blender-Pipeline-Plugin>
#
# CC/iC-Blender-Pipeline-Plugin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CC/iC-Blender-Pipeline-Plugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CC/iC-Blender-Pipeline-Plugin.  If not, see <https://www.gnu.org/licenses/>.

import RLPy
from btp import vars, prefs, cc, qt, tests, importer, exporter, morph, link, gob


rl_plugin_info = { "ap": "iClone", "ap_version": "8.0" }

FBX_IMPORTER: importer.Importer = None
BLOCK_UPDATE = False


def initialize_plugin():
    global BLOCK_UPDATE

    BLOCK_UPDATE = True

    print("CC/iC Blender Pipeline Plugin: Initialize")

    prefs.detect_paths()

    icon_export = qt.get_icon("BlenderExport.png")
    icon_import = qt.get_icon("BlenderImport.png")
    icon_link = qt.get_icon("BlenderDataLink.png")
    icon_blender = qt.get_icon("BlenderLogo.png")
    icon_settings = qt.get_icon("BlenderSettings.png")
    icon_morph = qt.get_icon("MeshIcoSphere.png")

    # Menu (CC4 & iClone)
    plugin_menu = qt.find_add_plugin_menu("Blender Pipeline")
    qt.clear_menu(plugin_menu)
    qt.add_menu_action(plugin_menu, "Export Character to Blender", action=menu_export, icon=icon_export)
    if cc.is_cc():
        qt.add_menu_action(plugin_menu, "Import Character from Blender", action=menu_import, icon=icon_import)
    qt.menu_separator(plugin_menu)
    qt.add_menu_action(plugin_menu, "DataLink", action=menu_link, icon=icon_link)
    qt.menu_separator(plugin_menu)
    qt.add_menu_action(plugin_menu, "Go-B", action=menu_go_b, icon=icon_blender)
    if cc.is_cc():
        qt.add_menu_action(plugin_menu, "Go-B (Morph)", action=menu_go_morph, icon=icon_morph)
    qt.menu_separator(plugin_menu)
    qt.add_menu_action(plugin_menu, "Settings", action=menu_settings, icon=icon_settings)
    qt.add_menu_action(plugin_menu, "Toolbar", action=menu_toolbar, toggle=True, on=True)

    toolbar = qt.find_add_toolbar("Blender Pipeline Toolbar", show_hide=fetch_toolbar_state)
    qt.clear_toolbar(toolbar)
    qt.add_toolbar_action(toolbar, icon_blender, "GoB", action=menu_go_b)
    if cc.is_cc():
        qt.add_toolbar_action(toolbar, icon_morph, "GoB-Morph", action=menu_go_morph)
    qt.add_toolbar_action(toolbar, icon_link, "Blender DataLink", action=menu_link, toggle=True)
    qt.add_toolbar_separator(toolbar)
    qt.add_toolbar_action(toolbar, icon_export, "Export to Blender", action=menu_export)
    if cc.is_cc():
        qt.add_toolbar_action(toolbar, icon_import, "Import from Blender", action=menu_import)
    qt.add_toolbar_separator(toolbar)
    qt.add_toolbar_action(toolbar, icon_settings, "Blender Pipeline Settings", action=menu_settings, toggle=True)

    if prefs.AUTO_START_SERVICE:
        link.link_auto_start()

    BLOCK_UPDATE = False


def fetch_toolbar_state(visible):
    """Update the menu Toolbar toggle with the visibilty state of the toolbar.
       CC4 / iC8 remembers the visibility state of toolbars and applies it after the
       plug-in has been initialized. This will update the menu with those changes."""
    global BLOCK_UPDATE
    if BLOCK_UPDATE: return
    plugin_menu = qt.find_plugin_menu("Blender Pipeline")
    if plugin_menu:
        menu_toolbar_action = qt.find_menu_action(plugin_menu, "Toolbar")
        if menu_toolbar_action:
            BLOCK_UPDATE = True
            menu_toolbar_action.setChecked(visible)
            BLOCK_UPDATE = False


def menu_toolbar():
    global BLOCK_UPDATE
    if BLOCK_UPDATE: return
    plugin_menu = qt.find_plugin_menu("Blender Pipeline")
    toolbar = qt.find_toolbar("Blender Pipeline Toolbar")
    if plugin_menu and toolbar:
        menu_toolbar_action = qt.find_menu_action(plugin_menu, "Toolbar")
        if menu_toolbar_action:
            BLOCK_UPDATE = True
            if menu_toolbar_action.isChecked():
                toolbar.show()
            else:
                toolbar.hide()
            BLOCK_UPDATE = False


def menu_import():
    global FBX_IMPORTER
    FBX_IMPORTER = None
    file_path = RLPy.RUi.OpenFileDialog("Model Files(*.fbx *.obj)")
    model_type, key_path = cc.model_type_and_key_path(file_path)
    if model_type == "FBX" and file_path and file_path != "":
        FBX_IMPORTER = importer.Importer(file_path)
    elif model_type == "OBJ" and file_path and file_path != "":
        if cc.model_file_has_key(file_path):
            morph.MorphSlider(file_path, key_path)


def menu_export():
    export = exporter.get_exporter()
    if export.is_shown():
        export.hide()
    else:
        export.show()


def menu_link():
    data_link = link.get_data_link()
    if not data_link.is_listening():
        data_link.link_start()
    if data_link.is_shown():
        data_link.hide()
    else:
        data_link.show()


def menu_settings():
    preferences = prefs.get_preferences()
    if preferences.is_shown():
        preferences.hide()
    else:
        preferences.show()


def show_settings():
    preferences = prefs.get_preferences()
    if not preferences.is_shown():
        preferences.show()


def menu_go_b():
    data_link = link.get_data_link()
    if data_link.is_connected():
        data_link.send_actors()
    else:
        if prefs.check_paths(create=True):
            gob.go_b()
        else:
            show_settings()


def menu_go_morph():
    data_link = link.get_data_link()
    if data_link.is_connected():
        data_link.send_morph()
    else:
        if prefs.check_paths(create=True):
            gob.go_morph()
        else:
            show_settings()


def run_script():
    initialize_plugin()


