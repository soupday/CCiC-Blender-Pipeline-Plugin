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
import PySide2
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
import os
import blender, cc, qt, utils, vars


FBX_EXPORTER = None


AVATAR_TYPES = {
    RLPy.EAvatarType__None: "None",
    RLPy.EAvatarType_Standard: "Standard",
    RLPy.EAvatarType_NonHuman: "NonHuman",
    RLPy.EAvatarType_NonStandard: "NonStandard",
    RLPy.EAvatarType_StandardSeries: "StandardSeries",
    RLPy.EAvatarType_All: "All",
}

FACIAL_PROFILES = {
    RLPy.EFacialProfile__None: "None",
    RLPy.EFacialProfile_CC4Extended: "CC4Extended",
    RLPy.EFacialProfile_CC4Standard: "CC4Standard",
    RLPy.EFacialProfile_Traditional: "Traditional",
}


class Exporter:
    fbx_path = "C:/folder/dummy.fbx"
    folder = "C:/folder"
    fbx_file = "dummy.fbx"
    key_file = "C:/folder/dummy.fbxkey"
    character_id = "dummy"
    json_path = "C:/folder/dummy.json"
    hik_path = "C:/folder/dummy.3dxProfile"
    profile_path = "C:/folder/dummy.ccFacialProfile"
    json_data = None
    avatar = None
    avatar_type = None
    avatar_type_string = "None"
    profile_type = None
    profile_type_string = "None"
    window_options = None
    check_bakehair = None
    check_bakeskin = None
    check_t_pose = None
    check_current_pose = None
    check_current_animation = None
    check_hik_data = None
    check_profile_data = None
    check_remove_hidden = None
    option_bakehair = False
    option_bakeskin = False
    option_t_pose = False
    option_current_pose = False
    option_current_animation = False
    option_hik_data = False
    option_profile_data = False
    option_remove_hidden = False
    preset_button_1 = None
    preset_button_2 = None
    preset_button_3 = None
    label_desc = None


    def __init__(self):
        utils.log("================================================================")
        utils.log("New character export, Fbx")

        avatar_list = RLPy.RScene.GetAvatars()

        if len(avatar_list) > 0:

            self.avatar = avatar_list[0]

            if self.avatar:

                self.avatar_type = self.avatar.GetAvatarType()
                self.avatar_type_string = "None"
                if self.avatar_type in AVATAR_TYPES.keys():
                    self.avatar_type_string = AVATAR_TYPES[self.avatar_type]

                self.profile_type = RLPy.EFacialProfile__None
                self.profile_type_string = "None"
                if (self.avatar_type == RLPy.EAvatarType_NonStandard or
                    self.avatar_type == RLPy.EAvatarType_Standard or
                    self.avatar_type == RLPy.EAvatarType_StandardSeries):
                    facial_profile = self.avatar.GetFacialProfileComponent()
                    self.profile_type = facial_profile.GetProfileType()
                    if self.profile_type in FACIAL_PROFILES.keys():
                        self.profile_type_string = FACIAL_PROFILES[self.profile_type]

                self.create_options_window()


    def clean_up_globals(self):
        global FBX_EXPORTER
        FBX_EXPORTER = None


    def set_paths(self, file_path):
        self.fbx_path = file_path
        self.fbx_file = os.path.basename(self.fbx_path)
        self.folder = os.path.dirname(self.fbx_path)
        self.character_id = os.path.splitext(self.fbx_file)[0]
        self.key_file = os.path.join(self.folder, self.character_id + ".fbxkey")
        self.json_path = os.path.join(self.folder, self.character_id + ".json")
        self.hik_path = os.path.join(self.folder, self.character_id + ".3dxProfile")
        self.profile_path = os.path.join(self.folder, self.character_id + ".ccFacialProfile")


    def create_options_window(self):
        title = f"Blender Auto-setup Character Export ({vars.VERSION}) - Options"
        self.window_options, layout = qt.window(title, 500)

        row = qt.row(layout)
        self.preset_button_1 = qt.button(row, "Mesh Only", self.preset_mesh_only, height=24, toggle=True, value=True)
        self.preset_button_2 = qt.button(row, "Current Pose", self.preset_current_pose, height=24, toggle=True, value=False)
        self.preset_button_3 = qt.button(row, "Blender > Unity", self.preset_unity, height=24, toggle=True, value=False)
        self.label_desc = qt.label(layout, "", "color: #d2ff7b; font: italic 13px", wrap=True)

        qt.spacing(layout, 10)

        qt.label(layout, f"Avatar: {self.avatar_type_string}  -  Profile: {self.profile_type_string}", "color: white; font: bold")

        qt.spacing(layout, 10)

        self.check_hik_data = None
        if self.avatar_type == RLPy.EAvatarType_NonStandard:
            self.check_hik_data = qt.checkbox(layout, "Export HIK Profile", False)

        self.check_profile_data = None
        if (self.avatar_type == RLPy.EAvatarType_NonStandard or
            self.avatar_type == RLPy.EAvatarType_Standard or
            self.avatar_type == RLPy.EAvatarType_StandardSeries):
            self.check_profile_data = qt.checkbox(layout, "Export Facial Expression Profile", False)

        qt.spacing(layout, 10)

        self.check_bakehair = qt.checkbox(layout, "Bake Hair Diffuse and Specular", False)
        self.check_bakeskin = qt.checkbox(layout, "Bake Skin Diffuse", False)
        self.check_t_pose = qt.checkbox(layout, "Bindpose as T-Pose", False)
        self.check_current_pose = qt.checkbox(layout, "Current Pose", False)
        self.check_current_animation = qt.checkbox(layout, "Current Animation", False)
        self.check_remove_hidden = qt.checkbox(layout, "Delete Hidden Faces", False)

        qt.spacing(layout, 10)

        qt.button(layout, "Export Character", self.do_export, height=32)

        self.preset_mesh_only()
        self.window_options.Show()


    def update_options(self):
        if self.check_hik_data: self.check_hik_data.setChecked(self.option_hik_data)
        if self.check_profile_data: self.check_profile_data.setChecked(self.option_profile_data)
        if self.check_bakehair: self.check_bakehair.setChecked(self.option_bakehair)
        if self.check_bakeskin: self.check_bakeskin.setChecked(self.option_bakeskin)
        if self.check_t_pose: self.check_t_pose.setChecked(self.option_t_pose)
        if self.check_current_pose: self.check_current_pose.setChecked(self.option_current_pose)
        if self.check_current_animation: self.check_current_animation.setChecked(self.option_current_animation)
        if self.check_remove_hidden: self.check_remove_hidden.setChecked(self.option_remove_hidden)


    def fetch_options(self):
        if self.check_bakehair: self.option_bakehair = self.check_bakehair.isChecked()
        if self.check_bakeskin: self.option_bakeskin = self.check_bakeskin.isChecked()
        if self.check_current_pose: self.option_current_pose = self.check_current_pose.isChecked()
        if self.check_current_animation: self.option_current_animation = self.check_current_animation.isChecked()
        if self.check_hik_data: self.option_hik_data = self.check_hik_data.isChecked()
        if self.check_profile_data: self.option_profile_data = self.check_profile_data.isChecked()
        if self.check_t_pose: self.option_t_pose = self.check_t_pose.isChecked()
        if self.check_remove_hidden: self.option_remove_hidden = self.check_remove_hidden.isChecked()


    def preset_mesh_only(self):
        self.preset_button_1.setChecked(True)
        self.preset_button_2.setChecked(False)
        self.preset_button_3.setChecked(False)
        self.preset_button_1.setStyleSheet("background-color: #82be0f; color: black; font: bold")
        self.preset_button_2.setStyleSheet("background-color: none; color: white; font: bold")
        self.preset_button_3.setStyleSheet("background-color: none; color: white; font: bold")
        self.label_desc.setText("Round Trip Editing:\n\n" +
                                "Export the character as mesh only in the bind pose without animation, " +
                                "with full facial expression data and human IK profile (non-standard), " +
                                "for complete round trip character editing.")
        self.option_bakehair = False
        self.option_bakeskin = False
        self.option_hik_data = True
        self.option_profile_data = False
        self.option_t_pose = False
        self.option_current_pose = False
        self.option_current_animation = False
        self.option_remove_hidden = False
        self.update_options()


    def preset_current_pose(self):
        self.preset_button_1.setChecked(False)
        self.preset_button_2.setChecked(True)
        self.preset_button_3.setChecked(False)
        self.preset_button_1.setStyleSheet("background-color: none; color: white; font: bold")
        self.preset_button_2.setStyleSheet("background-color: #82be0f; color: black; font: bold")
        self.preset_button_3.setStyleSheet("background-color: none; color: white; font: bold")
        self.label_desc.setText("Accessory Creation / Replace Mesh:\n\n" +
                                "Export the full character in the current pose, " +
                                "for accessory creation or replacement mesh editing.\n")
        self.option_bakehair = True
        self.option_bakeskin = True
        self.option_hik_data = True
        self.option_profile_data = False
        self.option_t_pose = False
        self.option_current_pose = True
        self.option_current_animation = False
        self.option_remove_hidden = False
        self.update_options()


    def preset_unity(self):
        self.preset_button_1.setChecked(False)
        self.preset_button_2.setChecked(False)
        self.preset_button_3.setChecked(True)
        self.preset_button_1.setStyleSheet("background-color: none; color: white; font: bold")
        self.preset_button_2.setStyleSheet("background-color: none; color: white; font: bold")
        self.preset_button_3.setStyleSheet("background-color: #82be0f; color: black; font: bold")
        self.label_desc.setText("Blender to Unity Pipeline:\n\n" +
                                "Export the character with hidden faces removed, skin & hair textures baked and " +
                                "with T-pose bind pose, for editing in Blender before exporting from Blender to Unity.")
        self.option_bakehair = True
        self.option_bakeskin = True
        self.option_hik_data = False
        self.option_profile_data = False
        self.option_t_pose = True
        self.option_current_pose = False
        self.option_current_animation = False
        self.option_remove_hidden = True
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


    def do_export(self):
        file_path = RLPy.RUi.SaveFileDialog("Fbx Files(*.fbx)")
        if file_path and file_path != "":
            self.set_paths(file_path)
            self.fetch_options()
            self.close_options_window()
            self.export_fbx()
            self.export_extra_data()
            utils.log("Done!")
            self.clean_up_globals()
        else:
            utils.log("Export Cancelled.")


    def export_fbx(self):
        avatar = self.avatar
        file_path = self.fbx_path

        utils.log(f"Exporting FBX: {file_path}")

        options1 = RLPy.EExportFbxOptions__None
        options1 = options1 | RLPy.EExportFbxOptions_FbxKey
        options1 = options1 | RLPy.EExportFbxOptions_AutoSkinRigidMesh
        options1 = options1 | RLPy.EExportFbxOptions_RemoveAllUnused
        options1 = options1 | RLPy.EExportFbxOptions_ExportPbrTextureAsImageInFormatDirectory
        if self.option_remove_hidden:
            options1 = options1 | RLPy.EExportFbxOptions_RemoveHiddenMesh

        options2 = RLPy.EExportFbxOptions2__None
        options2 = options2 | RLPy.EExportFbxOptions2_ResetBoneScale
        options2 = options2 | RLPy.EExportFbxOptions2_ResetSelfillumination

        options3 = RLPy.EExportFbxOptions3__None
        options3 = options3 | RLPy.EExportFbxOptions3_ExportJson
        options3 = options3 | RLPy.EExportFbxOptions3_ExportVertexColor

        export_fbx_setting = RLPy.RExportFbxSetting()

        export_fbx_setting.SetOption(options1)
        export_fbx_setting.SetOption2(options2)
        export_fbx_setting.SetOption3(options3)

        export_fbx_setting.EnableBakeDiffuseSpecularFromShader(self.option_bakehair)
        export_fbx_setting.EnableBakeDiffuseFromSkinColor(self.option_bakeskin)
        export_fbx_setting.EnableBasicBindPose(not self.option_t_pose)

        export_fbx_setting.SetTextureFormat(RLPy.EExportTextureFormat_Default)
        export_fbx_setting.SetTextureSize(RLPy.EExportTextureSize_Original)

        if self.option_current_pose:
            export_fbx_setting.EnableExportMotion(True)
            export_fbx_setting.SetExportMotionRange(RLPy.RRangePair(0, 1))
            export_fbx_setting.SetExportMotionFps(RLPy.RFps.Fps60)
        elif self.option_current_animation:
            fps = RLPy.RGlobal.GetFps()
            startFrame = fps.GetFrameIndex(RLPy.RGlobal.GetStartTime())
            endFrame = fps.GetFrameIndex(RLPy.RGlobal.GetEndTime())
            export_fbx_setting.EnableExportMotion(True)
            export_fbx_setting.SetExportMotionRange(RLPy.RRangePair(startFrame, endFrame))
            export_fbx_setting.SetExportMotionFps(RLPy.RFps.Fps60)
        else:
            export_fbx_setting.EnableExportMotion(False)

        result = RLPy.RFileIO.ExportFbxFile(avatar, file_path, export_fbx_setting)


    def export_extra_data(self):

        json_data = cc.CCJsonData(self.json_path, self.fbx_path, self.character_id)
        root_json = json_data.get_root_json()

        mesh_materials = cc.get_avatar_mesh_materials(self.avatar, json_data=json_data)

        root_json["Avatar_Type"] = self.avatar_type_string

        utils.log(f"Avatar Type: {self.avatar_type_string}")

        if self.option_hik_data:

            # Non-standard HIK profile
            if self.avatar_type == RLPy.EAvatarType_NonStandard:

                utils.log(f"Exporting HIK profile: {self.hik_path}")

                self.avatar.SaveHikProfile(self.hik_path)
                root_json["HIK"] = {}
                root_json["HIK"]["Profile_Path"] = os.path.relpath(self.hik_path, self.folder)

        if self.option_profile_data:

            # Standard and Non-standard facial profiles
            if (self.avatar_type == RLPy.EAvatarType_NonStandard or
                self.avatar_type == RLPy.EAvatarType_Standard or
                self.avatar_type == RLPy.EAvatarType_StandardSeries):

                utils.log(f"Exporting Facial Expression profile ({self.profile_type_string}): {self.profile_path}")

                facial_profile = self.avatar.GetFacialProfileComponent()
                facial_profile.SaveProfile(self.profile_path)
                root_json["Facial_Profile"] = {}
                root_json["Facial_Profile"]["Profile_Path"] = os.path.relpath(self.profile_path, self.folder)
                root_json["Facial_Profile"]["Type"] = self.profile_type_string
                categories = facial_profile.GetExpressionCategoryNames()
                root_json["Facial_Profile"]["Categories"] = {}
                for category in categories:
                    slider_names = facial_profile.GetExpressionSliderNames(category)
                    root_json["Facial_Profile"]["Categories"][category] = slider_names


        self.export_physics(mesh_materials)

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

