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