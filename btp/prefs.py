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
from . import cc, qt, utils, vars

# Datalink prefs
BLENDER_PATH: str = None
DATALINK_FOLDER: str = None
DATALINK_OVERWRITE: bool = False
EXPORT_MORPH_MATERIALS: bool = True
DEFAULT_MORPH_SLIDER_PATH: str = "Custom/Blender"
AUTO_START_SERVICE: bool = False
MATCH_CLIENT_RATE: bool = True
DATALINK_FRAME_SYNC: bool = False
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
CC_EXPORT_MAX_SUB_LEVEL: int = -1
IC_EXPORT_MAX_SUB_LEVEL: int = -1
# Export prefs
EXPORT_PRESET: int = 0
EXPORT_BAKE_HAIR: bool = False
EXPORT_BAKE_SKIN: bool = False
EXPORT_T_POSE: bool = False
EXPORT_CURRENT_POSE: bool = False
EXPORT_CURRENT_ANIMATION: bool = False
EXPORT_SUB_LEVEL: int = -1
EXPORT_MOTION_ONLY: bool = False
EXPORT_HIK: bool = False
EXPORT_FACIAL_PROFILE: bool = False
EXPORT_REMOVE_HIDDEN: bool = False
#
TOOLBAR_STATE_CC: bool = True
TOOLBAR_STATE_IC: bool = True

BLENDER_VERSIONS = [ "4.6", "4.5", "4.4", "4.3", "4.2", "4.1", "4.0",
                     "3.6", "3.5", "3.4", "3.3", "3.2", "3.1", "3.0",
                     "2.93", "2.92", "2.91", "2.90", "2.83" ]

class Preferences(QObject):
    window: RLPy.RIDockWidget = None
    go_b_path: str = None
    # UI
    textbox_go_b_path: QLineEdit = None
    textbox_blender_path: QLineEdit = None
    checkbox_export_morph_materials: QCheckBox = None
    checkbox_auto_start_service: QCheckBox = None
    checkbox_match_client_rate: QCheckBox = None
    checkbox_datalink_frame_sync: QCheckBox = None
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
    combo_cc_export_max_sub_level: QComboBox = None
    combo_ic_export_max_sub_level: QComboBox = None
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
        W = 500
        H = 540
        if cc.is_cc():
            H = 580
        self.window, layout = qt.window(f"Blender Pipeline Plug-in Preferences", width=W, height=H, fixed=True, show_hide=self.on_show_hide)
        self.window.SetFeatures(RLPy.EDockWidgetFeatures_Closable)

        qt.spacing(layout, 10)

        # title
        grid = qt.grid(layout)
        qt.label(grid, f"DataLink Settings:", style=qt.STYLE_RL_BOLD, row=0, col=0)
        qt.label(grid, f"Version {vars.VERSION}  ", style=qt.STYLE_VERSION, row=0, col=1, align=Qt.AlignVCenter | Qt.AlignRight)
        qt.button(grid, "Detect", func=self.detect_settings, height=26, width=64, row=0, col=2)

        # DataLink folder
        qt.label(grid, "DataLink Folder", row=1, col=0)
        self.textbox_go_b_path = qt.textbox(grid, DATALINK_FOLDER, update=self.update_textbox_datalink_folder,
                                            row=1, col=1)
        qt.button(grid, "Find", func=self.browse_datalink_folder, height=26, width=64, row=1, col=2)

        # Blender exe
        qt.label(grid, "Blender Executable", row=2, col=0)
        self.textbox_blender_path = qt.textbox(grid, BLENDER_PATH, update=self.update_textbox_blender_path,
                                               row=2, col=1)
        qt.button(grid, "Find", func=self.browse_blender_exe, height=26, width=64, row=2, col=2)

        qt.spacing(layout, 10)

        col = qt.column(layout)
        self.checkbox_auto_start_service = qt.checkbox(col, "Auto-start Link Server", AUTO_START_SERVICE, update=self.update_checkbox_auto_start_service)
        self.checkbox_match_client_rate = qt.checkbox(col, "Match Client Rate", MATCH_CLIENT_RATE, update=self.update_checkbox_match_client_rate)
        self.checkbox_datalink_frame_sync = qt.checkbox(col, "Sequence Frame Sync", DATALINK_FRAME_SYNC, update=self.update_checkbox_datalink_frame_sync)

        qt.spacing(layout, 10)
        qt.separator(layout, 1)
        qt.spacing(layout, 4)

        # Export Morph Materials
        grid = qt.grid(layout)
        grid.setColumnStretch(1, 2)

        qt.label(grid, "DataLink Send Settings:", style=qt.STYLE_RL_BOLD,
                 row=0, col=0, col_span=2)

        subd_levels = { -1: "Current", 0: "SubD 0", 1: "SubD 1", 2: "SubD 2" }
        if cc.is_cc():

            qt.label(grid, "Export With:", style=qt.STYLE_NONE, row=1, col=0)
            self.combo_cc_export_mode = qt.combobox(grid, CC_EXPORT_MODE, options = [
                                                        "Bind Pose", "Current Pose", "Animation"
                                                    ], update=self.update_combo_cc_export_mode,
                                                    row=1, col=1)

            qt.label(grid, "Default Morph Slider Path", row=2, col=0)
            self.textbox_morph_slider_path = qt.textbox(grid, DEFAULT_MORPH_SLIDER_PATH, update=self.update_textbox_morph_slider_path,
                                                    row=2, col=1)

            qt.label(grid, "Max SubD-Level:", style=qt.STYLE_NONE, row=3, col=0)
            self.combo_cc_export_max_sub_level = qt.combobox(grid, subd_levels[CC_EXPORT_MAX_SUB_LEVEL],
                                                            options = [ "Current", "SubD 0", "SubD 1", "SubD 2" ],
                                                            update=self.update_combo_cc_export_max_sub_level,
                                                            row=3, col=1)

            self.checkbox_cc_use_facial_profile = qt.checkbox(grid, "Use Facial Setting", CC_USE_FACIAL_PROFILE,
                                                            update=self.update_checkbox_cc_use_facial_profile,
                                                            row=4, col=0, col_span=2)
            self.checkbox_cc_use_facial_expressions = qt.checkbox(grid, "Use Facial Expressions", CC_USE_FACIAL_EXPRESSIONS,
                                                            update=self.update_checkbox_cc_use_facial_expressions,
                                                            row=5, col=0, col_span=2)
            self.checkbox_cc_use_hik_profile = qt.checkbox(grid, "Use HIK Profile", CC_USE_HIK_PROFILE,
                                                            update=self.update_checkbox_cc_use_hik_profile,
                                                            row=6, col=0, col_span=2)
            self.checkbox_cc_delete_hidden_faces = qt.checkbox(grid, "Delete Hidden Faces", CC_DELETE_HIDDEN_FACES,
                                                            update=self.update_checkbox_cc_delete_hidden_faces,
                                                            row=7, col=0, col_span=2)
            self.checkbox_cc_bake_textures = qt.checkbox(grid, "Bake Textures", CC_BAKE_TEXTURES,
                                                            update=self.update_checkbox_cc_bake_textures,
                                                            row=8, col=0, col_span=2)
            self.checkbox_export_morph_materials = qt.checkbox(grid, "Export Materials with Send Morph", EXPORT_MORPH_MATERIALS,
                                                            update=self.update_checkbox_export_morph_materials,
                                                            row=9, col=0, col_span=2)

        else:

            qt.label(grid, "Export With:", style=qt.STYLE_NONE, row=1, col=0)
            self.combo_ic_export_mode = qt.combobox(grid, IC_EXPORT_MODE, options = [
                                                        "Bind Pose", "Current Pose", "Animation"
                                                    ], update=self.update_combo_ic_export_mode,
                                                    row=1, col=1)

            qt.label(grid, "Max SubD-Level:", style=qt.STYLE_NONE, row=2, col=0)
            self.combo_ic_export_max_sub_level = qt.combobox(grid, subd_levels[IC_EXPORT_MAX_SUB_LEVEL],
                                                            options = [ "Current", "SubD 0", "SubD 1", "SubD 2" ],
                                                            update=self.update_combo_ic_export_max_sub_level,
                                                            row=2, col=1)

            self.checkbox_ic_use_facial_profile = qt.checkbox(grid, "Use Facial Setting", IC_USE_FACIAL_PROFILE,
                                                            update=self.update_checkbox_ic_use_facial_profile,
                                                            row=3, col=0, col_span=2)
            self.checkbox_ic_use_facial_expressions = qt.checkbox(grid, "Use Facial Expressions", IC_USE_FACIAL_EXPRESSIONS,
                                                            update=self.update_checkbox_ic_use_facial_expressions,
                                                            row=4, col=0, col_span=2)
            self.checkbox_ic_use_hik_profile = qt.checkbox(grid, "Use HIK Profile", IC_USE_HIK_PROFILE,
                                                            update=self.update_checkbox_ic_use_hik_profile,
                                                            row=5, col=0, col_span=2)
            self.checkbox_ic_delete_hidden_faces = qt.checkbox(grid, "Delete Hidden Faces", IC_DELETE_HIDDEN_FACES,
                                                            update=self.update_checkbox_ic_delete_hidden_faces,
                                                            row=6, col=0, col_span=2)
            self.checkbox_ic_bake_textures = qt.checkbox(grid, "Bake Textures", IC_BAKE_TEXTURES,
                                                            update=self.update_checkbox_ic_bake_textures,
                                                            row=7, col=0, col_span=2)

        qt.spacing(layout, 10)
        qt.stretch(layout, 1)

    def refresh_ui(self):
        self.no_update = True
        if self.textbox_blender_path:
            self.textbox_blender_path.setText(BLENDER_PATH)
        if self.textbox_go_b_path:
            self.textbox_go_b_path.setText(DATALINK_FOLDER)
        self.no_update = False

    def on_show_hide(self, visible):
        if visible:
            qt.toggle_toolbar_action("Blender Pipeline Toolbar", "Blender Pipeline Settings", True)
            self.refresh_ui()
        else:
            qt.toggle_toolbar_action("Blender Pipeline Toolbar", "Blender Pipeline Settings", False)

    def detect_settings(self):
        global DATALINK_FOLDER
        # if datalink path is invalid, generate a new one
        if not check_datalink_path()[0]:
            DATALINK_FOLDER = ""
        detect_paths()
        self.textbox_blender_path.setText(BLENDER_PATH)
        self.textbox_go_b_path.setText(DATALINK_FOLDER)
        return

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
        if DATALINK_FOLDER:
            folder_path = qt.browse_folder("Datalink Folder", DATALINK_FOLDER)
        else:
            folder_path = qt.browse_folder("Datalink Folder")
        if os.path.exists(folder_path):
            self.textbox_go_b_path.setText(folder_path)
            DATALINK_FOLDER = folder_path
            write_temp_state()

    def browse_blender_exe(self):
        global BLENDER_PATH
        if BLENDER_PATH:
            file_path = RLPy.RUi.OpenFileDialog("Blender Executable(*.exe)", BLENDER_PATH)
        else:
            file_path = RLPy.RUi.OpenFileDialog("Blender Executable(*.exe)")
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

    def update_checkbox_datalink_frame_sync(self):
        global DATALINK_FRAME_SYNC
        if self.no_update:
            return
        self.no_update = True
        DATALINK_FRAME_SYNC = self.checkbox_datalink_frame_sync.isChecked()
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

    def update_combo_cc_export_max_sub_level(self):
        global CC_EXPORT_MAX_SUB_LEVEL
        if self.no_update:
            return
        self.no_update = True
        text = self.combo_cc_export_max_sub_level.currentText()
        levels = { "Current": -1, "SubD 0": 0, "SubD 1": 1, "SubD 2": 2 }
        CC_EXPORT_MAX_SUB_LEVEL = levels[text]
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

    def update_combo_ic_export_max_sub_level(self):
        global IC_EXPORT_MAX_SUB_LEVEL
        if self.no_update:
            return
        self.no_update = True
        text = self.combo_ic_export_max_sub_level.currentText()
        levels = { "Current": -1, "SubD 0": 0, "SubD 1": 1, "SubD 2": 2 }
        IC_EXPORT_MAX_SUB_LEVEL = levels[text]
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
    global DATALINK_FRAME_SYNC
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
    global CC_EXPORT_MAX_SUB_LEVEL
    global IC_EXPORT_MAX_SUB_LEVEL
    global EXPORT_PRESET
    global EXPORT_BAKE_HAIR
    global EXPORT_BAKE_SKIN
    global EXPORT_T_POSE
    global EXPORT_CURRENT_POSE
    global EXPORT_CURRENT_ANIMATION
    global EXPORT_MOTION_ONLY
    global EXPORT_HIK
    global EXPORT_FACIAL_PROFILE
    global EXPORT_REMOVE_HIDDEN
    global EXPORT_SUB_LEVEL
    global TOOLBAR_STATE_CC
    global TOOLBAR_STATE_IC

    res = RLPy.RGlobal.GetPath(RLPy.EPathType_CustomContent, "")
    temp_path = res[1]
    utils.log_info(f"Custom Content Path: {temp_path}")
    temp_state_path = os.path.join(temp_path, "ccic_blender_pipeline_plugin.txt")
    utils.log_info(f"Config File Path: {temp_state_path}")
    if os.path.exists(temp_state_path):
        temp_state_json = read_json(temp_state_path)
        if temp_state_json:
            BLENDER_PATH = get_attr(temp_state_json, "blender_path", "")
            DATALINK_FOLDER = get_attr(temp_state_json, "datalink_folder", "")
            EXPORT_MORPH_MATERIALS = get_attr(temp_state_json, "export_morph_materials", True)
            DEFAULT_MORPH_SLIDER_PATH = get_attr(temp_state_json, "default_morph_slider_path", "Custom/Blender")
            AUTO_START_SERVICE = get_attr(temp_state_json, "auto_start_service", False)
            MATCH_CLIENT_RATE = get_attr(temp_state_json, "match_client_rate", True)
            DATALINK_FRAME_SYNC = get_attr(temp_state_json, "datalink_frame_sync", False)
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
            CC_EXPORT_MAX_SUB_LEVEL = get_attr(temp_state_json, "cc_export_max_sub_level", -1)
            IC_EXPORT_MAX_SUB_LEVEL = get_attr(temp_state_json, "ic_export_max_sub_level", -1)
            EXPORT_PRESET = get_attr(temp_state_json, "export_preset", -1)
            EXPORT_BAKE_HAIR = get_attr(temp_state_json, "export_bake_hair", False)
            EXPORT_BAKE_SKIN = get_attr(temp_state_json, "export_bake_skin", False)
            EXPORT_T_POSE = get_attr(temp_state_json, "export_t_pose", False)
            EXPORT_CURRENT_POSE = get_attr(temp_state_json, "export_current_pose", False)
            EXPORT_CURRENT_ANIMATION = get_attr(temp_state_json, "export_current_animation", True)
            EXPORT_MOTION_ONLY = get_attr(temp_state_json, "export_motion_only", False)
            EXPORT_HIK = get_attr(temp_state_json, "export_hik", False)
            EXPORT_FACIAL_PROFILE = get_attr(temp_state_json, "export_facial_profile", False)
            EXPORT_REMOVE_HIDDEN = get_attr(temp_state_json, "export_remove_hidden", False)
            EXPORT_SUB_LEVEL = get_attr(temp_state_json, "export_sub_level", -1)
            TOOLBAR_STATE_CC = get_attr(temp_state_json, "toolbar_state_cc", True)
            TOOLBAR_STATE_IC = get_attr(temp_state_json, "toolbar_state_ic", True)


def write_temp_state():
    global BLENDER_PATH
    global DATALINK_FOLDER
    global EXPORT_MORPH_MATERIALS
    global DEFAULT_MORPH_SLIDER_PATH
    global AUTO_START_SERVICE
    global MATCH_CLIENT_RATE
    global DATALINK_FRAME_SYNC
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
    global CC_EXPORT_MAX_SUB_LEVEL
    global IC_EXPORT_MAX_SUB_LEVEL
    global EXPORT_PRESET
    global EXPORT_BAKE_HAIR
    global EXPORT_BAKE_SKIN
    global EXPORT_T_POSE
    global EXPORT_CURRENT_POSE
    global EXPORT_CURRENT_ANIMATION
    global EXPORT_MOTION_ONLY
    global EXPORT_HIK
    global EXPORT_FACIAL_PROFILE
    global EXPORT_REMOVE_HIDDEN
    global EXPORT_SUB_LEVEL
    global TOOLBAR_STATE_CC
    global TOOLBAR_STATE_IC

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
        "datalink_frame_sync": DATALINK_FRAME_SYNC,
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
        "cc_export_max_sub_level": CC_EXPORT_MAX_SUB_LEVEL,
        "ic_export_max_sub_level": IC_EXPORT_MAX_SUB_LEVEL,
        "export_preset": EXPORT_PRESET,
        "export_bake_hair": EXPORT_BAKE_HAIR,
        "export_bake_skin": EXPORT_BAKE_SKIN,
        "export_t_pose": EXPORT_T_POSE,
        "export_current_pose": EXPORT_CURRENT_POSE,
        "export_current_animation": EXPORT_CURRENT_ANIMATION,
        "export_motion_only": EXPORT_MOTION_ONLY,
        "export_hik": EXPORT_HIK,
        "export_facial_profile": EXPORT_FACIAL_PROFILE,
        "export_remove_hidden": EXPORT_REMOVE_HIDDEN,
        "export_sub_level": EXPORT_SUB_LEVEL,
        "toolbar_state_cc": TOOLBAR_STATE_CC,
        "toolbar_state_ic": TOOLBAR_STATE_IC,
    }
    write_json(temp_state_json, temp_state_path)


def get_program_files_path():
    current_path = utils.get_current_path()
    path, dir = os.path.split(current_path)
    while dir and "Program Files" not in dir:
        path, dir = os.path.split(path)
    if dir:
        return os.path.join(path, dir)
    drive_letters = "CDEFGHIJKLMNOPQRSTUVWXYZ"
    for drive_letter in drive_letters:
        try_path = f"{drive_letter}:\\Program Files"
        if os.path.exists(try_path):
            return try_path
    return "C:\\Program Files"


def get_blender_folder_version(blender_path):
    if blender_path:
        blender_folder = os.path.dirname(blender_path)
        for ver in BLENDER_VERSIONS:
            version_folder = os.path.join(blender_folder, ver)
            if os.path.exists(version_folder):
                return ver
    return None


def detect_paths():
    global BLENDER_PATH
    global DATALINK_FOLDER

    utils.log_info("Reading settings...")
    read_temp_state()

    changed = False

    if not BLENDER_PATH or not os.path.exists(BLENDER_PATH):
        BLENDER_PATH = ""
        utils.log_info("No valid Blender path, detecting Blender Exe")
        blender_base_path = ""
        blender_steam_path = ""
        steam_version = "0.0"
        program_files_path = get_program_files_path()
        if program_files_path:
            try_path = os.path.join(program_files_path, "Blender Foundation")
            if os.path.exists(try_path):
                blender_base_path = try_path
            program_files_x86_path = program_files_path + " (x86)"
            steam_path = os.path.join(program_files_x86_path, "Steam")
            if os.path.exists(steam_path):
                try_path = os.path.join(steam_path, "steamapps", "common", "Blender", "blender-launcher.exe")
                utils.log_info(f" - trying: {try_path}")
                if os.path.exists(try_path):
                    blender_steam_path = try_path
                    steam_version = get_blender_folder_version(blender_steam_path)
                    BLENDER_PATH = blender_steam_path
                    changed = True
                    utils.log_info(f" - Found Blender (Steam Version {steam_version})")

        # find direct Blender installs
        if blender_base_path:
            steam_version_number = float(steam_version)
            for ver in BLENDER_VERSIONS:
                ver_number = float(ver)
                # prefer steam version only if it's higher
                if steam_version_number > ver_number:
                    continue
                B = f"Blender {ver}"
                try_path = os.path.join(blender_base_path, B, "blender-launcher.exe")
                utils.log_info(f" - trying: {try_path}")
                if os.path.exists(try_path):
                    BLENDER_PATH = try_path
                    changed = True
                    utils.log_info(f" - Found!")
                    break

    if DATALINK_FOLDER:
        utils.log_info(f"Datalink folder setting: {DATALINK_FOLDER}")
        if not os.path.exists(DATALINK_FOLDER):
            utils.log_info(f" - Datalink folder not found!")
            try:
                os.makedirs(DATALINK_FOLDER, exist_ok=True)
                utils.log_info(f" - Datalink folder created.")
            except:
                utils.log_warn(f" - DataLink folder: {DATALINK_FOLDER} invalid! Using default.")
                DATALINK_FOLDER = ""

    if not DATALINK_FOLDER:
        path = cc.user_files_path("DataLink", create=True)
        DATALINK_FOLDER = path
        utils.log_info(f"No Datalink folder setting: Using user home dir: {path}")
        changed = True

    if changed:
        utils.log_info(f"Writing updated settings...")
        write_temp_state()

    utils.log_info(f"using Blender Executable Path: {BLENDER_PATH}")
    utils.log_info(f"Using Datalink Folder: {DATALINK_FOLDER}")


def get_blender_path():
    return BLENDER_PATH


def check_datalink_path(report=None, create=False, warn=False):
    global DATALINK_FOLDER
    if not report:
        report = ""

    valid = True
    write = False

    # correct old datalink folder default path (or any CC/iC temp files path)
    if utils.contains_path(DATALINK_FOLDER, cc.temp_files_path()):
        DATALINK_FOLDER = cc.user_files_path("DataLink", create=True)
        utils.log_info(f"Using corrected default DataLink path: {DATALINK_FOLDER}")
        write = True

    # if empty use user documents folder
    if not DATALINK_FOLDER:
        DATALINK_FOLDER = cc.user_files_path("DataLink", create=True)
        utils.log_info(f"Using default DataLink path: {DATALINK_FOLDER}")
        write = True

    if DATALINK_FOLDER:
        if os.path.exists(DATALINK_FOLDER):
            # if exists but not a folder, reset to user documents
            if not os.path.isdir(DATALINK_FOLDER):
                report += "Datalink path is not a folder!\n"
                utils.log_warn(f"DataLink path: {DATALINK_FOLDER} is not a folder!")
                DATALINK_FOLDER = cc.user_files_path("DataLink", create=True)
                utils.log_info(f"Using default DataLink path: {DATALINK_FOLDER}")
                write = True
        elif create:
            try:
                os.makedirs(DATALINK_FOLDER, exist_ok=True)
                utils.log_info(f"DataLink path: {DATALINK_FOLDER} created!")
            except:
                # the datalink path can't be made, reset to user documents
                utils.log_warn(f"DataLink path: {DATALINK_FOLDER} is not valid, unable to create path!")
                DATALINK_FOLDER = cc.user_files_path("DataLink", create=True)
                utils.log_info(f"Using default DataLink path: {DATALINK_FOLDER}")
                write = True

    if valid and write:
        write_temp_state()

    if warn and not valid:
        report += "\n\nPlease check plugin datalink path settings."
        qt.message_box("Path Error", report)

    return valid, report


def check_blender_path(report=None):
    blender_path = get_blender_path()
    if not report:
        report = ""

    valid = True

    if not blender_path or not os.path.exists(blender_path):
        valid = False
        report += "Blender .exe path is invalid!\n"

    return valid, report


def check_paths(quiet=False, create=False):
    report = ""
    valid = True

    datalink_valid, report = check_datalink_path(report=report, create=create)
    blender_valid, report = check_blender_path(report=report)
    valid = datalink_valid and blender_valid

    if not quiet and not valid:
        report += "\n\nPlease check plugin path settings."
        qt.message_box("Path Error", report)

    return valid


def export_animation():
    if cc.is_cc() and CC_EXPORT_MODE == "Animation":
        return True
    if cc.is_iclone() and IC_EXPORT_MODE == "Animation":
        return True
    return False


PREFERENCES: Preferences = None

def get_preferences():
    global PREFERENCES
    if not PREFERENCES:
        PREFERENCES = Preferences()
    return PREFERENCES