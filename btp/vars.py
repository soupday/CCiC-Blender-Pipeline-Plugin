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

from RLPy import *

VERSION = "2.0.0"

AVATAR_TYPES = {
    EAvatarType__None: "None",
    EAvatarType_Standard: "Standard",
    EAvatarType_NonHuman: "NonHuman",
    EAvatarType_NonStandard: "NonStandard",
    EAvatarType_StandardSeries: "StandardSeries",
    EAvatarType_All: "All",
}

FACIAL_PROFILES = {
    EFacialProfile__None: "None",
    EFacialProfile_CC4Extended: "CC4Extended",
    EFacialProfile_CC4Standard: "CC4Standard",
    EFacialProfile_Traditional: "Traditional",
}