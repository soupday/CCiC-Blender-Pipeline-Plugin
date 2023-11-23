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

from RLPy import *
import PySide2
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
import os, socket, select, struct, time, json, random
import blender, exporter, cc, qt, utils, vars, tests
from enum import IntEnum

LOCALHOST = "127.0.0.1"
BLENDER_PORT = 9334
UNITY_PORT = 9335
RL_PORT = 9333
TIMER_INTERVAL = 1000/60
MAX_CHUNK_SIZE = 32768
HANDSHAKE_TIMEOUT_S = 60
KEEPALIVE_TIMEOUT_S = 30
PING_INTERVAL_S = 10
SERVER_ONLY = True
CLIENT_ONLY = False
EMPTY_SOCKETS = []
MAX_RECEIVE = 24

class OpCodes(IntEnum):
    NONE = 0
    HELLO = 1
    PING = 2
    STOP = 10
    DISCONNECT = 11
    NOTIFY = 50
    CHARACTER = 100
    RIGIFY = 110
    TEMPLATE = 200
    POSE = 201
    SEQUENCE = 202
    SEQUENCE_REQ = 203
    SEQUENCE_FRAME = 204


class LinkData():
    link_host: str = "localhost"
    link_host_ip: str = "127.0.0.1"
    link_target: str = "BLENDER"
    link_port: int = 9333

    sequence_read_count: int = 24
    current_frame: int = 0
    start_frame: int = 0
    end_frame: int = 0


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


def encode_character_template(avatar: RIAvatar):
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones = SC.GetSkinBones()
    bones = []
    for bone in skin_bones:
        bones.append(bone.GetName())
    character_template = {
        "name": avatar.GetName(),
        "link_id": str(avatar.GetID()),
        "bones": bones
    }
    return encode_from_json(character_template)


def encode_pose_data(avatar: RIAvatar):
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones = SC.GetSkinBones()

    data = bytearray()
    data += struct.pack("!I", get_current_frame())
    for bone in skin_bones:
        T: RTransform = bone.WorldTransform()
        t: RVector3 = T.T()
        r: RQuaternion = T.R()
        s: RVector3 = T.S()
        data += struct.pack("!ffffffffff", t.x, t.y, t.z, r.x, r.y, r.z, r.w, s.x, s.y, s.z)
    return data


def get_animation_data(avatar: RIAvatar):
    fps: RFps = RGlobal.GetFps()
    current_time: RTime = RGlobal.GetTime()
    start_time: RTime = RGlobal.GetStartTime()
    end_time: RTime = RGlobal.GetEndTime()
    current_frame = fps.GetFrameIndex(current_time)
    start_frame = fps.GetFrameIndex(start_time)
    end_frame = fps.GetFrameIndex(end_time)
    data = {
        "name": avatar.GetName(),
        "link_id": str(avatar.GetID()),
        "fps": fps.ToFloat(),
        "current_time": current_time.ToFloat(),
        "start_time": start_time.ToFloat(),
        "end_time": end_time.ToFloat(),
        "current_frame": current_frame,
        "start_frame": start_frame,
        "end_frame": end_frame,
    }
    return data


def reset_animation():
    start_time = RGlobal.GetStartTime()
    RGlobal.SetTime(start_time)
    return start_time


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


def decode_character_template(template_data):
    template_json = decode_to_json(template_data)
    return template_json


def decode_pose_data(character_template, pose_data):
    pose = {}
    # unpack the binary transform data directly into the datalink rig pose bones
    offset = 0
    frame = struct.unpack_from("!I", pose_data, offset)
    offset += 4
    for bone_name in character_template["bones"]:
        tx,ty,tz,rx,ry,rz,rw,sx,sy,sz = struct.unpack_from("!ffffffffff", pose_data, offset)
        pose[bone_name] = [tx,ty,tz,rx,ry,rz,rw,sx,sy,sz]
        offset += 40
    return pose


def set_frame_range(start_frame, end_frame):
    fps: RFps = RGlobal.GetFps()
    RGlobal.SetStartTime(fps.IndexedFrameTime(start_frame))
    RGlobal.SetEndTime(fps.IndexedFrameTime(end_frame))


def set_frame(frame):
    fps: RFps = RGlobal.GetFps()
    RGlobal.SetTime(fps.IndexedFrameTime(frame))


def get_clip_time(frame):
    fps: RFps = RGlobal.GetFps()
    return fps.IndexedFrameTime(frame)


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


def make_avatar_clip(avatar, clip_start_time, num_frames):
    fps: RFps = RGlobal.GetFps()
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    clip: RIClip = SC.AddClip(clip_start_time)
    clip_start_frame = 0
    clip_start_time = fps.IndexedFrameTime(clip_start_frame)
    clip_end_frame = clip_start_frame + num_frames
    clip_end_time = fps.IndexedFrameTime(clip_end_frame)
    length = clip_end_time - clip_start_time
    clip.SetLength(length)
    # move the time to the end of the clip and the animation will play as it is being created
    scene_start_time = clip.ClipTimeToSceneTime(clip_end_time)
    scene_end_time = clip.ClipTimeToSceneTime(clip_end_time)
    #update_timeline(scene_end_time)
    RGlobal.SetTime(scene_end_time)
    #update_timeline(scene_end_time)
    return clip


def prep_avatar_clip(avatar, num_frames, scene_time=None):
    """Creates an empty clip and grabs the t-pose data for the character"""
    fps: RFps = RGlobal.GetFps()
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    if not scene_time:
        scene_time = RGlobal.GetTime()
    #existing_clip: RIClip = SC.GetClipByTime(scene_time)
    #if existing_clip:
    #    next_frame_time = fps.GetNextFrameTime(scene_time)
    #    SC.BreakClip(next_frame_time)
    animation_clip = make_avatar_clip(avatar, scene_time, num_frames)
    avatar.Update()
    t_pose_data = get_pose_local(avatar)
    return animation_clip, t_pose_data


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
    "RL_BoneRoot": ["CC_Base_BoneRoot", "Rigify_BoneRoot", "BoneRoot", "root"]
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
    #if "Ribs" in source_name or "Breast" in source_name:
    #    return

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

    def start_server(self):
        if not self.server_sock:
            try:
                self.keepalive_timer = HANDSHAKE_TIMEOUT_S
                self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_sock.bind(('', RL_PORT))
                self.server_sock.listen(5)
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
            self.server_sock.close()
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
                sock.connect((host, port))
                self.is_connected = False
                self.is_connecting = True
                self.client_sock = sock
                self.client_sockets = [sock]
                self.client_ip = self.host_ip
                self.client_port = self.host_port
                self.keepalive_timer = KEEPALIVE_TIMEOUT_S
                self.ping_timer = PING_INTERVAL_S
                self.send_hello()
                utils.log_info(f"Connecting to data link server on {self.host_ip}:{self.host_port}")
                self.connecting.emit()
                self.changed.emit()
                return True
            except:
                self.client_sock = None
                self.client_sockets = []
                self.is_connected = False
                self.is_connecting = False
                utils.log_info(f"Host not listening...")
                return False
        else:
            utils.log_info(f"Client already connected!")
            return True

    def send_hello(self):
        self.local_app = RApplication.GetProductName()
        self.local_version = RApplication.GetProductVersion()
        self.local_path = cc.temp_files_path("Data Link", True)
        json_data = {
            "Application": self.local_app,
            "Version": self.local_version,
            "Path": self.local_path
        }
        self.send(OpCodes.HELLO, encode_from_json(json_data))

    def stop_client(self):
        if self.client_sock:
            utils.log_info(f"Closing Client Socket")
            self.client_sock.close()
        self.is_connected = False
        self.is_connecting = False
        self.client_sock = None
        self.client_sockets = []
        if self.listening:
            self.keepalive_timer = HANDSHAKE_TIMEOUT_S
        self.client_stopped.emit()
        self.changed.emit()

    def recv(self):
        self.is_data = False
        try:
            if self.client_sock and (self.is_connected or self.is_connecting):
                r,w,x = select.select(self.client_sockets, self.empty_sockets, self.empty_sockets, 0)
                count = 0
                while r:
                    op_code = None
                    header = self.client_sock.recv(8)
                    if header and len(header) == 8:
                        op_code, size = struct.unpack("!II", header)
                        data = None
                        if size > 0:
                            data = bytearray()
                            while size > 0:
                                chunk_size = min(size, MAX_CHUNK_SIZE)
                                chunk = self.client_sock.recv(chunk_size)
                                data.extend(chunk)
                                size -= len(chunk)
                        self.parse(op_code, data)
                        self.received.emit(op_code, data)
                        count += 1
                    self.is_data = False
                    r,w,x = select.select(self.client_sockets, self.empty_sockets, self.empty_sockets, 0)
                    if r:
                        self.is_data = True
                        if count >= MAX_RECEIVE or op_code == OpCodes.NOTIFY:
                            return
        except:
            self.stop_client()

    def accept(self):
        if self.server_sock and self.is_listening:
            r,w,x = select.select(self.server_sockets, self.empty_sockets, self.empty_sockets, 0)
            if r:
                sock, address = self.server_sock.accept()
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

    def parse(self, op_code, data):
        self.keepalive_timer = KEEPALIVE_TIMEOUT_S
        if op_code == OpCodes.HELLO:
            utils.log_info(f"Hello Received")
            self.service_initialize()
            print(data)
            if data:
                json_data = decode_to_json(data)
                self.remote_app = json_data["Application"]
                self.remote_version = json_data["Version"]
                self.remote_path = json_data["Path"]
                utils.log_info(f"Connected to: {self.remote_app} {self.remote_version}")
                utils.log_info(f"Using file path: {self.remote_path}")
                self.changed.emit()
        if op_code == OpCodes.PING:
            utils.log_info(f"Ping Received")
            pass
        elif op_code == OpCodes.STOP:
            utils.log_info(f"Termination Received")
            self.service_stop()
        elif op_code == OpCodes.DISCONNECT:
            utils.log_info(f"Disconnection Received")
            self.service_disconnect()

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

    def service_disconnect(self):
        self.send(OpCodes.DISCONNECT)
        self.stop_client()

    def service_stop(self):
        self.send(OpCodes.STOP)
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

            if self.ping_timer <= 0:
                self.send(OpCodes.PING)

            if self.keepalive_timer <= 0:
                utils.log_info("lost connection!")
                self.service_stop()

        elif self.is_listening:
            self.keepalive_timer -= delta_time

            if self.keepalive_timer <= 0:
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
                utils.log_error("Error sending message, disconnecting...")
                self.lost_connection.emit()
                self.stop_client()

    def start_sequence(self, func=None):
        self.is_sequence = True
        if func:
            self.sequence.connect(func)
        else:
            try: self.sequence.disconnect()
            except: pass

    def stop_sequence(self):
        self.is_sequence = False
        try: self.sequence.disconnect()
        except: pass






class LinkEventCallback(REventCallback):

    def __init__(self):
       REventCallback.__init__(self)

    def OnCurrentTimeChanged(self, fTime):
        print('Current time:' + str(fTime))


class DataLink(QObject):
    window: QWindow = None
    host_name: str = "localhost"
    host_ip: str = "127.0.0.1"
    host_port: int = BLENDER_PORT
    target: str = "Blender"
    # Callback
    callback = LinkEventCallback()
    # UI
    label_header: QLabel = None
    button_link: QPushButton = None
    textbox_host: QLineEdit = None
    combo_target: QComboBox = None
    # Service
    service: LinkService = None
    # Send Props
    frame_time: RTime = 0
    frame: int = 0
    sent_frame: int = 0
    # Receive Props
    clip = None
    clip_t_pose_data = None
    clip_time = None
    sequence_read_count: int = 24
    current_frame: int = 0
    start_frame: int = 0
    end_frame: int = 0


    def __init__(self):
        QObject.__init__(self)
        self.create_window()

    def show(self):
        self.window.Show()
        self.show_link_state()

    def create_window(self):
        self.window, layout = qt.window("Data Link", 400)

        self.label_header = qt.label(layout, "Data Link: Not Connected", style=qt.STYLE_TITLE)

        row = qt.row(layout)
        self.textbox_host = qt.textbox(row, self.host_name, update=self.update_host)
        self.combo_target = qt.combobox(row, "", options=["Blender", "Unity"], update=self.update_target)

        qt.spacing(layout, 10)

        self.label_status = qt.label(layout, "...", style=qt.STYLE_RL_DESC)

        qt.spacing(layout, 10)

        self.button_link = qt.button(layout, "Listen", self.link_start, toggle=True, value=False)
        qt.button(layout, "Stop", self.link_stop)

        qt.spacing(layout, 20)

        qt.button(layout, "Send Character", self.send_character)
        qt.button(layout, "Rigify Character", self.send_rigify)
        qt.button(layout, "Send Pose", self.send_pose)
        qt.button(layout, "Send Animation", self.send_animation)
        qt.button(layout, "Live Sequence", self.send_sequence)

        qt.stretch(layout, 20)

        #qt.button(layout, "Test 1", tests.show_foot_effector_transforms)
        #qt.button(layout, "Test 2", tests.test2)
        #qt.button(layout, "Test 3", tests.compare_clip_with_bones)

        self.show_link_state()
        self.window.Show()

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
        elif self.service and self.service.is_listening:
            self.textbox_host.setEnabled(False)
            self.combo_target.setEnabled(False)
            self.button_link.setStyleSheet("background-color: #505050; color: white; font: bold")
            self.button_link.setText("Listening...")
            self.label_header.setText("Waiting for Connection")
        else:
            self.textbox_host.setEnabled(True)
            self.combo_target.setEnabled(True)
            self.button_link.setStyleSheet(qt.STYLE_NONE)
            if SERVER_ONLY:
                self.button_link.setText("Start Server")
            else:
                self.button_link.setText("Connect")
            self.label_header.setText("Not Connected")

    def link_start(self):
        if not self.service:
            self.service = LinkService(self)
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

        if op_code == OpCodes.SEQUENCE_REQ:
            self.receive_sequence_req(data)

        if op_code == OpCodes.SEQUENCE:
            self.receive_sequence(data)

        if op_code == OpCodes.SEQUENCE_FRAME:
            self.receive_sequence_frame(data)

    def on_connected(self):
        self.send_notify("Connected")

    def send_notify(self, message):
        notify_json = { "message": message }
        self.service.send(OpCodes.NOTIFY, encode_from_json(notify_json))

    def receive_notify(self, data):
        notify_json = decode_to_json(data)
        self.update_link_status(notify_json["message"])

    def get_export_path(self, name):
        remote_path = self.service.remote_path
        local_path = self.service.local_path
        if remote_path:
            export_folder = remote_path
        else:
            export_folder = local_path
        return os.path.join(export_folder, name)

    def send_character(self):
        avatar = cc.get_first_avatar()
        self.update_link_status(f"Sending Character for Import: {avatar.GetName()}")
        self.send_notify(f"Exporting: {avatar.GetName()}")
        export_path = self.get_export_path(avatar.GetName() + ".fbx")
        export = exporter.Exporter(avatar, no_window=True)
        export.set_data_link_export(export_path)
        export.export_fbx()
        export.export_extra_data()
        self.send_notify(f"Character Import: {avatar.GetName()}")
        export_data = { "path": export_path, "name": avatar.GetName(), "link_id": str(avatar.GetID()) }
        self.service.send(OpCodes.CHARACTER, encode_from_json(export_data))

    def send_rigify(self):
        avatar = cc.get_first_avatar()
        self.update_link_status(f"Requesting Rigify Character: {avatar.GetName()}")
        self.send_notify(f"Rigify: {avatar.GetName()}")
        rigify_data = { "name": avatar.GetName(), "link_id": str(avatar.GetID()) }
        self.service.send(OpCodes.RIGIFY, encode_from_json(rigify_data))

    def send_pose(self):
        avatar = cc.get_first_avatar()
        self.update_link_status(f"Sending Current Pose: {avatar.GetName()}")
        self.send_notify(f"Pose: {avatar.GetName()}")
        # send template data first
        character_template = encode_character_template(avatar)
        self.service.send(OpCodes.TEMPLATE, character_template)
        # send pose data
        pose_data = encode_pose_data(avatar)
        self.service.send(OpCodes.POSE, pose_data)

    def send_animation(self):
        return

    def send_sequence(self):
        avatar = cc.get_first_avatar()
        self.update_link_status(f"Sending Animation Sequence: {avatar.GetName()}")
        self.send_notify(f"Animation Sequence: {avatar.GetName()}")
        # reset animation to start
        self.frame_time = reset_animation()
        self.frame = get_current_frame()
        # send animation meta data
        anim_data = get_animation_data(avatar)
        self.service.send(OpCodes.SEQUENCE, encode_from_json(anim_data))
        # send template data first
        template_data = encode_character_template(avatar)
        self.service.send(OpCodes.TEMPLATE, template_data)
        # start the sending sequence
        self.service.timer.setInterval(0)
        self.service.sequence.connect(self.send_sequence_frame)

    def send_sequence_frame(self):
        avatar = cc.get_first_avatar()
        # send current sequence frame pose
        self.update_link_status(f"Sending Animation Frame: {get_current_frame()}")
        pose_data = encode_pose_data(avatar)
        self.service.send(OpCodes.SEQUENCE_FRAME, pose_data)
        self.sent_frame = get_current_frame()
        # check for end
        if self.sent_frame == get_end_frame():
            self.service.sequence.disconnect()
            self.service.timer.setInterval(TIMER_INTERVAL)
            return
        # advance to next frame now
        self.frame_time = next_frame(self.frame_time)
        self.frame = get_current_frame()
        #qt.do_events()

    def receive_character_template(self, data):
        utils.log_info(f"Character Template Received")
        self.update_link_status(f"Character Template Data Recevied")
        self.character_template = decode_character_template(data)

    def receive_pose(self, data):
        avatar = cc.get_first_avatar()
        self.update_link_status(f"Character Pose Recevied")
        self.clip, self.clip_t_pose_data = prep_avatar_clip(avatar, 1)
        pose_data = decode_pose_data(self.character_template, data)
        apply_pose(avatar, self.clip, get_clip_time(0), pose_data, self.clip_t_pose_data)
        #RGlobal.SetTime(self.clip.ClipTimeToSceneTime(get_clip_time(0)))
        scene_start_time = RGlobal.GetTime()
        scene_end_time = RGlobal.GetTime()
        RGlobal.Play(scene_start_time, scene_end_time)
        print("Done!")

    def receive_sequence(self, data):
        self.update_link_status(f"Character Animation Sequence Incoming...")
        json_data = decode_to_json(data)
        name = json_data["name"]
        avatar = cc.get_first_avatar()
        self.start_frame = json_data["start_frame"]
        self.end_frame = json_data["end_frame"]
        self.current_frame = json_data["current_frame"]
        num_frames = self.end_frame - self.start_frame
        self.service.is_sequence = True
        self.clip, self.clip_t_pose_data = prep_avatar_clip(avatar, num_frames)
        self.service.start_sequence()

    def receive_sequence_frame(self, data):
        #utils.log_info(f"Sequence Frame Received")
        self.current_frame = struct.unpack_from("!I", data, 0)[0]
        self.update_link_status(f"Character Animation Frame: {self.current_frame} Received")
        clip_time = get_clip_time(self.current_frame)
        avatar = cc.get_first_avatar()
        pose_data = decode_pose_data(self.character_template, data)
        apply_pose(avatar, self.clip, clip_time, pose_data, self.clip_t_pose_data)
        #scene_time = self.clip.ClipTimeToSceneTime(clip_time)
        #RGlobal.SetTime(scene_time)
        if self.current_frame == self.end_frame:
            num_frames = self.end_frame - self.start_frame
            self.service.stop_sequence()
            scene_start_time = self.clip.SceneTimeToClipTime(get_clip_time(0))
            scene_end_time = self.clip.SceneTimeToClipTime(get_clip_time(self.current_frame))
            RGlobal.Play(scene_start_time, scene_end_time)
            self.update_link_status(f"Character Animation Sequence Complete: {num_frames} frames")


