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

VERSION = "2.2.5"
DEV = False
#DEV = True
AVATAR_TYPES = {
    EAvatarType__None: "None",
    EAvatarType_Standard: "Standard",
    EAvatarType_NonHuman: "NonHuman",
    EAvatarType_NonStandard: "NonStandard",
    EAvatarType_StandardSeries: "StandardSeries",
    EAvatarType_LightAvatarStandard: "LightAvatarStandard",
    # composite flags
    EAvatarType_All: "All",
    EAvatarType_AllEditable: "AllEditAble",
    EAvatarType_AllNonEditable: "AllNonEditable",
    EAvatarType_AllWithLight: "AllWithLight",
    EAvatarType_LightAvatar: "LightAvatar",
    EAvatarType_LightAvatarNonHuman: "LightAvatarNonHuman",
    EAvatarType_LightAvatarNonStandard: "LightAvatarNonStandard",
    EAvatarType_LightAvatarStandardSeries: "LightAvatarStandardSeries",
}

AVATAR_GENERATIONS = {
    EAvatarGeneration__None: "",
    EAvatarGeneration_AccuRig: "AccuRig",
    EAvatarGeneration_ActorBuild: "ActorBuild",
    EAvatarGeneration_ActorScan: "ActorScan",
    EAvatarGeneration_CC_G1_Avatar: "G1",
    EAvatarGeneration_CC_G3_Avatar: "G3",
    EAvatarGeneration_CC_G3_Plus_Avatar: "RL_CC3_Plus",
    EAvatarGeneration_CC_Game_Base_One: "RL_CharacterCreator_Base_Game_G1_One_UV",
    EAvatarGeneration_CC_Game_Base_Multi: "RL_CharacterCreator_Base_Game_G1_Multi_UV",
}

CHARACTER_TYPES = {
    "STANDARD": {
        "generations": [ "G3",
                         "RL_CC3_Plus", ],

        "avatar_types": [ "Standard",
                          "StandardSeries",
                          "LightAvatarStandard",
                          "LightAvatarStandardSeries", ],
    },

    "HUMANOID": {
        "generations": [ "AccuRig",
                         "ActorBuild",
                         "ActorScan",
                         "G1",
                         "RL_CharacterCreator_Base_Game_G1_One_UV",
                         "RL_CharacterCreator_Base_Game_G1_Multi_UV",
                         "Humanoid", "Rigify", "Rigify+", "GameBase", ],

        "avatar_types": [ "NonStandard",
                          "LightAvatarNonStandard", ],
    },

    "CREATURE": {
        "generations": [ "Creature", ],
        "avatar_types": [ "NonHuman", "LightAvatarNonHuman", ],
    },

    "PROP": {
        "generations": [ "Prop", ],
        "avatar_types": [],
    },
}

FACIAL_PROFILES = {
    EFacialProfile__None: "None",
    EFacialProfile_CC4Extended: "CC4Extended",
    EFacialProfile_CC4Standard: "CC4Standard",
    EFacialProfile_Traditional: "Traditional",
}