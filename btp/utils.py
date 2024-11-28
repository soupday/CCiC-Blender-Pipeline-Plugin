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
import copy
import urllib.parse
import time
import random
import shutil

LOG_TIMER = {}
LOG_LEVEL = "DETAILS"
LOG_INDENT = 0
DO_EVENTS = True


def log(message):
    log_info(message)


def log_reset():
    global LOG_INDENT, LOG_TIMER
    LOG_INDENT = 0
    LOG_TIMER = 0


def log_events(enable):
    global DO_EVENTS
    DO_EVENTS = enable


def log_indent():
    global LOG_INDENT
    LOG_INDENT += 5


def log_recess():
    global LOG_INDENT
    LOG_INDENT -= 5


def log_spacing():
    return " " * LOG_INDENT


def log_detail(msg):
    """Log an info message to console."""
    if LOG_LEVEL == "DETAILS":
        print((" " * LOG_INDENT) + msg)


def log_info(msg):
    """Log an info message to console."""
    if LOG_LEVEL == "ALL" or LOG_LEVEL == "DETAILS":
        print((" " * LOG_INDENT) + msg)


def log_always(msg):
    """Log an info message to console."""
    print((" " * LOG_INDENT) + msg)


def log_warn(msg):
    """Log a warning message to console."""
    if LOG_LEVEL == "ALL" or LOG_LEVEL == "DETAILS" or LOG_LEVEL == "WARN":
        print((" " * LOG_INDENT) + "Warning: " + msg)


def log_error(msg, e = None):
    """Log an error message to console and raise an exception."""
    indent = LOG_INDENT
    if indent > 1: indent -= 1
    print("*" + (" " * indent) + "Error: " + msg)
    if e is not None:
        print("    -> " + getattr(e, 'message', repr(e)))


def start_timer(name="NONE"):
    global LOG_TIMER
    LOG_TIMER[name] = [time.perf_counter(), 0.0, 0]


def mark_timer(name="NONE"):
    LOG_TIMER[name][0] = time.perf_counter()


def update_timer(name="NONE"):
    global LOG_TIMER
    pc = time.perf_counter()
    duration = pc - LOG_TIMER[name][0]
    LOG_TIMER[name][1] += duration
    LOG_TIMER[name][0] = pc
    LOG_TIMER[name][2] += 1


def log_timer(msg, unit = "s", name="NONE"):
    global LOG_TIMER
    if LOG_TIMER[name][2] == 0:
        update_timer(name)
    if LOG_LEVEL == "ALL":
        total_duration = LOG_TIMER[name][1]
        if unit == "ms":
            total_duration *= 1000
        elif unit == "us":
            total_duration *= 1000000
        elif unit == "ns":
            total_duration *= 1000000000
        print((" " * LOG_INDENT) + msg + ": " + str(total_duration) + " " + unit)


def get_current_path():
    return os.path.dirname(os.path.dirname(os.path.realpath(__file__)))


def get_resource_path(sub_folder, file_name=""):
    path = get_current_path()
    resource_path = os.path.join(path, sub_folder, file_name)
    return resource_path


def RGB_to_rgb(RGB):
    r = min(max(RGB[0] / 255, 0), 1)
    g = min(max(RGB[1] / 255, 0), 1)
    b = min(max(RGB[2] / 255, 0), 1)
    return [r,g,b]


def rgb_to_RGB(rgb):
    R = min(max(rgb[0] * 256.0, 0), 255)
    G = min(max(rgb[1] * 256.0, 0), 255)
    B = min(max(rgb[2] * 256.0, 0), 255)
    return [R,G,B]


def copy_dict_obj(from_obj, to_obj):
    for key in from_obj.keys():
        if type(from_obj[key]) is list or type(from_obj[key]) is dict:
            to_obj[key] = copy.deepcopy(from_obj[key])
        else:
            to_obj[key] = from_obj[key]


def url_encode(plain_text):
    return urllib.parse.quote(plain_text)


def url_decode(url_encoded_text):
    return urllib.parse.unquote(url_encoded_text)


def first(*things):
    for thing in things:
        if thing:
            return thing


def lerp(A, B, t):
    return A + (B - A) * t


def lerp_int(A, B, t):
    return int(A + (B - A) * t)


def lerp_byte(A, B, T):
    # integer lerp (A/B/F=0-255) : (A*(256-T) + B*T) >> 8
    return int(A*(256-T) + B*T) >> 8


def inverse_lerp(A, B, v):
    return (v - A) / (B - A)


def clamp(x, low = 0, high = 1):
    return min(max(x, low), high)


def clamp_int(x, low = 0, high = 1):
    return int(min(max(x, low), high))


def smoothstep(A, B, x):
    t = (x - A) / (B - A)
    return t * t * (3 - 2*t)


def remap(in_min, in_max, out_min, out_max, v, clamp = True):
    t = inverse_lerp(in_min, in_max, v)
    result = lerp(out_min, out_max, t)
    if clamp:
        result = min(max(result, out_min), out_max)
    return result


def name_contains_distinct_keywords(name : str, keywords : list):
    """Does the name contain the supplied keywords in distinct form:\n
       i.e. capitalized "OneTwoThree"\n
            or hungarian notation "oneTwoThree"\n
            or surrouned by underscores "one_two_three"
    """

    name_lower = name.lower()
    name_length = len(name)

    SEPS = [" ", "-", "_", "+", "!", "$"]

    for k in keywords:
        k_lower = k.lower()
        k_length = len(k)

        s = name_lower.find(k_lower)
        e = s + k_length

        if s >= 0:

            if name_lower == k_lower:
                return True

            # is the keyword at the start, ending with separator
            if s == 0 and e < name_length and name_lower[e] in SEPS:
                return True

            # is the keyword at the end, preceded by separator
            if s > 0 and e == name_length and name_lower[s - 1] in SEPS:
                return True

            # is the keyword surrounded by separators
            if s > 0 and e < name_length:
                if name_lower[s - 1] in SEPS and name_lower[e] in SEPS:
                    return True

            # match distinct keyword at start of name (any capitalization) or captitalized anywhere else
            if s == 0 or name[s].isupper():
                if e >= name_length or not name[e].islower():
                    return True

    return False


def name_is_split_mesh(name):
    if (len(name) >= 4 and
        name[-1].isdigit() and
        name[-2].isdigit() and
        name[-3] == "S" and
        name[-4] == "_"):
        return True
    return False


def make_folder(path):
    folder, file = os.path.split(path)
    os.makedirs(folder, exist_ok=True)
    if os.path.exists(folder):
        return True
    return False


def fd2(s):
    return '{0:.2f}'.format(s)


def dot(A, B):
    C = A.copy()
    for i in range(0, len(A)):
        C[i] *= B[i]
    return C


def cap(text: str):
    if text and len(text) >= 1:
        return text[0].upper() + text[1:]
    return text


def linear_to_srgbx(x):
    if x < 0.0:
        return 0.0
    elif x < 0.0031308:
        return x * 12.92
    elif x < 1.0:
        return 1.055 * pow(x, 1.0 / 2.4) - 0.055
    else:
        return pow(x, 5.0 / 11.0)


def linear_to_srgb(color):
    return [
        linear_to_srgbx(color[0]),
        linear_to_srgbx(color[1]),
        linear_to_srgbx(color[2]),
    ]


def srgb_to_linearx(x):
    if x <= 0.04045:
        return x / 12.95
    elif x < 1.0:
        return pow((x + 0.055) / 1.055, 2.4)
    else:
        return pow(x, 2.2)


def srgb_to_linear(color):
    return [
        srgb_to_linearx(color[0]),
        srgb_to_linearx(color[1]),
        srgb_to_linearx(color[2]),
    ]


def random_string(length):
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    l = len(chars)
    res = ""
    for i in range(0, length):
        r = random.randrange(0, l)
        res += chars[r]
    return res


def safe_long_unc_path(path):
    if path.startswith("//") or path.startswith("\\\\"):
        return "\\\\?\\UNC" + path[1:]
    else:
        return "\\\\?\\" + path


def safe_copy_file(from_path, to_path):
    safe_from_path = safe_long_unc_path(from_path)
    safe_to_path = safe_long_unc_path(to_path)
    shutil.copyfile(safe_from_path, safe_to_path)


def get_unique_folder_path(parent_folder, folder_name, create=False):
    suffix = 1
    base_name = folder_name
    folder_path = os.path.normpath(os.path.join(parent_folder, folder_name))
    while os.path.exists(folder_path):
        folder_name = base_name + "_" + str(suffix)
        suffix += 1
        folder_path = os.path.normpath(os.path.join(parent_folder, folder_name))
    if create:
        os.makedirs(folder_path)
    return folder_path


def make_sub_folder(parent_folder, folder_name):
    try:
        folder_path = os.path.normpath(os.path.join(parent_folder, folder_name))
        os.makedirs(folder_path, exist_ok=True)
        return folder_path
    except:
        return None


def contains_path(path1, path2):
    """Returns True if path2 is a parent path of path1"""
    if not os.path.isdir(path1):
        path1 = os.path.dirname(path1)
    if not os.path.isdir(path2):
        path1 = os.path.dirname(path2)
    path1 = os.path.normcase(os.path.normpath(os.path.abspath(path1)))
    path2 = os.path.normcase(os.path.normpath(os.path.abspath(path2)))
    return path1.startswith(path2)
    #parent = os.path.dirname(path1)
    #while parent:
    #    if os.path.samefile(parent, path2):
    #        return True
    #    if os.path.ismount(parent) and parent.endswith(":\\"):
    #        break
    #    parent = os.path.dirname(parent)
    #return False


def stop_now():
    raise Exception("STOP!")


