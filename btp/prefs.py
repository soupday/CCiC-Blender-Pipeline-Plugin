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

import os
import RLPy
import json
import os
import gzip
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
import os, json
from . import qt

BLENDER_PATH = None
DATALINK_FOLDER = None
DATALINK_OVERWRITE = False

class Preferences(QObject):
    window: QWindow = None
    go_b_path: str = None
    # UI
    textbox_go_b_path: QLineEdit = None
    textbox_blender_path: QLineEdit = None
    no_update: bool = False

    def __init__(self):
        QObject.__init__(self)
        self.create_window()

    def show(self):
        self.window.Show()

    def create_window(self):
        self.window, layout = qt.window("CC/iC Blender Pipeline Preferences", 400)

        qt.spacing(layout, 10)

        # Data-Link folder
        grid = qt.grid(layout)
        qt.label(grid, "Datalink Folder", row=0, col=0)
        self.textbox_go_b_path = qt.textbox(grid, DATALINK_FOLDER, update=self.update_textbox_datalink_folder,
                                            row=0, col=1)
        qt.button(grid, "Find", func=self.browse_datalink_folder, height=26, width=64, row=0, col=2)

        # Blender exe
        qt.label(grid, "Blender Executable", row=1, col=0)
        self.textbox_blender_path = qt.textbox(grid, BLENDER_PATH, update=self.update_textbox_blender_path,
                                               row=1, col=1)
        qt.button(grid, "Find", func=self.browse_blender_exe, height=26, width=64, row=1, col=2)

        qt.spacing(layout, 10)

        self.window.Show()

    def update_textbox_datalink_folder(self):
        global DATALINK_FOLDER
        if self.no_update:
            return
        self.no_update = True
        DATALINK_FOLDER = self.textbox_go_b_path.text()
        write_temp_state()
        self.no_update = False

    def update_textbox_blender_path(self):
        global BLENDER_PATH
        if self.no_update:
            return
        self.no_update = True
        BLENDER_PATH = self.textbox_blender_path.text()
        write_temp_state()
        self.no_update = False

    def browse_datalink_folder(self):
        global DATALINK_FOLDER
        folder_path = qt.browse_folder("Datalink Folder", DATALINK_FOLDER)
        if os.path.exists(folder_path):
            self.path_daz_library_root = folder_path
            self.textbox_go_b_path.setText(folder_path)
            DATALINK_FOLDER = folder_path
            write_temp_state()

    def browse_blender_exe(self):
        global BLENDER_PATH
        file_path = RLPy.RUi.OpenFileDialog("Blender Executable(*.exe)", BLENDER_PATH)
        if os.path.exists(file_path):
            self.textbox_blender_path.setText(file_path)
            BLENDER_PATH = file_path
            write_temp_state()


def read_json(json_path):
    try:
        if os.path.exists(json_path):

            # determine start of json text data
            file_bytes = open(json_path, "rb")
            bytes = file_bytes.read(3)
            file_bytes.close()
            start = 0
            is_gz = False
            # json files outputted from Visual Studio projects start with a byte mark order block (3 bytes EF BB BF)
            if bytes[0] == 0xEF and bytes[1] == 0xBB and bytes[2] == 0xBF:
                start = 3
            elif bytes[0] == 0x1F and bytes[1] == 0x8B:
                is_gz = True
                start = 0

            # read json text
            if is_gz:
                file = gzip.open(json_path, "rt")
            else:
                file = open(json_path, "rt")

            file.seek(start)
            text_data = file.read()
            json_data = json.loads(text_data)
            file.close()
            return json_data

        return None
    except:
        print(f"Error reading Json Data: {json_path}")
        return None


def get_attr(dictionary, name, default=None):
    if name in dictionary:
        return dictionary[name]
    return default


def write_json(json_data, path):
    json_object = json.dumps(json_data, indent = 4)
    with open(path, "w") as write_file:
        write_file.write(json_object)


def read_temp_state():
    global BLENDER_PATH
    global DATALINK_FOLDER
    res = RLPy.RGlobal.GetPath(RLPy.EPathType_CustomContent, "")
    temp_path = res[1]
    temp_state_path = os.path.join(temp_path, "ccic_blender_pipeline_plugin.txt")
    if os.path.exists(temp_state_path):
        temp_state_json = read_json(temp_state_path)
        if temp_state_json:
            BLENDER_PATH = get_attr(temp_state_json, "blender_path")
            DATALINK_FOLDER = get_attr(temp_state_json, "datalink_folder")


def write_temp_state():
    global BLENDER_PATH
    global DATALINK_FOLDER
    res = RLPy.RGlobal.GetPath(RLPy.EPathType_CustomContent, "")
    temp_path = res[1]
    temp_state_path = os.path.join(temp_path, "ccic_blender_pipeline_plugin.txt")
    temp_state_json = {
        "blender_path": BLENDER_PATH,
        "datalink_folder": DATALINK_FOLDER,
    }
    write_json(temp_state_json, temp_state_path)


def detect_paths():
    global BLENDER_PATH
    global DATALINK_FOLDER

    read_temp_state()

    changed = False

    if not BLENDER_PATH:
        blender_base_path = "C:\\Program Files\\Blender Foundation\\"
        blender_versions = [ "4.0", "3.6", "3.5", "3.4", "3.3", "3.2", "3.1", "3.0", "2.93", "2.92", "2.91", "2.90", "2.83" ]
        for ver in blender_versions:
            B = f"Blender {ver}"
            try_path = os.path.join(blender_base_path, B, "blender.exe")
            if os.path.exists(try_path):
                BLENDER_PATH = try_path
                changed = True
                break

    if not DATALINK_FOLDER:
        res = RLPy.RGlobal.GetPath(RLPy.EPathType_Temp, "")
        path = os.path.join(res[1], "Data Link")
        DATALINK_FOLDER = path
        changed = True

    if DATALINK_FOLDER:
        if not os.path.exists(DATALINK_FOLDER):
            os.makedirs(DATALINK_FOLDER, exist_ok=True)

    if changed:
        write_temp_state()

    print(f"using Blender Executable Path: {BLENDER_PATH}")
    print(f"Using Datalink Folder: {DATALINK_FOLDER}")