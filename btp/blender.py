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

import RLPy
from PySide2 import *
from . import cc


def fix_blender_name(name: str, import_mesh):
    """Remove any Blenderized duplicate name suffixes, but *only* if imported from Blender.
       CC3 exports replace and ' ' or '.' with underscores, so the Json data will have no
       blender duplication suffixes.
       This function is used to remove any Blender duplication suffix from the mesh/material
       names, just in case...
    """
    if import_mesh and len(name) > 4:
        if name[-3:].isdigit() and name[-4] == ".":
            name = name[:-4]
    return name


def get_json_mesh_name_map(avatar):
    """When trying to match the original character objects and meshes with an export from Blender:
       (i.e. when importing textures and paramaters over the *original* character mesh.)

       CC3 names each export mesh with the original object name replacing ' '/'.' with underscores.
       So to match the original mesh names with the newly imported json data mesh names, we need to
       re-construct the CC3 exported mesh json names from the original object names.

       This function generates a name mapping dictionary from the original character mesh name to
       the blender exported mesh name, which is used as a fallback name to find the mesh json data
       in get_object_json()
    """
    mapping = {}
    child_objects = RLPy.RScene.FindChildObjects(avatar, RLPy.EObjectType_Avatar)
    for obj in child_objects:
        obj_name = obj.GetName()
        if obj_name not in cc.IGNORE_NODES:
            mesh_names = obj.GetMeshNames()
            for mesh_name in mesh_names:
                mapping[mesh_name] = cc.safe_export_name(obj_name)
    return mapping