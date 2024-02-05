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
import time
from . import utils
from PySide2.QtWidgets import *
from PySide2.QtCore import Qt, Signal, QSize
from PySide2.QtGui import *
from shiboken2 import wrapInstance


STYLE_NONE = ""
STYLE_TITLE = "color: white; font: bold"
STYLE_BUTTON_BOLD = "color: white; font: bold 14px"
STYLE_RL_DESC = "color: #d2ff7b; font: italic 13px"
STYLE_RL_TITLEBAR = "background-color: #82be0f; color: black; font: bold"
STYLE_RL_TAB = "background-color: none; color: white; font: bold"
STYLE_RL_TAB_SELECTED = "background-color: gray; color: white; font: bold"
TINY_TEXT = "font: bold 4px"
BUTTON_HEIGHT = 32
ALIGN_CENTRE = Qt.AlignCenter
HORIZONTAL = Qt.Horizontal


def window(title, width = 400, changed=None):
    window: RLPy.RIDockWidget
    dock: QDockWidget

    window = RLPy.RUi.CreateRDockWidget()
    window.SetWindowTitle(title)
    window.SetAllowedAreas(RLPy.EDockWidgetAreas_AllFeatures)
    window.SetFeatures(RLPy.EDockWidgetFeatures_AllFeatures)
    dock = wrapInstance(int(window.GetWindow()), QDockWidget)
    #dock.setFixedWidth(width)
    dock.setMinimumWidth(width)
    widget = QWidget()
    dock.setWidget(widget)
    layout = QVBoxLayout()
    widget.setLayout(layout)

    if changed:
        dock.visibilityChanged.connect(changed)

    return window, layout


def find_add_plugin_menu(name):
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


def add_menu_action(menu: QMenu, name, action=None):
    actions = menu.actions()
    to_remove = []
    for a in actions:
        if a.text() == name:
            to_remove.append(a)
    for a in to_remove:
        menu.removeAction(a)
    menu_action: QAction = menu.addAction(name)
    menu_action.triggered.connect(action)
    return menu_action


def get_main_window() -> QMainWindow:
    main_window: QMainWindow = wrapInstance(int(RLPy.RUi.GetMainWindow()), QMainWindow)
    return main_window


def find_add_toolbar(name) -> QToolBar:
    rl_tool_bar = RLPy.RUi.FindToolBar(name)
    if rl_tool_bar:
        tool_bar = wrapInstance(int(rl_tool_bar), QToolBar)
    else:
        main_window = get_main_window()
        tool_bar = QToolBar(name)
        tool_bar.setIconSize(QSize(24, 24))
        main_window.addToolBar(tool_bar)
    return tool_bar


def clear_tool_bar(tool_bar):
    tool_bar.clear()


def get_icon(file_name):
    icon_path = utils.get_resource_path("icons", file_name)
    return QIcon(icon_path)


def add_tool_bar_action(tool_bar: QToolBar, icon, text, action=None):
    icon_path = utils.get_resource_path("icons", "BlenderLogo.png")
    tool_bar_action: QAction = tool_bar.addAction(icon, text)
    tool_bar_action.setText(text)
    tool_bar_action.triggered.connect(action)
    return tool_bar_action


class QLabelClickable(QLabel):
    clicked=Signal()

    def mousePressEvent(self, ev):
        self.clicked.emit()


def label(layout, text, style = STYLE_NONE,
          row=-1, col=-1, align=None, wrap=False, dblclick = None):

    w = QLabelClickable()
    w.setText(text)
    w.setStyleSheet(style)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    if wrap:
        w.setWordWrap(True)
    if dblclick:
        w.clicked.connect(dblclick)
    return w


def spacing(layout, size):
    w = layout.addSpacing(size)
    return w


def stretch(layout, size):
    w = layout.addStretch(size)
    return w


def frame(layout, style = "", line_width = 1):
    f = QFrame()
    f.setFrameShape(QFrame.StyledPanel)
    f.setFrameShadow(QFrame.Plain)
    f.setLineWidth(line_width)
    l = QVBoxLayout(f)
    layout.addWidget(f)
    return l


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


def checkbox(layout, label, checked, style = STYLE_NONE,
             row=-1, col=-1, align=None, update=None):

    w = QCheckBox()
    w.setText(label)
    w.setChecked(checked)
    w.setStyleSheet(style)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col)
    else:
        layout.addWidget(w)
    if update:
        w.stateChanged.connect(update)
    if align:
        w.setAlignment(align)
    return w


def container(layout, style = STYLE_NONE,
              row=-1, col=-1, align=None):
    w = QWidget()
    w.setStyleSheet(style)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    return w


def textbox(layout, text, style = STYLE_NONE, read_only = False,
            width=0, height=0, row = -1, col = -1, align=None, update=None):

    w = QLineEdit(readOnly=read_only)
    w.setText(text)
    w.setStyleSheet(style)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    if update:
        w.editingFinished.connect(update)
    if width:
        w.setFixedWidth(width)
    if height:
        w.setFixedHeight(height)
    return w


def combobox(layout, text, style = STYLE_NONE, options=None,
             width=0, height=0, row = -1, col = -1, align=None, update=None):

    w = QComboBox()
    w.setStyleSheet(style)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    if update:
        w.currentTextChanged.connect(update)
    if width:
        w.setFixedWidth(width)
    if height:
        w.setFixedHeight(height)
    if options:
        for option in options:
            w.addItem(option)
    return w


def spinbox(layout, min, max, step, value, style = STYLE_NONE, read_only = False,
            width=0, height=0, row = -1, col = -1, align=None, update=None):

    w = QSpinBox(readOnly=read_only)
    w.setRange(min, max)
    w.setValue(value)
    w.setStyleSheet(style)
    w.setSingleStep(step)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    if update:
        w.valueChanged.connect(update)
    if width:
        w.setFixedWidth(width)
    if height:
        w.setFixedHeight(height)
    return w


def button(layout, text, func=None, style="",
           width=0, height=BUTTON_HEIGHT, row=-1, col=-1, align=None,
           toggle=False, value=False):

    w = QPushButton(text, minimumHeight=height, minimumWidth=width)
    w.setStyleSheet(style)
    if func:
        w.clicked.connect(func)
    if toggle:
        w.setCheckable(True)
        w.setChecked(value)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col)
    else:
        layout.addWidget(w)
    if align:
        w.setAlignment(align)
    return w


def slider(layout, min, max, step, value, style = STYLE_NONE,
           row = -1, col = -1, align=None, update=None):

    w = QSlider(HORIZONTAL)
    w.setRange(min, max)
    w.setSingleStep(step)
    w.setStyleSheet(style)
    #w.setPageStep(pageStep)
    w.setValue(value)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col)
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
             width=0, height=0, row = -1, col = -1, align=None):

    w = QProgressBar(minimumHeight=height, minimumWidth=width)
    w.setRange(min, max)
    w.setValue(value)
    w.setFormat(text)
    w.setStyleSheet(style)
    if row >= 0 and col >= 0:
        layout.addWidget(w, row, col)
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


def message_box(msg):
    RLPy.RUi.ShowMessageBox("Message", str(msg), RLPy.EMsgButton_Ok)


def do_events():
    QApplication.processEvents()

