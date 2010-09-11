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

        self.create_menus()
        self.read_settings()

    def create_menus(self):
        self.menus = {}
        self.menus['project'] = self.menuBar().addMenu('&Project')
        self.menus['project'].addAction(QtGui.QAction("&Load project", self, triggered=self.load_project))
        self.menus['load_rom'] = self.menus['project'].addMenu('Load &ROM')
        for rom in ROMs:
            self.menus['load_rom'].addAction(QtGui.QAction(rom['name'], self, triggered=self.load_rom(rom['class'])))
        self.menus['help'] = self.menuBar().addMenu('&Help')
        self.menus['help'].addAction(QtGui.QAction("&About Feel2", self, triggered=self.about))

    def load_project(self):
        file_dialog = QtGui.QFileDialog()
        file_dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        file_dialog.setNameFilter("Feel projects (*.fap)")
        file_dialog.restoreState(self.settings.value("loadproject/state").toByteArray())
        file_dialog.exec_()
        for filename in file_dialog.selectedFiles():
            self.editor.load_fap(filename)
        self.settings.setValue("loadproject/state", file_dialog.saveState())

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
 
    sys.exit(app.exec_())

if __name__=="__main__":
    main(sys.argv)
