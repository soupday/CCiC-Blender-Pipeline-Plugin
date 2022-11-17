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

VERSION = "1.1.1"

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

NUM_SUBSTANCE_MAPS = 10

PLUGIN_MENU = None
MENU_IMPORT = None
MENU_EXPORT = None
FBX_IMPORTER = None
FBX_EXPORTER = None


def initialize_plugin():
    global PLUGIN_MENU
    global MENU_IMPORT
    global MENU_EXPORT

    # Add menu
    PLUGIN_MENU = wrapInstance(int(RLPy.RUi.AddMenu("Blender Pipeline", RLPy.EMenu_Plugins)), PySide2.QtWidgets.QMenu)

    MENU_EXPORT = PLUGIN_MENU.addAction("Export Character to Blender")
    MENU_EXPORT.triggered.connect(menu_export)

    PLUGIN_MENU.addSeparator()

    MENU_IMPORT = PLUGIN_MENU.addAction("Import Character from Blender")
    MENU_IMPORT.triggered.connect(menu_import)


def menu_import():
    global FBX_IMPORTER
    FBX_IMPORTER = None

    file_path = RLPy.RUi.OpenFileDialog("Fbx Files(*.fbx)")
    if file_path and file_path != "":
        FBX_IMPORTER = Importer(file_path)


def menu_export():
    global FBX_EXPORTER
    FBX_EXPORTER = None

    avatar_list = RLPy.RScene.GetAvatars()
    if len(avatar_list) > 0:
        FBX_EXPORTER = Exporter()


def clean_up_globals():
    global FBX_IMPORTER
    global FBX_EXPORTER
    FBX_IMPORTER = None
    FBX_EXPORTER = None


def do_events():
    PySide2.QtWidgets.QApplication.processEvents()


def log(message):
    print(message)
    do_events()








#
# Class: Importer
#

class Importer:
    path = "C:/folder/dummy.fbx"
    folder = "C:/folder"
    file = "dummy.fbx"
    key = "C:/folder/dummy.fbxkey"
    name = "dummy"
    json_path = "C:/folder/dummy.json"
    hik_path = "C:/folder/dummy.3dxProfile"
    profile_path = "C:/folder/dummy.ccFacialProfile"
    json_data = None
    avatar = None
    window_options = None
    window_progress = None
    progress_1 = None
    progress_2 = None
    check_mesh = None
    check_textures = None
    check_parameters = None
    check_import_hik = None
    check_import_profile = None
    check_import_expressions = None
    num_pbr = 0
    num_custom = 0
    count_pbr = 0
    count_custom = 0
    mat_duplicates = {}
    substance_import_success = False
    option_mesh = True
    option_textures = True
    option_parameters = True
    option_import_hik = False
    option_import_profile = False
    option_import_expressions = None
    character_type = None
    generation = None


    def __init__(self, file_path):
        log("================================================================")
        log("New character import, Fbx: " + file_path)
        self.path = file_path
        self.file = os.path.basename(self.path)
        self.folder = os.path.dirname(self.path)
        self.name = os.path.splitext(self.file)[0]
        self.key = os.path.join(self.folder, self.name + ".fbxkey")
        self.json_path = os.path.join(self.folder, self.name + ".json")
        self.json_data = read_json(self.json_path)
        self.hik_path = os.path.join(self.folder, self.name + ".3dxProfile")
        self.profile_path = os.path.join(self.folder, self.name + ".ccFacialProfile")

        self.generation = get_character_generation_json(self.json_data, self.name, self.name)
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
            if not os.path.exists(self.key):
                message_box("There is no Fbx Key with this character!\n\nCC3/4 Standard characters cannot be imported back into Character Creator without a corresponding Fbx Key.\nThe Fbx Key will be generated when the character is exported as Mesh only, or in Calibration Pose, and with no hidden faces.")
                error = True

        self.option_mesh = True
        self.option_textures = True
        self.option_parameters = True
        self.option_import_hik = False
        self.option_import_profile = False
        self.option_import_expressions = False
        if self.json_data:
            if self.name in self.json_data.keys():
                if "HIK" in self.json_data[self.name].keys():
                    if "Profile_Path" in self.json_data[self.name]["HIK"].keys():
                        self.hik_path = os.path.join(self.folder, self.json_data[self.name]["HIK"]["Profile_Path"])
                        self.option_import_hik = True
                if "Facial_Profile" in self.json_data[self.name].keys():
                    if "Profile_Path" in self.json_data[self.name]["Facial_Profile"].keys():
                        self.profile_path = os.path.join(self.folder, self.json_data[self.name]["Facial_Profile"]["Profile_Path"])
                        self.option_import_profile = True
                    if "Categories" in self.json_data[self.name]["Facial_Profile"].keys():
                        self.option_import_expressions = True

        if not error:
            self.create_options_window()


    def fetch_options(self):
        if self.check_mesh: self.option_mesh = self.check_mesh.isChecked()
        if self.check_textures: self.option_textures = self.check_textures.isChecked()
        if self.check_parameters: self.option_parameters = self.check_parameters.isChecked()
        if self.check_import_expressions: self.option_import_expressions = self.check_import_expressions.isChecked()
        if self.check_import_hik: self.option_import_hik = self.check_import_hik.isChecked()
        if self.check_import_profile: self.option_import_profile = self.check_import_profile.isChecked()


    def close_options_window(self):
        if self.window_options:
            self.window_options.Close()
        self.window_options = None
        self.check_mesh = None
        self.check_textures = None
        self.check_parameters = None
        self.check_import_expressions = None
        self.check_import_hik = None
        self.check_import_profile = None


    def close_progress_window(self):
        self.close_options_window()
        if self.window_progress:
            self.window_progress.Close()
        self.path = "C:/folder/dummy.fbx"
        self.folder = "C:/folder"
        self.file = "dummy.fbx"
        self.name = "dummy"
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
        self.window_options = RLPy.RUi.CreateRDockWidget()
        self.window_options.SetWindowTitle(f"Blender Auto-setup Character Import ({VERSION}) - Options")

        dock = wrapInstance(int(self.window_options.GetWindow()), PySide2.QtWidgets.QDockWidget)
        dock.setFixedWidth(500)

        widget = PySide2.QtWidgets.QWidget()
        dock.setWidget(widget)

        layout = PySide2.QtWidgets.QVBoxLayout()
        widget.setLayout(layout)

        label_1 = PySide2.QtWidgets.QLabel()
        label_1.setText(f"Character Name: {self.name}")
        layout.addWidget(label_1)

        label_2 = PySide2.QtWidgets.QLabel()
        label_2.setText(f"Character Path: {self.path}")
        layout.addWidget(label_2)

        label_3 = PySide2.QtWidgets.QLabel()
        label_3.setText(f"Type: {self.character_type}")
        layout.addWidget(label_3)

        layout.addSpacing(10)

        row = PySide2.QtWidgets.QHBoxLayout()
        layout.addLayout(row)

        col_1 = PySide2.QtWidgets.QVBoxLayout()
        col_2 = PySide2.QtWidgets.QVBoxLayout()
        row.addLayout(col_1)
        row.addLayout(col_2)

        self.check_mesh = PySide2.QtWidgets.QCheckBox()
        self.check_mesh.setText("Import Mesh")
        self.check_mesh.setChecked(self.option_mesh)
        col_1.addWidget(self.check_mesh)

        self.check_textures = PySide2.QtWidgets.QCheckBox()
        self.check_textures.setText("Import Textures")
        self.check_textures.setChecked(self.option_textures)
        col_1.addWidget(self.check_textures)

        self.check_parameters = PySide2.QtWidgets.QCheckBox()
        self.check_parameters.setText("Import Parameters")
        self.check_parameters.setChecked(self.option_parameters)
        col_1.addWidget(self.check_parameters)

        self.check_import_hik = PySide2.QtWidgets.QCheckBox()
        self.check_import_hik.setText("Import HIK Profile")
        self.check_import_hik.setChecked(self.option_import_hik)
        col_2.addWidget(self.check_import_hik)

        self.check_import_profile = PySide2.QtWidgets.QCheckBox()
        self.check_import_profile.setText("Import Facial Profile")
        self.check_import_profile.setChecked(self.option_import_profile)
        col_2.addWidget(self.check_import_profile)

        self.check_import_expressions = PySide2.QtWidgets.QCheckBox()
        self.check_import_expressions.setText("Import Facial Expressions")
        self.check_import_expressions.setChecked(self.option_import_expressions)
        col_2.addWidget(self.check_import_expressions)

        layout.addSpacing(10)

        start_button = PySide2.QtWidgets.QPushButton("Import Character", minimumHeight=32)
        start_button.clicked.connect(self.import_fbx)
        layout.addWidget(start_button)

        cancel_button = PySide2.QtWidgets.QPushButton("Cancel", minimumHeight=32)
        cancel_button.clicked.connect(self.close_progress_window)
        layout.addWidget(cancel_button)

        #self.window_options.RegisterEventCallback(self.dialog_callback)

        self.window_options.Show()


    def create_progress_window(self):
        self.window_progress = RLPy.RUi.CreateRDockWidget()
        self.window_progress.SetWindowTitle("Blender Auto-setup Character Import - Progress")

        dock = wrapInstance(int(self.window_progress.GetWindow()), PySide2.QtWidgets.QDockWidget)
        dock.setFixedWidth(500)

        widget = PySide2.QtWidgets.QWidget()
        dock.setWidget(widget)

        layout = PySide2.QtWidgets.QVBoxLayout()
        widget.setLayout(layout)

        label_1 = PySide2.QtWidgets.QLabel()
        label_1.setText(f"Character Name: {self.name}")
        layout.addWidget(label_1)

        label_2 = PySide2.QtWidgets.QLabel()
        label_2.setText(f"Character Path: {self.path}")
        layout.addWidget(label_2)

        layout.addSpacing(10)

        label_progress_1 = PySide2.QtWidgets.QLabel()
        label_progress_1.setText("First Pass: (Pbr Textures)")
        layout.addWidget(label_progress_1)

        self.progress_1 = PySide2.QtWidgets.QProgressBar()
        self.progress_1.setRange(0, 100)
        self.progress_1.setValue(0)
        self.progress_1.setFormat("Calculating...")
        layout.addWidget(self.progress_1)

        layout.addSpacing(10)

        label_progress_2 = PySide2.QtWidgets.QLabel()
        label_progress_2.setText("Second Pass: (Custom Shader Textures and Parameters)")
        layout.addWidget(label_progress_2)

        self.progress_2 = PySide2.QtWidgets.QProgressBar()
        self.progress_2.setRange(0, 100)
        self.progress_2.setValue(0)
        self.progress_2.setFormat("Waiting...")
        layout.addWidget(self.progress_2)

        #self.window_progress.RegisterEventCallback(self.dialog_callback)

        self.window_progress.Show()


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
        do_events()


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
        do_events()


    def import_fbx(self):
        """Import the character into CC3 and read in the json data.
        """
        self.fetch_options()
        self.close_options_window()

        if self.json_data:

            # importing changes the selection so store it first.
            selected_objects = RLPy.RScene.GetSelectedObjects()
            objects = []

            if self.option_mesh:

                args = RLPy.EImportFbxOption__None
                if self.character_type == "STANDARD":
                    args = args | RLPy.EImportFbxOption_StandardHumanCharacter
                elif self.character_type == "HUMANOID":
                    args = args | RLPy.EImportFbxOption_Humanoid
                elif self.character_type == "CREATURE":
                    args = args | RLPy.EImportFbxOption_Creature
                elif self.character_type == "PROP":
                    args = args | RLPy.EImportFbxOption_Prop

                # to determine which prop(s) was imported, store a list of all current props
                if self.character_type == "PROP":
                    stored_props = RLPy.RScene.GetProps()

                RLPy.RFileIO.LoadFbxFile(self.path, args)

                # any prop not in the stored list is newly imported.
                if self.character_type == "PROP":
                    all_props = RLPy.RScene.GetProps()
                    for prop in all_props:
                        if prop not in stored_props:
                            objects.append(prop)
            else:

                if self.character_type == "PROP":
                   objects = selected_objects

            # if not importing a prop, use the current avatar
            if self.character_type != "PROP":
                avatars = RLPy.RScene.GetAvatars(RLPy.EAvatarType_All)
                objects = [avatars[0]]

            if len(objects) > 0:
                for obj in objects:
                    self.avatar = obj
                    self.rebuild_materials()
                    RLPy.RScene.SelectObject(obj)


    def rebuild_materials(self):
        """Material reconstruction process.
        """
        avatar = self.avatar

        start_timer()

        if self.option_textures or self.option_parameters:
            self.create_progress_window()

            material_component = avatar.GetMaterialComponent()
            mesh_names = avatar.GetMeshNames()

            obj_name_map = None
            if not self.option_mesh:
                obj_name_map = get_json_mesh_name_map(avatar)

            json_data = self.json_data

            char_json = get_character_json(json_data, self.name, self.name)

            log("Rebuilding character materials and texures:")

            self.count(char_json, material_component, mesh_names, obj_name_map)

            # only need to import all the textures when importing a new mesh
            if self.character_type != "PROP":
                if self.option_textures:
                    self.import_substance_textures(char_json, material_component, mesh_names, obj_name_map)

            self.import_custom_textures(char_json, material_component, mesh_names, obj_name_map)

            self.import_physics(char_json, obj_name_map)

        if self.character_type == "HUMANOID":
            self.import_hik_profile()

        if self.character_type == "STANDARD" or self.character_type == "HUMANOID":
            self.window_progress.Close()
            self.import_facial_profile()

        time.sleep(1)
        self.close_progress_window()

        RLPy.RGlobal.ObjectModified(avatar, RLPy.EObjectModifiedType_Material)

        log_timer("Import complete! Materials applied in: ")


    def import_custom_textures(self, char_json, material_component, mesh_names, obj_name_map):
        """Process all mesh objects and materials in the avatar, apply material settings,
           texture settings, custom shader textures and parameters from the json data.
        """
        global TEXTURE_MAPS

        key_zero = RLPy.RKey()
        key_zero.SetTime(RLPy.RTime.FromValue(0))

        log(" - Beginning custom shader import...")

        for mesh_name in mesh_names:

            mesh_name = fix_blender_name(mesh_name, self.option_mesh)
            obj_json = get_object_json(char_json, mesh_name, obj_name_map)

            if obj_json:

                mat_names = material_component.GetMaterialNames(mesh_name)

                for mat_name in mat_names:

                    mat_name = fix_blender_name(mat_name, self.option_mesh)
                    mat_json = get_material_json(obj_json, mat_name, obj_name_map)

                    if mat_json:

                        pid = mesh_name + " / " + mat_name
                        shader = material_component.GetShader(mesh_name, mat_name)


                        if self.option_parameters:
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

                        if self.option_textures and "Textures" in mat_json.keys():

                            # Custom shader textures
                            shader_textures = material_component.GetShaderTextureNames(mesh_name, mat_name)
                            if shader_textures:
                                for shader_texture in shader_textures:
                                    tex_info = get_shader_texture_info(mat_json, shader_texture)
                                    tex_path = convert_texture_path(tex_info, "Texture Path", self.folder)
                                    if tex_path and os.path.exists(tex_path) and os.path.isfile(tex_path):
                                        material_component.LoadShaderTexture(mesh_name, mat_name, shader_texture, tex_path)
                                    self.update_custom_progress(1, pid)

                            # Pbr Textures
                            png_base_color = False
                            has_opacity_map = "Opacity" in mat_json["Textures"].keys()
                            for tex_id in TEXTURE_MAPS.keys():
                                tex_channel = TEXTURE_MAPS[tex_id][0]
                                is_substance = TEXTURE_MAPS[tex_id][1]
                                load_texture = not is_substance
                                # fully process textures for materials with duplicates,
                                # as the substance texture import can't really deal with them.
                                if self.mat_duplicates[mat_name]:
                                    load_texture = True
                                # or if the substance texture import method failed, import all textures individually
                                if not self.substance_import_success:
                                    load_texture = True
                                # prop objects don't work with substance texture import currently
                                if self.character_type == "PROP":
                                    load_texture = True
                                tex_info = get_pbr_texture_info(mat_json, tex_id)
                                tex_path = convert_texture_path(tex_info, "Texture Path", self.folder)
                                if tex_path:
                                    # PNG diffuse maps with alpha channels don't fill in opacity correctly with substance import method
                                    if tex_id == "Base Color" and not has_opacity_map and os.path.splitext(tex_path)[-1].lower() == ".png":
                                        png_base_color = True
                                        load_texture = True
                                    elif tex_id == "Opacity" and png_base_color:
                                        load_texture = True
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
                                    if os.path.exists(tex_path) and os.path.isfile(tex_path):
                                        if load_texture:
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

        log(" - Custom shader import complete!")


    def import_substance_textures(self, char_json, material_component, mesh_names, obj_name_map):
        """Cache all PBR textures in a temporary location to load in all at once with:
           RLPy.RFileIO.LoadSubstancePainterTextures()
           This is *much* faster than loading these textures individually,
           but requires a particular directory and file naming structure.
        """
        global TEXTURE_MAPS, NUM_SUBSTANCE_MAPS

        log(" - Beginning substance texture import...")

        self.update_pbr_progress(1)
        self.substance_import_success = False

        # create temp folder for substance import (use the temporary files location from the RGlobal.GetPath)
        res = RLPy.RGlobal.GetPath(RLPy.EPathType_Temp, "")
        temp_path = res[1]
        # safest not to write temporary files in random locations...
        if not os.path.exists(temp_path):
            log(" - Unable to determine temporary file location, skipping substance import!")
            return

        temp_folder = os.path.join(temp_path, "CC3_BTP_Temp_" + random_string(8))
        log(" - Using temp folder: " + temp_folder)

        # delete if exists
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)
        # make a new temporary folder
        if not os.path.exists(temp_folder):
            os.mkdir(temp_folder)

        for mesh_name in mesh_names:

            mesh_name = fix_blender_name(mesh_name, self.option_mesh)
            obj_json = get_object_json(char_json, mesh_name, obj_name_map)

            if obj_json:

                mat_names = material_component.GetMaterialNames(mesh_name)

                if mesh_name.startswith("CC_Base_Body"):
                    # body is a special case, everything is stored in the first material name with incremental indicees

                    # create folder with first matertial name in each mesh
                    first_mat_in_mesh = mat_names[0]
                    mesh_folder = os.path.join(temp_folder, first_mat_in_mesh)
                    if not os.path.exists(mesh_folder):
                        os.mkdir(mesh_folder)

                    mat_index = 1001

                    for mat_name in mat_names:

                        mat_name = fix_blender_name(mat_name, self.option_mesh)
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
                                    tex_path = convert_texture_path(tex_info, "Texture Path", self.folder)
                                    if tex_path:
                                        tex_dir, tex_file = os.path.split(tex_path)
                                        tex_name, tex_type = os.path.splitext(tex_file)
                                        # copy valid texture files to the temporary texture cache
                                        if tex_name and os.path.exists(tex_path) and os.path.isfile(tex_path):
                                            substance_name = first_mat_in_mesh + "_" + str(mat_index) + "_" + substance_postfix + tex_type
                                            substance_path = os.path.normpath(os.path.join(mesh_folder, substance_name))
                                            shutil.copyfile("\\\\?\\" + tex_path, "\\\\?\\" + substance_path)

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

                            mat_name = fix_blender_name(mat_name, self.option_mesh)
                            mat_json = get_material_json(obj_json, mat_name, obj_name_map)

                            if mat_json:

                                # create folder with the matertial name
                                mesh_folder = os.path.join(temp_folder, mat_name)
                                if not os.path.exists(mesh_folder):
                                    os.mkdir(mesh_folder)

                                mat_index = 1001

                                # for each texture channel that can be imported with the substance texture method:
                                for tex_id in TEXTURE_MAPS.keys():
                                    is_substance = TEXTURE_MAPS[tex_id][1]
                                    if is_substance:
                                        tex_channel = TEXTURE_MAPS[tex_id][0]
                                        substance_postfix = TEXTURE_MAPS[tex_id][2]
                                        tex_info = get_pbr_texture_info(mat_json, tex_id)
                                        tex_path = convert_texture_path(tex_info, "Texture Path", self.folder)
                                        if tex_path:
                                            tex_dir, tex_file = os.path.split(tex_path)
                                            tex_name, tex_type = os.path.splitext(tex_file)
                                            # copy valid texture files to the temporary texture cache
                                            if tex_name and os.path.exists(tex_path) and os.path.isfile(tex_path):
                                                substance_name = mat_name + "_" + str(mat_index) + "_" + substance_postfix + tex_type
                                                substance_path = os.path.normpath(os.path.join(mesh_folder, substance_name))
                                                shutil.copyfile("\\\\?\\" + tex_path, "\\\\?\\" + substance_path)

                                        self.update_pbr_progress(2, pid)

                        else:
                            self.count_pbr += (NUM_SUBSTANCE_MAPS - 1)
                            self.update_pbr_progress(2, pid)

        self.update_pbr_progress(3)
        avatar = self.avatar

        # load all pbr textures in one go from the texture cache
        RLPy.RFileIO.LoadSubstancePainterTextures(avatar, temp_folder)
        self.substance_import_success = True

        log (" - Substance texture import successful!")
        log (" - Cleaning up temp folder: " + temp_folder)

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

            mesh_name = fix_blender_name(mesh_name, self.option_mesh)
            obj_json = get_object_json(char_json, mesh_name, obj_name_map)

            if obj_json:

                mat_names = material_component.GetMaterialNames(mesh_name)
                for mat_name in mat_names:

                    mat_name = fix_blender_name(mat_name, self.option_mesh)
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
                            #material_component.SetShader(mesh_name, mat_name, "PBR")
                            material_component.SetShader(mesh_name, mat_name, wanted_shader)

                        # Calculate stats
                        num_pbr += NUM_SUBSTANCE_MAPS
                        num_materials += 1

                        # Custom shader parameters
                        if self.option_parameters:
                            shader_params = material_component.GetShaderParameterNames(mesh_name, mat_name)
                            num_params += len(shader_params)

                        # Custom shader textures
                        if self.option_textures:
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

        do_events()


    def import_physics(self, char_json, obj_name_map):
        avatars = RLPy.RScene.GetAvatars()
        if avatars is None or len(avatars) == 0:
            return
        avatar = avatars[0]
        done = []
        physics_components = []

        log(f"Import Physics")

        # get physics components of all child objects
        child_objects = RLPy.RScene.FindChildObjects(avatar, RLPy.EObjectType_Avatar)
        for obj in child_objects:
            obj_physics_component = obj.GetPhysicsComponent()
            if obj_physics_component and obj_physics_component not in physics_components:
                physics_components.append(obj_physics_component)

        # get physics components of all accessory_objects
        accessories = avatar.GetAccessories()
        for obj in accessories:
            obj_physics_component = obj.GetPhysicsComponent()
            if obj_physics_component and obj_physics_component not in physics_components:
                physics_components.append(obj_physics_component)

        # get physics components of all hair meshes
        hairs = avatar.GetHairs()
        for hair in hairs:
            hair_physics_component = hair.GetPhysicsComponent()
            if hair_physics_component and hair_physics_component not in physics_components:
                physics_components.append(hair_physics_component)

        # process each physics component and reconstruct from the JSON data
        for physics_component in physics_components:

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
                                log(f"Object: {obj.GetName()}, Mesh: {mesh_name}, Material: {mat_name}")
                                mass = None
                                for json_param_name in physics_material_json.keys():
                                    phys_param_name = json_param_name.replace(' ', '').replace('_', '')
                                    param_value = get_physics_var(physics_material_json, json_param_name)
                                    #log(f"  Param: {phys_param_name} = {param_value}")

                                    if json_param_name == "Activate Physics": # activate physics
                                        physics_component.SetActivatePhysicsEnable(param_value)

                                    elif json_param_name == "Use Global Gravity": # global gravity
                                        physics_component.SetObjectGravityEnable(mesh_name, mat_name, param_value)

                                    elif json_param_name == "Weight Map Path": # weight map
                                        tex_path = convert_texture_path(physics_material_json, json_param_name, self.folder)
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


    def import_facial_profile(self):
        avatar = self.avatar
        json_data = self.json_data

        if "Facial_Profile" in json_data[self.name].keys():

            log("Importing Facial Profile")

            profile_json = json_data[self.name]["Facial_Profile"]
            facial_profile = avatar.GetFacialProfileComponent()

            if self.option_import_profile:
                # first reload the original profile of the character
                # TODO: this will not work if the topology has changed, does it fail gracefully?
                if os.path.exists(self.profile_path):
                    log(f"Restoring Facial Profile: {self.profile_path}")
                    facial_profile.LoadProfile(self.profile_path)

            if self.option_import_expressions:
                # then overwrite with the blend shapes in the fbx
                # any new/custom expression blend shapes must be added to json when exported from Blender
                # Blender must add viseme Blend shapes to json when exporting back
                sliders = []
                if "Categories" in profile_json.keys():
                    categories_json = profile_json["Categories"]
                    for category in categories_json.keys():
                        log(f"Gathering Expressions for Category: {category}")
                        sliders.extend(categories_json[category])
                log(f"Importing Facial Expressions:")
                facial_profile.ImportMorphs(self.path, True, sliders, "")


    def import_hik_profile(self):
        avatar = self.avatar

        if self.option_import_hik:
            if os.path.exists(self.hik_path):
                log(f"Restoring HIK Profile: {self.hik_path}")
                #avatar.LoadHikProfile(self.hik_path, True, True, True)
                avatar.DoCharacterization(self.hik_path, True, True, True)










#
# Class Exporter
#

class Exporter:
    path = "C:/folder/dummy.fbx"
    folder = "C:/folder"
    file = "dummy.fbx"
    key = "C:/folder/dummy.fbxkey"
    name = "dummy"
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
    check_hik_data = None
    check_profile_data = None
    check_remove_hidden = None
    option_bakehair = False
    option_bakeskin = False
    option_t_pose = False
    option_current_pose = False
    option_hik_data = False
    option_profile_data = True
    option_remove_hidden = False


    def __init__(self):
        log("================================================================")
        log("New character export, Fbx")

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


    def set_paths(self, file_path):
        self.path = file_path
        self.file = os.path.basename(self.path)
        self.folder = os.path.dirname(self.path)
        self.name = os.path.splitext(self.file)[0]
        self.key = os.path.join(self.folder, self.name + ".fbxkey")
        self.json_path = os.path.join(self.folder, self.name + ".json")
        self.hik_path = os.path.join(self.folder, self.name + ".3dxProfile")
        self.profile_path = os.path.join(self.folder, self.name + ".ccFacialProfile")


    def create_options_window(self):
        self.window_options = RLPy.RUi.CreateRDockWidget()
        self.window_options.SetWindowTitle(f"Blender Auto-setup Character Export ({VERSION}) - Options")

        dock = wrapInstance(int(self.window_options.GetWindow()), PySide2.QtWidgets.QDockWidget)
        dock.setFixedWidth(500)

        widget = PySide2.QtWidgets.QWidget()
        dock.setWidget(widget)

        layout = PySide2.QtWidgets.QVBoxLayout()
        widget.setLayout(layout)

        row = PySide2.QtWidgets.QHBoxLayout()
        layout.addLayout(row)

        button1 = PySide2.QtWidgets.QPushButton("Mesh Only", minimumHeight=24)
        button1.clicked.connect(self.preset_mesh_only)
        row.addWidget(button1)

        button2 = PySide2.QtWidgets.QPushButton("Current Pose", minimumHeight=24)
        button2.clicked.connect(self.preset_current_pose)
        row.addWidget(button2)

        button3 = PySide2.QtWidgets.QPushButton("Unity", minimumHeight=24)
        button3.clicked.connect(self.preset_unity)
        row.addWidget(button3)

        label_1 = PySide2.QtWidgets.QLabel()
        label_1.setText(f"Avatar Type: {self.avatar_type_string}")
        layout.addWidget(label_1)

        label_2 = PySide2.QtWidgets.QLabel()
        label_2.setText(f"Facial Profile: {self.profile_type_string}")
        layout.addWidget(label_2)

        layout.addSpacing(10)

        self.check_hik_data = None
        if self.avatar_type == RLPy.EAvatarType_NonStandard:
            self.check_hik_data = PySide2.QtWidgets.QCheckBox()
            self.check_hik_data.setText("Export HIK Profile")
            layout.addWidget(self.check_hik_data)

        self.check_profile_data = None
        if (self.avatar_type == RLPy.EAvatarType_NonStandard or
            self.avatar_type == RLPy.EAvatarType_Standard or
            self.avatar_type == RLPy.EAvatarType_StandardSeries):
            self.check_profile_data = PySide2.QtWidgets.QCheckBox()
            self.check_profile_data.setText("Export Facial Expression Profile")
            layout.addWidget(self.check_profile_data)

        layout.addSpacing(10)

        self.check_bakehair = PySide2.QtWidgets.QCheckBox()
        self.check_bakehair.setText("Bake Hair Diffuse and Specular")
        layout.addWidget(self.check_bakehair)

        self.check_bakeskin = PySide2.QtWidgets.QCheckBox()
        self.check_bakeskin.setText("Bake Skin Diffuse")
        layout.addWidget(self.check_bakeskin)

        self.check_t_pose = PySide2.QtWidgets.QCheckBox()
        self.check_t_pose.setText("Bindpose as T-Pose")
        layout.addWidget(self.check_t_pose)

        self.check_current_pose = PySide2.QtWidgets.QCheckBox()
        self.check_current_pose.setText("Current Pose")
        layout.addWidget(self.check_current_pose)

        self.check_remove_hidden = PySide2.QtWidgets.QCheckBox()
        self.check_remove_hidden.setText("Delete Hidden Faces")
        layout.addWidget(self.check_remove_hidden)

        layout.addSpacing(10)

        start_button = PySide2.QtWidgets.QPushButton("Export Character", minimumHeight=32)
        start_button.clicked.connect(self.do_export)
        layout.addWidget(start_button)

        self.preset_mesh_only()

        #self.window_options.RegisterEventCallback(self.dialog_callback)

        self.window_options.Show()


    def update_options(self):
        if self.check_hik_data: self.check_hik_data.setChecked(self.option_hik_data)
        if self.check_profile_data: self.check_profile_data.setChecked(self.option_profile_data)
        if self.check_bakehair: self.check_bakehair.setChecked(self.option_bakehair)
        if self.check_bakeskin: self.check_bakeskin.setChecked(self.option_bakeskin)
        if self.check_t_pose: self.check_t_pose.setChecked(self.option_t_pose)
        if self.check_current_pose: self.check_current_pose.setChecked(self.option_current_pose)
        if self.check_remove_hidden: self.check_remove_hidden.setChecked(self.option_remove_hidden)


    def fetch_options(self):
        if self.check_bakehair: self.option_bakehair = self.check_bakehair.isChecked()
        if self.check_bakeskin: self.option_bakeskin = self.check_bakeskin.isChecked()
        if self.check_current_pose: self.option_current_pose = self.check_current_pose.isChecked()
        if self.check_hik_data: self.option_hik_data = self.check_hik_data.isChecked()
        if self.check_profile_data: self.option_profile_data = self.check_profile_data.isChecked()
        if self.check_t_pose: self.option_t_pose = self.check_t_pose.isChecked()
        if self.check_remove_hidden: self.option_remove_hidden = self.check_remove_hidden.isChecked()


    def preset_mesh_only(self):
        self.option_bakehair = False
        self.option_bakeskin = False
        self.option_hik_data = True
        self.option_profile_data = True
        self.option_t_pose = False
        self.option_current_pose = False
        self.option_remove_hidden = False
        self.update_options()


    def preset_current_pose(self):
        self.option_bakehair = True
        self.option_bakeskin = True
        self.option_hik_data = True
        self.option_profile_data = False
        self.option_t_pose = False
        self.option_current_pose = True
        self.option_remove_hidden = False
        self.update_options()


    def preset_unity(self):
        self.option_bakehair = True
        self.option_bakeskin = True
        self.option_hik_data = False
        self.option_profile_data = False
        self.option_t_pose = True
        self.option_current_pose = False
        self.option_remove_hidden = True
        self.update_options()


    def close_options_window(self):
        if self.window_options:
            self.window_options.Close()
        self.window_options = None
        self.check_bakehair = None
        self.check_bakeskin = None
        self.check_current_pose = None
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
            log("Done!")
            clean_up_globals()
        else:
            log("Export Cancelled.")


    def export_fbx(self):
        avatar = self.avatar
        file_path = self.path

        log(f"Exporting FBX: {file_path}")

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
        else:
            export_fbx_setting.EnableExportMotion(False)

        result = RLPy.RFileIO.ExportFbxFile(avatar, file_path, export_fbx_setting)


    def export_extra_data(self):
        json_data = read_json(self.json_path)
        self.json_data = json_data
        json_data[self.name]["Avatar_Type"] = self.avatar_type_string

        log(f"Avatar Type: {self.avatar_type_string}")

        if self.option_hik_data:

            # Non-standard HIK profile
            if self.avatar_type == RLPy.EAvatarType_NonStandard:

                log(f"Exporting HIK profile: {self.hik_path}")

                self.avatar.SaveHikProfile(self.hik_path)
                json_data[self.name]["HIK"] = {}
                json_data[self.name]["HIK"]["Profile_Path"] = os.path.relpath(self.hik_path, self.folder)

        if self.option_profile_data:

            # Standard and Non-standard facial profiles
            if (self.avatar_type == RLPy.EAvatarType_NonStandard or
                self.avatar_type == RLPy.EAvatarType_Standard or
                self.avatar_type == RLPy.EAvatarType_StandardSeries):

                log(f"Exporting Facial Expression profile ({self.profile_type_string}): {self.profile_path}")

                facial_profile = self.avatar.GetFacialProfileComponent()
                facial_profile.SaveProfile(self.profile_path)
                json_data[self.name]["Facial_Profile"] = {}
                json_data[self.name]["Facial_Profile"]["Profile_Path"] = os.path.relpath(self.profile_path, self.folder)
                json_data[self.name]["Facial_Profile"]["Type"] = self.profile_type_string
                categories = facial_profile.GetExpressionCategoryNames()
                json_data[self.name]["Facial_Profile"]["Categories"] = {}
                for category in categories:
                    slider_names = facial_profile.GetExpressionSliderNames(category)
                    json_data[self.name]["Facial_Profile"]["Categories"][category] = slider_names


        self.export_physics(json_data)

        # Update JSON data
        log(f"Re-writing JSON data: {self.json_path}")

        write_json(json_data, self.json_path)


    def export_physics(self, json_data):

        done = []
        physics_components = []
        obj_name_map = get_json_mesh_name_map(self.avatar)
        char_json = get_character_json(json_data, self.name, self.name)

        log(f"Exporting Extra Physics Data")

        # get physics components of all child objects
        child_objects = RLPy.RScene.FindChildObjects(self.avatar, RLPy.EObjectType_Avatar)
        for obj in child_objects:
            obj_physics_component = obj.GetPhysicsComponent()
            if obj_physics_component and obj_physics_component not in physics_components:
                physics_components.append(obj_physics_component)

        # get physics components of all accessory_objects
        accessories = self.avatar.GetAccessories()
        for obj in accessories:
            obj_physics_component = obj.GetPhysicsComponent()
            if obj_physics_component and obj_physics_component not in physics_components:
                physics_components.append(obj_physics_component)

        # get physics components of all hair meshes
        hairs = self.avatar.GetHairs()
        for hair in hairs:
            hair_physics_component = hair.GetPhysicsComponent()
            if hair_physics_component and hair_physics_component not in physics_components:
                physics_components.append(hair_physics_component)

        # process each physics component and reconstruct from the JSON data
        for physics_component in physics_components:

            mesh_names = physics_component.GetSoftPhysicsMeshNameList()

            for mesh_name in mesh_names:

                if mesh_name not in done:
                    done.append(mesh_name)

                    safe_mesh_name = safe_export_name(mesh_name)

                    physics_object_json = get_physics_object_json(char_json, safe_mesh_name, obj_name_map)
                    if physics_object_json:

                        material_names = physics_component.GetSoftPhysicsMaterialNameList(mesh_name)

                        for mat_name in material_names:

                            safe_mat_name = safe_export_name(mat_name, True)

                            physics_material_json = get_physics_material_json(physics_object_json, safe_mat_name, obj_name_map)

                            if physics_material_json:

                                if "Weight Map Path" in physics_material_json.keys():
                                    if not physics_material_json["Weight Map Path"]:

                                        log(f"No weightmap texture path in physics component: {mesh_name} / {mat_name}")

                                        weight_map_path = os.path.join(self.folder, "textures", self.name, safe_mesh_name,
                                                                       safe_mesh_name, safe_mat_name,
                                                                       f"{safe_mat_name}_WeightMap.png")

                                        if not os.path.exists(weight_map_path):
                                            log(f"Weightmap missing, attempting to save: {weight_map_path}")
                                            physics_component.SavePhysicsSoftColthWeightMap(mesh_name, mat_name, weight_map_path)
                                        if os.path.exists(weight_map_path):
                                            physics_material_json["Weight Map Path"] = os.path.relpath(weight_map_path, self.folder)
                                            log(f"Adding weightmap path: {physics_material_json['Weight Map Path']}")
                                        else:
                                            log(f"Unable to save missing weightmap: {weight_map_path}")









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
    log(msg + ": " + str(duration) + " " + unit)


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
        return os.path.normpath(os.path.join(folder, rel_path))
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
                mapping[mesh_name] = safe_export_name(obj_name)
    return mapping


def fix_json_name(mat_name):
    """When matching *original* character object/material names to to imported json data from Blender,
       replace spaces and dots with underscores."""
    return mat_name.replace(' ','_').replace('.','_')


INVALID_EXPORT_CHARACTERS = "`¬!\"£$%^&*()+-=[]{}:@~;'#<>?,./\| "
DIGITS = "0123456789"


def is_invalid_export_name(name, is_material = False):
    for char in INVALID_EXPORT_CHARACTERS:
        if char in name:
            return True
    if is_material:
        if name[0] in DIGITS:
            return True
    return False


def safe_export_name(name, is_material = False):
    for char in INVALID_EXPORT_CHARACTERS:
        if char in name:
            name = name.replace(char, "_")
    if is_material:
        if name[0] in DIGITS:
            name = f"_{name}"
    return name


def get_json_path(fbx_path):
    fbx_file = os.path.basename(fbx_path)
    fbx_folder = os.path.dirname(fbx_path)
    fbx_name = os.path.splitext(fbx_file)[0]
    json_path = os.path.join(fbx_folder, fbx_name + ".json")
    return json_path


def get_hik_path(fbx_path):
    fbx_file = os.path.basename(fbx_path)
    fbx_folder = os.path.dirname(fbx_path)
    fbx_name = os.path.splitext(fbx_file)[0]
    hik_path = os.path.join(fbx_folder, fbx_name + ".3dxProfile")
    return hik_path


def read_json(json_path):
    try:
        if os.path.exists(json_path):
            log(" - Loading Json data: " + json_path)

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
            log(" - Json data successfully parsed!")
            return json_data

        log(" - No Json Data!")
        return None
    except:
        log(" - Error reading Json Data!")
        return None


def write_json(json_data, path):
    json_object = json.dumps(json_data, indent = 4)
    with open(path, "w") as write_file:
        write_file.write(json_object)


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
        log("Could not find character json: " + character_id)
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
    log("Could not find object json: " + mesh_name)
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
    #log("Could not find physics object json: " + mesh_name)
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
            mat_name_ext = safe_export_name(mat_name)
            # some materials are suffixed with _Transparency
            for material_name in physics_materials_json.keys():
                if material_name == mat_name_ext or material_name == mat_name_ext + "_Transparency":
                    return physics_materials_json[material_name]
    except:
        pass
    log("Could not find physics material json: " + mat_name)
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
            mat_name_ext = safe_export_name(mat_name)
            # some materials are suffixed with _Transparency
            for material_name in materials_json.keys():
                if material_name == mat_name_ext or material_name == mat_name_ext + "_Transparency":
                    return materials_json[material_name]
    except:
        pass
    log("Could not find material json: " + mat_name)
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
    menu_export()
    #menu_import()