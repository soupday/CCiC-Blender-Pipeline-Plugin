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
import os, socket, select, struct, time, json, random, atexit
from . import blender, importer, exporter, cc, qt, prefs, tests, utils, vars
from enum import IntEnum

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
    NOTIFY = 50
    MORPH = 90
    CHARACTER = 100
    CHARACTER_UPDATE = 101
    PROP = 102
    PROP_UPDATE = 103
    RIGIFY = 110
    TEMPLATE = 200
    POSE = 201
    SEQUENCE = 202
    SEQUENCE_FRAME = 203
    SEQUENCE_END = 204
    LIGHTS = 205
    CAMERA_SYNC = 206


class LinkActor():
    name: str = "Name"
    object: RIObject = None
    template: list = []
    expressions: list = []
    t_pose: dict = None

    def __init__(self, object):
        self.name = object.GetName()
        self.object = object
        self.get_link_id()

    def get_avatar(self) -> RIAvatar:
        return self.object

    def get_prop(self) -> RIProp:
        return self.object

    def get_object(self) -> RIObject:
        return self.object

    def update(self, object, link_id):
        self.name = object.GetName()
        self.object = object
        self.set_link_id(link_id)

    def get_skeleton_component(self) -> RISkeletonComponent:
        if self.object:
            if type(self.object) is RIAvatar or type(self.object) is RIProp:
                return self.object.GetSkeletonComponent()
        return None

    def set_template(self, template):
        self.template = template

    def set_expressions(self, expressions):
        self.expressions = expressions

    def set_t_pose(self, t_pose):
        self.t_pose = t_pose

    def is_avatar(self):
        return type(self.object) is RIAvatar

    def is_prop(self):
        return type(self.object) is RIProp

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
    actors: list = []
    # Sequence Props
    sequence_start_frame: int = 0
    sequence_end_frame: int = 0
    sequence_current_frame_time: RTime = 0
    sequence_actors: list = None

    def __init__(self):
        return

    def get_actor(self, link_id) -> LinkActor:
        actor: LinkActor
        for actor in self.actors:
            if actor.get_link_id() == link_id:
                return actor
        obj = cc.find_object_by_link_id(link_id)
        if obj:
            return self.add_actor(obj)
        return None

    def get_actor_from_object(self, obj) -> LinkActor:
        actor: LinkActor
        for actor in self.actors:
            if actor.object == obj:
                return actor
        return self.add_actor(obj)

    def add_actor(self, obj) -> LinkActor:
        for actor in self.actors:
            if actor.object == obj:
                return actor
        actor = LinkActor(obj)
        self.actors.append(actor)
        return actor


LINK_DATA = LinkData()


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


def prep_timeline(SC: RISkeletonComponent):
    fps: RFps = RGlobal.GetFps()
    current_time: RTime = RGlobal.GetTime()
    start_time: RTime = RGlobal.GetStartTime()
    end_time: RTime = RGlobal.GetEndTime()
    print(f"start: {start_time.ToFloat()}, end: {end_time.ToFloat()}")
    clips = SC.GetClipCount()
    clip = SC.GetClip(0)
    print(f"clips: {clips}, clip: {clip}")
    #if start_time.ToFloat() == 0 and end_time.ToFloat() == 0:
    #    pass
        #RGlobal.SetStartTime(RTime.FromValue(0))
        #RGlobal.SetEndTime(RTime.FromValue(1000))
        #RGlobal.SetPreviewStartTime(RTime.FromValue(0))
        #RGlobal.SetPreviewEndTime(RTime.FromValue(1000))
        #RGlobal.SetTime(RTime.FromValue(1000))
        #RGlobal.Stop()
    #if scene_time > end_time:
    #    RGlobal.SetEndTime(scene_time)


def get_current_frame():
    fps: RFps = RGlobal.GetFps()
    current_time = RGlobal.GetTime()
    current_frame = fps.GetFrameIndex(current_time)
    return current_frame


def get_end_frame():
    fps: RFps = RGlobal.GetFps()
    end_time: RTime = RGlobal.GetEndTime()
    end_frame = fps.GetFrameIndex(end_time)
    return end_frame


def next_frame(time):
    fps: RFps = RGlobal.GetFps()
    current_time = RGlobal.GetTime()
    next_time = fps.GetNextFrameTime(time)
    RGlobal.SetTime(next_time)
    return next_time


def set_frame_range(start_frame, end_frame):
    fps: RFps = RGlobal.GetFps()
    RGlobal.SetStartTime(fps.IndexedFrameTime(start_frame))
    RGlobal.SetEndTime(fps.IndexedFrameTime(end_frame))


def set_frame(frame):
    fps: RFps = RGlobal.GetFps()
    RGlobal.SetTime(fps.IndexedFrameTime(frame))


def get_frame_time(frame):
    fps: RFps = RGlobal.GetFps()
    return fps.IndexedFrameTime(frame)


def get_clip_frame(clip: RIClip, scene_time: RTime):
    fps: RFps = RGlobal.GetFps()
    clip_time = clip.SceneTimeToClipTime(scene_time)
    return fps.GetFrameIndex(clip_time)


def update_timeline(to_time=None):
    """Force the timeline to update by playing the current frame"""
    if not to_time:
        to_time = RGlobal.GetTime()
    RGlobal.Play(to_time, to_time)


def get_clip_at_or_before(avatar: RIAvatar, time: RTime):
    fps: RFps = RGlobal.GetFps()
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
    fps: RFps = RGlobal.GetFps()
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    clip: RIClip = SC.AddClip(start_time)
    length = fps.IndexedFrameTime(num_frames)
    clip.SetLength(length)
    return clip


def finalize_avatar_clip(avatar, clip):
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    SC.BakeFkToIk(RTime.FromValue(0), True)


def apply_pose(avatar, clip: RIClip, clip_time: RTime, pose_data, t_pose_data):
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    root_bone = SC.GetRootBone()
    root_rot = RQuaternion(RVector4(0,0,0,1))
    root_tra = RVector3(RVector3(0,0,0))
    root_sca = RVector3(RVector3(1,1,1))
    apply_world_fk_pose(SC, clip, clip_time, root_bone, pose_data, t_pose_data,
                     root_rot, root_tra, root_sca)
    #apply_world_ik_pose(SC, clip, current_time, pose_data)
    scene_time = clip.ClipTimeToSceneTime(clip_time)
    SC.BakeFkToIk(scene_time, False)
    avatar.Update()
    RGlobal.ObjectModified(avatar, EObjectModifiedType_Transform)


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


def fetch_transform_data(pose_data, bone_name):
    D = pose_data[bone_name]
    tra = RVector3(D[0], D[1], D[2])
    rot = RQuaternion(RVector4(D[3], D[4], D[5], D[6]))
    sca = RVector3(D[7], D[8], D[9])
    return tra, rot, sca


def log_transform(name, rot, tra, sca):
    utils.log_info(f" - {name}: ({utils.fd2(tra.x)}, {utils.fd2(tra.y)}, {utils.fd2(tra.z)}) - ({utils.fd2(rot.x)}, {utils.fd2(rot.x)}, {utils.fd2(rot.z)}, {utils.fd2(rot.w)}) - ({utils.fd2(sca.x)}, {utils.fd2(sca.y)}, {utils.fd2(sca.z)})")


TRY_BONES = {
    "RL_BoneRoot": ["CC_Base_BoneRoot", "Rigify_BoneRoot", "BoneRoot", "root"],
}

def try_get_pose_bone(name, pose_data):
    if name not in pose_data and name in TRY_BONES:
        names = TRY_BONES[name]
        for n in names:
            if n in pose_data:
                return n
    return name


def apply_world_ik_pose(SC: RISkeletonComponent, clip: RIClip, time: RTime, pose_data):
    tra, rot, sca = fetch_transform_data(pose_data, "CC_Base_BoneRoot")
    set_ik_effector(SC, clip, EHikEffector_LeftFoot, time,  rot, tra, sca)
    tra, rot, sca = fetch_transform_data(pose_data, "CC_Base_BoneRoot")
    set_ik_effector(SC, clip, EHikEffector_RightFoot, time,  rot, tra, sca)


def apply_world_fk_pose(SC, clip, time, bone, pose_data, t_pose_data,
                     parent_world_rot, parent_world_tra, parent_world_sca):

    source_name = bone.GetName()
    bone_name = try_get_pose_bone(source_name, pose_data)
    #print(f"Trying: {bone_name}")
    if bone_name in pose_data:
        #print(f"Found: {bone_name} / {source_name}")

        world_tra, world_rot, world_sca = fetch_transform_data(pose_data, bone_name)
        t_pose_tra, t_pose_rot, t_pose_sca = fetch_transform_data(t_pose_data, source_name)

        local_rot, local_tra, local_sca = calc_local(world_rot, world_tra, world_sca,
                                                     parent_world_rot, parent_world_tra, parent_world_sca)

        #if source_name == "RL_BoneRoot":
        #    log_transform("WORLD", world_rot, world_tra, world_sca)
        #    log_transform("TPOSE", t_pose_rot, t_pose_tra, t_pose_sca)
        #    log_transform("LOCAL", local_rot, local_tra, local_sca)

        set_bone_control(SC, clip, bone, time,
                         t_pose_rot, t_pose_tra, t_pose_sca,
                         local_rot, local_tra, local_sca)

        children = bone.GetChildren()
        for child in children:
            apply_world_fk_pose(SC, clip, time, child, pose_data, t_pose_data,
                             world_rot, world_tra, world_sca)
    #else:
    #    utils.log(f"Bone Not Found in pose data: {bone_name}")


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


def set_bone_control(SC, clip, bone, time,
                     t_pose_rot: RQuaternion, t_pose_tra: RVector3, t_pose_sca: RVector3,
                     local_rot: RQuaternion, local_tra: RVector3, local_sca: RVector3):
    clip_bone_control: RControl = clip.GetControl("Layer", bone)
    if clip_bone_control:
        # get local transform relative to T-pose
        # CC/iC doesn't support bone scaling in human animations? so use the t-pose scale
        sca = t_pose_sca #local_sca / t_pose_sca
        tra = local_tra - t_pose_tra
        rot = local_rot.Multiply(t_pose_rot.Inverse())
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
    rot_matrix = rot.ToRotationMatrix()
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


def set_transform_control(obj: RIObject, loc: RVector3, rot: RQuaternion, sca: RVector3):
    control = obj.GetControl("Transform")
    print(control)
    if control:
        transform = RTransform(sca, rot, loc)
        time = RGlobal.GetTime()
        control.SetValue(time, transform)



def set_loc_rot_sca(obj: RIObject, loc: RVector3, rot: RQuaternion, sca: RVector3):
    loc_control = obj.GetControl()







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
    # local props
    local_app: str = None
    local_version: str = None
    local_path: str = None
    # remote props
    remote_app: str = None
    remote_version: str = None
    remote_path: str = None

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
                utils.log_info(f"Connecting to data link server on {self.host_ip}:{self.host_port}")
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
        self.local_path = prefs.DATALINK_FOLDER
        json_data = {
            "Application": self.local_app,
            "Version": self.local_version,
            "Path": self.local_path,
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
                utils.log_error("Client socket receive:select failed!", e)
                self.service_lost()
            count = 0
            while r:
                op_code = None
                try:
                    header = self.client_sock.recv(8)
                except Exception as e:
                    utils.log_error("Client socket receive:recv failed!", e)
                    self.service_lost()
                if header == 0:
                    print("Socket closed by client")
                    self.service_lost()
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
                                utils.log_error("Client socket receive:chunk_recv failed!", e)
                                self.service_lost()
                            data.extend(chunk)
                            size -= len(chunk)
                    self.parse(op_code, data)
                    self.received.emit(op_code, data)
                    count += 1
                self.is_data = False
                # parse may have received a disconnect notice
                if not self.has_client_sock():
                    return
                try:
                    r,w,x = select.select(self.client_sockets, self.empty_sockets, self.empty_sockets, 0)
                except Exception as e:
                    utils.log_error("Client socket receive:re-select failed!", e)
                    self.service_lost()
                if r:
                    self.is_data = True
                    if count >= MAX_RECEIVE or op_code == OpCodes.NOTIFY:
                        return
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
            self.service_initialize()
            if data:
                json_data = decode_to_json(data)
                self.remote_app = json_data["Application"]
                self.remote_version = json_data["Version"]
                self.remote_path = json_data["Path"]
                utils.log_info(f"Connected to: {self.remote_app} {self.remote_version}")
                utils.log_info(f"Using file path: {self.remote_path}")
                self.changed.emit()
        elif op_code == OpCodes.PING:
            utils.log_info(f"Ping Received")
            pass
        elif op_code == OpCodes.STOP:
            utils.log_info(f"Termination Received")
            self.service_stop()
        elif op_code == OpCodes.DISCONNECT:
            utils.log_info(f"Disconnection Received")
            self.service_recv_disconnect()

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

    def service_recv_disconnect(self):
        self.stop_client()

    def service_stop(self):
        self.send(OpCodes.STOP)
        self.stop_timer()
        self.stop_client()
        self.stop_server()

    def service_lost(self):
        self.lost_connection.emit()
        self.stop_timer()
        self.stop_client()
        self.stop_server()

    def loop(self):
        current_time = time.time()
        delta_time = current_time - self.time
        self.time = current_time

        if self.is_connected:
            self.ping_timer -= delta_time
            self.keepalive_timer -= delta_time

            if USE_PING and self.ping_timer <= 0:
                print("ping")
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
        self.sequence.emit()


    def send(self, op_code, binary_data = None):
        if self.client_sock and (self.is_connected or self.is_connecting):
            try:
                data_length = len(binary_data) if binary_data else 0
                header = struct.pack("!II", op_code, data_length)
                data = bytearray()
                data.extend(header)
                if binary_data:
                    data.extend(binary_data)
                self.client_sock.sendall(data)
                self.ping_timer = PING_INTERVAL_S
                self.sent.emit()
            except:
                utils.log_error("Client socket send failed!")
                self.service_lost()

    def start_sequence(self, func=None):
        self.is_sequence = True
        if func:
            self.sequence.connect(func)
        else:
            try: self.sequence.disconnect()
            except: pass
        self.timer.setInterval(0)

    def stop_sequence(self):
        self.is_sequence = False
        self.timer.setInterval(TIMER_INTERVAL)
        try: self.sequence.disconnect()
        except: pass


class LinkEventCallback(REventCallback):

    def __init__(self):
       REventCallback.__init__(self)

    #def OnCurrentTimeChanged(self, fTime):
    #    print('Current time:' + str(fTime))

    def OnObjectSelectionChanged(self):
        global LINK
        REventCallback.OnObjectSelectionChanged(self)
        if LINK and LINK.is_shown():
            LINK.update_ui()


class DataLink(QObject):
    window: RIDockWidget = None
    host_name: str = "localhost"
    host_ip: str = "127.0.0.1"
    host_port: int = BLENDER_PORT
    target: str = "Blender"
    # Callback
    callback = LinkEventCallback()
    callback_id = None
    # UI
    label_header: QLabel = None
    button_link: QPushButton = None
    textbox_host: QLineEdit = None
    combo_target: QComboBox = None
    # Service
    service: LinkService = None
    # Data
    data = LinkData()


    def __init__(self):
        QObject.__init__(self)
        self.create_window()
        atexit.register(self.on_close)

    def show(self):
        self.window.Show()
        self.show_link_state()

    def is_shown(self):
        return self.window.IsVisible()

    def create_window(self):
        self.window, layout = qt.window("Data Link (WIP)", 400, show_hide=self.on_show_hide)

        self.label_header = qt.label(layout, "Data Link: Not Connected", style=qt.STYLE_TITLE)
        self.label_folder = qt.label(layout, f"Working Folder: {self.get_remote_folder()}", style=qt.STYLE_TITLE)

        row = qt.row(layout)
        self.textbox_host = qt.textbox(row, self.host_name, update=self.update_host)
        self.combo_target = qt.combobox(row, "", options=["Blender", "Unity"], update=self.update_target)

        qt.spacing(layout, 10)

        self.label_status = qt.label(layout, "...", style=qt.STYLE_RL_DESC)

        qt.spacing(layout, 10)

        self.button_link = qt.button(layout, "Listen", self.link_start, toggle=True, value=False)
        qt.button(layout, "Stop", self.link_stop)

        qt.spacing(layout, 20)

        grid = qt.grid(layout)

        qt.button(grid, "Send Character", self.send_actor, row=0, col=0, icon="Character.png", width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT)
        qt.button(grid, "Send Morph", self.send_morph, row=0, col=1, icon="FullBodyMorph.png", width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT)
        qt.button(grid, "Rigify Character", self.send_rigify, row=1, col=0, icon="PostEffect.png", width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT)
        qt.button(grid, "Send Pose", self.send_pose, row=1, col=1, icon="Pose.png", width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT)
        #qt.button(layout, "Send Animation", self.send_animation)
        qt.button(grid, "Live Sequence", self.send_sequence, row=2, col=0, icon="Motion.png", width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT)
        qt.button(grid, "Sync Lights", self.sync_lights, row=2, col=1, icon="Light.png", width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT)
        qt.button(grid, "Sync Camera", self.send_camera_sync, row=3, col=0, icon="Camera.png", width=qt.ICON_BUTTON_HEIGHT, height=qt.ICON_BUTTON_HEIGHT)

        qt.stretch(layout, 20)

        qt.button(layout, "T Test", tests.t_test)
        qt.button(layout, "Show ID", tests.show_id)
        qt.button(layout, "Add Datablock", tests.test_data_block_set)
        qt.button(layout, "Test Datablock", tests.test_data_block_bad_get)

        self.show_link_state()
        self.window.Show()

    def on_show_hide(self, visible):
        if visible:
            if not self.callback_id:
                print("Registering callback")
                self.callback_id = REventHandler.RegisterCallback(self.callback)
        else:
            if self.callback_id:
                print("Un-registering callback")
                REventHandler.UnregisterCallback(self.callback_id)
                self.callback_id = None

    def on_close(self):
        self.on_show_hide(False)

    def update_ui(self):
        print("Update UI")
        return

    def update_link_status(self, text):
        self.label_status.setText(text)

    def update_host(self):
        if self.textbox_host:
            self.host_name = self.textbox_host.text()
            try:
                self.host_ip = socket.gethostbyname(self.host_name)
            except:
                self.host_ip = "127.0.0.1"
            utils.log_info(f"{self.host_name} ({self.host_ip})")

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
        if self.service and self.service.is_connected:
            self.textbox_host.setEnabled(False)
            self.combo_target.setEnabled(False)
            self.button_link.setStyleSheet("background-color: #82be0f; color: black; font: bold")
            self.button_link.setText("Linked")
            self.label_header.setText(f"Connected: {self.service.remote_app} ({self.service.remote_version})")
            self.label_folder.setText(f"Working Folder: {self.get_remote_folder()}")
        elif self.service and self.service.is_listening:
            self.textbox_host.setEnabled(False)
            self.combo_target.setEnabled(False)
            self.button_link.setStyleSheet("background-color: #505050; color: white; font: bold")
            self.button_link.setText("Listening...")
            self.label_header.setText("Waiting for Connection")
            self.label_folder.setText(f"Working Folder: None")
        else:
            self.textbox_host.setEnabled(True)
            self.combo_target.setEnabled(True)
            self.button_link.setStyleSheet(qt.STYLE_NONE)
            if SERVER_ONLY:
                self.button_link.setText("Start Server")
            else:
                self.button_link.setText("Connect")
            self.label_header.setText("Not Connected")
            self.label_folder.setText(f"Working Folder: None")

    def is_connected(self):
        if self.service:
            return self.service.is_connected
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

        if op_code == OpCodes.NOTIFY:
            self.receive_notify(data)

        if op_code == OpCodes.TEMPLATE:
            self.receive_character_template(data)

        if op_code == OpCodes.POSE:
            self.receive_pose(data)

        if op_code == OpCodes.SEQUENCE:
            self.receive_sequence(data)

        if op_code == OpCodes.SEQUENCE_FRAME:
            self.receive_sequence_frame(data)

        if op_code == OpCodes.SEQUENCE_END:
            self.receive_sequence_end(data)

        if op_code == OpCodes.CHARACTER:
            self.receive_character_import(data)

        if op_code == OpCodes.MORPH:
            self.receive_morph(data)

        if op_code == OpCodes.CAMERA_SYNC:
            self.receive_camera_sync(data)

    def on_connected(self):
        self.send_notify("Connected")

    def send_notify(self, message):
        notify_json = { "message": message }
        self.service.send(OpCodes.NOTIFY, encode_from_json(notify_json))

    def receive_notify(self, data):
        notify_json = decode_to_json(data)
        self.update_link_status(notify_json["message"])

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
            return "None"

    def get_remote_export_path(self, name):
        export_folder = self.get_remote_folder()
        return os.path.join(export_folder, name)

    def get_selected_actors(self):
        selected = RScene.GetSelectedObjects()
        avatars = RScene.GetAvatars()
        actors = []
        # if nothing selected and only 1 avatar, use this actor
        # otherwise return a list of all selected actors
        if not selected and len(avatars) == 1:
            actor = self.data.get_actor_from_object(avatars[0])
            if actor:
                actors.append(actor)
        else:
            for obj in selected:
                actor_object = cc.find_parent_avatar_or_prop(obj)
                if actor_object:
                    SC: RISkeletonComponent = actor_object.GetSkeletonComponent()
                    actor = self.data.get_actor_from_object(actor_object)
                    if actor and actor not in actors:
                        actors.append(actor)
        return actors

    def get_active_actor(self):
        avatar = cc.get_first_avatar()
        if avatar:
            actor = self.data.get_actor_from_object(avatar)
            return actor
        return None

    def get_sub_object_data(self, object: RIObject):
        """Get attached sub objects: Lights, Cameras, Props, Accessories, Clothing & Hair"""

        sub_objects = RScene.FindChildObjects(object, EObjectType_Light | EObjectType_Camera | EObjectType_Prop |
                                                      EObjectType_Cloth | EObjectType_Accessory | EObjectType_Hair)

        # TODO export.export_extra_data should add the link_id's for these sub-objects.
        # TODO only add link_id data when using data link export...

    def send_avatar(self, actor: LinkActor):
        """
        TODO: Send sub object link id's?
        """
        self.update_link_status(f"Sending Avatar for Import: {actor.name}")
        self.send_notify(f"Exporting: {actor.name}")
        export_path = self.get_remote_export_path(actor.name + ".fbx")
        #linked_object = actor.object.GetLinkedObject(RGlobal.GetTime())
        export = exporter.Exporter(actor.object, no_window=True)
        export.set_data_link_export(export_path)
        export.export_fbx()
        export.export_extra_data()
        self.send_notify(f"Avatar Import: {actor.name}")
        export_data = encode_from_json({
            "path": export_path,
            "name": actor.name,
            "link_id": actor.get_link_id(),
        })
        self.service.send(OpCodes.CHARACTER, export_data)

    def send_prop(self, actor: LinkActor):
        self.update_link_status(f"Sending Prop for Import: {actor.name}")
        self.send_notify(f"Exporting: {actor.name}")
        export_path = self.get_remote_export_path(actor.name + ".fbx")
        export = exporter.Exporter(actor.object, no_window=True)
        export.set_data_link_export(export_path)
        export.export_fbx()
        export.export_extra_data() # TODO: do extra data for props.
        self.send_notify(f"Prop Import: {actor.name}")
        export_data = encode_from_json({
            "path": export_path,
            "name": actor.name,
            "link_id": actor.get_link_id(),
        })
        self.service.send(OpCodes.PROP, export_data)


    def send_light(self, actor: LinkActor):
        return


    def send_camera(self, actor: LinkActor):
        return


    def send_attached_actors(self, actor: LinkActor):
        """Send attached lights and cameras.
           Attached props are sent as part of the parent prop.
           (Avatars can only be linked, not attached)
        """
        objects = RScene.FindChildObjects(EObjectType_Prop |
                                          EObjectType_Light |
                                          EObjectType_Camera)
        for obj in objects:
            name = obj.GetName()
            if "Preview" in name: continue
            actor = self.data.get_actor_from_object(obj)
            if actor.is_avatar():
                self.send_avatar(actor)
            elif actor.is_prop():
                self.send_prop(actor)
            elif actor.is_light():
                self.send_light()
            elif actor.is_camera():
                self.send_camera()
        return


    def send_actor(self):
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

    def send_avatar_morph(self, actor: LinkActor):
        self.update_link_status(f"Sending Character for Morph: {actor.name}")
        self.send_notify(f"Exporting Morph: {actor.name}")
        export_path = self.get_remote_export_path(actor.name + ".obj")
        obj_options = (EExport3DFileOption_ResetToBindPose |
                       EExport3DFileOption_FullBodyPart |
                       EExport3DFileOption_AxisYUp |
                       EExport3DFileOption_GenerateDrmProtectedFile |
                       EExport3DFileOption_TextureMapsAreShaderGenerated |
                       EExport3DFileOption_GenerateMeshGroupIni |
                       EExport3DFileOption_ExportExtraMaterial)
        RFileIO.ExportObjFile(actor.object, export_path, obj_options)
        self.send_notify(f"Morph Import: {actor.name}")
        export_data = encode_from_json({
            "path": export_path,
            "name": actor.name,
            "link_id": actor.get_link_id(),
        })
        self.service.send(OpCodes.MORPH, export_data)

    def send_morph(self):
        actors = self.get_selected_actors()
        actor: LinkActor
        for actor in actors:
            if actor.is_standard():
                self.send_avatar_morph(actor)

    def send_morph_exported(self, avatar=None, obj_path=None):
        """Send a pre-exported avatar obj through the DataLink"""

        actor = LinkActor(avatar)
        self.update_link_status(f"Sending Character for Morph: {actor.name}")
        self.send_notify(f"Character Morph: {actor.name}")
        export_data = encode_from_json({
            "path": obj_path,
            "name": actor.name,
            "link_id": actor.get_link_id(),
        })
        self.service.send(OpCodes.MORPH, export_data)

    def send_actor_exported(self, avatar=None, fbx_path=None):
        """Send a pre-exported avatar/actor through the DataLink"""

        actor = LinkActor(avatar)
        self.update_link_status(f"Sending Character for Import: {actor.name}")
        self.send_notify(f"Character Import: {actor.name}")
        export_data = encode_from_json({
            "path": fbx_path,
            "name": actor.name,
            "link_id": actor.get_link_id(),
        })
        self.service.send(OpCodes.CHARACTER, export_data)

    def send_actor_update(self, actor, old_name, old_link_id):
        if not actor:
            actor = self.get_active_actor()
        if actor:
            self.update_link_status(f"Updating Blender Character: {actor.name}")
            self.send_notify(f"Updating: {actor.name}")
            update_data = encode_from_json({
                "old_name": old_name,
                "old_link_id": old_link_id,
                "new_name": actor.name,
                "new_link_id": actor.get_link_id(),
            })
            self.service.send(OpCodes.CHARACTER_UPDATE, update_data)

    def send_rigify(self):
        actors = self.get_selected_actors()
        actor: LinkActor
        for actor in actors:
            if type(actor.object) is RIAvatar:
                self.update_link_status(f"Requesting Rigify Character: {actor.name}")
                self.send_notify(f"Rigify: {actor.name}")
                rigify_data = encode_from_json({
                    "name": actor.name,
                    "link_id": actor.get_link_id(),
                })
                self.service.send(OpCodes.RIGIFY, rigify_data)

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
            skin_bones = SC.GetSkinBones()
            bones = []
            for bone_node in skin_bones:
                bones.append(bone_node.GetName())
            actor_data.append({
                "name": actor.name,
                "link_id": actor.get_link_id(),
                "bones": bones
            })
        return encode_from_json(character_template)

    def encode_pose_data(self, actors: list):
        data = bytearray()
        data += struct.pack("!II", len(actors), get_current_frame())
        actor: LinkActor
        for actor in actors:
            SC: RISkeletonComponent = actor.get_skeleton_component()
            skin_bones = SC.GetSkinBones()
            data += pack_string(actor.name)
            data += pack_string(actor.get_link_id())
            data += struct.pack("!I", len(skin_bones))
            bone: RIObject
            for bone in skin_bones:
                T: RTransform = bone.WorldTransform()
                t: RVector3 = T.T()
                r: RQuaternion = T.R()
                s: RVector3 = T.S()
                data += struct.pack("!ffffffffff", t.x, t.y, t.z, r.x, r.y, r.z, r.w, s.x, s.y, s.z)
        return data

    def encode_sequence_data(self, actors):
        fps: RFps = RGlobal.GetFps()
        start_time: RTime = RGlobal.GetStartTime()
        end_time: RTime = RGlobal.GetEndTime()
        start_frame = fps.GetFrameIndex(start_time)
        end_frame = fps.GetFrameIndex(end_time)
        actors_data = []
        data = {
            "fps": fps.ToFloat(),
            "start_time": start_time.ToFloat(),
            "end_time": end_time.ToFloat(),
            "start_frame": start_frame,
            "end_frame": end_frame,
            "actors": actors_data,
        }
        actor: LinkActor
        for actor in actors:
            actors_data.append({
                "name": actor.name,
                "link_id": actor.get_link_id(),
            })
        return encode_from_json(data)

    def get_lights_data(self, lights):

        all_lights = RScene.FindObjects(EObjectType_Light)
        all_light_id = []
        for light in all_lights:
            all_light_id.append(cc.get_link_id(light))

        data = {
            "lights": [],
            "count": len(lights),
            "scene_lights": all_light_id,
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
            falloff: float = 0
            attenuation: float = 0
            light_range: float = 0
            transmission: bool = False
            is_tube: bool = False
            tube_length: float = 0
            tube_radius: float = 0
            tube_soft_radius: float = 0
            is_rectangle: bool = False
            rect: RVector2 = RVector2(0,0)
            cast_shadow: bool = False

            if is_spot or is_point:
                light_range = light.GetRange()
            if is_spot:
                status, angle, falloff, attenuation = light.GetSpotLightBeam(angle, falloff, attenuation)
            if is_spot or is_dir:
                transmission = light.GetTransmission()
            if is_spot or is_point:
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

    def encode_lights_data(self, lights):
        data = self.get_lights_data(lights)
        return encode_from_json(data)

    def get_all_lights(self):
        lights = RScene.FindObjects(EObjectType_Light)
        return lights

    def sync_lights(self):
        self.update_link_status(f"Synchronizing Lights")
        self.send_notify(f"Sync Lights")
        lights = self.get_all_lights()
        lights_data = self.encode_lights_data(lights)
        self.service.send(OpCodes.LIGHTS, lights_data)

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
            #print(f"t: {t.x}, {t.y}, {t.z}")
            #print(f"off: {off.x}, {off.y}, {off.z}")
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
        self.service.send(OpCodes.CAMERA_SYNC, encode_from_json(data))

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


    # Character Pose
    #

    def send_pose(self):
        # get actors
        actors = self.get_selected_actors()
        if actors:
            self.update_link_status(f"Sending Current Pose Set")
            self.send_notify(f"Pose Set")
            # send template data first
            template_data = self.encode_character_templates(actors)
            self.service.send(OpCodes.TEMPLATE, template_data)
            # send pose data
            pose_data = self.encode_pose_data(actors)
            self.service.send(OpCodes.POSE, pose_data)

    def send_animation(self):
        return

    def send_sequence(self):
        # get actors
        actors = self.get_selected_actors()
        if actors:
            self.update_link_status(f"Sending Animation Sequence")
            self.send_notify(f"Animation Sequence")
            # reset animation to start
            self.data.sequence_current_frame_time = reset_animation()
            # send animation meta data
            sequence_data = self.encode_sequence_data(actors)
            self.service.send(OpCodes.SEQUENCE, sequence_data)
            # send template data first
            template_data = self.encode_character_templates(actors)
            self.service.send(OpCodes.TEMPLATE, template_data)
            # start the sending sequence
            self.data.sequence_actors = actors
            self.service.start_sequence(self.send_sequence_frame)

    def send_sequence_frame(self):
        # set/fetch the current frame in the sequence
        if RGlobal.GetTime() != self.data.sequence_current_frame_time:
            RGlobal.SetTime(self.data.sequence_current_frame_time)
        current_frame = get_current_frame()
        self.update_link_status(f"Sending Sequence Frame: {current_frame}")
        # send current sequence frame actor poses
        pose_data = self.encode_pose_data(self.data.sequence_actors)
        self.service.send(OpCodes.SEQUENCE_FRAME, pose_data)
        # check for end
        if current_frame >= get_end_frame():
            self.data.sequence_actors = None
            self.service.stop_sequence()
            self.send_sequence_end()
            return
        # advance to next frame
        self.data.sequence_current_frame_time = next_frame(self.data.sequence_current_frame_time)

    def send_sequence_end(self):
        self.service.send(OpCodes.SEQUENCE_END)

    def prep_actor_clip(self, actor: LinkActor, start_time, num_frames):
        """Creates an empty clip and grabs the t-pose data for the character"""
        SC = actor.get_skeleton_component()
        existing_clip: RIClip = SC.GetClipByTime(start_time)
        clip = make_avatar_clip(actor.object, start_time, num_frames)
        actor.object.Update()
        t_pose = get_pose_local(actor.object) if actor.is_avatar() else None
        actor.set_t_pose(t_pose)
        #if existing_clip:
        #    SC.MergeClips(existing_clip, clip)

    def decode_character_templates(self, template_data):
        template_json = decode_to_json(template_data)
        count = template_json["count"]
        for actor_data in template_json["actors"]:
            link_id = actor_data["link_id"]
            name = actor_data["name"]
            actor = self.data.get_actor(link_id)
            if actor:
                actor.set_template(actor_data["bones"])
            else:
                utils.log_error(f"Unable to find actor: {name} ({link_id})")
        return template_json

    def decode_pose_data(self, pose_data):
        count, frame = struct.unpack_from("!II", pose_data)
        offset = 8
        actors_list = []
        pose_json = {
            "count": count,
            "frame": frame,
            "actors": actors_list,
        }
        for i in range(0, count):
            pose = {}
            offset, name = unpack_string(pose_data, offset)
            offset, link_id = unpack_string(pose_data, offset)
            actor = self.data.get_actor(link_id)
            actor_data = {
                "name": name,
                "link_id": link_id,
                "actor": actor,
                "pose": pose,
            }
            actors_list.append(actor_data)
            for bone_name in actor.template:
                tx,ty,tz,rx,ry,rz,rw,sx,sy,sz = struct.unpack_from("!ffffffffff", pose_data, offset)
                pose[bone_name] = [tx,ty,tz,rx,ry,rz,rw,sx,sy,sz]
                offset += 40
        return pose_json

    def receive_character_template(self, data):
        self.update_link_status(f"Character Templates Received")
        self.decode_character_templates(data)

    def receive_pose(self, data):
        pose_data = self.decode_pose_data(data)
        frame = pose_data["frame"]
        scene_time = get_frame_time(frame)
        no_timeline = False
        if cc.is_cc() and RGlobal.GetStartTime().ToFloat() == 0 and RGlobal.GetEndTime().ToFloat() == 0:
            frame = 0
            scene_time = RTime.FromValue(0)
            no_timeline = True
        self.update_link_status(f"Pose Data Recevied: {frame}")
        # update all actor poses
        for actor_data in pose_data["actors"]:
            actor: LinkActor = actor_data["actor"]
            SC: RISkeletonComponent = actor.get_skeleton_component()
            self.prep_actor_clip(actor, scene_time, 1)
            clip: RIClip = SC.GetClipByTime(scene_time)
            clip_time = clip.SceneTimeToClipTime(scene_time)
            apply_pose(actor.object, clip, clip_time, actor_data["pose"], actor.t_pose)
        # set the scene time to the end of the clip(s)
        if not no_timeline:
            RGlobal.SetTime(scene_time + get_frame_time(1))
            scene_start_time = RGlobal.GetTime()
            scene_end_time = RGlobal.GetTime()
            RGlobal.Play(scene_start_time, scene_end_time)
        if cc.is_cc():
            RGlobal.ForceViewportUpdate()

    def receive_sequence(self, data):
        self.update_link_status(f"Receiving Live Sequence...")
        json_data = decode_to_json(data)
        # sequence frame range
        self.data.sequence_start_frame = json_data["start_frame"]
        self.data.sequence_end_frame = json_data["end_frame"]
        num_frames = self.data.sequence_end_frame - self.data.sequence_start_frame
        start_time = get_frame_time(self.data.sequence_start_frame)
        # sequence actors
        actors = []
        for actor_data in json_data["actors"]:
            name = actor_data["name"]
            link_id = actor_data["link_id"]
            actor = self.data.get_actor(link_id)
            if actor:
                self.prep_actor_clip(actor, start_time, num_frames)
                actors.append(actor)
        self.data.sequence_actors = actors
        # move to end of range
        RGlobal.SetTime(get_frame_time(self.data.sequence_end_frame))
        # start the sequence
        self.service.start_sequence()

    def receive_sequence_frame(self, data):
        pose_data = self.decode_pose_data(data)
        frame = pose_data["frame"]
        scene_time = get_frame_time(frame)
        self.data.sequence_current_frame_time = scene_time
        self.update_link_status(f"Sequence Frame: {frame} Received")
        # update all actor poses
        for actor_data in pose_data["actors"]:
            actor: LinkActor = actor_data["actor"]
            SC = actor.get_skeleton_component()
            scene_time = get_frame_time(frame)
            clip: RIClip = SC.GetClipByTime(scene_time)
            clip_time = clip.SceneTimeToClipTime(scene_time)
            apply_pose(actor.object, clip, clip_time, actor_data["pose"], actor.t_pose)

    def receive_sequence_end(self, data):
        num_frames = self.data.sequence_end_frame - self.data.sequence_start_frame
        self.service.stop_sequence()
        self.data.sequence_actors = None
        scene_start_time = get_frame_time(self.data.sequence_start_frame)
        scene_end_time = get_frame_time(self.data.sequence_end_frame)
        self.update_link_status(f"Live Sequence Complete: {num_frames} frames")
        RGlobal.Play(scene_start_time, scene_end_time)

    def receive_character_import(self,data):
        json_data = decode_to_json(data)
        fbx_path = json_data["path"]
        old_name = json_data["name"]
        old_link_id = json_data["link_id"]
        self.update_link_status(f"Receving Character Import: {old_name}")
        if os.path.exists(fbx_path):
            imp = importer.Importer(fbx_path, no_window=True)
            imp.set_data_link_import()
            imp.import_fbx()
            self.update_link_status(f"Character Imported: {old_name}")
            actor = self.data.get_actor(old_link_id)
            # the new avatar will have it's ID changed
            avatar = cc.get_first_avatar()
            if actor and avatar:
                actor.update(avatar, old_link_id)
                # now tell Blender of the new avatar
                self.update_link_status(f"Updating Blender: {actor.name}")
                self.send_actor_update(actor, old_name, old_link_id)
                #RScene.SelectObject(avatar)
                #self.send_pose()
                #self.sync_lights()
                #self.sync_camera()

    def receive_morph(self, data):
        json_data = decode_to_json(data)
        obj_path = json_data["path"]
        key_path = json_data["key_path"]
        name = json_data["name"]
        link_id = json_data["link_id"]
        morph_name = json_data["morph_name"]
        morph_path = json_data["morph_path"]

        actor = self.data.get_actor(link_id)
        avatar: RIAvatar = actor.object

        slider_setting = RMorphSliderSetting()
        slider_setting.SetMorphName(morph_name)
        slider_setting.SetSliderPath(morph_path)
        slider_setting.SetCategory(ESetCategory_Body)
        slider_setting.SetSourceBaseType(EChooseBase_Current)
        slider_setting.SetTargetFilePath(obj_path)
        slider_setting.SetTargetMorphChecksumFilePath(key_path)
        slider_setting.SetAutoApplyToCurrentCharacter(True)
        slider_setting.SetMorphValueRange(0, 100)
        slider_setting.SetAxisSettingForObj(EAxisSetting_YUp)

        ASC: RIAvatarShapingComponent = avatar.GetAvatarShapingComponent()
        print(obj_path)
        ASC.CreateSlider(slider_setting, "")






LINK: DataLink = None

def get_data_link():
    global LINK
    if not LINK:
        LINK = DataLink()
    else:
        LINK.show()
    return LINK