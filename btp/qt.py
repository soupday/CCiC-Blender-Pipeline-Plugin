# Copyright (C) 2023 Victor Soupday
# This file is part of CC/iC-Blender-Pipeline-Plugin <https://github.com/soupday/CCiC-Blender-Pipeline-Plugin>
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
import time
from . import utils
from PySide2.QtWidgets import *
from PySide2.QtCore import *
from PySide2.QtCore import Qt, Signal, QSize, QRect, QPoint, QTimer
from PySide2.QtGui import *
from shiboken2 import wrapInstance


STYLE_NONE = ""
STYLE_TITLE = "color: white; font: bold"
STYLE_BOLD = "font: bold"
STYLE_ITALIC = "font: italic 13px"
STYLE_ITALIC_SMALL = "font: italic 10px"
STYLE_VERSION = "font: italic 10px; text-align: right; color: #888888"
STYLE_RL_BOLD = "color: #d2ff7b; font: bold"
STYLE_BUTTON = ""
STYLE_ICON_BUTTON_PADDED = "text-align: left;"
STYLE_ICON_BUTTON_PADDED_BOLD = "color: white; font: bold 14px; text-align: left;"
STYLE_BLENDER_TOGGLE = """QPushButton { border: 1px solid #505050; }
                          QPushButton:hover { border: 1px solid 505050; background-color: #505050; }
                          QPushButton:pressed { border: 1px solid 505050; background-color: #4772b3; }
                          QPushButton:checked { border: 1px solid 505050; background-color: #4772b3; }
                          """
STYLE_BUTTON_WAITING = "background-color: #505050; color: white; font: bold"
STYLE_BUTTON_ACTIVE = "background-color: #82be0f; color: black; font: bold"
STYLE_BUTTON_ACTIVE_ALT = "background-color: #dfdf12; color: black; font: bold"
STYLE_BUTTON_BOLD = "color: white; font: bold 14px"
STYLE_RL_DESC = "color: #d2ff7b; font: italic 13px"
STYLE_RL_TITLEBAR = "background-color: #82be0f; color: black; font: bold"
STYLE_RL_TAB = "background-color: none; color: white; font: bold"
STYLE_RL_TAB_SELECTED = "background-color: gray; color: white; font: bold"
TINY_TEXT = "font: bold 4px"
BUTTON_HEIGHT = 32
ALIGN_LEFT = Qt.AlignLeft
ALIGN_CENTRE = Qt.AlignCenter
HORIZONTAL = Qt.Horizontal
ICON_BUTTON_HEIGHT = 64
STYLE_ICON_BUTTON = ""
BLANK_ICON: QIcon = None

def window(title, width=400, height=0, fixed=False, show_hide=None):
    window: RLPy.RIDockWidget
    window = RLPy.RUi.CreateRDockWidget()
    window.SetWindowTitle(title)
    window.SetAllowedAreas(RLPy.EDockWidgetAreas_AllFeatures)
    window.SetFeatures(RLPy.EDockWidgetFeatures_AllFeatures)
    dock = get_dock_widget(window)
    if fixed and width > 0:
        dock.setFixedWidth(width)
    if fixed and height > 0:
        dock.setFixedHeight(height)
    if width > 0:
        dock.setMinimumWidth(width)
    if height > 0:
        dock.setMinimumHeight(height)
    widget = QWidget()
    dock.setWidget(widget)
    layout = QVBoxLayout()
    widget.setLayout(layout)

    if show_hide:
        dock.visibilityChanged.connect(show_hide)

    return window, layout


def get_dock_widget(ri_dock: RLPy.RIDockWidget) -> QDockWidget:
    dock: QDockWidget = wrapInstance(int(ri_dock.GetWindow()), QDockWidget)
    return dock


def get_main_window() -> QMainWindow:
    main_window: QMainWindow = wrapInstance(int(RLPy.RUi.GetMainWindow()), QMainWindow)
    return main_window


def place_window(window: RLPy.RIDockWidget, px, py):
    """Places window at a percentage position of the main window width and height"""
    dock: QDockWidget = wrapInstance(int(window.GetWindow()), QDockWidget)
    main_window = get_main_window()
    dock_geo: QRect = dock.geometry()
    main_geo: QRect = main_window.geometry()
    pos = QPoint(max(10, main_window.x() + (main_geo.width() * px) - (dock_geo.width() / 2)),
                 max(10, main_window.y() + (main_geo.height() * py) - (dock_geo.height() / 2)))
    dock.move(pos)


def find_plugin_menu(name) -> QMenu:
    rl_menu = RLPy.RUi.FindMenu(name)
    if rl_menu:
        return wrapInstance(int(rl_menu), QMenu)
    return None


def find_add_plugin_menu(name) -> QMenu:
    rl_menu = RLPy.RUi.FindMenu(name)
    if rl_menu:
        menu = wrapInstance(int(rl_menu), QMenu)
    else:
        menu = wrapInstance(int(RLPy.RUi.AddMenu(name, RLPy.EMenu_Plugins)), QMenu)
    return menu


def clear_menu(menu: QMenu):
    menu.clear()


def menu_separator(menu: QMenu):
    menu.addSeparator()


def find_menu_action(menu: QMenu, name):
    actions = menu.actions()
    for a in actions:
        if a.text() == name:
            return a
    return None


def get_blank_icon():
    global BLANK_ICON
    if not BLANK_ICON:
        BLANK_ICON = get_icon("Blank.png")
    return BLANK_ICON


def add_menu_action(menu: QMenu, name, action=None, toggle=False, icon=None, blank_icon=False, on=False):
    actions = menu.actions()
    to_remove = []
    for a in actions:
        if a.text() == name:
            to_remove.append(a)
    for a in to_remove:
        menu.removeAction(a)
    menu_action = QAction(name, menu, checkable=toggle)
    if toggle and on:
        menu_action.setChecked(on)
    if icon:
        menu_action.setIcon(icon)
    elif blank_icon:
        menu_action.setIcon(get_blank_icon())
    menu_action.triggered.connect(action)
    menu.addAction(menu_action)
    return menu_action


def get_main_window() -> QMainWindow:
    main_window: QMainWindow = wrapInstance(int(RLPy.RUi.GetMainWindow()), QMainWindow)
    return main_window


def find_toolbar(name) -> QToolBar:
    rl_toolbar = RLPy.RUi.FindToolBar(name)
    if rl_toolbar:
        toolbar: QToolBar = wrapInstance(int(rl_toolbar), QToolBar)
        return toolbar
    return None


def find_add_toolbar(name, show_hide=None) -> QToolBar:
    rl_toolbar = RLPy.RUi.FindToolBar(name)
    if rl_toolbar:
        toolbar: QToolBar = wrapInstance(int(rl_toolbar), QToolBar)
    else:
        main_window = get_main_window()
        toolbar = QToolBar(name)
        main_window.addToolBar(toolbar)
    toolbar.setMovable(True)
    toolbar.setFloatable(True)
    try:
        toolbar.visibilityChanged.disconnect()
    except:
        ...
    toolbar.visibilityChanged.connect(show_hide)
    #toolbar.setIconSize(QSize(16, 16))
    #toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
    toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
    return toolbar


def remove_toolbar(name):
    rl_toolbar = RLPy.RUi.FindToolBar(name)
    if rl_toolbar:
        toolbar = wrapInstance(int(rl_toolbar), QToolBar)
        if toolbar:
            clear_toolbar(toolbar)
            main_window = get_main_window()
            main_window.removeToolBar(toolbar)
            return True
    return False


def clear_toolbar(toolbar):
    toolbar.clear()


def find_toolbar_action(toolbar_name, action_name):
    rl_toolbar = RLPy.RUi.FindToolBar(toolbar_name)
    if rl_toolbar:
        toolbar: QToolBar = wrapInstance(int(rl_toolbar), QToolBar)
        if toolbar:
            action: QAction
            for action in toolbar.actions():
                if action.text() == action_name:
                    return action
    return None


def toggle_toolbar_action(toolbar_name, action_name, toggled):
    toolbar_action = find_toolbar_action(toolbar_name, action_name)
    if toolbar_action:
        if not toolbar_action.isCheckable():
            toolbar_action.setCheckable(True)
        toolbar_action.setChecked(toggled)


def get_icon(file_name):
    icon_path = utils.get_resource_path("icons", file_name)
    return QIcon(icon_path)


def get_pixmap(file_name):
    pixmap_path = utils.get_resource_path("icons", file_name)
    return QPixmap(pixmap_path)


def add_toolbar_label(toolbar: QToolBar, icon=None, text=None):
    if text:
        l = QLabel()
        l.setText(text)
        toolbar.addWidget(l)
    if icon:
        if type(icon) is str:
            pixmap = get_pixmap(utils.get_resource_path("icons", icon))
        else:
            pixmap = icon.pixmap(QSize(16, 16))
        l = QLabel()
        l.setPixmap(pixmap)
        toolbar.addWidget(l)


def add_toolbar_action(toolbar: QToolBar, icon, text, action=None, toggle=False):
    icon_path = utils.get_resource_path("icons", "BlenderLogo.png")
    if text:
        toolbar_action: QAction = toolbar.addAction(icon, text)
        toolbar_action.setText(text)
        toolbar_action.setIconText(text)
    else:
        toolbar_action: QAction = toolbar.addAction(icon, None)
    if action:
        toolbar_action.triggered.connect(action)
    if toggle:
        toolbar_action.setCheckable(True)
    return toolbar_action


def add_toolbar_separator(toolbar: QToolBar):
    toolbar.addSeparator()


class QLabelClickable(QLabel):
    clicked=Signal()

    def mousePressEvent(self, ev):
        self.clicked.emit()


def label(layout: QLayout, text, style = STYLE_NONE,
          row=-1, col=-1, row_span=1, col_span=1,
          align=None, wrap=False, dblclick = None, no_size=False,
          width=-1, height=-1):

    w = QLabelClickable()
    w.setText(text)
    w.setStyleSheet(style)
    if no_size:
        p = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        p.setHorizontalPolicy(QSizePolicy.Ignored)
        w.setSizePolicy(p)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col, row_span, col_span)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    if wrap:
        w.setWordWrap(True)
    if width >= 0:
        w.setFixedWidth(width)
    if height >= 0:
        w.setFixedHeight(height)
    if dblclick:
        w.clicked.connect(dblclick)
    return w


def spacing(layout: QLayout, size):
    w = layout.addSpacing(size)
    return w


def separator(layout: QLayout, line_width: int, style=""):
    f = QFrame()
    f.setFrameShape(QFrame.HLine)
    f.setFrameShadow(QFrame.Plain)
    f.setLineWidth(line_width)
    if not style:
        style = "color: #555555;"
    f.setStyleSheet(style)
    layout.addWidget(f)
    return f


def stretch(layout: QLayout, size):
    w = layout.addStretch(size)
    return w


def frame(layout: QLayout, style = "", line_width = 1):
    f = QFrame()
    f.setFrameShape(QFrame.StyledPanel)
    f.setFrameShadow(QFrame.Plain)
    f.setLineWidth(line_width)
    if style:
        f.setStyleSheet(style)
    l = QVBoxLayout(f)
    layout.addWidget(f)
    return f, l


def group(layout: QLayout, style="", title=""):
    g = QGroupBox()
    if style:
        g.setStyleSheet(style)
    if title:
        g.setTitle(title)
    l = QVBoxLayout(g)
    layout.addWidget(g)
    return g, l

def scroll_area(layout: QLayout, vertical=True, horizontal=False):
    s = QScrollArea()
    w = QWidget()
    l = QVBoxLayout()
    w.setLayout(l)
    s.setWidget(w)
    s.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded if vertical else Qt.ScrollBarAlwaysOff)
    s.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded if horizontal else Qt.ScrollBarAlwaysOff)
    s.setWidgetResizable(True)
    s.setFrameStyle(QFrame.NoFrame)
    layout.addWidget(s)
    return s, l


def grid(layout):
    l = QGridLayout()
    layout.addLayout(l)
    return l


def row(layout):
    l = QHBoxLayout()
    layout.addLayout(l)
    return l


def column(layout):
    l = QVBoxLayout()
    layout.addLayout(l)
    return l


TAB_STYLE = """
QTabWidget::pane {
    border: 1px solid #505050;
}

QTabWidget::tab-bar {
}

QTabBar::tab {
    border: 1px solid #373737;
    height: 24px;
    min-height: 24px;
    min-width: 44px;
    padding: 6px 12px 6px 12px;
}

QTabBar::tab:selected {
    border: 1px solid #a0a0a0;
}
"""


def tab(layout):
    t = QTabWidget()
    t.setStyleSheet(TAB_STYLE)
    layout.addWidget(t)
    return t


def page(tab_widget: QTabWidget, name: str):
    p = QWidget()
    tab_widget.addTab(p, name)
    layout = QVBoxLayout()
    p.setLayout(layout)
    return layout


def checkbox(layout: QLayout, label, checked, style = STYLE_NONE,
             row=-1, col=-1, row_span=1, col_span=1,
             align=None, update=None):

    w = QCheckBox()
    w.setText(label)
    w.setChecked(checked)
    w.setStyleSheet(style)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col, row_span, col_span)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    if update:
        w.stateChanged.connect(update)
    return w


def radio_button(layout: QLayout, label, down: bool, style = STYLE_NONE,
                 row=-1, col=-1, row_span=1, col_span=1,
                 align=None, update=None):
    w = QRadioButton()
    w.setText(label)
    w.setChecked(down)
    w.setDown(down)
    w.setStyleSheet(style)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col, row_span, col_span)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    if update:
        w.toggled.connect(update)
    return w


def container(layout: QLayout, style = STYLE_NONE,
              row=-1, col=-1, row_span=1, col_span=1, align=None):
    w = QWidget()
    w.setStyleSheet(style)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col, row_span, col_span)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    return w


def textbox(layout: QLayout, text, style = STYLE_NONE, read_only = False,
            width=0, height=0, row = -1, col = -1, row_span=1, col_span=1,
            align=None, update=None):

    w = QLineEdit(readOnly=read_only)
    w.setText(text)
    w.setStyleSheet(style)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col, row_span, col_span)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    if width:
        w.setFixedWidth(width)
    if height:
        w.setFixedHeight(height)
    if update:
        w.editingFinished.connect(update)
    return w


def combobox(layout: QLayout, text, style = STYLE_NONE, options=None,
             width=0, height=0, row = -1, col = -1, row_span=1, col_span=1,
             align=None, update=None) -> QComboBox:

    w = QComboBox()
    w.setStyleSheet(style)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col, row_span, col_span)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    if width:
        w.setFixedWidth(width)
    if height:
        w.setFixedHeight(height)
    if options:
        for i, option in enumerate(options):
            w.addItem(option)
            if text == option:
                w.setCurrentIndex(i)
    if update:
        w.currentTextChanged.connect(update)
    return w


def update_combobox_options(cb: QComboBox, options, current):
    cb.clear()
    for i, option in enumerate(options):
        cb.addItem(option)
        if current == option:
            cb.setCurrentIndex(i)


def spinbox(layout: QLayout, min, max, step, value, style = STYLE_NONE, read_only = False,
            width=0, height=0, row = -1, col = -1, row_span=1, col_span=1,
            align=None, update=None):

    w = QSpinBox(readOnly=read_only)
    w.setRange(min, max)
    w.setValue(value)
    w.setStyleSheet(style)
    w.setSingleStep(step)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col, row_span, col_span)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    if width:
        w.setFixedWidth(width)
    if height:
        w.setFixedHeight(height)
    if update:
        w.valueChanged.connect(update)
    return w


class DComboBox(QWidget):
    combo: QComboBox = None
    obj = None
    prop = None
    default_value = None
    valueChanged = Signal()
    no_update: bool = False
    options: list = None

    def __init__(self, layout: QLayout, obj, prop, value, options: list,
                       row=-1, col=-1, row_span=1, col_span=1, style="",
                       update=None):
        super().__init__()
        self.obj = obj
        self.prop = prop
        value = self.get_value()
        self.default_value = value
        self.options = options

        self.combo = QComboBox()
        self.combo.setStyleSheet(style)
        if row >= 0 and col >= 0:
            layout.addWidget(self.combo, row, col, row_span, col_span)
        else:
            layout.addWidget(self.combo)
        if options:
            for i, option in enumerate(options):
                if type(option) is list:
                    self.combo.addItem(option[1])
                else:
                    self.combo.addItem(option)
                    if value == option:
                        self.combo.setCurrentIndex(i)
        if update:
            value.valueChanged.connect(update)
        self.combo.currentIndexChanged.connect(self.combo_value_changed)

    def update_value(self):
        value = self.get_value()
        us = self.no_update
        self.no_update = True
        for i, option in enumerate(self.options):
            if type(option) is list:
                if value == option[0]:
                    self.combo.setCurrentIndex(i)
            else:
                if value == option:
                    self.combo.setCurrentIndex(i)
        self.no_update = us

    def set_value(self, value: float):
        setattr(self.obj, self.prop, value)
        us = self.no_update
        self.no_update = True
        for i, option in enumerate(self.options):
            if type(option) is list:
                if value == option[1]:
                    self.combo.setCurrentIndex(i)
            else:
                if value == option:
                    self.combo.setCurrentIndex(i)
        self.no_update = us

    def get_value(self):
        value = None
        if self.obj and self.prop:
            if hasattr(self.obj, self.prop):
                value = getattr(self.obj, self.prop)
            else:
                utils.log_error(f"Object: {self.obj} has no attribute {self.prop}")
        return value

    def combo_value_changed(self):
        if not self.no_update:
            self.no_update = True
            index = self.combo.currentIndex()
            option = self.options[index]
            if type(option) is list:
                value = option[0]
            else:
                value = option
            setattr(self.obj, self.prop, value)
            self.valueChanged.emit()
            self.no_update = False


class DFQSliderSpin(QWidget):
    spinbox: QSpinBox = None
    label: QLabel = None
    slider: QSlider = None
    obj = None
    prop = None
    scale: float = 100
    min: float = 0
    max: float = 1
    step: float = 0.01
    default_value: int = 0
    clicked = Signal()
    valueChanged = Signal()
    no_update: bool = False

    def __init__(self, layout: QLayout, label, obj, prop, min, max, step, scale=100,
                 readOnly=False, row=-1, col=-1, skip=0, label_style="", slider_style="", spinbox_style="",
                 update=None, clicked=None):
        super().__init__()
        self.obj = obj
        self.prop = prop
        self.scale = scale
        self.min = min
        self.max = max
        self.step = step
        value = self.get_value()
        self.default_value = value
        min *= scale
        max *= scale
        step *= scale
        value *= self.scale
        #
        self.label = QLabelClickable()
        self.label.setText(label)
        self.label.setStyleSheet(label_style)
        #
        self.slider = QSlider(HORIZONTAL)
        self.slider.setRange(min, max)
        self.slider.setSingleStep(step)
        self.slider.setStyleSheet(slider_style)
        self.slider.setValue(value)
        #
        self.spinbox = QSpinBox(readOnly=readOnly)
        self.spinbox.setRange(min, max)
        self.spinbox.setValue(value)
        self.spinbox.setSingleStep(step)
        self.spinbox.setStyleSheet(spinbox_style)
        #
        if row >= 0 and col >= 0:
            layout.addWidget(self.label, row, col)
            col += 1 + skip
            layout.addWidget(self.slider, row, col)
            col += 1 + skip
            layout.addWidget(self.spinbox, row, col)
        else:
            layout.addWidget(self.label)
            layout.addWidget(self.slider)
            layout.addWidget(self.spinbox)
        #
        if update:
            self.valueChanged.connect(update)
        if clicked:
            self.clicked.connect(clicked)
        self.label.clicked.connect(self.label_clicked)
        self.slider.valueChanged.connect(self.slider_value_changed)
        self.spinbox.valueChanged.connect(self.spinbox_value_changed)

    def update_value(self):
        value = self.get_value()
        scaled = value * self.scale
        us = self.no_update
        self.no_update = True
        self.slider.setValue(scaled)
        self.spinbox.setValue(scaled)
        self.no_update = us

    def set_value(self, value: float):
        setattr(self.obj, self.prop, value)
        scaled = value * self.scale
        us = self.no_update
        self.no_update = True
        self.slider.setValue(scaled)
        self.spinbox.setValue(scaled)
        self.no_update = us

    def get_value(self):
        value = None
        if self.obj and self.prop:
            if hasattr(self.obj, self.prop):
                value = getattr(self.obj, self.prop)
            else:
                utils.log_error(f"Object: {self.obj} has no attribute {self.prop}")
        return value

    def label_clicked(self):
        self.set_value(self.default_value)
        self.clicked.emit()

    def spinbox_value_changed(self):
        if not self.no_update:
            self.no_update = True
            value = self.spinbox.value()
            descaled = value / self.scale
            self.slider.setValue(value)
            setattr(self.obj, self.prop, descaled)
            self.valueChanged.emit()
            self.no_update = False

    def slider_value_changed(self):
        if not self.no_update:
            self.no_update = True
            value = self.slider.value()
            descaled = value / self.scale
            self.spinbox.setValue(value)
            setattr(self.obj, self.prop, descaled)
            self.valueChanged.emit()
            self.no_update = False


class DColorPicker(QWidget):
    button: QPushButton = None
    label: QLabel = None
    obj = None
    prop = None
    default_color = QColor(255,255,255)
    valueChanged = Signal()

    def __init__(self, layout, label, obj, prop, text="", width=0, height=0,
                 row=-1, col=-1, skip=0, update=None, label_style="", tooltip=""):
        super().__init__()
        self.obj = obj
        self.prop = prop
        color = self.get_color()
        self.default_color = color
        self.button = QPushButton(text, minimumHeight=height, minimumWidth=width)
        self.button.setStyleSheet(f"background-color: {color.name()}")
        if tooltip:
            self.button.setToolTip(tooltip)
        if label:
            self.label = QLabelClickable()
            self.label.setText(label)
            self.label.setStyleSheet(label_style)
        if width:
            self.button.setFixedWidth(width)
        if height:
            self.button.setFixedHeight(height)
        if row >= 0 and col >= 0:
            if label:
                layout.addWidget(self.label, row, col)
                col += 1 + skip
            layout.addWidget(self.button, row, col)
        else:
            if label:
                layout.addWidget(self.label)
            layout.addWidget(self.button)
        if update:
            self.valueChanged.connect(update)
        #
        self.button.clicked.connect(self.button_clicked)
        if label:
            self.label.clicked.connect(self.label_clicked)
        print("DONE")

    def update_color(self):
        color = self.get_color()
        self.button.setStyleSheet(f"background-color: {color.name()}")

    def get_color(self):
        color = None
        if self.obj and self.prop:
            if hasattr(self.obj, self.prop):
                color = getattr(self.obj, self.prop)
            else:
                utils.log_error(f"Object: {self.obj} has no attribute {self.prop}")
        return color

    def set_color(self, color):
        if self.obj and self.prop:
            setattr(self.obj, self.prop, color)
            self.button.setStyleSheet(f"background-color: {color.name()}")

    def label_clicked(self):
        print("LABEL CLICKED")
        self.set_color(self.default_color)

    def button_clicked(self):
        print("BUTTON CLICKED")
        color = self.get_color()
        color: QColor = QColorDialog.getColor(initial=color)
        if color.isValid():
            self.set_color(color)
            self.valueChanged.emit()





def button(layout: QLayout, text, func=None, icon = None, style="",
           width=0, height=BUTTON_HEIGHT, row=-1, col=-1, row_span=1, col_span=1, icon_size=0,
           align=None, toggle=False, value=False, fixed=False, tooltip=None):

    w = QPushButton(text, minimumHeight=height, minimumWidth=width)
    if fixed:
        if width:
            w.setFixedWidth(width)
        if height:
            w.setFixedHeight(height)
    if icon:
        if type(icon) is str:
            w.setIcon(get_icon(icon))
            if icon_size > 0:
                w.setIconSize(QSize(icon_size, icon_size))
        elif type(icon) is QIcon:
            w.setIcon(icon)
            if icon_size > 0:
                w.setIconSize(QSize(icon_size, icon_size))
    w.setStyleSheet(style)
    if toggle:
        w.setCheckable(True)
        w.setChecked(value)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col, row_span, col_span)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    if func:
        w.clicked.connect(func)
    if tooltip:
        w.setToolTip(tooltip)
    return w


class QAlignedIconButton(QPushButton):

    align_width: int = 0
    last_width: int = 0
    toggle: bool = False

    def setAlignWidth(self, x):
        self.align_width = x

    def toggleOn(self):
        if not self.toggle:
            self.toggle = True
            self.restyle()

    def toggleOff(self):
        if self.toggle:
            self.toggle = False
            self.restyle()

    def restyle(self):
        self.last_width = self.width()
        padding = max(2, (self.last_width - self.align_width) / 2)
        if self.toggle:
            self.setStyleSheet(f"{STYLE_ICON_BUTTON_PADDED_BOLD}; padding-left: {padding}px;")
        else:
            self.setStyleSheet(f"{STYLE_ICON_BUTTON_PADDED}; padding-left: {padding}px;")

    def paintEvent(self, event):
        # Heres a total hack: whenever the button is re-drawn...
        #    if the width has changed re-calculate the padding centred around the 'alignment_width'
        if self.last_width != self.width():
            self.restyle()

        QPushButton.paintEvent(self, event)


def icon_button(layout: QLayout, text, func=None, icon = None,
           width=0, height=BUTTON_HEIGHT, row=-1, col=-1, row_span=1, col_span=1, icon_size=0,
           fixed=False, align_width=80):

    w = QAlignedIconButton(text, minimumHeight=height, minimumWidth=width)
    w.setAlignWidth(align_width)
    if fixed:
        if width:
            w.setFixedWidth(width)
        if height:
            w.setFixedHeight(height)
    if icon:
        if type(icon) is str:
            w.setIcon(get_icon(icon))
            if icon_size > 0:
                w.setIconSize(QSize(icon_size, icon_size))
        elif type(icon) is QIcon:
            w.setIcon(icon)
            if icon_size > 0:
                w.setIconSize(QSize(icon_size, icon_size))
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col, row_span, col_span)
    else:
        layout.addWidget(w)
    if func:
        w.clicked.connect(func)
    return w


def color_button(layout: QLayout, text, color: QColor, func=None,
                 width=0, height=BUTTON_HEIGHT, row=-1, col=-1, row_span=1, col_span=1, icon_size=0,
                 fixed=False):

    w = QPushButton(text, minimumHeight=height, minimumWidth=width)
    w.setStyleSheet(f"background-color: {color.name()}")
    if fixed:
        if width:
            w.setFixedWidth(width)
        if height:
            w.setFixedHeight(height)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col, row_span, col_span)
    else:
        layout.addWidget(w)
    if func:
        w.clicked.connect(func)
    return w


def set_button_color(w: QPushButton, color: QColor):
    w.setStyleSheet(f"background-color: {color.name()}")


def slider(layout: QLayout, min, max, step, value, style = STYLE_NONE,
           row = -1, col = -1, row_span=1, col_span=1,
           align=None, update=None):

    w = QSlider(HORIZONTAL)
    w.setRange(min, max)
    w.setSingleStep(step)
    w.setStyleSheet(style)
    #w.setPageStep(pageStep)
    w.setValue(value)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col, row_span, col_span)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    if update:
        w.valueChanged.connect(update)
    return w


def slider_spin_grid(grid, row, text, min, max, step, value, slider_func, spinbox_func, reset_func = None):
    l = label(grid, text, row=row, col=0, dblclick=reset_func)
    s = slider(grid, min, max, step, value, row=row, col=1, update=slider_func)
    b = spinbox(grid, min, max, step, value, row=row, col=2, width=40, update=spinbox_func)
    return l,s,b


def slider_text_grid(grid, row, text, min, max, step, value, slider_func):
    l = label(grid, text, row=row, col=0)
    s = slider(grid, min, max, step, value, row=row, col=1, update=slider_func)
    b = textbox(grid, str(value), row=row, col=2, width=45, read_only=True)
    return l,s,b


def progress(layout, min, max, value, text, style = STYLE_NONE,
             width=0, height=0, row=-1, col=-1, row_span=1, col_span=1,
             align=None):

    w = QProgressBar(minimumHeight=height, minimumWidth=width)
    w.setRange(min, max)
    w.setValue(value)
    w.setFormat(text)
    w.setStyleSheet(style)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col, row_span, col_span)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    return w


def progress_range(w, min, max):
    if w:
        w.setRange(min, max)


def progress_update(w, value, text = None):
    if w:
        w.setValue(value)
        if text is not None:
            w.setFormat(text)


def enable(*widgets):
    for w in widgets:
        if w:
            w.setEnabled(True)


def disable(*widgets):
    for w in widgets:
        if w:
            w.setEnabled(False)


def show(*widgets):
    for w in widgets:
        if w:
            w.setVisible(True)


def hide(*widgets):
    for w in widgets:
        if w:
            w.setVisible(False)


def browse_folder(title, start_folder):
    folder = QFileDialog.getExistingDirectory(None, title, start_folder, QFileDialog.Option.ShowDirsOnly)
    return folder


def image(width, height, rgb, path):
    RGB = utils.rgb_to_RGB(rgb)
    qcol = qRgb(RGB[0], RGB[1], RGB[2])
    image = QImage(width, height, QImage.Format_RGB32)
    image.fill(qcol)
    image.save(path)
    return image


def wait(t, force = False):
    if utils.DO_EVENTS or force:
        total = 0
        while total < t:
            time.sleep(0.025)
            QApplication.processEvents()
            total += 0.025


def array_to_color(c: list):
    return QColor(int(max(min(c[0]*256, 255),0)),
                  int(max(min(c[1]*256, 255),0)),
                  int(max(min(c[2]*256, 255),0)),
                  255)


def calc_target_color(color: QColor, target: QColor):
    cr = color.redF()
    cg = color.greenF()
    cb = color.blueF()
    tr = target.redF()
    tg = target.greenF()
    tb = target.blueF()
    brightness = max(tr/cr, tg/cg, tb/cb)
    cr *= brightness
    cg *= brightness
    cb *= brightness
    tint = QColor.fromRgbF(tr/cr, tg/cg, tb/cb)
    return tint, brightness


def calc_target_intensity(color: QColor, target: QColor):
    c = (color.redF() + color.greenF() + color.blueF()) / 3
    t = (target.redF() + target.greenF() + target.blueF()) / 3
    brightness = t / c
    return brightness


def color_to_array(c: QColor):
    if type(c) is str:
        c = QColor(c)
    return [c.redF(), c.greenF(), c.blueF()]


def linear_to_srgb(c: QColor):
    return QColor(int(max(min(utils.linear_to_srgbx(c.redF())*256, 255),0)),
                  int(max(min(utils.linear_to_srgbx(c.greenF())*256, 255),0)),
                  int(max(min(utils.linear_to_srgbx(c.blueF())*256, 255),0)),
                  255)


def message_box(title, msg):
    RLPy.RUi.ShowMessageBox(title, str(msg), RLPy.EMsgButton_Ok)


def do_events():
    QApplication.processEvents()


def delay_run(func, interval_msec):
    timer = QTimer()
    timer.timeout.connect(func)
    timer.setInterval(interval_msec)
    timer.start()
    return timer