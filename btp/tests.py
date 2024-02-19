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
from RLPy import *
from . import cc, utils


def list_objects():
    selected = RScene.GetSelectedObjects()
    for sel in selected:
        print("######")
        print(sel.GetName())
        print("------")
    #    p = cc.find_parent_avatar_or_prop(sel)
    #    print(p.GetName())
        children = RScene.FindChildObjects(sel, EObjectType_Avatar | EObjectType_Prop | EObjectType_Camera | EObjectType_Light)
        for child in children:
            print(f"{child.GetName()} ({type(child)})")


def show_id():
    actor_objects = cc.get_selected_actor_objects()
    for obj in actor_objects:
        print(f"{obj.GetName()}: {obj.GetID()}")


def test_data_block_set():
    data_block = RDataBlock.Create([])
    attr = RAttribute("TestAttr", EAttributeType_String, EAttributeFlag_Default)
    data_block = RDataBlock.Create([attr])
    time_zero = RTime.FromValue(0)
    value = RVariant("TestString")
    data_block.SetData("TestAttr", value)
    #data_block.SetData("Something", time_zero, value)
    actor_objects = cc.get_selected_actor_objects()
    for obj in actor_objects:
        obj.SetDataBlock("TestBlock", data_block)


def test_data_block_get():
    actor_objects = cc.get_selected_actor_objects()
    for obj in actor_objects:
        data_block: RDataBlock = obj.GetDataBlock("TestBlock")
        value: RVariant = data_block.GetData("TestAttr")
        print(value.ToString())


def test_data_block_bad_get():
    print("Bad Get")
    actor_objects = cc.get_selected_actor_objects()
    for obj in actor_objects:
        data_block: RDataBlock = obj.GetDataBlock("TestBlock")
        print(data_block)
        if data_block:
            value: RVariant = data_block.GetData("TestAttrNotExists")
            print(value)
            print(value.ToString())



def test():
    avatar = cc.get_first_avatar()
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones: list = SC.GetSkinBones()
    root_bone: RIObject = SC.GetRootBone()
    bone_data = {}
    pairs: RINodeTransformPairs = SC.ConvertToOriginalBoneAxis()
    for pair in pairs:
        node = pair[0]
        T = pair[1]
        r = T.R()
        print(f"{node.GetName()} : {r.x},{r.y},{r.z},{r.w}")


# Compares the bone transforms (local and world) with the animation clip transform control transforms
# animation clip transforms are relative to the T-pose
def compare_clip_with_bones():
    avatar = cc.get_first_avatar()
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    skin_bones: list = SC.GetSkinBones()
    root_bone = SC.GetRootBone()
    time = RGlobal.GetTime()
    clip = avatar.GetSkeletonComponent().GetClipByTime(time)
    for bone in skin_bones:
        bone_name = bone.GetName()
        print(f"Bone: {bone_name}")
        TW: RTransform = bone.WorldTransform()
        tw: RVector3 = TW.T()
        rw: RQuaternion = TW.R()
        sw: RVector3 = TW.S()
        TL: RTransform = bone.LocalTransform()
        tl: RVector3 = TL.T()
        rl: RQuaternion = TL.R()
        sl: RVector3 = TL.S()
        print(f"Local - T: ({f2(tl.x)}, {f2(tl.y)}, {f2(tl.z)}) R: ({f2(rl.x)}, {f2(rl.y)}, {f2(rl.z)}, {f2(rl.w)}) S: ({f2(sl.x)}, {f2(sl.y)}, {f2(sl.z)})")
        print(f"World - T: ({f2(tw.x)}, {f2(tw.y)}, {f2(tw.z)}) R: ({f2(rw.x)}, {f2(rw.y)}, {f2(rw.z)}, {f2(rw.w)}) S: ({f2(sw.x)}, {f2(sw.y)}, {f2(sw.z)})")
        transform_control: RTransformControl = clip.GetControl("Transform", bone)
        if transform_control:
            T = RTransform()
            transform_control.GetValue(time, T)
            t: RVector3 = T.T()
            r: RQuaternion = T.R()
            s: RVector3 = T.S()
            print(f"Control - T: ({f2(t.x)}, {f2(t.y)}, {f2(t.z)}) R: ({f2(r.x)}, {f2(r.y)}, {f2(r.z)}, {f2(r.w)}) S: ({f2(s.x)}, {f2(s.y)}, {f2(s.z)})")


# Calculate the world transform hierarchy of an avatar by following the local
# transforms from the root bone.
# Knowing the forward calculation means it can be reversed to get local transforms from
# bones in world space (i.e. from Blender)

def calculate_avatar_world_hierarchy():
    avatar = cc.get_first_avatar()
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    root_bone = SC.GetRootBone()
    root_rot = RQuaternion(RVector4(0,0,0,1))
    root_tra = RVector3(RVector3(0,0,0))
    root_sca = RVector3(RVector3(1,1,1))
    calc_world_transform(root_bone, root_rot, root_tra, root_sca)

def calc_world_transform(bone, parent_world_rot, parent_world_tra, parent_world_sca):
    bone_name = bone.GetName()
    print(bone_name)
    T: RTransform = bone.LocalTransform()
    local_rot: RQuaternion = T.R()
    local_tra: RVector3 = T.T()
    local_sca: RVector3 = T.S()
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
    T: RTransform = bone.LocalTransform()
    t: RVector3 = T.T()
    r: RQuaternion = T.R()
    s: RVector3 = T.S()
    print(f"Local - T: ({f2(t.x)}, {f2(t.y)}, {f2(t.z)}) R: ({f2(r.x)}, {f2(r.y)}, {f2(r.z)}, {f2(r.w)}) S: ({f2(s.x)}, {f2(s.y)}, {f2(s.z)})")

def show_world(bone):
    T: RTransform = bone.WorldTransform()
    t: RVector3 = T.T()
    r: RQuaternion = T.R()
    s: RVector3 = T.S()
    print(f"World - T: ({f2(t.x)}, {f2(t.y)}, {f2(t.z)}) R: ({f2(r.x)}, {f2(r.y)}, {f2(r.z)}, {f2(r.w)}) S: ({f2(s.x)}, {f2(s.y)}, {f2(s.z)})")

def calc_world(local_rot: RQuaternion, local_tra: RVector3, local_sca: RVector3,
              parent_world_rot: RQuaternion, parent_world_tra: RVector3, parent_world_sca: RVector3):
    world_rot = parent_world_rot.Multiply(local_rot)
    world_tra = parent_world_rot.MultiplyVector(local_tra * parent_world_sca) + parent_world_tra
    world_sca = local_sca
    # Calculated transform should exactly match the world transform
    print(f"Calculated - T: ({f2(world_tra.x)}, {f2(world_tra.y)}, {f2(world_tra.z)}) R: ({f2(world_rot.x)}, {f2(world_rot.y)}, {f2(world_rot.z)}, {f2(world_rot.w)}) S: ({f2(world_sca.x)}, {f2(world_sca.y)}, {f2(world_sca.z)})")
    return world_rot, world_tra, world_sca


def show_foot_effector_transforms():
    avatar = cc.get_first_avatar()
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    time = RGlobal.GetTime()
    clip: RIClip = SC.GetClipByTime(time)
    print("Left Foot:")
    show_effector(SC, clip, EHikEffector_LeftFoot, time)
    print("Right Foot:")
    show_effector(SC, clip, EHikEffector_RightFoot, time)


def show_effector(SC: RISkeletonComponent, clip: RIClip, effector_type, time):
    ik_effector = SC.GetEffector(effector_type)
    if ik_effector:
        clip_data_block: RDataBlock = clip.GetDataBlock("Layer", ik_effector)
        #attribs = clip_data_block.GetAttributes()
        #a: RAttribute
        #for a in attribs:
            #print(a.GetName())
            #control = clip_data_block.GetControl(a.GetName())
            #print(control)
        if clip_data_block:
            show_control_data(SC, clip_data_block, time)


def show_control_data(SC: RISkeletonComponent, data_block: RDataBlock, time: RTime):
    rx = ry = rz = 0
    tx = ty = tz = 0
    ta = ra = 0

    v = data_block.GetControl("TranslateActive").GetValue(time, ta)
    print(v)
    data_block.GetControl("RotateActive").GetValue(time, ra)
    data_block.GetControl("Rotation/RotationX").GetValue(time, rx)
    data_block.GetControl("Rotation/RotationY").GetValue(time, ry)
    data_block.GetControl("Rotation/RotationZ").GetValue(time, rz)
    if data_block.GetControl("Position/PositionX") is not None:
        data_block.GetControl("Position/PositionX").GetValue(time, tx)
        data_block.GetControl("Position/PositionY").GetValue(time, ty)
        data_block.GetControl("Position/PositionZ").GetValue(time, tz)
        print(f" - {ta}/{ra} - ({utils.fd2(tx)}, {utils.fd2(ty)}, {utils.fd2(tz)}) - ({utils.fd2(rx)}, {utils.fd2(ry)}, {utils.fd2(rz)})")
    else:
        print(f" - {ta}/{ra} - ({utils.fd2(rx)}, {utils.fd2(ry)}, {utils.fd2(rz)})")




def test2():
    avatar = cc.get_first_avatar()
    fps: RFps = RGlobal.GetFps()
    SC: RISkeletonComponent = avatar.GetSkeletonComponent()
    current_time = RGlobal.GetTime()
    existing_clip: RIClip = SC.GetClipByTime(current_time)
    if existing_clip:
        SC.BreakClip(current_time)
        next_frame_time = fps.GetNextFrameTime(current_time)
        SC.BreakClip(next_frame_time)
    clip: RIClip = SC.AddClip(current_time)
    avatar.Update()


def test_face():
    avatar = cc.get_first_avatar()
    FC: RIFacialProfileComponent = avatar.GetFacialProfileComponent()
    path = "F:\\Testing\\T1.ccFacialProfile"
    print(path)
    FC.LoadProfile(path)
    # broken for non-standard humanoids
    return
