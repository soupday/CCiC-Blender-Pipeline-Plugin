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

import os
import RLPy
import json
import os
import gzip

VERSION = "2.0.0"

BLENDER_PROCESS = None
BLENDER_PATH = None
EXPORT_PATH = None


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
        print(f"Error reading Json Data: {json_path}")
        return None


def write_json(json_data, path):
    json_object = json.dumps(json_data, indent = 4)
    with open(path, "w") as write_file:
        write_file.write(json_object)


def read_temp_state():
    global BLENDER_PATH
    global EXPORT_PATH
    res = RLPy.RGlobal.GetPath(RLPy.EPathType_CustomContent, "")
    temp_path = res[1]
    temp_state_path = os.path.join(temp_path, "GoB_plugin.txt")
    if os.path.exists(temp_state_path):
        temp_state_json = read_json(temp_state_path)
        if temp_state_json:
            try:
                BLENDER_PATH = temp_state_json["blender_path"]
                EXPORT_PATH = temp_state_json["export_path"]
            except:
                pass


def write_temp_state():
    global BLENDER_PATH
    global EXPORT_PATH
    res = RLPy.RGlobal.GetPath(RLPy.EPathType_CustomContent, "")
    temp_path = res[1]
    temp_state_path = os.path.join(temp_path, "GoB_plugin.txt")
    temp_state_json = {
        "blender_path": BLENDER_PATH,
        "export_path": EXPORT_PATH,
    }
    write_json(temp_state_json, temp_state_path)


def detect_paths():
    global BLENDER_PATH
    global EXPORT_PATH

    read_temp_state()

    changed = False

    if not BLENDER_PATH:
        blender_base_path = "C:\\Program Files\\Blender Foundation\\"
        blender_versions = [ "4.0", "3.6", "3.5", "3.4", "3.3", "3.2", "3.1", "3.0", "2.93", "2.92", "2.91", "2.90", "2.83" ]
        for ver in blender_versions:
            B = f"Blender {ver}"
            try_path = os.path.join(blender_base_path, B, "blender.exe")
            if os.path.exists(try_path):
                BLENDER_PATH = try_path
                changed = True
                break

    if not EXPORT_PATH:
        res = RLPy.RGlobal.GetPath(RLPy.EPathType_Temp, "")
        path = os.path.join(res[1], "Data Link")
        EXPORT_PATH = path
        changed = True

    if EXPORT_PATH:
        if not os.path.exists(EXPORT_PATH):
            os.makedirs(EXPORT_PATH, exist_ok=True)

    if changed:
        write_temp_state()

    print(BLENDER_PATH)
    print(EXPORT_PATH)


