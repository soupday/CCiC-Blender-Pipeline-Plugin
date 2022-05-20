# Copyright (C) 2021 Victor Soupday
# This file is part of CC4-Blender-Tools-Plugin <https://github.com/soupday/CC4-Blender-Tools-Plugin>
#
# CC4-Blender-Tools-Plugin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# CC4-Blender-Tools-Plugin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with CC4-Blender-Tools-Plugin.  If not, see <https://www.gnu.org/licenses/>.

import RLPy
import json
import os
import time
import shutil
import random
import PySide2
from PySide2 import *
from shiboken2 import wrapInstance
from enum import IntEnum

VERSION = "1.0.7"

rl_plugin_info = {"ap": "CC4", "ap_version": "4.0"}

class TextureChannel(IntEnum):
    METALLIC      = 0
    DIFFUSE       = 1
    SPECULAR      = 2
    SHININESS     = 3
    GLOW          = 4
    DISPLACEMENT  = 5
    OPACITY       = 6
    DIFFUSE_BLEND = 7
    BUMP          = 8
    REFLECTION    = 9
    REFRACTION    = 10
    CUBE          = 11
    AMBIENT       = 12
    NORMAL        = 13
    VECTOR_DISPLACEMENT = 14


SHADER_MAPS = { # { "Json_shader_name" : "CC3_shader_name", }
    "Tra": "Traditional",
    "Pbr": "PBR",
    "RLEyeTearline": "Digital_Human Tear Line",
    "RLHair": "Digital_Human Hair",
    "RLTeethGum": "Digital_Human Teeth Gums",
    "RLEye": "Digital_Human Eye",
    "RLHead": "Digital_Human Head",
    "RLSkin": "Digital_Human Skin",
    "RLEyeOcclusion": "Digital_Human Eye Occlusion",
    "RLTongue": "Digital_Human Tongue",
    "RLSSS": "SSS",
}

TEXTURE_MAPS = { # { "json_channel_name": [RL_Texture_Channel, is_Substance_Painter_Channel?, substance_channel_postfix], }
    "Metallic": [RLPy.EMaterialTextureChannel_Metallic, True, "metallic"],
    "Base Color": [RLPy.EMaterialTextureChannel_Diffuse, True, "diffuse"],
    "Specular": [RLPy.EMaterialTextureChannel_Specular, True, "specular"],
    "Roughness": [RLPy.EMaterialTextureChannel_Shininess, True, "roughness"],
    "Glow": [RLPy.EMaterialTextureChannel_Glow, True, "glow"],
    "Displacement": [RLPy.EMaterialTextureChannel_Displacement, True, "displacement"],
    "Opacity": [RLPy.EMaterialTextureChannel_Opacity, True, "opacity"],
    "Blend": [RLPy.EMaterialTextureChannel_DiffuseBlend, False, ""],
    "Reflection": [RLPy.EMaterialTextureChannel_Reflection, False, ""],
    "Refraction": [RLPy.EMaterialTextureChannel_Refraction, False, ""],
    "Cube": [RLPy.EMaterialTextureChannel_Cube, False, ""],
    "AO": [RLPy.EMaterialTextureChannel_AmbientOcclusion, True, "ao"],
    "Bump": [RLPy.EMaterialTextureChannel_Bump, True, "bump"],
    "Normal": [RLPy.EMaterialTextureChannel_Normal, True, "normal"],
}

NUM_SUBSTANCE_MAPS = 10


plugin_menu = None
menu_import_action_1 = None
menu_import_action_2 = None
menu_import_action_3 = None
menu_import_action_4 = None
menu_import_action_5 = None


def initialize_plugin():
    global plugin_menu
    global menu_import_action_1
    global menu_import_action_2
    global menu_import_action_3
    global menu_import_action_4
    global menu_import_action_5

    # Add menu
    plugin_menu = wrapInstance(int(RLPy.RUi.AddMenu("Blender Pipeline", RLPy.EMenu_Plugins)), PySide2.QtWidgets.QMenu)

    menu_import_action_5 = plugin_menu.addAction("Export Character to Blender (Mesh Only)")
    menu_import_action_5.triggered.connect(menu_export_mesh_only)

    plugin_menu.addSeparator()

    menu_import_action_1 = plugin_menu.addAction("Import Character From Blender")
    menu_import_action_1.triggered.connect(menu_import_standard)


FBX_IMPORTER = None

def menu_import_standard():
    global FBX_IMPORTER

    FBX_IMPORTER = None

    file_path = RLPy.RUi.OpenFileDialog("Fbx Files(*.fbx)")
    if file_path and file_path != "":
        # keep hold of this instance, otherwise it is destroyed when this function ends...
        FBX_IMPORTER = Importer(file_path)


def menu_export_mesh_only():

    avatar_list = RLPy.RScene.GetAvatars()
    if len(avatar_list) == 0:
        return

    avatar = avatar_list[0]

    file_path = RLPy.RUi.SaveFileDialog("Fbx Files(*.fbx)")
    if file_path and file_path != "":

        options1 = RLPy.EExportFbxOptions__None
        options1 = options1 | RLPy.EExportFbxOptions_FbxKey
        options1 = options1 | RLPy.EExportFbxOptions_AutoSkinRigidMesh
        options1 = options1 | RLPy.EExportFbxOptions_RemoveAllUnused
        options1 = options1 | RLPy.EExportFbxOptions_ExportPbrTextureAsImageInFormatDirectory

        options2 = RLPy.EExportFbxOptions2__None
        options2 = options2 | RLPy.EExportFbxOptions2_ResetBoneScale
        options2 = options2 | RLPy.EExportFbxOptions2_ResetSelfillumination

        options3 = RLPy.EExportFbxOptions3__None
        options3 = options3 | RLPy.EExportFbxOptions3_ExportJson
        options3 = options3 | RLPy.EExportFbxOptions3_ExportVertexColor

        result = RLPy.RFileIO.ExportFbxFile(avatar, file_path, options1, options2, options3,
                                            RLPy.EExportTextureSize_Original,
                                            RLPy.EExportTextureFormat_Default)
    return


def clean_up_globals():
    global FBX_IMPORTER
    FBX_IMPORTER = None


#
# Class: Importer
#

class Importer:
    fbx_path = "C:/folder/dummy.fbx"
    fbx_folder = "C:/folder"
    fbx_file = "dummy.fbx"
    fbx_key = "C:/folder/dummy.fbxkey"
    fbx_name = "dummy"
    json_path = "C:/folder/dummy.json"
    json_data = None
    avatar = None
    window_options = None
    window_progress = None
    progress_1 = None
    progress_2 = None
    check_mesh = None
    check_textures = None
    check_parameters = None
    num_pbr = 0
    num_custom = 0
    count_pbr = 0
    count_custom = 0
    mat_duplicates = {}
    substance_import_success = False
    import_mesh = True
    import_textures = True
    import_parameters = True
    character_type = None
    generation = None


    def __init__(self, file_path):
        print("================================================================")
        print("New character import, Fbx: " + file_path)
        self.fbx_path = file_path
        self.fbx_file = os.path.basename(self.fbx_path)
        self.fbx_folder = os.path.dirname(self.fbx_path)
        self.fbx_name = os.path.splitext(self.fbx_file)[0]
        self.fbx_key = os.path.join(self.fbx_folder, self.fbx_name + ".fbxkey")
        self.json_path = os.path.join(self.fbx_folder, self.fbx_name + ".json")
        self.json_data = read_json(self.json_path)

        self.generation = get_character_generation_json(self.json_data, self.fbx_name, self.fbx_name)
        self.character_type = "STANDARD"
        if self.generation == "Humanoid" or self.generation == "" or self.generation == "Unknown":
            self.character_type = "HUMANOID"
        elif self.generation == "Creature":
            self.character_type = "CREATURE"
        elif self.generation == "Prop":
            self.character_type = "PROP"

        error = False
        if not self.json_data:
            message_box("There is no JSON data with this character!\n\nThe plugin will be unable to set-up any materials.\n\nPlease use the standard character importer instead (File Menu > Import).")
            error = True
        if self.character_type == "STANDARD":
            if not os.path.exists(self.fbx_key):
                message_box("There is no Fbx Key with this character!\n\nCC3/4 Standard characters cannot be imported back into Character Creator without a corresponding Fbx Key.\nThe Fbx Key will be generated when the character is exported as Mesh only, or in Calibration Pose, and with no hidden faces.")
                error = True

        if not error:
            self.create_options_window()


    def close_options_window(self):
        if self.check_mesh:
            self.import_mesh = self.check_mesh.isChecked()
        if self.check_textures:
            self.import_textures = self.check_textures.isChecked()
        if self.check_parameters:
            self.import_parameters = self.check_parameters.isChecked()
        if self.window_options:
            self.window_options.Close()
        self.window_options = None
        self.check_mesh = None
        self.check_textures = None
        self.check_parameters = None


    def close_progress_window(self):
        self.close_options_window()
        if self.window_progress:
            self.window_progress.Close()
        self.fbx_path = "C:/folder/dummy.fbx"
        self.fbx_folder = "C:/folder"
        self.fbx_file = "dummy.fbx"
        self.fbx_name = "dummy"
        self.json_path = "C:/folder/dummy.json"
        self.json_data = None
        self.avatar = None
        self.window_progress = None
        self.progress_1 = None
        self.progress_2 = None
        self.num_pbr = 0
        self.num_custom = 0
        self.count_pbr = 0
        self.count_custom = 0
        self.mat_duplicates = {}
        self.substance_import_success = False
        clean_up_globals()


    def create_options_window(self):
        window = RLPy.RUi.CreateRDockWidget()
        window.SetWindowTitle("Blender Auto-setup Character Import - Options")
        print(PySide2.QtWidgets.QDockWidget)
        dock = wrapInstance(int(window.GetWindow()), PySide2.QtWidgets.QDockWidget)
        dock.setFixedWidth(500)

        widget = PySide2.QtWidgets.QWidget()
        dock.setWidget(widget)

        layout = PySide2.QtWidgets.QVBoxLayout()
        widget.setLayout(layout)

        label_1 = PySide2.QtWidgets.QLabel()
        label_1.setText(f"Character Name: {self.fbx_name}")
        layout.addWidget(label_1)

        label_2 = PySide2.QtWidgets.QLabel()
        label_2.setText(f"Character Path: {self.fbx_path}")
        layout.addWidget(label_2)

        label_3 = PySide2.QtWidgets.QLabel()
        label_3.setText(f"Type: {self.character_type}")
        layout.addWidget(label_3)

        layout.addSpacing(10)

        check_mesh = PySide2.QtWidgets.QCheckBox()
        check_mesh.setText("Import Mesh")
        check_mesh.setChecked(self.import_mesh)
        layout.addWidget(check_mesh)

        check_textures = PySide2.QtWidgets.QCheckBox()
        check_textures.setText("Import Textures")
        check_textures.setChecked(self.import_textures)
        layout.addWidget(check_textures)

        check_parameters = PySide2.QtWidgets.QCheckBox()
        check_parameters.setText("Import Parameters")
        check_parameters.setChecked(self.import_parameters)
        layout.addWidget(check_parameters)

        layout.addSpacing(10)

        start_button = PySide2.QtWidgets.QPushButton("Import Character", minimumHeight=32)
        start_button.clicked.connect(self.import_fbx)
        layout.addWidget(start_button)

        cancel_button = PySide2.QtWidgets.QPushButton("Cancel", minimumHeight=32)
        cancel_button.clicked.connect(self.close_progress_window)
        layout.addWidget(cancel_button)

        #window.RegisterEventCallback(self.dialog_callback)

        window.Show()
        self.window_options = window
        self.check_mesh = check_mesh
        self.check_textures = check_textures
        self.check_parameters = check_parameters


    def create_progress_window(self):
        window = RLPy.RUi.CreateRDockWidget()
        window.SetWindowTitle("Blender Auto-setup Character Import - Progress")

        dock = wrapInstance(int(window.GetWindow()), PySide2.QtWidgets.QDockWidget)
        dock.setFixedWidth(500)

        widget = PySide2.QtWidgets.QWidget()
        dock.setWidget(widget)

        layout = PySide2.QtWidgets.QVBoxLayout()
        widget.setLayout(layout)

        label_1 = PySide2.QtWidgets.QLabel()
        label_1.setText(f"Character Name: {self.fbx_name}")
        layout.addWidget(label_1)

        label_2 = PySide2.QtWidgets.QLabel()
        label_2.setText(f"Character Path: {self.fbx_path}")
        layout.addWidget(label_2)

        layout.addSpacing(10)

        label_progress_1 = PySide2.QtWidgets.QLabel()
        label_progress_1.setText("First Pass: (Pbr Textures)")
        layout.addWidget(label_progress_1)

        progress_1 = PySide2.QtWidgets.QProgressBar()
        progress_1.setRange(0, 100)
        progress_1.setValue(0)
        progress_1.setFormat("Calculating...")
        layout.addWidget(progress_1)

        layout.addSpacing(10)

        label_progress_2 = PySide2.QtWidgets.QLabel()
        label_progress_2.setText("Second Pass: (Custom Shader Textures and Parameters)")
        layout.addWidget(label_progress_2)

        progress_2 = PySide2.QtWidgets.QProgressBar()
        progress_2.setRange(0, 100)
        progress_2.setValue(0)
        progress_2.setFormat("Waiting...")
        layout.addWidget(progress_2)

        #window.RegisterEventCallback(self.dialog_callback)

        window.Show()
        self.window_progress = window
        self.progress_1 = progress_1
        self.progress_2 = progress_2


    def update_pbr_progress(self, stage, text = ""):
        if stage == 0:
            self.progress_1.setValue(0)
            self.progress_1.setFormat("Calculating...")
        if stage == 1:
            self.progress_1.setFormat("Cleaning up temp files...")
        elif stage == 2:
            self.count_pbr += 1
            self.progress_1.setValue(self.count_pbr)
            self.progress_1.setFormat(f"Collecting textures ({text}) {round(50.0 * self.count_pbr / self.num_pbr)}%")
        elif stage == 3:
            self.progress_1.setValue(self.count_pbr)
            self.progress_1.setFormat("Loading all PBR textures... (Please Wait)")
        elif stage > 3:
            self.progress_1.setValue(self.num_pbr * 2)
            self.progress_1.setFormat("Done PBR Textures!")
        PySide2.QtWidgets.QApplication.processEvents()


    def update_custom_progress(self, stage, text = ""):
        if stage == 0:
            self.progress_2.setValue(0)
            self.progress_2.setFormat("Waiting...")
        elif stage == 1:
            self.count_custom += 1
            self.progress_2.setValue(self.count_custom)
            self.progress_2.setFormat(f"Processing ({text}): {round(50.0 * self.count_custom/self.num_custom)}%")
        elif stage > 1:
            self.progress_2.setValue(self.num_custom)
            self.progress_2.setFormat("Done Custom Shader Textures and Settings!")
        PySide2.QtWidgets.QApplication.processEvents()


    def import_fbx(self):
        """Import the character into CC3 and read in the json data.
        """
        self.close_options_window()
        if self.json_data:
            if self.import_mesh:

                args = RLPy.EImportFbxOption__None
                if self.character_type == "STANDARD":
                    args = args | RLPy.EImportFbxOption_StandardHumanCharacter
                elif self.character_type == "HUMANOID":
                    args = args | RLPy.EImportFbxOption_Humanoid
                elif self.character_type == "CREATURE":
                    args = args | RLPy.EImportFbxOption_Creature
                elif self.character_type == "PROP":
                    args = args | RLPy.EImportFbxOption_Prop

                RLPy.RFileIO.LoadFbxFile(self.fbx_path, args)

            avatars = RLPy.RScene.GetAvatars(RLPy.EAvatarType_All)
            if len(avatars) > 0:
                self.avatar = avatars[0]
                self.rebuild_materials()
                time.sleep(2)
                RLPy.RScene.SelectObject(self.avatar)
        self.close_progress_window()


    def rebuild_materials(self):
        """Material reconstruction process.
        """
        avatar = self.avatar

        start_timer()

        if self.import_textures or self.import_parameters:
            self.create_progress_window()

            material_component = avatar.GetMaterialComponent()
            mesh_names = avatar.GetMeshNames()

            obj_name_map = None
            if not self.import_mesh:
                obj_name_map = get_json_mesh_name_map(avatar)

            json_data = self.json_data

            char_json = get_character_json(json_data, self.fbx_name, self.fbx_name)

            print("Rebuilding character materials and texures:")

            self.count(char_json, material_component, mesh_names, obj_name_map)

            # only need to import all the textures when importing a new mesh
            if self.import_textures:
                self.import_substance_textures(char_json, material_component, mesh_names, obj_name_map)

            self.import_custom_textures(char_json, material_component, mesh_names, obj_name_map)

            self.import_physics(char_json, obj_name_map)

        RLPy.RGlobal.ObjectModified(avatar, RLPy.EObjectModifiedType_Material)

        log_timer("Import complete! Materials applied in: ")


    def import_custom_textures(self, char_json, material_component, mesh_names, obj_name_map):
        """Process all mesh objects and materials in the avatar, apply material settings,
           texture settings, custom shader textures and parameters from the json data.
        """
        global TEXTURE_MAPS

        key_zero = RLPy.RKey()
        key_zero.SetTime(RLPy.RTime.FromValue(0))

        print(" - Beginning custom shader import...")

        for mesh_name in mesh_names:

            mesh_name = fix_blender_name(mesh_name, self.import_mesh)
            obj_json = get_object_json(char_json, mesh_name, obj_name_map)

            if obj_json:

                mat_names = material_component.GetMaterialNames(mesh_name)

                for mat_name in mat_names:

                    mat_name = fix_blender_name(mat_name, self.import_mesh)
                    mat_json = get_material_json(obj_json, mat_name, obj_name_map)

                    if mat_json:

                        pid = mesh_name + " / " + mat_name
                        shader = material_component.GetShader(mesh_name, mat_name)


                        if self.import_parameters:
                            # Material parameters
                            diffuse_value = get_material_var(mat_json, "Diffuse Color")
                            diffuse_color = RLPy.RRgb(diffuse_value[0], diffuse_value[1], diffuse_value[2])
                            ambient_value = get_material_var(mat_json, "Ambient Color")
                            ambient_color = RLPy.RRgb(ambient_value[0], ambient_value[1], ambient_value[2])
                            specular_value = get_material_var(mat_json, "Specular Color")
                            specular_color = RLPy.RRgb(specular_value[0], specular_value[1], specular_value[2])
                            glow_strength = mat_json["Self Illumination"] * 100.0
                            opacity_strength = mat_json["Opacity"] * 100.0
                            material_component.AddDiffuseKey(key_zero, mesh_name, mat_name, diffuse_color)
                            material_component.AddAmbientKey(key_zero, mesh_name, mat_name, ambient_color)
                            material_component.AddSpecularKey(key_zero, mesh_name, mat_name, 0.0)
                            material_component.AddSelfIlluminationKey(key_zero, mesh_name, mat_name, glow_strength)
                            material_component.AddOpacityKey(key_zero, mesh_name, mat_name, opacity_strength)

                            # Custom shader parameters
                            shader_params = material_component.GetShaderParameterNames(mesh_name, mat_name)
                            for param in shader_params:
                                json_value = None
                                if param.startswith("SSS "):
                                    json_value = get_sss_var(mat_json, param[4:])
                                else:
                                    json_value = get_shader_var(mat_json, param)
                                if json_value is not None:
                                    material_component.SetShaderParameter(mesh_name, mat_name, param, json_value)
                                self.update_custom_progress(1, pid)

                        if self.import_textures:
                            # Custom shader textures
                            shader_textures = material_component.GetShaderTextureNames(mesh_name, mat_name)
                            if shader_textures:
                                for shader_texture in shader_textures:
                                    tex_info = get_shader_texture_info(mat_json, shader_texture)
                                    tex_path = convert_texture_path(tex_info, "Texture Path", self.fbx_folder)
                                    if tex_path:
                                        material_component.LoadShaderTexture(mesh_name, mat_name, shader_texture, tex_path)
                                    self.update_custom_progress(1, pid)

                            # Pbr Textures
                            for tex_id in TEXTURE_MAPS.keys():
                                tex_channel = TEXTURE_MAPS[tex_id][0]
                                is_substance = TEXTURE_MAPS[tex_id][1]
                                if self.mat_duplicates[mat_name]: # fully process textures for materials with duplicates,
                                    is_substance = False          # as the substance texture import can't really deal with them.
                                if not self.substance_import_success: # or if the substance texture import method failed
                                    is_substance = False              # import all textures individually
                                tex_info = get_pbr_texture_info(mat_json, tex_id)
                                tex_path = convert_texture_path(tex_info, "Texture Path", self.fbx_folder)
                                if tex_path:
                                    if tex_id == "Base Color" and os.path.splitext(tex_path)[-1].lower() == ".png":
                                        is_substance = False
                                    strength = float(tex_info["Strength"]) / 100.0
                                    offset = tex_info["Offset"]
                                    offset_vector = RLPy.RVector2(float(offset[0]), float(offset[1]))
                                    tiling = tex_info["Tiling"]
                                    tiling_vector = RLPy.RVector2(float(tiling[0]), float(tiling[1]))
                                    # Note: rotation doesn't seem to be exported to the Json?
                                    rotation = float(0.0)
                                    if "Rotation" in tex_info.keys():
                                        rotation = float(tex_info["Rotation"])
                                    # set textures
                                    if os.path.exists(tex_path):
                                        if not is_substance:
                                            material_component.LoadImageToTexture(mesh_name, mat_name, tex_channel, tex_path)
                                        material_component.AddUvDataKey(key_zero, mesh_name, mat_name, tex_channel, offset_vector, tiling_vector, rotation)
                                        material_component.AddTextureWeightKey(key_zero, mesh_name, mat_name, tex_channel, strength)
                                        twl = material_component.GetTextureWeights(mesh_name, mat_name)
                                    if tex_id == "Displacement":
                                        level = 0
                                        multiplier = 0
                                        threshold = 50
                                        if "Tessellation Level" in tex_info:
                                            level = tex_info["Tessellation Level"]
                                        if "Multiplier" in tex_info:
                                            multiplier = tex_info["Multiplier"]
                                        if "Gray-scale Base Value" in tex_info:
                                            threshold = tex_info["Gray-scale Base Value"] * 100
                                        material_component.SetAttributeValue(mesh_name, mat_name, "TessellationLevel", level)
                                        material_component.SetAttributeValue(mesh_name, mat_name, "TessellationMultiplier", multiplier)
                                        material_component.SetAttributeValue(mesh_name, mat_name, "TessellationThreshold", threshold)
                                self.update_custom_progress(1, pid)

            self.update_custom_progress(2)

        print(" - Custom shader import complete!")


    def import_substance_textures(self, char_json, material_component, mesh_names, obj_name_map):
        """Cache all PBR textures in a temporary location to load in all at once with:
           RLPy.RFileIO.LoadSubstancePainterTextures()
           This is *much* faster than loading these textures individually,
           but requires a particular directory and file naming structure.
        """
        global TEXTURE_MAPS, NUM_SUBSTANCE_MAPS

        print(" - Beginning substance texture import...")

        self.update_pbr_progress(1)
        self.substance_import_success = False

        # create temp folder for substance import (use the temporary files location from the RGlobal.GetPath)
        res = RLPy.RGlobal.GetPath(RLPy.EPathType_Temp, "")
        temp_path = res[1]
        # safest not to write temporary files in random locations...
        if not os.path.exists(temp_path):
            print(" - Unable to determine temporary file location, skipping substance import!")
            return

        temp_folder = os.path.join(temp_path, "CC3_BTP_Temp_" + random_string(8))
        print(" - Using temp folder: " + temp_folder)

        # delete if exists
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
        # make a new temporary folder
        os.mkdir(temp_folder)

        for mesh_name in mesh_names:

            mesh_name = fix_blender_name(mesh_name, self.import_mesh)
            obj_json = get_object_json(char_json, mesh_name, obj_name_map)

            if obj_json:

                mat_names = material_component.GetMaterialNames(mesh_name)

                if mesh_name.startswith("CC_Base_Body"):
                    # body is a special case, everything is stored in the first material name with incremental indicees

                    # create folder with first matertial name in each mesh
                    first_mat_in_mesh = mat_names[0]
                    mesh_folder = os.path.join(temp_folder, first_mat_in_mesh)
                    os.mkdir(mesh_folder)

                    mat_index = 1001

                    for mat_name in mat_names:

                        mat_name = fix_blender_name(mat_name, self.import_mesh)
                        mat_json = get_material_json(obj_json, mat_name, obj_name_map)

                        if mat_json:

                            pid = mesh_name + " / " + mat_name

                            # for each texture channel that can be imported with the substance texture method:
                            for tex_id in TEXTURE_MAPS.keys():
                                is_substance = TEXTURE_MAPS[tex_id][1]
                                if is_substance:
                                    tex_channel = TEXTURE_MAPS[tex_id][0]
                                    substance_postfix = TEXTURE_MAPS[tex_id][2]
                                    tex_info = get_pbr_texture_info(mat_json, tex_id)
                                    tex_path = convert_texture_path(tex_info, "Texture Path", self.fbx_folder)
                                    if tex_path:
                                        tex_dir, tex_file = os.path.split(tex_path)
                                        tex_name, tex_type = os.path.splitext(tex_file)
                                        # copy valid texture files to the temporary texture cache
                                        if os.path.exists(tex_path):
                                            substance_name = first_mat_in_mesh + "_" + str(mat_index) + "_" + substance_postfix + tex_type
                                            substance_path = os.path.join(mesh_folder, substance_name)
                                            shutil.copyfile(tex_path, substance_path)

                                    self.update_pbr_progress(2, pid)

                        mat_index += 1

                else:

                    for mat_name in mat_names:

                        pid = mesh_name + " / " + mat_name

                        has_duplicates = False
                        if mat_name in self.mat_duplicates.keys() and self.mat_duplicates[mat_name]:
                            has_duplicates = True

                        # only process those materials here that don't have duplicates
                        # substance texture import doesn't deal with duplicates well...
                        if not has_duplicates:

                            mat_name = fix_blender_name(mat_name, self.import_mesh)
                            mat_json = get_material_json(obj_json, mat_name, obj_name_map)

                            if mat_json:

                                # create folder with the matertial name
                                mesh_folder = os.path.join(temp_folder, mat_name)
                                os.mkdir(mesh_folder)

                                mat_index = 1001

                                # for each texture channel that can be imported with the substance texture method:
                                for tex_id in TEXTURE_MAPS.keys():
                                    is_substance = TEXTURE_MAPS[tex_id][1]
                                    if is_substance:
                                        tex_channel = TEXTURE_MAPS[tex_id][0]
                                        substance_postfix = TEXTURE_MAPS[tex_id][2]
                                        tex_info = get_pbr_texture_info(mat_json, tex_id)
                                        tex_path = convert_texture_path(tex_info, "Texture Path", self.fbx_folder)
                                        if tex_path:
                                            tex_dir, tex_file = os.path.split(tex_path)
                                            tex_name, tex_type = os.path.splitext(tex_file)
                                            # copy valid texture files to the temporary texture cache
                                            if os.path.exists(tex_path):
                                                substance_name = mat_name + "_" + str(mat_index) + "_" + substance_postfix + tex_type
                                                substance_path = os.path.join(mesh_folder, substance_name)
                                                shutil.copyfile(tex_path, substance_path)

                                        self.update_pbr_progress(2, pid)

                        else:
                            self.count_pbr += (NUM_SUBSTANCE_MAPS - 1)
                            self.update_pbr_progress(2, pid)

        self.update_pbr_progress(3)
        avatar = self.avatar

        # load all pbr textures in one go from the texture cache
        RLPy.RFileIO.LoadSubstancePainterTextures(avatar, temp_folder)
        self.substance_import_success = True

        print (" - Substance texture import successful!")
        print (" - Cleaning up temp folder: " + temp_folder)

        # delete temp folder
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)

        self.update_pbr_progress(4)


    def count(self, char_json, material_component, mesh_names, obj_name_map):
        """Precalculate the number of materials, textures and parameters that need to be processed,
           to initialise progress bars.
           Also determine which materials may have duplicate names as these need to be treated differently.
        """
        global TEXTURE_MAPS, NUM_SUBSTANCE_MAPS

        num_materials = 0
        num_params = 0
        num_textures = 0
        num_custom = 0
        num_pbr = 0

        self.mat_duplicates = {}

        for mesh_name in mesh_names:

            mesh_name = fix_blender_name(mesh_name, self.import_mesh)
            obj_json = get_object_json(char_json, mesh_name, obj_name_map)

            if obj_json:

                mat_names = material_component.GetMaterialNames(mesh_name)
                for mat_name in mat_names:

                    mat_name = fix_blender_name(mat_name, self.import_mesh)
                    mat_json = get_material_json(obj_json, mat_name, obj_name_map)

                    if mat_json:

                        # determine material duplicates
                        if mat_name in self.mat_duplicates.keys():
                            self.mat_duplicates[mat_name] = True
                        else:
                            self.mat_duplicates[mat_name] = False

                        # ensure the shader is correct:
                        imported_shader = material_component.GetShader(mesh_name, mat_name)
                        wanted_shader = SHADER_MAPS[mat_json["Material Type"]]
                        if "Custom Shader" in mat_json.keys():
                            wanted_shader = SHADER_MAPS[mat_json["Custom Shader"]["Shader Name"]]
                        if imported_shader != wanted_shader:
                            material_component.SetShader(mesh_name, mat_name, "PBR")
                            material_component.SetShader(mesh_name, mat_name, wanted_shader)

                        # Calculate stats
                        num_pbr += NUM_SUBSTANCE_MAPS
                        num_materials += 1

                        # Custom shader parameters
                        if self.import_parameters:
                            shader_params = material_component.GetShaderParameterNames(mesh_name, mat_name)
                            num_params += len(shader_params)

                        # Custom shader textures
                        if self.import_textures:
                            shader_textures = material_component.GetShaderTextureNames(mesh_name, mat_name)
                            num_textures += len(shader_textures)
                            # Pbr Textures
                            num_textures += len(TEXTURE_MAPS)

        self.num_pbr = num_pbr
        self.num_custom = num_params + num_textures

        self.progress_1.setRange(0, self.num_pbr * 2)
        self.progress_2.setRange(0, self.num_custom)
        self.count_pbr = 0
        self.count_custom = 0
        self.update_pbr_progress(0)
        self.update_custom_progress(0)

        PySide2.QtWidgets.QApplication.processEvents()


    def import_physics(self, char_json, obj_name_map):
        avatar = RLPy.RScene.GetAvatars()[0]
        child_objects = RLPy.RScene.FindChildObjects(avatar, RLPy.EObjectType_Avatar)
        done = []

        print(f"Import Physics")

        for obj in child_objects:
            physics_component = obj.GetPhysicsComponent()

            if physics_component:
                mesh_names = physics_component.GetSoftPhysicsMeshNameList()

                for mesh_name in mesh_names:

                    if mesh_name not in done:
                        done.append(mesh_name)

                        physics_object_json = get_physics_object_json(char_json, mesh_name, obj_name_map)
                        if physics_object_json:

                            material_names = physics_component.GetSoftPhysicsMaterialNameList(mesh_name)

                            for mat_name in material_names:
                                physics_material_json = get_physics_material_json(physics_object_json, mat_name, obj_name_map)

                                if physics_material_json:
                                    print(f"Object: {obj.GetName()}, Mesh: {mesh_name}, Material: {mat_name}")
                                    mass = None
                                    for json_param_name in physics_material_json.keys():
                                        phys_param_name = json_param_name.replace(' ', '').replace('_', '')
                                        param_value = get_physics_var(physics_material_json, json_param_name)
                                        print(f"  Param: {phys_param_name} = {param_value}")

                                        if json_param_name == "Activate Physics": # activate physics
                                            physics_component.SetActivatePhysicsEnable(param_value)

                                        elif json_param_name == "Use Global Gravity": # global gravity
                                            physics_component.SetObjectGravityEnable(mesh_name, mat_name, param_value)

                                        elif json_param_name == "Weight Map Path": # weight map
                                            tex_path = convert_texture_path(physics_material_json, json_param_name, self.fbx_folder)
                                            if tex_path:
                                                physics_component.SetPhysicsSoftColthWeightMap(mesh_name, mat_name, tex_path)

                                        elif json_param_name == "Soft Vs Rigid Collision" or json_param_name == "Self Collision":
                                            physics_component.SetSoftPhysXCollisionEnable(mesh_name, mat_name, phys_param_name, param_value)

                                        elif json_param_name == "Soft Vs Rigid Collision_Margin" or json_param_name == "Self Collision Margin":
                                            physics_component.SetSoftPhysXCollisionValue(mesh_name, mat_name, phys_param_name, param_value)

                                        elif json_param_name == "Mass":
                                            mass = param_value

                                        else:
                                            physics_component.SetSoftPhysXProperty(mesh_name, mat_name, phys_param_name, float(param_value))

                                    # mass needs to be set last or set after something else, otherwise it gets reset back to 1
                                    if mass is not None:
                                        physics_component.SetSoftPhysXProperty(mesh_name, mat_name, "Mass", mass)


#
# Functions
#

def message_box(msg):
    RLPy.RUi.ShowMessageBox("Message", str(msg), RLPy.EMsgButton_Ok)


TIMER = 0

def start_timer():
    global TIMER
    TIMER = time.perf_counter()


def log_timer(msg, unit = "s"):
    global TIMER
    duration = time.perf_counter() - TIMER
    if unit == "ms":
        duration *= 1000
    elif unit == "us":
        duration *= 1000000
    elif unit == "ns":
        duration *= 1000000000
    print(msg + ": " + str(duration) + " " + unit)


def fix_blender_name(name: str, import_mesh):
    """Remove any Blenderized duplicate name suffixes, but *only* if imported from Blender.
       CC3 exports replace and ' ' or '.' with underscores, so the Json data will have no
       blender duplication suffixes.
       This function is used to remove any Blender duplication suffix from the mesh/material
       names, just in case...
    """
    if import_mesh and len(name) > 4:
        if name[-3:].isdigit() and name[-4] == ".":
            name = name[:-4]
    return name


def convert_texture_path(tex_info, var_name, folder):
    """Get the Json texture path relative to the import character file.
    """
    if tex_info and var_name in tex_info.keys():
        rel_path = tex_info[var_name]
        if os.path.isabs(rel_path):
            return os.path.normpath(rel_path)
        return os.path.join(folder, rel_path)
    return None


def get_json_mesh_name_map(avatar):
    """When trying to match the original character objects and meshes with an export from Blender:
       (i.e. when importing textures and paramaters over the *original* character mesh.)

       CC3 names each export mesh with the original object name replacing ' '/'.' with underscores.
       So to match the original mesh names with the newly imported json data mesh names, we need to
       re-construct the CC3 exported mesh json names from the original object names.

       This function generates a name mapping dictionary from the original character mesh name to
       the blender exported mesh name, which is used as a fallback name to find the mesh json data
       in get_object_json()
    """
    mapping = {}
    ignore = ["RL_BoneRoot", "IKSolverDummy"]
    child_objects = RLPy.RScene.FindChildObjects(avatar, RLPy.EObjectType_Avatar)
    for obj in child_objects:
        obj_name = obj.GetName()
        if obj_name not in ignore:
            mesh_names = obj.GetMeshNames()
            for mesh_name in mesh_names:
                mapping[mesh_name] = fix_json_name(obj_name)
    return mapping


def fix_json_name(mat_name):
    """When matching *original* character object/material names to to imported json data from Blender,
       replace spaces and dots with underscores."""
    return mat_name.replace(' ','_').replace('.','_')


def read_json(json_path):
    try:
        if os.path.exists(json_path):
            print(" - Loading Json data: " + json_path)

            # determine start of json text data
            file_bytes = open(json_path, "rb")
            bytes = file_bytes.read(3)
            file_bytes.close()
            start = 0
            # json files outputted from Visual Studio projects start with a byte mark order block (3 bytes EF BB BF)
            if bytes[0] == 0xEF and bytes[1] == 0xBB and bytes[2] == 0xBF:
                start = 3

            # read json text
            file = open(json_path, "rt")
            file.seek(start)
            text_data = file.read()
            json_data = json.loads(text_data)
            file.close()
            print(" - Json data successfully parsed!")
            return json_data

        print(" - No Json Data!")
        return None
    except:
        print(" - Error reading Json Data!")
        return None


def get_character_generation_json(json_data, file_name, character_id):
    try:
        return json_data[file_name]["Object"][character_id]["Generation"]
    except:
        return "Unknown"

def get_character_root_json(json_data, file_name):
    if not json_data:
        return None
    try:
        return json_data[file_name]["Object"]
    except:
        return None


def get_character_json(json_data, file_name, character_id):
    if not json_data:
        return None
    try:
        character_json = json_data[file_name]["Object"][character_id]
        return character_json
    except:
        print("Could not find character json: " + character_id)
        return None


def get_object_json(character_json, mesh_name, json_name_map):
    if not character_json:
        return None
    try:
        meshes_json = character_json["Meshes"]
        for object_name in meshes_json.keys():
            if object_name == mesh_name:
                return meshes_json[object_name]
        if json_name_map:
            # look for the json mesh name from the original object name remaps
            search_obj_name = json_name_map[mesh_name]
            for object_name in meshes_json.keys():
                if object_name == search_obj_name:
                    return meshes_json[object_name]
    except:
        pass
    print("Could not find object json: " + mesh_name)
    return None


def get_physics_object_json(character_json, mesh_name, json_name_map):
    if not character_json:
        return None
    try:
        physics_object_json = character_json["Physics"]["Soft Physics"]["Meshes"]
        for object_name in physics_object_json.keys():
            if object_name == mesh_name:
                return physics_object_json[object_name]
        if json_name_map:
            # look for the json mesh name from the original object name remaps
            search_obj_name = json_name_map[mesh_name]
            for object_name in physics_object_json.keys():
                if object_name == search_obj_name:
                    return physics_object_json[object_name]
    except:
        pass
    #print("Could not find physics object json: " + mesh_name)
    return None


def get_physics_material_json(physics_object_json, mat_name, json_name_map):
    if not physics_object_json:
        return None
    try:
        physics_materials_json = physics_object_json["Materials"]
        for material_name in physics_materials_json.keys():
            if material_name == mat_name:
                return physics_materials_json[material_name]
        if json_name_map: # json_name_map used only to test for re-import over existing avatar
            mat_name_ext = fix_json_name(mat_name)
            # some materials are suffixed with _Transparency
            for material_name in physics_materials_json.keys():
                if material_name == mat_name_ext or material_name == mat_name_ext + "_Transparency":
                    return physics_materials_json[material_name]
    except:
        pass
    print("Could not find physics material json: " + mat_name)
    return None


def get_custom_shader(material_json):
    try:
        return material_json["Custom Shader"]["Shader Name"]
    except:
        try:
            return material_json["Material Type"]
        except:
            return "Pbr"


def get_material_json(object_json, mat_name, json_name_map):
    if not object_json:
        return None
    try:
        materials_json = object_json["Materials"]
        for material_name in materials_json.keys():
            if material_name == mat_name:
                return materials_json[material_name]
        if json_name_map: # json_name_map used only to test for re-import over existing avatar
            mat_name_ext = fix_json_name(mat_name)
            # some materials are suffixed with _Transparency
            for material_name in materials_json.keys():
                if material_name == mat_name_ext or material_name == mat_name_ext + "_Transparency":
                    return materials_json[material_name]
    except:
        pass
    print("Could not find material json: " + mat_name)
    return None


def get_texture_info(material_json, texture_id):
    tex_info = get_pbr_texture_info(material_json, texture_id)
    if tex_info is None:
        tex_info = get_shader_texture_info(material_json, texture_id)
    return tex_info


def get_pbr_texture_info(material_json, texture_id):
    if not material_json:
        return None
    try:
        return material_json["Textures"][texture_id]
    except:
        return None


def get_shader_texture_info(material_json, texture_id):
    if not material_json:
        return None
    try:
        return material_json["Custom Shader"]["Image"][texture_id]
    except:
        return None


def get_material_json_var(material_json, var_path: str):
    var_type, var_name = var_path.split('/')
    if var_type == "Custom":
        return get_shader_var(material_json, var_name)
    elif var_type == "SSS":
        return get_sss_var(material_json, var_name)
    elif var_type == "Pbr":
        return get_pbr_var(material_json, var_name)
    else: # var_type == "Base":
        return get_material_var(material_json, var_name)


def get_changed_json(json_item):
    if json_item:
        try:
            return json_item["Has Changed"]
        except:
            pass
    return False


def rgb_to_float(rgb):
    l = len(rgb)
    out = []
    for i in range(0, l):
        out.append(rgb[i] / 255.0)
    return out


def convert_var(var_name, var_value):
    if type(var_value) == tuple or type(var_value) == list:
        if len(var_value) == 3:
            return rgb_to_float(var_value)
        else:
            return var_value
    else:
        return [var_value]


def convert_phys_var(var_name, var_value):
    if type(var_value) == tuple or type(var_value) == list:
        if var_name == "Inertia":
            return var_value[0]
    return var_value


def get_shader_var(material_json, var_name):
    if not material_json:
        return None
    try:
        result = material_json["Custom Shader"]["Variable"][var_name]
        return convert_var(var_name, result)
    except:
        return None


def get_pbr_var(material_json, var_name):
    if not material_json:
        return None
    try:
        #result = material_json["Textures"][var_name]["Strength"] / 100.0
        result = material_json["Textures"][var_name]["Strength"]
        return convert_var(var_name, result)
    except:
        return None


def get_material_var(material_json, var_name):
    if not material_json:
        return None
    try:
        result = material_json[var_name]
        return convert_var(var_name, result)
    except:
        return None


def get_sss_var(material_json, var_name):
    if not material_json:
        return None
    try:
        result = material_json["Subsurface Scatter"][var_name]
        return convert_var(var_name, result)
    except:
        return None


def get_physics_var(physics_material_json, var_name):
    if not physics_material_json:
        return None
    try:
        result = physics_material_json[var_name]
        return convert_phys_var(var_name, result)
    except:
        return None


def random_string(length):
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    l = len(chars)
    res = ""
    for i in range(0, length):
        r = random.randrange(0, l)
        res += chars[r]
    return res


def run_script():
    menu_import_standard()
    #menu_export()