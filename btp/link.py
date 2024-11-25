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
del abs
import PySide2
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
import os, socket, select, struct, time, json, random, atexit, traceback
from . import blender, importer, exporter, morph, cc, qt, prefs, tests, utils, vars
from enum import IntEnum
import math

LOCALHOST = "127.0.0.1"
BLENDER_PORT = 9334
UNITY_PORT = 9335
RL_PORT = 9333
TIMER_INTERVAL = 1000/60
MAX_CHUNK_SIZE = 32768
HANDSHAKE_TIMEOUT_S = 60
KEEPALIVE_TIMEOUT_S = 300
PING_INTERVAL_S = 1
SERVER_ONLY = True
CLIENT_ONLY = False
EMPTY_SOCKETS = []
MAX_RECEIVE = 24
USE_PING = False
USE_KEEPALIVE = False
USE_BLOCKING = False
SOCKET_TIMEOUT = 5.0

class OpCodes(IntEnum):
    NONE = 0
    HELLO = 1
    PING = 2
    STOP = 10
    DISCONNECT = 11
    DEBUG = 15
    NOTIFY = 50
    SAVE = 60
    MORPH = 90
    MORPH_UPDATE = 91
    REPLACE_MESH = 95
    MATERIALS = 96
    CHARACTER = 100
    CHARACTER_UPDATE = 101
    PROP = 102
    PROP_UPDATE = 103
    UPDATE_REPLACE = 108
    RIGIFY = 110
    TEMPLATE = 200
    POSE = 210
    POSE_FRAME = 211
    SEQUENCE = 220
    SEQUENCE_FRAME = 221
    SEQUENCE_END = 222
    SEQUENCE_ACK = 223
    LIGHTS = 230
    CAMERA_SYNC = 231
    FRAME_SYNC = 232
    MOTION = 240


VISEME_NAME_MAP = {
    "EE": EVisemeID_EE,
    "Er": EVisemeID_ER,
    "IH": EVisemeID_IH,
    "Ah": EVisemeID_AH,
    "Oh": EVisemeID_OH,
    "W_OO": EVisemeID_W_OO,
    "S_Z": EVisemeID_S_Z,
    "Ch_J": EVisemeID_CH_J,
    "F_V": EVisemeID_F_V,
    "TH": EVisemeID_TH,
    "T_L_D_N": EVisemeID_T_L_D_N,
    "B_M_P": EVisemeID_B_M_P,
    "K_G_H_NG": EVisemeID_K_G_H_NG,
    "AE": EVisemeID_AE,
    "R": EVisemeID_R,
}


FACE_EXPRESSION_PREFIXES = ["Mouth_",
                            "Jaw_",
                            "Eye_",
                            "Right_Eyeball_",
                            "Left_Eyeball_"]

IGNORE_EXPRESSIONS = [ "Mouth_Close" ]

FACE_BONES = [ "CC_Base_JawRoot", "CC_Base_FacialBone", "CC_Base_Head",
               "CC_Base_Tongue01", "CC_Base_Tongue02", "CC_Base_Tongue03",
               "CC_Base_R_Eye", "CC_Base_L_Eye",
               "CC_Base_Teeth01", "CC_Base_Teeth02", "CC_Base_UpperJaw", ""]

FACE_DRIVERS = {
    "Jaw_Open": "CC_Base_JawRoot",
    "Eye_L_Look_L": "CC_Base_L_Eye",
    "Eye_R_Look_L": "CC_Base_R_Eye",
    "Eye_L_Look_R": "CC_Base_L_Eye",
    "Eye_R_Look_R": "CC_Base_R_Eye",
    "Eye_L_Look_Up": "CC_Base_L_Eye",
    "Eye_R_Look_Up": "CC_Base_R_Eye",
    "Eye_L_Look_Down": "CC_Base_L_Eye",
    "Eye_R_Look_Down": "CC_Base_R_Eye",
    "A10_Eye_Look_Out_Left": "CC_Base_L_Eye",
    "A12_Eye_Look_In_Right": "CC_Base_R_Eye",
    "A11_Eye_Look_In_Left": "CC_Base_L_Eye",
    "A13_Eye_Look_Out_Right": "CC_Base_R_Eye",
    "A06_Eye_Look_Up_Left": "CC_Base_L_Eye",
    "A07_Eye_Look_Up_Right": "CC_Base_R_Eye",
    "A08_Eye_Look_Down_Left": "CC_Base_L_Eye",
    "A09_Eye_Look_Down_Right": "CC_Base_R_Eye",
}


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


class LinkActor():
    name: str = "Name"
    object: RIObject = None
    bones: list = None
    shapes: list = None
    skin_bones: list = None
    skin_meshes: list = None
    expressions: dict = None
    expression_rotations: dict = None
    face_rotations: dict = None
    face_drivers: dict = None
    visemes: dict = None
    morphs: dict = None
    t_pose: dict = None
    alias: list = None

    def __init__(self, object):
        self.name = object.GetName()
        self.object = object
        self.bones = []
        self.shapes = []
        self.skin_bones = []
        self.skin_meshes = []
        self.expressions = {}
        self.expression_rotations = {}
        self.face_rotations = {}
        self.face_drivers = {}
        self.visemes = {}
        self.morphs = {}
        self.t_pose = None
        self.alias = []
        self.get_link_id()

    def get_avatar(self) -> RIAvatar:
        return self.object

    def get_prop(self) -> RIProp:
        return self.object

    def get_object(self) -> RIObject:
        return self.object

    def update(self, name, link_id):
        self.name = name
        self.set_link_id(link_id)

    def begin_editing(self):
        FC = self.get_face_component()
        if FC:
            FC.BeginKeyEditing()

    def end_editing(self, time):
        FC = self.get_face_component()
        if FC:
            FC.EndKeyEditing()
        SC = self.get_skeleton_component()
        SC.BakeFkToIk(time, True)

    def get_skeleton_component(self) -> RISkeletonComponent:
        if self.object:
            if cc.is_avatar(self.object) or cc.is_prop(self.object):
                return self.object.GetSkeletonComponent()
        return None

    def get_face_component(self) -> RIFaceComponent:
        if self.object:
            if cc.is_avatar(self.object):
                return self.object.GetFaceComponent()
        return None

    def get_viseme_component(self) -> RIVisemeComponent:
        if self.object:
            if cc.is_avatar(self.object):
                return self.object.GetVisemeComponent()
        return None

    def get_morph_component(self) -> RIMorphComponent:
        if self.object:
            if cc.is_avatar(self.object) or cc.is_prop(self.object):
                return self.object.GetMorphComponent()
        return None

    def get_expression_bone_rotations(self, actor_expressions):
        FC = self.get_face_component()
        SC = self.get_skeleton_component()
        bones = SC.GetSkinBones()
        expressions = FC.GetExpressionNames("")
        expression_rotations = {}
        face_rotations = {}
        face_drivers = {}

        for expression in expressions:
            is_face = False
            if expression in IGNORE_EXPRESSIONS:
                continue
            for face_prefix in FACE_EXPRESSION_PREFIXES:
                if expression.startswith(face_prefix):
                    is_face = True
                    break
            for bone in bones:
                bone_name = bone.GetName()
                if is_face and bone_name not in FACE_BONES:
                    continue
                try:
                    ERM: RMatrix3 = FC.GetExpressionBoneRotation(bone_name, expression)
                except:
                    ERM = RMatrix3(1, 0, 0,
                                   0, 1, 0,
                                   0, 0, 1)
                ERQ = RQuaternion()
                ERQ.FromRotationMatrix(ERM)
                euler_angle_x, euler_angle_y, euler_angle_z = cc.quaternion_to_euler_xyz(ERQ, degrees=True)
                t = abs(euler_angle_x) + abs(euler_angle_y) + abs(euler_angle_z)
                if t > 0.1:
                    if expression in actor_expressions:
                        if is_face:
                            if expression not in face_rotations:
                                face_rotations[expression] = {}
                            face_rotations[expression][bone_name] = ERQ
                            #print(f"{expression} / {bone_name} = ({euler_angle_x:.4f}, {euler_angle_y:.4f}, {euler_angle_z:.4f})")
                            if expression in FACE_DRIVERS:
                                driving_bone = FACE_DRIVERS[expression]
                                if driving_bone not in face_drivers:
                                    face_drivers[driving_bone] = []
                                face_drivers[driving_bone].append(expression)
                        else:
                            if expression not in expression_rotations:
                                expression_rotations[expression] = {}
                            expression_rotations[expression][bone_name] = ERQ
        self.expression_rotations = expression_rotations
        self.face_rotations = face_rotations
        self.face_drivers = face_drivers

    def set_template(self, actor_data):
        self.bones = actor_data["bones"]
        self.shapes = actor_data["shapes"]
        FC = self.get_face_component()
        VC = self.get_viseme_component()
        MC = self.get_morph_component()
        self.expressions = {}
        self.visemes = {}
        self.morphs = {}
        if FC:
            names = FC.GetExpressionNames("")
            for i, name in enumerate(self.shapes):
                if name in names:
                    self.expressions[name] = i
        if VC:
            for i, name in enumerate(self.shapes):
                if name in VISEME_NAME_MAP:
                    viseme_id = VISEME_NAME_MAP[name]
                    self.visemes[viseme_id] = i
        if MC:
            pass
        self.get_expression_bone_rotations(self.expressions)

    def set_t_pose(self, t_pose):
        self.t_pose = t_pose

    def add_alias(self, link_id):
        actor_link_id = cc.get_link_id(self.object)
        if not actor_link_id:
            utils.log_info(f"Assigning actor link_id: {self.object.GetName()}: {link_id}")
            cc.set_link_id(self.object, link_id)
            return
        if link_id not in self.alias and actor_link_id != link_id:
            utils.log_info(f"Assigning actor alias: {self.object.GetName()}: {link_id}")
            self.alias.append(link_id)
            return

    @staticmethod
    def find_actor(link_id, search_name=None, search_type=None):

        utils.log_detail(f"Looking for LinkActor: {search_name} {link_id} {search_type}")
        actor: LinkActor = None
        obj = cc.find_object_by_link_id(link_id)
        if obj:
            if not search_type or LinkActor.get_actor_type(obj) == search_type:
                actor = LinkActor(obj)
                return actor
        utils.log_detail(f"Chr not found by link_id")

        if search_name:
            obj = cc.find_object_by_name_and_type(search_name, search_type)
            if obj:
                found_link_id = cc.get_link_id(obj)
                utils.log_detail(f"Chr found by name: {obj.GetName()} / {found_link_id}")
                actor = LinkActor(obj)
                actor.add_alias(link_id)
                return actor
            utils.log_detail(f"Chr not found by name")

        if cc.is_cc() and search_type == "AVATAR":
            avatar = cc.get_first_avatar()
            if avatar:
                found_link_id = cc.get_link_id(obj)
                utils.log_detail(f"Falling back to first Avatar: {avatar.GetName()} / {found_link_id}")
                actor = LinkActor(avatar)
                actor.add_alias(link_id)
                return actor

        utils.log_info(f"LinkActor not found: {search_name} {link_id} {search_type}")
        return actor

    @staticmethod
    def get_actor_type(obj):
        T = type(obj)
        if T is RIAvatar or T is RILightAvatar:
            return "AVATAR"
        elif T is RIProp or T is RIMDProp:
            return "PROP"
        elif T is RILight:
            return "LIGHT"
        elif T is RICamera:
            return "CAMERA"
        else:
            return "NONE"

    def get_type(self):
        return self.get_actor_type(self.object)

    def is_avatar(self):
        return cc.is_avatar(self.object)

    def is_prop(self):
        return cc.is_prop(self.object)

    def is_light(self):
        return type(self.object) is RILight

    def is_camera(self):
        return type(self.object) is RICamera

    def is_standard(self):
        if self.is_avatar():
            avatar_type = self.object.GetAvatarType()
            if avatar_type == EAvatarType_Standard or avatar_type == EAvatarType_StandardSeries:
                return True
        return False

    def get_link_id(self):
        return cc.get_link_id(self.object, add_if_missing=True)

    def set_link_id(self, link_id):
        cc.set_link_id(self.object, link_id)


class LinkData():
    link_host: str = "localhost"
    link_host_ip: str = "127.0.0.1"
    link_target: str = "BLENDER"
    link_port: int = 9333
    # Pose Props
    pose_frame: int = 0
    # Sequence Props
    sequence_start_frame: int = 0
    sequence_end_frame: int = 0
    sequence_current_frame_time: RTime = 0
    sequence_current_frame: int = 0
    sequence_actors: list = None
    sequence_active: bool = False
    #
    ack_rate: float = 0.0
    ack_time: float = 0.0
    #
    stored_selection: list = None

    def __init__(self):
        return

    def find_sequence_actor(self, link_id) -> LinkActor:
        for actor in self.sequence_actors:
            if actor.get_link_id() == link_id:
                return actor
        for actor in self.sequence_actors:
            if link_id in actor.alias:
                return actor
        return None


def pack_string(s):
    buffer = bytearray()
    buffer += struct.pack("!I", len(s))
    buffer += bytes(s, encoding="utf-8")
    return buffer


def unpack_string(buffer, offset=0):
    length = struct.unpack_from("!I", buffer, offset)[0]
    offset += 4
    string: bytearray = buffer[offset:offset+length]
    offset += length
    return offset, string.decode(encoding="utf-8")


def encode_from_json(json_data):
    json_string = json.dumps(json_data)
    json_bytes = bytearray(json_string, "utf-8")
    return json_bytes


def decode_to_json(data):
    text = data.decode("utf-8")
    json_data = json.loads(text)
    return json_data


def reset_animation():
    start_time = RGlobal.GetStartTime()
    RGlobal.SetTime(start_time)
    return start_time


def prep_timeline_old(SC: RISkeletonComponent, start_frame, end_frame):
    fps = get_fps()
    start_time = fps.IndexedFrameTime(start_frame)
    end_time: fps.IndexedFrameTime(end_frame)
    RGlobal.SetStartTime(start_time)
    RGlobal.SetEndTime(end_time)
    utils.log_info(f"start: {start_time.ToFloat()}, end: {end_time.ToFloat()}")
    num_clips = SC.GetClipCount()
    if num_clips == 0:
        clip = SC.AddClip(start_time)
    elif num_clips == 1:
        pass
    else:
        while SC.GetClipCount() > 1:
            num_clips = SC.GetClipCount()
            clip0 = SC.GetClip(num_clips-2)
            clip1 = SC.GetClip(num_clips-1)
            SC.MergeClips(clip0, clip1)
    clip: RIClip = SC.GetClip(0)
    return


def get_fps() -> RFps:
    return RGlobal.GetFps()


def get_current_frame():
    fps = get_fps()
    current_time = RGlobal.GetTime()
    current_frame = fps.GetFrameIndex(current_time)
    return current_frame


def get_end_frame():
    fps = get_fps()
    end_time: RTime = RGlobal.GetEndTime()
    end_frame = fps.GetFrameIndex(end_time)
    return end_frame


def next_frame(time):
    fps = get_fps()
    current_time = RGlobal.GetTime()
    next_time = fps.GetNextFrameTime(time)
    RGlobal.SetTime(next_time)
    return next_time


def prev_frame(time):
    fps = get_fps()
    current_time = RGlobal.GetTime()
    prev_time = fps.GetPreviousFrameTime(time)
    RGlobal.SetTime(prev_time)
    return prev_time


def set_frame_range(start_frame, end_frame):
    fps = get_fps()
    RGlobal.SetStartTime(fps.IndexedFrameTime(start_frame))
    RGlobal.SetEndTime(fps.IndexedFrameTime(end_frame))


def set_frame(frame):
    fps = get_fps()
    RGlobal.SetTime(fps.IndexedFrameTime(frame))


def refresh_timeline(actors):
    """Selecting and deselecting the actors is enough to refresh the animation player timeline
       after any changes in project length and animation clips"""
    RScene.ClearSelectObjects()
    if actors:
        actor: LinkActor
        for actor in actors:
            RScene.SelectObject(actor.object)
        RScene.ClearSelectObjects()


def get_frame_time(frame) -> RTime:
    fps = get_fps()
    return fps.IndexedFrameTime(frame)


def get_clip_frame(clip: RIClip, scene_time: RTime):
    fps = get_fps()
    clip_time = clip.SceneTimeToClipTime(scene_time)
    return fps.GetFrameIndex(clip_time)


def update_timeline(to_time=None):
    """Force the timeline to update by playing the current frame"""
    if not to_time:
        to_time = RGlobal.GetTime()
    RGlobal.Play(to_time, to_time)


def extend_project_range(end_time: RTime, min_time = 0):
    proj_length: RTime = RGlobal.GetProjectLength()
    if end_time.ToFloat() > proj_length.ToFloat():
        utils.log_info(f"Extending Project Range: {end_time.ToFloat()}")
        RGlobal.SetProjectLength(end_time)
    else:
        RGlobal.SetProjectLength(proj_length)


def set_project_range(end_time: RTime):
    utils.log_info(f"Setting Project Range: {end_time.ToFloat()}")
    RGlobal.SetProjectLength(end_time)


def get_clip_at_or_before(avatar: RIAvatar, time: RTime):
    fps = get_fps()
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    num_clips = SC.GetClipCount()
    found_clip: RIClip = None
    nearest_end_time: RTime = None
    for i in range(0, num_clips):
        clip:RIClip = SC.GetClip(i)
        clip_start = clip.ClipTimeToSceneTime(fps.IndexedFrameTime(0))
        length = clip.GetClipLength()
        clip_end = clip.ClipTimeToSceneTime(length)
        if time >= clip_start and time <= clip_end:
            found_clip = clip
            return found_clip
        elif time > clip_end:
            if not found_clip or clip_end > nearest_end_time:
                found_clip = clip
                nearest_end_time = clip_end
    return found_clip


def make_avatar_clip(avatar, start_time, num_frames):
    fps = get_fps()
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    clip: RIClip = SC.AddClip(start_time)
    length = fps.IndexedFrameTime(num_frames)
    clip.SetLength(length)
    return clip


def finalize_avatar_clip(avatar, clip):
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    SC.BakeFkToIk(RTime.FromValue(0), True)


def decompose_transform(T: RTransform):
    t: RVector3 = T.T()
    r: RQuaternion = T.R()
    s: RVector3 = T.S()
    return t, r, s


def apply_pose(actor: LinkActor, time: RTime, pose_data, shape_data, t_pose_data):
    SC = actor.get_skeleton_component()
    if SC:
        clip: RIClip = SC.GetClipByTime(time)
        if clip:
            clip_time = clip.SceneTimeToClipTime(time)
            if len(actor.bones) != len(pose_data):
                utils.log_error("Bones do not match!")
                return
            root_bone: RINode = SC.GetRootBone()
            root_rot = RQuaternion(RVector4(0,0,0,1))
            root_tra = RVector3(0,0,0)
            root_sca = RVector3(1,1,1)
            apply_world_fk_pose(actor, SC, clip, clip_time,
                                root_bone, pose_data, shape_data,
                                t_pose_data, root_rot, root_tra, root_sca)
            scene_time = clip.ClipTimeToSceneTime(clip_time)
            SC.BakeFkToIk(scene_time, False)


def get_pose_local(avatar: RIAvatar):
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones = SC.GetSkinBones()
    pose = {}
    for bone in skin_bones:
        T: RTransform = bone.LocalTransform()
        t: RVector3 = T.T()
        r: RQuaternion = T.R()
        s: RVector3 = T.S()
        pose[bone.GetName()] = [
            t.x, t.y, t.z,
            r.x, r.y, r.z, r.w,
            s.x, s.y, s.z,
        ]
    return pose


def get_pose_world(avatar: RIAvatar):
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones = SC.GetSkinBones()
    pose = {}
    for bone in skin_bones:
        T: RTransform = bone.WorldTransform()
        t: RVector3 = T.T()
        r: RQuaternion = T.R()
        s: RVector3 = T.S()
        pose[bone.GetName()] = [
            t.x, t.y, t.z,
            r.x, r.y, r.z, r.w,
            s.x, s.y, s.z,
        ]
    return pose


def fetch_pose_transform(pose_data, bone_index_or_name):
    D = pose_data[bone_index_or_name]
    tra = RVector3(D[0], D[1], D[2])
    rot = RQuaternion(RVector4(D[3], D[4], D[5], D[6]))
    sca = RVector3(D[7], D[8], D[9])
    return tra, rot, sca


def fetch_transform(D):
    tra = RVector3(D[0], D[1], D[2])
    rot = RQuaternion(RVector4(D[3], D[4], D[5], D[6]))
    sca = RVector3(D[7], D[8], D[9])
    return tra, rot, sca


def fetch_pose_root_transform(actor: LinkActor, pose_data):
    SC = actor.get_skeleton_component()
    root_bone = SC.GetRootBone()
    source_name = root_bone.GetName()
    root_bone_name = try_get_pose_bone(source_name, actor.bones)
    if root_bone_name in actor.bones:
        bone_index = actor.bones.index(root_bone_name)
        return fetch_transform(pose_data[bone_index])
    else:
        return fetch_transform([0,0,0,0,0,0,1,1,1,1])


def log_transform(name, rot, tra, sca):
    utils.log_info(f" - {name}: ({utils.fd2(tra.x)}, {utils.fd2(tra.y)}, {utils.fd2(tra.z)}) - ({utils.fd2(rot.x)}, {utils.fd2(rot.x)}, {utils.fd2(rot.z)}, {utils.fd2(rot.w)}) - ({utils.fd2(sca.x)}, {utils.fd2(sca.y)}, {utils.fd2(sca.z)})")


TRY_BONES = {
    "RL_BoneRoot": ["CC_Base_BoneRoot", "Rigify_BoneRoot", "BoneRoot", "root"],
}

def try_get_pose_bone(name, bones: list):
    if name not in bones and name in TRY_BONES:
        names = TRY_BONES[name]
        for n in names:
            if n in bones:
                return n
    return name


def get_expression_counter_rotation(actor: LinkActor, bone_name, expression_weights) -> RQuaternion:
    """TODO optimize this:
         store expression_rotation keys as indices not names
         only need to figure out once which bones are affected and pass that list along"""
    exp_rotations = actor.expression_rotations
    R = RQuaternion(RVector4(0,0,0,1))
    I = RQuaternion(RVector4(0,0,0,1))
    if True:
        for exp_name in exp_rotations:
            exp_index = actor.expressions[exp_name]
            w = expression_weights[exp_index]
            if w > 0.001:
                if bone_name in exp_rotations[exp_name]:
                    ERQ: RQuaternion = exp_rotations[exp_name][bone_name]
                    ERQW = I + (ERQ - I)*w
                    R = R.Multiply(ERQW)
    return R.Inverse()


def apply_world_ik_pose(actor, SC: RISkeletonComponent, clip: RIClip, time: RTime, pose_data):
    tra, rot, sca = fetch_pose_transform(pose_data, 0)
    set_ik_effector(SC, clip, EHikEffector_LeftFoot, time,  rot, tra, sca)
    tra, rot, sca = fetch_pose_transform(pose_data, 0)
    set_ik_effector(SC, clip, EHikEffector_RightFoot, time,  rot, tra, sca)


def apply_world_fk_pose(actor, SC: RISkeletonComponent, clip, time, bone: RINode, pose_data, shape_data, t_pose_data,
                        parent_world_rot, parent_world_tra, parent_world_sca):
    source_name = bone.GetName()
    bone_name = try_get_pose_bone(source_name, actor.bones)
    if bone_name in actor.bones:
        bone_index = actor.bones.index(bone_name)
        world_tra, world_rot, world_sca = fetch_pose_transform(pose_data, bone_index)
        t_pose_tra, t_pose_rot, t_pose_sca = fetch_pose_transform(t_pose_data, source_name)
        local_rot, local_tra, local_sca = calc_local(world_rot, world_tra, world_sca,
                                                     parent_world_rot, parent_world_tra, parent_world_sca)
        # don't apply any translation to twist or share bones
        if "Twist" in bone_name or "Share" in bone_name:
            local_tra = t_pose_tra
        if bone_name in actor.face_drivers:
            apply_face_drivers(actor, bone_name, shape_data, local_rot, parent_world_rot, t_pose_rot)
        ec_rot = get_expression_counter_rotation(actor, bone_name, shape_data)
        set_bone_control(SC, clip, bone, time, ec_rot,
                         t_pose_rot, t_pose_tra, t_pose_sca,
                         local_rot, local_tra, local_sca)

        children = bone.GetChildren()
        for child in children:
            apply_world_fk_pose(actor, SC, clip, time, child, pose_data, shape_data,
                                t_pose_data, world_rot, world_tra, world_sca)


def calc_world(local_rot: RQuaternion, local_tra: RVector3, local_sca: RVector3,
               parent_world_rot: RQuaternion, parent_world_tra: RVector3, parent_world_sca: RVector3):
    world_rot = parent_world_rot.Multiply(local_rot)
    world_tra = parent_world_rot.MultiplyVector(local_tra * parent_world_sca) + parent_world_tra
    world_sca = local_sca
    return world_rot, world_tra, world_sca


def calc_local(world_rot: RQuaternion, world_tra: RVector3, world_sca: RVector3,
               parent_world_rot: RQuaternion, parent_world_tra: RVector3, parent_world_sca: RVector3):
    parent_world_rot_inv: RQuaternion = parent_world_rot.Conjugate()
    local_rot = parent_world_rot_inv.Multiply(world_rot)
    local_tra = parent_world_rot_inv.MultiplyVector(world_tra - parent_world_tra) / world_sca
    local_sca = world_sca
    return local_rot, local_tra, local_sca


def set_bone_transform(clip, bone, time,
                       t_pose_rot: RQuaternion, t_pose_tra: RVector3, t_pose_sca: RVector3,
                       local_rot: RQuaternion, local_tra: RVector3, local_sca: RVector3):
    transform_control: RTransformControl = clip.GetControl("Transform", bone)
    if transform_control:
        # get local transform relative to T-pose
        sca = local_sca / t_pose_sca
        tra = local_tra - t_pose_tra
        rot = local_rot.Multiply(t_pose_rot.Inverse())
        T: RTransform = RTransform(sca, rot, tra)
        transform_control.SetValue(time, T)


def set_bone_control(SC, clip, bone, time, ec_rot: RQuaternion,
                     t_pose_rot: RQuaternion, t_pose_tra: RVector3, t_pose_sca: RVector3,
                     local_rot: RQuaternion, local_tra: RVector3, local_sca: RVector3):
    clip_bone_control: RControl = clip.GetControl("Layer", bone)
    if clip_bone_control:
        # get local transform relative to T-pose
        # CC/iC doesn't support bone scaling in human animations? so use the t-pose scale
        sca = t_pose_sca #local_sca / t_pose_sca
        tra = local_tra - t_pose_tra
        # counteract expression rotations
        exp_local_rot = local_rot.Multiply(ec_rot)
        # get relative to t-pose
        rot = exp_local_rot.Multiply(t_pose_rot.Inverse())
        # apply to clip
        clip_data_block: RDataBlock = clip_bone_control.GetDataBlock()
        if clip_data_block:
            set_control_data(SC, clip_data_block, time, rot, tra, sca)


def set_ik_effector(SC: RISkeletonComponent, clip: RIClip, effector_type, time: RTime,
                    rot: RQuaternion, tra: RVector3, sca: RVector3):
    ik_effector = SC.GetEffector(effector_type)
    if ik_effector:
        clip_data_block = clip.GetDataBlock("Layer", ik_effector)
        if clip_data_block:
            set_control_data(SC, clip_data_block, time, rot, tra, sca)


def set_control_data(SC: RISkeletonComponent, data_block: RDataBlock, time: RTime,
                     rot: RQuaternion, tra: RVector3, sca: RVector3):
    rot_matrix: RMatrix3 = rot.ToRotationMatrix()
    x = y = z = 0
    euler = rot_matrix.ToEulerAngle(EEulerOrder_XYZ, x, y, z)
    data_block.GetControl("Rotation/RotationX").SetValue(time, euler[0])
    data_block.GetControl("Rotation/RotationY").SetValue(time, euler[1])
    data_block.GetControl("Rotation/RotationZ").SetValue(time, euler[2])
    if data_block.GetControl("Position/PositionX") is not None:
        data_block.GetControl("Position/PositionX").SetValue(time, tra.x)
        data_block.GetControl("Position/PositionY").SetValue(time, tra.y)
        data_block.GetControl("Position/PositionZ").SetValue(time, tra.z)
    if data_block.GetControl("Position/ScaleX") is not None:
        data_block.GetControl("Position/ScaleX").SetValue(time, sca.x)
        data_block.GetControl("Position/ScaleY").SetValue(time, sca.y)
        data_block.GetControl("Position/ScaleZ").SetValue(time, sca.z)


def set_transform_control(time, obj: RIObject, loc: RVector3, rot: RQuaternion, sca: RVector3):
    control = obj.GetControl("Transform")
    if control:
        transform = RTransform(sca, rot, loc)
        control.SetValue(time, transform)


def apply_face_drivers(actor: LinkActor, bone_name, shape_data,
                       local_rot: RQuaternion, parent_world_rot: RQuaternion, t_pose_rot: RQuaternion):

    expressions = actor.face_drivers[bone_name]
    face_rotations = actor.face_rotations

    # forward is -y
    forward: RVector3 = RVector3(0, -1, 0)
    t_pose_rot_inv: RQuaternion = t_pose_rot.Inverse()
    # local pose rotation
    local_pose: RQuaternion = t_pose_rot_inv.Multiply(local_rot)
    # pose bone vector
    pose_dir: RVector3 = local_pose.MultiplyVector(forward)

    for expr in expressions:
        if expr in actor.face_rotations and bone_name in actor.face_rotations[expr]:
            ERQ: RQuaternion = face_rotations[expr][bone_name]
            expr_index = actor.expressions[expr]
            # expression bone vector
            expr_dir: RVector3 = ERQ.MultiplyVector(forward)
            # expression axis
            expr_axis: RVector3 = expr_dir.Cross(forward)
            # angles for the pose and expression vectors on this axis
            angle_pose = cc.signed_angle_between_vectors(forward, pose_dir, expr_axis)
            angle_expr = cc.signed_angle_between_vectors(forward, expr_dir, expr_axis)
            # expression weight to produce this pose rotation
            angle_fac = min(1.5, max(0, angle_pose/angle_expr))
            shape_data[expr_index] = min(1.5, max(-1.5, angle_fac))
            #print(f"{bone_name}:{expr} {cc.dumps_quaternion_xyz(local_pose)} / {cc.dumps_quaternion_xyz(ERQ)} // {cc.dumps_vector3(pose_dir)} / {cc.dumps_vector3(expr_dir)} - {angle_pose:.3f} / {angle_expr:.3f} / {angle_fac:.3f}")


def apply_shapes(actor: LinkActor, time: RTime, pose_data, shape_data, t_pose_data):
    FC = actor.get_face_component()
    VC = actor.get_viseme_component()
    MC = actor.get_morph_component()

    if FC and actor.expressions:
        expressions = [expression for expression in actor.expressions]
        strengths = [shape_data[idx] for idx in actor.expressions.values()]
        #FC.BeginKeyEditing()
        FC.AddExpressivenessKey(time, 1.0)
        res = FC.AddExpressionKeys(time, expressions, strengths, RTime.FromValue(1))
        if res.IsError():
            utils.log_error("Failed to set expressions")
        #FC.EndKeyEditing()

    # can only have one active viseme key at a time?
    # disabled for now: viseme's need their own system...
    if False and VC and actor.visemes:
        max_id = -1
        max_weight = 0
        for visime_id, shape_index in actor.visemes.items():
            weight = shape_weights[shape_index]
            weight = utils.clamp(weight) * 100
            if weight > max_weight:
                max_id = visime_id
                max_weight = weight
        if max_id > -1:
            viseme_key = RVisemeKey()
            viseme_key.SetID(max_id)
            viseme_key.SetWeight(max_weight)
            viseme_key.SetTime(time)
            res = VC.AddVisemeKey(viseme_key)
            if res.IsError():
                utils.log_error("Failed to set visemes")






class LinkService(QObject):
    timer: QTimer = None
    server_sock: socket.socket = None
    client_sock: socket.socket = None
    server_sockets = []
    client_sockets = []
    empty_sockets = []
    client_ip: str = "127.0.0.1"
    client_port: int = BLENDER_PORT
    is_listening: bool = False
    is_connected: bool = False
    is_connecting: bool = False
    ping_timer: float = 0
    keepalive_timer: float = 0
    time: float = 0
    is_data: bool = False
    is_sequence: bool = False
    loop_rate: float = 0.0
    loop_count: int = 0
    # Signals
    listening = Signal()
    connecting = Signal()
    connected = Signal()
    lost_connection = Signal()
    server_stopped = Signal()
    client_stopped = Signal()
    received = Signal(int, bytearray)
    accepted = Signal(str, int)
    sent = Signal()
    changed = Signal()
    sequence = Signal()
    #
    sequence_send_count: int = 4
    # local props
    local_app: str = None
    local_version: str = None
    local_path: str = None
    # remote props
    remote_app: str = None
    remote_version: str = None
    remote_path: str = None
    remote_addon: str = None

    def __init__(self):
        QObject.__init__(self)
        atexit.register(self.service_stop)

    def __enter__(self):
        return self

    def __exit__(self):
        self.service_stop()

    def start_server(self):
        if not self.server_sock:
            try:
                self.keepalive_timer = HANDSHAKE_TIMEOUT_S
                self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_sock.settimeout(SOCKET_TIMEOUT)
                self.server_sock.bind(('', RL_PORT))
                self.server_sock.listen(5)
                #self.server_sock.setblocking(True)
                self.server_sockets = [self.server_sock]
                self.is_listening = True
                utils.log_info(f"Listening on TCP *:{RL_PORT}")
                self.listening.emit()
                self.changed.emit()
            except:
                self.server_sock = None
                self.server_sockets = []
                self.is_listening = True
                utils.log_error(f"Unable to start server on TCP *:{RL_PORT}")

    def stop_server(self):
        if self.server_sock:
            utils.log_info(f"Closing Server Socket")
            try:
                self.server_sock.shutdown()
                self.server_sock.close()
            except:
                pass
        self.is_listening = False
        self.server_sock = None
        self.server_sockets = []
        self.server_stopped.emit()
        self.changed.emit()

    def start_timer(self):
        self.time = time.time()
        if not self.timer:
            self.timer = QTimer(self)
            self.timer.setInterval(TIMER_INTERVAL)
            self.timer.timeout.connect(self.loop)
        self.timer.start()
        utils.log_info(f"Service timer started")

    def stop_timer(self):
        if self.timer:
            self.timer.stop()
            utils.log_info(f"Service timer stopped")

    def try_start_client(self, host, port):
        if not self.client_sock:
            utils.log_info(f"Attempting to connect")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(SOCKET_TIMEOUT)
                sock.connect((host, port))
                #sock.setblocking(False)
                self.is_connected = False
                self.is_connecting = True
                self.client_sock = sock
                self.client_sockets = [sock]
                self.client_ip = self.host_ip
                self.client_port = self.host_port
                self.keepalive_timer = KEEPALIVE_TIMEOUT_S
                self.ping_timer = PING_INTERVAL_S
                utils.log_info(f"Connecting to data-link server on {self.host_ip}:{self.host_port}")
                self.send_hello()
                self.connecting.emit()
                self.changed.emit()
                return True
            except:
                self.client_sock = None
                self.client_sockets = []
                self.is_connected = False
                self.is_connecting = False
                utils.log_info(f"Client socket connect failed!")
                return False
        else:
            utils.log_info(f"Client already connected!")
            return True

    def send_hello(self):
        self.local_app = RApplication.GetProductName()
        self.local_version = RApplication.GetProductVersion()
        prefs.check_paths(quiet=True, create=True)
        self.local_path = prefs.DATALINK_FOLDER
        json_data = {
            "Application": self.local_app,
            "Version": self.local_version,
            "Path": self.local_path,
            "Plugin": vars.VERSION,
            "Exe": RApplication.GetProgramPath()
        }
        self.send(OpCodes.HELLO, encode_from_json(json_data))

    def stop_client(self):
        if self.client_sock:
            utils.log_info(f"Closing Client Socket")
            try:
                self.client_sock.shutdown()
                self.client_sock.close()
            except:
                pass
        self.is_connected = False
        self.is_connecting = False
        self.client_sock = None
        self.client_sockets = []
        if self.listening:
            self.keepalive_timer = HANDSHAKE_TIMEOUT_S
        self.client_stopped.emit()
        self.changed.emit()

    def has_client_sock(self):
        if self.client_sock and (self.is_connected or self.is_connecting):
            return True
        else:
            return False

    def recv(self):
        self.is_data = False
        if self.has_client_sock():
            try:
                r,w,x = select.select(self.client_sockets, self.empty_sockets, self.empty_sockets, 0)
            except Exception as e:
                utils.log_error("Client socket recv:select failed!", e)
                self.client_lost()
                return
            count = 0
            while r:
                op_code = None
                try:
                    header = self.client_sock.recv(8)
                    if header == 0:
                        utils.log_warn("Socket closed by client")
                        self.client_lost()
                        return
                except Exception as e:
                    utils.log_error("Client socket recv:recv header failed!", e)
                    self.client_lost()
                    return
                if header and len(header) == 8:
                    op_code, size = struct.unpack("!II", header)
                    data = None
                    if size > 0:
                        data = bytearray()
                        while size > 0:
                            chunk_size = min(size, MAX_CHUNK_SIZE)
                            try:
                                chunk = self.client_sock.recv(chunk_size)
                            except Exception as e:
                                utils.log_error("Client socket recv:recv chunk failed!", e)
                                self.client_lost()
                                return
                            data.extend(chunk)
                            size -= len(chunk)
                    self.parse(op_code, data)
                    self.received.emit(op_code, data)
                    count += 1
                self.is_data = False
                if op_code == OpCodes.SEQUENCE_FRAME:
                    self.is_data = True
                    return
                if op_code == OpCodes.POSE_FRAME:
                    self.is_data = False
                    return
                # parse may have received a disconnect notice
                if not self.has_client_sock():
                    return
                try:
                    r,w,x = select.select(self.client_sockets, self.empty_sockets, self.empty_sockets, 0)
                except Exception as e:
                    utils.log_error("Client socket recv:select (reselect) failed!", e)
                    self.client_lost()
                    return
                if r:
                    self.is_data = True
                    if count >= MAX_RECEIVE or op_code == OpCodes.NOTIFY:
                        return

    def accept(self):
        if self.server_sock and self.is_listening:
            r,w,x = select.select(self.server_sockets, self.empty_sockets, self.empty_sockets, 0)
            while r:
                try:
                    sock, address = self.server_sock.accept()
                except:
                    utils.log_error("Server socket accept failed!")
                    self.service_lost()
                    return
                self.client_sock = sock
                self.client_sockets = [sock]
                self.client_ip = address[0]
                self.client_port = address[1]
                self.is_connected = False
                self.is_connecting = True
                self.keepalive_timer = KEEPALIVE_TIMEOUT_S
                self.ping_timer = PING_INTERVAL_S
                utils.log_info(f"Incoming connection received from: {address[0]}:{address[1]}")
                self.send_hello()
                self.accepted.emit(self.client_ip, self.client_port)
                self.changed.emit()
                r,w,x = select.select(self.server_sockets, self.empty_sockets, self.empty_sockets, 0)

    def parse(self, op_code, data):
        self.keepalive_timer = KEEPALIVE_TIMEOUT_S
        if op_code == OpCodes.HELLO:
            utils.log_info(f"Hello Received")
            if data:
                json_data = decode_to_json(data)
                self.remote_app = json_data["Application"]
                self.remote_version = json_data["Version"]
                self.remote_path = json_data["Path"]
                self.remote_addon = json_data.get("Addon", "x.x.x")
                utils.log_info(f"Connected to: {self.remote_app} {self.remote_version} / {self.remote_addon}")
                utils.log_info(f"Using file path: {self.remote_path}")
            self.service_initialize()
            if data:
                self.changed.emit()
        elif op_code == OpCodes.PING:
            utils.log_info(f"Ping Received")
            pass
        elif op_code == OpCodes.STOP:
            utils.log_info(f"Termination Received")
            self.service_stop()
        elif op_code == OpCodes.DISCONNECT:
            utils.log_info(f"Disconnection Received")
            self.service_recv_disconnected()

    def service_start(self, host, port):
        if not self.is_listening:
            self.start_timer()
            if SERVER_ONLY:
                self.start_server()
            else:
                if not self.try_start_client(host, port):
                    if not CLIENT_ONLY:
                        self.start_server()

    def service_initialize(self):
        if self.is_connecting:
            self.is_connecting = False
            self.is_connected = True
            self.connected.emit()
            self.changed.emit()

    def service_recv_disconnected(self):
        self.stop_client()

    def service_stop(self):
        self.send(OpCodes.STOP)
        self.stop_client()
        self.stop_timer()
        self.stop_server()

    def service_lost(self):
        self.lost_connection.emit()
        self.stop_timer()
        self.stop_client()
        self.stop_server()

    def client_lost(self):
        self.lost_connection.emit()
        self.stop_client()

    def loop(self):
        try:
            current_time = time.time()
            delta_time = current_time - self.time
            self.time = current_time
            if delta_time > 0:
                rate = 1.0 / delta_time
                self.loop_rate = self.loop_rate * 0.75 + rate * 0.25
                #if self.loop_count % 100 == 0:
                #    utils.log_info(f"LinkServer loop timer rate: {self.loop_rate}")
                self.loop_count += 1

            if self.is_connected:
                self.ping_timer -= delta_time
                self.keepalive_timer -= delta_time

                if USE_PING and self.ping_timer <= 0:
                    self.send(OpCodes.PING)

                if USE_KEEPALIVE and self.keepalive_timer <= 0:
                    utils.log_info("lost connection!")
                    self.service_stop()

            elif self.is_listening:
                self.keepalive_timer -= delta_time

                if USE_KEEPALIVE and self.keepalive_timer <= 0:
                    utils.log_info("no connection within time limit!")
                    self.service_stop()

            # accept incoming connections
            self.accept()

            # receive client data
            self.recv()

            # run anything in sequence
            if prefs.DATALINK_FRAME_SYNC:
                self.sequence.emit()
            else:
                for i in range(0, self.sequence_send_count):
                    self.sequence.emit()

        except Exception as e:
            utils.log_error("LinkService timer loop crash!")
            traceback.print_exc()
            return TIMER_INTERVAL


    def send(self, op_code, binary_data = None):
        try:
            if self.client_sock and (self.is_connected or self.is_connecting):
                data_length = len(binary_data) if binary_data else 0
                header = struct.pack("!II", op_code, data_length)
                data = bytearray()
                data.extend(header)
                if binary_data:
                    data.extend(binary_data)
                try:
                    self.client_sock.sendall(data)
                except Exception as e:
                    utils.log_error("Client socket sendall failed!")
                    self.client_lost()
                    return
                self.ping_timer = PING_INTERVAL_S
                self.sent.emit()

        except:
            utils.log_error("LinkService send failed!")
            traceback.print_exc()

    def start_sequence(self, func=None):
        self.is_sequence = True
        if func:
            self.sequence.connect(func)
        else:
            try: self.sequence.disconnect()
            except: pass
        self.changed.emit()
        self.timer.setInterval(1000/60)

    def stop_sequence(self):
        self.is_sequence = False
        self.timer.setInterval(TIMER_INTERVAL)
        try: self.sequence.disconnect()
        except: pass
        self.changed.emit()

    def update_sequence(self, rate, count, delta_frames):
        self.is_sequence = True
        if rate is None:
            self.timer.setInterval(0)
            self.sequence_send_count = count
        else:
            interval = 1000/rate
            self.timer.setInterval(interval)
            self.sequence_send_count = count
            if self.loop_count % 30 == 0:
                print(f"rate: {rate} count: {count} delta_frames: {delta_frames}")


class LinkEventCallback(REventCallback):

    target = None

    def __init__(self, target):
       REventCallback.__init__(self)
       self.target = target

    #def OnCurrentTimeChanged(self, fTime):
    #    utils.log_info('Current time:' + str(fTime))

    def OnObjectSelectionChanged(self):
        global LINK
        REventCallback.OnObjectSelectionChanged(self)
        if self.target and self.target.is_shown():
            self.target.update_ui()


class DataLink(QObject):
    window: RIDockWidget = None
    host_name: str = "localhost"
    motion_prefix: str = ""
    use_fake_user: bool = True
    host_ip: str = "127.0.0.1"
    host_port: int = BLENDER_PORT
    target: str = "Blender"
    # Callback
    callback: LinkEventCallback = None # type: ignore
    callback_id = None
    # UI
    label_header: QLabel = None
    button_link: QPushButton = None
    textbox_host: QLineEdit = None
    combo_target: QComboBox = None
    context_frame: QVBoxLayout = None
    info_label_name: QLabel = None
    info_label_type: QLabel = None
    info_label_link_id: QLabel = None
    #
    button_send: QPushButton = None
    button_rigify: QPushButton = None
    button_pose: QPushButton = None
    button_sequence: QPushButton = None
    button_animation: QPushButton = None
    button_update_replace: QPushButton = None
    button_morph: QPushButton = None
    button_morph_update: QPushButton = None
    button_sync_lights: QPushButton = None
    button_sync_camera: QPushButton = None
    toggle_use_fake_user: QPushButton = None
    #
    icon_avatar: QIcon = None
    icon_prop: QIcon = None
    icon_light: QIcon = None
    icon_camera: QIcon = None
    icon_all: QIcon = None
    icon_fake_user_off: QIcon = None
    icon_fake_user_on: QIcon = None
    icon_replace_avatar: QIcon = None
    icon_replace_clothing: QIcon = None
    # Service
    service: LinkService = None
    # Data
    data = LinkData()


    def __init__(self):
        QObject.__init__(self)
        self.create_window()
        atexit.register(self.on_exit)

    def show(self):
        self.window.Show()
        self.show_link_state()

    def hide(self):
        self.window.Hide()

    def is_shown(self):
        return self.window.IsVisible()

    def create_window(self):
        self.window, window_layout = qt.window("Blender DataLink", width=440, height=524, show_hide=self.on_show_hide)

        scroll, layout = qt.scroll_area(window_layout, vertical=True, horizontal=False)

        self.icon_avatar = qt.get_icon("Character.png")
        self.icon_prop = qt.get_icon("Prop.png")
        self.icon_light = qt.get_icon("Light.png")
        self.icon_camera = qt.get_icon("Camera.png")
        self.icon_all = qt.get_icon("Actor.png")
        self.icon_fake_user_off = qt.get_icon("BlenderFakeUserOff.png")
        self.icon_fake_user_on = qt.get_icon("BlenderFakeUserOn.png")
        self.icon_replace_avatar = qt.get_icon("FullBodyMorphSkin.png")
        self.icon_replace_clothing = qt.get_icon("Clothing.png")

        grid = qt.grid(layout)
        grid.setColumnStretch(1, 3)
        qt.label(grid, f"DataLink ({vars.VERSION}):", row=0, col=0, style=qt.STYLE_TITLE)
        self.label_header = qt.label(grid, f"Not Connected",
                                     row=0, col=1, style=qt.STYLE_RL_BOLD, no_size=True)
        qt.label(grid, f"Working Folder:", row=1, col=0, style=qt.STYLE_TITLE)
        self.label_folder = qt.label(grid, f"{self.get_remote_folder()}",
                                     row=1, col=1, style=qt.STYLE_RL_BOLD, no_size=True)

        row = qt.row(layout)
        self.textbox_host = qt.textbox(row, self.host_name, update=self.update_host)
        self.combo_target = qt.combobox(row, "", options=["Blender", "Unity"], update=self.update_target)

        #qt.spacing(layout, 10)

        grid = qt.grid(layout)
        grid.setColumnStretch(2, 0)
        qt.label(grid, f"Action Name Prefix:", row=0, col=0, style=qt.STYLE_TITLE)
        self.textbox_motion_prefix = qt.textbox(grid, self.motion_prefix,
                                                     row=0, col=1, update=self.update_motion_prefix)
        self.toggle_use_fake_user = qt.button(grid, "", self.update_toggle_use_fake_user,
                                              icon=self.icon_fake_user_on if self.use_fake_user else self.icon_fake_user_off,
                                              toggle=True, value=self.use_fake_user,
                                              style=qt.STYLE_BLENDER_TOGGLE, icon_size=22, width=32,
                                              row=0, col=2)

        qt.spacing(layout, 10)

        self.label_status = qt.label(layout, "...", style=qt.STYLE_RL_DESC, no_size=True)

        qt.spacing(layout, 10)

        grid = qt.grid(layout)
        grid.setColumnStretch(0, 2)
        self.button_link = qt.button(grid, "Listen", self.link_start, row=0, col=0, toggle=True, value=False, height=48)
        qt.button(grid, "Stop", self.link_stop, row=0, col=1, width=64, height=48)

        qt.label(layout, "Send:")
        grid = qt.grid(layout)
        grid.setColumnStretch(0,1)
        grid.setColumnStretch(1,1)
        align_width = 150
        self.button_send = qt.icon_button(grid, "Send Character", self.send_actor,
                                     row=0, col=0, icon=self.icon_avatar,
                                     width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT,
                                     icon_size=48, align_width=align_width)
        self.button_rigify = qt.icon_button(grid, "Rigify Character", self.send_rigify_request,
                                       row=0, col=1, icon="PostEffect.png",
                                       width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT,
                                       icon_size=48, align_width=align_width)
        self.button_pose = qt.icon_button(grid, "Send Pose", self.send_pose,
                                     row=1, col=0, icon="Pose.png",
                                     width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT,
                                     icon_size=48, align_width=align_width)
        self.button_animation = qt.icon_button(grid, "Send Motion", self.send_motion_export,
                                          row=1, col=1, icon="Animation.png",
                                          width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT,
                                          icon_size=48, align_width=align_width)
        self.button_sequence = qt.icon_button(grid, "Live Sequence", self.send_sequence,
                                         row=2, col=0, icon="Motion.png",
                                         width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT,
                                         icon_size=48, align_width=align_width)

        if cc.is_cc():
            self.button_update_replace = qt.icon_button(grid, "Update / Replace", self.send_update_replace,
                                                   row=2, col=1, icon=self.icon_replace_avatar,
                                                   width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT,
                                                   icon_size=48, align_width=align_width)

        if cc.is_cc():
            qt.label(layout, "Morph:")
            grid = qt.grid(layout)
            grid.setColumnStretch(0,1)
            grid.setColumnStretch(1,1)
            self.button_morph = qt.icon_button(grid, "Send Morph", self.send_morph,
                                          row=0, col=0, icon="FullBodyMorph.png",
                                          width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT,
                                          icon_size=48, align_width=align_width)
            self.button_morph_update = qt.icon_button(grid, "Update Morph", self.send_morph_update,
                                                 row=0, col=1, icon="Morph.png",
                                                 width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT,
                                                 icon_size=48, align_width=align_width)

        qt.label(layout, "Lights & Camera:")
        grid = qt.grid(layout)
        grid.setColumnStretch(0,1)
        grid.setColumnStretch(1,1)
        self.button_sync_lights = qt.icon_button(grid, "Sync Lights", self.sync_lights,
                                            row=0, col=0, icon=self.icon_light,
                                            width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT,
                                            icon_size=48, align_width=align_width)
        self.button_sync_camera = qt.icon_button(grid, "Sync Camera", self.send_camera_sync,
                                            row=0, col=1, icon=self.icon_camera,
                                            width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT,
                                            icon_size=48, align_width=align_width)

        qt.stretch(layout, 20)

        self.context_frame, frame_layout = qt.frame(layout)
        grid = qt.grid(frame_layout)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(3, 2)
        qt.label(grid, "Name", style=qt.STYLE_BOLD, row=0, col=0)
        self.info_label_name = qt.label(grid, "", row=0, col=1, no_size=True)
        qt.label(grid, "Type", style=qt.STYLE_BOLD, row=0, col=2)
        self.info_label_type = qt.label(grid, "", row=0, col=3, no_size=True)
        qt.label(grid, "Link ID", style=qt.STYLE_BOLD, row=1, col=0)
        self.info_label_link_id = qt.label(grid, "", row=1, col=1, no_size=True)

        if vars.DEV:
            qt.button(layout, "DEBUG", self.send_debug)
            qt.button(layout, "TEST", test)
            #
            #qt.button(layout, "Load Test", tests.load_test)
            #qt.button(layout, "IK Effectors", tests.end_effectors)
            #qt.button(layout, "Print", tests.bone_tree)
            #qt.button(layout, "Clip Name", tests.clip_test)
            #qt.button(layout, "Prop Clip", tests.prop_clip_test)

        self.show_link_state()

    def on_show_hide(self, visible):
        if visible:
            qt.toggle_toolbar_action("Blender Pipeline Toolbar", "Blender DataLink", True)
            if not self.callback_id:
                self.callback = LinkEventCallback(self)
                self.callback_id = REventHandler.RegisterCallback(self.callback)
        else:
            qt.toggle_toolbar_action("Blender Pipeline Toolbar", "Blender DataLink", False)
            if self.callback_id:
                REventHandler.UnregisterCallback(self.callback_id)
                self.callback = None
                self.callback_id = None

    def on_exit(self):
        if self.callback_id:
            REventHandler.UnregisterCallback(self.callback_id)
            self.callback_id = None

    def update_ui(self):
        avatar: RIAvatar = None
        prop: RIProp = None
        light: RILight = None
        camera: RICamera = None

        num_avatars = 0
        num_standard = 0
        num_nonstandard = 0
        num_props = 0
        num_lights = 0
        num_cameras = 0
        num_total = 0
        num_posable = 0
        num_types = 0
        num_rigable = 0

        selected = RScene.GetSelectedObjects()
        cc.get_selected_actor_objects()
        if selected:
            first = selected[0]
            prop_or_avatar = cc.find_parent_avatar_or_prop(first)
            T = type(first)
            if prop_or_avatar:
                T = type(prop_or_avatar)
            if T is RIAvatar or T is RILightAvatar:
                avatar = prop_or_avatar
            elif T is RIProp or T is RIMDProp:
                prop = prop_or_avatar
            elif T is RILight or T is RISpotLight or T is RIPointLight or T is RIDirectionalLight:
                light = first
            elif T is RICamera:
                camera = first
            else:
                first = None

        props_and_avatars = []
        avatars = []
        props = []
        for obj in selected:
            T = type(obj)
            prop_or_avatar = cc.find_parent_avatar_or_prop(obj)
            if prop_or_avatar:
                T = type(prop_or_avatar)
            if (T is RIAvatar or T is RILightAvatar) and prop_or_avatar not in props_and_avatars:
                num_avatars += 1
                props_and_avatars.append(prop_or_avatar)
                avatars.append(prop_or_avatar)
                if (prop_or_avatar.GetAvatarType() == EAvatarType_Standard or
                    prop_or_avatar.GetAvatarType() == EAvatarType_StandardSeries):
                    num_standard += 1
                else:
                    num_nonstandard += 1
                generation = prop_or_avatar.GetGeneration()
                if (prop_or_avatar.GetAvatarType() == EAvatarType_Standard or
                    prop_or_avatar.GetAvatarType() == EAvatarType_StandardSeries or
                    generation == EAvatarGeneration_AccuRig or
                    generation == EAvatarGeneration_ActorBuild or
                    generation == EAvatarGeneration_ActorScan or
                    generation == EAvatarGeneration_CC_G3_Plus_Avatar or
                    generation == EAvatarGeneration_CC_G3_Avatar or
                    generation == EAvatarGeneration_CC_Game_Base_Multi or
                    generation == EAvatarGeneration_CC_Game_Base_One):
                    num_rigable += 1

            elif (T is RIProp or T is RIMDProp) and prop_or_avatar not in props_and_avatars:
                props_and_avatars.append(prop_or_avatar)
                props.append(prop_or_avatar)
                num_props += 1
            elif T is RILight or T is RISpotLight or T is RIPointLight or T is RIDirectionalLight:
                num_lights += 1
            elif T is RICamera:
                num_cameras += 1

        num_total = num_avatars + num_props + num_lights + num_cameras
        num_posable = num_avatars + num_props
        num_sendable = num_avatars + num_props
        num_types = min(1,num_avatars) + min(1, num_props) + min(1, num_lights) + min(1, num_cameras)

        # button text

        type_name = "All"
        icon = self.icon_all
        if num_types > 1:
            type_name = "All"
        elif num_avatars == 1:
            type_name = "Avatar"
            icon = self.icon_avatar
        elif num_avatars > 1:
            type_name = "Avatars"
            icon = self.icon_avatar
        elif num_props == 1:
            type_name = "Prop"
            icon = self.icon_prop
        elif num_props > 1:
            type_name = "Props"
            icon = self.icon_prop
        elif num_lights == 1:
            type_name = "Light"
            icon = self.icon_light
        elif num_lights > 1:
            type_name = "Lights"
            icon = self.icon_light
        elif num_cameras == 1:
            type_name = "Camera"
            icon = self.icon_camera
        elif num_cameras > 1:
            type_name = "Cameras"
            icon = self.icon_camera
        self.button_send.setText(f"Send {type_name}")
        self.button_send.setIcon(icon)
        if num_posable > 1:
            self.button_pose.setText(f"Send Poses")
        else:
            self.button_pose.setText(f"Send Pose")

        if selected and avatars:
            icon = self.icon_replace_clothing
            for obj in selected:
                if obj in avatars:
                    icon = self.icon_replace_avatar
            if self.button_update_replace:
                self.button_update_replace.setIcon(icon)

        # button enable

        qt.disable(self.button_send, self.button_rigify,
                   self.button_pose, self.button_sequence,
                   self.button_animation, self.button_update_replace,
                   self.button_morph, self.button_morph_update,
                   self.button_sync_lights, self.button_sync_camera)

        if self.is_connected():
            if num_posable > 0:
                qt.enable(self.button_pose, self.button_sequence, self.button_animation)
            if num_sendable > 0:
                qt.enable(self.button_send, self.button_update_replace)
            if num_standard > 0:
                qt.enable(self.button_morph, self.button_morph_update)
            if num_rigable > 0:
                qt.enable(self.button_rigify)
            qt.enable(self.button_sync_lights, self.button_sync_camera)

        # context info

        if avatar:
            self.context_frame.show()
            self.info_label_name.setText(avatar.GetName())
            avatar_type = avatar.GetAvatarType()
            type_name = "Unknown"
            if avatar_type in vars.AVATAR_TYPES:
                type_name = vars.AVATAR_TYPES[avatar_type]
            self.info_label_type.setText(type_name)
            link_id = cc.get_link_id(avatar)
            self.info_label_link_id.setText(link_id)
            if cc.has_link_id(avatar):
                self.info_label_link_id.setStyleSheet(qt.STYLE_RL_BOLD)
            else:
                self.info_label_link_id.setStyleSheet(qt.STYLE_NONE)
        elif prop:
            self.context_frame.show()
            self.info_label_name.setText(prop.GetName())
            self.info_label_type.setText("Prop")
            link_id = cc.get_link_id(prop)
            self.info_label_link_id.setText(link_id)
            if cc.has_link_id(prop):
                self.info_label_link_id.setStyleSheet(qt.STYLE_RL_BOLD)
            else:
                self.info_label_link_id.setStyleSheet(qt.STYLE_NONE)
        elif light:
            self.context_frame.show()
            self.info_label_name.setText(light.GetName())
            self.info_label_type.setText("Light")
            link_id = cc.get_link_id(light)
            self.info_label_link_id.setText(link_id)
            if cc.has_link_id(light):
                self.info_label_link_id.setStyleSheet(qt.STYLE_RL_BOLD)
            else:
                self.info_label_link_id.setStyleSheet(qt.STYLE_NONE)
        elif camera:
            self.context_frame.show()
            self.info_label_name.setText(camera.GetName())
            self.info_label_type.setText("Camera")
            link_id = cc.get_link_id(camera)
            self.info_label_link_id.setText(link_id)
            if cc.has_link_id(camera):
                self.info_label_link_id.setStyleSheet(qt.STYLE_RL_BOLD)
            else:
                self.info_label_link_id.setStyleSheet(qt.STYLE_NONE)
        else:
            self.context_frame.hide()

        if self.is_sequence_running():
            qt.enable(self.button_sequence)

        return

    def update_link_status(self, text):
        self.label_status.setText(text)
        #utils.log_info(text)

    def update_host(self):
        if self.textbox_host:
            self.host_name = self.textbox_host.text()
            try:
                self.host_ip = socket.gethostbyname(self.host_name)
            except:
                self.host_ip = "127.0.0.1"
            utils.log_info(f"{self.host_name} ({self.host_ip})")

    def update_motion_prefix(self):
        self.motion_prefix = self.textbox_motion_prefix.text()

    def update_toggle_use_fake_user(self):
        if self.toggle_use_fake_user.isChecked():
            self.toggle_use_fake_user.setIcon(self.icon_fake_user_on)
        else:
            self.toggle_use_fake_user.setIcon(self.icon_fake_user_off)
        self.use_fake_user = self.toggle_use_fake_user.isChecked()


    def update_target(self):
        if self.combo_target:
            self.target = self.combo_target.currentText()
            if self.target == "Blender":
                self.host_port = BLENDER_PORT
            elif self.target == "Unity":
                self.host_port = UNITY_PORT

    def set_target(self, target):
        self.combo_target.setCurrentText(target)

    def set_host(self, host_name):
        self.textbox_host.setText(host_name)
        self.host_name = host_name

    def show_link_state(self):

        if self.is_connected():
            self.textbox_host.setEnabled(False)
            self.combo_target.setEnabled(False)
            self.button_link.setStyleSheet(qt.STYLE_BUTTON_ACTIVE)
            self.button_link.setText("Linked")
            self.label_header.setText(f"Connected to {self.service.remote_app} {self.service.remote_version} ({self.service.remote_addon})")
            self.label_folder.setText(f"{self.get_remote_folder()}")
        elif self.is_listening():
            self.textbox_host.setEnabled(False)
            self.combo_target.setEnabled(False)
            self.button_link.setStyleSheet(qt.STYLE_BUTTON_WAITING)
            self.button_link.setText("Listening ...")
            self.label_header.setText("Waiting for Connection")
            self.label_folder.setText(f"None")
        else:
            self.textbox_host.setEnabled(True)
            self.combo_target.setEnabled(True)
            self.button_link.setStyleSheet(qt.STYLE_BUTTON)
            if SERVER_ONLY:
                self.button_link.setText("Start Server")
            else:
                self.button_link.setText("Connect")
            self.label_header.setText(f"Not Connected")
            self.label_folder.setText(f"None")

        if self.is_sequence_running():
            self.button_sequence.setText("Stop Sequence")
            self.button_sequence.toggleOn()
        else:
            self.button_sequence.setText("Live Sequence")
            self.button_sequence.toggleOff()

        self.update_ui()

    def is_connected(self):
        if self.service:
            return self.service.is_connected
        else:
            return False

    def is_listening(self):
        if self.service:
            return self.service.is_listening
        else:
            return False

    def link_start(self):
        if not self.service:
            self.service = LinkService()
            self.service.changed.connect(self.show_link_state)
            self.service.received.connect(self.parse)
            self.service.connected.connect(self.on_connected)
        self.service.service_start(self.host_ip, self.host_port)

    def link_stop(self):
        if self.service:
            self.service.service_stop()

    def link_disconnect(self):
        if self.service:
            self.service.service_disconnect()

    def parse(self, op_code, data):

        if op_code == OpCodes.DEBUG:
            self.receive_debug(data)

        if op_code == OpCodes.NOTIFY:
            self.receive_notify(data)

        if op_code == OpCodes.TEMPLATE:
            self.receive_character_template(data)

        if op_code == OpCodes.POSE:
            self.receive_pose(data)

        if op_code == OpCodes.POSE_FRAME:
            self.receive_pose_frame(data)

        if op_code == OpCodes.SEQUENCE:
            self.receive_sequence(data)

        if op_code == OpCodes.SEQUENCE_FRAME:
            self.receive_sequence_frame(data)

        if op_code == OpCodes.SEQUENCE_END:
            self.receive_sequence_end(data)

        if op_code == OpCodes.SEQUENCE_ACK:
            self.receive_sequence_ack(data)

        if op_code == OpCodes.CHARACTER:
            self.receive_character_import(data)

        if op_code == OpCodes.MORPH:
            self.receive_morph(data)

        if op_code == OpCodes.REPLACE_MESH:
            self.receive_replace_mesh(data)

        if op_code == OpCodes.MATERIALS:
            self.receive_material_update(data)

        if op_code == OpCodes.CAMERA_SYNC:
            self.receive_camera_sync(data)

        if op_code == OpCodes.FRAME_SYNC:
            self.receive_frame_sync(data)

    def on_connected(self):
        self.update_ui()
        self.send_notify("Connected")

    def send(self, op_code, data=None):
        if self.is_connected():
            self.service.send(op_code, data)

    def is_sequence_running(self):
        return self.data.sequence_active and self.service.is_sequence

    def start_sequence(self, func=None):
        if self.is_connected():
            self.data.sequence_active = True
            self.service.start_sequence(func=func)

    def stop_sequence(self):
        if self.is_connected():
            self.data.sequence_active = False
            self.service.stop_sequence()

    def update_sequence(self, rate, count, delta_frames):
        if self.is_connected():
            self.service.update_sequence(rate, count, delta_frames)

    def send_notify(self, message):
        notify_json = { "message": message }
        self.send(OpCodes.NOTIFY, encode_from_json(notify_json))

    def send_debug(self):
        self.send(OpCodes.DEBUG)

    def receive_notify(self, data):
        notify_json = decode_to_json(data)
        self.update_link_status(notify_json["message"])

    def receive_debug(self, data):
        debug_json = None
        if data:
            debug_json = decode_to_json(data)
        debug(debug_json)

    def get_remote_folder(self):
        if self.service:
            remote_path = self.service.remote_path
            local_path = self.service.local_path
            if remote_path:
                export_folder = remote_path
            else:
                export_folder = local_path
            return export_folder
        else:
            return ""

    def get_export_path(self, folder_name, file_name, unique=True):
        if self.service:
            if self.service.remote_path:
                export_folder = utils.make_sub_folder(self.service.remote_path, "imports")
                if not export_folder:
                    qt.message_box("Path Error", f"Unable to create remote export path: {self.service.remote_path}\\imports")
            else:
                export_folder = utils.make_sub_folder(self.service.local_path, "imports")
                if not export_folder:
                    qt.message_box("Path Error", f"Unable to create local export path:\n"
                                                 f"      {self.service.local_path}\\imports\n\n"
                                                  "Please check DataLink folder path.")
                    prefs.get_preferences().show()

            if not export_folder:
                return ""

            if unique:
                character_export_folder = utils.get_unique_folder_path(export_folder, folder_name, create=True)
            else:
                character_export_folder = os.path.join(export_folder, folder_name)
                if not os.path.exists(character_export_folder):
                    os.makedirs(character_export_folder, exist_ok=True)
            export_path = os.path.join(character_export_folder, file_name)
            return export_path
        return ""

    def send_save(self):
        self.send(OpCodes.SAVE)

    def get_selected_actors(self, of_types=None):
        selected = RScene.GetSelectedObjects()
        avatars = RScene.GetAvatars()
        actors = []
        selected_actor_objects = []
        # if nothing selected and only 1 avatar, use this actor
        # otherwise return a list of all selected actors
        if not selected and len(avatars) == 1:
            actor = LinkActor(avatars[0])
            if actor:
                if (not of_types or
                    (type(of_types) is list and actor.get_type() in of_types) or
                    (actor.get_type() == of_types)):
                    actors.append(actor)
        else:
            for obj in selected:
                actor_object = cc.find_parent_avatar_or_prop(obj)
                if actor_object and actor_object not in selected_actor_objects:
                    SC: RISkeletonComponent = actor_object.GetSkeletonComponent()
                    actor = LinkActor(actor_object)
                    if actor:
                        if (not of_types or
                            (type(of_types) is list and actor.get_type() in of_types) or
                            (actor.get_type() == of_types)):
                            actors.append(actor)
                            selected_actor_objects.append(actor_object)
        return actors

    def get_active_actor(self):
        avatar = cc.get_first_avatar()
        if avatar:
            actor = LinkActor(avatar)
            return actor
        return None

    def get_sub_object_data(self, object: RIObject):
        """Get attached sub objects: Lights, Cameras, Props, Accessories, Clothing & Hair"""

        sub_objects = RScene.FindChildObjects(object, EObjectType_Light | EObjectType_Camera | EObjectType_Prop |
                                                      EObjectType_Cloth | EObjectType_Accessory | EObjectType_Hair)

        # TODO export.export_extra_data should add the link_id's for these sub-objects.
        # TODO only add link_id data when using data-link export...

    def send_avatar(self, actor: LinkActor):
        """
        TODO: Send sub object link id's?
        """
        self.update_link_status(f"Sending Avatar for Import: {actor.name}")
        self.send_notify(f"Exporting: {actor.name}")
        export_path = self.get_export_path(actor.name, actor.name + ".fbx")
        if not export_path: return
        utils.log_info(f"Exporting Character: {export_path}")
        #linked_object = actor.object.GetLinkedObject(RGlobal.GetTime())
        export = exporter.Exporter(actor.object, no_window=True)
        export.set_datalink_export()
        export.do_export(file_path=export_path)
        time.sleep(0.5)
        self.send_notify(f"Avatar Import: {actor.name}")
        export_data = encode_from_json({
            "path": export_path,
            "name": actor.name,
            "type": actor.get_type(),
            "link_id": actor.get_link_id(),
            "motion_prefix": self.motion_prefix,
            "use_fake_user": self.use_fake_user,
        })
        self.send(OpCodes.CHARACTER, export_data)

    def send_prop(self, actor: LinkActor):
        self.update_link_status(f"Sending Prop for Import: {actor.name}")
        self.send_notify(f"Exporting: {actor.name}")
        export_path = self.get_export_path(actor.name, actor.name + ".fbx")
        if not export_path: return
        export = exporter.Exporter(actor.object, no_window=True)
        export.set_datalink_export()
        export.do_export(file_path=export_path)
        self.send_notify(f"Prop Import: {actor.name}")
        export_data = encode_from_json({
            "path": export_path,
            "name": actor.name,
            "type": actor.get_type(),
            "link_id": actor.get_link_id(),
            "motion_prefix": self.motion_prefix,
            "use_fake_user": self.use_fake_user,
        })
        self.send(OpCodes.PROP, export_data)


    def send_light(self, actor: LinkActor):
        return


    def send_camera(self, actor: LinkActor):
        return


    def send_attached_actors(self, actor: LinkActor):
        """Send attached lights and cameras.
           Attached props are sent as part of the parent prop.
           (Avatars can only be linked, not attached)
        """
        objects = RScene.FindChildObjects(EObjectType_Prop | EObjectType_MDProp |
                                          EObjectType_Light |
                                          EObjectType_Camera)
        for obj in objects:
            name = obj.GetName()
            if "Preview" in name: continue
            actor = LinkActor(obj)
            if actor.is_avatar():
                self.send_avatar(actor)
            elif actor.is_prop():
                self.send_prop(actor)
            elif actor.is_light():
                self.send_light()
            elif actor.is_camera():
                self.send_camera()
            else:
                utils.log_error("Unknown Actor type!")
        return

    def send_actor(self):
        #cc.deduplicate_scene()
        actors = self.get_selected_actors()
        actor: LinkActor
        for actor in actors:
            if actor.is_avatar():
                self.send_avatar(actor)
            elif actor.is_prop():
                self.send_prop(actor)
            elif actor.is_light():
                self.send_light()
            elif actor.is_camera():
                self.send_camera()

    def send_update_replace(self):
        avatars = {}
        selected = RScene.GetSelectedObjects()
        for obj in selected:
            prop_or_avatar: RIAvatar = cc.find_parent_avatar_or_prop(obj)
            id = prop_or_avatar.GetID()
            if type(prop_or_avatar) is RIAvatar or type(prop_or_avatar) is RILightAvatar:
                if id not in avatars:
                    avatars[id] = {
                            "avatar": prop_or_avatar,
                            "replace": False,
                            "objects": []
                        }
                if obj == prop_or_avatar:
                    avatars[id]["replace"] = True
                else:
                    avatars[id]["objects"].append(obj)
        for id in avatars:
            avatar = avatars[id]["avatar"]
            actor = LinkActor(avatar)
            objects = [ cc.safe_export_name(o.GetName()) for o in avatars[id]["objects"] ]
            export_path = self.get_export_path(actor.name + "_Update", actor.name + "_Update.fbx")
            if not export_path: return
            export = exporter.Exporter(actor.object, no_window=True)
            export.set_update_replace_export(full_avatar=not objects)
            export.do_export(file_path=export_path)
            self.send_notify(f"Update / Replace Import: {actor.name}")
            update_data = encode_from_json({
                "path": export_path,
                "name": actor.name,
                "type": actor.get_type(),
                "link_id": actor.get_link_id(),
                "replace": avatars[id]["replace"],
                "objects": objects,
            })
            self.send(OpCodes.UPDATE_REPLACE, update_data)

    def send_motion_export(self):
        actors = self.get_selected_actors()
        actor: LinkActor
        for actor in actors:
            motion_name = actor.name + "_motion"
            self.update_link_status(f"Sending Animation: {motion_name}")
            self.send_notify(f"Exporting Motion: {motion_name}")
            export_path = self.get_export_path(motion_name, motion_name + ".fbx")
            if not export_path: return
            utils.log_info(f"Exporting Character: {export_path}")
            #linked_object = actor.object.GetLinkedObject(RGlobal.GetTime())
            export = exporter.Exporter(actor.object, no_window=True)
            export.set_datalink_motion_export()
            export.do_export(export_path)
            time.sleep(0.5)
            self.send_notify(f"Motion Import: {motion_name}")
            fps = get_fps()
            start_time: RTime = RGlobal.GetStartTime()
            end_time: RTime = RGlobal.GetEndTime()
            start_frame = fps.GetFrameIndex(start_time)
            end_frame = fps.GetFrameIndex(end_time)
            current_time: RTime = RGlobal.GetTime()
            current_frame = fps.GetFrameIndex(current_time)
            export_data = encode_from_json({
                "path": export_path,
                "name": actor.name,
                "type": actor.get_type(),
                "link_id": actor.get_link_id(),
                "fps": fps.ToFloat(),
                "start_time": start_time.ToFloat(),
                "end_time": end_time.ToFloat(),
                "start_frame": start_frame,
                "end_frame": end_frame,
                "time": current_time.ToFloat(),
                "frame": current_frame,
                "motion_prefix": self.motion_prefix,
                "use_fake_user": self.use_fake_user,
            })
            self.send(OpCodes.MOTION, export_data)

    def send_avatar_morph(self, actor: LinkActor, update=False):
        self.update_link_status(f"Sending Character for Morph: {actor.name}")
        self.send_notify(f"Exporting Morph: {actor.name}")
        export_path = self.get_export_path(actor.name, actor.name + ".obj")
        if not export_path: return
        obj_options = (EExport3DFileOption_ResetToBindPose |
                       EExport3DFileOption_FullBodyPart |
                       EExport3DFileOption_AxisYUp |
                       EExport3DFileOption_GenerateDrmProtectedFile |
                       EExport3DFileOption_TextureMapsAreShaderGenerated |
                       EExport3DFileOption_GenerateMeshGroupIni |
                       EExport3DFileOption_ExportExtraMaterial)
        if not update and prefs.EXPORT_MORPH_MATERIALS:
            obj_options |= EExport3DFileOption_ExportMaterial
        RFileIO.ExportObjFile(actor.object, export_path, obj_options)
        self.send_notify(f"Morph Import: {actor.name}")
        export_data = encode_from_json({
            "path": export_path,
            "name": actor.name,
            "type": actor.get_type(),
            "link_id": actor.get_link_id(),
        })
        if update:
            self.send(OpCodes.MORPH_UPDATE, export_data)
        else:
            self.send(OpCodes.MORPH, export_data)

    def send_morph(self):
        actors = self.get_selected_actors()
        actor: LinkActor
        for actor in actors:
            if actor.is_standard():
                self.send_avatar_morph(actor)

    def send_morph_update(self):
        actors = self.get_selected_actors()
        actor: LinkActor
        for actor in actors:
            if actor.is_standard():
                self.send_avatar_morph(actor, update=True)

    def send_morph_exported(self, avatar=None, obj_path=None):
        """Send a pre-exported avatar obj through the DataLink"""

        actor = LinkActor(avatar)
        self.update_link_status(f"Sending Character for Morph: {actor.name}")
        self.send_notify(f"Character Morph: {actor.name}")
        export_data = encode_from_json({
            "path": obj_path,
            "name": actor.name,
            "type": actor.get_type(),
            "link_id": actor.get_link_id(),
        })
        self.send(OpCodes.MORPH, export_data)

    def send_actor_exported(self, avatar=None, fbx_path=None, save_after_import=False):
        """Send a pre-exported avatar/actor through the DataLink"""

        actor = LinkActor(avatar)
        self.update_link_status(f"Sending Character for Import: {actor.name}")
        self.send_notify(f"Character Import: {actor.name}")
        export_data = encode_from_json({
            "path": fbx_path,
            "name": actor.name,
            "type": actor.get_type(),
            "link_id": actor.get_link_id(),
            "motion_prefix": self.motion_prefix,
            "use_fake_user": self.use_fake_user,
            "save_after_import": save_after_import,
        })
        self.send(OpCodes.CHARACTER, export_data)

    def send_actor_update(self, actor, old_name, old_link_id):
        if not actor:
            actor = self.get_active_actor()
        if actor:
            self.update_link_status(f"Updating Blender Character: {actor.name}")
            self.send_notify(f"Updating: {actor.name}")
            update_data = encode_from_json({
                "old_name": old_name,
                "old_link_id": old_link_id,
                "type": actor.get_type(),
                "new_name": actor.name,
                "new_link_id": actor.get_link_id(),
            })
            self.send(OpCodes.CHARACTER_UPDATE, update_data)

    def send_rigify_request(self):
        actors = self.get_selected_actors()
        actor: LinkActor
        for actor in actors:
            if type(actor.object) is RIAvatar or type(actor.object) is RILightAvatar:
                self.update_link_status(f"Requesting Rigify Character: {actor.name}")
                self.send_notify(f"Rigify: {actor.name}")
                rigify_data = encode_from_json({
                    "name": actor.name,
                    "type": actor.get_type(),
                    "link_id": actor.get_link_id(),
                })
                self.send(OpCodes.RIGIFY, rigify_data)

    def encode_light_data(self, actors: list):
        return

    def encode_character_templates(self, actors: list):
        actor_data = []
        character_template = {
            "count": len(actors),
            "actors": actor_data
        }
        actor: LinkActor
        for actor in actors:
            SC: RISkeletonComponent = actor.get_skeleton_component()
            FC: RIFaceComponent = actor.get_face_component()
            VC: RIVisemeComponent = actor.get_viseme_component()
            MC: RIMorphComponent = actor.get_morph_component()
            skin_bone_tree = cc.get_extended_skin_bones_tree(actor.object)
            is_prop = actor.get_type() == "PROP"
            skin_bones, skin_meshes = cc.extract_skin_bones_from_tree(skin_bone_tree, extract_mesh=is_prop)
            actor.skin_bones = skin_bones
            actor.skin_meshes = skin_meshes
            bones = []
            meshes = []
            expressions = []
            visemes = []
            morphs = []
            if SC:
                for bone_node in skin_bones:
                    bones.append(bone_node.GetName())
                for mesh_obj in skin_meshes:
                    meshes.append(mesh_obj.GetName())
            if FC:
                expressions = FC.GetExpressionNames("")
            if VC:
                visemes = VC.GetVisemeNames()
            actor_data.append({
                "name": actor.name,
                "type": actor.get_type(),
                "link_id": actor.get_link_id(),
                "bones": bones,
                "meshes": meshes,
                "expressions": expressions,
                "visemes": visemes,
                "morphs": morphs,
            })
        return encode_from_json(character_template)

    def encode_pose_data(self, actors):
        fps = get_fps()
        start_time: RTime = RGlobal.GetStartTime()
        end_time: RTime = RGlobal.GetEndTime()
        start_frame = fps.GetFrameIndex(start_time)
        end_frame = fps.GetFrameIndex(end_time)
        current_time: RTime = RGlobal.GetTime()
        current_frame = fps.GetFrameIndex(current_time)
        actors_data = []
        data = {
            "fps": fps.ToFloat(),
            "start_time": start_time.ToFloat(),
            "end_time": end_time.ToFloat(),
            "start_frame": start_frame,
            "end_frame": end_frame,
            "time": current_time.ToFloat(),
            "frame": current_frame,
            "motion_prefix": self.motion_prefix,
            "use_fake_user": self.use_fake_user,
            "actors": actors_data,
        }
        actor: LinkActor
        for actor in actors:
            actors_data.append({
                "name": actor.name,
                "type": actor.get_type(),
                "link_id": actor.get_link_id(),
            })
        return encode_from_json(data)

    def encode_pose_frame_data(self, actors: list):
        data = bytearray()
        data += struct.pack("!II", len(actors), get_current_frame())
        actor: LinkActor
        for actor in actors:
            SC: RISkeletonComponent = actor.get_skeleton_component()
            FC: RIFaceComponent = actor.get_face_component()
            VC: RIVisemeComponent = actor.get_viseme_component()
            MC: RIMorphComponent = actor.get_morph_component()

            skin_bones = actor.skin_bones
            skin_meshes = actor.skin_meshes

            data += pack_string(actor.name)
            data += pack_string(actor.get_type())
            data += pack_string(actor.get_link_id())

            # pack object transform
            T: RTransform = actor.get_object().WorldTransform()
            t: RVector3 = T.T()
            r: RQuaternion = T.R()
            s: RVector3 = T.S()
            data += struct.pack("!ffffffffff", t.x, t.y, t.z, r.x, r.y, r.z, r.w, s.x, s.y, s.z)

            # pack bone transforms
            data += struct.pack("!I", len(skin_bones))
            bone: RIObject
            for bone in skin_bones:
                T: RTransform = bone.WorldTransform()
                t: RVector3 = T.T()
                r: RQuaternion = T.R()
                s: RVector3 = T.S()
                data += struct.pack("!ffffffffff", t.x, t.y, t.z, r.x, r.y, r.z, r.w, s.x, s.y, s.z)

            # pack mesh transforms
            data += struct.pack("!I", len(skin_meshes))
            bone: RIObject
            for bone in skin_meshes:
                T: RTransform = bone.WorldTransform()
                t: RVector3 = T.T()
                r: RQuaternion = T.R()
                s: RVector3 = T.S()
                data += struct.pack("!ffffffffff", t.x, t.y, t.z, r.x, r.y, r.z, r.w, s.x, s.y, s.z)

            # pack facial expressions
            if FC:
                names = FC.GetExpressionNames("")
                weights = FC.GetExpressionWeights(RGlobal.GetTime(), names)
                data += struct.pack("!I", len(names))
                for weight in weights:
                    data += struct.pack("!f", weight)
            else:
                data += struct.pack("!I", 0)

            # pack visemes
            if VC:
                names = VC.GetVisemeNames()
                weights = VC.GetVisemeMorphWeights()
                data += struct.pack("!I", len(weights))
                for weight in weights:
                    data += struct.pack("!f", weight)
            else:
                data += struct.pack("!I", 0)

            # TODO: pack morphs
            if MC:
                pass

        return data

    def encode_sequence_data(self, actors):
        fps = get_fps()
        start_time: RTime = RGlobal.GetStartTime()
        end_time: RTime = RGlobal.GetEndTime()
        start_frame = fps.GetFrameIndex(start_time)
        end_frame = fps.GetFrameIndex(end_time)
        current_time: RTime = RGlobal.GetTime()
        current_frame = fps.GetFrameIndex(current_time)
        actors_data = []
        data = {
            "fps": fps.ToFloat(),
            "start_time": start_time.ToFloat(),
            "end_time": end_time.ToFloat(),
            "start_frame": start_frame,
            "end_frame": end_frame,
            "time": current_time.ToFloat(),
            "frame": current_frame,
            "motion_prefix": self.motion_prefix,
            "use_fake_user": self.use_fake_user,
            "actors": actors_data,
        }
        actor: LinkActor
        for actor in actors:
            actors_data.append({
                "name": actor.name,
                "type": actor.get_type(),
                "link_id": actor.get_link_id(),
            })
        return encode_from_json(data)

    def get_lights_data(self, lights):

        all_lights = RScene.FindObjects(EObjectType_Light)
        all_light_id = []
        for light in all_lights:
            all_light_id.append(cc.get_link_id(light))

        VSC: RIVisualSettingComponent = RGlobal.GetVisualSettingComponent()
        try:
            ambient_color: RRgb = VSC.GetAmbientColor()
        except:
            ambient_color = RRgb(0.2,0.2,0.2)

        data = {
            "lights": [],
            "count": len(lights),
            "scene_lights": all_light_id,
            "ambient_color": [ambient_color.R(), ambient_color.G(), ambient_color.B()],
        }

        light: RILight
        for light in lights:

            is_spot = type(light) is RISpotLight
            is_point = type(light) is RIPointLight
            is_dir = type(light) is RIDirectionalLight

            T = light.WorldTransform()
            t: RVector3 = T.T()
            r: RQuaternion = T.R()
            s: RVector3 = T.S()

            link_id: str = cc.get_link_id(light, add_if_missing=True)
            active: bool = light.GetActive()
            color: RRgb = light.GetColor()
            multiplier: float = light.GetMultiplier()

            light_type = "SPOT" if is_spot else "POINT" if is_point else "DIR"
            angle: float = 0
            falloff: float = 100
            attenuation: float = 100
            light_range: float = 1000
            transmission: bool = False
            is_tube: bool = False
            tube_length: float = 0
            tube_radius: float = 0
            tube_soft_radius: float = 0
            is_rectangle: bool = False
            rect: RVector2 = RVector2(0,0)
            cast_shadow: bool = False
            inverse_square: bool = False

            if is_spot or is_point:
                light_range = light.GetRange()
            if is_spot:
                status, angle, falloff, attenuation = light.GetSpotLightBeam(angle, falloff, attenuation)
            if is_spot or is_dir:
                transmission = light.GetTransmission()
            if is_spot or is_point:
                inverse_square = light.GetInverseSquare()
                is_tube = light.IsTubeShape()
                tube_length = light.GetTubeLength()
                tube_radius = light.GetTubeRadius()
                tube_soft_radius = light.GetTubeSoftRadius()
                is_rectangle = light.IsRectangleShape()
                rect = light.GetRectWidthHeight()
            cast_shadow = light.IsCastShadow()

            light_data = {
                "link_id": link_id,
                "name": light.GetName(),
                "loc": [t.x, t.y, t.z],
                "rot": [r.x, r.y, r.z, r.w],
                "sca": [s.x, s.y, s.z],
                "active": active,
                "color": [color.R(), color.G(), color.B()],
                "multiplier": multiplier,
                "type": light_type,
                "range": light_range,
                "angle": angle,
                "falloff": falloff,
                "attenuation": attenuation,
                "inverse_square": inverse_square,
                "transmission": transmission,
                "is_tube": is_tube,
                "tube_length": tube_length,
                "tube_radius": tube_radius,
                "tube_soft_radius": tube_soft_radius,
                "is_rectangle": is_rectangle,
                "rect": [rect.x, rect.y],
                "cast_shadow": cast_shadow,
            }

            data["lights"].append(light_data)

        return data

    def get_all_lights(self):
        lights = RScene.FindObjects(EObjectType_Light)
        return lights

    def export_hdri(self, lights_data):
        VSC: RIVisualSettingComponent = RGlobal.GetVisualSettingComponent()
        use_ibl = VSC.IsIBLEnable() and VSC.IsValid()
        lights_data["use_ibl"] = use_ibl
        try:
            ambient_color: RRgb = VSC.GetAmbientColor()
        except:
            ambient_color = RRgb(0.2,0.2,0.2)
        if use_ibl:
            export_path = self.get_export_path("Lighting Settings", "RL_Scene_HDRI.hdr", unique=False)
            if not export_path: return
            if os.path.exists(export_path):
                try:
                    os.remove(export_path)
                except:
                    pass
            utils.log_info(f"Export HDRI: {export_path}")
            VSC.SaveIBLImage(export_path)
            lights_data["ibl_path"] = export_path
            # TODO need API to get IBl strength (and blur)
            # ibl_strength = VSC.GetIBLStrength()
            # for now set to ambient color average
            ambient_strength = (ambient_color.R() + ambient_color.G() + ambient_color.B()) / 3
            ibl_strength = (0.5 + ambient_strength) / 2
            lights_data["ibl_strength"] = ibl_strength
            # TODO need API to get IBL transform
            # ibl_transform = VSC.GetIBLTransform()
            # or...
            # ibl_location = VSC.GetIBLTranslation()
            # ibl_rotation = VSC.GetIBLRotation()
            # ibl_scale = VSC.GetIBLScale()
            # for now get from the sky (which is not updated by the IBL settings, but better than nothing)
            ibl_location = [ 0.0, 0.0, 0.0 ]
            ibl_rotation = [ 0.0, 0.0, 0.0 ]
            ibl_scale = RVector3(1,1,1)
            if True: #VSC.IsIBLSyncSkyOrientation():
                sky: RISky = RScene.FindObject(EObjectType_Sky, "Sky")
                if sky:
                    T: RTransform = sky.WorldTransform()
                    t: RVector3 = T.T()
                    r: RQuaternion = T.R()
                    s: RVector3 = T.S()
                    rot_matrix: RMatrix3 = r.ToRotationMatrix()
                    (x, y, z) = cc.matrix_to_euler_xyz(rot_matrix)
                    ibl_location = [ t.x, t.y, t.z ]
                    ibl_rotation = [ x, y, z - 96.5*0.01745329 ]
                    ibl_scale = s
            lights_data["ibl_location"] = ibl_location
            lights_data["ibl_rotation"] = ibl_rotation
            lights_data["ibl_scale"] = ibl_scale.x

    def sync_lights(self):
        self.update_link_status(f"Synchronizing Lights")
        self.send_notify(f"Sync Lights")
        lights = self.get_all_lights()
        lights_data = self.get_lights_data(lights)
        self.export_hdri(lights_data)
        self.send(OpCodes.LIGHTS, encode_from_json(lights_data))

    def get_camera_data(self, camera: RICamera):
        link_id = cc.get_link_id(camera, add_if_missing=True)
        name = camera.GetName()
        time = RGlobal.GetTime()
        width = 0
        height = 0
        camera.GetAperture(width, height)
        # Get camera bounds
        max = RVector3()
        center = RVector3()
        min = RVector3()
        camera.GetBounds(max, center, min)
        # Get the camera pivot transform values
        pos = RVector3()
        rot = RVector3()
        camera.GetPivot(pos, rot)
        focal_length = camera.GetFocalLength(time)
        fov = camera.GetAngleOfView(time)
        fit = ("HORIZONTAL" if camera.GetFitRenderRegionType() == ECameraFitResolution_Horizontal
                            else "VERTICAL")
        T: RTransform = camera.WorldTransform()
        t: RVector3 = T.T()
        r: RQuaternion = T.R()
        s: RVector3 = T.S()
        data = {
            "link_id": link_id,
            "name": name,
            "loc": [t.x, t.y, t.z],
            "rot": [r.x, r.y, r.z, r.w],
            "sca": [s.x, s.y, s.z],
            "fov": fov,
            "fit": fit,
            "width": width,
            "height": height,
            "focal_length": focal_length,
            "min": [min.x, min.y, min.z],
            "max": [max.x, max.y, max.z],
            "center": [center.x, center.y, center.z],
            "pos": [pos.x, pos.y, pos.z],
        }
        return data

    def encode_camera_data(self, camera):
        data = self.get_camera_data(camera)
        return encode_from_json(data)

    def get_selection_pivot(self) -> RVector3:
        selected_objects = RScene.GetSelectedObjects()
        obj: RIObject
        pivot = RVector3(0,0,0)
        for obj in selected_objects:
            max = RVector3()
            min = RVector3()
            mid = RVector3()
            obj.GetBounds(max, mid, min)
            pivot += mid
        l = len(selected_objects)
        if l > 0:
            pivot /= len(selected_objects)
        return pivot

    def send_camera_sync(self):
        self.update_link_status(f"Synchronizing View Camera")
        self.send_notify(f"Sync View Camera")
        view_camera: RICamera = RScene.GetCurrentCamera()
        camera_data = self.get_camera_data(view_camera)
        pivot = self.get_selection_pivot()
        data = {
            "view_camera": camera_data,
            "pivot": [pivot.x, pivot.y, pivot.z],
        }
        self.send(OpCodes.CAMERA_SYNC, encode_from_json(data))
        self.send_frame_sync()

    def decode_camera_sync_data(self, data):
        data = decode_to_json(data)
        view_camera: RICamera = RScene.GetCurrentCamera()
        camera_data = data["view_camera"]
        pivot = cc.array_to_vector3(data["pivot"]) * 100
        loc = cc.array_to_vector3(camera_data["loc"]) * 100
        rot = cc.array_to_quaternion(camera_data["rot"])
        sca = cc.array_to_vector3(camera_data["sca"])
        time = RGlobal.GetTime()
        view_camera.SetFocalLength(time, camera_data["focal_length"])
        # doesn't work on the preview camera...
        #set_transform_control(view_camera, loc, rot, sca)

    def receive_camera_sync(self, data):
        self.update_link_status(f"Camera Data Receveived")
        self.decode_camera_sync_data(data)

    def send_frame_sync(self):
        self.update_link_status(f"Sending Frame Sync")
        fps = get_fps()
        start_time = RGlobal.GetStartTime()
        end_time = RGlobal.GetEndTime()
        current_time = RGlobal.GetTime()
        start_frame = fps.GetFrameIndex(start_time)
        end_frame = fps.GetFrameIndex(end_time)
        current_frame = fps.GetFrameIndex(current_time)
        frame_data = {
            "fps": fps.ToFloat(),
            "start_time": start_time.ToFloat(),
            "end_time": end_time.ToFloat(),
            "current_time": current_time.ToFloat(),
            "start_frame": start_frame,
            "end_frame": end_frame,
            "current_frame": current_frame,
            "motion_prefix": self.motion_prefix,
            "use_fake_user": self.use_fake_user,
        }
        self.send(OpCodes.FRAME_SYNC, encode_from_json(frame_data))

    def receive_frame_sync(self, data):
        self.update_link_status(f"Frame Sync Receveived")
        frame_data = decode_to_json(data)
        start_frame = frame_data["start_frame"]
        end_frame = frame_data["end_frame"]
        current_frame = frame_data["current_frame"]
        end_frame = max(current_frame, end_frame)
        start_frame = min(current_frame, start_frame)
        start_time = get_frame_time(start_frame)
        end_time = get_frame_time(end_frame)
        current_time = get_frame_time(current_frame)
        RGlobal.SetStartTime(start_time)
        RGlobal.SetEndTime(end_time)
        RGlobal.SetTime(current_time)


    # Character Pose
    #

    def send_pose(self):
        # get actors
        actors = self.get_selected_actors(of_types=["AVATAR", "PROP"])
        if actors:
            self.update_link_status(f"Sending Current Pose Set")
            self.send_notify(f"Pose Set")
            # send pose info
            pose_data = self.encode_pose_data(actors)
            self.send(OpCodes.POSE, pose_data)
            # send template data
            template_data = self.encode_character_templates(actors)
            self.send(OpCodes.TEMPLATE, template_data)
            # store the actors
            self.data.sequence_actors = actors
            # send pose frame data
            pose_frame_data = self.encode_pose_frame_data(actors)
            self.send(OpCodes.POSE_FRAME, pose_frame_data)

    def send_sequence(self):

        # stop the sequence if running...
        if self.is_sequence_running():
            # as the next frame was never sent
            self.data.sequence_current_frame_time = prev_frame(self.data.sequence_current_frame_time)
            self.data.sequence_current_frame -= 1
            self.update_link_status(f"Sequence Aborted: {self.data.sequence_current_frame}")
            self.stop_sequence()
            self.send_sequence_end()
            return

        # get actors
        actors = self.get_selected_actors(of_types=["AVATAR", "PROP"])
        self.data.stored_selection = RScene.GetSelectedObjects()
        RScene.ClearSelectObjects()
        if actors:
            self.update_link_status(f"Sending Animation Sequence")
            self.send_notify(f"Animation Sequence")
            # reset animation to start
            self.data.sequence_current_frame_time = reset_animation()
            current_frame = get_current_frame()
            self.data.sequence_current_frame = current_frame
            # send animation meta data
            sequence_data = self.encode_sequence_data(actors)
            self.send(OpCodes.SEQUENCE, sequence_data)
            # send template data first
            template_data = self.encode_character_templates(actors)
            self.send(OpCodes.TEMPLATE, template_data)
            # start the sending sequence
            self.data.sequence_actors = actors
            self.start_sequence(func=self.send_sequence_frame)
            self.data.ack_rate = 60
            self.data.ack_time = 0

    def send_sequence_frame(self):
        if not self.data.sequence_active or not self.data.sequence_actors:
            return
        # set/fetch the current frame in the sequence
        if RGlobal.GetTime() != self.data.sequence_current_frame_time:
            RGlobal.SetTime(self.data.sequence_current_frame_time)
        # clear selected objects will trigger the OnObjectSelectionChanged event every frame
        # which slows down the sequence, so don't use it unless we have to.
        if RScene.GetSelectedObjects():
            RScene.ClearSelectObjects()
        current_frame = get_current_frame()
        self.data.sequence_current_frame = current_frame
        self.update_link_status(f"Sending Sequence Frame: {current_frame}")
        num_frames = current_frame - self.data.sequence_start_frame
        # send current sequence frame actor poses
        pose_data = self.encode_pose_frame_data(self.data.sequence_actors)
        self.send(OpCodes.SEQUENCE_FRAME, pose_data)
        # check for end
        if current_frame >= get_end_frame():
            self.stop_sequence()
            self.send_sequence_end()
            return
        # advance to next frame
        self.data.sequence_current_frame_time = next_frame(self.data.sequence_current_frame_time)

    def send_sequence_end(self):
        actors = self.data.sequence_actors
        if actors:
            sequence_data = self.encode_sequence_data(actors)
            self.send(OpCodes.SEQUENCE_END, sequence_data)
            self.data.sequence_actors = None
        if self.data.stored_selection:
            RScene.SelectObjects(self.data.stored_selection)

    def prep_actor_clip(self, actor: LinkActor, start_time, num_frames, start_frame, end_frame):
        """Creates an empty clip and grabs the t-pose data for the character"""

        fps = get_fps()
        RGlobal.RemoveAllAnimations(actor.object)

        clip: RIClip
        t0 = RTime.FromValue(0)
        length = fps.IndexedFrameTime(end_frame)

        SC = actor.get_skeleton_component()
        clip = SC.AddClip(t0)
        clip.SetLength(length)

        FC = actor.get_face_component()
        FC.AddClip(t0, "Expressions", length)
        FC.AddExpressivenessKey(t0, 1.0)
        clip = FC.GetClip(0)
        clip.SetLength(length)

        VC = actor.get_viseme_component()
        VC.AddVisemesClip(t0, "Visemes", length)
        clip = VC.GetClip(0)
        clip.SetLength(length)

        set_transform_control(t0, actor.object, RVector3(0,0,0), RQuaternion(RVector4(0,0,0,1)), RVector3(1,1,1))
        RGlobal.ObjectModified(actor.object, EObjectModifiedType_Transform)
        actor.object.Update()
        t_pose = get_pose_local(actor.object) if actor.is_avatar() else None
        actor.set_t_pose(t_pose)

    def decode_pose_frame_data(self, pose_data):
        count, frame = struct.unpack_from("!II", pose_data)
        offset = 8
        actors_list = []
        pose_json = {
            "count": count,
            "frame": frame,
            "actors": actors_list,
        }

        for i in range(0, count):
            pose = []
            shapes = []
            offset, name = unpack_string(pose_data, offset)
            offset, character_type = unpack_string(pose_data, offset)
            offset, link_id = unpack_string(pose_data, offset)
            actor = self.data.find_sequence_actor(link_id)
            actor_data = {
                "name": name,
                "type": character_type,
                "link_id": link_id,
                "actor": actor,
                "transform": None,
                "pose": pose,
                "shapes": shapes,
            }

            if actor:
                actors_list.append(actor_data)
            tx,ty,tz,rx,ry,rz,rw,sx,sy,sz = struct.unpack_from("!ffffffffff", pose_data, offset)
            offset += 40
            actor_data["transform"] = [tx,ty,tz,rx,ry,rz,rw,sx,sy,sz]

            num_bones = struct.unpack_from("!I", pose_data, offset)[0]
            offset += 4
            for i in range(0, num_bones):
                tx,ty,tz,rx,ry,rz,rw,sx,sy,sz = struct.unpack_from("!ffffffffff", pose_data, offset)
                offset += 40
                pose.append([tx,ty,tz,rx,ry,rz,rw,sx,sy,sz])

            num_shapes = struct.unpack_from("!I", pose_data, offset)[0]
            offset += 4
            for i in range(0, num_shapes):
                weight = struct.unpack_from("!f", pose_data, offset)[0]
                offset += 4
                shapes.append(weight)

        return pose_json

    def receive_character_template(self, data):
        self.update_link_status(f"Character Templates Received")
        template_json = decode_to_json(data)
        count = template_json["count"]
        for actor_data in template_json["actors"]:
            name = actor_data["name"]
            character_type = actor_data["type"]
            link_id = actor_data["link_id"]
            actor = self.data.find_sequence_actor(link_id)
            if actor:
                utils.log_info(f"Character Template Received: {name}")
                actor.set_template(actor_data)
            else:
                utils.log_error(f"Unable to find actor: {name} ({link_id})")

    def receive_pose(self, data):
        self.update_link_status(f"Receiving Pose ...")
        json_data = decode_to_json(data)
        frame = json_data["frame"]
        start_frame = json_data["start_frame"]
        end_frame = json_data["end_frame"]
        # sequence frame range
        self.data.pose_frame = frame
        end_frame = max(frame + 1, end_frame)
        start_frame = min(frame, start_frame)
        start_time = get_frame_time(start_frame)
        end_time = get_frame_time(end_frame)
        frame_time = get_frame_time(frame)
        # extend project range
        extend_project_range(end_time)
        # move to the start frame
        RGlobal.SetStartTime(start_time)
        RGlobal.SetEndTime(end_time)
        RGlobal.SetTime(RTime.FromValue(0))
        # for performance it is best to do all actor processing with nothing selected
        RScene.ClearSelectObjects()
        # pose actors
        actors = []
        for actor_data in json_data["actors"]:
            name = actor_data["name"]
            character_type = actor_data["type"]
            link_id = actor_data["link_id"]
            actor = LinkActor.find_actor(link_id, search_name=name, search_type=character_type)
            if actor:
                self.prep_actor_clip(actor, frame_time, 1, start_frame, end_frame)
                actors.append(actor)
        self.data.sequence_actors = actors
        # refresh actor timelines
        refresh_timeline(actors)

    def receive_pose_frame(self, data):
        pose_frame_data = self.decode_pose_frame_data(data)
        if not pose_frame_data:
            return
        frame = pose_frame_data["frame"]
        scene_time = get_frame_time(frame)
        scene_time2 = get_frame_time(frame+1)
        if scene_time2 > RGlobal.GetEndTime():
            RGlobal.SetEndTime(scene_time2)
        if scene_time < RGlobal.GetStartTime():
            RGlobal.SetStartTime(scene_time)
        self.update_link_status(f"Pose Data Recevied: {frame}")
        # update all actor poses
        RScene.ClearSelectObjects()
        for actor_data in pose_frame_data["actors"]:
            actor: LinkActor = actor_data["actor"]
            actor.begin_editing()
            apply_pose(actor, scene_time, actor_data["pose"], actor_data["shapes"], actor.t_pose)
            apply_pose(actor, scene_time2, actor_data["pose"], actor_data["shapes"], actor.t_pose)
            apply_shapes(actor, scene_time, actor_data["pose"], actor_data["shapes"], actor.t_pose)
            apply_shapes(actor, scene_time2, actor_data["pose"], actor_data["shapes"], actor.t_pose)
            actor.end_editing(scene_time)
        for actor_data in pose_frame_data["actors"]:
            actor: LinkActor = actor_data["actor"]
            RScene.SelectObject(actor.object)
        # set the scene time to the end of the clip(s)
        RGlobal.SetTime(scene_time)
        RGlobal.ForceViewportUpdate()

    def receive_sequence(self, data):
        self.update_link_status(f"Receiving Live Sequence ...")
        json_data = decode_to_json(data)
        # sequence frame range
        start_frame = json_data["start_frame"]
        end_frame = json_data["end_frame"]
        self.data.sequence_start_frame = start_frame
        self.data.sequence_end_frame = end_frame
        num_frames = self.data.sequence_end_frame - self.data.sequence_start_frame + 1
        start_time = get_frame_time(self.data.sequence_start_frame)
        end_time = get_frame_time(self.data.sequence_end_frame)
        # extend project range
        extend_project_range(end_time)
        # move to start of timeline
        RGlobal.SetStartTime(start_time)
        RGlobal.SetEndTime(end_time)
        # move to the start frame
        RGlobal.SetTime(start_time)
        # for performance it is best to do all actor processing with nothing selected
        RScene.ClearSelectObjects()
        # sequence actors
        actors = []
        for actor_data in json_data["actors"]:
            name = actor_data["name"]
            character_type = actor_data["type"]
            link_id = actor_data["link_id"]
            actor = LinkActor.find_actor(link_id, search_name=name, search_type=character_type)
            if actor:
                self.prep_actor_clip(actor, start_time, num_frames, start_frame, end_frame)
                actor.begin_editing()
                actors.append(actor)
        self.data.sequence_actors = actors
        # refresh actor timelines
        refresh_timeline(actors)
        # move to end of range
        RGlobal.SetTime(get_frame_time(self.data.sequence_end_frame))
        # start the sequence
        self.start_sequence()
        #utils.start_timer("apply_world_fk_pose")
        #utils.start_timer("try_get_pose_bone")
        #utils.start_timer("fetch_transforms")

    def receive_sequence_frame(self, data):
        sequence_frame_data = self.decode_pose_frame_data(data)
        if not sequence_frame_data:
            return
        # clear selected objects, only if needed as this triggers UI updates
        if RScene.GetSelectedObjects():
            RScene.ClearSelectObjects()
        frame = sequence_frame_data["frame"]
        scene_time = get_frame_time(frame)
        if scene_time > RGlobal.GetEndTime():
            RGlobal.SetEndTime(scene_time)
        if scene_time < RGlobal.GetStartTime():
            RGlobal.SetStartTime(scene_time)
        self.data.sequence_current_frame_time = scene_time
        self.data.sequence_current_frame = frame
        self.update_link_status(f"Sequence Frame: {frame} Received")
        # update all actor poses
        for actor_data in sequence_frame_data["actors"]:
            actor: LinkActor = actor_data["actor"]
            apply_pose(actor, scene_time, actor_data["pose"], actor_data["shapes"], actor.t_pose)
            apply_shapes(actor, scene_time, actor_data["pose"], actor_data["shapes"], actor.t_pose)
        # send sequence frame ack
        self.send_sequence_ack(frame)

    def send_sequence_ack(self, frame):
        # encode sequence ack
        data = encode_from_json({
            "frame": frame,
            "rate": self.service.loop_rate,
        })
        # send sequence ack
        self.send(OpCodes.SEQUENCE_ACK, data)

    def receive_sequence_end(self, data):
        json_data = decode_to_json(data)
        frame = json_data["frame"]
        self.data.sequence_end_frame = frame
        num_frames = self.data.sequence_end_frame - self.data.sequence_start_frame
        self.stop_sequence()
        scene_start_time = get_frame_time(self.data.sequence_start_frame)
        scene_end_time = get_frame_time(self.data.sequence_end_frame)
        actor: LinkActor
        RScene.ClearSelectObjects()
        for actor in self.data.sequence_actors:
            actor.end_editing(scene_start_time)
            RScene.SelectObject(actor.object)
        self.data.sequence_actors = None
        self.update_link_status(f"Live Sequence Complete: {num_frames} frames")
        RGlobal.Play(scene_start_time, scene_end_time)
        #utils.log_timer("apply_world_fk_pose", name="apply_world_fk_pose")
        #utils.log_timer("try_get_pose_bone", name="try_get_pose_bone")
        #utils.log_timer("fetch_transforms", name="fetch_transforms")

    def receive_sequence_ack(self, data):
        json_data = decode_to_json(data)
        ack_frame = json_data["frame"]
        server_rate = json_data["rate"]
        delta_frames = self.data.sequence_current_frame - ack_frame
        if prefs.MATCH_CLIENT_RATE:
            if self.data.ack_time == 0.0:
                self.data.ack_time = time.time()
                self.data.ack_rate = 120
                rate = 120
                count = 4
            else:
                t = time.time()
                delta_time = max(t - self.data.ack_time, 1/120)
                self.data.ack_time = t
                ack_rate = (1.0 / delta_time)
                self.data.ack_rate = utils.lerp(self.data.ack_rate, ack_rate, 0.25)

                if delta_frames > 30:
                    rate = 5
                    count = 1
                elif delta_frames > 20:
                    rate = 15
                    count = 1
                elif delta_frames > 10:
                    rate = 30
                    count = 1
                elif delta_frames > 5:
                    rate = 60
                    count = 2
                else:
                    rate = 120
                    count = 4

            self.update_sequence(rate, count, delta_frames)
        else:
            self.update_sequence(120, 4, delta_frames)

    def receive_character_import(self,data):
        json_data = decode_to_json(data)
        fbx_path = json_data["path"]
        name = json_data["name"]
        character_type = json_data["type"]
        link_id = json_data["link_id"]
        self.update_link_status(f"Receving Character Import: {name}")
        if os.path.exists(fbx_path):
            imp = importer.Importer(fbx_path, no_window=True)
            imp.set_datalink_import()
            imported_objects = imp.import_fbx()
            if imported_objects:
                self.update_link_status(f"Character Imported: {name}")
                utils.log_info(f"Looking for imported Actor: {link_id} / {name} / {character_type}")
                actor = LinkActor.find_actor(link_id, search_name=name, search_type=character_type)
                if actor and (actor.get_link_id() != link_id or actor.name != name):
                    # sometimes CC or Blender will change the name or link_id, so let Blender know of the change
                    utils.log_info(f"Imported Actor has different ID: {link_id} != {actor.get_link_id()} or {name} != {actor.name} / {character_type}")
                    # now tell Blender of the new avatar ID
                    self.update_link_status(f"Updating Blender: {actor.name}")
                    self.send_actor_update(actor, name, link_id)

    def receive_morph(self, data):
        json_data = decode_to_json(data)
        obj_path = json_data["path"]
        key_path = json_data["key_path"]
        name = json_data["name"]
        character_type = json_data["type"]
        link_id = json_data["link_id"]
        morph_name = json_data["morph_name"]
        morph_path = json_data["morph_path"]
        actor = LinkActor.find_actor(link_id, search_name=name, search_type=character_type)
        if actor:
            avatar: RIAvatar = actor.object
        morph_slider = morph.MorphSlider(obj_path, key_path)

    def receive_replace_mesh(self, data):
        json_data = decode_to_json(data)
        obj_file_path = json_data["path"]
        actor_name = json_data["actor_name"]
        obj_name = json_data["object_name"]
        mesh_name = json_data["mesh_name"]
        character_type = json_data["type"]
        link_id = json_data["link_id"]
        actor = LinkActor.find_actor(link_id, search_name=actor_name, search_type=character_type)
        if actor:
            avatar: RIAvatar = actor.object
            results = cc.find_actor_source_meshes(mesh_name, obj_name, avatar)
            if results:
                for cc_mesh_name in results:
                    utils.log_info(f"Replace Mesh: {obj_name} / {mesh_name} -> {cc_mesh_name}")
                    status = None
                    try:
                        status: RStatus = avatar.ReplaceMesh(cc_mesh_name, obj_file_path)
                    except:
                        qt.message_box("Error", "Replace Mesh failed! Make sure you are using CC4 version 4.42.3004.1 or above!")
                        return
                    if status == RStatus.Success:
                        RGlobal.ForceViewportUpdate()
                        self.update_link_status(f"Replace Mesh: {actor.name} / {cc_mesh_name}")
                        utils.log_info(f"Replace mesh success!")
                        return
                    else:
                        utils.log_error(f"Replace mesh failed!")
            qt.message_box("Error", f"Unable to determine source mesh for replacement: {obj_name} / {mesh_name}")
            return
        qt.message_box("Error", f"Unable to find actor: {actor_name} / {character_type}")
        return

    def receive_material_update(self, data):
        json_data = decode_to_json(data)
        json_path = json_data["path"]
        actor_name = json_data["actor_name"]
        character_type = json_data["type"]
        link_id = json_data["link_id"]
        actor = LinkActor.find_actor(link_id, search_name=actor_name, search_type=character_type)
        if actor:
            imp = importer.Importer(json_path, no_window=True, json_only=True)
            imp.update_materials(actor.object)
            RGlobal.ForceViewportUpdate()
            self.update_link_status(f"Material Update: {actor.name}")







LINK: DataLink = None

def link_auto_start():
    global LINK
    utils.log_info("Auto-starting Data-link!")
    if not LINK:
        LINK = DataLink()
        LINK.link_start()

def get_data_link():
    global LINK
    if not LINK:
        LINK = DataLink()
    return LINK


def debug(debug_json):
    utils.log_always("")
    utils.log_always("DEBUG")
    utils.log_always("=====")


def test():
    utils.log_always("")
    utils.log_always("TEST")
    utils.log_always("====")
    tests.test()