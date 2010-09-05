from PyQt4 import QtGui, QtCore


class Pane(QtGui.QTabWidget):
    def __init__(self, parent=None):
        super(Pane, self).__init__(parent)

        #self.addTab(QtGui.QWidget(), "Level info")
        #self.addTab(QtGui.QWidget(), "Tiles")
        #self.addTab(QtGui.QWidget(), "Objects")

        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Maximum)

    def sizeHint(self):
        return QtCore.QSize(160, 160)


class Canvas(QtGui.QWidget):
    def __init__(self, parent=None):
        super(Canvas, self).__init__()

        self.image = QtGui.QImage()
        self.level_image = QtGui.QImage()
        self.camera = QtCore.QPoint(0, 0)
        self.delta = QtCore.QPoint(0, 0)
        self.pressed = False
        self.zoom = 1.0

        self.reload = False

        self.move_timer = QtCore.QTimer()
        self.move_timer.setSingleShot(True)

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
        painter.setPen(QtCore.Qt.NoPen)
        gradient = QtGui.QLinearGradient()
        gradient.setColorAt(0.0, QtGui.QColor(255, 255, 255, 0))
        if self.pressed:
            gradient.setColorAt(1.0, QtGui.QColor(255, 255, 255, 96))
        else:
            gradient.setColorAt(1.0, QtGui.QColor(255, 255, 255, 64))

        if self.delta.x() > 0:
            rect = QtCore.QRect(self.width()-50, 0, 50, self.height())
            gradient.setStart(self.width()-50, 0)
            gradient.setFinalStop(self.width(), 0)
            painter.setBrush(QtGui.QBrush(gradient))
            painter.drawRect(rect)

        if self.delta.x() < 0:
            rect = QtCore.QRect(0, 0, 50, self.height())
            gradient.setStart(50, 0)
            gradient.setFinalStop(0, 0)
            painter.setBrush(QtGui.QBrush(gradient))
            painter.drawRect(rect)

        if self.delta.y() > 0:
            rect = QtCore.QRect(0, self.height()-50, self.width(), 50)
            gradient.setStart(0, self.height()-50)
            gradient.setFinalStop(0, self.height())
            painter.setBrush(QtGui.QBrush(gradient))
            painter.drawRect(rect)

        if self.delta.y() < 0:
            rect = QtCore.QRect(0, 0, self.width(), 50)
            gradient.setStart(0, 50)
            gradient.setFinalStop(0, 0)
            painter.setBrush(QtGui.QBrush(gradient))
            painter.drawRect(rect)

    def updateImage(self):
        self.image = QtGui.QImage(self.width(), self.height(), QtGui.QImage.Format_ARGB32)
        self.image.fill(QtGui.QColor(0, 0, 0).rgb())
        

class LevelSelector(QtGui.QWidget):
    pass


class ProgressBar(QtGui.QProgressBar):
    pass


class Editor(QtGui.QWidget):
    def __init__(self):
        super(Editor, self).__init__()
        self.resize(800, 600)
        self.setWindowTitle("Feel2")

        self.createCanvas()
        self.createPane()
        self.progress_bar = ProgressBar()
        self.progress_bar.setVisible(False)
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.addWidget(self.pane)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

    def createCanvas(self):
        self.canvas = Canvas()

    def createPane(self):
        self.pane = Pane()

    def setLevels(self, levels):
        pass
