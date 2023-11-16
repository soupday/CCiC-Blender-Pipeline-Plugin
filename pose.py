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


def blender_matrix4():
    M4 = RLPy.RMatrix4( 1,  0,  0,  1,
                        0, -1,  0,  1,
                        0,  0,  1,  1,
                        0,  0,  0,  1)
    return M4


def blender_matrix3():
    M3 = RLPy.RMatrix3( 1,  0,  0,
                        0, -1,  0,
                        0,  0,  1)
    return M3


def get_skeleton(avatar: RLPy.RIAvatar):
    SC: RLPy.RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones: list = SC.GetSkinBones()
    bone: RLPy.RINode
    skeleton = []
    for bone in skin_bones:
        name = bone.GetName()
        if name not in skeleton:
            skeleton.append(name)
    return skeleton


def get_world_pose(avatar: RLPy.RIAvatar):
    SC: RLPy.RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones: list = SC.GetSkinBones()
    bone: RLPy.RIObject
    pose_data = {}
    T: RLPy.RTransform
    for bone in skin_bones:
        name = bone.GetName()
        T = bone.WorldTransform()
        t: RLPy.RVector3 = T.T()
        r: RLPy.RQuaternion = T.R()
        s: RLPy.RVector3 = T.S()

        pose_data[name] = {
            "loc": [t.x, t.y, t.z],
            "rot": [r.x, r.y, r.z, r.w],
            "sca": [s.x, s.y, s.z],
        }

    return pose_data


def get_local_pose(avatar: RLPy.RIAvatar):
    SC: RLPy.RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones: list = SC.GetSkinBones()
    bone: RLPy.RIObject
    pose_data = {}
    T: RLPy.RTransform
    for bone in skin_bones:
        name = bone.GetName()
        T = bone.LocalTransform()
        t: RLPy.RVector3 = T.T()
        r: RLPy.RQuaternion = T.R()
        s: RLPy.RVector3 = T.S()

        pose_data[name] = {
            "loc": [t.x, t.y, t.z],
            "rot": [r.x, r.y, r.z, r.w],
            "sca": [s.x, s.y, s.z],
        }

    return pose_data


def get_original_axis_pose(avatar: RLPy.RIAvatar):
    SC: RLPy.RISkeletonComponent = avatar.GetSkeletonComponent()
    pose_data = {}
    T: RLPy.RTransform
    pairs: RLPy.RINodeTransformPairs = SC.ConvertToOriginalBoneAxis()
    for pair in pairs:
        node = pair[0]
        name = node.GetName()
        T = pair[1]
        t: RLPy.RVector3 = T.T()
        r: RLPy.RQuaternion = T.R()
        s: RLPy.RVector3 = T.S()
        pose_data[name] = {
            "loc": [t.x, t.y, t.z],
            "rot": [r.x, r.y, r.z, r.w],
            "sca": [s.x, s.y, s.z],
        }

    return pose_data


def get_pose_data(avatar: RLPy.RIAvatar):
    bone_data = {}
    skeleton = get_skeleton(avatar)
    pose = get_world_pose(avatar)
    bone_data["skeleton"] = skeleton
    bone_data["pose"] = pose
    return bone_data

