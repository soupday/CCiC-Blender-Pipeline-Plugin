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
from . import qt, utils, vars

BLENDER_PATH: str = None
DATALINK_FOLDER: str = None
DATALINK_OVERWRITE: bool = False
EXPORT_MORPH_MATERIALS: bool = True
DEFAULT_MORPH_SLIDER_PATH: str = "Custom/Blender"
AUTO_START_SERVICE: bool = False
MATCH_CLIENT_RATE: bool = True
CC_USE_FACIAL_PROFILE: bool = True
CC_USE_HIK_PROFILE: bool = True
CC_USE_FACIAL_EXPRESSIONS: bool = True
CC_DELETE_HIDDEN_FACES: bool = False
CC_BAKE_TEXTURES: bool = False
CC_EXPORT_MODE: str = "Animation"
IC_USE_FACIAL_PROFILE: bool = False
IC_USE_HIK_PROFILE: bool = False
IC_USE_FACIAL_EXPRESSIONS: bool = False
IC_DELETE_HIDDEN_FACES: bool = True
IC_BAKE_TEXTURES: bool = True
IC_EXPORT_MODE: str = "Animation"


class Preferences(QObject):
    window: RLPy.RIDockWidget = None
    go_b_path: str = None
    # UI
    textbox_go_b_path: QLineEdit = None
    textbox_blender_path: QLineEdit = None
    checkbox_export_morph_materials: QCheckBox = None
    checkbox_auto_start_service: QCheckBox = None
    checkbox_match_client_rate: QCheckBox = None
    checkbox_cc_use_facial_profile: QCheckBox = None
    checkbox_cc_use_hik_profile: QCheckBox = None
    checkbox_cc_use_facial_expressions: QCheckBox = None
    checkbox_cc_delete_hidden_faces: QCheckBox = None
    checkbox_cc_bake_textures: QCheckBox = None
    checkbox_ic_use_facial_profile: QCheckBox = None
    checkbox_ic_use_hik_profile: QCheckBox = None
    checkbox_ic_use_facial_expressions: QCheckBox = None
    checkbox_ic_delete_hidden_faces: QCheckBox = None
    checkbox_ic_bake_textures: QCheckBox = None
    combo_cc_export_mode: QComboBox = None
    combo_ic_export_mode: QComboBox = None
    no_update: bool = False

    def __init__(self):
        QObject.__init__(self)
        self.create_window()

    def show(self):
        self.window.Show()

    def hide(self):
        self.window.Hide()

    def is_shown(self):
        return self.window.IsVisible()

    def create_window(self):
        self.window, layout = qt.window(f"CC/iC Blender Pipeline Preferences ({vars.VERSION})", 600, show_hide=self.on_show_hide)
        self.window.SetFeatures(RLPy.EDockWidgetFeatures_Closable)

        qt.spacing(layout, 10)

        qt.label(layout, "Data-Link Settings:", style=qt.STYLE_RL_BOLD)

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

        self.checkbox_auto_start_service = qt.checkbox(layout, "Auto-start Link Server", AUTO_START_SERVICE, update=self.update_checkbox_auto_start_service)
        self.checkbox_match_client_rate = qt.checkbox(layout, "Match Client Rate", MATCH_CLIENT_RATE, update=self.update_checkbox_match_client_rate)

        qt.spacing(layout, 10)

        # Export Morph Materials
        grid = qt.grid(layout)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(3, 2)

        qt.label(grid, "Character Creator:", style=qt.STYLE_RL_BOLD,
                 row=0, col=0, col_span=2)
        self.checkbox_cc_use_facial_profile = qt.checkbox(grid, "Use Facial Profile", CC_USE_FACIAL_PROFILE,
                                                          update=self.update_checkbox_cc_use_facial_profile,
                                                          row=1, col=0, col_span=2)
        self.checkbox_cc_use_facial_expressions = qt.checkbox(grid, "Use Facial Expressions", CC_USE_FACIAL_EXPRESSIONS,
                                                              update=self.update_checkbox_cc_use_facial_expressions,
                                                              row=2, col=0, col_span=2)
        self.checkbox_cc_use_hik_profile = qt.checkbox(grid, "Use HIK Profile", CC_USE_HIK_PROFILE,
                                                       update=self.update_checkbox_cc_use_hik_profile,
                                                       row=3, col=0, col_span=2)
        self.checkbox_cc_delete_hidden_faces = qt.checkbox(grid, "Delete Hidden Faces", CC_DELETE_HIDDEN_FACES,
                                                           update=self.update_checkbox_cc_delete_hidden_faces,
                                                           row=4, col=0, col_span=2)
        self.checkbox_cc_bake_textures = qt.checkbox(grid, "Bake Textures", CC_BAKE_TEXTURES,
                                                           update=self.update_checkbox_cc_bake_textures,
                                                           row=5, col=0, col_span=2)
        self.checkbox_export_morph_materials = qt.checkbox(grid, "Export Materials with Morph", EXPORT_MORPH_MATERIALS,
                                                           update=self.update_checkbox_export_morph_materials,
                                                           row=6, col=0, col_span=2)
        qt.label(grid, "Export With:", style=qt.STYLE_NONE,
                 row=7, col=0)
        self.combo_cc_export_mode = qt.combobox(grid, CC_EXPORT_MODE, options = [
                                                    "Bind Pose", "Current Pose", "Animation"
                                                ], update=self.update_combo_cc_export_mode,
                                                row=7, col=1)

        qt.label(grid, "iClone:", style=qt.STYLE_RL_BOLD,
                 row=0, col=2, col_span=2)
        self.checkbox_ic_use_facial_profile = qt.checkbox(grid, "Use Facial Profile", IC_USE_FACIAL_PROFILE,
                                                          update=self.update_checkbox_ic_use_facial_profile,
                                                          row=1, col=2, col_span=2)
        self.checkbox_ic_use_facial_expressions = qt.checkbox(grid, "Use Facial Expressions", IC_USE_FACIAL_EXPRESSIONS,
                                                              update=self.update_checkbox_ic_use_facial_expressions,
                                                              row=2, col=2, col_span=2)
        self.checkbox_ic_use_hik_profile = qt.checkbox(grid, "Use HIK Profile", IC_USE_HIK_PROFILE,
                                                       update=self.update_checkbox_ic_use_hik_profile,
                                                       row=3, col=2, col_span=2)
        self.checkbox_ic_delete_hidden_faces = qt.checkbox(grid, "Delete Hidden Faces", IC_DELETE_HIDDEN_FACES,
                                                           update=self.update_checkbox_ic_delete_hidden_faces,
                                                           row=4, col=2, col_span=2)
        self.checkbox_ic_bake_textures = qt.checkbox(grid, "Bake Textures", IC_BAKE_TEXTURES,
                                                           update=self.update_checkbox_ic_bake_textures,
                                                           row=5, col=2, col_span=2)
        qt.label(grid, "Export With:", style=qt.STYLE_NONE,
                 row=7, col=2)
        self.combo_ic_export_mode = qt.combobox(grid, IC_EXPORT_MODE, options = [
                                                    "Bind Pose", "Current Pose", "Animation"
                                                ], update=self.update_combo_ic_export_mode,
                                                row=7, col=3)

        qt.spacing(layout, 10)

        grid = qt.grid(layout)
        qt.label(grid, "Default Morph Slider Path", row=0, col=0)
        self.textbox_morph_slider_path = qt.textbox(grid, DEFAULT_MORPH_SLIDER_PATH, update=self.update_textbox_morph_slider_path,
                                                    row=0, col=1)

        qt.spacing(layout, 10)

    def on_show_hide(self, visible):
        if visible:
            qt.toggle_toolbar_action("Blender Pipeline Toolbar", "Settings", True)
        else:
            qt.toggle_toolbar_action("Blender Pipeline Toolbar", "Settings", False)

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

    def update_checkbox_auto_start_service(self):
        global AUTO_START_SERVICE
        if self.no_update:
            return
        self.no_update = True
        AUTO_START_SERVICE = self.checkbox_auto_start_service.isChecked()
        write_temp_state()
        self.no_update = False

    def update_checkbox_match_client_rate(self):
        global MATCH_CLIENT_RATE
        if self.no_update:
            return
        self.no_update = True
        MATCH_CLIENT_RATE = self.checkbox_match_client_rate.isChecked()
        write_temp_state()
        self.no_update = False

    def update_checkbox_export_morph_materials(self):
        global EXPORT_MORPH_MATERIALS
        if self.no_update:
            return
        self.no_update = True
        EXPORT_MORPH_MATERIALS = self.checkbox_export_morph_materials.isChecked()
        write_temp_state()
        self.no_update = False

    def update_checkbox_cc_use_facial_profile(self):
        global CC_USE_FACIAL_PROFILE
        if self.no_update:
            return
        self.no_update = True
        CC_USE_FACIAL_PROFILE = self.checkbox_cc_use_facial_profile.isChecked()
        write_temp_state()
        self.no_update = False

    def update_checkbox_cc_use_hik_profile(self):
        global CC_USE_HIK_PROFILE
        if self.no_update:
            return
        self.no_update = True
        CC_USE_HIK_PROFILE = self.checkbox_cc_use_hik_profile.isChecked()
        write_temp_state()
        self.no_update = False

    def update_checkbox_cc_use_facial_expressions(self):
        global CC_USE_FACIAL_EXPRESSIONS
        if self.no_update:
            return
        self.no_update = True
        CC_USE_FACIAL_EXPRESSIONS = self.checkbox_cc_use_facial_expressions.isChecked()
        write_temp_state()
        self.no_update = False

    def update_checkbox_cc_delete_hidden_faces(self):
        global CC_DELETE_HIDDEN_FACES
        if self.no_update:
            return
        self.no_update = True
        CC_DELETE_HIDDEN_FACES = self.checkbox_cc_delete_hidden_faces.isChecked()
        write_temp_state()
        self.no_update = False

    def update_checkbox_cc_bake_textures(self):
        global CC_BAKE_TEXTURES
        if self.no_update:
            return
        self.no_update = True
        CC_BAKE_TEXTURES = self.checkbox_cc_bake_textures.isChecked()
        write_temp_state()
        self.no_update = False

    def update_combo_cc_export_mode(self):
        global CC_EXPORT_MODE
        if self.no_update:
            return
        self.no_update = True
        CC_EXPORT_MODE = self.combo_cc_export_mode.currentText()
        write_temp_state()
        self.no_update = False

    def update_checkbox_ic_use_facial_profile(self):
        global IC_USE_FACIAL_PROFILE
        if self.no_update:
            return
        self.no_update = True
        IC_USE_FACIAL_PROFILE = self.checkbox_ic_use_facial_profile.isChecked()
        write_temp_state()
        self.no_update = False

    def update_checkbox_ic_use_hik_profile(self):
        global IC_USE_HIK_PROFILE
        if self.no_update:
            return
        self.no_update = True
        IC_USE_HIK_PROFILE = self.checkbox_ic_use_hik_profile.isChecked()
        write_temp_state()
        self.no_update = False

    def update_checkbox_ic_use_facial_expressions(self):
        global IC_USE_FACIAL_EXPRESSIONS
        if self.no_update:
            return
        self.no_update = True
        IC_USE_FACIAL_EXPRESSIONS = self.checkbox_ic_use_facial_expressions.isChecked()
        write_temp_state()
        self.no_update = False

    def update_textbox_morph_slider_path(self):
        global DEFAULT_MORPH_SLIDER_PATH
        if self.no_update:
            return
        self.no_update = True
        DEFAULT_MORPH_SLIDER_PATH = self.textbox_morph_slider_path.text()
        write_temp_state()
        self.no_update = False

    def update_checkbox_ic_delete_hidden_faces(self):
        global IC_DELETE_HIDDEN_FACES
        if self.no_update:
            return
        self.no_update = True
        IC_DELETE_HIDDEN_FACES = self.checkbox_ic_delete_hidden_faces.isChecked()
        write_temp_state()
        self.no_update = False

    def update_checkbox_ic_bake_textures(self):
        global IC_BAKE_TEXTURES
        if self.no_update:
            return
        self.no_update = True
        IC_BAKE_TEXTURES = self.checkbox_ic_bake_textures.isChecked()
        write_temp_state()
        self.no_update = False

    def update_combo_ic_export_mode(self):
        global IC_EXPORT_MODE
        if self.no_update:
            return
        self.no_update = True
        IC_EXPORT_MODE = self.combo_ic_export_mode.currentText()
        write_temp_state()
        self.no_update = False


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
        utils.log_info(f"Error reading Json Data: {json_path}")
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
    global EXPORT_MORPH_MATERIALS
    global DEFAULT_MORPH_SLIDER_PATH
    global AUTO_START_SERVICE
    global MATCH_CLIENT_RATE
    global CC_USE_FACIAL_PROFILE
    global CC_USE_HIK_PROFILE
    global CC_USE_FACIAL_EXPRESSIONS
    global CC_DELETE_HIDDEN_FACES
    global CC_BAKE_TEXTURES
    global IC_USE_FACIAL_PROFILE
    global IC_USE_HIK_PROFILE
    global IC_USE_FACIAL_EXPRESSIONS
    global IC_DELETE_HIDDEN_FACES
    global IC_BAKE_TEXTURES
    global CC_EXPORT_MODE
    global IC_EXPORT_MODE
    res = RLPy.RGlobal.GetPath(RLPy.EPathType_CustomContent, "")
    temp_path = res[1]
    temp_state_path = os.path.join(temp_path, "ccic_blender_pipeline_plugin.txt")
    if os.path.exists(temp_state_path):
        temp_state_json = read_json(temp_state_path)
        if temp_state_json:
            BLENDER_PATH = get_attr(temp_state_json, "blender_path", "")
            DATALINK_FOLDER = get_attr(temp_state_json, "datalink_folder", "")
            EXPORT_MORPH_MATERIALS = get_attr(temp_state_json, "export_morph_materials", True)
            DEFAULT_MORPH_SLIDER_PATH = get_attr(temp_state_json, "default_morph_slider_path", "Custom/Blender")
            AUTO_START_SERVICE = get_attr(temp_state_json, "auto_start_service", False)
            MATCH_CLIENT_RATE = get_attr(temp_state_json, "match_client_rate", True)
            CC_USE_FACIAL_PROFILE = get_attr(temp_state_json, "cc_use_facial_profile", True)
            CC_USE_HIK_PROFILE = get_attr(temp_state_json, "cc_use_hik_profile", True)
            CC_USE_FACIAL_EXPRESSIONS = get_attr(temp_state_json, "cc_use_facial_expressions", True)
            CC_DELETE_HIDDEN_FACES = get_attr(temp_state_json, "cc_delete_hidden_faces", False)
            CC_BAKE_TEXTURES = get_attr(temp_state_json, "cc_bake_textures", False)
            IC_USE_FACIAL_PROFILE = get_attr(temp_state_json, "ic_use_facial_profile", False)
            IC_USE_HIK_PROFILE = get_attr(temp_state_json, "ic_use_hik_profile", False)
            IC_USE_FACIAL_EXPRESSIONS = get_attr(temp_state_json, "ic_use_facial_expressions", False)
            IC_DELETE_HIDDEN_FACES = get_attr(temp_state_json, "ic_delete_hidden_faces", True)
            IC_BAKE_TEXTURES = get_attr(temp_state_json, "ic_bake_textures", True)
            CC_EXPORT_MODE = get_attr(temp_state_json, "cc_export_mode", "Animation")
            IC_EXPORT_MODE = get_attr(temp_state_json, "ic_export_mode", "Animation")


def write_temp_state():
    global BLENDER_PATH
    global DATALINK_FOLDER
    global EXPORT_MORPH_MATERIALS
    global DEFAULT_MORPH_SLIDER_PATH
    global AUTO_START_SERVICE
    global MATCH_CLIENT_RATE
    global CC_USE_FACIAL_PROFILE
    global CC_USE_HIK_PROFILE
    global CC_USE_FACIAL_EXPRESSIONS
    global CC_DELETE_HIDDEN_FACES
    global CC_BAKE_TEXTURES
    global IC_USE_FACIAL_PROFILE
    global IC_USE_HIK_PROFILE
    global IC_USE_FACIAL_EXPRESSIONS
    global IC_DELETE_HIDDEN_FACES
    global IC_BAKE_TEXTURES
    global CC_EXPORT_MODE
    global IC_EXPORT_MODE
    res = RLPy.RGlobal.GetPath(RLPy.EPathType_CustomContent, "")
    temp_path = res[1]
    temp_state_path = os.path.join(temp_path, "ccic_blender_pipeline_plugin.txt")
    temp_state_json = {
        "blender_path": BLENDER_PATH,
        "datalink_folder": DATALINK_FOLDER,
        "export_morph_materials": EXPORT_MORPH_MATERIALS,
        "default_morph_slider_path": DEFAULT_MORPH_SLIDER_PATH,
        "auto_start_service": AUTO_START_SERVICE,
        "match_client_rate": MATCH_CLIENT_RATE,
        "cc_use_facial_profile": CC_USE_FACIAL_PROFILE,
        "cc_use_hik_profile": CC_USE_HIK_PROFILE,
        "cc_use_facial_expressions": CC_USE_FACIAL_EXPRESSIONS,
        "cc_delete_hidden_faces": CC_DELETE_HIDDEN_FACES,
        "cc_bake_textures": CC_BAKE_TEXTURES,
        "ic_use_facial_profile": IC_USE_FACIAL_PROFILE,
        "ic_use_hik_profile": IC_USE_HIK_PROFILE,
        "ic_use_facial_expressions": IC_USE_FACIAL_EXPRESSIONS,
        "ic_delete_hidden_faces": IC_DELETE_HIDDEN_FACES,
        "ic_bake_textures": IC_BAKE_TEXTURES,
        "cc_export_mode": CC_EXPORT_MODE,
        "ic_export_mode": IC_EXPORT_MODE,
    }
    write_json(temp_state_json, temp_state_path)


def detect_paths():
    global BLENDER_PATH
    global DATALINK_FOLDER

    read_temp_state()

    changed = False

    if not BLENDER_PATH:
        blender_base_path = "C:\\Program Files\\Blender Foundation\\"
        blender_versions = [ "4.3", "4.2", "4.1", "4.0", "3.6", "3.5", "3.4", "3.3", "3.2", "3.1", "3.0", "2.93", "2.92", "2.91", "2.90", "2.83" ]
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

    utils.log_info(f"using Blender Executable Path: {BLENDER_PATH}")
    utils.log_info(f"Using Datalink Folder: {DATALINK_FOLDER}")


def check_paths():
    global BLENDER_PATH
    global DATALINK_FOLDER

    report = ""
    valid = True

    if DATALINK_FOLDER:
        if not os.path.exists(DATALINK_FOLDER):
            os.makedirs(DATALINK_FOLDER, exist_ok=True)

    if not DATALINK_FOLDER:
        valid = False
        report += "Invalid Datalink folder!\n"

    if os.path.exists(DATALINK_FOLDER):
        if not os.path.isdir(DATALINK_FOLDER):
            valid = False
            report += "Datalink path is not a folder!\n"
    else:
        valid = False
        report += "Datalink folder could not be created!\n"

    if not BLENDER_PATH or not os.path.exists(BLENDER_PATH):
        valid = False
        report += "Blender .exe path is invalid!\n"

    if not valid:
        report += "\n\nPlease check plugin path settings."
        qt.message_box("Path Error", report)

    return valid

PREFERENCES: Preferences = None

def get_preferences():
    global PREFERENCES
    if not PREFERENCES:
        PREFERENCES = Preferences()
    return PREFERENCES