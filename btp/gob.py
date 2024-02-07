
import subprocess
import os
import RLPy
from . import link, cc, exporter, prefs, utils, vars

GOB_AVATAR = None
GOB_FBX_PATH = None
GOB_CONNECTED = False
GOB_DONE = False

BLENDER_PROCESS = None


def go_b():
    global GOB_AVATAR, GOB_FBX_PATH, GOB_CONNECTED, GOB_DONE
    GOB_FBX_PATH = None
    GOB_AVATAR = None
    GOB_CONNECTED = False
    GOB_DONE = False

    export_path = prefs.DATALINK_FOLDER
    avatar = cc.get_first_avatar()
    if avatar:

        RLPy.RScene.SelectObject(avatar)
        name = avatar.GetName()

        LINK = link.get_data_link()
        LINK.link_start()
        LINK.service.connected.connect(go_b_connected)

        sub_folder, script_path, blend_path = get_go_b_paths(name)
        write_script(script_path, blend_path)
        launch_blender(script_path)

        # export the avatar while blender launches
        fbx_path = os.path.join(sub_folder, name + ".fbx")
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
    # if blender has connected back and the fbx has finished exporting:
    if GOB_FBX_PATH and GOB_CONNECTED and not GOB_DONE:
        GOB_DONE = True
        LINK = link.get_data_link()
        LINK.service.connected.disconnect(go_b_connected)
        LINK.send_actor_exported(GOB_AVATAR, GOB_FBX_PATH)
        LINK.send_pose()
        LINK.sync_lights()
        LINK.sync_camera()
        GOB_AVATAR = None
        GOB_FBX_PATH = None
        GOB_CONNECTED = False
        GOB_DONE = False


def start_datalink():
    LINK = link.get_data_link()
    LINK.link_start()


def get_go_b_paths(name):
    folder = prefs.DATALINK_FOLDER

    if not os.path.exists(folder):
        folder = cc.temp_files_path("Data Link")
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)

    base_name = name
    sub_folder = os.path.normpath(os.path.join(folder, name))
    if os.path.exists(sub_folder):
        suffix = 1
        name = base_name + "_" + str(suffix)
        sub_folder = os.path.normpath(os.path.join(folder, name))
        while os.path.exists(sub_folder):
            suffix += 1
            name = base_name + "_" + str(suffix)
            sub_folder = os.path.normpath(os.path.join(folder, name))

    if not os.path.exists(sub_folder):
        os.makedirs(sub_folder, exist_ok=True)

    blend_path = os.path.normpath(os.path.join(sub_folder, base_name + ".blend"))

    script_path = os.path.normpath(os.path.join(sub_folder, "go_b.py"))

    utils.log_info(f"Using DataLink Sub-Folder Path: {sub_folder}")

    return sub_folder, script_path, blend_path


def write_script(script_path, blend_path):
    script_text = f"""
import bpy

bpy.ops.wm.save_as_mainfile(filepath=r"{blend_path}")
bpy.ops.file.make_paths_relative()
bpy.ops.ccic.datalink(param="START")
    """
    utils.log_info(f"Writing Blender Launch Script: {script_path}")
    with open(script_path, 'w') as f:
        f.write(script_text)


def launch_blender(script_path):
    global BLENDER_PROCESS
    utils.log_info(f"Launching Blender...")
    BLENDER_PROCESS = subprocess.Popen([f"{prefs.BLENDER_PATH}", "-P", f"{script_path}"])
