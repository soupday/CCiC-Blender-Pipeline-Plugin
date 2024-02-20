# Copyright (C) 2023 Victor Soupday
# This file is part of CC/iC-Blender-Pipeline-Plugin <https://github.com/soupday/CC/iC-Blender-Pipeline-Plugin>
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
import btp.importer as importer
import btp.exporter as exporter
import btp.link as link
import btp.cc as cc
import btp.qt as qt
import btp.tests as tests
import btp.gob as gob
import btp.vars as vars
import btp.prefs as prefs

rl_plugin_info = { "ap": "iClone", "ap_version": "8.0" }

FBX_IMPORTER: importer.Importer = None
FBX_EXPORTER: exporter.Exporter = None
SETTINGS: prefs.Preferences = None


def initialize_plugin():
    prefs.detect_paths()
    # Menu (CC4 & iClone)
    plugin_menu = qt.find_add_plugin_menu("Blender Pipeline")
    qt.clear_menu(plugin_menu)
    qt.add_menu_action(plugin_menu, "Settings", menu_link)
    qt.menu_separator(plugin_menu)
    qt.add_menu_action(plugin_menu, "Export Character to Blender", menu_export)
    if cc.is_cc():
        qt.menu_separator(plugin_menu)
        qt.add_menu_action(plugin_menu, "Import Character from Blender", menu_import)
    qt.menu_separator(plugin_menu)
    qt.add_menu_action(plugin_menu, "Data Link", menu_link)
    qt.menu_separator(plugin_menu)
    qt.add_menu_action(plugin_menu, "Go-B", menu_go_b)

    tool_bar = qt.find_add_toolbar("Blender Pipeline Toolbar")
    qt.clear_tool_bar(tool_bar)

    icon_blender = qt.get_icon("BlenderLogo.png")
    qt.add_tool_bar_action(tool_bar, icon_blender, "GoB", menu_go_b)

    if cc.is_cc():
        icon_morph = qt.get_icon("MeshIcoSphere.png")
        qt.add_tool_bar_action(tool_bar, icon_morph, "Morph", menu_go_morph)

    icon_export = qt.get_icon("BlenderExport.png")
    qt.add_tool_bar_action(tool_bar, icon_export, "Export", menu_export)

    if cc.is_cc():
        icon_import = qt.get_icon("BlenderImport.png")
        qt.add_tool_bar_action(tool_bar, icon_import, "Import", menu_import)

    icon_link = qt.get_icon("BlenderDataLink.png")
    qt.add_tool_bar_action(tool_bar, icon_link, "Data-link", menu_link)

    icon_settings = qt.get_icon("BlenderSettings.png")
    qt.add_tool_bar_action(tool_bar, icon_settings, "Settings", menu_settings)


def menu_import():
    global FBX_IMPORTER
    FBX_IMPORTER = None
    file_path = RLPy.RUi.OpenFileDialog("Fbx Files(*.fbx)")
    if file_path and file_path != "":
        FBX_IMPORTER = importer.Importer(file_path)


def menu_export():
    global FBX_EXPORTER
    FBX_EXPORTER = None
    avatar_list = RLPy.RScene.GetAvatars()
    if len(avatar_list) > 0:
        FBX_EXPORTER = exporter.Exporter(avatar_list[0])


def menu_export_iclone():
    global FBX_EXPORTER
    FBX_EXPORTER = None


def menu_link():
    link.get_data_link()


def menu_go_b():
    gob.go_b()


def menu_go_morph():
    gob.go_morph()


def menu_settings():
    global FBX_EXPORTER
    FBX_EXPORTER = None
    FBX_EXPORTER = prefs.Preferences()


def run_script():
    initialize_plugin()


