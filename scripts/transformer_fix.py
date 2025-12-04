import bpy
import bmesh
import os

FBX_PATH = r"$1"
EXPORT_PATH = r"$2"
NOTIFY_PATH = r"$3"

MAPPINGS = {
    "l_bigtoe2": "l_toes",
    "l_indextoe2": "l_toes",
    "l_midtoe2": "l_toes",
    "l_ringtoe2": "l_toes",
    "l_pinkytoe2": "l_toes",
    "l_bigtoe1": "l_toes",
    "l_indextoe1": "l_toes",
    "l_midtoe1": "l_toes",
    "l_ringtoe1": "l_toes",
    "l_pinkytoe1": "l_toes",
    "r_bigtoe2": "r_toes",
    "r_indextoe2": "r_toes",
    "r_midtoe2": "r_toes",
    "r_ringtoe2": "r_toes",
    "r_pinkytoe2": "r_toes",
    "r_bigtoe1": "r_toes",
    "r_indextoe1": "r_toes",
    "r_midtoe1": "r_toes",
    "r_ringtoe1": "r_toes",
    "r_pinkytoe1": "r_toes",
}

def remap_vertex_groups(obj):
    vg_mappings = {}
    for vg in obj.vertex_groups:
        if vg.name in MAPPINGS:
            map_to = MAPPINGS[vg.name]
            if map_to in obj.vertex_groups:
                vg_to = obj.vertex_groups[map_to]
                to_index = vg_to.index
                vg_mappings[vg.index] = to_index

    if not vg_mappings:
        return False

    bm = get_bmesh(obj)

    dl = bm.verts.layers.deform.active
    for vert in bm.verts:
        for i, j in vg_mappings.items():
            try:
                vert[dl][j] = min(1.0, vert[dl][j] + vert[dl][i])
            except:
                if i in vert[dl]:
                    vert[dl][j] = vert[dl][i]

    bm.to_mesh(obj.data)

    to_remove = []
    for vg in obj.vertex_groups:
        if vg.name in MAPPINGS:
            to_remove.append(vg)
    for vg in to_remove:
        obj.vertex_groups.remove(vg)

    return True

def get_bmesh(obj):
    mesh = obj.data
    if type(mesh) is bpy.types.Object:
        mesh = mesh.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bm.faces.ensure_lookup_table()
    bm.edges.ensure_lookup_table()
    bm.verts.ensure_lookup_table()
    bm.verts.layers.deform.verify()
    return bm

def fix_groups():
    result = False
    for obj in bpy.data.objects:
        if obj.type == "MESH":
            if not obj.name.startswith("Genesis"):
                result = result or remap_vertex_groups(obj)
    return result

def notify(code, msg=None):
    with open(NOTIFY_PATH, 'w') as f:
        if msg:
            f.write(f"{code}:{msg}")
        else:
            f.write(code)

try:
    bpy.ops.wm.fbx_import(filepath=FBX_PATH)
    if fix_groups():
        bpy.ops.export_scene.fbx(filepath=EXPORT_PATH)
        file = os.path.split(EXPORT_PATH)[1]
        notify("FIXED", file)
    else:
        notify("OK")
except:
    notify("ERROR")