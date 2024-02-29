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
import os, json
from . import utils
from enum import IntEnum


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


TEXTURE_MAPS = { # { "json_channel_name": [RL_Texture_Channel, is_Substance_Painter_Channel?, substance_channel_postfix], }
    "Base Color": [RLPy.EMaterialTextureChannel_Diffuse, True, "diffuse"],
    "Metallic": [RLPy.EMaterialTextureChannel_Metallic, True, "metallic"],
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


class CCMaterialJson():
    name: str = None
    mat_json: dict = None

    def __init__(self, mat_json, name):
        self.name = name
        self.mat_json = mat_json

    def json(self):
        return self.mat_json

    def get_base_channel(self, json_channel):
        try:
            return self.mat_json["Textures"][json_channel]
        except:
            return None

    def get_custom_channel(self, json_channel):
        try:
            return self.mat_json["Custom Shader"]["Image"][json_channel]
        except:
            return None

    def get_base_texture_file(self, json_channel):
        try:
            return self.mat_json["Textures"][json_channel]["Texture Path"]
        except:
            return None

    def get_base_texture_strength(self, json_channel):
        try:
            return self.mat_json["Textures"][json_channel]["Strength"] / 100
        except:
            return None

    def get_base_texture_offset_tiling(self, json_channel):
        try:
            offset = self.mat_json["Textures"][json_channel]["Offset"]
            tiling = self.mat_json["Textures"][json_channel]["Tiling"]
            offset_vector = RLPy.RVector2(float(offset[0]), float(offset[1]))
            tiling_vector = RLPy.RVector2(float(tiling[0]), float(tiling[1]))
            return offset_vector, tiling_vector
        except:
            return RLPy.RVector2(0.0, 0.0), RLPy.RVector2(1.0, 1.0)

    def get_tessellation(self):
        level = 0
        multiplier = 0
        threshold = 50
        try:
            tex_info = self.mat_json["Textures"]["Displacement"]
            if "Tessellation Level" in tex_info:
                level = tex_info["Tessellation Level"]
            if "Multiplier" in tex_info:
                multiplier = tex_info["Multiplier"]
            if "Gray-scale Base Value" in tex_info:
                threshold = tex_info["Gray-scale Base Value"]
        except:
            pass
        return level, multiplier, threshold

    def get_base_texture_rotation(self, json_channel):
        try:
            rotation = float(self.mat_json["Textures"][json_channel]["Rotation"])
            return rotation
        except:
            return 0.0

    def get_custom_texture_file(self, json_channel):
        try:
            return self.mat_json["Custom Shader"]["Image"][json_channel]["Texture Path"]
        except:
            return None

    def has_texture(self, json_channel):
        if self.get_base_texture_file(json_channel) or self.get_custom_texture_file(json_channel):
            return True
        else:
            return False

    def has_channel(self, json_channel):
        if self.get_base_channel(json_channel) or self.get_custom_channel(json_channel):
            return True
        else:
            return False

    def get_texture_file(self, json_channel):
        base_file = self.get_base_texture_file(json_channel)
        if base_file:
            return base_file
        custom_file = self.get_custom_texture_file(json_channel)
        if custom_file:
            return custom_file
        return None

    def get_texture_full_path(self, json_channel, folder):
        """Get the Json texture full path from the relative path from the folder
        """
        rel_path = self.get_texture_file(json_channel)
        if rel_path:
            if os.path.isabs(rel_path):
                return os.path.normpath(rel_path)
            return os.path.normpath(os.path.join(folder, rel_path))
        return None

    def get_shader(self):
        try:
            return self.mat_json["Custom Shader"]["Shader Name"]
        except:
            try:
                return self.mat_json["Material Type"]
            except:
                return "Pbr"

    def get_custom_shader_var(self, var_name, default = None):
        """Parameters in the custom shader variables section of the json:
           scalar: float (0-1)
           colors: rgb (0-1) converted from (0-255)
           """
        try:
            result = self.mat_json["Custom Shader"]["Variable"][var_name]
            return convert_from_json_param(var_name, result)
        except:
            return default

    def get_base_var(self, var_name, default = None):
        """Material parameters in the main materials section of the json:
           scalar: float (0-1)
           colors: rgb (0-1) converted from (0-255)
           """
        try:
            result = self.mat_json[var_name]
            return convert_from_json_param(var_name, result)
        except:
            return default

    def get_sss_var(self, var_name, default = None):
        """Subsurface parameters in the SSS section of the json:
           Falloff: rgb (0-1) converted from (0-255)
           scalar: float (0-1)
        """
        try:
            result = self.mat_json["Subsurface Scatter"][var_name]
            return convert_from_json_param(var_name, result)
        except:
            return default

    def get_diffuse_color(self):
        return self.get_base_var("Diffuse Color", [1,1,1])

    def get_ambient_color(self):
        return self.get_base_var("Ambient Color", [1,1,1])

    def get_specular_color(self):
        return self.get_base_var("Specular Color", [1,1,1])

    def get_self_illumination(self):
        return self.get_base_var("Self Illumination", 0)

    def get_opacity(self):
        return self.get_base_var("Opacity", 1)


class CCMeshJson():
    name: str = None
    mesh_json: dict = None
    materials: dict = None

    def __init__(self, mesh_json, name):
        self.name = name
        self.mesh_json = mesh_json
        self.parse()

    def parse(self):
        materials = {}
        materials_json = self.mesh_json["Materials"]
        for mat_name in materials_json:
            mat_json = materials_json[mat_name]
            materials[mat_name] = CCMaterialJson(mat_json, mat_name)
        self.materials = materials

    def json(self):
        return self.mesh_json

    def find_material_name(self, search_mat_name):
        try_names = set()
        try_names.add(search_mat_name)
        try_names.add(safe_export_name(search_mat_name))
        for mat_name in self.materials:
            if mat_name in try_names:
                return mat_name
            if mat_name.endswith("_Transparency"):
                trunc_mat_name = mat_name[:-13]
                if trunc_mat_name in try_names:
                    return mat_name
        return None

    def find_material(self, search_mat_name):
        mat_name = self.find_material_name(search_mat_name)
        cc_mat_json: CCMaterialJson = None
        if mat_name:
            cc_mat_json = self.materials[mat_name]
        return cc_mat_json


class CCPhysicsMaterialJson():
    name: str = None
    physics_mat_json: dict = None

    def __init__(self, physics_mat_json, name):
        self.name = name
        self.physics_mat_json = physics_mat_json

    def json(self):
        return self.physics_mat_json

    def get_var(self, var_name, default = None):
        try:
            result = self.physics_mat_json[var_name]
            return convert_phys_var(var_name, result)
        except:
            return default

    def get_params(self):
        params = []
        for name in self.physics_mat_json:
            params.append(name)
        return params


class CCPhysicsMeshJson():
    name: str = None
    physics_mesh_json: dict = None
    materials: dict = None

    def __init__(self, physics_mesh_json, name):
        self.name = name
        self.physics_mesh_json = physics_mesh_json
        self.parse()

    def parse(self):
        materials = {}
        physics_materials_json = self.physics_mesh_json["Materials"]
        for phys_mat_name in physics_materials_json:
            phys_mat_json = physics_materials_json[phys_mat_name]
            materials[phys_mat_name] = CCPhysicsMaterialJson(phys_mat_json, phys_mat_name)
        self.materials = materials

    def json(self):
        return self.physics_mesh_json

    def find_material_name(self, search_mat_name):
        try_names = set()
        try_names.add(search_mat_name)
        try_names.add(safe_export_name(search_mat_name))
        for mat_name in self.materials:
            if mat_name in try_names:
                return mat_name
            if mat_name.endswith("_Transparency"):
                trunc_mat_name = mat_name[:-13]
                if trunc_mat_name in try_names:
                    return mat_name
        return None

    def find_material(self, search_mat_name):
        mat_name = self.find_material_name(search_mat_name)
        cc_mat_json: CCPhysicsMaterialJson = None
        if mat_name:
            cc_mat_json = self.materials[mat_name]
        return cc_mat_json


class CCJsonData():

    json_path: str = ""
    fbx_path: str = ""
    file_name: str = ""
    character_id: str = ""
    json_data: dict = None

    meshes: dict = None
    physics_meshes: dict = None

    def __init__(self, json_path, fbx_path, character_id):
        self.json_path = json_path
        self.fbx_path = fbx_path
        self.character_id = character_id
        if self.read():
            self.parse()

    def read(self):
        try:
            if os.path.exists(self.json_path):
                utils.log(" - Loading Json data: " + self.json_path)

                # determine start of json text data
                file_bytes = open(self.json_path, "rb")
                bytes = file_bytes.read(3)
                file_bytes.close()
                start = 0
                # json files outputted from Visual Studio projects start with a byte mark order block (3 bytes EF BB BF)
                if bytes[0] == 0xEF and bytes[1] == 0xBB and bytes[2] == 0xBF:
                    start = 3

                # read json text
                file = open(self.json_path, "rt")
                file.seek(start)
                text_data = file.read()
                self.json_data = json.loads(text_data)
                file.close()
                utils.log(" - Json data successfully parsed!")
                return True

            else:
                utils.log(" - No Json Data!")
                return False

        except:
            utils.log(" - Error reading Json Data!")
            return False

    def write(self, path_override = None):
        path = path_override if path_override else self.json_path
        json_string = json.dumps(self.json_data, indent = 4)
        with open(path, "w") as write_file:
            write_file.write(json_string)

    def parse(self):
        meshes = {}
        physics_meshes = {}
        character_json = self.get_character_json()

        if character_json:

            meshes_json = get_json(character_json, "Meshes")
            if meshes_json:
                for mesh_name in meshes_json:
                    mesh_json = meshes_json[mesh_name]
                    meshes[mesh_name] = CCMeshJson(mesh_json, mesh_name)

            physics_meshes_json = get_json(character_json, "Physics/Soft Physics/Meshes")
            if physics_meshes_json:
                for phys_mesh_name in physics_meshes_json:
                    physics_mesh_json = physics_meshes_json[phys_mesh_name]
                    physics_meshes[phys_mesh_name] = CCPhysicsMeshJson(physics_mesh_json, phys_mesh_name)

        self.meshes = meshes
        self.physics_meshes = physics_meshes

    def json(self):
        return self.json_data

    def get_character_generation(self):
        try:
            return self.json_data[self.character_id]["Object"][self.character_id]["Generation"]
        except:
            return "Unknown"

    def get_character_type(self):
        character_type = "STANDARD"
        generation = self.get_character_generation().lower()
        if generation == "humanoid" or generation == "":
            character_type = "HUMANOID"
        elif generation == "actorcore" or generation == "actorbuild" or generation == "actorscan":
            character_type = "HUMANOID"
        elif generation == "gamebase" or generation == "accurig":
            character_type = "HUMANOID"
        elif generation == "creature":
            character_type = "CREATURE"
        elif generation is None or generation == "prop":
            character_type = "PROP"
        else:
            character_type = "NONE"
        return character_type

    def get_root_json(self):
        if not self.json_data:
            return None
        try:
            return self.json_data[self.character_id]
        except:
            return None

    def get_character_json(self):
        if not self.json_data:
            return None
        try:
            character_json = self.json_data[self.character_id]["Object"][self.character_id]
            return character_json
        except:
            utils.log("Could not find character json: " + self.character_id)
            return None

    def find_mesh_name(self, search_mesh_name, search_obj_name = None):
        try_names = set()
        try_names.add(search_mesh_name)
        try_names.add(safe_export_name(search_mesh_name))
        # accessories can cause mesh renames with _0 _1 _2 suffixes added
        if search_mesh_name[-1].isdigit() and search_mesh_name[-2] == "_":
            try_names.add(search_mesh_name[:-2])
        if search_obj_name:
            try_names.add(search_obj_name)
            try_names.add(safe_export_name(search_obj_name))
        for mesh_name in self.meshes:
            if mesh_name in try_names:
                return mesh_name
        return None

    def find_mesh(self, search_mesh_name, search_obj_name = None):
        mesh_name = self.find_mesh_name(search_mesh_name, search_obj_name)
        cc_mesh_json: CCMeshJson = None
        if mesh_name:
            cc_mesh_json = self.meshes[mesh_name]
        return cc_mesh_json

    def find_physics_mesh_name(self, search_mesh_name, search_obj_name = None):
        try_names = set()
        if search_mesh_name:
            try_names.add(search_mesh_name)
            try_names.add(safe_export_name(search_mesh_name))
        if search_obj_name:
            try_names.add(search_obj_name)
            try_names.add(safe_export_name(search_obj_name))
        for mesh_name in self.physics_meshes:
            if mesh_name in try_names:
                return mesh_name
        return None

    def find_physics_mesh(self, search_mesh_name, search_obj_name = None):
        mesh_name = self.find_physics_mesh_name(search_mesh_name, search_obj_name)
        cc_physics_mesh_json: CCPhysicsMeshJson = None
        if mesh_name:
            cc_physics_mesh_json = self.physics_meshes[mesh_name]
        return cc_physics_mesh_json


class CCMeshMaterial():
    actor = None
    actor_name: str = None
    obj = None
    obj_name: str = None
    mesh_name: str = None
    mat_name: str = None
    duf_material: dict = None
    duf_mesh: dict = None
    mat_component: RLPy.RIMaterialComponent = None
    data: dict = None
    substance_index = 1001
    json_data: CCJsonData = None
    json_mesh_name: str = None
    json_mat_name: str = None
    mesh_json: CCMeshJson = None
    mat_json: CCMaterialJson = None
    physx_mesh_json: CCPhysicsMeshJson = None
    physx_mat_json: CCPhysicsMaterialJson = None
    physx_object = None
    physx_component: RLPy.RIPhysicsComponent = None

    def __init__(self, actor = None, obj = None,
                 mesh_name = None, mat_name = None,
                 duf_mesh = None, duf_material = None,
                 physx_object = None, cc_json_data = None):
        self.actor = actor
        self.obj = obj
        self.actor_name = actor.GetName()
        self.obj_name = obj.GetName()
        self.mesh_name = mesh_name
        self.mat_name = mat_name
        self.actor = actor
        self.physx_object = physx_object
        self.duf_mesh = duf_mesh
        self.duf_material = duf_material
        self.json_data = cc_json_data
        if self.json_data:
            self.find_json_data()

    def material_component(self):
        if not self.mat_component and self.actor:
            self.mat_component = self.actor.GetMaterialComponent()
        return self.mat_component

    def physics_component(self):
        if not self.physx_component and self.physx_object:
            self.physx_component = self.physx_object.GetPhysicsComponent()
        return self.physx_component

    def has_json(self):
        return self.json_data and self.mesh_json and self.mat_json

    def has_physics_json(self):
        return self.json_data and self.physx_mesh_json and self.physx_mat_json

    def set_duf_mesh_material(self, duf_mesh, duf_material):
        self.duf_mesh = duf_mesh
        self.duf_material = duf_material

    def change_material_name(self, name):
        MC = self.material_component()
        MC.SetMaterialName(self.mesh_name, self.mat_name, name)

    def set_diffuse(self, rgb):
        material_component = self.material_component()
        if material_component:
            c = rgb_color(rgb)
            material_component.AddDiffuseKey(key_zero(), self.mesh_name, self.mat_name, c)

    def set_ambient(self, rgb):
        material_component = self.material_component()
        if material_component:
            c = rgb_color(rgb)
            material_component.AddAmbientKey(key_zero(), self.mesh_name, self.mat_name, c)

    def set_specular(self, rgb):
        material_component = self.material_component()
        if material_component:
            c = rgb_color(rgb)
            material_component.AddSpecularKey(key_zero(), self.mesh_name, self.mat_name, c)

    def set_opacity(self, opacity):
        material_component = self.material_component()
        if material_component:
            material_component.AddOpacityKey(key_zero(), self.mesh_name, self.mat_name, opacity*100)

    def set_glossiness(self, glossiness):
        material_component = self.material_component()
        if material_component:
            material_component.AddGlossinessKey(key_zero(), self.mesh_name, self.mat_name, glossiness*100)

    def set_self_illumination(self, glow):
        material_component = self.material_component()
        if material_component:
            material_component.AddSelfIlluminationKey(key_zero(), self.mesh_name, self.mat_name, glow*100)

    def remove_channel_image(self, channel):
        material_component = self.material_component()
        if material_component:
            material_component.RemoveMaterialTexture(self.mesh_name, self.mat_name, channel)

    def set_attribute(self, attrib, value):
        material_component = self.material_component()
        if material_component:
            material_component.SetAttributeValue(self.mesh_name, self.mat_name, attrib, value)

    def load_material(self, material_path):
        material_component = self.material_component()
        if material_component:
            material_component.LoadMaterial(self.mesh_name, self.mat_name, material_path)

    def get_shader(self):
        material_component = self.material_component()
        if material_component:
            shader_full_name = material_component.GetShader(self.mesh_name, self.mat_name)
            for shader in SHADER_MAPS:
                if SHADER_MAPS[shader] == shader_full_name:
                    return shader

    def set_shader(self, shader):
        material_component = self.material_component()
        if material_component:
            if shader in SHADER_MAPS:
                shader_full_name = SHADER_MAPS[shader]
                material_component.SetShader(self.mesh_name, self.mat_name, shader_full_name)

    def load_channel_image(self, channel, file):
        material_component = self.material_component()
        if material_component:
            material_component.LoadImageToTexture(self.mesh_name, self.mat_name, channel, file)

    def load_shader_texture(self, shader_texture, file):
        material_component = self.material_component()
        if material_component:
            material_component.LoadShaderTexture(self.mesh_name, self.mat_name, shader_texture, file)

    def channel_has_image(self, channel):
        material_component = self.material_component()
        if material_component:
            res = material_component.GetImageColor(self.mesh_name, self.mat_name, channel)
            if len(res) == 7:
                return True
        return False

    def set_uv_mapping(self, channel, offset_vector, tiling_vector, rotation):
        material_component = self.material_component()
        if material_component:
            material_component.AddUvDataKey(key_zero(), self.mesh_name, self.mat_name, channel, offset_vector, tiling_vector, rotation)

    def set_channel_texture_weight(self, channel, weight):
        material_component = self.material_component()
        if material_component:
            if self.channel_has_image(channel):
                material_component.AddTextureWeightKey(key_zero(), self.mesh_name, self.mat_name, channel, weight)

    def set_channel_image_color(self, channel, softness, H,S,B,C,c,y,m):
        material_component = self.material_component()
        if material_component:
            softness = utils.clamp(softness, 0.0, 10.0)
            H = utils.clamp(H, -100, 100)
            S = utils.clamp(S, -100, 100)
            B = utils.clamp(B, -100, 100)
            C = utils.clamp(C, -100, 100)
            c = utils.clamp(c, -100, 100)
            y = utils.clamp(y, -100, 100)
            m = utils.clamp(m, -100, 100)
            hsbc = RLPy.RVector4(H, S, B, C)
            cym = RLPy.RVector3(c, y, m)
            res = material_component.GetImageColor(self.mesh_name, self.mat_name, channel)
            if res == (-999):
                return
            if res != (H,S,B,C,c,y,m):
                utils.log_info(f" - Changing channel HSBC: {(H,S,B,C,c,y,m)}")
                material_component.SetImageColor(self.mesh_name, self.mat_name, channel, softness, hsbc, cym)

    def set_shader_parameter(self, parameter, value):
        """Expects scalars as float (0-1) and colors and RGB lists (0-255)"""
        material_component = self.material_component()
        if material_component:
            parameter_names = material_component.GetShaderParameterNames(self.mesh_name, self.mat_name)
            #if parameter in parameter_names:
            value = shader_value(value)
            material_component.SetShaderParameter(self.mesh_name, self.mat_name, parameter, value)
            #else:
            #    utils.log_info(f"Parameter: {parameter} does not exist in shader!")

    def get_shader_parameter(self, parameter):
        material_component = self.material_component()
        if material_component:
            parameter_names = material_component.GetShaderParameterNames(self.mesh_name, self.mat_name)
            if parameter in parameter_names:
                value = material_component.GetShaderParameter(self.mesh_name, self.mat_name, parameter)
                return un_shader_value(value)
            else:
                utils.log_info(f"Parameter: {parameter} does not exist in shader!")
                return None

    def get_shader_parameter_names(self):
        material_component = self.material_component()
        if material_component:
            names = material_component.GetShaderParameterNames(self.mesh_name, self.mat_name)
            return names
        return None

    def get_shader_texture_names(self):
        material_component = self.material_component()
        if material_component:
            names = material_component.GetShaderTextureNames(self.mesh_name, self.mat_name)
            return names
        return None

    def skin_template_textures_path(self, channel):
        template_folder = f"$/Others/Skin Textures/SkinBase/RL_CC3_Plus/{self.mat_name}"
        content = find_content_in_folder(template_folder, channel)
        return content

    def temp_image_path(self, channel_name, ext):
        path = temp_files_path()
        image_name = self.mesh_material_channel_image_name(channel_name, ext)
        image_path = os.path.join(path, image_name)
        return image_path

    def mesh_material_channel_image_name(self, channel_name, ext):
        image_name = f"{self.mesh_name}_{self.mat_name}_{channel_name}.{ext}"
        return image_name

    def set_data(self, name, value):
        if not self.data:
            self.data = {}
        self.data[name] = value

    def get_data(self, name, default=None):
        if self.data:
            if name in self.data:
                return self.data[name]
        return default

    def increment_substance_index(self):
        index = self.substance_index
        self.substance_index += 1
        return index

    def reset_substance_index(self):
        self.substance_index = 1001

    def set_physics_param(self, json_param_name, param_value, folder = None):
        PC = self.physics_component()
        phys_param_name = json_param_name.replace(' ', '').replace('_', '')

        if json_param_name == "Activate Physics":
            PC.SetActivatePhysicsEnable(param_value)

        elif json_param_name == "Use Global Gravity":
            PC.SetObjectGravityEnable(self.mesh_name, self.mat_name, param_value)

        elif json_param_name == "Weight Map Path":
            if folder:
                tex_path = get_full_path(param_value, folder)
                if tex_path:
                    PC.SetPhysicsSoftColthWeightMap(self.mesh_name, self.mat_name, tex_path)

        elif json_param_name == "Soft Vs Rigid Collision" or json_param_name == "Self Collision":
            PC.SetSoftPhysXCollisionEnable(self.mesh_name, self.mat_name, phys_param_name, param_value)

        elif json_param_name == "Soft Vs Rigid Collision_Margin" or json_param_name == "Self Collision Margin":
            PC.SetSoftPhysXCollisionValue(self.mesh_name, self.mat_name, phys_param_name, param_value)

        elif json_param_name == "Mass":
            PC.SetSoftPhysXProperty(self.mesh_name, self.mat_name, "Mass", param_value)

        else:
            PC.SetSoftPhysXProperty(self.mesh_name, self.mat_name, phys_param_name, float(param_value))

    def find_json_data(self):
        if self.json_data:
            self.mesh_json = self.json_data.find_mesh(self.mesh_name, self.obj_name)
            if self.mesh_json:
                self.json_mesh_name = self.mesh_json.name
                self.mat_json = self.mesh_json.find_material(self.mat_name)
                if self.mat_json:
                    self.json_mat_name = self.mat_json.name
                if self.physx_object:
                    self.physx_mesh_json = self.json_data.find_physics_mesh(self.json_mesh_name)
                    if self.physx_mesh_json:
                        self.physx_mat_json = self.physx_mesh_json.find_material(self.json_mat_name)


def get_selected_mesh_materials(exclude_mesh_names=None, exclude_material_names=None,
                                mesh_filter=None, material_filter=None, json_data=None):

    selected_objects = RLPy.RScene.GetSelectedObjects()

    mesh_materials = []

    obj: RLPy.RIObject
    for obj in selected_objects:
        actor = find_parent_avatar_or_prop(obj)
        obj_name = obj.GetName()
        if actor:
            material_component = actor.GetMaterialComponent()
            mesh_names = obj.GetMeshNames()

            for mesh_name in mesh_names:

                if exclude_mesh_names and mesh_name in exclude_mesh_names:
                    continue

                if mesh_filter and mesh_filter(mesh_name):
                    continue

                obj = find_actor_object(obj, mesh_name)

                material_names = material_component.GetMaterialNames(mesh_name)
                for mat_name in material_names:

                    if exclude_material_names and mat_name in exclude_material_names:
                        continue

                    if material_filter and material_filter(mesh_name):
                        continue

                    physics_object, physics_component = get_actor_physics_object(actor, mesh_name, mat_name)

                    M = CCMeshMaterial(actor=actor, obj=obj, mesh_name=mesh_name, mat_name=mat_name,
                                       physx_object=physics_object, cc_json_data=json_data)

                    mesh_materials.append(M)

    return mesh_materials


def get_avatar_mesh_materials(avatar, exclude_mesh_names=None, exclude_material_names=None,
                              mesh_filter=None, material_filter=None, json_data=None):

    mesh_materials = []

    if avatar:

        material_component = avatar.GetMaterialComponent()
        mesh_names = list(avatar.GetMeshNames())

        # put the body first
        if "CC_Base_Body" in mesh_names:
            mesh_names.remove("CC_Base_Body")
            mesh_names.insert(0, "CC_Base_Body")

        for mesh_name in mesh_names:

            if exclude_mesh_names and mesh_name in exclude_mesh_names:
                continue

            if mesh_filter and mesh_filter(mesh_name):
                continue

            obj = find_actor_object(avatar, mesh_name)
            if obj:

                utils.log_info(f"Actor Object: {obj.GetName()}")
                utils.log_indent()

                material_names = material_component.GetMaterialNames(mesh_name)
                for mat_name in material_names:

                    if exclude_material_names and mat_name in exclude_material_names:
                        continue

                    if material_filter and material_filter(mesh_name):
                        continue

                    utils.log_info(f"Mesh/Material: {mesh_name} / {mat_name}")
                    utils.log_indent()

                    physics_object, physics_component = get_actor_physics_object(avatar, mesh_name, mat_name)

                    M = CCMeshMaterial(actor=avatar, obj=obj, mesh_name=mesh_name, mat_name=mat_name,
                                       physx_object=physics_object, cc_json_data=json_data)

                    mesh_materials.append(M)

                    utils.log_recess()

                utils.log_recess()

            else:

                utils.log_error(f"Could not find actor object for: {mesh_name}")

    return mesh_materials


def is_cc():
    return RLPy.RApplication.GetProductName() == "Character Creator"


def is_iclone():
    return RLPy.RApplication.GetProductName() == "iClone"


def find_child_obj(obj, search):
    if obj == search:
        return True
    else:
        children = obj.GetChildren()
        for child in children:
            if find_child_obj(child, search):
                return True
    return False


def get_parent_avatar(obj):
    avatars = RLPy.RScene.GetAvatars()
    for avatar in avatars:
        if find_child_obj(avatar, obj):
            return avatar
    return avatars[0]


def get_first_avatar():
    avatars = RLPy.RScene.GetAvatars()
    avatar: RLPy.RIAvatar = None
    if avatars:
        avatar = avatars[0]
    return avatar


def get_selected_avatars():
    objects = get_selected_actor_objects()
    all_avatars = RLPy.RScene.GetAvatars()
    avatars = []
    for obj in objects:
        if obj in all_avatars and obj not in avatars:
            avatars.append(obj)
    return avatars


def get_selected_actor_objects():
    selected = RLPy.RScene.GetSelectedObjects()
    actor_objects = []
    for obj in selected:
        actor_object = find_parent_avatar_or_prop(obj)
        if actor_object and actor_object not in actor_objects:
            actor_objects.append(actor_object)
    return actor_objects


def find_content_in_folder(folder, search):
    content_files = RLPy.RApplication.GetContentFilesInFolder(folder)
    for content in content_files:
        folder, name = os.path.split(content)
        file, ext = os.path.splitext(name)
        if file.lower() == search.lower():
            return content
    return ""


def custom_content_path():
    res = RLPy.RGlobal.GetPath(RLPy.EPathType_CustomContent, "")
    return res[1]


def custom_morph_path():
    res = RLPy.RGlobal.GetPath(RLPy.EPathType_CustomContent, "")
    return res[1]


def temp_files_path(sub_path=None, create=False):
    res = RLPy.RGlobal.GetPath(RLPy.EPathType_Temp, "")
    path = res[1]
    if sub_path:
        path = os.path.join(path, sub_path)
        if create:
            os.makedirs(path, exist_ok=True)
    return path


def model_type_and_key_path(file_path):
    dir, file = os.path.split(file_path)
    name, ext = os.path.splitext(file)
    key_path = None
    model_type = "NONE"
    if ext.lower() == ".fbx":
        model_type = "FBX"
        key_path = os.path.join(dir, name + ".fbxkey")
    elif ext.lower() == ".obj":
        model_type = "OBJ"
        key_path = os.path.join(dir, name + ".ObjKey")
    return model_type, key_path


def model_file_has_key(file_path):
    model_type, key_path = model_type_and_key_path(file_path)
    if model_type != "NONE" and key_path and os.path.exists(key_path):
        return True
    return False


def key_zero():
    key_zero = RLPy.RKey()
    key_zero.SetTime(RLPy.RTime.FromValue(0))
    return key_zero


def time_zero():
    time_zero = RLPy.RTime.FromValue(0)
    return time_zero


def shader_value(var_value):
    if type(var_value) == tuple or type(var_value) == list:
        return var_value
    else:
        return [var_value]


def un_shader_value(var_value):
    if type(var_value) == tuple or type(var_value) == list:
        if len(var_value) == 1:
            return var_value[0]
        else:
            return var_value
    else:
        return var_value


def get_selected_mesh_names():
    selected = RLPy.RScene.GetSelectedObjects()
    obj: RLPy.RIObject
    mesh_names = []
    for obj in selected:
        mesh_names.extend(obj.GetMeshNames())
    return mesh_names


def find_node(node : RLPy.RINode, id):
    if node.GetID() == id:
        return node
    children = node.GetChildren()
    for child in children:
        found = find_node(child, id)
        if found:
            return found
    return None


def find_parent_avatar_or_prop(obj : RLPy.RIObject):
    avatars = RLPy.RScene.GetAvatars()
    props = RLPy.RScene.GetProps()
    root : RLPy.RINode = RLPy.RScene.GetRootNode()
    node = find_node(root, obj.GetID())
    while node:
        node_id = node.GetID()
        for avatar in avatars:
            if avatar.GetID() == node_id:
                return avatar
        for prop in props:
            if prop.GetID() == node_id:
                return prop
        node = node.GetParent()
    return None


def add_data_block(obj: RLPy.RIObject, block_name):
    data_block: RLPy.RDataBlock = None
    if obj:
        data_block = obj.GetDataBlock(block_name)
        if data_block:
            return data_block
        data_block = RLPy.RDataBlock.Create([])
        obj.SetDataBlock(block_name, data_block)
        return data_block
    return None


def has_attr(data_block: RLPy.RDataBlock, attr_name: str):
    attr: RLPy.RAttribute = None
    if data_block:
        attribs = data_block.GetAttributes()
        for attr in attribs:
            if attr.GetName() == attr_name:
                return True
    return False


def add_attr(data_block: RLPy.RDataBlock, attr_name: str, attr_type, attr_flags):
    attr: RLPy.RAttribute = None
    if data_block:
        attribs = data_block.GetAttributes()
        for attr in attribs:
            if attr.GetName() == attr_name:
                return attr
        attr = RLPy.RAttribute(attr_name, attr_type, attr_flags)
        data_block.AddAttribute(attr)
        return attr
    return None


def get_data_block_str(obj: RLPy.RIObject, block_name, attr_name):
    data_block: RLPy.RDataBlock = obj.GetDataBlock(block_name)
    if data_block and has_attr(data_block, attr_name):
        return data_block.GetData(attr_name).ToString()
    return None


def has_link_id(obj: RLPy.RIObject):
    if obj:
        link_id = get_data_block_str(obj, "DataLink", "LinkID")
        if link_id:
            return True
    return False


def get_link_id(obj: RLPy.RIObject, add_if_missing=False):
    if obj:
        link_id = get_data_block_str(obj, "DataLink", "LinkID")
        if not link_id:
            link_id = str(obj.GetID())
            if add_if_missing:
                set_link_id(obj, link_id)
        return link_id
    return None


def set_link_id(obj: RLPy.RIObject, link_id):
    if obj:
        data_block: RLPy.RDataBlock = add_data_block(obj, "DataLink")
        add_attr(data_block, "LinkID", RLPy.EAttributeType_String, RLPy.EAttributeFlag_Default)
        value = RLPy.RVariant(str(link_id))
        data_block.SetData("LinkID", value)


def find_object_by_link_id(link_id):
    objects = RLPy.RScene.FindObjects(RLPy.EObjectType_Avatar |
                                      RLPy.EObjectType_Prop |
                                      RLPy.EObjectType_Light |
                                      RLPy.EObjectType_Camera)
    for obj in objects:
        if get_link_id(obj) == link_id:
            return obj
    return None


def find_linked_objects(object: RLPy.RIObject):
    objects = RLPy.RScene.FindObjects(RLPy.EObjectType_Avatar |
                                      RLPy.EObjectType_Prop |
                                      RLPy.EObjectType_Light |
                                      RLPy.EObjectType_Camera)
    linked_objects = []
    for obj in objects:
        linked_object = obj.GetLinkedObject()
        if linked_object and linked_object == object:
            linked_objects.append(obj)
    return linked_objects


def find_attached_objects(object: RLPy.RIObject):
    attached = RLPy.RScene.FindChildObjects(object,
                                            RLPy.EObjectType_Light |
                                            RLPy.EObjectType_Camera |
                                            RLPy.EObjectType_Prop |
                                            RLPy.EObjectType_Cloth |
                                            RLPy.EObjectType_Accessory |
                                            RLPy.EObjectType_Hair)
    return attached


def find_object_by_id(object_id):
    avatar = find_avatar_by_id(object_id)
    if avatar:
        return avatar
    prop = find_prop_by_id(object_id)
    if prop:
        return prop
    return None


def find_avatar_by_id(avatar_id):
    avatars = RLPy.RScene.GetAvatars()
    for avatar in avatars:
        if avatar.GetID() == avatar_id:
            return avatar
    return None


def find_prop_by_id(prop_id):
    props = RLPy.RScene.GetProps()
    for prop in props:
        if prop.GetID() == prop_id:
            return prop
    return None


def print_nodes(node, level=0):
    node_id = node.GetID()
    node_name = node.GetName()
    print(("  "*level) + f"node: {node_name} ({node_id})")
    children = node.GetChildren()
    for child in children:
        print_nodes(child, level+1)
    return None


def print_note_tree(obj):
    root : RLPy.RINode = RLPy.RScene.GetRootNode()
    node = find_node(root, obj.GetID())
    print_nodes(node)


IGNORE_NODES = ["RL_BoneRoot", "IKSolverDummy", "NodeForExpressionLookAtSolver"]

def get_actor_objects(actor):
    objects = []
    if actor and type(actor) is RLPy.RIAvatar:
        avatar: RLPy.RIAvatar = actor
        objects.extend(avatar.GetClothes())
        objects.extend(avatar.GetAccessories())
        objects.extend(avatar.GetHairs())
        child_objects = RLPy.RScene.FindChildObjects(actor, RLPy.EObjectType_Avatar)
        for obj in child_objects:
            name = obj.GetName()
            if name not in IGNORE_NODES and obj not in objects:
                objects.append(obj)
        if avatar.GetAvatarType() != RLPy.EAvatarType_Standard:
            objects.append(avatar)

    elif actor and type(actor) is RLPy.RIProp:
        child_objects = RLPy.RScene.FindChildObjects(actor, RLPy.EObjectType_Avatar)
        for obj in child_objects:
            name = obj.GetName()
            if name not in IGNORE_NODES and obj not in objects:
                objects.append(obj)
    else:
        print("Other")
        objects.append(actor)

    return objects


def find_actor_object(actor, mesh_name):
    objects = get_actor_objects(actor)
    for obj in objects:
        mesh_names = obj.GetMeshNames()
        if mesh_name in mesh_names:
            return obj
    return None


def get_actor_physics_object(actor, mesh_name, mat_name):
    objects = get_actor_objects(actor)
    for obj in objects:
        if (type(obj) == RLPy.RIAccessory or
            type(obj) == RLPy.RIHair or
            type(obj) == RLPy.RIAvatar):
            physics_component = obj.GetPhysicsComponent()
            if physics_component:
                if mesh_name in physics_component.GetSoftPhysicsMeshNameList():
                    if mat_name in physics_component.GetSoftPhysicsMaterialNameList(mesh_name):
                        return obj, physics_component
    return None, None


def get_actor_physics_components(actor: RLPy.RIAvatar):
    physics_components = []
    objects = get_actor_objects(actor)
    for obj in objects:
        if (type(obj) == RLPy.RIAccessory or
            type(obj) == RLPy.RIHair or
            type(obj) == RLPy.RIAvatar):
            obj_physics_component = obj.GetPhysicsComponent()
            if obj_physics_component and obj_physics_component not in physics_components:
                physics_components.append(obj_physics_component)
    return physics_components


INVALID_EXPORT_CHARACTERS: str = "`¬!\"£$%^&*()+-=[]{}:@~;'#<>?,./\| "
DIGITS: str = "0123456789"

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


def get_full_path(rel_path, folder):
    if rel_path and folder:
        if os.path.isabs(rel_path):
            return os.path.normpath(rel_path)
        return os.path.normpath(os.path.join(folder, rel_path))
    return None


def RGB_color(RGB):
    c = RLPy.RRgb()
    c.From(RGB[0], RGB[1], RGB[2])
    return c


def rgb_color(rgb):
    c = RLPy.RRgb(rgb[0], rgb[1], rgb[2])
    return c


def array_to_vector3(arr):
    return RLPy.RVector3(arr[0], arr[1], arr[2])


def array_to_vector4(arr):
    return RLPy.RVector4(arr[0], arr[1], arr[2], arr[3])


def array_to_quaternion(arr):
    v = array_to_vector4(arr)
    return RLPy.RQuaternion(v)


def get_material_resource(file_name):
    return utils.get_resource_path("materials", file_name)


def convert_from_json_param(var_name, var_value):
    if type(var_value) == tuple or type(var_value) == list:
        if len(var_value) == 3:
            return utils.RGB_to_rgb(var_value)
        else:
            return var_value
    else:
        return var_value


def get_json(json_data, path: str):
    keys = path.split("/")
    for key in keys:
        if key in json_data:
            json_data = json_data[key]
        else:
            return None
    return json_data


def convert_phys_var(var_name, var_value):
    if type(var_value) == tuple or type(var_value) == list:
        if var_name == "Inertia":
            return var_value[0]
    return var_value


def get_changed_json(json_item):
    if json_item and "Has Changed" in json_item:
        return json_item["Has Changed"]
    return False


def fix_json_name(mat_name):
    """When matching *original* character object/material names to to imported json data from Blender,
       replace spaces and dots with underscores."""
    return mat_name.replace(' ','_').replace('.','_')


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


