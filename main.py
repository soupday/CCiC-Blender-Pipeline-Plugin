# Copyright (C) 2023 Victor Soupday
# This file is part of CC4-Blender-Pipeline-Plugin <https://github.com/soupday/CC4-Blender-Pipeline-Plugin>
#
# CC4-Blender-Pipeline-Plugin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CC4-Blender-Pipeline-Plugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CC4-Blender-Pipeline-Plugin.  If not, see <https://www.gnu.org/licenses/>.

import RLPy
import importer
import exporter
import link
import qt
import tests

rl_plugin_info = {"ap": "CC4", "ap_version": "4.0"}

FBX_IMPORTER: importer.Importer = None
FBX_EXPORTER: exporter.Exporter = None
LINK: link.DataLink = None


def initialize_plugin():
    plugin_menu = qt.find_add_plugin_menu("Blender Pipeline")
    qt.clear_menu(plugin_menu)
    qt.add_menu_action(plugin_menu, "Export Character to Blender", menu_export)
    qt.menu_separator(plugin_menu)
    qt.add_menu_action(plugin_menu, "Import Character from Blender", menu_import)
    qt.menu_separator(plugin_menu)
    qt.add_menu_action(plugin_menu, "Data Link", menu_link)


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
        FBX_EXPORTER = exporter.Exporter()


def menu_link():
    global LINK
    if not LINK:
        LINK = link.DataLink()
    else:
        LINK.show()


def run_script():
    initialize_plugin()


