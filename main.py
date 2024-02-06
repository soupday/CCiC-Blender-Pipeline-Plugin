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
import btp.qt as qt
import btp.tests as tests
import btp.gob as gob
import btp.vars as vars

rl_plugin_info = { "ap": "iClone", "ap_version": "8.0" }

FBX_IMPORTER: importer.Importer = None
FBX_EXPORTER: exporter.Exporter = None


def initialize_plugin():
    vars.detect_paths()
    # Menu (CC4 & iClone)
    plugin_menu = qt.find_add_plugin_menu("Blender Pipeline")
    qt.clear_menu(plugin_menu)
    qt.add_menu_action(plugin_menu, "Settings", menu_link)
    qt.menu_separator(plugin_menu)
    qt.add_menu_action(plugin_menu, "Export Character to Blender", menu_export)
    qt.menu_separator(plugin_menu)
    qt.add_menu_action(plugin_menu, "Import Character from Blender", menu_import)
    qt.menu_separator(plugin_menu)
    qt.add_menu_action(plugin_menu, "Data Link", menu_link)
    qt.menu_separator(plugin_menu)
    qt.add_menu_action(plugin_menu, "Go-B", menu_go_b)
    # Toolbar (CC4 Only)
    if RLPy.RApplication.GetProductName() == "Character Creator":
        icon_blender = qt.get_icon("BlenderLogo.png")
        icon_import = qt.get_icon("BlenderImport.png")
        icon_export = qt.get_icon("BlenderExport.png")
        icon_settings = qt.get_icon("BlenderSettings.png")
        icon_link = qt.get_icon("BlenderDataLink.png")
        tool_bar = qt.find_add_toolbar("Blender Pipeline Toolbar")
        qt.clear_tool_bar(tool_bar)
        qt.add_tool_bar_action(tool_bar, icon_blender, "GoB", menu_go_b)
        qt.add_tool_bar_action(tool_bar, icon_export, None, menu_export)
        qt.add_tool_bar_action(tool_bar, icon_import, None, menu_import)
        qt.add_tool_bar_action(tool_bar, icon_link, None, menu_link)
        qt.add_tool_bar_action(tool_bar, icon_settings, None, menu_link)


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


def menu_link():
    link.get_data_link()


def menu_go_b():
    gob.go_b()


def run_script():
    initialize_plugin()


