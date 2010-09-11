#!/usr/bin/env python
import sys
from PyQt4 import QtGui, QtCore
from editor import Editor


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
        self.menus['help'] = self.menuBar().addMenu('&Help')
        self.menus['help'].addAction(QtGui.QAction("&About Feel2", self, triggered=self.about))

    def load_project(self):
        file_dialog = QtGui.QFileDialog()
        file_dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
        file_dialog.setNameFilters(["Feel projects (*.fap)", "ROMs (*.*)"])
        file_dialog.restoreState(self.settings.value("loadproject/state").toByteArray())
        file_dialog.exec_()
        selected_filter = file_dialog.selectedNameFilter()
        if selected_filter.startsWith('ROMs'):
            for filename in file_dialog.selectedFiles():
                self.editor.load_rom(filename)
        if selected_filter.startsWith('Feel projects'):
            print 'Not implemented'
        self.settings.setValue("loadproject/state", self.saveState())

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
