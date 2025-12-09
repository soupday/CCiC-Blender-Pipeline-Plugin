
import RLPy
import os
import json
import gzip
from typing import List
from . utils import log_info, log_warn, log_error
from . cc import is_cc

OPTS: 'Options' = None


def get_opts():
    global OPTS
    if not OPTS:
        OPTS = Options()
    return OPTS


class Options():
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
    CC_EXPORT_MAX_SUB_LEVEL: int = -1
    CC_EXPORT_FPS: float = 0.0
    IC_USE_FACIAL_PROFILE: bool = False
    IC_USE_HIK_PROFILE: bool = False
    IC_USE_FACIAL_EXPRESSIONS: bool = False
    IC_DELETE_HIDDEN_FACES: bool = True
    IC_BAKE_TEXTURES: bool = True
    IC_EXPORT_MODE: str = "Animation"
    IC_EXPORT_MAX_SUB_LEVEL: int = -1
    IC_EXPORT_FPS: float = 0.0
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
    EXPORT_FPS: float = 0.0
    #
    TOOLBAR_STATE_CC: bool = True
    TOOLBAR_STATE_IC: bool = True

    def get_export_fps(self):
        if self.EXPORT_FPS < 0.1:
            return RLPy.RGlobal.GetFps().ToFloat()
        return self.EXPORT_FPS

    def get_export_RFps(self):
        if self.EXPORT_FPS < 0.1:
            return RLPy.RGlobal.GetFps()
        return RLPy.RFps(float(self.EXPORT_FPS))

    def get_link_fps(self):
        if is_cc():
            if self.CC_EXPORT_FPS < 0.1:
                return RLPy.RGlobal.GetFps().ToFloat()
            return self.CC_EXPORT_FPS
        else:
            if self.IC_EXPORT_FPS < 0.1:
                return RLPy.RGlobal.GetFps().ToFloat()
            return self.IC_EXPORT_FPS

    def get_link_RFps(self):
        if is_cc():
            if self.CC_EXPORT_FPS < 0.1:
                return RLPy.RGlobal.GetFps()
            return RLPy.RFps(float(self.CC_EXPORT_FPS))
        else:
            if self.IC_EXPORT_FPS < 0.1:
                return RLPy.RGlobal.GetFps()
            return RLPy.RFps(float(self.IC_EXPORT_FPS))

    def read_state(self):
        res = RLPy.RGlobal.GetPath(RLPy.EPathType_CustomContent, "")
        temp_path = res[1]
        log_info(f"Custom Content Path: {temp_path}")
        temp_state_path = os.path.join(temp_path, "ccic_blender_pipeline_plugin.txt")
        log_info(f"Config File Path: {temp_state_path}")
        if os.path.exists(temp_state_path):
            temp_state_json = read_json(temp_state_path)
            if temp_state_json:
                self.BLENDER_PATH = get_attr(temp_state_json, "blender_path", "")
                self.DATALINK_FOLDER = get_attr(temp_state_json, "datalink_folder", "")
                self.EXPORT_MORPH_MATERIALS = get_attr(temp_state_json, "export_morph_materials", True)
                self.DEFAULT_MORPH_SLIDER_PATH = get_attr(temp_state_json, "default_morph_slider_path", "Custom/Blender")
                self.AUTO_START_SERVICE = get_attr(temp_state_json, "auto_start_service", False)
                self.MATCH_CLIENT_RATE = get_attr(temp_state_json, "match_client_rate", True)
                self.DATALINK_FRAME_SYNC = get_attr(temp_state_json, "datalink_frame_sync", False)
                self.CC_USE_FACIAL_PROFILE = get_attr(temp_state_json, "cc_use_facial_profile", True)
                self.CC_USE_HIK_PROFILE = get_attr(temp_state_json, "cc_use_hik_profile", True)
                self.CC_USE_FACIAL_EXPRESSIONS = get_attr(temp_state_json, "cc_use_facial_expressions", True)
                self.CC_DELETE_HIDDEN_FACES = get_attr(temp_state_json, "cc_delete_hidden_faces", False)
                self.CC_BAKE_TEXTURES = get_attr(temp_state_json, "cc_bake_textures", False)
                self.IC_USE_FACIAL_PROFILE = get_attr(temp_state_json, "ic_use_facial_profile", False)
                self.IC_USE_HIK_PROFILE = get_attr(temp_state_json, "ic_use_hik_profile", False)
                self.IC_USE_FACIAL_EXPRESSIONS = get_attr(temp_state_json, "ic_use_facial_expressions", False)
                self.IC_DELETE_HIDDEN_FACES = get_attr(temp_state_json, "ic_delete_hidden_faces", True)
                self.IC_BAKE_TEXTURES = get_attr(temp_state_json, "ic_bake_textures", True)
                self.CC_EXPORT_MODE = get_attr(temp_state_json, "cc_export_mode", "Animation")
                self.IC_EXPORT_MODE = get_attr(temp_state_json, "ic_export_mode", "Animation")
                self.CC_EXPORT_MAX_SUB_LEVEL = get_attr(temp_state_json, "cc_export_max_sub_level", -1)
                self.IC_EXPORT_MAX_SUB_LEVEL = get_attr(temp_state_json, "ic_export_max_sub_level", -1)
                self.CC_EXPORT_FPS = get_attr(temp_state_json, "cc_export_fps", 0.0)
                self.IC_EXPORT_FPS = get_attr(temp_state_json, "ic_export_fps", 0.0)
                self.EXPORT_PRESET = get_attr(temp_state_json, "export_preset", -1)
                self.EXPORT_BAKE_HAIR = get_attr(temp_state_json, "export_bake_hair", False)
                self.EXPORT_BAKE_SKIN = get_attr(temp_state_json, "export_bake_skin", False)
                self.EXPORT_T_POSE = get_attr(temp_state_json, "export_t_pose", False)
                self.EXPORT_CURRENT_POSE = get_attr(temp_state_json, "export_current_pose", False)
                self.EXPORT_CURRENT_ANIMATION = get_attr(temp_state_json, "export_current_animation", True)
                self.EXPORT_MOTION_ONLY = get_attr(temp_state_json, "export_motion_only", False)
                self.EXPORT_HIK = get_attr(temp_state_json, "export_hik", False)
                self.EXPORT_FACIAL_PROFILE = get_attr(temp_state_json, "export_facial_profile", False)
                self.EXPORT_REMOVE_HIDDEN = get_attr(temp_state_json, "export_remove_hidden", False)
                self.EXPORT_SUB_LEVEL = get_attr(temp_state_json, "export_sub_level", -1)
                self.TOOLBAR_STATE_CC = get_attr(temp_state_json, "toolbar_state_cc", True)
                self.TOOLBAR_STATE_IC = get_attr(temp_state_json, "toolbar_state_ic", True)
                self.EXPORT_FPS = get_attr(temp_state_json, "export_fps", 0.0)
        if self.CC_EXPORT_MODE == "Bind Pose": self.CC_EXPORT_MODE = "No Animation"
        if self.IC_EXPORT_MODE == "Bind Pose": self.CC_EXPORT_MODE = "No Animation"

    def write_state(self):
        res = RLPy.RGlobal.GetPath(RLPy.EPathType_CustomContent, "")
        temp_path = res[1]
        temp_state_path = os.path.join(temp_path, "ccic_blender_pipeline_plugin.txt")
        temp_state_json = {
            "blender_path": self.BLENDER_PATH,
            "datalink_folder": self.DATALINK_FOLDER,
            "export_morph_materials": self.EXPORT_MORPH_MATERIALS,
            "default_morph_slider_path": self.DEFAULT_MORPH_SLIDER_PATH,
            "auto_start_service": self.AUTO_START_SERVICE,
            "match_client_rate": self.MATCH_CLIENT_RATE,
            "datalink_frame_sync": self.DATALINK_FRAME_SYNC,
            "cc_use_facial_profile": self.CC_USE_FACIAL_PROFILE,
            "cc_use_hik_profile": self.CC_USE_HIK_PROFILE,
            "cc_use_facial_expressions": self.CC_USE_FACIAL_EXPRESSIONS,
            "cc_delete_hidden_faces": self.CC_DELETE_HIDDEN_FACES,
            "cc_bake_textures": self.CC_BAKE_TEXTURES,
            "ic_use_facial_profile": self.IC_USE_FACIAL_PROFILE,
            "ic_use_hik_profile": self.IC_USE_HIK_PROFILE,
            "ic_use_facial_expressions": self.IC_USE_FACIAL_EXPRESSIONS,
            "ic_delete_hidden_faces": self.IC_DELETE_HIDDEN_FACES,
            "ic_bake_textures": self.IC_BAKE_TEXTURES,
            "cc_export_mode": self.CC_EXPORT_MODE,
            "ic_export_mode": self.IC_EXPORT_MODE,
            "cc_export_max_sub_level": self.CC_EXPORT_MAX_SUB_LEVEL,
            "ic_export_max_sub_level": self.IC_EXPORT_MAX_SUB_LEVEL,
            "cc_export_fps": self.CC_EXPORT_FPS,
            "ic_export_fps": self.IC_EXPORT_FPS,
            "export_preset": self.EXPORT_PRESET,
            "export_bake_hair": self.EXPORT_BAKE_HAIR,
            "export_bake_skin": self.EXPORT_BAKE_SKIN,
            "export_t_pose": self.EXPORT_T_POSE,
            "export_current_pose": self.EXPORT_CURRENT_POSE,
            "export_current_animation": self.EXPORT_CURRENT_ANIMATION,
            "export_motion_only": self.EXPORT_MOTION_ONLY,
            "export_hik": self.EXPORT_HIK,
            "export_facial_profile": self.EXPORT_FACIAL_PROFILE,
            "export_remove_hidden": self.EXPORT_REMOVE_HIDDEN,
            "export_sub_level": self.EXPORT_SUB_LEVEL,
            "toolbar_state_cc": self.TOOLBAR_STATE_CC,
            "toolbar_state_ic": self.TOOLBAR_STATE_IC,
            "export_fps": self.EXPORT_FPS,
        }
        write_json(temp_state_json, temp_state_path)

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
        log_info(f"Error reading Json Data: {json_path}")
        return None


def get_attr(dictionary, name, default=None):
    if name in dictionary:
        return dictionary[name]
    return default


def write_json(json_data, path):
    json_object = json.dumps(json_data, indent = 4)
    with open(path, "w") as write_file:
        write_file.write(json_object)
