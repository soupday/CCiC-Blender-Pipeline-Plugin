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
import os, socket, struct, time, json, random
import pose, blender, cc, qt, utils, vars

LOCALHOST = "127.0.0.1"
BLENDER_PORT = 9334
UNITY_PORT = 9335
RL_PORT = 9333
INTERVAL_MS = 100

HANDSHAKE_TIMEOUT_S = 60
KEEPALIVE_TIMEOUT_S = 30
PING_INTERVAL_S = 10

SERVER_ONLY = True


class DataLink(QObject):
    timer: QTimer = None
    window: QWindow = None
    host_name: str = "localhost"
    host_ip: str = "127.0.0.1"
    host_port: int = BLENDER_PORT
    target: str = "Blender"
    server_sock: socket.socket = None
    client_sock: socket.socket = None
    client_ip: str = "127.0.0.1"
    client_port: int = BLENDER_PORT
    link_server: bool = False
    link_client: bool = False
    link_listening: bool = False
    link_connected: bool = False
    ping_timer: float = 0
    keepalive_timer: float = 0
    time: float = 0
    # UI
    button_link: QPushButton = None
    textbox_host: QLineEdit = None
    combo_target: QComboBox = None


    def __init__(self):
        QObject.__init__(self)
        self.create_window()

    def show(self):
        self.window.Show()
        self.show_link_state()

    def create_window(self):
        self.window, layout = qt.window("Data Link", 400)
        qt.label(layout, "A LABAL")
        row = qt.row(layout)
        self.textbox_host = qt.textbox(row, self.host_name, update=self.update_host)
        self.combo_target = qt.combobox(row, "", options=["Blender", "Unity"], update=self.update_target)
        self.button_link = qt.button(layout, "Listen", self.link_start, toggle=True, value=False)
        qt.button(layout, "Stop", self.link_stop)
        qt.spacing(layout, 10)
        qt.button(layout, "TEST", self.send_test)
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
        if self.link_connected:
            self.textbox_host.setEnabled(False)
            self.combo_target.setEnabled(False)
            self.button_link.setStyleSheet("background-color: #82be0f; color: black; font: bold")
            self.button_link.setText("Linked")
        elif self.link_listening:
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

    def start_server(self):
        self.link_listening = False
        try:
            self.keepalive_timer = HANDSHAKE_TIMEOUT_S
            self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_sock.bind(('', RL_PORT))
            self.server_sock.setblocking(0)
            self.server_sock.listen(5)
            self.link_listening = True
            utils.log_info(f"Listening on TCP *:{RL_PORT}")
        except:
            utils.log_error(f"Unable to start server on TCP *:{RL_PORT}")

    def stop_server(self):
        self.link_listening = False
        if self.server_sock:
            utils.log_info(f"Closing Server Socket")
            self.server_sock.close()
            self.link_server = False

    def stop_client(self):
        self.link_connected = False
        if self.client_sock:
            utils.log_info(f"Closing Client Socket")
            self.client_sock.close()
            self.link_client = False

    def start_timer(self):
        self.time = time.time()
        if not self.timer:
            self.timer = QTimer(self)
            self.timer.setInterval(INTERVAL_MS)
            self.timer.timeout.connect(self.listen_loop)
        self.timer.start()
        utils.log_info(f"timer started")

    def stop_timer(self):
        if self.timer:
            self.timer.stop()
            utils.log_info(f"timer stopped")

    def try_connect(self):
        self.link_connected = False
        utils.log_info(f"attempting to connect")
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host_ip, self.host_port))
            self.link_connected = True
            self.link_client = True
            self.client_sock = sock
            self.client_ip = self.host_ip
            self.client_port = self.host_port
            self.keepalive_timer = KEEPALIVE_TIMEOUT_S
            self.ping_timer = PING_INTERVAL_S
            sock.setblocking(0)
            utils.log_info(f"Connected to data link server on {self.host_ip}:{self.host_port}")
            return True
        except:
            utils.log_info(f"Host not listening...")
            return False

    def recv(self, size=40960):
        try:
            if self.client_sock:
                message = self.client_sock.recv(size)
                return message
        except:
            pass
        return None

    def accept(self):
        try:
            sock, address = self.server_sock.accept()
            self.client_sock = sock
            self.client_ip = address[0]
            self.client_port = address[1]
            self.link_connected = True
            self.link_server = True
            self.keepalive_timer = KEEPALIVE_TIMEOUT_S
            self.ping_timer = PING_INTERVAL_S
            utils.log_info(f"Incoming connection received from: {address[0]}:{address[1]}")
            self.show_link_state()
            self.ping()
        except:
            return

    def link_start(self):
        if not self.link_listening and not self.link_connected:
            self.start_timer()
            if SERVER_ONLY:
                self.start_server()
            else:
                if not self.try_connect():
                    self.start_server()
            self.show_link_state()
        elif self.link_listening and self.link_connected:
            self.link_disconnect()

    def link_disconnect(self):
        self.send_disconnect()
        self.stop_client()
        self.show_link_state()

    def link_stop(self):
        self.send_stop()
        self.stop_timer()
        self.stop_client()
        self.stop_server()
        self.show_link_state()

    def listen_loop(self):
        current_time = time.time()
        delta_time = current_time - self.time
        self.time = current_time

        if self.link_connected:
            self.ping_timer -= delta_time
            self.keepalive_timer -= delta_time

            if self.ping_timer <= 0:
                self.ping()

            if self.keepalive_timer <= 0:
                utils.log_info("lost connection!")
                self.link_stop()

        elif self.link_listening:
            self.keepalive_timer -= delta_time

            if self.keepalive_timer <= 0:
                utils.log_info("no connection within time limit!")
                self.link_stop()

        if self.link_listening and not self.link_connected:
            self.accept()

        if self.link_connected:
            message = self.recv()
            if message:
                self.parse(message)

    def parse(self, message):
        self.keepalive_timer = KEEPALIVE_TIMEOUT_S
        text = message.decode("utf-8")
        print(f"Message: {text}")

        if text == "STOP":
            self.link_connected = False
            self.link_stop()
            utils.log_info(f"Link terminated by request!")

        if text == "DISCONNECT":
            self.link_connected = False
            self.link_disconnect()
            utils.log_info(f"Link terminated by request!")

    def send(self, message):
        if self.client_sock and self.link_connected:
            try:
                self.client_sock.sendall(message)
            except:
                utils.log_error("Error sending message, disconnecting...")
                self.stop_client()
                self.show_link_state()

    def send_stop(self):
        self.send(b"STOP")

    def send_disconnect(self):
        self.send(b"DISCONNECT")

    def ping(self):
        self.ping_timer = PING_INTERVAL_S
        self.send(b"PING")

    def send_test(self):
        if self.server_sock and self.link_connected:
            avatar = cc.get_first_avatar()
            pose_data = pose.get_pose_data(avatar)
            #self.send_json_data(pose_data)

    def send_json_data(self, json_data, op):
        if self.server_sock and self.link_connected:
            data_set = self.make_data_set(json_data, op)
            for s, chunk_data in enumerate(data_set):
                utils.log_info(f"sending data chunk {s} ({len(chunk_data)}")
                self.server_sock.sendto(chunk_data, (self.host_ip, self.host_port))

    def make_data_set(self, json_data, op, chunk_size=8192):

        chunk_bytes = byte_serialize(json_data)
        self.server_sock.sendall()

        l = len(chunk_bytes)
        if l % chunk_size > 0:
            num = l / chunk_size + 1
        else:
            num = l / chunk_size
        uid = random.randrange(1,2147483647)
        header = {
            "uid": uid,
            "op": op,
            "size": len(chunk_bytes),
            "num": num
        }
        chunk_bytes = bytearray()
        chunk_bytes.extend(struct.pack("<II", 0,0))
        chunk_bytes.extend(byte_serialize(header))

        data_set = [chunk_bytes]

        s = 0
        i: int
        for s, i in enumerate(range(0, l, chunk_size)):
            chunk_bytes = bytearray()
            chunk_bytes.extend(struct.pack("<II", i, s))
            chunk_bytes.extend(chunk_bytes[i:i+chunk_size])
            data_set.append(chunk_bytes)

        return data_set



def byte_serialize(json_data):
    json_string = json.dumps(json_data)
    json_bytes = bytearray(json_string, "utf-8")
    return json_bytes