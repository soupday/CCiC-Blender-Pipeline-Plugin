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

import RLPy
import PySide2
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
import os, socket, select, struct, time, json, random
import blender, exporter, cc, qt, utils, vars
from enum import IntEnum

LOCALHOST = "127.0.0.1"
BLENDER_PORT = 9334
UNITY_PORT = 9335
RL_PORT = 9333
TIMER_INTERVAL = 1000/30
MAX_CHUNK_SIZE = 32768
HANDSHAKE_TIMEOUT_S = 60
KEEPALIVE_TIMEOUT_S = 30
PING_INTERVAL_S = 10
SERVER_ONLY = True
CLIENT_ONLY = False
EMPTY_SOCKETS = []

class OpCodes(IntEnum):
    NONE = 0
    HELLO = 1
    PING = 2
    STOP = 10
    DISCONNECT = 11
    CHARACTER = 100
    RIGIFY = 110
    SKELETON = 200
    POSE = 201
    SEQUENCE = 202
    SEQUENCE_REQ = 203
    SEQUENCE_FRAME = 204


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


def encode_skeleton_data(avatar: RLPy.RIAvatar):
    # num_bones: int,
    # bone_name: str (x num_bones)

    SC: RLPy.RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones = SC.GetSkinBones()

    data = bytearray()
    data += struct.pack("!I", len(skin_bones))
    for bone in skin_bones:
        name = bone.GetName()
        print(f"Name: {name}")
        data += pack_string(name)
    return data


def encode_pose_data(avatar: RLPy.RIAvatar):
    SC: RLPy.RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones = SC.GetSkinBones()

    data = bytearray()
    data += struct.pack("!I", get_current_frame())
    for bone in skin_bones:
        T: RLPy.RTransform = bone.WorldTransform()
        t: RLPy.RVector3 = T.T()
        r: RLPy.RQuaternion = T.R()
        s: RLPy.RVector3 = T.S()
        data += struct.pack("!ffffffffff", t.x, t.y, t.z, r.x, r.y, r.z, r.w, s.x, s.y, s.z)
    return data


def get_animation_data(avatar: RLPy.RIAvatar):
    fps: RLPy.RFps = RLPy.RGlobal.GetFps()
    current_time: RLPy.RTime = RLPy.RGlobal.GetTime()
    start_time: RLPy.RTime = RLPy.RGlobal.GetStartTime()
    end_time: RLPy.RTime = RLPy.RGlobal.GetEndTime()
    current_frame = fps.GetFrameIndex(current_time)
    start_frame = fps.GetFrameIndex(start_time)
    end_frame = fps.GetFrameIndex(end_time)
    data = {
        "name": avatar.GetName(),
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
    start_time = RLPy.RGlobal.GetStartTime()
    RLPy.RGlobal.SetTime(start_time)
    return start_time


def get_current_frame():
    fps: RLPy.RFps = RLPy.RGlobal.GetFps()
    current_time = RLPy.RGlobal.GetTime()
    current_frame = fps.GetFrameIndex(current_time)
    return current_frame

def get_end_frame():
    fps: RLPy.RFps = RLPy.RGlobal.GetFps()
    end_time: RLPy.RTime = RLPy.RGlobal.GetEndTime()
    end_frame = fps.GetFrameIndex(end_time)
    return end_frame


def next_frame(time):
    fps: RLPy.RFps = RLPy.RGlobal.GetFps()
    next_time = fps.GetNextFrameTime(time)
    RLPy.RGlobal.SetTime(next_time)
    return next_time








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
        self.local_app = RLPy.RApplication.GetProductName()
        self.local_version = RLPy.RApplication.GetProductVersion()
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
        if self.client_sock and (self.is_connected or self.is_connecting):
            r,w,x = select.select(self.client_sockets, self.empty_sockets, self.empty_sockets, 0)
            if r:
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
            if data:
                json_data = decode_to_json(data)
                self.remote_app = json_data["Application"]
                self.remote_version = json_data["Version"]
                self.remote_path = json_data["Path"]
                utils.log_info(f"Connected to: {self.remote_app} {self.remote_version}")
                utils.log_info(f"Using file path: {self.remote_path}")
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








class DataLink(QObject):
    window: QWindow = None
    host_name: str = "localhost"
    host_ip: str = "127.0.0.1"
    host_port: int = BLENDER_PORT
    target: str = "Blender"
    # UI
    button_link: QPushButton = None
    textbox_host: QLineEdit = None
    combo_target: QComboBox = None
    # Service
    service: LinkService = None
    #
    frame_time: RLPy.RTime = 0
    frame: int = 0
    sent_frame: int = 0

    def __init__(self):
        QObject.__init__(self)
        self.create_window()

    def show(self):
        self.window.Show()
        self.show_link_state()

    def create_window(self):
        self.window, layout = qt.window("Data Link", 400)

        qt.label(layout, "Some Label")

        row = qt.row(layout)
        self.textbox_host = qt.textbox(row, self.host_name, update=self.update_host)
        self.combo_target = qt.combobox(row, "", options=["Blender", "Unity"], update=self.update_target)

        qt.spacing(layout, 10)

        self.button_link = qt.button(layout, "Listen", self.link_start, toggle=True, value=False)
        qt.button(layout, "Stop", self.link_stop)

        qt.spacing(layout, 10)

        qt.button(layout, "Send Character", self.send_character)
        qt.button(layout, "Rigify Character", self.send_rigify)
        qt.button(layout, "Send Pose", self.send_pose)
        qt.button(layout, "Send Animation", self.send_sequence)

        qt.stretch(layout, 10)

        self.show_link_state()
        self.window.Show()

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
        elif self.service and self.service.is_listening:
            self.textbox_host.setEnabled(False)
            self.combo_target.setEnabled(False)
            self.button_link.setStyleSheet("background-color: #505050; color: white; font: bold")
            self.button_link.setText("Listening...")
        else:
            self.textbox_host.setEnabled(True)
            self.combo_target.setEnabled(True)
            self.button_link.setStyleSheet(qt.STYLE_NONE)
            if SERVER_ONLY:
                self.button_link.setText("Start Server")
            else:
                self.button_link.setText("Connect")

    def link_start(self):
        if not self.service:
            self.service = LinkService(self)
            self.service.changed.connect(self.show_link_state)
            self.service.received.connect(self.parse)
        self.service.service_start(self.host_ip, self.host_port)

    def link_stop(self):
        if self.service:
            self.service.service_stop()

    def link_disconnect(self):
        if self.service:
            self.service.service_disconnect()

    def parse(self, op_code, data):
        if op_code == OpCodes.POSE:
            print(f"Do something with the pose...")

        if op_code == OpCodes.SEQUENCE_REQ:
            print(f"Sequence Request")
            self.receive_sequence_req(data)

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
        export_path = self.get_export_path(avatar.GetName() + ".fbx")
        export = exporter.Exporter(avatar, no_window=True)
        export.set_data_link_export(export_path)
        export.export_fbx()
        export.export_extra_data()
        export_data = { "path": export_path, "name": avatar.GetName() }
        self.service.send(OpCodes.CHARACTER, encode_from_json(export_data))

    def send_rigify(self):
        avatar = cc.get_first_avatar()
        rigify_data = { "name": avatar.GetName() }
        self.service.send(OpCodes.RIGIFY, encode_from_json(rigify_data))

    def send_pose(self):
        avatar = cc.get_first_avatar()
        # send skeleton data first
        skeleton_data = encode_skeleton_data(avatar)
        self.service.send(OpCodes.SKELETON, skeleton_data)
        # send pose data
        pose_data = encode_pose_data(avatar)
        self.service.send(OpCodes.POSE, pose_data)

    def send_sequence(self):
        avatar = cc.get_first_avatar()
        # reset animation to start
        self.frame_time = reset_animation()
        self.frame = get_current_frame()
        # send animation meta data
        anim_data = get_animation_data(avatar)
        self.service.send(OpCodes.SEQUENCE, encode_from_json(anim_data))
        # send skeleton data first
        skeleton_data = encode_skeleton_data(avatar)
        self.service.send(OpCodes.SKELETON, skeleton_data)
        # start the sending sequence
        self.service.timer.setInterval(1000/60)
        self.service.sequence.connect(self.send_sequence_frame)

    def send_sequence_frame(self):
        avatar = cc.get_first_avatar()
        # send current sequence frame pose
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

    def receive_sequence_req(self, data):
        req_data = decode_to_json(data)
        end_frame = get_end_frame()
        req_frame = req_data["frame"]
        req_count = req_data["count"]
        print(f"frame: {self.frame}, end_frame: {end_frame}, req_frame: {req_frame}")



