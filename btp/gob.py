
import subprocess
import os
import RLPy
from . import link, cc, exporter, prefs, utils, vars

GOB_QUEUE = None
GOB_CONNECTED = False
GOB_DONE = False

BLENDER_PROCESS = None

def go_b():
    global GOB_CONNECTED, GOB_DONE, GOB_QUEUE
    GOB_QUEUE = []
    GOB_CONNECTED = False
    GOB_DONE = False

    #cc.deduplicate_scene()

    objects = cc.get_selected_actor_objects()

    if cc.is_cc():
        name = "Untitled"
        # in CC4, if nothing selected, use the available character, if there is one
        if not objects:
            avatar = cc.get_first_avatar()
            RLPy.RScene.SelectObject(avatar)
            if avatar:
                objects = [avatar]
    else:
        name = "iClone Project"

    GOB_OBJECTS = []
    for obj in objects:
        GOB_OBJECTS.append({
            "name": obj.GetName(),
            "object": obj,
        })

    # prefer using avatar names over prop names
    avatars = cc.get_selected_avatars()
    if cc.is_cc():
        if avatars:
            name = f"CC4 - {avatars[0].GetName()}"
        elif objects:
            name = f"CC4 - {objects[0].GetName()}"
    else:
        if avatars:
            name = f"iClone - {avatars[0].GetName()}"
        elif objects:
            name = f"iClone - {objects[0].GetName()}"

    utils.log_info(f"Using project name: {name}")

    LINK = link.get_data_link()
    if not LINK.is_connected():
        LINK.link_start()
        LINK.service.connected.connect(go_b_connected)
        LINK.show()

    project_folder, script_path, blend_path, import_folder, export_folder = get_go_b_paths(name)
    write_script(script_path, blend_path)
    launch_blender(script_path)

    # TODO only export character if doesn't exist in Blender...

    # export the avatar(s) while Blender launches
    for gob_data in GOB_OBJECTS:
        name = gob_data["name"]
        obj = gob_data["object"]
        object_folder = utils.get_unique_folder_path(import_folder, name, create=True)
        fbx_path = os.path.join(object_folder, name + ".fbx")
        gob_data["path"] = fbx_path
        export = exporter.Exporter(obj, no_window=True)
        export.set_datalink_export()
        export.do_export(file_path=fbx_path)
        GOB_QUEUE.append(gob_data)
        go_b_send()

    GOB_DONE = True
    go_b_send()


def go_b_connected():
    global GOB_CONNECTED
    GOB_CONNECTED = True
    LINK = link.get_data_link()
    LINK.service.connected.disconnect(go_b_connected)
    # send the lights and camera
    LINK.sync_lights()
    LINK.send_camera_sync()
    # then send the characters
    go_b_send()


def go_b_send():
    global GOB_CONNECTED, GOB_DONE, GOB_QUEUE
    if GOB_CONNECTED:
        if GOB_QUEUE:
            LINK = link.get_data_link()
            while GOB_QUEUE:
                gob_data = GOB_QUEUE.pop(0)
                LINK.send_actor_exported(gob_data["object"], gob_data["path"])
        if GOB_DONE:
            go_b_finish()


def go_b_finish():
    global GOB_CONNECTED, GOB_DONE, GOB_QUEUE
    GOB_CONNECTED = False
    GOB_DONE = False
    GOB_QUEUE = None
    LINK = link.get_data_link()
    # finally pose the characters ()
    LINK.send_frame_sync()
    LINK.send_save()



def go_morph():
    global GOB_OBJECTS, GOB_CONNECTED, GOB_DONE, GOB_EXPORTED
    GOB_OBJECTS = []
    GOB_CONNECTED = False
    GOB_DONE = False
    GOB_EXPORTED = False

    avatar = cc.get_first_avatar()
    if not avatar:
        return

    GOB_OBJECTS.append({
        "name": avatar.GetName(),
        "object": avatar,
    })

    name = f"Morph Edit - {avatar.GetName()}"
    utils.log_info(f"Using project name: {name}")

    LINK = link.get_data_link()
    if not LINK.is_connected():
        LINK.link_start()
        LINK.service.connected.connect(go_morph_connected)

    project_folder, script_path, blend_path, import_folder, export_folder = get_go_b_paths(name)
    write_script(script_path, blend_path)
    launch_blender(script_path)

    # export the avatar nude obj in bind pose while Blender launches
    for gob_data in GOB_OBJECTS:
        name = gob_data["name"]
        obj = gob_data["object"]
        object_folder = utils.get_unique_folder_path(import_folder, name, create=True)
        obj_path = os.path.join(object_folder, name + ".obj")
        gob_data["path"] = obj_path
        obj_options = (RLPy.EExport3DFileOption_ResetToBindPose |
                       RLPy.EExport3DFileOption_FullBodyPart |
                       RLPy.EExport3DFileOption_AxisYUp |
                       RLPy.EExport3DFileOption_GenerateDrmProtectedFile |
                       RLPy.EExport3DFileOption_TextureMapsAreShaderGenerated |
                       RLPy.EExport3DFileOption_GenerateMeshGroupIni |
                       RLPy.EExport3DFileOption_ExportExtraMaterial)
        if prefs.EXPORT_MORPH_MATERIALS:
            obj_options |= RLPy.EExport3DFileOption_ExportMaterial
        RLPy.RFileIO.ExportObjFile(avatar, obj_path, obj_options)

    GOB_EXPORTED = True

    # try to finish after exporting the avatar(s)
    go_morph_finish()


def go_morph_connected():
    global GOB_CONNECTED
    GOB_CONNECTED = True
    # try to finish after connecting
    go_morph_finish()


def go_morph_finish():
    global GOB_CONNECTED, GOB_DONE, GOB_EXPORTED, GOB_OBJECTS
    # if Blender has connected back and the avatar(s) have finished exporting:
    if GOB_CONNECTED and GOB_EXPORTED and not GOB_DONE:
        GOB_DONE = True
        LINK = link.get_data_link()
        LINK.service.connected.disconnect(go_morph_connected)
        if prefs.EXPORT_MORPH_MATERIALS:
            LINK.sync_lights()
        LINK.send_camera_sync()
        for gob_data in GOB_OBJECTS:
            LINK.send_morph_exported(gob_data["object"], gob_data["path"])
        LINK.send_save()
        GOB_EXPORTED = False
        GOB_CONNECTED = False
        GOB_OBJECTS = None


def start_datalink():
    LINK = link.get_data_link()
    LINK.link_start()


def get_go_b_paths(name):
    datalink_folder = prefs.DATALINK_FOLDER

    if not os.path.exists(datalink_folder):
        datalink_folder = cc.temp_files_path("Data Link")
        if not os.path.exists(datalink_folder):
            os.makedirs(datalink_folder, exist_ok=True)

    project_folder = utils.get_unique_folder_path(datalink_folder, name, create=True)
    blend_path = os.path.normpath(os.path.join(project_folder, name + ".blend"))
    import_folder = utils.make_sub_folder(project_folder, "imports")
    export_folder = utils.make_sub_folder(project_folder, "exports")
    script_path = os.path.normpath(os.path.join(project_folder, "go_b.py"))
    utils.log_info(f"Using DataLink Project Path: {project_folder}")

    return project_folder, script_path, blend_path, import_folder, export_folder


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
    utils.log_info(f"Launching Blender ...")
    BLENDER_PROCESS = subprocess.Popen([f"{prefs.BLENDER_PATH}", "-P", f"{script_path}"])
