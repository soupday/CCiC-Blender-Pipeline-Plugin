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
import importer, exporter, link, qt, cc

def test():
    avatar = cc.get_first_avatar()
    SC: RLPy.RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones: list = SC.GetSkinBones()
    root_bone: RLPy.RIObject = SC.GetRootBone()
    bone_data = {}
    pairs: RLPy.RINodeTransformPairs = SC.ConvertToOriginalBoneAxis()
    for pair in pairs:
        node = pair[0]
        T = pair[1]
        r = T.R()
        print(f"{node.GetName()} : {r.x},{r.y},{r.z},{r.w}")


# Compares the bone transforms (local and world) with the animation clip transform control transforms
# animation clip transforms are relative to the T-pose
def compare_clip_with_bones():
    avatar = cc.get_first_avatar()
    SC: RLPy.RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones: list = SC.GetSkinBones()
    root_bone = SC.GetRootBone()
    time = RLPy.RGlobal.GetTime()
    clip = avatar.GetSkeletonComponent().GetClipByTime(time)
    for bone in skin_bones:
        bone_name = bone.GetName()
        print(f"Bone: {bone_name}")
        TW: RLPy.RTransform = bone.WorldTransform()
        tw: RLPy.RVector3 = TW.T()
        rw: RLPy.RQuaternion = TW.R()
        sw: RLPy.RVector3 = TW.S()
        TL: RLPy.RTransform = bone.LocalTransform()
        tl: RLPy.RVector3 = TL.T()
        rl: RLPy.RQuaternion = TL.R()
        sl: RLPy.RVector3 = TL.S()
        print(f"Local - T: ({f2(tl.x)}, {f2(tl.y)}, {f2(tl.z)}) R: ({f2(rl.x)}, {f2(rl.y)}, {f2(rl.z)}, {f2(rl.w)}) S: ({f2(sl.x)}, {f2(sl.y)}, {f2(sl.z)})")
        print(f"World - T: ({f2(tw.x)}, {f2(tw.y)}, {f2(tw.z)}) R: ({f2(rw.x)}, {f2(rw.y)}, {f2(rw.z)}, {f2(rw.w)}) S: ({f2(sw.x)}, {f2(sw.y)}, {f2(sw.z)})")
        transform_control: RLPy.RTransformControl = clip.GetControl("Transform", bone)
        if transform_control:
            T = RLPy.RTransform()
            transform_control.GetValue(time, T)
            t: RLPy.RVector3 = T.T()
            r: RLPy.RQuaternion = T.R()
            s: RLPy.RVector3 = T.S()
            print(f"Control - T: ({f2(t.x)}, {f2(t.y)}, {f2(t.z)}) R: ({f2(r.x)}, {f2(r.y)}, {f2(r.z)}, {f2(r.w)}) S: ({f2(s.x)}, {f2(s.y)}, {f2(s.z)})")


# Calculate the world transform hierarchy of an avatar by following the local
# transforms from the root bone.
# Knowing the forward calculation means it can be reversed to get local transforms from
# bones in world space (i.e. from Blender)

def calculate_avatar_world_hierarchy():
    avatar = cc.get_first_avatar()
    SC: RLPy.RISkeletonComponent = avatar.GetSkeletonComponent()
    root_bone = SC.GetRootBone()
    root_rot = RLPy.RQuaternion(RLPy.RVector4(0,0,0,1))
    root_tra = RLPy.RVector3(RLPy.RVector3(0,0,0))
    root_sca = RLPy.RVector3(RLPy.RVector3(1,1,1))
    calc_world_transform(root_bone, root_rot, root_tra, root_sca)

def calc_world_transform(bone, parent_world_rot, parent_world_tra, parent_world_sca):
    bone_name = bone.GetName()
    print(bone_name)
    T: RLPy.RTransform = bone.LocalTransform()
    local_rot: RLPy.RQuaternion = T.R()
    local_tra: RLPy.RVector3 = T.T()
    local_sca: RLPy.RVector3 = T.S()
    show_local(bone)
    show_world(bone)
    world_rot, world_tra, world_sca = calc_world(local_rot, local_tra, local_sca,
                                                 parent_world_rot, parent_world_tra, parent_world_sca)
    children = bone.GetChildren()
    for child in children:
        calc_world_transform(child, world_rot, world_tra, world_sca)

def f2(v):
    return '{0:.2f}'.format(v)

def show_local(bone):
    T: RLPy.RTransform = bone.LocalTransform()
    t: RLPy.RVector3 = T.T()
    r: RLPy.RQuaternion = T.R()
    s: RLPy.RVector3 = T.S()
    print(f"Local - T: ({f2(t.x)}, {f2(t.y)}, {f2(t.z)}) R: ({f2(r.x)}, {f2(r.y)}, {f2(r.z)}, {f2(r.w)}) S: ({f2(s.x)}, {f2(s.y)}, {f2(s.z)})")

def show_world(bone):
    T: RLPy.RTransform = bone.WorldTransform()
    t: RLPy.RVector3 = T.T()
    r: RLPy.RQuaternion = T.R()
    s: RLPy.RVector3 = T.S()
    print(f"World - T: ({f2(t.x)}, {f2(t.y)}, {f2(t.z)}) R: ({f2(r.x)}, {f2(r.y)}, {f2(r.z)}, {f2(r.w)}) S: ({f2(s.x)}, {f2(s.y)}, {f2(s.z)})")

def calc_world(local_rot: RLPy.RQuaternion, local_tra: RLPy.RVector3, local_sca: RLPy.RVector3,
              parent_world_rot: RLPy.RQuaternion, parent_world_tra: RLPy.RVector3, parent_world_sca: RLPy.RVector3):
    world_rot = parent_world_rot.Multiply(local_rot)
    world_tra = parent_world_rot.MultiplyVector(local_tra * parent_world_sca) + parent_world_tra
    world_sca = local_sca
    # Calculated transform should exactly match the world transform
    print(f"Calculated - T: ({f2(world_tra.x)}, {f2(world_tra.y)}, {f2(world_tra.z)}) R: ({f2(world_rot.x)}, {f2(world_rot.y)}, {f2(world_rot.z)}, {f2(world_rot.w)}) S: ({f2(world_sca.x)}, {f2(world_sca.y)}, {f2(world_sca.z)})")
    return world_rot, world_tra, world_sca