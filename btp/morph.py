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
import PySide2
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtGui import *
from shiboken2 import wrapInstance
import os, socket, select, struct, time, json, random, atexit
from . import blender, importer, exporter, cc, qt, prefs, tests, utils, vars
from enum import IntEnum

CATEGORIES = {
    "Head": ESetCategory_Head,
    "Body": ESetCategory_Body,
    "Eyes": ESetCategory_Eyes,
    "Teeth": ESetCategory_Teeth,
    "Eyelash": ESetCategory_Eyelash,
    "Nail": ESetCategory_Nail,
}

class MorphSlider(QObject):
    window: RIDockWidget = None
    # UI
    label_category: QLabel = None
    textbox_morph_name: QLineEdit = None
    dropdown_category: QComboBox = None
    label_slider_path: QLabel = None
    textbox_slider_path: QLineEdit = None
    spinbox_min: QSpinBox = None
    spinbox_max: QSpinBox = None
    radio_default_morph: QRadioButton = None
    radio_current_morph: QRadioButton = None
    textbox_target_path: QLineEdit = None
    textbox_key_path: QLineEdit = None
    checkbox_adjust_bones: QCheckBox = None
    checkbox_auto_apply: QCheckBox = None
    no_update: bool = False
    #
    morph_name = "Unnamed"
    slider_path = "Custom/Blender"
    category = "Body"
    target_path = None
    key_path = None
    source_base_type = EChooseBase_Current
    auto_apply = True
    adjust_bones = True
    morph_min_value = 0
    morph_max_value = 100


    def __init__(self, target_path, key_path):
        QObject.__init__(self)
        dir, file = os.path.split(target_path)
        name, ext = os.path.splitext(file)
        self.target_path = target_path
        self.key_path = key_path
        self.morph_name = self.check_morph_name(name)
        self.slider_path = prefs.DEFAULT_MORPH_SLIDER_PATH
        self.create_window()
        atexit.register(self.on_close)

    def show(self):
        self.window.Show()

    def is_shown(self):
        return self.window.IsVisible()

    def create_window(self):
        self.window, layout = qt.window("Import Character Morph", width=400, height=540, fixed=True, show_hide=self.on_show_hide)
        self.window.SetFeatures(EDockWidgetFeatures_Closable)

        grid = qt.grid(layout)
        grid.setColumnStretch(1, 2)
        grid.setColumnStretch(2, 2)
        qt.label(grid, "Morph Name", row=0, col=0, style=qt.STYLE_RL_BOLD)
        self.textbox_morph_name = qt.textbox(grid, self.morph_name, row=0, col=1, col_span=2, update=self.update_textbox_morph_name)

        qt.label(grid, "Category", row=1, col=0, style=qt.STYLE_RL_BOLD)
        category_options = []
        for category in CATEGORIES:
            category_options.append(category)
        self.dropdown_category = qt.combobox(grid, self.category, row=1, col=1, col_span=2, update=self.update_dropdown_category,
                                             options=category_options)

        self.label_slider_path = qt.label(grid, "/Actor/Body/", row=2, col=0, style=qt.STYLE_RL_BOLD)
        self.textbox_slider_path = qt.textbox(grid, self.slider_path, row=2, col=1, col_span=2, update=self.update_textbox_slider_path)

        qt.label(grid, "Morph Range", row=3, col=0, style=qt.STYLE_RL_BOLD)
        self.spinbox_min = qt.spinbox(grid, -100, 100, 1, self.morph_min_value, row=3, col=1, update=self.update_spinbox_min)
        self.spinbox_max = qt.spinbox(grid, -100, 100, 1, self.morph_max_value, row=3, col=2, update=self.update_spinbox_max)

        qt.spacing(layout, 5)

        qt.label(layout, "Source Morph", style=qt.STYLE_RL_BOLD)
        self.radio_default_morph = qt.radio_button(layout, "Default Morph", False, update=self.update_radio_source_morph)
        self.radio_current_morph = qt.radio_button(layout, "Current Morph", True, update=self.update_radio_source_morph)

        qt.spacing(layout, 5)

        qt.label(layout, "Target Morph", style=qt.STYLE_RL_BOLD)
        grid = qt.grid(layout)
        grid.setColumnStretch(1, 4)
        qt.label(grid, "OBJ Path", row=0, col=0)
        self.textbox_target_path = qt.textbox(grid, self.target_path, row=0, col=1, update=self.update_textbox_target_path)
        icon = qt.get_icon("OpenFile.png")
        qt.button(grid, "", func=self.button_browse_target_path, row=0, col=2, icon=icon, width=32)
        qt.label(grid, "Key Path", row=1, col=0)
        self.textbox_key_path = qt.textbox(grid, self.key_path, row=1, col=1, update=self.update_textbox_key_path)
        qt.button(grid, "", func=self.button_browse_key_path, row=1, col=2, icon=icon, width=32)

        qt.spacing(layout, 5)

        self.checkbox_adjust_bones = qt.checkbox(layout, "Adjust Bones", self.adjust_bones, update=self.update_checkbox_adjust_bones)
        self.checkbox_auto_apply = qt.checkbox(layout, "Auto Apply", self.auto_apply, update=self.update_checkbox_auto_apply)

        qt.spacing(layout, 5)
        qt.stretch(layout, 1)

        qt.button(layout, "Create Slider", self.create_slider, width=200, height=80, style=qt.STYLE_BUTTON_BOLD)

        self.window.Show()

    def on_show_hide(self, visible):
        return

    def on_close(self):
        self.on_show_hide(False)

    def update_textbox_morph_name(self):
        if self.no_update:
            return
        unique_morph_name = self.check_morph_name(self.textbox_morph_name.text())
        self.morph_name = unique_morph_name
        if self.textbox_morph_name.text() != unique_morph_name:
            self.no_update = True
            self.textbox_morph_name.setText(unique_morph_name)
            self.no_update = False

    def update_dropdown_category(self):
        if self.no_update:
            return
        self.no_update = True
        self.category = self.dropdown_category.currentText()
        self.label_slider_path.setText("/Actor/" + self.category + "/")
        self.no_update = False

    def update_textbox_slider_path(self):
        if self.no_update:
            return
        self.slider_path = self.textbox_slider_path.text()

    def update_spinbox_min(self):
        if self.no_update:
            return
        self.morph_min_value = int(self.spinbox_min.value())

    def update_spinbox_max(self):
        if self.no_update:
            return
        self.morph_max_value = int(self.spinbox_max.value())

    def update_radio_source_morph(self):
        if self.no_update:
            return
        if self.radio_current_morph.isChecked():
            self.source_base_type = EChooseBase_Current
        else:
            self.source_base_type = EChooseBase_Default

    def update_textbox_target_path(self):
        if self.no_update:
            return
        self.no_update = True
        self.target_path = self.textbox_target_path.text()
        dir, file = os.path.split(self.target_path)
        name, ext = os.path.splitext(file)
        unique_morph_name = self.check_morph_name(name)
        self.morph_name = unique_morph_name
        self.textbox_morph_name.setText(unique_morph_name)
        key_path = os.path.join(dir, name + ".ObjKey")
        if os.path.exists(key_path):
            self.key_path = key_path
            self.textbox_key_path.setText(key_path)
        else:
            self.key_path = ""
            self.textbox_key_path.setText("")
        self.no_update = False

    def update_textbox_key_path(self):
        if self.no_update:
            return
        self.key_path = self.textbox_key_path.text()

    def button_browse_target_path(self):
        file_path = RUi.OpenFileDialog("Obj Files(*.obj)", self.target_path)
        if os.path.exists(file_path):
            self.textbox_target_path.setText(file_path)
            self.target_path = file_path
            self.update_textbox_target_path()

    def button_browse_key_path(self):
        file_path = RUi.OpenFileDialog("ObjKey Files(*.ObjKey)", self.key_path)
        if os.path.exists(file_path):
            self.textbox_key_path.setText(file_path)
            self.key_path = file_path
            self.update_textbox_key_path()

    def update_checkbox_adjust_bones(self):
        if self.no_update:
            return
        self.adjust_bones = self.checkbox_adjust_bones.isChecked()

    def update_checkbox_auto_apply(self):
        if self.no_update:
            return
        self.auto_apply = self.checkbox_auto_apply.isChecked()

    def check_morph_name(self, name):
        avatar = cc.get_first_avatar()
        ASC: RIAvatarShapingComponent = avatar.GetAvatarShapingComponent()
        names = ASC.GetShapingMorphDisplayNames("")
        base_name = name
        index = 1
        while name in names:
            name = f"{base_name}_{index}"
            index += 1
        return name

    def create_slider(self):
        if os.path.exists(self.target_path) and os.path.exists(self.key_path):

            slider_setting = RMorphSliderSetting()
            unique_morph_name = self.check_morph_name(self.morph_name)
            slider_setting.SetMorphName(unique_morph_name)
            slider_setting.SetSliderPath(self.slider_path)
            slider_setting.SetCategory(CATEGORIES[self.category])
            slider_setting.SetSourceBaseType(self.source_base_type)
            slider_setting.SetTargetFilePath(self.target_path)
            slider_setting.SetTargetMorphChecksumFilePath(self.key_path)
            slider_setting.SetAutoApplyToCurrentCharacter(self.auto_apply)
            slider_setting.SetMorphValueRange(self.morph_min_value, self.morph_max_value)
            slider_setting.SetAxisSettingForObj(EAxisSetting_YUp)
            slider_setting.SetAdjustBonesToFitMorph(self.adjust_bones)

            utils.log_info(f"Creating Morph Slider: name: {unique_morph_name}, path: {self.slider_path}")

            avatar = cc.get_first_avatar()
            ASC: RIAvatarShapingComponent = avatar.GetAvatarShapingComponent()

            slider_folder = os.path.normpath(RApplication.GetCustomContentFolder(ETemplateRootFolder_AvatarControl))
            ext = ".ccCustomSlider"
            slider_path = os.path.join(slider_folder, unique_morph_name + ext)
            ASC.CreateSlider(slider_setting, self.slider_path)
            morph_id = cc.find_morph_id(avatar, unique_morph_name)
            if morph_id is None:
                utils.log_error(f"Failed to create morph: {unique_morph_name} from {self.target_path}")
                qt.message_box("Error", f"Failed to create morph: {unique_morph_name} from {self.target_path}")
                return
            if self.auto_apply:
                if morph_id:
                    utils.log_info(f"Created Morph ID: {morph_id}")
                    min_max = ASC.GetShapingMorphMinMax(morph_id)
                    utils.log_info(f"Morph Min/Max: {min_max[0]}/{min_max[1]}")
                    ASC.SetShapingMorphWeight(morph_id, min_max[1])
                    avatar.Update()

        self.window.Close()






def poke_morph_zero(avatar: RIAvatar):
    ASC: RIAvatarShapingComponent = avatar.GetAvatarShapingComponent()
    ids = ASC.GetShapingMorphIDs("")
    if len(ids) > 0:
        morph_0 = ids[0]
        w = ASC.GetShapingMorphWeight(morph_0)
        ASC.SetShapingMorphWeight(morph_0, w + 1)
        ASC.SetShapingMorphWeight(morph_0, w)
