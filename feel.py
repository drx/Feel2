#!/usr/bin/env python
import sys
from PyQt4 import QtGui, QtCore
from games.ristar import Editor


def main(argv): 

    app = QtGui.QApplication(argv)
    app.setStyle(QtGui.QStyleFactory.create('Plastique'))

    stylesheet = open('stylesheet.qss', 'r').read()
    app.setStyleSheet(stylesheet)
 
    window = Editor()
    window.show() 
 
    sys.exit(app.exec_())

if __name__=="__main__":
    main(sys.argv)
