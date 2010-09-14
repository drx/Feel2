#!/usr/bin/env python
import sys
from PyQt4 import QtGui, QtCore
from editor import Editor
from games import ROMs


class Window(QtGui.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setWindowTitle("Feel2")
        self.editor = Editor()
        self.setCentralWidget(self.editor)
       
        self.max_recent_projects = 10

        self.create_menus()
        self.create_shortcuts()
        self.read_settings()

    def create_shortcuts(self):
        self.shortcuts = []

        shortcut = QtGui.QShortcut(QtCore.Qt.CTRL + QtCore.Qt.SHIFT + QtCore.Qt.Key_M, self)
        shortcut.activated.connect(self.toggle_menu)
        self.shortcuts.append(shortcut)

        shortcut = QtGui.QShortcut(QtCore.Qt.CTRL + QtCore.Qt.SHIFT + QtCore.Qt.Key_F, self)
        shortcut.activated.connect(self.toggle_full_screen)
        self.shortcuts.append(shortcut)

        shortcut = QtGui.QShortcut(QtCore.Qt.Key_F11, self)
        shortcut.activated.connect(self.toggle_full_screen)
        self.shortcuts.append(shortcut)

    def create_menus(self):
        self.menus = {}
        self.menus['project'] = self.menuBar().addMenu('&Project')

        action = QtGui.QAction("&Load project", self, triggered=self.load_project)
        action.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_L)
        self.menus['project'].addAction(action)

        self.menus['load_rom'] = self.menus['project'].addMenu('Load &ROM')
        for rom in ROMs:
            self.menus['load_rom'].addAction(QtGui.QAction(rom['name'], self, triggered=self.load_rom(rom['class'])))

        self.menus['project'].addSeparator()
        action = QtGui.QAction("&Save project", self, triggered=self.editor.save_project)
        action.setShortcut(QtCore.Qt.CTRL + QtCore.Qt.Key_S)
        self.menus['project'].addAction(action)

        self.menus['project'].addSeparator()
        self.menus['recent_projects'] = self.menus['project'].addMenu('Recent projects')

        self.recent_project_actions = []
        for i in range(self.max_recent_projects):
            self.recent_project_actions.append(QtGui.QAction(self, visible=False, triggered=self.load_recent_project))
            if i in range(9):
                key = QtCore.Qt.CTRL + QtCore.Qt.Key_1 + i
            elif i == 9:
                key = QtCore.Qt.CTRL + QtCore.Qt.Key_0
            else:
                key = None
            if key is not None:
                self.recent_project_actions[i].setShortcut(key)
            self.menus['recent_projects'].addAction(self.recent_project_actions[i])

        self.update_recent_projects()

        self.menus['help'] = self.menuBar().addMenu('&Help')
        self.menus['help'].addAction(QtGui.QAction("&About Feel2", self, triggered=self.about))

    def toggle_menu(self):
        self.menuBar().setVisible(not self.menuBar().isVisible())

    def toggle_full_screen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def load_recent_project(self):
        action = self.sender()
        if action:
            self.load_project_file(action.data().toPyObject())

    def add_recent_project(self, name, filename):
        recent_projects = self.settings.value("recent_projects").toPyObject()
        if recent_projects is None:
            recent_projects = []

        key = (name, filename)
        try:
            recent_projects.remove(key)
        except ValueError:
            pass
        
        recent_projects.insert(0, key)
        del recent_projects[self.max_recent_projects:]
        self.settings.setValue("recent_projects", recent_projects)

        self.update_recent_projects()

    def update_recent_projects(self):
        recent_projects = self.settings.value("recent_projects").toPyObject()
        if recent_projects is None:
            return

        n_recent_projects = min(len(recent_projects), self.max_recent_projects)
        
        import os.path
        for i in range(n_recent_projects):
            name, filename = recent_projects[i]
            text = '{name} ({filename})'.format(name=name, filename=os.path.basename(filename))
            self.recent_project_actions[i].setText(text)
            self.recent_project_actions[i].setData(filename)
            self.recent_project_actions[i].setVisible(True)

        for i in range(n_recent_projects, self.max_recent_projects):
            self.recent_project_actions[i].setVisible(False)

    def load_project(self):
        file_dialog = QtGui.QFileDialog()
        file_dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Feel projects (*.fap)")
        file_dialog.restoreState(self.settings.value("loadproject/state").toByteArray())
        file_dialog.exec_()
        for filename in file_dialog.selectedFiles():
            self.load_project_file(filename)
        self.settings.setValue("loadproject/state", file_dialog.saveState())

    def load_project_file(self, filename):
        name = self.editor.load_project(str(filename))
        self.add_recent_project(name, str(filename))

    def load_rom(self, rom_class):
        def do():
            file_dialog = QtGui.QFileDialog()
            file_dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
            file_dialog.setNameFilter("ROMs (*.*)")
            file_dialog.restoreState(self.settings.value("loadrom/state").toByteArray())
            file_dialog.exec_()
            selected_filename = None
            for filename in file_dialog.selectedFiles():
                selected_filename = filename
            self.settings.setValue("loadrom/state", file_dialog.saveState())
            self.editor.load_rom(rom_class, selected_filename)
        return do

    def about(self):
        pass

    @property
    def settings(self):
        return QtCore.QSettings("Feel2", "Feel2")

    def read_settings(self):
        self.resize(self.settings.value("window/size", QtCore.QSize(800, 600)).toSize())
        self.move(self.settings.value("window/pos", QtCore.QPoint(100, 100)).toPoint())

    def save_settings(self):
        self.settings.setValue("window/size", self.size())
        self.settings.setValue("window/pos", self.pos())        

    def closeEvent(self, event):
        self.save_settings()


def main(argv): 
    app = QtGui.QApplication(argv)
    app.setStyle(QtGui.QStyleFactory.create('Plastique'))

    stylesheet = open('stylesheet.qss', 'r').read()
    app.setStyleSheet(stylesheet)

    window = Window() 
    window.show() 

    app.exec_()

if __name__=="__main__":
    main(sys.argv)
