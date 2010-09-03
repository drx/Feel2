from editor import Pane as BasePane, Canvas as BaseCanvas, Editor as BaseEditor, LevelSelector as BaseLevelSelector
from compression import nemesis, star
from PyQt4 import QtGui, QtCore

import struct  # for Data

class Data(str):
    #def __new__(cls, value, *args, **kwargs):
    #    return str.__new__(cls, value)
#
    #def __init__(self, value):

    def byte(self, addr):
        return struct.unpack('>B', str(self)[addr])[0]

    def word(self, addr):
        return struct.unpack('>H', self[addr:addr+2])[0]

    def dword(self, addr):
        return struct.unpack('>I', self[addr:addr+4])[0]

    def __getitem__(self, key):
        if type(key) == slice:
            return Data(str.__getitem__(key))
        else:
            return self.byte(key)


class Project(object):
    pass


class ROM(Project):
    def __init__(self):
        self.loaded = False

    def load(self, filename):
        f = open(filename, "rb")
        self.data = Data(f.read())
        self.loaded = True

    @staticmethod
    def palette_md_to_rgb(md_palette):
        palette = []
        for i in xrange(len(md_palette)/2):
            md_color = Data(md_palette).word(i*2)
            r, g, b = (md_color&0xe), (md_color&0xe0)>>4, (md_color&0xe00) >> 8
            rgb_color = 0xff000000 + (r << 20) + (g << 12) + (b << 4)
            palette.append(rgb_color)
        return palette

    class UnrecognizedROM(Exception):
        pass


class RistarROM(ROM):
    pointers = {
        'jp': {
            'palettes': 0x11c1b8,
            'treasure_palette_main': 0xf00c,
            'treasure_palettes_level': 0xf02c,
            'mappings_256': 0x163716,
            'mappings_16': 0x11c764,
            'tiles': 0x129270,
            'objects': 0x5e4,
            'foreground': 0x188492,
            'background': 0,
            'flora_hack': 0x129320,
            'level_collisions': 0x188baa,
            'collision_array': 0x1e97a,
        },
    }
    levels = {
        0x00: "00: Flora (1-1)",
        0x01: "01: Flora (1-2)",
        0x02: "02: Flora (1-3)",
        0x03: "03: Undertow (2-1)",
        0x04: "04: Undertow (2-2)",
        0x05: "05: Undertow (2-3)",
        0x06: "06: Scorch (3-1)",
        0x07: "07: Scorch (3-2)",
        0x08: "08: Scorch (3-3)",
        0x09: "09: Sonata (4-1)",
        0x0a: "0a: Sonata (4-2)",
        0x0b: "0b: Sonata (4-3)",
        0x0c: "0c: Freon (5-1)",
        0x0d: "0d: Freon (5-2)",
        0x0e: "0e: Freon (5-3)",
        0x0f: "0f: Automaton (6-1)",
        0x10: "10: Automaton (6-2)",
        0x11: "11: Automaton (6-3)",
        0x12: "12: Castle Greedy (7-1)",
        0x13: "13: Castle Greedy (7-2)",
        0x14: "14: Castle Greedy (7-3)",
        0x24: "24: Treasure level (1-1)",
        0x25: "25: Treasure level (1-2)",
        0x26: "26: Treasure level (2-1)",
        0x27: "27: Treasure level (2-2)",
        0x28: "28: Treasure level (3-1)",
        0x29: "29: Treasure level (3-2)",
        0x2a: "2a: Treasure level (4-1)",
        0x2b: "2b: Treasure level (4-2)",
        0x2c: "2c: Treasure level (5-1)",
        0x2d: "2d: Treasure level (5-2)",
        0x2e: "2e: Treasure level (6-1)",
        0x2f: "2f: Treasure level (6-2)",
    }

    def load(self, filename):
        super(RistarROM, self).load(filename)

        self.serial = self.data[0x183:0x18a]
        self.date = self.data[0x11d:0x120]
        if self.serial == 'G-4126 ':
            self.rom_version = 'jp'
        elif self.serial == 'MK-1555' and self.date == 'AUG':
            self.rom_version = 'us_aug'
        elif self.serial == 'MK-1555' and self.date == 'SEP':
            self.rom_version = 'us_sep'
        else:
            raise self.UnrecognizedROM()

    def load_level(self, level_id):
        pointers = self.pointers[self.rom_version]
        level = {}
        
        if level_id >= 0x24:
            tileset_id = 0x15
            objectset_id = level_id+4
            collisionset_id = 0x29
        else:
            tileset_id = level_id
            objectset_id = level_id
            collisionset_id = level_id

        tiles_address = self.data.dword(pointers['tiles']+tileset_id*4)
        tile_data = self.data[tiles_address:]
        if tileset_id in (0, 1):
            flora_hack = star.decompress(self.data[pointers['flora_hack']:])
            level['tiles'] = flora_hack + star.decompress(tile_data)
            if tileset_id == 0:
                level['tiles'] = '\0'*0x40+level['tiles'] 
        elif tileset_id == 0x15:
            level['tiles'] = star.decompress(tile_data)
        else:
            level['tiles'] = nemesis.decompress(tile_data)

        mappings_256_address = self.data.dword(pointers['mappings_256']+level_id*4)
        level['mappings_256'] = Data(star.decompress(self.data[mappings_256_address:]))

        mappings_16_address = self.data.dword(pointers['mappings_16']+tileset_id*8)
        level['mappings_16'] = Data(star.decompress(self.data[mappings_16_address:]))

        objects_address = pointers['objects'] + self.data.word(pointers['objects']+objectset_id*2) + 2
        level['objects'] = star.decompress(self.data[objects_address:])

        collisions_address = pointers['level_collisions'] + self.data.word(pointers['level_collisions']+objectset_id*2)
        level['collisions'] = star.decompress(self.data[collisions_address:])

        level['collision_array'] = self.data[pointers['collision_array']:pointers['collision_array']+0x3c0]

        if level_id < 0x15:
            palette_address = pointers['palettes'] + self.data.word(pointers['palettes']+level_id*2)
            level['palette'] = self.data[palette_address:palette_address+0x80]
        else:
            palette_address = pointers['treasure_palettes_level'] + 0x20*(level_id-0x24)
            level['palette'] = self.data[palette_address:palette_address+0x40] + '\0'*0x20 + self.data[pointers['treasure_palette']:pointers['treasure_palette']+0x20]

        level['palette'] = RistarROM.palette_md_to_rgb(level['palette'])

        address = self.data.dword(pointers['foreground']+level_id*4)
        x, y = self.data[address]+1, self.data[address+1]+1
        address += 2
       
        layout = []
        for cur_y in xrange(y):
            layout_line = []
            for cur_x in xrange(x):
                layout_line.append(self.data[address])
                address += 1
            layout.append(layout_line)

        level['foreground'] = {'x': x, 'y': y, 'layout': layout}


        '''Build 16x16 blocks'''
        blocks_16 = []
        for i in xrange(len(level['mappings_16'])/8):
            block = QtGui.QImage(16, 16, QtGui.QImage.Format_ARGB32)
            for x in range(2):
                for y in range(2):
                    flags, tile_id = divmod(level['mappings_16'].word(i*8+y*4+x*2), 0x800)
                    flip_x, flip_y = flags & 0x1, flags & 0x2
                    palette_line = (flags & 0xc) >> 2

                    tile_data = level['tiles'][tile_id*0x20:(tile_id+1)*0x20]
                    tile_i = 0
                    for tile_byte in tile_data:
                        tile_y, tile_x = divmod(tile_i, 8)
                        tile_byte = ord(tile_byte)
                        for k in (0, 1):
                            tyle_byte, palette_cell = divmod(tile_byte, 0x10)
                            color = level['palette'][palette_line*0x10+palette_cell]
                            set_x, set_y = tile_x+k, tile_y
                            if flip_x:
                                set_x = 7-set_x
                            if flip_y:
                                set_y = 7-set_y
                            block.setPixel(x*8+set_x, y*8+set_y, color)
                        tile_i += 2

            blocks_16.append(block)
        level['blocks_16'] = blocks_16

        '''Build 256x256 blocks'''
        blocks_256 = []
        for i in xrange(len(level['mappings_256'])/0x200):
            block = QtGui.QImage(256, 256, QtGui.QImage.Format_ARGB32)
            painter = QtGui.QPainter(block)
            for x in range(16):
                for y in range(16):
                    flags, block_16_id = divmod(level['mappings_256'].word(i*0x200+y*0x20+x*2), 0x200)
                    flip_x, flip_y = bool(flags & 0x2), bool(flags & 0x4)
                    try:
                        painter.drawImage(x*16, y*16, level['blocks_16'][block_16_id].mirrored(horizontal = flip_x, vertical = flip_y))
                    except IndexError:
                        pass

            blocks_256.append(block)
        level['blocks'] = blocks_256

        return level


class Canvas(BaseCanvas):
    def updateImage(self):
        super(Canvas, self).updateImage()
        from PyQt4 import QtGui, QtCore
        if not self.parent().level_loaded:
            return

        foreground = self.parent().current_level['foreground']
        blocks = self.parent().current_level['blocks']

        self.max_camera = QtCore.QPoint(256*foreground['x'], 256*foreground['y'])
        self.old_camera = QtCore.QPoint(self.camera)
        self.camera += self.delta/self.zoom
        if self.camera.x() < 0:
            self.camera.setX(0)
        if self.camera.y() < 0:
            self.camera.setY(0)
        if self.camera.x() + self.width()/self.zoom > self.max_camera.x():
            self.camera.setX(self.max_camera.x()-self.width())
        if self.camera.y() + self.height()/self.zoom > self.max_camera.y():
            self.camera.setY(self.max_camera.y()-self.height())
        
        self.setMouseTracking(True)
        painter = QtGui.QPainter(self.image)

        x_start = (self.camera.x() >> 8)-1
        x_end = x_start + (int(self.width()/self.zoom) >> 8)+3
        y_start = (self.camera.y() >> 8)-1
        y_end = y_start + (int(self.height()/self.zoom) >> 8)+3

        
        if (self.camera.x()>>8) != (self.old_camera.x()>>8) or (self.camera.y()>>8) != (self.old_camera.y()>>8) or self.level_image.isNull():
            self.reload = True

        if self.reload:
            self.reload = False
            self.level_image = QtGui.QImage((x_end-x_start)*256, (y_end-y_start)*256, QtGui.QImage.Format_ARGB32)
            level_painter = QtGui.QPainter(self.level_image)
            level_painter.fillRect(self.level_image.rect(), QtCore.Qt.black)
            for y in range(y_start, y_end):
                for x in range(x_start, x_end):
                    try:
                        block_id = foreground['layout'][y][x]
                    except IndexError:
                        pass
                    if block_id:
                        try:
                            level_painter.drawImage((x-x_start)*256, (y-y_start)*256, blocks[block_id-1])
                        except IndexError:
                            pass

        source_rect = self.level_image.rect()
        source_rect.setX((self.camera.x()&0xff)+256)
        source_rect.setWidth(self.width()/self.zoom)
        source_rect.setY((self.camera.y()&0xff)+256)
        source_rect.setHeight(self.height()/self.zoom)
        painter.drawImage(self.rect(), self.level_image, source_rect)


    def mouseMoveEvent(self, event):
        from PyQt4 import QtGui, QtCore
        #self.move_timer = QtCore.QTimer.singleShot(200, self.startMoving)
        self.updateMouse(event)
        #QtGui.QToolTip.showText(event.globalPos(), '{0}x{1}'.format(event.x(), event.y()), self, QtCore.QRect(event.pos(), QtCore.QPoint(1,1)))

    def mousePressEvent(self, event):
        self.pressed = True
        self.updateMouse(event)

    def mouseReleaseEvent(self, event):
        self.pressed = False
        self.updateMouse(event)

    def leaveEvent(self, event):
        self.delta.setX(0)
        self.delta.setY(0)

    def wheelEvent(self, event):
        steps = event.delta() / (8*15)
        if event.orientation() == QtCore.Qt.Vertical:
            self.zoom += (0.1*steps)*self.zoom
            self.reload = True

    def updateMouse(self, event):
        def speed(distance):
            speed = (50-distance)/10
            if self.pressed:
                speed *= 3
            return speed

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


    def startMoving(self):
        #self.delta.setX(12)
        #self.delta.setY(2)

        '''
        x = 10
        y = 10
        i = 0
        for color in self.parent().rom.level['palette']:
            painter.setBrush(QtGui.QBrush(QtGui.QColor(color)))
            painter.drawRect(x, y, 30, 30)
            x += 30
            i += 1
            if i % 16 == 0:
                x = 10
                y += 30
        x = 10
        y = 150
        i = 0
        for block in self.parent().rom.level['blocks_16']:
            painter.drawImage(x, y, block)
            x += 16
            i += 1
            if i % 32 == 0:
                x = 10
                y += 16
        painter.drawText(self.rect(), QtCore.Qt.AlignCenter, "Welcome to Feel2")

        x = 10
        y = 300
        i = 0
        for block in self.parent().rom.level['blocks']:
            painter.drawImage(x, y, block)
            x += 256
            i += 1
            if i % 32 == 0:
                x = 10
                y += 256
        '''

class LoadLevels(QtCore.QThread):
    started = QtCore.pyqtSignal(int)
    progress = QtCore.pyqtSignal(int)
    loaded = QtCore.pyqtSignal(object, object, Project)

    @staticmethod
    def entropy(image):
        import zlib, base64
        buf = QtCore.QBuffer()
        buf.open(QtCore.QBuffer.ReadWrite)
        image.save(buf, 'PNG')
        data = base64.b64decode(buf.buffer().toBase64())
        return len(zlib.compress(data))

    def run(self):
        rom = RistarROM()
        rom.load('./roms/Ristar - The Shooting Star (J) [!].bin')

        self.started.emit(len(rom.levels))

        levels = {}
        thumbnails = {}
        i = 0
        for level_id in rom.levels:
            if level_id > 3:
                break
            try:
                levels[level_id] = rom.load_level(level_id)
            except Exception as e:
                print 'Could not load level {id} ({e})'.format(id=level_id, e=e)

            # select block with biggest entropy for thumbnail
            blocks_entropy = map(self.entropy, levels[level_id]['blocks'])
            thumbnails[level_id] = blocks_entropy.index(max(blocks_entropy))

            i += 1
            self.progress.emit(i)

        self.loaded.emit(levels, thumbnails, rom)


class LevelSelector(BaseLevelSelector):
    def __init__(self, level_names):
        super(LevelSelector, self).__init__()

        self.level_names = level_names
        self.current_thumb = None

        self.setMouseTracking(True)

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update)
        timer.start(1000/30)

    def paintEvent(self, event):
        x = 10
        y = 10
        i = 0
        thumb_size = self.height()-20
        painter = QtGui.QPainter(self)
        painter.fillRect(self.rect(), QtCore.Qt.black)

        for level_id, thumbnail_id in self.editor.thumbnails.items():
            thumbnail = QtGui.QImage(self.editor.levels[level_id]['blocks'][thumbnail_id])

            if self.current_thumb == level_id:
                thumb_border = 0
            else:
                thumb_border = 5
    
                alpha = QtGui.QImage(256, 256, QtGui.QImage.Format_RGB32)
                alpha.fill(0x808080)
                thumbnail.setAlphaChannel(alpha)

            painter.drawImage(QtCore.QRect(x+thumb_border, y+thumb_border, thumb_size-thumb_border*2, thumb_size-thumb_border*2), thumbnail, thumbnail.rect())
            x += thumb_size
            i += 1

    def mouseMoveEvent(self, event):
        self.current_thumb = (event.x()-10)/(self.height()-20)

    def mousePressEvent(self, event):
        if self.current_thumb:
            self.editor.current_level = self.editor.levels[self.current_thumb]
            self.editor.canvas.reload = True


class Pane(BasePane):
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_L:
            self.load_thread = LoadLevels()
            self.load_thread.started.connect(self.started)
            self.load_thread.progress.connect(self.progress)
            self.load_thread.loaded.connect(self.loaded)
            self.load_thread.start(QtCore.QThread.IdlePriority)

    def started(self, steps):
        self.parent().progress.setVisible(True)
        self.parent().progress.setMaximum(steps)

    def progress(self, step):
        self.parent().progress.setValue(step)

    def loaded(self, levels, thumbnails, project):
        self.parent().progress.setVisible(False)
        self.parent().project = project
        self.parent().levels = levels
        self.parent().thumbnails = thumbnails
        self.parent().current_level = levels[0]
        self.parent().level_loaded = True

        self.level_selector = LevelSelector(project.levels)
        self.level_selector.editor = self.parent()

        self.addTab(self.level_selector, 'Levels')

    
class Editor(BaseEditor):
    def __init__(self):
        super(Editor, self).__init__()

        self.level_loaded = False


    def createCanvas(self):
        self.canvas = Canvas()

    def createPane(self):
        self.pane = Pane()
