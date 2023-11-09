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


def get_pose_data(avatar: RLPy.RIAvatar):
    SC: RLPy.RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones: list = SC.GetSkinBones()
    bone_data = {}

    bone: RLPy.RIObject
    T: RLPy.RTransform
    for bone in skin_bones:
        name = bone.GetName()
        T = bone.LocalTransform()
        t: RLPy.RVector3 = T.T()
        r: RLPy.RVector4 = T.R()
        s: RLPy.RVector3 = T.S()

        bone_data[name] = {
            "loc": [t.x, t.y, t.z],
            "rot": [r.x, r.y, r.z, r.w],
            "sca": [s.x, s.y, s.z],
        }

    return bone_data