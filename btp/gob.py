
import subprocess
import os
import RLPy
from . import utils, cc, options, prefs, exporter, link
from . qt import do_events

GOB_QUEUE = None
GOB_CONNECTED = False
GOB_DONE = False
GOB_LIGHTING = False
GOB_SCENE_SELECTION = None

BLENDER_PROCESS = None

def go_b():
    global GOB_CONNECTED, GOB_DONE, GOB_QUEUE, GOB_LIGHTING, GOB_SCENE_SELECTION
    OPTS = options.get_opts()

    GOB_QUEUE = []
    GOB_CONNECTED = False
    GOB_DONE = False

    GOB_SCENE_SELECTION = cc.store_scene_selection()

    cc.deduplicate_scene_objects()

    objects = cc.get_selected_actor_objects()

    #RLPy.RGlobal.SetTime(RLPy.RGlobal.GetStartTime())

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
    GOB_LIGHTING = True
    GOB_LIGHTS_CAMERAS = []
    GOB_AVATARS = []
    GOB_PROPS = []
    GOB_OTHERS = []
    for obj in objects:
        obj_type = cc.get_object_type(obj)
        if obj_type == "LIGHT":
            GOB_LIGHTING = False
        gob_object = {
            "name": obj.GetName(),
            "object": obj,
            "type": obj_type,
        }
        if obj_type == "LIGHT" or obj_type == "CAMERA":
            GOB_LIGHTS_CAMERAS.append(gob_object)
        elif obj_type == "PROP":
            GOB_PROPS.append(gob_object)
        elif obj_type == "AVATAR":
            GOB_AVATARS.append(gob_object)
        else:
            GOB_OTHERS.append(gob_object)

    GOB_OBJECTS = GOB_LIGHTS_CAMERAS + GOB_PROPS + GOB_AVATARS + GOB_OTHERS

    # prefer using avatar names over prop names
    avatars = cc.get_selected_avatars()
    if cc.is_cc5():
        if avatars:
            name = f"CC5 - {avatars[0].GetName()}"
        elif objects:
            name = f"CC5 - {objects[0].GetName()}"
    elif cc.is_cc4():
        if avatars:
            name = f"CC4 - {avatars[0].GetName()}"
        elif objects:
            name = f"CC4 - {objects[0].GetName()}"
    elif cc.is_iclone8:
        if avatars:
            name = f"iClone8 - {avatars[0].GetName()}"
        elif objects:
            name = f"iClone8 - {objects[0].GetName()}"
    else:
        utils.log_warn(f"Unknown application version")
        if avatars:
            name = f"Project - {avatars[0].GetName()}"
        elif objects:
            name = f"Project - {objects[0].GetName()}"

    utils.log_info(f"Using project name: {name}")

    LINK = link.get_data_link()
    if not LINK.is_connected():
        LINK.link_start()
        LINK.service.connected.connect(go_b_connected)
        LINK.show()

    project_folder, script_path, blend_path, import_folder, export_folder = get_go_b_paths(name)
    write_go_b_script(script_path, blend_path)
    launch_blender(script_path)

    lights_cameras = [ gob_data["object"] for gob_data in GOB_OBJECTS if (gob_data["type"] == "LIGHT" or gob_data["type"] == "CAMERA")]
    if lights_cameras:
        folder_name = "Staging_" + utils.timestampns()
        name = lights_cameras[0].GetName()
        staging_folder = utils.get_unique_folder_path(import_folder, folder_name, create=True)
        fbx_path = os.path.join(staging_folder, name + ".rlx")
        gob_data = {
            "name": folder_name,
            "objects": lights_cameras,
            "type": "STAGING",
            "path": fbx_path,
        }
        export = exporter.Exporter(lights_cameras, no_window=True)
        export.set_datalink_export(fps=OPTS.get_link_RFps())
        export.do_export(file_path=fbx_path, no_base_folder=True)
        GOB_QUEUE.append(gob_data)

    # export the avatar(s) while Blender launches
    for gob_data in GOB_OBJECTS:
        name = gob_data["name"]
        obj = gob_data["object"]
        if gob_data["type"] == "PROP" or gob_data["type"] == "AVATAR":
            object_folder = utils.get_unique_folder_path(import_folder, name, create=True)
            fbx_path = os.path.join(object_folder, name + ".fbx")
            gob_data["path"] = fbx_path
            export = exporter.Exporter(obj, no_window=True)
            prop_fix = gob_data["type"] == "PROP" and link.PROP_FIX
            export.set_datalink_export(no_animation=prop_fix, fps=OPTS.get_link_RFps())
            export.do_export(file_path=fbx_path)
            GOB_QUEUE.append(gob_data)
            go_b_send()

    GOB_DONE = True
    go_b_send()


def go_b_connected():
    global GOB_CONNECTED, GOB_LIGHTING
    GOB_CONNECTED = True
    LINK = link.get_data_link()
    LINK.service.connected.disconnect(go_b_connected)
    # send the lights and camera
    LINK.sync_lighting(go_b=True)
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
                if gob_data["type"] != "STAGING":
                    LINK.send_actor_exported(gob_data["object"], gob_data["path"])
                else:
                    LINK.send_lights_cameras_exported(gob_data["objects"], gob_data["path"])
        if GOB_DONE:
            go_b_finish()


def go_b_finish():
    global GOB_CONNECTED, GOB_DONE, GOB_QUEUE, GOB_LIGHTING, GOB_SCENE_SELECTION
    GOB_CONNECTED = False
    GOB_DONE = False
    GOB_QUEUE = None
    GOB_LIGHTING = False
    LINK = link.get_data_link()
    # finally pose the characters ()
    LINK.send_frame_sync()
    LINK.send_save()
    cc.restore_scene_selection(GOB_SCENE_SELECTION)
    GOB_SCENE_SELECTION = None



def go_morph():
    global GOB_OBJECTS, GOB_CONNECTED, GOB_DONE, GOB_EXPORTED
    OPTS = options.get_opts()

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
    write_go_b_script(script_path, blend_path)
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
        if OPTS.EXPORT_MORPH_MATERIALS:
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
    OPTS = options.get_opts()

    # if Blender has connected back and the avatar(s) have finished exporting:
    if GOB_CONNECTED and GOB_EXPORTED and not GOB_DONE:
        GOB_DONE = True
        LINK = link.get_data_link()
        LINK.service.connected.disconnect(go_morph_connected)
        if OPTS.EXPORT_MORPH_MATERIALS:
            LINK.sync_lighting(go_b=True)
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
    OPTS = options.get_opts()

    # paths have been checked by go_b / go_morph
    datalink_folder = OPTS.DATALINK_FOLDER
    project_folder = utils.get_unique_folder_path(datalink_folder, name, create=True)
    blend_path = os.path.normpath(os.path.join(project_folder, name + ".blend"))
    import_folder = utils.make_sub_folder(project_folder, "imports")
    export_folder = utils.make_sub_folder(project_folder, "exports")
    script_path = os.path.normpath(os.path.join(project_folder, "go_b.py"))
    utils.log_info(f"Using DataLink Project Path: {project_folder}")

    return project_folder, script_path, blend_path, import_folder, export_folder


def get_blender_script(script, *args):
    code_path: str = utils.get_resource_path("scripts", script)
    code = None
    with open(code_path, 'r') as f:
        code = f.read()
        for i, arg in enumerate(args):
            code = code.replace(f"${i+1}", str(arg))
    return code


def write_go_b_script(script_path, blend_path):
    OPTS = options.get_opts()

    code = get_blender_script("go_b.py", blend_path, int(OPTS.get_link_fps()))
    if code:
        utils.log_info(f"Writing Blender Launch Script: {script_path}")
        with open(script_path, 'w') as f:
            f.write(code)
            f.close()


def launch_blender(script_path, background=False):
    global BLENDER_PROCESS
    utils.log_info(f"Launching Blender ...")
    blender_path = prefs.get_blender_path()
    if blender_path and os.path.exists(blender_path):
        if background:
            BLENDER_PROCESS = subprocess.Popen([f"{blender_path}", "-b", "-P", f"{script_path}"])
        else:
            BLENDER_PROCESS = subprocess.Popen([f"{blender_path}", "-P", f"{script_path}"])
        return True
    else:
        return False


def go_b_transformer(fbx_path):
    script_folder = cc.temp_files_path("Blender Scripts", create=True)
    script_path = os.path.join(script_folder, "gob_transformer.py")
    notify_path = os.path.join(script_folder, "gob_transformer_notify.txt")
    if os.path.exists(notify_path):
        os.unlink(notify_path)
    write_transformer_script(script_path, notify_path, fbx_path)
    launch_blender(script_path, background=True)
    wait_for_notify(notify_path)


def wait_for_notify(notify_path):
    while not os.path.exists(notify_path):
        do_events()
    result = "NONE"
    with open(notify_path) as f:
        result = f.read()
        f.close()
    if result == "OK":
        RLPy.RUi.ShowMessageBox("Ok", "No issues found with transformer FBX", RLPy.EMsgButton_Ok)
    elif result == "ERROR":
        RLPy.RUi.ShowMessageBox("Error", "Something went wrong!", RLPy.EMsgButton_Ok)
    elif result[:5] == "FIXED":
        RLPy.RUi.ShowMessageBox("Fixed", f"Transformer FBX fixed!\n\n{result[6:]}", RLPy.EMsgButton_Ok)
    else:
        RLPy.RUi.ShowMessageBox("Nothing", "Nothing happened?", RLPy.EMsgButton_Ok)
    os.unlink(notify_path)


def write_transformer_script(script_path, notify_path, fbx_path):
    dir, file = os.path.split(fbx_path)
    name, ext = os.path.splitext(file)
    export_path = os.path.join(dir, name + "(Fixed)" + ext)
    code = get_blender_script("transformer_fix.py", fbx_path, export_path, notify_path)
    if code:
        utils.log_info(f"Writing Blender Launch Script: {script_path}")
        with open(script_path, 'w') as f:
            f.write(code)
            f.close()

