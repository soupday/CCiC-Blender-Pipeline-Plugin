
import subprocess
import os
import RLPy
import re
from . import link, cc, exporter, vars

GOB_AVATAR = None
GOB_FBX_PATH = None
GOB_CONNECTED = False
GOB_DONE = False

def go_b_1():
    LINK = link.get_data_link()
    LINK.link_start()
    LINK.service.connected.connect(go_b_connected)
    write_script()
    launch_blender()


def go_b():
    global GOB_AVATAR, GOB_FBX_PATH, GOB_CONNECTED, GOB_DONE
    GOB_FBX_PATH = None
    GOB_AVATAR = None
    GOB_CONNECTED = False
    GOB_DONE = False

    export_path = vars.EXPORT_PATH
    avatar = cc.get_first_avatar()
    if avatar:

        RLPy.RScene.SelectObject(avatar)

        LINK = link.get_data_link()
        LINK.link_start()
        LINK.service.connected.connect(go_b_connected)

        write_script()
        launch_blender()

        # export the avatar while blender launches
        fbx_path = os.path.join(export_path, avatar.GetName() + ".fbx")
        export = exporter.Exporter(avatar, no_window=True)
        export.set_go_b_export(fbx_path)
        export.export_fbx()
        export.export_extra_data()
        GOB_FBX_PATH = fbx_path
        GOB_AVATAR = avatar

        # try to finish after exporting avatar
        go_b_finish()


def go_b_connected():
    global GOB_AVATAR, GOB_FBX_PATH, GOB_CONNECTED, GOB_DONE
    GOB_CONNECTED = True

    # try to finish after connecting
    go_b_finish()


def go_b_finish():
    global GOB_AVATAR, GOB_FBX_PATH, GOB_CONNECTED, GOB_DONE
    if GOB_FBX_PATH and GOB_CONNECTED and not GOB_DONE:
        GOB_DONE = True
        LINK = link.get_data_link()
        LINK.service.connected.disconnect(go_b_connected)
        LINK.send_actor_exported(GOB_AVATAR, GOB_FBX_PATH)
        LINK.send_pose()
        LINK.sync_lights()
        GOB_AVATAR = None
        GOB_FBX_PATH = None
        GOB_CONNECTED = False
        GOB_DONE = False


def start_datalink():
    LINK = link.get_data_link()
    LINK.link_start()


def get_script_path():
    temp_path = vars.EXPORT_PATH
    script_path = os.path.join(temp_path, "start_data_link.py")
    return script_path


def write_script():
    script_path = get_script_path()
    script_text = """
import bpy
print("HELLO!")
bpy.ops.ccic.datalink(param="START")
    """
    with open(script_path, 'w') as f:
        f.write(script_text)


def launch_blender():
    script_path = get_script_path()
    vars.BLENDER_PROCESS = subprocess.Popen([f"{vars.BLENDER_PATH}", "-P", f"{script_path}"])
