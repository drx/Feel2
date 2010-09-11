from PyQt4 import QtGui, QtCore


def image_entropy(image):
    import zlib, base64
    buf = QtCore.QBuffer()
    buf.open(QtCore.QBuffer.ReadWrite)
    image.save(buf, 'PNG')
    data = base64.b64decode(buf.buffer().toBase64())
    return len(zlib.compress(data))


def image_set_alpha(image, alpha_value):
    alpha = QtGui.QImage(image.width(), image.height(), QtGui.QImage.Format_RGB32)
    alpha.fill((alpha_value<<16)+(alpha_value<<8)+alpha_value)
    image.setAlphaChannel(alpha)


class Pane(QtGui.QTabWidget):
    def __init__(self, parent=None):
        super(Pane, self).__init__(parent)

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
        self.mouse_pos = QtCore.QPoint()
        self.pressed = False
        self.zoom = 1.0

        self.reload = False

        self.move_timer = QtCore.QTimer()
        self.move_timer.setSingleShot(True)

        self.setBackgroundRole(QtGui.QPalette.Base)
        self.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000/24)

    def reset(self):
        self.camera.setX(0)
        self.camera.setY(0)

    @property
    def editor(self):
        return self.parent()


    def paintEvent(self, event):
        self.updateImage()
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
        if not self.parent().level_loaded:
            return

        self.image = QtGui.QImage(self.width(), self.height(), QtGui.QImage.Format_ARGB32)
        self.image.fill(QtGui.QColor(0, 0, 0).rgb())

        foreground = self.parent().current_level['foreground'].data
        background = self.parent().current_level['background'].data
        blocks_foreground = self.parent().current_level['blocks_foreground']
        blocks_background = self.parent().current_level['blocks_background']

        self.wrap_background = True
        self.block_size = 256

        self.max_camera = QtCore.QPoint(self.block_size*foreground['x'], self.block_size*foreground['y'])
        self.old_camera = QtCore.QPoint(self.camera)
        self.camera += self.delta/self.zoom
        if self.camera.x() + self.width()/self.zoom > self.max_camera.x():
            self.camera.setX(self.max_camera.x()-self.width()/self.zoom)
        if self.camera.y() + self.height()/self.zoom > self.max_camera.y():
            self.camera.setY(self.max_camera.y()-self.height()/self.zoom)
        if self.camera.x() < 0:
            self.camera.setX(0)
        if self.camera.y() < 0:
            self.camera.setY(0)
        
        self.setMouseTracking(True)
        painter = QtGui.QPainter(self.image)

        x_start = (self.camera.x() >> 8)-1
        x_end = x_start + (int(self.width()/self.zoom) >> 8)+3
        y_start = (self.camera.y() >> 8)-1
        y_end = y_start + (int(self.height()/self.zoom) >> 8)+3

        wrap_background = self.wrap_background
        if self.editor.mode == 'levels':
            draw_foreground = True
            draw_background = True
            plane = None
        elif self.editor.mode == 'foreground':
            draw_foreground = True
            draw_background = False
            plane = foreground
        elif self.editor.mode == 'background':
            draw_foreground = False
            draw_background = True
            wrap_background = False
            plane = background
        
        if (self.camera.x()>>8) != (self.old_camera.x()>>8) or (self.camera.y()>>8) != (self.old_camera.y()>>8) or self.level_image.isNull():
            self.reload = True

        if self.reload:
            self.reload = False
            self.level_image = QtGui.QImage((x_end-x_start)*self.block_size, (y_end-y_start)*self.block_size, QtGui.QImage.Format_ARGB32)
            level_painter = QtGui.QPainter(self.level_image)
            level_painter.fillRect(self.level_image.rect(), QtCore.Qt.black)

            for y in range(y_start, y_end):
                for x in range(x_start, x_end):
                    if draw_background:
                        if wrap_background:
                            background_block_id = background['layout'][y%background['y']][x%background['x']]
                        else:
                            try:
                                background_block_id = background['layout'][y][x]
                            except IndexError:
                                background_block_id = None
                        if background_block_id:
                            level_painter.drawImage((x-x_start)*self.block_size, (y-y_start)*self.block_size, blocks_background[background_block_id])

                    if draw_foreground:
                        try:
                            foreground_block_id = foreground['layout'][y][x]
                        except IndexError:
                            foreground_block_id = None
                        if foreground_block_id:
                            try:
                                level_painter.drawImage((x-x_start)*self.block_size, (y-y_start)*self.block_size, blocks_foreground[foreground_block_id])
                            except IndexError:
                                pass

                    if not self.delta and self.editor.mode in ('background', 'foreground') and self.editor.pane_tab.selected_block is not None and (x,y) == self.mouse_layout_xy() and x < plane['x'] and y < plane['y']:
                        if self.editor.mode == 'foreground':
                            hover_block = QtGui.QImage(blocks_foreground[self.editor.pane_tab.selected_block])
                        elif self.editor.mode == 'background':
                            hover_block = QtGui.QImage(blocks_background[self.editor.pane_tab.selected_block])
                        image_set_alpha(hover_block, 0x80)
                        level_painter.drawImage((x-x_start)*self.block_size, (y-y_start)*self.block_size, hover_block)

        source_rect = self.level_image.rect()
        source_rect.setX((self.camera.x()&0xff)+self.block_size)
        source_rect.setWidth(self.width()/self.zoom)
        source_rect.setY((self.camera.y()&0xff)+self.block_size)
        source_rect.setHeight(self.height()/self.zoom)
        painter.drawImage(self.rect(), self.level_image, source_rect)

    def mouse_layout_xy(self):
        return ((int(self.camera.x()+self.mouse_pos.x()/self.zoom)>>8),(int(self.camera.y()+self.mouse_pos.y()/self.zoom)>>8))

    def resizeEvent(self, event):
        self.reload = True

    def mouseMoveEvent(self, event):
        self.updateMouse(event)

    def mousePressEvent(self, event):
        self.pressed = True
        self.updateMouse(event)
        if not self.delta and self.editor.mode in ('foreground', 'background') and self.editor.pane_tab.selected_block is not None:
            if self.editor.mode == 'foreground':
                plane = self.editor.current_level['foreground'].data
            elif self.editor.mode == 'background':
                plane = self.editor.current_level['background'].data
            x, y = self.mouse_layout_xy()
            if x < plane['x'] and y < plane['y']:
                plane['layout'][y][x] = self.editor.pane_tab.selected_block
                self.reload = True

    def mouseReleaseEvent(self, event):
        self.pressed = False
        self.updateMouse(event)

    def leaveEvent(self, event):
        self.delta.setX(0)
        self.delta.setY(0)
        self.mouse_pos = QtCore.QPoint()

    def wheelEvent(self, event):
        steps = event.delta() / (8*15)
        if event.orientation() == QtCore.Qt.Vertical:
            self.zoomBy(steps)

    def zoomBy(self, steps):
        self.zoom += (0.1*steps)*self.zoom
        if self.zoom < 0.15:
            self.zoom = 0.15
        if self.zoom > 10:
            self.zoom = 10
        self.reload = True

    def updateMouse(self, event):
        def speed(distance):
            speed = (50-distance)/10
            if self.pressed:
                speed *= 3
            return speed

        self.old_mouse_pos = self.mouse_pos
        self.mouse_pos = event.pos()

        if event.x() > self.width()-50:
            self.delta.setX(speed(self.width()-event.x()))
        elif event.x() < 50:
            self.delta.setX(-speed(event.x()))
        else:
            self.delta.setX(0)

        if event.y() > self.height()-50:
            self.delta.setY(speed(self.height()-event.y()))
        elif event.y() < 50:
            self.delta.setY(-speed(event.y()))
        else:
            self.delta.setY(0)

        if not self.delta and ((self.old_mouse_pos/self.zoom+self.camera).x()>>8) != ((self.mouse_pos/self.zoom+self.camera).x()>>8) or ((self.old_mouse_pos/self.zoom+self.camera).y()>>8) != ((self.mouse_pos/self.zoom+self.camera).y()>>8):
            self.reload = True


class BlockSelector(QtGui.QWidget):
    selected = QtCore.pyqtSignal(int)

    def __init__(self, blocks, block_names=None, block_size=256):
        super(BlockSelector, self).__init__()

        self.current_block = None
        self.selected_block = None
        self.block_size = block_size
        self.blocks = blocks
        self.block_names = block_names
        self.delta = 0
        self.pos = 0

        self.setMouseTracking(True)

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_pos)
        timer.start(1000/30)

    @property
    def blocks(self):
        return self._blocks

    @blocks.setter
    def blocks(self, value):
        self._blocks = value
        self.block_list = sorted(value.keys())

    @blocks.deleter
    def blocks(self):
        del self._blocks
        del self.block_list        

    def reset(self):
        self.selected_block = None
        self.pos = 0
        self.update()

    def update_pos(self):
        if not self.delta:
            return
        self.pos += self.delta
        pos_max = len(self.blocks)*(self.height()-20)+10
        if self.pos + self.width() > pos_max:
            self.pos = pos_max-self.width()
        if self.pos < 0:
            self.pos = 0
        self.update()

    def paintEvent(self, event):
        x = 10-self.pos
        y = 10
        i = 0
        thumb_size = self.height()-20
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtCore.Qt.black)

        for block_id in self.block_list:
            block = self.blocks[block_id]
            thumbnail = QtGui.QImage(block) 
            if self.current_block == block_id:
                thumb_margin = 0
            else:
                thumb_margin = 5
                image_set_alpha(thumbnail, 0x80)

            thumb_rect = QtCore.QRect(x+thumb_margin, y+thumb_margin, thumb_size-thumb_margin*2, thumb_size-thumb_margin*2)
            if self.selected_block == block_id:
                painter.setPen(QtCore.Qt.gray)
                border_rect = thumb_rect.adjusted(-1, -1, 1, 1)
                painter.drawRect(border_rect)

            if -thumb_size+thumb_margin*2 < x+thumb_margin < self.width():
                painter.drawImage(thumb_rect, thumbnail, thumbnail.rect())
            x += thumb_size
            i += 1

        if self.current_block is not None and self.block_names is not None and self.current_block in self.block_names:
            painter.setPen(QtCore.Qt.NoPen)
            painter.setBrush(QtGui.QColor(0, 0, 0, 128))
            rect = QtCore.QRect(0, self.height()-40, self.width(), 40)
            painter.drawRect(rect)
            painter.setPen(QtCore.Qt.white)
            painter.setFont(QtGui.QFont("Helvetica", 12))
            painter.drawText(rect, QtCore.Qt.AlignCenter, self.block_names[self.current_block])

    def mouseMoveEvent(self, event):
        try:
            if self.pos+event.x() >= 10:
                self.current_block = self.block_list[(self.pos+event.x()-10)/(self.height()-20)]
            else:
                self.current_block = None
        except IndexError:
            self.current_block = None
        self.update()
        self.updateMouse(event)

    def mousePressEvent(self, event):
        self.pressed = True
        if self.current_block is not None:
            self.selected_block = self.current_block
            self.selected.emit(self.selected_block)
            self.update()
        self.updateMouse(event)

    def mouseReleaseEvent(self, event):
        self.pressed = False
        self.updateMouse(event)

    def leaveEvent(self, event):
        self.delta = 0
        self.current_block = None
        self.update()

    def updateMouse(self, event):
        def speed(distance):
            speed = (50-distance)
            return speed

        if event.x() > self.width()-50:
            self.delta = speed(self.width()-event.x())
        elif event.x() < 50:
            self.delta = -speed(event.x())
        else:
            self.delta = 0


class LevelSelector(BlockSelector):
    def __init__(self, level_names, editor):
        self.editor = editor
        blocks = dict((level_id, self.editor.levels[level_id]['blocks_foreground'][thumbnail_id]) for (level_id, thumbnail_id) in self.editor.thumbnails.items())
        super(LevelSelector, self).__init__(blocks, block_names=level_names)

        self.level_names = level_names


class ProgressBar(QtGui.QProgressBar):
    pass


class ProjectLoader(QtCore.QThread):
    started = QtCore.pyqtSignal(int)
    progress = QtCore.pyqtSignal(int)
    loaded = QtCore.pyqtSignal(object, object, object)

    def __init__(self, project):
        super(ProjectLoader, self).__init__()
        self.project = project

    def run_(self):
        self.project.load()

        self.started.emit(len(self.project.levels))
        self.progress.emit(0)

        levels = {}
        thumbnails = {}
        i = 0
        for level_id in self.project.levels:
            if level_id > 0x204:
                continue
            try:
                self.project.load_level(level_id)
                for level_processor in self.project.level_processors:
                    self.project.levels[level_id] = level_processor(self.project.levels[level_id])
            except str as e:
                print 'Could not load level {id} ({e})'.format(id=level_id, e=e)

            # select block with biggest entropy for thumbnail
            blocks_entropy = map(image_entropy, self.project.levels[level_id]['blocks_foreground'])
            thumbnails[level_id] = blocks_entropy.index(max(blocks_entropy))

            i += 1
            self.progress.emit(i)

        levels = self.project.levels
        self.loaded.emit(levels, thumbnails, self.project)

    def run(self):
        import os
        if 'FEEL2_PROFILE_THREADS' in os.environ:
            import cProfile, pstats
            profiler = cProfile.Profile()
            try:
                return profiler.runcall(self.run_)
            finally:
                profiler.dump_stats(os.environ['FEEL2_PROFILE_THREADS'])
                pstats.Stats(os.environ['FEEL2_PROFILE_THREADS']).sort_stats('time').print_stats()
        else:
            self.run_()


class Editor(QtGui.QWidget):
    def __init__(self):
        super(Editor, self).__init__()
        self.createCanvas()
        self.createPane()
        self.progress_bar = ProgressBar()
        self.progress_bar.setVisible(False)
        layout = QtGui.QVBoxLayout()
        layout.setMargin(0)
        layout.addWidget(self.canvas)
        layout.addWidget(self.pane)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        self.level_loaded = False
        self.show_pane = True

    def createCanvas(self):
        self.canvas = Canvas()

    def createPane(self):
        self.pane = Pane()
        self.pane.currentChanged.connect(self.set_mode)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_L:
            self.load_rom()
        elif event.key() == QtCore.Qt.Key_0:
            self.canvas.zoom = 1.0
            self.canvas.reload = True
        elif event.key() == QtCore.Qt.Key_P and event.modifiers() & QtCore.Qt.ControlModifier:
            self.show_pane = not self.show_pane
            self.pane.setVisible(self.show_pane)
        else:
            event.ignore()
            super(Editor, self).keyPressEvent(event)

    def load_rom(self):
        from games.ristar import RistarROM
        self.project_loader = ProjectLoader(RistarROM())
        self.project_loader.started.connect(self.started)
        self.project_loader.progress.connect(self.progress)
        self.project_loader.loaded.connect(self.loaded)
        self.project_loader.start(QtCore.QThread.IdlePriority)
    

    def started(self, steps):
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(steps)

    def progress(self, step):
        self.progress_bar.setValue(step)

    def loaded(self, levels, thumbnails, project):
        self.progress_bar.setVisible(False)
        self.project = project
        self.levels = levels
        self.thumbnails = thumbnails

        self.level_selector = LevelSelector(project.level_names, editor=self)
        self.level_selector.selected.connect(self.set_level)
        self.foreground_selector = BlockSelector({})
        self.background_selector = BlockSelector({})

        self.modes = {
            0: 'levels',
            1: 'foreground',
            2: 'background',
        }
        self.mode_id = 0
        self.pane.addTab(self.level_selector, 'Levels')
        self.pane.addTab(self.foreground_selector, 'Foreground')
        self.pane.addTab(self.background_selector, 'Background')

    def set_level(self, level_id):
        self.current_level = self.levels[level_id]
        self.canvas.reset()
        self.level_selector.selected_block = level_id
        self.foreground_selector.blocks = dict(enumerate(self.levels[level_id]['blocks_foreground']))
        self.foreground_selector.reset()
        self.background_selector.blocks = dict(enumerate(self.levels[level_id]['blocks_background']))
        self.background_selector.reset()
        self.level_loaded = True
        self.canvas.reload = True

    def set_mode(self, mode_id):
        self.pane_tab = self.pane.currentWidget()
        self.mode_id = mode_id
        self.canvas.reload = True

    @property
    def mode(self):
        return self.modes[self.mode_id]
