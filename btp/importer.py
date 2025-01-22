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
import PySide2
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
import os, time, shutil
from . import blender, morph, cc, qt, prefs, utils, vars


FBX_IMPORTER = None

class Importer:
    path = "C:/folder/dummy.fbx"
    folder = "C:/folder"
    file = "dummy.fbx"
    key = "C:/folder/dummy.fbxkey"
    name = "dummy"
    json_path = "C:/folder/dummy.json"
    hik_path = "C:/folder/dummy.3dxProfile"
    profile_path = "C:/folder/dummy.ccFacialProfile"
    avatar = None
    window_options = None
    window_progress = None
    progress_bar = None
    progress_2 = None
    check_mesh = None
    check_textures = None
    check_parameters = None
    check_import_hik = None
    check_import_profile = None
    check_import_expressions = None
    progress_count = 0
    mat_count = {}
    substance_import_success = False
    option_mesh = True
    option_textures = True
    option_parameters = True
    option_import_hik = False
    option_import_profile = False
    option_import_expressions = None
    character_type = None
    generation = None

    json_data: cc.CCJsonData = None

    def __init__(self, file_path, no_window=False, json_only=False):
        utils.log("================================================================")
        file_path = os.path.normpath(file_path)
        if json_only:
            utils.log("Material update import: " + file_path)
        else:
            utils.log("New character import, Fbx: " + file_path)
        self.path = file_path
        self.file = os.path.basename(self.path)
        self.folder = os.path.dirname(self.path)
        self.name = os.path.splitext(self.file)[0]
        self.key = os.path.join(self.folder, self.name + ".fbxkey")
        self.json_path = os.path.join(self.folder, self.name + ".json")
        self.json_data = cc.CCJsonData(self.json_path, self.path, self.name)
        self.hik_path = os.path.join(self.folder, self.name + ".3dxProfile")
        self.profile_path = os.path.join(self.folder, self.name + ".ccFacialProfile")

        self.generation = self.json_data.get_character_generation()
        self.character_type = self.json_data.get_character_type()
        self.link_id = self.json_data.get_link_id()
        utils.log_info(f"Character Generation: {self.generation}")
        utils.log_info(f"Character Type: {self.character_type}")

        error = False
        if not self.json_data.valid:
            qt.message_box("Invalid JSON Data", "There is no valid JSON data with this character or this is not a compatible CC3+ character.\n\nThe plugin will be unable to set-up any materials.\n\nPlease use the standard character importer instead (File Menu > Import).")
            error = True
        if not json_only and self.character_type == "STANDARD":
            if not os.path.exists(self.key):
                qt.message_box("No FBX Key", "There is no Fbx Key with this character!\n\nCC3/4 Standard characters cannot be imported back into Character Creator without a corresponding Fbx Key.\nThe Fbx Key will be generated when the character is exported as Mesh only, or in Calibration Pose, and with no hidden faces.")
                error = True

        if json_only:
            self.option_mesh = False
            self.option_textures = True
            self.option_parameters = True
        else:
            self.option_mesh = True
            self.option_textures = True
            self.option_parameters = True

        self.option_import_hik = False
        self.option_import_profile = False
        self.option_import_expressions = False
        if self.json_data.valid:
            root_json = self.json_data.get_root_json()
            if "HIK" in root_json and "Profile_Path" in root_json["HIK"]:
                self.hik_path = os.path.normpath(os.path.join(self.folder, root_json["HIK"]["Profile_Path"]))
                self.option_import_hik = True
            if "Facial_Profile" in root_json and "Profile_Path" in root_json["Facial_Profile"]:
                self.profile_path = os.path.normpath(os.path.join(self.folder, root_json["Facial_Profile"]["Profile_Path"]))
                self.option_import_profile = True
            if "Facial_Profile" in root_json and "Categories" in root_json["Facial_Profile"]:
                self.option_import_expressions = False

        if not error and not no_window:
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
        self.progress_bar = None
        self.progress_2 = None
        self.progress_count = 0
        self.mat_count = {}
        self.substance_import_success = False
        self.clean_up_globals()

    def clean_up_globals(self):
        global FBX_IMPORTER
        FBX_IMPORTER = None

    def create_options_window(self):
        W = 500
        H = 300
        TITLE = f"Blender Pipeline Import FBX"
        self.window_options, layout = qt.window(TITLE, width=W, height=H, fixed=True)
        self.window_options.SetFeatures(RLPy.EDockWidgetFeatures_Closable)

        qt.label(layout, f"Character Name: {self.name}", style=qt.STYLE_TITLE)
        qt.label(layout, f"Character Path: {self.path}", style=qt.STYLE_TITLE)
        qt.label(layout, f"Type: {self.character_type}", style=qt.STYLE_TITLE)

        qt.spacing(layout, 10)

        grid = qt.grid(layout)
        self.check_mesh = qt.checkbox(grid, "Import Mesh", self.option_mesh, row=0, col=0)
        self.check_textures = qt.checkbox(grid, "Import Textures", self.option_textures, row=1, col=0)
        self.check_parameters = qt.checkbox(grid, "Import Parameters", self.option_parameters, row=2, col=0)
        self.check_import_hik = qt.checkbox(grid, "Import HIK Profile", self.option_import_hik, row=0, col=1)
        self.check_import_profile = qt.checkbox(grid, "Import Facial Profile", self.option_import_profile, row=1, col=1)
        self.check_import_expressions = qt.checkbox(grid, "Import Facial Expressions", self.option_import_expressions, row=2, col=1)

        qt.spacing(layout, 10)

        qt.stretch(layout, 1)

        row = qt.row(layout)
        qt.button(row, "Import Character", self.import_fbx, height=32)
        qt.button(row, "Cancel", self.close_progress_window, height=32)

        self.window_options.Show()

    def create_progress_window(self):
        title = "Blender Auto-setup Character Import - Progress"
        self.window_progress, layout = qt.window(title, width=500, height=180, fixed=True)
        self.window_progress.SetFeatures(RLPy.EDockWidgetFeatures_NoFeatures)

        col = qt.column(layout)
        qt.label(col, f"Character Name: {self.name}")
        qt.label(col, f"Character Path: {self.path}")

        qt.spacing(layout, 10)
        qt.stretch(layout, 1)

        qt.label(layout, "Import Progress")
        self.progress_bar = qt.progress(layout, 0, 0, 0, "Intializing ...")

        self.window_progress.Show()

    def update_progress(self, inc, text = "", events = False):
        self.progress_count += inc
        qt.progress_update(self.progress_bar, self.progress_count, text)
        if events:
            qt.do_events()

    def set_datalink_import(self):
        self.option_mesh = True
        self.option_textures = True
        self.option_parameters = True
        self.option_import_expressions = False
        self.option_import_hik = False
        self.option_import_profile = False
        if cc.is_cc():
            self.option_import_expressions = prefs.CC_USE_FACIAL_EXPRESSIONS
            self.option_import_hik = prefs.CC_USE_HIK_PROFILE
            self.option_import_profile = prefs.CC_USE_FACIAL_PROFILE


    def import_fbx(self):
        """Import the character into CC3 and read in the json data.
        """
        self.fetch_options()
        self.close_options_window()

        objects = []

        if self.json_data.valid:

            # importing changes the selection so store it first.
            selected_objects = RLPy.RScene.GetSelectedObjects()

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
                    stored_md_props = RLPy.RScene.GetMDProps()

                if os.path.exists(self.key):
                    RLPy.RFileIO.LoadFbxFile(self.path, args, self.key, "", True)
                else:
                    RLPy.RFileIO.LoadFbxFile(self.path, args)

                # any prop not in the stored list is newly imported.
                if self.character_type == "PROP":
                    all_props = RLPy.RScene.GetProps()
                    all_md_props = RLPy.RScene.GetMDProps()
                    for prop in all_props:
                        if prop not in stored_props:
                            objects.append(prop)
                    for prop in all_md_props:
                        if prop not in stored_md_props:
                            objects.append(prop)
            else:

                if self.character_type == "PROP":
                   objects = selected_objects

            # if not importing a prop, use the current avatar
            if self.character_type != "PROP":
                avatar = cc.get_first_avatar()
                if avatar:
                    utils.log_info(f"Setting Character Name: {self.name}")
                    avatar.SetName(self.name)
                    morph.poke_morph_zero(avatar)
                    objects = [avatar]

            if len(objects) > 0:
                for obj in objects:
                    if obj:
                        self.avatar = obj
                        self.rebuild_materials()
                        RLPy.RScene.SelectObject(obj)

            # link ids
            if self.link_id:
                # single import, set the link_id
                if len(objects) == 1:
                    utils.log_info(f"Setting Link-ID: {objects[0].GetName()} {self.link_id}")
                    cc.set_link_id(objects[0], self.link_id)
                # if split props, generate new link id's
                elif len(objects) > 1:
                    utils.log_info(f"Generating new Link-ID's for split props")
                    for obj in objects:
                        link_id = cc.get_link_id(obj, add_if_missing=True)
                        utils.log_info(f"New Link-ID: {obj.GetName()} {link_id}")

        return objects

    def update_materials(self, obj):
        # NOTE: RILightAvatars and RIMDProps do not have material components so can't be updated.
        if type(obj) is RLPy.RIAvatar:
            self.avatar = obj
            self.rebuild_materials(update=True)
        elif type(obj) is RLPy.RIProp:
            objects = set()
            objects.add(obj)
            child_objects = RLPy.RGlobal.FindChildObjects(obj, RLPy.EObjectType_Prop)
            for child in child_objects:
                if cc.is_prop(child):
                    objects.add(child)
            for obj in objects:
                self.avatar = obj
                self.rebuild_materials(update=True)

    def rebuild_materials(self, update=False):
        """Material reconstruction process.
        """

        avatar = self.avatar
        json_data = self.json_data

        utils.start_timer()

        self.create_progress_window()
        cc_mesh_materials = cc.get_avatar_mesh_materials(avatar, json_data=json_data, exact=update)
        utils.log("Rebuilding character materials and texures:")
        self.update_shaders(cc_mesh_materials)
        self.update_progress(0, "Done Initializing!", True)

        if self.option_textures or self.option_parameters:
            self.import_substance_textures(cc_mesh_materials)
            self.import_custom_textures(cc_mesh_materials)
            self.import_physics(cc_mesh_materials)

        if not update: # do not update HIK / facial profiles on material updates

            if self.character_type == "HUMANOID":
                self.option_import_hik = True
                self.option_import_profile = True
                # user optional for importing custom facial expressions as the import profile will load the old ones.
                # and it's slow...
                #self.option_import_expressions = True

            if self.option_import_hik:
                self.import_hik_profile()

            if self.character_type == "STANDARD" or self.character_type == "HUMANOID":
                if self.option_import_profile or self.option_import_expressions:
                    self.import_facial_profile()

        self.final(cc_mesh_materials)

        time.sleep(1)
        self.close_progress_window()

        RLPy.RGlobal.ObjectModified(avatar, RLPy.EObjectModifiedType_Material)

        utils.log_timer("Import complete! Materials applied in: ")


    def update_shaders(self, cc_mesh_materials):
        """Precalculate the number of materials to be processed,
           to initialise progress bars.
           Also determine which materials may have duplicate names as these need to be treated differently.
        """

        num_materials = 0
        self.mat_count = {}

        M: cc.CCMeshMaterial
        for M in cc_mesh_materials:

            M.set_self_illumination(0)

            if M.has_json():

                # determine material duplication
                if M.mat_name in self.mat_count:
                    self.mat_count[M.mat_name] += 1
                else:
                    self.mat_count[M.mat_name] = 1

                # ensure the shader is correct:
                current_shader = M.get_shader()
                wanted_shader = M.mat_json.get_shader()
                # SSS skin on gamebase does not re-import correctly, use Pbr instead
                # TODO Testing if this is fixed - It isn't.
                if wanted_shader == "RLSSS" and M.mat_name.startswith("Ga_Skin_"):
                    wanted_shader = "Pbr"
                if current_shader != wanted_shader:
                    utils.log_info(f"Changing shader ({M.obj_name} / {M.mat_name}): {current_shader} to {wanted_shader}")
                    if not M.set_shader(wanted_shader):
                        utils.log_info(f" - Failed to set shader!")

                # Calculate stats
                num_materials += 1

            else:

                utils.log_info(f"Material: {M.mesh_name} / {M.mat_name} has no Json!")

        steps = 0
        # substance init & import
        if self.option_textures and self.character_type != "PROP":
            steps = 2 + num_materials
        # custom textures & params
        if self.option_textures or self.option_parameters:
            steps += num_materials
        # physics
        steps += 1
        # HIK import
        if self.character_type == "HUMANOID" and self.option_import_hik:
            steps += 2
        # facial expressions
        if self.character_type == "STANDARD" or self.character_type == "HUMANOID":
            if self.option_import_profile:
                steps += 2
            if self.option_import_expressions:
                steps += 2

        self.num_steps = steps
        self.num_materials = num_materials

        qt.progress_range(self.progress_bar, 0, self.num_steps)
        qt.do_events()


    def import_substance_textures(self, mesh_materials):
        """Cache all PBR textures in a temporary location to load in all at once with:
           RLPy.RFileIO.LoadSubstancePainterTextures()
           This is *much* faster than loading these textures individually,
           but requires a particular directory and file naming structure.
        """

        self.substance_import_success = False

        # only need to import all the textures when importing a new mesh with textures,
        # also doesn't work with props...
        if self.character_type == "PROP" or not self.option_textures:
            self.update_progress(0, "Skipping Substance Import", True)
            return

        utils.log("Beginning substance texture import:")
        utils.log_indent()

        self.update_progress(1, "Collecting Substance Textures", True)

        # create temp folder for substance import (use the temporary files location from the RGlobal.GetPath)
        # safest not to write temporary files in random locations...
        temp_path = cc.temp_files_path()
        if not os.path.exists(temp_path):
            utils.log("Unable to determine temporary file location, skipping substance import!")
            return
        temp_folder = os.path.join(temp_path, "CC3_BTP_Temp_" + utils.random_string(8))
        utils.log("Using temp folder: " + temp_folder)

        # delete if exists
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)

        # make a new temporary folder
        if not os.path.exists(temp_folder):
            os.mkdir(temp_folder)

        if vars.DEV:
            os.startfile(temp_folder)

        F: cc.CCMeshMaterial = None
        M: cc.CCMeshMaterial = None

        for M in mesh_materials:

            if not M.has_json():
                continue

            # The FbxKey will attempt to restore old textures,
            # but it wrongly restores the Normals into the Bump channel,
            # and the LoadSubstancePainterTextures() does not overrule this.
            # This causes major problems with texture channel loading later on,
            # so we need to remove all the existing normals and bump maps now:
            if True:
                if M.channel_has_image(RLPy.EMaterialTextureChannel_Bump):
                    M.remove_channel_image(RLPy.EMaterialTextureChannel_Bump)
                if M.channel_has_image(RLPy.EMaterialTextureChannel_Normal):
                    M.remove_channel_image(RLPy.EMaterialTextureChannel_Normal)

            if not F or F.mesh_name != M.mesh_name or M.mesh_name != "CC_Base_Body":
                F = M

            # substance texture import doesn't deal with duplicates well..
            if self.mat_count[M.mat_name] > 1:
                continue

            # create folder with first material name in each mesh
            substance_mat_folder = os.path.join(temp_folder, F.mat_name)
            if not os.path.exists(substance_mat_folder):
                os.makedirs(substance_mat_folder, exist_ok=True)

            mat_index = F.increment_substance_index()

            pid = M.mesh_name + " / " + M.mat_name
            utils.log(f"Mesh: {M.mesh_name}, Material: {M.mat_name}")

            # for each texture channel that can be imported with the substance texture method:
            for json_channel in cc.TEXTURE_MAPS.keys():
                is_substance = cc.TEXTURE_MAPS[json_channel][1]
                if is_substance:
                    substance_postfix = cc.TEXTURE_MAPS[json_channel][2]
                    tex_path = M.mat_json.get_texture_full_path(json_channel, self.folder)
                    if tex_path:
                        tex_dir, tex_file = os.path.split(tex_path)
                        tex_name, tex_type = os.path.splitext(tex_file)
                        # copy valid texture files to the temporary texture cache
                        if tex_name and os.path.exists(tex_path) and os.path.isfile(tex_path):
                            substance_name = F.mat_name + "_" + str(mat_index) + "_" + substance_postfix + tex_type
                            substance_path = os.path.normpath(os.path.join(substance_mat_folder, substance_name))
                            utils.safe_copy_file(tex_path, substance_path)

        self.update_progress(1, "Importing Substance Textures", True)

        # load all pbr textures in one go from the texture cache
        RLPy.RFileIO.LoadSubstancePainterTextures(self.avatar, temp_folder)
        self.substance_import_success = True

        utils.log_recess()
        utils.log("Substance texture import successful!")
        utils.log("Cleaning up temp folder: " + temp_folder)

        # delete temp folder
        if os.path.exists(temp_folder):
            shutil.rmtree(temp_folder)

        # done!
        self.update_progress(self.num_materials, "Substance Textures Done!", True)


    def import_custom_textures(self, mesh_materials):
        """Process all mesh objects and materials in the avatar, apply material settings,
           texture settings, custom shader textures and parameters from the json data.
        """

        utils.log("Beginning custom shader import ...")
        utils.log_indent()

        M: cc.CCMeshMaterial = None
        for M in mesh_materials:

            pid = M.mesh_name + " / " + M.mat_name
            self.update_progress(0, pid, True)

            if not M.has_json():
                self.update_progress(1, pid, True)
                continue

            utils.log(f"Mesh: {M.mesh_name}, Material: {M.mat_name}")

            if self.option_textures:

                # Custom shader textures
                shader_textures = M.get_shader_texture_names()
                if shader_textures:
                    for shader_channel in shader_textures:
                        tex_path = M.mat_json.get_texture_full_path(shader_channel, self.folder)
                        if tex_path and os.path.exists(tex_path) and os.path.isfile(tex_path):
                            M.load_shader_texture(shader_channel, tex_path)

                # Pbr Textures
                png_base_color = False
                has_opacity_map = M.mat_json.has_texture("Opacity")
                displacement_strength = -1
                normal_strength = -1
                bump_strength = -1

                for shader_channel in cc.TEXTURE_MAPS.keys():

                    rl_channel = cc.TEXTURE_MAPS[shader_channel][0]
                    is_substance = cc.TEXTURE_MAPS[shader_channel][1]
                    load_texture = not is_substance
                    # fully process textures for materials with duplicates,
                    # as the substance texture import can't really deal with them.
                    if self.mat_count[M.mat_name] > 1:
                        load_texture = True
                    # load any textures the substance importer may have missed
                    if not M.channel_has_image(rl_channel):
                        load_texture = True
                    # or if the substance texture import method failed, import all textures individually
                    if not self.substance_import_success:
                        load_texture = True
                    # prop objects don't work with substance texture import currently
                    if self.character_type == "PROP":
                        load_texture = True

                    tex_path = M.mat_json.get_texture_full_path(shader_channel, self.folder)
                    if tex_path:
                        # PNG diffuse maps with alpha channels don't fill in opacity correctly with substance import method
                        if shader_channel == "Base Color" and not has_opacity_map and os.path.splitext(tex_path)[-1].lower() == ".png":
                            png_base_color = True
                            load_texture = True
                        elif shader_channel == "Opacity" and png_base_color:
                            load_texture = True
                        strength = M.mat_json.get_base_texture_strength(shader_channel)
                        offset, tiling = M.mat_json.get_base_texture_offset_tiling(shader_channel)
                        # Note: rotation doesn't seem to be exported to the Json?
                        rotation = M.mat_json.get_base_texture_rotation(shader_channel)
                        # set textures
                        if os.path.exists(tex_path) and os.path.isfile(tex_path):
                            if load_texture:
                                M.load_channel_image(rl_channel, tex_path)
                            M.set_uv_mapping(rl_channel, offset, tiling, rotation)
                            if shader_channel == "Displacement":
                                displacement_strength = strength
                            elif shader_channel == "Normal":
                                normal_strength = strength
                            elif shader_channel == "Bump":
                                bump_strength = strength
                            else:
                                M.set_channel_texture_weight(rl_channel, strength)
                        if shader_channel == "Displacement":
                            level, multiplier, threshold = M.mat_json.get_tessellation()
                            M.set_attribute("TessellationLevel", level)
                            M.set_attribute("TessellationMultiplier", multiplier)
                            M.set_attribute("TessellationThreshold", threshold * 100)

                # displacement strength overrides normal strength which overrides bump, so only set one.
                if displacement_strength > -1:
                    #print(f"Displacement Strength: {displacement_strength}")
                    M.set_channel_texture_weight(RLPy.EMaterialTextureChannel_Displacement, displacement_strength)
                elif normal_strength > -1:
                    #print(f"Normal Strength: {normal_strength}")
                    M.set_channel_texture_weight(RLPy.EMaterialTextureChannel_Normal, normal_strength)
                elif bump_strength > -1:
                    #print(f"Bump Strength: {bump_strength}")
                    M.set_channel_texture_weight(RLPy.EMaterialTextureChannel_Bump, bump_strength)


            if self.option_parameters:

                # Base material parameters
                diffuse_color = M.mat_json.get_diffuse_color()
                ambient_color = M.mat_json.get_ambient_color()
                specular_color = M.mat_json.get_specular_color()
                self_illumination = M.mat_json.get_self_illumination()
                opacity = M.mat_json.get_opacity()
                M.set_diffuse(diffuse_color)
                M.set_ambient(ambient_color)
                M.set_specular(specular_color)
                M.set_self_illumination(self_illumination)
                M.set_opacity(opacity)

                # Custom shader parameters
                shader_params = M.get_shader_parameter_names()
                for param in shader_params:
                    json_value = None
                    if param.startswith("SSS "):
                        json_value = M.mat_json.get_sss_var(param[4:])
                    else:
                        json_value = M.mat_json.get_custom_shader_var(param)
                    if json_value is not None:
                        M.set_shader_parameter(param, json_value)

                # Extra parameters (from Blender)
                hue = M.mat_json.get_base_var("Diffuse Hue", 0.5)
                saturation = M.mat_json.get_base_var("Diffuse Saturation", 1.0)
                brightness = M.mat_json.get_base_var("Diffuse Brightness", 1.0)
                if hue != 0.5 or saturation != 1.0 or brightness != 1.0:
                    hue = 200 * hue - 100
                    saturation = 100 * saturation - 100
                    brightness = 100 * brightness - 100
                    M.set_channel_image_color(cc.TextureChannel.DIFFUSE, 0.0, hue, saturation, brightness, 0, 0,0,0)

            self.update_progress(1, pid, True)

        utils.log_recess()
        utils.log("Custom shader import complete!")


    def import_physics(self, cc_mesh_materials):

        utils.log(f"Import Physics")
        utils.log_indent()

        self.update_progress(0, "Importing Physics", True)

        M: cc.CCMeshMaterial
        for M in cc_mesh_materials:
            if M.physics_component() and M.has_physics_json():
                utils.log(f"Mesh: {M.mesh_name}, Material: {M.mat_name}")
                mass = None
                param_names = M.physx_mat_json.get_params()
                for param_name in param_names:
                    param_value = M.physx_mat_json.get_var(param_name)
                    if param_name == "Mass":
                        mass = param_value
                    else:
                        M.set_physics_param(param_name, param_value, self.folder)
                # mass needs to be set last, otherwise it gets reset back to 1
                if mass is not None:
                    M.set_physics_param("Mass", mass)

        self.update_progress(1, "Importing Physics", True)

        utils.log_recess()
        utils.log("Physics import complete!")


    def import_facial_profile(self):
        avatar = self.avatar
        json_data = self.json_data.json_data

        if "Facial_Profile" in json_data[self.name].keys():

            utils.log("Importing Facial Profile")

            profile_json = json_data[self.name]["Facial_Profile"]
            facial_profile:RLPy.RIFacialProfileComponent = avatar.GetFacialProfileComponent()

            if self.option_import_profile:

                self.update_progress(0, "Importing Facial Profile", True)

                # first reload the original profile of the character
                # TODO: this will not work if the topology has changed, does it fail gracefully?
                if os.path.exists(self.profile_path):
                    utils.log(f"Restoring Facial Profile: {self.profile_path}")
                    facial_profile.LoadProfile(self.profile_path)
                else:
                    utils.log_warn(f"No facial profile at: {self.profile_path}")

                self.update_progress(2, "Importing Facial Profile", True)

            if self.option_import_expressions:

                self.update_progress(0, "Importing Expressions", True)
                utils.log(f"Importing Facial Expressions:")

                # then overwrite with the blend shapes in the fbx
                # any new/custom expression blend shapes must be added to json when exported from Blender
                # Blender must add viseme Blend shapes to json when exporting back
                sliders = []
                if "Categories" in profile_json.keys():
                    categories_json = profile_json["Categories"]
                    for category in categories_json.keys():
                        if category != "Jaw" and category != "EyeLook" and category != "Head":
                            utils.log(f"Gathering Expressions for Category: {category}")
                            sliders.extend(categories_json[category])
                    utils.log(f"Importing Gathered Expressions: {sliders}")
                    utils.log(f" - Path: {self.path}")
                    res: RLPy.RStatus = facial_profile.ImportMorphs(self.path, True, sliders, "Custom")
                    if res.IsError():
                        utils.log_error(f"Expression import failed!")

                self.update_progress(2, "Importing Expressions", True)


    def import_hik_profile(self):
        if self.option_import_hik:
            self.update_progress(0, "Importing HIK Profile", True)
            if os.path.exists(self.hik_path):
                utils.log(f"Restoring HIK Profile: {self.hik_path}")
                self.avatar.DoCharacterization(self.hik_path, True, True, True)
            self.update_progress(2, "Importing HIK Profile", True)


    def final(self, cc_mesh_materials):
        M: cc.CCMeshMaterial
        for M in cc_mesh_materials:
            if M.has_json():
                # lastly remove any _Transparency suffix from the material names
                if M.mat_name.endswith("_Transparency"):
                    new_name = M.mat_name[:-13]
                    M.change_material_name(new_name)
                    M.mat_name = new_name

        self.update_progress(0, "Done!")
        qt.do_events()
