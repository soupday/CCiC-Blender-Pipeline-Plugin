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
import os, json, math
from . import utils, vars
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


class SkinBoneType(IntEnum):
    BONE    = 0
    OBJECT  = 1
    PIVOT   = 2
    NODE    = 3
    MESH    = 4


TEXTURE_MAPS = { # { "json_channel_name": [RL_Texture_Channel, is_Substance_Painter_Channel?, substance_channel_postfix], }
    "Base Color": [EMaterialTextureChannel_Diffuse, True, "diffuse"],
    "Metallic": [EMaterialTextureChannel_Metallic, True, "metallic"],
    "Specular": [EMaterialTextureChannel_Specular, True, "specular"],
    "Roughness": [EMaterialTextureChannel_Shininess, True, "roughness"],
    "Glow": [EMaterialTextureChannel_Glow, True, "glow"],
    "Displacement": [EMaterialTextureChannel_Displacement, True, "displacement"],
    "Opacity": [EMaterialTextureChannel_Opacity, True, "opacity"],
    "Blend": [EMaterialTextureChannel_DiffuseBlend, False, ""],
    "Reflection": [EMaterialTextureChannel_Reflection, False, ""],
    "Refraction": [EMaterialTextureChannel_Refraction, False, ""],
    "Cube": [EMaterialTextureChannel_Cube, False, ""],
    "AO": [EMaterialTextureChannel_AmbientOcclusion, True, "ao"],
    "Bump": [EMaterialTextureChannel_Bump, True, "bump"],
    "Normal": [EMaterialTextureChannel_Normal, True, "normal"],
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
            offset_vector = RVector2(float(offset[0]), float(offset[1]))
            tiling_vector = RVector2(float(tiling[0]), float(tiling[1]))
            return offset_vector, tiling_vector
        except:
            return RVector2(0.0, 0.0), RVector2(1.0, 1.0)

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

    def find_material_name(self, search_mat_name, exact=False):
        try_names = set()
        try_names.add(search_mat_name)
        try_names.add(safe_export_name(search_mat_name))
        if search_mat_name.endswith("_Transparency"):
            try_names.add(search_mat_name[:-13])
        for json_mat_name in self.materials:
            trunc_mat_name = None
            if json_mat_name.endswith("_Transparency"):
                trunc_mat_name = json_mat_name[:-13]
            if json_mat_name in try_names or (trunc_mat_name and trunc_mat_name in try_names):
                return json_mat_name
        if exact:
            return None
        # try a partial match, but only if there is only one result
        partial_mat_name = None
        partial_mat_count = 0
        for json_mat_name in self.materials:
            trunc_mat_name = None
            if json_mat_name.endswith("_Transparency"):
                trunc_mat_name = json_mat_name[:-13]
            for try_name in try_names:
                if try_name in json_mat_name or (trunc_mat_name and try_name in trunc_mat_name):
                    partial_mat_count += 1
                    if not partial_mat_name:
                        partial_mat_name = json_mat_name
                    # only count 1 match per try set
                    break
        if partial_mat_count == 1:
            return partial_mat_name
        return None

    def find_material(self, search_mat_name, exact=False):
        mat_name = self.find_material_name(search_mat_name, exact=exact)
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

    def find_material_name(self, search_mat_name, exact=False):
        try_names = set()
        try_names.add(search_mat_name)
        try_names.add(safe_export_name(search_mat_name))
        if search_mat_name.endswith("_Transparency"):
            try_names.add(search_mat_name[:-13])
        for json_mat_name in self.materials:
            trunc_mat_name = None
            if json_mat_name.endswith("_Transparency"):
                trunc_mat_name = json_mat_name[:-13]
            if json_mat_name in try_names or (trunc_mat_name and trunc_mat_name in try_names):
                return json_mat_name
        if exact:
            return None
        # try a partial match, but only if there is only one result
        partial_mat_name = None
        partial_mat_count = 0
        for json_mat_name in self.materials:
            trunc_mat_name = None
            if json_mat_name.endswith("_Transparency"):
                trunc_mat_name = json_mat_name[:-13]
            for try_name in try_names:
                if try_name in json_mat_name or (trunc_mat_name and try_name in trunc_mat_name):
                    partial_mat_count += 1
                    if not partial_mat_name:
                        partial_mat_name = json_mat_name
                    # only count 1 match per try set
                    break
        if partial_mat_count == 1:
            return partial_mat_name
        return None

    def find_material(self, search_mat_name, exact=False):
        mat_name = self.find_material_name(search_mat_name, exact=exact)
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
    valid: bool = False

    meshes: dict = None
    physics_meshes: dict = None

    def __init__(self, json_path, fbx_path, character_id):
        self.json_path = json_path
        self.fbx_path = fbx_path
        self.character_id = character_id
        if self.read():
            self.parse()

    def read(self):
        self.valid = False
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
                self.valid = True
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

    def set_character_generation(self, generation_type):
        try:
            if generation_type in vars.AVATAR_GENERATIONS:
                generation = vars.AVATAR_GENERATIONS[generation_type]
                self.json_data[self.character_id]["Object"][self.character_id]["Generation"] = generation
                return generation
        except:
            pass
        return ""

    def get_avatar_type(self):
        try:
            return self.json_data[self.character_id]["Avatar_Type"]
        except:
            return "NONE"

    def set_avatar_type(self, avatar_type):
        try:
            self.json_data[self.character_id]["Avatar_Type"] = avatar_type
        except:
            utils.log_error("Unable to set json avatar type!")

    def get_link_id(self):
        try:
            return self.json_data[self.character_id]["Link_ID"]
        except:
            return None

    def set_link_id(self, link_id):
        try:
            self.json_data[self.character_id]["Link_ID"] = link_id
        except:
            pass

    def get_character_type(self):
        generation = self.get_character_generation().lower()
        avatar_type = self.get_avatar_type()

        for character_type in vars.CHARACTER_TYPES:
            generations = [ g.lower() for g in vars.CHARACTER_TYPES[character_type]["generations"] ]
            avatar_types = vars.CHARACTER_TYPES[character_type]["avatar_types"]
            if generation in generations:
                return character_type
            if avatar_type in avatar_types:
                return character_type

        character_type = "STANDARD"
        if generation == "humanoid" or generation == "" or generation == "rigify" or generation == "rigify+":
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

    def find_source_mesh_name(self, imported_mesh_name, imported_obj_name, rl_meshes, exact=False):
        try_names = set()
        try_names.add(imported_mesh_name)
        try_names.add(safe_export_name(imported_mesh_name))
        # accessories can cause mesh renames with _0 _1 _2 suffixes added
        if imported_mesh_name[-1].isdigit() and imported_mesh_name[-2] == "_":
            try_names.add(imported_mesh_name[:-2])
        if imported_obj_name:
            try_names.add(imported_obj_name)
            try_names.add(safe_export_name(imported_obj_name))
        for mesh_name in rl_meshes:
            if mesh_name in try_names:
                return mesh_name
        if exact:
            return None
        # try a partial match, but only if there is only one result
        partial_mesh_match = None
        partial_mesh_count = 0
        for mesh_name in rl_meshes:
            for try_name in try_names:
                if try_name in mesh_name:
                    partial_mesh_count += 1
                    if not partial_mesh_match:
                        partial_mesh_match = mesh_name
                    # only count 1 match per try set
                    break
        if partial_mesh_count == 1:
            return partial_mesh_match
        return None

    def find_mesh(self, search_mesh_name, search_obj_name=None, exact=False):
        mesh_name = self.find_source_mesh_name(search_mesh_name, search_obj_name, self.meshes, exact=exact)
        cc_mesh_json: CCMeshJson = None
        if mesh_name:
            cc_mesh_json = self.meshes[mesh_name]
        return cc_mesh_json

    def find_physics_mesh_name(self, search_mesh_name, search_obj_name, rl_meshes, exact=False):
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
        if exact:
            return None
        # try a partial match, but only if there is only one result
        partial_mesh_match = None
        partial_mesh_count = 0
        for mesh_name in rl_meshes:
            for try_name in try_names:
                if try_name in mesh_name:
                    partial_mesh_count += 1
                    if not partial_mesh_match:
                        partial_mesh_match = mesh_name
                    # only count 1 match per try set
                    break
        if partial_mesh_count == 1:
            return partial_mesh_match
        return None

    def find_physics_mesh(self, search_mesh_name, search_obj_name=None, exact=False):
        mesh_name = self.find_physics_mesh_name(search_mesh_name, search_obj_name, self.physics_meshes, exact=exact)
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
    mat_component: RIMaterialComponent = None
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
    physx_component: RIPhysicsComponent = None

    def __init__(self, actor = None, obj = None,
                 mesh_name = None, mat_name = None,
                 duf_mesh = None, duf_material = None,
                 physx_object = None, cc_json_data = None,
                 exact=False):
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
            self.find_json_data(exact)

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
                result = material_component.SetShader(self.mesh_name, self.mat_name, shader_full_name)
                return (result == RStatus.Success)
        return False

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
            hsbc = RVector4(H, S, B, C)
            cym = RVector3(c, y, m)
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

    def find_json_data(self, exact):
        if self.json_data:
            self.mesh_json = self.json_data.find_mesh(self.mesh_name, self.obj_name, exact=exact)
            if self.mesh_json:
                self.json_mesh_name = self.mesh_json.name
                self.mat_json = self.mesh_json.find_material(self.mat_name, exact=exact)
                if self.mat_json:
                    self.json_mat_name = self.mat_json.name
                else:
                    utils.log_warn(f"Material JSON {self.mat_name} not found!")
                if self.physx_object:
                    self.physx_mesh_json = self.json_data.find_physics_mesh(self.json_mesh_name, exact=exact)
                    if self.physx_mesh_json:
                        self.physx_mat_json = self.physx_mesh_json.find_material(self.json_mat_name, exact=exact)
            else:
                utils.log_warn(f"Mesh JSON {self.obj_name}/{self.mesh_name} not found!")






def get_selected_mesh_materials(exclude_mesh_names=None, exclude_material_names=None,
                                mesh_filter=None, material_filter=None, json_data=None):

    selected_objects = RScene.GetSelectedObjects()

    mesh_materials = []

    obj: RIObject
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

                    physics_object = get_actor_physics_object(actor, mesh_name, mat_name)

                    M = CCMeshMaterial(actor=actor, obj=obj, mesh_name=mesh_name, mat_name=mat_name,
                                       physx_object=physics_object, cc_json_data=json_data)

                    mesh_materials.append(M)

    return mesh_materials


def get_avatar_mesh_materials(avatar, exclude_mesh_names=None, exclude_material_names=None,
                              mesh_filter=None, material_filter=None, json_data=None,
                              exact=False):

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

                utils.log_info(f"Actor Object: {obj.GetName()} ({mesh_name})")
                utils.log_indent()

                material_names = material_component.GetMaterialNames(mesh_name)
                for mat_name in material_names:

                    if exclude_material_names and mat_name in exclude_material_names:
                        continue

                    if material_filter and material_filter(mesh_name):
                        continue

                    utils.log_info(f"Mesh / Material: {mesh_name} / {mat_name}")
                    utils.log_indent()

                    physics_object = get_actor_physics_object(avatar, mesh_name, mat_name)

                    M = CCMeshMaterial(actor=avatar, obj=obj, mesh_name=mesh_name, mat_name=mat_name,
                                       physx_object=physics_object, cc_json_data=json_data,
                                       exact=exact)

                    mesh_materials.append(M)

                    utils.log_recess()

                utils.log_recess()

            else:

                utils.log_error(f"Could not find actor object for: {mesh_name}")

    return mesh_materials


def is_cc():
    return RApplication.GetProductName() == "Character Creator"


def is_iclone():
    return RApplication.GetProductName() == "iClone"


def find_actor_source_meshes(imported_mesh_name, imported_obj_name, actor: RIAvatar):
        objects = get_actor_objects(actor)
        try_names = set()
        try_names.add(imported_mesh_name)
        try_names.add(safe_export_name(imported_mesh_name))

        # accessories can cause mesh renames with _0 _1 _2 suffixes added
        if imported_mesh_name[-1].isdigit() and imported_mesh_name[-2] == "_":
            try_names.add(imported_mesh_name[:-2])
        safe_imported_obj_name = imported_obj_name
        if imported_obj_name:
            safe_imported_obj_name = safe_export_name(imported_obj_name)
            try_names.add(imported_obj_name)
            try_names.add(safe_imported_obj_name)

        #utils.log_info(f"Try Names: {try_names}")

        # first try to match mesh names directly
        for obj in objects:
            obj_name = obj.GetName()
            rl_meshes = obj.GetMeshNames()
            if rl_meshes:
                #utils.log_info(f"Object: {obj.GetName()}, Mesh Names: {rl_meshes}")
                for mesh_name in rl_meshes:
                    if mesh_name in try_names:
                        return [mesh_name]

        # then try to match object names
        if imported_obj_name:
            for obj in objects:
                obj_name = obj.GetName()
                if obj_name == imported_obj_name or obj_name == safe_imported_obj_name:
                    return obj.GetMeshNames()

        # try a partial match, but only if there is only one result
        partial_mesh_match = None
        partial_mesh_count = 0
        for obj in objects:
            obj_name = obj.GetName()
            rl_meshes = obj.GetMeshNames()
            for mesh_name in rl_meshes:
                for try_name in try_names:
                    if try_name in mesh_name:
                        partial_mesh_count += 1
                        if not partial_mesh_match:
                            partial_mesh_match = mesh_name
                        # only count 1 match per try set
                        break
        if partial_mesh_count == 1:
            return [partial_mesh_match]

        # try a partial match on the object names
        partial_obj_match = None
        partial_obj_count = 0
        for obj in objects:
            obj_name = obj.GetName()
            for imported_obj_name in obj_name or safe_imported_obj_name in obj_name:
                partial_obj_count += 1
                if not partial_obj_match:
                    partial_obj_match = obj
        if partial_obj_count == 1:
            return partial_obj_match.GetMeshNames()

        return []


def get_first_avatar():
    avatars = RScene.GetAvatars()
    avatar: RIAvatar = None
    if avatars:
        avatar = avatars[0]
    return avatar


def get_selected_avatars():
    objects = get_selected_actor_objects()
    all_avatars = RScene.GetAvatars()
    avatars = []
    for obj in objects:
        if obj in all_avatars and obj not in avatars:
            avatars.append(obj)
    return avatars


def get_selected_actor_objects():
    selected = RScene.GetSelectedObjects()
    actor_objects = []
    for obj in selected:
        actor_object = find_parent_avatar_or_prop(obj)
        if actor_object and actor_object not in actor_objects:
            actor_objects.append(actor_object)
    return actor_objects


def find_content_in_folder(folder, search):
    content_files = RApplication.GetContentFilesInFolder(folder)
    for content in content_files:
        folder, name = os.path.split(content)
        file, ext = os.path.splitext(name)
        if file.lower() == search.lower():
            return content
    return ""


def custom_content_path():
    res = RGlobal.GetPath(EPathType_CustomContent, "")
    return res[1]


def custom_morph_path():
    res = RGlobal.GetPath(EPathType_CustomContent, "")
    return res[1]


def user_files_path(sub_path=None, create=False):
    path = os.path.normpath(os.path.expanduser("~/Documents/Reallusion/"))
    if sub_path:
        path = os.path.join(path, sub_path)
    if create:
        os.makedirs(path, exist_ok=True)
    return path


def temp_files_path(sub_path=None, create=False):
    res = RGlobal.GetPath(EPathType_Temp, "")
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
    key_zero = RKey()
    key_zero.SetTime(RTime.FromValue(0))
    return key_zero


def time_zero():
    time_zero = RTime.FromValue(0)
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
    selected = RScene.GetSelectedObjects()
    obj: RIObject
    mesh_names = []
    for obj in selected:
        mesh_names.extend(obj.GetMeshNames())
    return mesh_names


def find_node(node: RINode, id):
    if node.GetID() == id:
        return node
    children = node.GetChildren()
    for child in children:
        found = find_node(child, id)
        if found:
            return found
    return None


def find_parent_avatar_or_prop(obj: RIObject):
    avatars = RScene.GetAvatars()
    props = RScene.GetProps()
    md_props = RScene.GetMDProps()
    root: RINode = RScene.GetRootNode()
    node = find_node(root, obj.GetID())
    while node:
        node_id = node.GetID()
        for avatar in avatars:
            if avatar.GetID() == node_id:
                return avatar
        for prop in props:
            if prop.GetID() == node_id:
                return prop
        for prop in md_props:
            if prop.GetID() == node_id:
                return prop
        node = node.GetParent()
    return None


def find_parent_avatar(obj: RIObject):
    avatars = RScene.GetAvatars()
    root: RINode = RScene.GetRootNode()
    node = find_node(root, obj.GetID())
    while node:
        node_id = node.GetID()
        for avatar in avatars:
            if avatar.GetID() == node_id:
                return avatar
        node = node.GetParent()
    return None


def add_data_block(obj: RIObject, block_name):
    data_block: RDataBlock = None
    if obj:
        data_block = obj.GetDataBlock(block_name)
        if data_block:
            return data_block
        data_block = RDataBlock.Create([])
        obj.SetDataBlock(block_name, data_block)
        return data_block
    return None


def has_attr(data_block: RDataBlock, attr_name: str):
    attr: RAttribute = None
    if data_block:
        attribs = data_block.GetAttributes()
        for attr in attribs:
            if attr.GetName() == attr_name:
                return True
    return False


def add_attr(data_block: RDataBlock, attr_name: str, attr_type, attr_flags):
    attr: RAttribute = None
    if data_block:
        attribs = data_block.GetAttributes()
        for attr in attribs:
            if attr.GetName() == attr_name:
                return attr
        attr = RAttribute(attr_name, attr_type, attr_flags)
        data_block.AddAttribute(attr)
        return attr
    return None


def get_data_block_str(obj: RIObject, block_name, attr_name):
    data_block: RDataBlock = obj.GetDataBlock(block_name)
    if data_block and has_attr(data_block, attr_name):
        return data_block.GetData(attr_name).ToString()
    return None


def has_link_id(obj: RIObject):
    if obj:
        link_id = get_data_block_str(obj, "DataLink", "LinkID")
        if link_id:
            return True
    return False


def get_link_id(obj: RIObject, add_if_missing=False):
    if obj:
        link_id = get_data_block_str(obj, "DataLink", "LinkID")
        if not link_id:
            link_id = str(obj.GetID())
            if add_if_missing:
                set_link_id(obj, link_id)
        return link_id
    return None


def set_link_id(obj: RIObject, link_id):
    if obj:
        data_block: RDataBlock = add_data_block(obj, "DataLink")
        add_attr(data_block, "LinkID", EAttributeType_String, EAttributeFlag_Default)
        value = RVariant(str(link_id))
        data_block.SetData("LinkID", value)


def find_object_by_link_id(link_id):
    objects = RScene.FindObjects(EObjectType_Avatar |
                                      EObjectType_Prop |
                                      EObjectType_Light |
                                      EObjectType_Camera)
    for obj in objects:
        if get_link_id(obj) == link_id:
            return obj
    return None


def find_object_by_name_and_type(search_name, search_type=None):
    objects = RScene.FindObjects(EObjectType_Avatar |
                                      EObjectType_Prop |
                                      EObjectType_Light |
                                      EObjectType_Camera)
    for obj in objects:
        if obj.GetName() == search_name:
            if search_type:
                if get_object_type(obj) == search_type:
                    return obj
            else:
                return obj


def get_avatar_type_name(avatar: RIAvatar):
    avatar_type = avatar.GetAvatarType()
    avatar_type_string = "None"
    if avatar_type in vars.AVATAR_TYPES.keys():
        avatar_type_string = vars.AVATAR_TYPES[avatar_type]
    return avatar_type_string


def get_avatar_profile_name(avatar: RIAvatar):
    avatar_type = avatar.GetAvatarType()
    profile_type = EFacialProfile__None
    profile_type_string = "None"
    if (avatar_type == EAvatarType_NonStandard or
        avatar_type == EAvatarType_Standard or
        avatar_type == EAvatarType_StandardSeries):
        facial_profile = avatar.GetFacialProfileComponent()
        profile_type = facial_profile.GetProfileType()
        if profile_type in vars.FACIAL_PROFILES.keys():
            profile_type_string = vars.FACIAL_PROFILES[profile_type]
    return profile_type_string


def is_avatar_non_standard(avatar: RIAvatar):
    avatar_generation = avatar.GetGeneration()
    avatar_type = avatar.GetAvatarType()
    if (avatar_generation == EAvatarGeneration_ActorBuild or
        avatar_generation == EAvatarGeneration_ActorScan or
        avatar_generation == EAvatarGeneration_CC_Game_Base_Multi or
        avatar_generation == EAvatarGeneration_CC_Game_Base_One or
        avatar_generation == EAvatarGeneration_AccuRig or
        avatar_generation == EAvatarType_NonStandard or
        (avatar_generation == EAvatarGeneration__None and
         avatar_type == EAvatarType_StandardSeries) or
        (avatar_generation == EAvatarGeneration__None and
         avatar_type == EAvatarType_Standard)):
            return True
    return False


def is_avatar_standard(avatar: RIAvatar):
    avatar_type = avatar.GetAvatarType()
    if (avatar_type == EAvatarType_Standard or
        avatar_type == EAvatarType_StandardSeries):
        return True


def get_object_type(obj):
    T = type(obj)
    if T is RIAvatar or T is RILightAvatar:
        return "AVATAR"
    elif T is RIProp or T is RIMDProp:
        return "PROP"
    elif T is RIAccessory:
        return "ACCESSORY"
    elif T is RILight:
        return "LIGHT"
    elif T is RICamera:
        return "CAMERA"
    elif T is RIHair:
        return "HAIR"
    return "NONE"


def find_linked_objects(object: RIObject):
    objects = RScene.FindObjects(EObjectType_Avatar |
                                      EObjectType_Prop |
                                      EObjectType_Light |
                                      EObjectType_Camera)
    linked_objects = []
    for obj in objects:
        linked_object = obj.GetLinkedObject()
        if linked_object and linked_object == object:
            linked_objects.append(obj)
    return linked_objects


def find_attached_objects(object: RIObject):
    attached = RScene.FindChildObjects(object,
                                            EObjectType_Light |
                                            EObjectType_Camera |
                                            EObjectType_Prop |
                                            EObjectType_Cloth |
                                            EObjectType_Accessory |
                                            EObjectType_Hair)
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
    avatars = RScene.GetAvatars()
    for avatar in avatars:
        if avatar.GetID() == avatar_id:
            return avatar
    return None


def find_prop_by_id(prop_id):
    props = RScene.GetProps()
    md_props = RScene.GetMDProps()
    for prop in props:
        if prop.GetID() == prop_id:
            return prop
    for prop in md_props:
        if prop.GetID() == prop_id:
            return prop
    return None


def deduplicate_scene():
    objects = RScene.FindObjects(EObjectType_Avatar |
                                 EObjectType_Prop |
                                 EObjectType_Light |
                                 EObjectType_Camera)
    names = {}
    ids_done = []
    for obj in objects:
        obj_id = obj.GetID()
        if obj_id not in ids_done:
            ids_done.append(obj_id)
            name = obj.GetName()
            if name not in names:
                names[name] = 1
            else:
                print(f"Deduplicating sub-item name: {name}")
                count = names[name]
                names[name] += 1
                obj.SetName(f"{name}_{count:03d}")


def get_mesh_skin_bones(obj, skin_bones):
    sub_objects = [obj]
    sub_objects.extend(RScene.FindChildObjects(obj, EObjectType_Prop | EObjectType_Accessory))
    sub_map = { p.GetID(): p for p in sub_objects }
    mesh_bones = []
    for bone in skin_bones:
        bone_id = bone.GetID()
        if bone_id in sub_map and bone.GetName() != "_Object_Pivot_Node_":
            mesh_bones.append(bone)
    return mesh_bones


def remove_pivot_mesh_bones(skin_bones):
    to_remove = []
    for i, bone in enumerate(skin_bones):
        if i > 1:
            if skin_bones[i-1].GetName() == "_Object_Pivot_Node_":
                if skin_bones[i-2].GetName() == bone.GetName():
                    # only remove leaf bones
                    if not bone.GetChildren():
                        to_remove.append(bone)
    for bone in to_remove:
        skin_bones.remove(bone)
    return skin_bones


def get_extended_skin_bones(obj, skin_bones: list=None, ignore_pivot=False):
    """Fetches the bones from the object and all child sub-objects in no particular order"""
    child_objects: list = RScene.FindChildObjects(obj, EObjectType_Prop | EObjectType_Accessory)
    objects = [obj]
    objects.extend(child_objects)
    skin_bones = []
    for obj in objects:
        SC = obj.GetSkeletonComponent()
        skin_bones = SC.GetSkinBones()
        for bone in skin_bones:
            if bone not in skin_bones:
                skin_bones.append(bone)
    return skin_bones


def get_extended_skin_bones_tree(prop: RIObject):

    child_objects: list = RScene.FindChildObjects(prop, EObjectType_Prop | EObjectType_Accessory)
    objects = [prop]
    objects.extend(child_objects)

    bone_defs = {}
    defs = []
    for obj in objects:
        SC = obj.GetSkeletonComponent()
        root = SC.GetRootBone()
        skin_bones = SC.GetSkinBones()
        if skin_bones:
            num_bones = 0
            for bone in skin_bones:
                if bone.GetName():
                    num_bones += 1
            bone: RINode
            if num_bones > 0:
                link_id = get_link_id(obj, add_if_missing=True)
            for bone in skin_bones:
                if bone.GetID() not in bone_defs:
                    bone_name = bone.GetName()
                    if bone_name:
                        bone_def = {
                            "bone": bone,
                            "object": obj,
                            "root": bone.GetID() == root.GetID(),
                            "name": bone_name,
                            "children": [],
                        }
                        bone_defs[bone.GetID()] = bone_def
                        defs.append(bone_def)

    for bone_def in defs:
        bone = bone_def["bone"]
        bone_name = bone_def["name"]
        parent = bone.GetParent()
        if parent:
            if parent.GetID() in bone_defs:
                parent_def = bone_defs[parent.GetID()]
                parent_def["children"].append(bone_def)

    if defs:
        return defs[0]
    else:
        return None


def extract_mesh_bones_from_tree(bone_def, mesh_bones=None):
    if mesh_bones is None:
        mesh_bones = []
    to_remove = []
    for child_def in bone_def["children"]:
        if child_def["children"]:
            extract_mesh_bones_from_tree(child_def, mesh_bones)
        else:
            bone = child_def["bone"]
            mesh_bones.append(bone)
            to_remove.append(child_def)
    for child_def in to_remove:
        bone_def["children"].remove(child_def)
    return mesh_bones


def extract_skin_bones_from_tree(bone_def: dict, skin_bones=None, mesh_bones=None, extract_mesh=True):
    if skin_bones is None:
        skin_bones = []
    if mesh_bones is None:
        mesh_bones = []
    to_remove = []
    child_bone: RINode = bone_def["bone"]
    skin_bones.append(child_bone)
    children = child_bone.GetChildren()
    # go through bones in the correct order
    #       very important to recreate bone structure in Blender,
    #       as it is impossible to match duplicate bone names
    #       unless the order and hierarchy of the bones matches the
    #       exported armature *exactly*.
    done = []
    for child in children:
        for child_def in bone_def["children"]:
            child_bone = child_def["bone"]
            if child_def not in done and child_bone.GetID() == child.GetID():
                if extract_mesh and not child_def["children"]:
                    mesh_bones.append(child_bone)
                    to_remove.append(child_def)
                extract_skin_bones_from_tree(child_def, skin_bones)
                done.append(child_def)
                break
        # bones not explicitly children of the node are sub props
        for child_def in bone_def["children"]:
            child_bone = child_def["bone"]
            if child_def not in done:
                if extract_mesh and not child_def["children"]:
                    mesh_bones.append(child_bone)
                    to_remove.append(child_def)
                extract_skin_bones_from_tree(child_def, skin_bones)
                done.append(child_def)
    for child_def in to_remove:
        bone_def["children"].remove(child_def)
    return skin_bones, mesh_bones


def rl_export_bone_name(bone_name):
    bone_name = bone_name.replace(' ', '_')
    bone_name = bone_name.replace('(', '_')
    bone_name = bone_name.replace(')', '_')
    bone_name = bone_name.replace('&', '_')
    return bone_name


def extract_root_bones_from_tree(bone_def: dict, root_bones=None, names=None):
    if root_bones is None:
        root_bones = []
    if names is None:
        names = {}
    bone: RINode = bone_def["bone"]
    name: str = bone_def["name"]
    if name not in names:
        names[name] = 0
    count = names[name]
    names[name] += 1
    if bone_def["root"]:
        export_name = rl_export_bone_name(name)
        blender_name = f"{export_name}.{count:03d}" if count > 0 else export_name
        obj = bone_def["object"]
        link_id = get_link_id(obj, add_if_missing=True)
        root_bones.append({
            "Name": blender_name,
            "Original Name": name,
            "Object": obj.GetName(),
            "Type": get_object_type(obj),
            "Link_ID": link_id,
        })
    children = bone.GetChildren()
    # go through bones in the correct order
    #       very important to recreate bone structure in Blender,
    #       as it is impossible to match duplicate bone names
    #       unless the order and hierarchy of the bones matches the
    #       exported armature *exactly*.
    done = []
    for child in children:
        for child_def in bone_def["children"]:
            child_bone = child_def["bone"]
            if child_def not in done and child_bone.GetID() == child.GetID():
                extract_root_bones_from_tree(child_def, root_bones, names)
                done.append(child_def)
                break
        # bones not explicitly children of the node are sub props
        for child_def in bone_def["children"]:
            if child_def not in done:
                extract_root_bones_from_tree(child_def, root_bones, names)
                done.append(child_def)
    return root_bones


def get_extended_skin_bones_tree_debug(prop: RIObject):

    child_objects: list = RScene.FindChildObjects(prop, EObjectType_Prop | EObjectType_Accessory)
    objects = [prop]
    objects.extend(child_objects)

    bone_defs = {}
    defs = []
    for obj in objects:
        T: RTransform = obj.WorldTransform()
        t: RVector3 = T.T()
        r: RQuaternion = T.R()
        s: RVector3 = T.S()
        print(obj.GetName())
        print(f"loc: {[t.x, t.y, t.z]}")
        print(f"rot: {[r.x, r.y, r.z, r.w]}")
        print(f"sca: {[s.x, s.y, s.z]}")
        SC = obj.GetSkeletonComponent()
        root = SC.GetRootBone()
        skin_bones = SC.GetSkinBones()
        if skin_bones:
            num_bones = 0
            for bone in skin_bones:
                if bone.GetName():
                    num_bones += 1
            bone: RINode
            if num_bones > 0:
                link_id = get_link_id(obj, add_if_missing=True)
            for bone in skin_bones:
                if bone.GetID() not in bone_defs:
                    bone_name = bone.GetName()
                    T: RTransform = bone.WorldTransform()
                    t: RVector3 = T.T()
                    r: RQuaternion = T.R()
                    s: RVector3 = T.S()
                    if bone_name:
                        bone_def = {
                            "bone": bone,
                            "object": obj.GetName(),
                            "root": bone.GetID() == root.GetID(),
                            "name": bone_name,
                            "loc": [t.x, t.y, t.z],
                            "rot": [r.x, r.y, r.z, r.w],
                            "sca": [s.x, s.y, s.z],
                            "children": [],
                        }
                        bone_defs[bone.GetID()] = bone_def
                        defs.append(bone_def)
    for bone_def in defs:
        bone = bone_def["bone"]
        bone_name = bone_def["name"]
        parent = bone.GetParent()
        if parent:
            if parent.GetID() in bone_defs:
                parent_def = bone_defs[parent.GetID()]
                parent_def["children"].append(bone_def)
    for bone_def in defs:
        del(bone_def["bone"])
    if defs:
        return defs[0]
    else:
        return None


def print_nodes(node, level=0):
    node_id = node.GetID()
    node_name = node.GetName()
    utils.log_always(("  "*level) + f"node: {node_name} ({node_id})")
    children = node.GetChildren()
    for child in children:
        print_nodes(child, level+1)
    return None


def print_node_tree(obj):
    root : RINode = RScene.GetRootNode()
    node = find_node(root, obj.GetID())
    print_nodes(node)


def is_prop(obj):
    T = type(obj)
    return (T is RIProp or T is RIMDProp)


def is_avatar(obj):
    T = type(obj)
    return (T is RIAvatar or T is RILightAvatar)


IGNORE_NODES = ["RL_BoneRoot", "IKSolverDummy", "NodeForExpressionLookAtSolver"]

def get_actor_objects(actor):
    objects = []
    T = type(actor)
    if actor and (T is RIAvatar or T is RILightAvatar):
        avatar: RIAvatar = actor
        objects.extend(avatar.GetClothes())
        objects.extend(avatar.GetAccessories())
        objects.extend(avatar.GetHairs())
        child_objects = RScene.FindChildObjects(actor, EObjectType_Avatar)
        for obj in child_objects:
            name = obj.GetName()
            if name not in IGNORE_NODES and obj not in objects:
                objects.append(obj)
        if avatar.GetAvatarType() != EAvatarType_Standard:
            objects.append(avatar)

    elif actor and (T is RIProp or T is RIMDProp):
        child_objects = RScene.FindChildObjects(actor, EObjectType_Avatar)
        for obj in child_objects:
            name = obj.GetName()
            if name not in IGNORE_NODES and obj not in objects:
                objects.append(obj)
    else:
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
        if (type(obj) == RIAccessory or
            type(obj) == RIHair or
            type(obj) == RIAvatar or
            type(obj) == RILightAvatar or
            type(obj) == RICloth):
            try:
                physics_component = obj.GetPhysicsComponent()
            except:
                physics_component = None
            if physics_component:
                if mesh_name in physics_component.GetSoftPhysicsMeshNameList():
                    if mat_name in physics_component.GetSoftPhysicsMaterialNameList(mesh_name):
                        return obj
    return None


def get_actor_physics_components(actor: RIAvatar):
    physics_components = []
    objects = get_actor_objects(actor)
    for obj in objects:
        if (type(obj) == RIAccessory or
            type(obj) == RIHair or
            type(obj) == RIAvatar or
            type(obj) == RILightAvatar or
            type(obj) == RICloth):
            try:
                obj_physics_component = obj.GetPhysicsComponent()
            except:
                obj_physics_component = None
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
    c = RRgb()
    c.From(RGB[0], RGB[1], RGB[2])
    return c


def rgb_color(rgb):
    c = RRgb(rgb[0], rgb[1], rgb[2])
    return c


def array_to_vector3(arr):
    return RVector3(arr[0], arr[1], arr[2])


def array_to_vector4(arr):
    return RVector4(arr[0], arr[1], arr[2], arr[3])


def array_to_quaternion(arr):
    v = array_to_vector4(arr)
    return RQuaternion(v)


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


def find_morph_id(avatar: RIAvatar, morph_name):
    ASC: RIAvatarShapingComponent = avatar.GetAvatarShapingComponent()
    ids = ASC.GetShapingMorphIDs("")
    names = ASC.GetShapingMorphDisplayNames("")
    for i, name in enumerate(names):
        if name == morph_name:
            return ids[i]
    return None


def set_morph_slider(avatar: RIAvatar, slider_name, weight):
    morph_id = find_morph_id(avatar, slider_name)
    if morph_id:
        ASC: RIAvatarShapingComponent = avatar.GetAvatarShapingComponent()
        ASC.SetShapingMorphWeight(morph_id, weight)


def matrix_to_euler_xyz(M: RMatrix3, degrees=False):
    x = y = z = 0.0
    result = M.ToEulerAngle(EEulerOrder_XYZ, x, y, z)
    if degrees:
        x = result[0] * 180.0 / math.pi
        y = result[1] * 180.0 / math.pi
        z = result[2] * 180.0 / math.pi
    else:
        x = result[0]
        y = result[1]
        z = result[2]
    return (x, y, z)


def quaternion_to_euler_xyz(q: RQuaternion, degrees=False):
    M: RMatrix3 = q.ToRotationMatrix()
    return matrix_to_euler_xyz(M, degrees=degrees)


def dumps_vector3(v: RVector3):
    return f"({v.x:.3f}, {v.y:.3f}, {v.z:.3f})"


def dumps_quaternion(q: RQuaternion):
    return f"({q.x:.3f}, {q.y:.3f}, {q.z:.3f}, {q.w:.3f})"


def dumps_quaternion_xyz(q: RQuaternion):
    x,y,z = quaternion_to_euler_xyz(q, degrees=True)
    return f"({x:.3f}, {y:.3f}, {z:.3f})"


def quaternion_to_angle_axis(q: RQuaternion, axis: RVector3):
    q.Normalize()
    axis.Normalize()
    q = [q.x, q.y, q.z, q.w]
    axis = [axis.x, axis.y, axis.z]
    # Calculate the dot product of quaternion's vector part and the axis
    dot_product = sum([q[i] * axis[i] for i in range(3)])
    # Calculate the angle of rotation
    angle = 2 * math.acos(dot_product)
    return angle


def quaternion_to_vector(q: RQuaternion, axis: RVector3) -> RVector3:
    # Normalize the quaternion and axis
    q = q.Normalize()
    qv = RVector3(q.x, q.y, q.z)
    axis.Normalize()
    # Project quaternion onto the plane perpendicular to the axis
    d = axis.Dot(qv)
    return qv - (axis * d)


def signed_angle_between_quaternions(q1: RQuaternion, q2: RQuaternion, axis: RVector3):
    # Get the vectors in the plane perpendicular to the axis
    v1 = quaternion_to_vector(q1, axis)
    v2 = quaternion_to_vector(q2, axis)
    # Normalize the vectors
    v1.Normalize()
    v2.Normalize()
    # Calculate the unsigned angle between the vectors
    d = v1.Dot(v2)
    angle = math.acos(d)
    # Determine the sign of the angle
    cp: RVector3 = v1.Cross(v2)
    sign = cp.Dot(axis)
    if sign < 0:
        angle = -angle
    return angle


def signed_angle_between_vectors(v1: RVector3, v2: RVector3, axis: RVector3):
    v1p: RVector3 = project_vector_around_axis(v1, axis)
    v2p: RVector3 = project_vector_around_axis(v2, axis)
    v1p.Normalize()
    v2p.Normalize()
    d = v1p.Dot(v2p)
    angle = math.acos(d)
    c: RVector3 = v1p.Cross(v2p)
    sign = c.Dot(axis)
    if sign < 0:
        angle = -angle
    return angle


def project_vector_around_axis(v: RVector3, axis: RVector3):
    axis.Normalize()
    # Project the vector onto the axis
    v_a = axis * v.Dot(axis)
    # Calculate the perpendicular component
    v_perpendicular = v - v_a
    return v_perpendicular

