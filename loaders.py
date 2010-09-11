from PyQt4 import QtGui, QtCore
import struct

from compression import nemesis, star


class Loader(object):
    def load(self):
        abstract

    def save(self):
        abstract

    def __add__(self, other):
        return LoaderList([self, other])


class LoaderList(Loader):
    def __init__(self, loader_list):
        self.loader_list = loader_list

    def __add__(self, other):
        if isinstance(other, LoaderList):
            self.loader_list += other.loader_list
            return self
        elif isinstance(other, Loader):
            self.loader_list += [other]
            return self
        else:
            raise NotImplementedError 

    def load(self):
        for loader in self.loader_list:
            loader.load()
        return self.data

    def save(self):
        print 'Not implemented'

    @property
    def data(self):
        import operator
        return reduce(operator.add, map(lambda x: x.data, self.loader_list))


class StaticData(Loader):
    def __init__(self, data):
        self.data = data

    def load(self):
        pass
    
    def save(self):
        pass


class Compressed(Loader):
    def __init__(self, subloader):
        self.subloader = subloader

    def load(self):
        compressed = self.subloader.load()
        decompressed = self.decompress(compressed)
        self.data = Data(decompressed)
        return self.data

    def save(self):
        compressed = self.compress(self.data)
        self.subloader.data = compressed
        self.subloader.save()


class StarCompressed(Compressed):
    @staticmethod
    def decompress(compressed):
        return star.decompress(compressed)

    @staticmethod
    def compress(decompressed):
        print "Not implemented"


class NemesisCompressed(Compressed):
    @staticmethod
    def decompress(compressed):
        return nemesis.decompress(compressed)

    @staticmethod
    def compress(decompressed):
        print "Not implemented"


class MDPalette(Loader):
    def __init__(self, subloader):
        self.subloader = subloader

    def load(self):
        md_palette = self.subloader.load()
        palette = []
        for i in xrange(len(md_palette)/2):
            md_color = Data(md_palette).word(i*2)
            r, g, b = (md_color&0xe), (md_color&0xe0)>>4, (md_color&0xe00) >> 8
            rgb_color = (r << 20) + (g << 12) + (b << 4)
            if i % 16 != 0:
                rgb_color += 0xff000000
            palette.append(rgb_color)
        self.data = palette
        return palette

    def save(self):
        print 'Not implemented'


class LevelLayout(Loader):
    def __init__(self, subloader):
        self.subloader = subloader

    def load(self):
        data = self.subloader.load()
        address = 0
        x, y = data[address]+1, data[address+1]+1
        address += 2
       
        layout = []
        for cur_y in xrange(y):
            layout_line = []
            for cur_x in xrange(x):
                layout_line.append(data[address])
                address += 1
            layout.append(layout_line)

        self.data = {'x': x, 'y': y, 'layout': layout}
        return self.data

    def save(self):
        print 'Not implemented'


class DataArray(Loader):
    def __init__(self, rom, base_address, index, length=None, alignment=2):
        self.rom = rom
        self.base_address = base_address
        self.index = index
        self.length = length
        self.alignment = alignment
        self.shift = 0
        self.end = None if length is None else self.address+length

    def load(self):
        self.data = self.rom[self.address:self.end].get(self.alignment, 0)
        return self.data

    def save(self):
        self.rom[self.address:self.end] = Data.from_(self.alignment, self.data)

    @property
    def address(self):
        return self.base_address + self.index*self.alignment


class RelativePointerArray(Loader):
    def __init__(self, rom, base_address, index, length=None, alignment=2, shift=0):
        self.rom = rom
        self.base_address = base_address
        self.index = index
        self.length = length
        self.alignment = alignment
        self.shift = 0
        self.end = None if length is None else self.address+length

    def load(self):
        self.data = self.rom[self.address:self.end]
        return self.data

    def save(self):
        self.rom[self.address:self.end] = self.data

    @property
    def address(self):
        return self.base_address + self.rom.word(self.base_address+self.index*self.alignment) + self.shift


class PointerArray(Loader):
    def __init__(self, rom, base_address, index, length=None, alignment=4):
        self.rom = rom
        self.base_address = base_address
        self.index = index
        self.length = length
        self.alignment = alignment
        self.end = None if length is None else self.address+length

    def load(self):
        self.data = self.rom[self.address:self.end]
        return self.data

    def save(self):
        self.rom[self.address:self.end] = self.data

    @property
    def address(self):
        return self.rom.dword(self.base_address + self.index*self.alignment)


class DataSlice(Loader):
    def __init__(self, rom, address, length):
        self.rom = rom
        self.address = address
        self.length = length

    def load(self):
        self.data = self.rom[self.address:self.address+self.length]
        return self.data

    def save(self):
        self.rom[self.address:self.address+self.length] = self.data


class ShiftedBy(Loader):
    def __init__(self, subloader, shift, alignment):
        self.subloader = subloader
        self.shift = shift
        self.typecode = {1: 'B', 2: 'H', 4: 'I'}[alignment]

    def load(self):
        input_data = self.subloader.load()
        from array import array
        a = array(self.typecode, input_data)
        a.byteswap()
        a = array(self.typecode, map(lambda x: x+self.shift, a))
        a.byteswap()
        self.data = Data(a.tostring())
        return self.data

    def save(self):
        raise Exception('This is broken.')
        self.subloader.data = Data(array(self.typecode, map(lambda x: x-self.shift, array(self.typecode, self.data))).tostring())
        self.subloader.save()


class Project(object):
    def load(self):
        pass

    def save(self):
        pass

    @property
    def levels(self):
        try:
            return self._levels
        except AttributeError:
            self._levels = self.get_levels()
            return self._levels

    def load_level(self, level_id):
        for attr in self.levels[level_id]:
            self.levels[level_id][attr].load()


class ROM(Project):
    def load(self):
        #self.filename = open_ROM()
        self.filename = 'roms/Ristar - The Shooting Star (J) [!].bin'
        f = open(self.filename, "rb")
        self.data = Data(f.read())
        f.close()

    def save(self):
        f = open(self.filename, "wb")
        f.write(self.data)
        f.close()        

    class UnrecognizedROM(Exception):
        pass


class Data(str):
    def byte(self, addr):
        return struct.unpack('>B', str(self)[addr])[0]

    def word(self, addr):
        return struct.unpack('>H', self[addr:addr+2])[0]

    def dword(self, addr):
        return struct.unpack('>I', self[addr:addr+4])[0]

    def get(self, alignment, addr):
        if alignment == 1:
            return self.byte(addr)
        elif alignment == 2:
            return self.word(addr)
        elif alignment == 4:
            return self.dword(addr)

    @staticmethod
    def from_byte(data):
        return Data(struct.pack('>B', data))

    @staticmethod
    def from_word(data):
        return Data(struct.pack('>H', data))

    @staticmethod
    def from_dword(data):
        return Data(struct.pack('>I', data))

    @staticmethod
    def from_(alignment, data):
            return {1: Data.from_byte, 2: Data.from_word, 4: Data.from_dword}[alignment](data)

    def __len__(self):
        return len(str(self))

    def __getitem__(self, key):
        if isinstance(key, slice):
            return Data(str.__getitem__(self, key))
        else:
            return self.byte(key)

    def __getslice__(self, i, j):
        return self.__getitem__(slice(i, j))

def build_blocks_16(level):
    '''Build 16x16 blocks'''
    for plane in ('foreground', 'background'):
        blocks_16 = []
        for i in xrange(len(level['mappings_16_'+plane].data)/8):
            block = QtGui.QImage(16, 16, QtGui.QImage.Format_ARGB32)
            block.fill(0xff000000)
            for x in range(2):
                for y in range(2):
                    flags, tile_id = divmod(level['mappings_16_'+plane].data.word(i*8+y*4+x*2), 0x800)
                    flip_x, flip_y = flags & 0x1, flags & 0x2
                    palette_line = (flags & 0xc) >> 2

                    tile_data = level['tiles'].data[tile_id*0x20:(tile_id+1)*0x20]
                    tile_i = 0
                    for tile_byte in tile_data:
                        tile_y, tile_x = divmod(tile_i, 8)
                        for k in (0, 1):
                            tyle_byte, palette_cell = divmod(ord(tile_byte), 0x10)
                            color = level['palette'].data[palette_line*0x10+palette_cell]
                            set_x, set_y = tile_x+k, tile_y
                            if flip_x:
                                set_x = 7-set_x
                            if flip_y:
                                set_y = 7-set_y
                            block.setPixel(x*8+set_x, y*8+set_y, color)
                        tile_i += 2

            blocks_16.append(block)
        level['blocks_16_'+plane] = blocks_16
    return level


def build_blocks_256(level):
    '''Build 256x256 blocks'''
    for plane in ('foreground', 'background'):
        blocks_256 = []
        block = QtGui.QImage(256, 256, QtGui.QImage.Format_ARGB32)
        block.fill(0xff000000)
        blocks_256.append(block)  # empty block
        for i in xrange(len(level['mappings_256_'+plane].data)/0x200):
            block = QtGui.QImage(256, 256, QtGui.QImage.Format_ARGB32)
            block.fill(0x00000000)
            painter = QtGui.QPainter(block)
            for x in range(16):
                for y in range(16):
                    flags, block_16_id = divmod(level['mappings_256_'+plane].data.word(i*0x200+y*0x20+x*2), 0x200)
                    flip_x, flip_y = bool(flags & 0x2), bool(flags & 0x4)
                    try:
                        painter.drawImage(x*16, y*16, level['blocks_16_'+plane][block_16_id].mirrored(horizontal = flip_x, vertical = flip_y))
                    except IndexError:
                        pass

            blocks_256.append(block)
        level['blocks_'+plane] = blocks_256
    return level


def open_ROM():
    settings = QtCore.QSettings("Feel2", "Feel2")
    file_dialog = QtGui.QFileDialog()
    file_dialog.setFileMode(QtGui.QFileDialog.ExistingFile)
    file_dialog.setNameFilter("ROMs (*.*)")
    file_dialog.restoreState(settings.value("openrom/state").toByteArray())
    file_dialog.exec_()
    selected_filename = None
    for filename in file_dialog.selectedFiles():
        selected_filename = filename
    settings.setValue("openrom/state", self.saveState())
    return selected_filename
