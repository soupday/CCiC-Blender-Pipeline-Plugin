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

from RLPy import *
import PySide2
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
import os
from . import blender, cc, qt, prefs, utils, vars


FBX_EXPORTER = None


class Exporter:
    base_path = ""
    fbx_path = "C:/folder/dummy.fbx"
    folder = "C:/folder"
    fbx_file = "dummy.fbx"
    key_file = "C:/folder/dummy.fbxkey"
    character_id = "dummy"
    json_path = "C:/folder/dummy.json"
    hik_path = "C:/folder/dummy.3dxProfile"
    profile_path = "C:/folder/dummy.ccFacialProfile"
    json_data = None
    avatar: RIAvatar = None # type: ignore
    prop: RIProp = None # type: ignore
    avatars = None
    props = None
    window_options = None
    window_progress = None
    progress_count = 0
    progress_bar = None
    check_bakehair = None
    check_bakeskin = None
    check_t_pose = None
    check_current_pose = None
    check_current_animation = None
    check_animation_only = None
    check_hik_data = None
    check_profile_data = None
    check_remove_hidden = None
    option_preset = 0
    option_bakehair = False
    option_bakeskin = False
    option_t_pose = False
    option_current_pose = False
    option_current_animation = False
    option_animation_only = False
    option_hik_data = False
    option_profile_data = False
    option_remove_hidden = False
    preset_button_1 = None
    preset_button_2 = None
    preset_button_3 = None
    label_desc = None
    no_options = False


    def __init__(self, objects, no_window=False):
        if type(objects) is not list:
            objects = [ objects ]
        self.avatars = [ o for o in objects if type(o) is RIAvatar ]
        self.props = [ o for o in objects if type(o) is RIProp ]

        self.option_preset = prefs.EXPORT_PRESET
        self.option_bakehair = prefs.EXPORT_BAKE_HAIR
        self.option_bakeskin = prefs.EXPORT_BAKE_SKIN
        self.option_t_pose = prefs.EXPORT_T_POSE
        self.option_current_pose = prefs.EXPORT_CURRENT_POSE
        self.option_current_animation = prefs.EXPORT_CURRENT_ANIMATION
        self.option_animation_only = prefs.EXPORT_MOTION_ONLY
        self.option_hik_data = prefs.EXPORT_HIK
        self.option_profile_data = prefs.EXPORT_FACIAL_PROFILE
        self.option_remove_hidden = prefs.EXPORT_REMOVE_HIDDEN

        utils.log("======================")
        utils.log("New Export")

        if self.avatars:
            utils.log("Avatars:")
            for avatar in self.avatars:
                utils.log(f" - {avatar.GetName()}")

        if self.props:
            utils.log("Props:")
            for prop in self.props:
                utils.log(f" - {prop.GetName()}")

        if not no_window:
            self.create_options_window()

    def clean_up_globals(self):
        global FBX_EXPORTER
        FBX_EXPORTER = None

    def set_avatar(self, avatar: RIAvatar):
        self.avatar = avatar
        self.prop = None

    def set_prop(self, prop: RIProp):
        self.avatar = None
        self.prop = prop

    def set_base_path(self, file_path, create=False, show=False):
        base_path = os.path.splitext(file_path)[0]
        base_dir, base_file = os.path.split(file_path)
        base_name, base_ext = os.path.splitext(base_file)
        if os.path.exists(base_path) and not os.path.isdir(base_path):
            base_path = utils.get_unique_folder_path(base_dir, base_name)
        self.base_path = os.path.normpath(base_path)
        if create:
            os.makedirs(base_path, exist_ok=True)
        if show:
            os.startfile(base_path)

    def set_multi_paths(self, object, motion_only=False):
        base_path = self.base_path
        ext = ".iCCX"
        if type(object) is RIAvatar or type(object) is RIProp:
            ext = ".Fbx"
        name = object.GetName()
        if motion_only:
            self.fbx_path = os.path.join(base_path, f"{name}_motion{ext}")
        else:
            self.fbx_path = os.path.join(base_path, f"{name}{ext}")
        self.fbx_file = os.path.basename(self.fbx_path)
        self.folder = os.path.dirname(self.fbx_path)
        self.character_id = os.path.splitext(self.fbx_file)[0]
        self.key_file = os.path.join(self.folder, self.character_id + ".fbxkey")
        self.json_path = os.path.join(self.folder, self.character_id + ".json")
        self.hik_path = os.path.join(self.folder, self.character_id + ".3dxProfile")
        self.profile_path = os.path.join(self.folder, self.character_id + ".ccFacialProfile")

    def set_paths(self, file_path, motion_only=False):
        file_path = os.path.normpath(file_path)
        self.base_path = os.path.splitext(file_path)[0]
        ext = ".Fbx"
        if motion_only and not self.base_path.endswith("_motion"):
            self.fbx_path = f"{self.base_path}_motion{ext}"
        else:
            self.fbx_path = f"{self.base_path}{ext}"
        self.fbx_path = file_path
        self.fbx_file = os.path.basename(self.fbx_path)
        self.folder = os.path.dirname(self.fbx_path)
        self.character_id = os.path.splitext(self.fbx_file)[0]
        self.key_file = os.path.join(self.folder, self.character_id + ".fbxkey")
        self.json_path = os.path.join(self.folder, self.character_id + ".json")
        self.hik_path = os.path.join(self.folder, self.character_id + ".3dxProfile")
        self.profile_path = os.path.join(self.folder, self.character_id + ".ccFacialProfile")

    def create_options_window(self):
        title = f"Blender Export ({vars.VERSION})"
        self.window_options, layout = qt.window(title, width=500)
        self.window_options.SetFeatures(EDockWidgetFeatures_Closable)

        # TODO Remember the preset and remember the settings (only reset settings if preset pressed)

        qt.label(layout, "Presets:", style=qt.STYLE_TITLE)

        row = qt.row(layout)
        self.preset_button_1 = qt.button(row, "Character Only", self.preset_mesh_only, height=32, toggle=True, value=True)
        self.preset_button_2 = qt.button(row, "Animated Character", self.preset_current_pose, height=32, toggle=True, value=False)
        self.preset_button_3 = qt.button(row, "Blender > Unity", self.preset_unity, height=32, toggle=True, value=False)
        self.label_desc = qt.label(layout, "", "color: #d2ff7b; font: italic 13px", wrap=True)

        qt.spacing(layout, 10)

        # Avatars

        if self.avatars:

            avatar_list = ""
            for avatar in self.avatars:
                if avatar_list:
                    avatar_list += ", "
                avatar_list += avatar.GetName()

            row = qt.row(layout)
            col_1 = qt.column(row)
            col_2 = qt.column(row)
            qt.label(col_1, f"Avatars:  ({len(self.avatars)}) ", style=qt.STYLE_TITLE, width=80)
            qt.label(col_2, avatar_list, style=qt.STYLE_ITALIC_SMALL, no_size=True)

            qt.spacing(layout, 4)

            row = qt.row(layout)
            col_1 = qt.column(row)
            col_2 = qt.column(row)
            qt.label(col_1, "", width=16)

            needs_hik_option = True
            needs_profile_option = False
            self.check_hik_data = None
            self.check_profile_data = None
            for avatar in self.avatars:
                if cc.is_avatar_non_standard(avatar):
                    needs_hik_profile = True
                    needs_profile_option = True
                elif cc.is_avatar_standard(avatar):
                    needs_profile_option = True

            grid = qt.grid(col_2)
            if needs_hik_option or needs_profile_option:
                if needs_hik_option:
                    self.check_hik_data = qt.checkbox(grid, "Export HIK Profile", False, row=0, col=0)
                if needs_profile_option:
                    self.check_profile_data = qt.checkbox(grid, "Export Facial Expression Profile", False, row=0, col=1)

            self.check_bakehair = qt.checkbox(grid, "Bake Hair Diffuse and Specular", False, row=1, col=0)
            self.check_bakeskin = qt.checkbox(grid, "Bake Skin Diffuse", False, row=1, col=1)
            self.check_remove_hidden = qt.checkbox(grid, "Delete Hidden Faces", False, row=2, col=0)
            self.check_t_pose = qt.checkbox(grid, "Bindpose as T-Pose", False, row=2, col=1)

            qt.spacing(col_2, 10)

        # Props

        if self.props:

            prop_list = ""
            for prop in self.props:
                if prop_list:
                    prop_list += ", "
                prop_list += prop.GetName()

            row = qt.row(layout)
            col_1 = qt.column(row)
            col_2 = qt.column(row)
            qt.label(col_1, f"Props:  ({len(self.props)}) ", style=qt.STYLE_TITLE, width=80)
            qt.label(col_2, prop_list, style=qt.STYLE_ITALIC_SMALL, no_size=True)

            qt.spacing(layout, 4)

        # Motion

        if True:

            qt.label(layout, f"Motion Options:", style=qt.STYLE_TITLE, width=100)

            qt.spacing(layout, 4)

            row = qt.row(layout)
            col_1 = qt.column(row)
            col_2 = qt.column(row)
            qt.label(col_1, "", width=16)

            grid = qt.grid(col_2)
            self.check_current_pose = qt.checkbox(grid, "Mesh with Pose", False, row=0, col=0,
                                                  update=lambda: self.check_mex("POSE"))
            self.check_current_animation = qt.checkbox(grid, "Mesh and Motion", False, row=0, col=1,
                                                       update=lambda: self.check_mex("ANIM"))
            self.check_animation_only = qt.checkbox(grid, "Motion Only", False, row=0, col=2,
                                                    update=lambda: self.check_mex("MOTION"))

        qt.button(layout, "Export", self.do_export, height=64)

        if self.option_preset == -1:
            self.preset_current_pose()
        else:
            self.update_options()
        self.window_options.Show()

    def create_progress_window(self):
        title = "Blender Export"
        self.window_progress, layout = qt.window(title, width=500)
        qt.spacing(layout, 8)
        label = qt.label(layout, f"Export Progress ...")
        label.setAlignment(Qt.AlignHCenter)
        qt.spacing(layout, 16)
        self.progress_bar = qt.progress(layout, 0, 0, 0, "Intializing ...", width=500)
        qt.stretch(layout, 0)
        self.progress_count = 0
        num_avatars = len(self.avatars)
        num_props = len(self.props)
        avatar_steps = 3 # fbx export
        avatar_steps += 1 # add physics
        if self.option_hik_data:
            avatar_steps += 1 # add hik
        if self.option_profile_data:
            avatar_steps += 2 # add facial profile
        steps = avatar_steps * num_avatars + num_props * 3
        qt.progress_range(self.progress_bar, 0, steps - 1)
        self.window_progress.Show()

    def update_progress(self, inc, text = "", events = False):
        self.progress_count += inc
        qt.progress_update(self.progress_bar, self.progress_count, text)
        if events:
            qt.do_events()

    def close_progress_window(self):
        if self.window_progress:
            self.window_progress.Close()

    def check_mex(self, id):
        if id == "ANIM":
            if self.check_current_animation.isChecked():
                self.check_current_pose.setChecked(False)
                self.check_animation_only.setChecked(False)
        elif id == "POSE":
            if self.check_current_pose.isChecked():
                self.check_current_animation.setChecked(False)
                self.check_animation_only.setChecked(False)
        elif id == "MOTION":
            if self.check_animation_only.isChecked():
                self.check_current_animation.setChecked(False)
                self.check_current_pose.setChecked(False)

    def update_options(self):
        self.preset_button_1.setChecked(self.option_preset == 0)
        self.preset_button_2.setChecked(self.option_preset == 1)
        self.preset_button_3.setChecked(self.option_preset == 2)
        self.preset_button_1.setStyleSheet(qt.STYLE_RL_TAB_SELECTED if self.option_preset == 0 else qt.STYLE_RL_TAB)
        self.preset_button_2.setStyleSheet(qt.STYLE_RL_TAB_SELECTED if self.option_preset == 1 else qt.STYLE_RL_TAB)
        self.preset_button_3.setStyleSheet(qt.STYLE_RL_TAB_SELECTED if self.option_preset == 2 else qt.STYLE_RL_TAB)
        self.label_desc.setText(self.preset_description(self.option_preset))
        if self.check_hik_data: self.check_hik_data.setChecked(self.option_hik_data)
        if self.check_profile_data: self.check_profile_data.setChecked(self.option_profile_data)
        if self.check_bakehair: self.check_bakehair.setChecked(self.option_bakehair)
        if self.check_bakeskin: self.check_bakeskin.setChecked(self.option_bakeskin)
        if self.check_t_pose: self.check_t_pose.setChecked(self.option_t_pose)
        if self.check_current_pose: self.check_current_pose.setChecked(self.option_current_pose)
        if self.check_current_animation: self.check_current_animation.setChecked(self.option_current_animation)
        if self.check_animation_only: self.check_animation_only.setChecked(self.option_animation_only)
        if self.check_remove_hidden: self.check_remove_hidden.setChecked(self.option_remove_hidden)

    def fetch_options(self):
        if self.preset_button_1.isChecked():
            self.option_preset = 0
        elif self.preset_button_2.isChecked():
            self.option_preset = 1
        elif self.preset_button_3.isChecked():
            self.option_preset = 2
        prefs.EXPORT_PRESET = self.option_preset
        if self.check_bakehair:
            self.option_bakehair = self.check_bakehair.isChecked()
            prefs.EXPORT_BAKE_HAIR = self.option_bakehair
        if self.check_bakeskin:
            self.option_bakeskin = self.check_bakeskin.isChecked()
            prefs.EXPORT_BAKE_SKIN = self.option_bakeskin
        if self.check_current_pose:
            self.option_current_pose = self.check_current_pose.isChecked()
            prefs.EXPORT_CURRENT_POSE = self.option_current_pose
        if self.check_current_animation:
            self.option_current_animation = self.check_current_animation.isChecked()
            prefs.EXPORT_CURRENT_ANIMATION = self.option_current_animation
        if self.check_animation_only:
            self.option_animation_only = self.check_animation_only.isChecked()
            prefs.EXPORT_MOTION_ONLY = self.option_animation_only
        if self.check_hik_data:
            self.option_hik_data = self.check_hik_data.isChecked()
            prefs.EXPORT_HIK = self.option_hik_data
        if self.check_profile_data:
            self.option_profile_data = self.check_profile_data.isChecked()
            prefs.EXPORT_FACIAL_PROFILE = self.option_profile_data
        if self.check_t_pose:
            self.option_t_pose = self.check_t_pose.isChecked()
            prefs.EXPORT_T_POSE = self.option_t_pose
        if self.check_remove_hidden:
            self.option_remove_hidden = self.check_remove_hidden.isChecked()
            prefs.EXPORT_REMOVE_HIDDEN = self.option_remove_hidden
        prefs.write_temp_state()

    def preset_description(self, preset):
        if preset == 0:
            return ("Round Trip Editing:\n\n" +
                    "Export the character as mesh only in the bind pose without animation, " +
                    "with full facial expression data and human IK profile (non-standard), " +
                    "for complete round trip character editing.")
        elif preset == 1:
            return ("Accessory Creation / Replace Mesh:\n\n" +
                    "Export the full character in the current pose, " +
                    "for accessory creation or replacement mesh editing.\n")
        elif preset == 2:
            return ("Blender to Unity Pipeline:\n\n" +
                    "Export the character with hidden faces removed, skin & hair textures baked and " +
                    "with T-pose bind pose, for editing in Blender before exporting from Blender to Unity.")
        return "No preset selected!\n\n\n\n"


    def preset_mesh_only(self):
        self.option_preset = 0
        self.preset_button_1.setChecked(True)
        self.preset_button_2.setChecked(False)
        self.preset_button_3.setChecked(False)
        self.preset_button_1.setStyleSheet(qt.STYLE_RL_TAB_SELECTED)
        self.preset_button_2.setStyleSheet(qt.STYLE_RL_TAB)
        self.preset_button_3.setStyleSheet(qt.STYLE_RL_TAB)
        self.label_desc.setText(self.preset_description(self.option_preset))
        self.option_bakehair = False
        self.option_bakeskin = False
        self.option_t_pose = False
        self.option_current_pose = False
        self.option_current_animation = False
        self.option_animation_only = False
        self.option_remove_hidden = False
        if cc.is_cc():
            self.option_profile_data = prefs.CC_USE_FACIAL_PROFILE
            self.option_hik_data = prefs.CC_USE_HIK_PROFILE
            self.check_non_standard_export()
        else:
            self.option_profile_data = prefs.IC_USE_FACIAL_PROFILE
            self.option_hik_data = prefs.IC_USE_HIK_PROFILE
        self.update_options()

    def preset_current_pose(self):
        self.option_preset = 1
        self.preset_button_1.setChecked(False)
        self.preset_button_2.setChecked(True)
        self.preset_button_3.setChecked(False)
        self.preset_button_1.setStyleSheet(qt.STYLE_RL_TAB)
        self.preset_button_2.setStyleSheet(qt.STYLE_RL_TAB_SELECTED)
        self.preset_button_3.setStyleSheet(qt.STYLE_RL_TAB)
        self.label_desc.setText(self.preset_description(self.option_preset))
        self.option_t_pose = False
        self.option_current_pose = prefs.CC_EXPORT_MODE != "Animation"
        self.option_current_animation = prefs.CC_EXPORT_MODE == "Animation"
        self.option_animation_only = False
        self.option_profile_data = False
        self.option_hik_data = prefs.CC_USE_HIK_PROFILE
        if cc.is_cc():
            self.option_bakehair = prefs.CC_BAKE_TEXTURES
            self.option_bakeskin = prefs.CC_BAKE_TEXTURES
            self.option_remove_hidden = prefs.CC_DELETE_HIDDEN_FACES
            self.check_non_standard_export()
        else:
            self.option_bakehair = prefs.IC_BAKE_TEXTURES
            self.option_bakeskin = prefs.IC_BAKE_TEXTURES
            self.option_remove_hidden = prefs.IC_DELETE_HIDDEN_FACES
        self.update_options()

    def preset_unity(self):
        self.option_preset = 2
        self.preset_button_1.setChecked(False)
        self.preset_button_2.setChecked(False)
        self.preset_button_3.setChecked(True)
        self.preset_button_1.setStyleSheet(qt.STYLE_RL_TAB)
        self.preset_button_2.setStyleSheet(qt.STYLE_RL_TAB)
        self.preset_button_3.setStyleSheet(qt.STYLE_RL_TAB_SELECTED)
        self.label_desc.setText(self.preset_description(self.option_preset))
        self.option_hik_data = False
        self.option_profile_data = False
        self.option_t_pose = True
        self.option_current_pose = False
        self.option_current_animation = False
        self.option_animation_only = False
        self.option_remove_hidden = True
        if cc.is_cc():
            self.option_bakehair = prefs.CC_BAKE_TEXTURES
            self.option_bakeskin = prefs.CC_BAKE_TEXTURES
        else:
            self.option_bakehair = prefs.IC_BAKE_TEXTURES
            self.option_bakeskin = prefs.IC_BAKE_TEXTURES
        self.update_options()

    def close_options_window(self):
        if self.window_options:
            self.window_options.Close()
        self.window_options = None
        self.check_bakehair = None
        self.check_bakeskin = None
        self.check_current_pose = None
        self.check_current_animation = None
        self.check_hik_data = None
        self.check_profile_data = None
        self.check_t_pose = None
        self.check_remove_hidden = None

    def check_non_standard_export(self):
        # non standard characters, especially actorbuild and actorscan
        # need the facial and HIK profile to come back into CC4
        if cc.is_cc():
            for avatar in self.avatars:
                if cc.is_avatar_non_standard(avatar):
                    self.option_hik_data = True
                    self.option_profile_data = True
                    return

    def set_datalink_export(self):
        self.no_options = True
        self.option_t_pose = False
        self.option_animation_only = False
        if cc.is_cc():
            self.option_bakehair = prefs.CC_BAKE_TEXTURES
            self.option_bakeskin = prefs.CC_BAKE_TEXTURES
            self.option_remove_hidden = prefs.CC_DELETE_HIDDEN_FACES
            if prefs.CC_EXPORT_MODE == "Current Pose":
                self.option_current_animation = False
                self.option_current_pose = True
            elif prefs.CC_EXPORT_MODE == "Animation":
                self.option_current_animation = True
                self.option_current_pose = False
            else:
                self.option_current_animation = False
                self.option_current_pose = False
            self.option_hik_data = prefs.CC_USE_HIK_PROFILE
            self.option_profile_data = prefs.CC_USE_FACIAL_PROFILE
            self.check_non_standard_export()
        else:
            self.option_bakehair = prefs.IC_BAKE_TEXTURES
            self.option_bakeskin = prefs.IC_BAKE_TEXTURES
            self.option_remove_hidden = prefs.IC_DELETE_HIDDEN_FACES
            if prefs.IC_EXPORT_MODE == "Current Pose":
                self.option_current_animation = False
                self.option_current_pose = True
            elif prefs.IC_EXPORT_MODE == "Animation":
                self.option_current_animation = True
                self.option_current_pose = False
            else:
                self.option_current_animation = False
                self.option_current_pose = False
            self.option_hik_data = prefs.IC_USE_HIK_PROFILE
            self.option_profile_data = prefs.IC_USE_FACIAL_PROFILE

    def set_update_replace_export(self, full_avatar=False):
        self.no_options = True
        self.option_t_pose = False
        self.option_bakehair = prefs.CC_BAKE_TEXTURES
        self.option_bakeskin = prefs.CC_BAKE_TEXTURES
        self.option_remove_hidden = prefs.CC_DELETE_HIDDEN_FACES if full_avatar else False
        self.option_current_animation = False
        self.option_current_pose = False
        self.option_animation_only = False
        self.option_hik_data = prefs.CC_USE_HIK_PROFILE if full_avatar else False
        self.option_profile_data = prefs.CC_USE_FACIAL_PROFILE if full_avatar else False
        if full_avatar:
            self.check_non_standard_export()

    def set_datalink_motion_export(self):
        self.no_options = True
        self.option_t_pose = False
        self.option_bakehair = False
        self.option_bakeskin = False
        self.option_remove_hidden = False
        self.option_current_animation = True
        self.option_current_pose = False
        self.option_animation_only = True
        self.option_hik_data = False
        self.option_profile_data = False

    def do_export(self, file_path=None):
        multi_export = (len(self.avatars) + len(self.props) > 1)
        single_export = (len(self.avatars) + len(self.props) == 1)
        if not file_path:
            file_path = RUi.SaveFileDialog("Fbx Files(*.fbx)")
        self.create_progress_window()
        self.update_progress(0, "Exporting ...", True)
        if file_path and file_path != "":
            if not self.no_options:
                self.fetch_options()
                self.close_options_window()
            if single_export:
                # export directly to file_path
                if self.avatars:
                    utils.log_info(f"Exporting Avatar: {self.avatars[0].GetName()}")
                    self.set_avatar(self.avatars[0])
                    self.set_paths(file_path, self.option_animation_only)
                    self.export_fbx()
                elif self.props:
                    utils.log_info(f"Exporting Prop: {self.props[0].GetName()}")
                    self.set_prop(self.props[0])
                    self.set_paths(file_path, self.option_animation_only)
                    self.export_fbx()
            elif multi_export:
                # set the base path and create a folder
                self.set_base_path(file_path, create=True, show=True)
                for avatar in self.avatars:
                    self.set_avatar(avatar)
                    self.set_multi_paths(avatar, self.option_animation_only)
                    self.export_fbx()
                for prop in self.props:
                    self.set_prop(prop)
                    self.set_multi_paths(prop, self.option_animation_only)
                    self.export_fbx()
            utils.log("Done!")
            self.clean_up_globals()

        else:
            utils.log("Export Cancelled.")

        self.close_progress_window()

    def export_fbx(self):
        obj = None
        if self.avatar:
            if self.option_animation_only:
                self.export_motion_fbx()
                return
            export_obj = self.avatar
            is_avatar = True
            is_prop = False
            obj = self.avatar
        elif self.prop:
            if self.option_animation_only:
                self.export_motion_fbx()
                return
            export_obj = self.prop
            is_avatar = False
            is_prop = True
            obj = self.prop
        else:
            utils.log_error("No avatar or prop to export!")
            return

        file_path = self.fbx_path
        if is_avatar:
            self.update_progress(0, f"Exporting Avatar: {obj.GetName()} ...", True)
        else:
            self.update_progress(0, f"Exporting Prop: {obj.GetName()} ...", True)

        utils.log(f"Exporting {('Avatar' if is_avatar else 'Prop')} - {obj.GetName()} - FBX: {file_path}")

        options1 = EExportFbxOptions__None
        options1 = options1 | EExportFbxOptions_AutoSkinRigidMesh
        options1 = options1 | EExportFbxOptions_RemoveAllUnused
        options1 = options1 | EExportFbxOptions_ExportPbrTextureAsImageInFormatDirectory
        options1 = options1 | EExportFbxOptions_ExportRootMotion
        if is_avatar:
            if self.option_remove_hidden:
                options1 = options1 | EExportFbxOptions_RemoveHiddenMesh
            else:
                options1 = options1 | EExportFbxOptions_FbxKey

        options2 = EExportFbxOptions2__None
        options2 = options2 | EExportFbxOptions2_ResetBoneScale
        options2 = options2 | EExportFbxOptions2_ResetSelfillumination

        options3 = EExportFbxOptions3__None
        options3 = options3 | EExportFbxOptions3_ExportJson
        options3 = options3 | EExportFbxOptions3_ExportVertexColor

        export_fbx_setting = RExportFbxSetting()

        export_fbx_setting.SetOption(options1)
        export_fbx_setting.SetOption2(options2)
        export_fbx_setting.SetOption3(options3)

        if is_avatar:
            export_fbx_setting.EnableBakeDiffuseSpecularFromShader(self.option_bakehair)
            export_fbx_setting.EnableBakeDiffuseFromSkinColor(self.option_bakeskin)
            export_fbx_setting.EnableBasicBindPose(not self.option_t_pose)

        export_fbx_setting.SetTextureFormat(EExportTextureFormat_Default)
        export_fbx_setting.SetTextureSize(EExportTextureSize_Original)

        # determine if any frames to export
        fps = RGlobal.GetFps()
        start_frame = fps.GetFrameIndex(RGlobal.GetStartTime())
        end_frame = fps.GetFrameIndex(RGlobal.GetEndTime())
        num_frames = end_frame - start_frame

        if self.option_current_animation and num_frames > 0:
            export_fbx_setting.EnableExportMotion(True)
            export_fbx_setting.SetExportMotionFps(RFps.Fps60)
            export_fbx_setting.SetExportMotionRange(RRangePair(start_frame, end_frame))
            utils.log_info(f"Exporting with current animation: {num_frames}")
        elif self.option_current_pose and num_frames > 0:
            export_fbx_setting.EnableExportMotion(True)
            frame = fps.GetFrameIndex(RGlobal.GetTime())
            export_fbx_setting.SetExportMotionRange(RRangePair(frame, frame))
            utils.log_info(f"Exporting with current frame pose: {frame}")
        else:
            export_fbx_setting.EnableExportMotion(False)
            utils.log_info(f"Exporting without motion")

        result = RFileIO.ExportFbxFile(export_obj, file_path, export_fbx_setting)

        if is_avatar:
            self.update_progress(3, f"Exported Avatar Fbx - {obj.GetName()}", True)
        else:
            self.update_progress(3, f"Exported Prop Fbx - {obj.GetName()}", True)

        self.export_extra_data()

    def export_motion_fbx(self):

        file_path = self.fbx_path

        if self.avatar:
            obj = self.avatar
            is_avatar = True
        elif self.prop:
            obj = self.prop
            is_avatar = False

        self.update_progress(0, f"Exporting Motion - {obj.GetName()}", True)
        utils.log(f"Exporting Motion FBX: {file_path}")

        options1 = EExportFbxOptions__None

        options1 = options1 | EExportFbxOptions_AutoSkinRigidMesh
        options1 = options1 | EExportFbxOptions_RemoveAllUnused
        if is_avatar:
            options1 = options1 | EExportFbxOptions_RemoveAllMeshKeepMorph
        options1 = options1 | EExportFbxOptions_ExportRootMotion

        options2 = EExportFbxOptions2__None
        options2 = options2 | EExportFbxOptions2_ResetBoneScale
        options2 = options2 | EExportFbxOptions2_ResetSelfillumination

        options3 = EExportFbxOptions3__None

        export_fbx_setting = RExportFbxSetting()

        export_fbx_setting.SetOption(options1)
        export_fbx_setting.SetOption2(options2)
        export_fbx_setting.SetOption3(options3)

        export_fbx_setting.SetTextureFormat(EExportTextureFormat_Default)
        export_fbx_setting.SetTextureSize(EExportTextureSize_Original)
        if is_avatar:
            export_fbx_setting.EnableBasicBindPose(not self.option_t_pose)
        else:
            export_fbx_setting.EnableBasicBindPose(True)

        fps = RGlobal.GetFps()
        start_frame = fps.GetFrameIndex(RGlobal.GetStartTime())
        end_frame = fps.GetFrameIndex(RGlobal.GetEndTime())
        export_fbx_setting.EnableExportMotion(True)
        export_fbx_setting.SetExportMotionFps(RFps.Fps60)
        export_fbx_setting.SetExportMotionRange(RRangePair(start_frame, end_frame))

        result = RFileIO.ExportFbxFile(obj, file_path, export_fbx_setting)

        self.update_progress(1, f"Exported Motion - {obj.GetName()}", True)

    def export_extra_data(self):
        """TODO write sub-object link_id's"""

        utils.log_info(self.json_path)
        utils.log_info(self.fbx_path)
        json_data = cc.CCJsonData(self.json_path, self.fbx_path, self.character_id)
        root_json = json_data.get_root_json()
        if json_data is None:
            utils.log_error("No valid json data could be found for the export ...")
            return

        obj = self.avatar if self.avatar else self.prop
        if not obj: return

        if self.avatar:

            mesh_materials = cc.get_avatar_mesh_materials(self.avatar, json_data=json_data)

            avatar_type_string = cc.get_avatar_type_name(self.avatar)
            root_json["Avatar_Type"] = avatar_type_string
            root_json["Link_ID"] = cc.get_link_id(self.avatar)

            utils.log(f"Avatar Type: {avatar_type_string}")

            # correct the generation
            generation_type = self.avatar.GetGeneration()
            generation = json_data.set_character_generation(generation_type)
            utils.log(f"Avatar Generation: {generation}")

            if self.option_hik_data:

                self.update_progress(0, "Exporting HIK Profile ...", True)

                # Non-standard HIK profile
                #if self.avatar_type == EAvatarType_NonStandard:
                utils.log(f"Exporting HIK profile: {self.hik_path}")

                self.avatar.SaveHikProfile(self.hik_path)
                root_json["HIK"] = {}
                root_json["HIK"]["Profile_Path"] = os.path.relpath(self.hik_path, self.folder)

                self.update_progress(1, "Exported HIK Profile.", True)

            if self.option_profile_data:

                avatar_type = self.avatar.GetAvatarType()

                # Standard and Non-standard facial profiles
                if (avatar_type == EAvatarType_NonStandard or
                    avatar_type == EAvatarType_Standard or
                    avatar_type == EAvatarType_StandardSeries):

                    self.update_progress(0, "Exporting Facial Profile ...", True)

                    profile_type_string = cc.get_avatar_profile_name(self.avatar)

                    utils.log(f"Exporting Facial Expression profile ({profile_type_string}): {self.profile_path}")

                    facial_profile = self.avatar.GetFacialProfileComponent()
                    if facial_profile:
                        facial_profile.SaveProfile(self.profile_path)
                        root_json["Facial_Profile"] = {}
                        root_json["Facial_Profile"]["Profile_Path"] = os.path.relpath(self.profile_path, self.folder)
                        root_json["Facial_Profile"]["Type"] = profile_type_string
                        categories = facial_profile.GetExpressionCategoryNames()
                        root_json["Facial_Profile"]["Categories"] = {}
                        for category in categories:
                            slider_names = facial_profile.GetExpressionSliderNames(category)
                            root_json["Facial_Profile"]["Categories"][category] = slider_names

                        self.update_progress(2, "Exported Facial Profile.", True)
                    else:
                        self.update_progress(2, "No Facial Profile!", True)

            self.update_progress(0, "Exporting Additional Physics ...", True)

            self.export_physics(mesh_materials)

            self.update_progress(1, "Exported Additional Physics.", True)

        elif self.prop:

            root_json["Avatar_Type"] = "Prop"
            root_json["Link_ID"] = cc.get_link_id(self.prop)

        # Add sub object id's and root bones
        info_json = []
        child_objects: list = RScene.FindChildObjects(obj, EObjectType_Prop | EObjectType_Accessory)
        objects = [obj]
        objects.extend(child_objects)
        root_def = cc.get_extended_skin_bones_tree(obj)
        root_json["Root Bones"] = cc.extract_root_bones_from_tree(root_def)
        for obj in objects:
            obj_name = obj.GetName()
            SC: RISkeletonComponent = obj.GetSkeletonComponent()
            root_bone = SC.GetRootBone()
            root_name = root_bone.GetName() if root_bone else ""
            skin_bones = SC.GetSkinBones()
            skin_bone_names = [ b.GetName() for b in skin_bones if b.GetName() ] if skin_bones else []
            obj_type = cc.get_object_type(obj)
            if obj_type != "NONE" and skin_bone_names:
                id = cc.get_link_id(obj, add_if_missing=True)
                info_obj_json = {
                    "Link_ID": id,
                    "Name": obj_name,
                    "Type": obj_type,
                    "Root": root_name,
                    "Bones": skin_bone_names,
                }
                info_json.append(info_obj_json)


        root_json["Object_Info"] = info_json

        # Update JSON data
        utils.log(f"Re-writing JSON data: {self.json_path}")

        json_data.write()

    def export_physics(self, mesh_materials):
        utils.log(f"Exporting Extra Physics Data")
        M: cc.CCMeshMaterial
        for M in mesh_materials:
            if M.has_physics_json():
                phys_json = M.physx_mat_json.json()
                if "Weight Map Path" in phys_json.keys():
                    weight_map_path = phys_json["Weight Map Path"]
                    if not weight_map_path:
                        utils.log(f"No weightmap texture path in physics component: {M.mesh_name} / {M.mat_name}")
                        weight_map_path = os.path.join(self.folder, "textures", self.character_id, M.json_mesh_name,
                                                        M.json_mesh_name, M.json_mat_name,
                                                        f"{M.json_mat_name}_WeightMap.png")
                        if not os.path.exists(weight_map_path):
                            utils.log(f"Weightmap missing, attempting to save: {weight_map_path}")
                            M.physics_component().SavePhysicsSoftColthWeightMap(M.mesh_name, M.mat_name, weight_map_path)
                        if os.path.exists(weight_map_path):
                            phys_json["Weight Map Path"] = os.path.relpath(weight_map_path, self.folder)
                            utils.log(f"Adding weightmap path: {phys_json['Weight Map Path']}")
                        else:
                            utils.log(f"Unable to save missing weightmap: {weight_map_path}")

