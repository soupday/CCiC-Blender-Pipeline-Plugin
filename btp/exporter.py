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
    fbx_path = "C:/folder/dummy.fbx"
    folder = "C:/folder"
    fbx_file = "dummy.fbx"
    key_file = "C:/folder/dummy.fbxkey"
    character_id = "dummy"
    json_path = "C:/folder/dummy.json"
    hik_path = "C:/folder/dummy.3dxProfile"
    profile_path = "C:/folder/dummy.ccFacialProfile"
    json_data = None
    avatar: RIAvatar = None
    prop: RIProp = None
    avatar_type = None
    avatar_type_string = "None"
    profile_type = None
    profile_type_string = "None"
    window_options = None
    window_progress = None
    progress_count = 0
    progress_bar = None
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
    option_animation_only = False
    preset_button_1 = None
    preset_button_2 = None
    preset_button_3 = None
    label_desc = None


    def __init__(self, object, no_window=False):

        if type(object) is RIAvatar:
            self.avatar = object
        elif type(object) is RIProp:
            self.prop = object

        if self.avatar:

            utils.log("======================")
            utils.log("New Avatar Export, Fbx")

            self.avatar_type = self.avatar.GetAvatarType()
            self.avatar_type_string = "None"
            if self.avatar_type in vars.AVATAR_TYPES.keys():
                self.avatar_type_string = vars.AVATAR_TYPES[self.avatar_type]

            self.profile_type = EFacialProfile__None
            self.profile_type_string = "None"
            if (self.avatar_type == EAvatarType_NonStandard or
                self.avatar_type == EAvatarType_Standard or
                self.avatar_type == EAvatarType_StandardSeries):
                facial_profile = self.avatar.GetFacialProfileComponent()
                self.profile_type = facial_profile.GetProfileType()
                if self.profile_type in vars.FACIAL_PROFILES.keys():
                    self.profile_type_string = vars.FACIAL_PROFILES[self.profile_type]

            if not no_window:
                self.create_options_window()

        if self.prop:

            utils.log("====================")
            utils.log("New Prop Export, Fbx")

            if not no_window:
                self.create_options_window()

    def clean_up_globals(self):
        global FBX_EXPORTER
        FBX_EXPORTER = None

    def set_paths(self, file_path):
        file_path = os.path.normpath(file_path)
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
        self.preset_button_2 = qt.button(row, "Pose/Animation", self.preset_current_pose, height=24, toggle=True, value=False)
        self.preset_button_3 = qt.button(row, "Blender > Unity", self.preset_unity, height=24, toggle=True, value=False)
        self.label_desc = qt.label(layout, "", "color: #d2ff7b; font: italic 13px", wrap=True)

        qt.spacing(layout, 10)

        qt.label(layout, f"Avatar: {self.avatar_type_string}  -  Profile: {self.profile_type_string}", "color: white; font: bold")

        qt.spacing(layout, 10)

        self.check_hik_data = None
        if self.avatar_type == EAvatarType_NonStandard:
            self.check_hik_data = qt.checkbox(layout, "Export HIK Profile", False)

        self.check_profile_data = None
        if (self.avatar_type == EAvatarType_NonStandard or
            self.avatar_type == EAvatarType_Standard or
            self.avatar_type == EAvatarType_StandardSeries):
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

    def create_progress_window(self):
        title = "Blender Character Export - Progress"
        self.window_progress, layout = qt.window(title, 500)
        qt.label(layout, f"Export Progress: {self.avatar.GetName()}" )
        self.progress_bar = qt.progress(layout, 0, 0, 0, "Intializing...")
        self.progress_count = 0
        steps = 3
        if self.avatar:
            steps += 1 # physics
            if self.option_hik_data:
                steps += 1
            if self.option_profile_data:
                steps += 2
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
        self.preset_button_1.setStyleSheet(qt.STYLE_RL_TAB_SELECTED)
        self.preset_button_2.setStyleSheet(qt.STYLE_RL_TAB)
        self.preset_button_3.setStyleSheet(qt.STYLE_RL_TAB)
        self.label_desc.setText("Round Trip Editing:\n\n" +
                                "Export the character as mesh only in the bind pose without animation, " +
                                "with full facial expression data and human IK profile (non-standard), " +
                                "for complete round trip character editing.")
        self.option_bakehair = False
        self.option_bakeskin = False
        self.option_t_pose = False
        self.option_current_pose = False
        self.option_current_animation = False
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
        self.preset_button_1.setChecked(False)
        self.preset_button_2.setChecked(True)
        self.preset_button_3.setChecked(False)
        self.preset_button_1.setStyleSheet(qt.STYLE_RL_TAB)
        self.preset_button_2.setStyleSheet(qt.STYLE_RL_TAB_SELECTED)
        self.preset_button_3.setStyleSheet(qt.STYLE_RL_TAB)
        self.label_desc.setText("Accessory Creation / Replace Mesh:\n\n" +
                                "Export the full character in the current pose, " +
                                "for accessory creation or replacement mesh editing.\n")
        self.option_t_pose = False
        self.option_current_pose = prefs.CC_EXPORT_MODE != "Animation"
        self.option_current_animation = prefs.CC_EXPORT_MODE == "Animation"
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
        self.preset_button_1.setChecked(False)
        self.preset_button_2.setChecked(False)
        self.preset_button_3.setChecked(True)
        self.preset_button_1.setStyleSheet(qt.STYLE_RL_TAB)
        self.preset_button_2.setStyleSheet(qt.STYLE_RL_TAB)
        self.preset_button_3.setStyleSheet(qt.STYLE_RL_TAB_SELECTED)
        self.label_desc.setText("Blender to Unity Pipeline:\n\n" +
                                "Export the character with hidden faces removed, skin & hair textures baked and " +
                                "with T-pose bind pose, for editing in Blender before exporting from Blender to Unity.")
        self.option_hik_data = False
        self.option_profile_data = False
        self.option_t_pose = True
        self.option_current_pose = False
        self.option_current_animation = False
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
        if (type(self.avatar) is RIAvatar and
                (self.avatar.GetGeneration() == EAvatarGeneration_ActorBuild or
                self.avatar.GetGeneration() == EAvatarGeneration_ActorScan or
                self.avatar.GetAvatarType() == EAvatarType_NonStandard)):
            self.option_hik_data = True
            self.option_profile_data = True

    def set_datalink_export(self, file_path):
        self.option_t_pose = False
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
            if prefs.CC_EXPORT_MODE == "Current Pose":
                self.option_current_animation = False
                self.option_current_pose = True
            elif prefs.CC_EXPORT_MODE == "Animation":
                self.option_current_animation = True
                self.option_current_pose = False
            else:
                self.option_current_animation = False
                self.option_current_pose = False
            self.option_hik_data = prefs.IC_USE_HIK_PROFILE
            self.option_profile_data = prefs.IC_USE_FACIAL_PROFILE
        self.set_paths(file_path)

    def set_datalink_motion_export(self, file_path):
        self.option_t_pose = False
        self.option_bakehair = False
        self.option_bakeskin = False
        self.option_remove_hidden = False
        self.option_current_animation = True
        self.option_current_pose = False
        self.option_hik_data = False
        self.option_profile_data = False
        self.option_animation_only = True
        self.set_paths(file_path)

    def do_export(self):
        file_path = RUi.SaveFileDialog("Fbx Files(*.fbx)")
        if file_path and file_path != "":
            self.set_paths(file_path)
            self.fetch_options()
            self.close_options_window()
            self.export_fbx()
            utils.log("Done!")
            self.clean_up_globals()
        else:
            utils.log("Export Cancelled.")

    def export_fbx(self):

        if self.avatar:
            obj = self.avatar
            is_avatar = True
        elif self.prop:
            obj = self.prop
            is_avatar = False
        else:
            utils.log_error("No avatar or prop to export!")
            return

        if is_avatar:
            self.create_progress_window()
            self.update_progress(0, "Exporting character Fbx...", True)

        file_path = self.fbx_path

        utils.log(f"Exporting {('Avatar' if is_avatar else 'Prop')} FBX: {file_path}")

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

        if self.option_current_animation:
            fps = RGlobal.GetFps()
            start_frame = fps.GetFrameIndex(RGlobal.GetStartTime())
            end_frame = fps.GetFrameIndex(RGlobal.GetEndTime())
            export_fbx_setting.EnableExportMotion(True)
            export_fbx_setting.SetExportMotionFps(RFps.Fps60)
            export_fbx_setting.SetExportMotionRange(RRangePair(start_frame, end_frame))
            utils.log_info(f"Exporting with current animation: {start_frame} - {end_frame}")
        elif self.option_current_pose:
            fps = RGlobal.GetFps()
            export_fbx_setting.EnableExportMotion(True)
            frame = fps.GetFrameIndex(RGlobal.GetTime())
            export_fbx_setting.SetExportMotionRange(RRangePair(frame, frame))
            utils.log_info(f"Exporting with current frame pose: {frame}")
        else:
            export_fbx_setting.EnableExportMotion(False)
            utils.log_info(f"Exporting without motion")

        result = RFileIO.ExportFbxFile(obj, file_path, export_fbx_setting)

        if is_avatar:
            self.update_progress(3, "Exported character Fbx.", True)

        self.export_extra_data()

        if is_avatar:
            self.close_progress_window()

    def export_motion_fbx(self):

        file_path = self.fbx_path

        if self.avatar:
            obj = self.avatar
            is_avatar = True
        elif self.prop:
            obj = self.prop
            is_avatar = False

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

    def export_extra_data(self):
        """TODO write sub-object link_id's"""

        utils.log_info(self.json_path)
        utils.log_info(self.fbx_path)
        json_data = cc.CCJsonData(self.json_path, self.fbx_path, self.character_id)
        root_json = json_data.get_root_json()

        obj = self.avatar if self.avatar else self.prop
        if not obj: return

        if self.avatar:

            mesh_materials = cc.get_avatar_mesh_materials(self.avatar, json_data=json_data)

            root_json["Avatar_Type"] = self.avatar_type_string
            root_json["Link_ID"] = cc.get_link_id(self.avatar)

            utils.log(f"Avatar Type: {self.avatar_type_string}")

            # correct the generation
            generation_type = self.avatar.GetGeneration()
            generation = json_data.set_character_generation(generation_type)
            utils.log(f"Avatar Generation: {generation}")

            if self.option_hik_data:

                self.update_progress(0, "Exporting HIK Profile...", True)

                # Non-standard HIK profile
                #if self.avatar_type == EAvatarType_NonStandard:
                utils.log(f"Exporting HIK profile: {self.hik_path}")

                self.avatar.SaveHikProfile(self.hik_path)
                root_json["HIK"] = {}
                root_json["HIK"]["Profile_Path"] = os.path.relpath(self.hik_path, self.folder)

                self.update_progress(1, "Exported HIK Profile.", True)

            if self.option_profile_data:

                # Standard and Non-standard facial profiles
                if (self.avatar_type == EAvatarType_NonStandard or
                    self.avatar_type == EAvatarType_Standard or
                    self.avatar_type == EAvatarType_StandardSeries):

                    self.update_progress(0, "Exporting Facial Profile...", True)

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

                    self.update_progress(2, "Exported Facial Profile.", True)

            self.update_progress(0, "Exporting Additional Physics...", True)

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

