from PyQt4 import QtGui, QtCore


class Pane(QtGui.QTabWidget):
    def __init__(self, parent=None):
        super(Pane, self).__init__(parent)

        self.addTab(QtGui.QWidget(), "Level info")
        self.addTab(QtGui.QWidget(), "Tiles")
        self.addTab(QtGui.QWidget(), "Objects")

        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)

    def sizeHint(self):
        return QtCore.QSize(160, 160)


class Canvas(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Canvas, self).__init__()

        self.image = QtGui.QImage()
        self.camera = QtCore.QPoint(0, 0)
        self.delta = QtCore.QPoint(0, 0)

        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000/30)

    def paintEvent(self, event):
        self.updateImage()  # temporary
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtCore.Qt.black)

        if self.image.isNull():
            painter.setPen(QtCore.Qt.white)
            painter.drawText(self.rect(), QtCore.Qt.AlignCenter, "Welcome to Feel2")
            return

        painter.drawImage(self.rect(), self.image)

    def updateImage(self):
        self.image = QtGui.QImage(self.width(), self.height(), QtGui.QImage.Format_ARGB32)
        self.image.fill(QtGui.QColor(0, 0, 0).rgb())
        


class Editor(QtGui.QWidget):
    def __init__(self):
        super(Editor, self).__init__()
        self.resize(800, 600)
        self.setWindowTitle("Feel2")

        self.createCanvas()
        self.createPane()

        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.pane)

        self.setLayout(layout)

    def createCanvas(self):
        self.canvas = Canvas()

    def createPane(self):
        self.pane = Pane()
