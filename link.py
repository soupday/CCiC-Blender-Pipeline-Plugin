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
import pose, blender, cc, qt, utils, vars
from enum import IntEnum

LOCALHOST = "127.0.0.1"
BLENDER_PORT = 9334
UNITY_PORT = 9335
RL_PORT = 9333
INTERVAL_MS = 100
MAX_CHUNK_SIZE = 32768
HANDSHAKE_TIMEOUT_S = 60
KEEPALIVE_TIMEOUT_S = 30
PING_INTERVAL_S = 10
SERVER_ONLY = True
EMPTY_SOCKETS = []

class OpCodes(IntEnum):
    NONE = 0
    HELLO = 1
    PING = 2
    STOP = 10
    DISCONNECT = 11
    POSE = 100

def byte_serialize(json_data):
    json_string = json.dumps(json_data)
    json_bytes = bytearray(json_string, "utf-8")
    return json_bytes


class LinkService(QObject):
    timer: QTimer = None
    server_sock: socket.socket = None
    client_sock: socket.socket = None
    server_sockets = []
    client_sockets = []
    empty_sockets = []
    client_ip: str = "127.0.0.1"
    client_port: int = BLENDER_PORT
    is_server: bool = False
    is_client: bool = False
    is_listening: bool = False
    is_connected: bool = False
    is_initializing: bool = False
    ping_timer: float = 0
    keepalive_timer: float = 0
    time: float = 0
    # Signals
    listening = Signal()
    initializing = Signal()
    connected = Signal()
    lost_connection = Signal()
    server_stopped = Signal()
    client_stopped = Signal()
    received = Signal()
    accepted = Signal()
    sent = Signal()
    changed = Signal()

    def start_server(self):
        self.is_listening = False
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
            utils.log_error(f"Unable to start server on TCP *:{RL_PORT}")

    def stop_server(self):
        self.is_listening = False
        if self.server_sock:
            utils.log_info(f"Closing Server Socket")
            self.server_sock.close()
            self.server_sock = None
            self.server_sockets = []
            self.is_server = False
            self.server_stopped.emit()
            self.changed.emit()

    def start_timer(self):
        self.time = time.time()
        if not self.timer:
            self.timer = QTimer(self)
            self.timer.setInterval(INTERVAL_MS)
            self.timer.timeout.connect(self.loop)
        self.timer.start()
        utils.log_info(f"Service timer started")

    def stop_timer(self):
        if self.timer:
            self.timer.stop()
            utils.log_info(f"Service timer stopped")

    def try_start_client(self, host, port):
        self.is_connected = False
        utils.log_info(f"Attempting to connect")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            self.is_connected = False
            self.is_initializing = True
            self.is_client = True
            self.client_sock = sock
            self.client_sockets = [sock]
            self.client_ip = self.host_ip
            self.client_port = self.host_port
            self.keepalive_timer = KEEPALIVE_TIMEOUT_S
            self.ping_timer = PING_INTERVAL_S
            self.send(OpCodes.HELLO)
            utils.log_info(f"Initializing data link server on {self.host_ip}:{self.host_port}")
            self.initializing.emit()
            self.changed.emit()
            return True
        except:
            utils.log_info(f"Host not listening...")
            return False

    def stop_client(self):
        self.is_connected = False
        if self.client_sock:
            utils.log_info(f"Closing Client Socket")
            self.client_sock.close()
            self.client_sock = None
            self.client_sockets = []
            self.is_client = False
            self.client_stopped.emit()
            self.changed.emit()

    def recv(self):
        if self.client_sock:
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
        if self.server_sock:
            r,w,x = select.select(self.server_sockets, self.empty_sockets, self.empty_sockets, 0)
            if r:
                sock, address = self.server_sock.accept()
                self.client_sock = sock
                self.client_sockets = [sock]
                self.client_ip = address[0]
                self.client_port = address[1]
                self.is_connected = True
                self.is_server = True
                self.keepalive_timer = KEEPALIVE_TIMEOUT_S
                self.ping_timer = PING_INTERVAL_S
                utils.log_info(f"Incoming connection received from: {address[0]}:{address[1]}")
                self.send(OpCodes.PING)
                self.accepted.emit(self.client_ip, self.client_port)
                self.changed.emit()

    def parse(self, op_code):
        if op_code == OpCodes.HELLO:
            utils.log_info(f"Hello Received")
            if self.is_initializing:
                self.is_initializing = False
                self.is_connected = True
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
        if not self.is_listening and not self.is_connected:
            self.start_timer()
            if SERVER_ONLY:
                self.start_server()
            else:
                if not self.try_start_client(host, port):
                    self.start_server()
        elif self.is_listening and self.is_connected:
            self.service_disconnect()

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

        if self.is_listening and not self.is_connected:
            self.accept()

        if self.is_connected:
            self.recv()

    def send(self, op_code, json_data = None):
        if self.client_sock and self.is_connected:
            try:
                json_bytes = None
                json_len = 0
                if json_data:
                    json_bytes = byte_serialize(json_data)
                    json_len = len(json_bytes)
                header = struct.pack("!II", op_code, json_len)
                data = bytearray()
                data.extend(header)
                if json_bytes:
                    data.extend(json_bytes)
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

        qt.button(layout, "TEST", self.send_test)

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
        if self.service:
            self.service.service_start(self.host_ip, self.host_port)
        else:
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

    def parse(self, op_code, message):
        if message:
            text = message.decode("utf-8")
            json_data = json.load(text)
            print(f"Message: {json_data}")

        if op_code == OpCodes.POSE:
            print(f"Do something with the pose...")

    def send_test(self):
        avatar = cc.get_first_avatar()
        pose_data = pose.get_pose_data(avatar)
        self.service.send(OpCodes.POSE, pose_data)

