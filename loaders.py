from PyQt4 import QtGui, QtCore
import struct
from array import array
from compression import nemesis, star, enigma, kosinski
from cache import cache


class Loader(object):
    def load(self):
        abstract

    def save(self):
        abstract

    def __add__(self, other):
        return LoaderList([self, other])

    def save_args(self, *args):
        self.args = args

    @property
    def signature(self):
        signature = self.__class__.__name__
        try:
            args = ', '.join(map(repr, self.args))
        except AttributeError:
            args = ''
        try:
            sub_signature = self.subloader.signature
            args = ', '+args if args else ''
            return '{sig}({sub_sig}{args})'.format(sig=signature, sub_sig=sub_signature, args=args)
        except AttributeError:
            return '{sig}({args})'.format(sig=signature, args=args)


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
        self.changed = False
        return self.data

    def save(self):
        print 'Not implemented'

    @property
    def data(self):
        import operator
        return reduce(operator.add, map(lambda x: x.data, self.loader_list))

    @property
    def signature(self):
        return ' + '.join(map(lambda x: x.signature, self.loader_list))


class StaticData(Loader):
    def __init__(self, data):
        self.data = data

    def load(self):
        self.changed = False
    
    def save(self):
        pass


class Compressed(Loader):
    def __init__(self, subloader):
        self.subloader = subloader

    def load(self):
        cache_key = ('compressed', self.signature)
        if cache_key in cache:
            self.data = cache[cache_key]
        else:    
            compressed = self.subloader.load()
            decompressed = self.decompress(compressed)
            self.data = Data(decompressed)
            cache[cache_key] = self.data
    
        self.changed = False

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


class EnigmaCompressed(Compressed):
    @staticmethod
    def decompress(compressed):
        return enigma.decompress(compressed)

    @staticmethod
    def compress(decompressed):
        print "Not implemented"


class KosinskiCompressed(Compressed):
    @staticmethod
    def decompress(compressed):
        return kosinski.decompress(compressed)

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
        self.changed = False
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
                try:
                    layout_line.append(data[address])
                    address += 1
                except IndexError:
                    layout_line.append(0)
            layout.append(layout_line)

        self.data = {'x': x, 'y': y, 'layout': layout}
        self.changed = False
        return self.data

    def save(self):
        saved_data = ''
        saved_data += chr(self.data['x']-1) + chr(self.data['y']-1)
        for layout_line in self.data['layout']:
            for layout_cell in layout_line:
                saved_data += chr(layout_cell)
        self.subloader.data = saved_data
        self.subloader.changed = True
        self.subloader.save()


class DataArray(Loader):
    def __init__(self, rom, base_address, index, length=None, alignment=2):
        self.rom = rom
        self.base_address = base_address
        self.index = index
        self.length = length
        self.alignment = alignment
        self.shift = 0
        self.end = None if length is None else self.address+length
        self.save_args(base_address, index, length, alignment)

    def load(self):
        self.data = self.rom['data'][self.address:self.end].get(self.alignment, 0)
        self.changed = False
        return self.data

    def save(self):
        self.rom['data'][self.address:self.end] = Data.from_(self.alignment, self.data)

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
        self.save_args(base_address, index, length, alignment, shift)

    def load(self):
        self.data = self.rom['data'][self.address:self.end]
        self.changed = False
        return self.data

    def save(self):
        self.rom['data'][self.address:self.end] = self.data

    @property
    def address(self):
        return self.base_address + self.rom['data'].word(self.base_address+self.index*self.alignment) + self.shift



class PointerArray(Loader):
    def __init__(self, rom, base_address, index, length=None, alignment=4):
        self.rom = rom
        self.base_address = base_address
        self.index = index
        self.length = length
        self.alignment = alignment
        self.end = None if length is None else self.address+length
        self.save_args(base_address, index, length, alignment)

    def load(self):
        self.data = self.rom['data'][self.address:self.end]
        self.changed = False
        return self.data

    def save(self):
        self.rom['data'] = Data(self.rom['data']).splice(self.address, self.end, self.data)

    @property
    def address(self):
        return self.rom['data'].dword(self.base_address + self.index*self.alignment)


class DataSlice(Loader):
    def __init__(self, rom, address, length):
        self.rom = rom
        self.address = address
        self.length = length
        self.save_args(address, length)

    def load(self):
        self.data = self.rom['data'][self.address:self.address+self.length]
        self.changed = False
        return self.data

    def save(self):
        self.rom['data'][self.address:self.address+self.length] = self.data


class ShiftedBy(Loader):
    def __init__(self, subloader, shift, alignment):
        self.subloader = subloader
        self.shift = shift
        self.typecode = {1: 'B', 2: 'H', 4: 'I'}[alignment]
        self.save_args(shift, alignment)

    def load(self):
        input_data = self.subloader.load()
        from array import array
        a = array(self.typecode, input_data)
        a.byteswap()
        a = array(self.typecode, map(lambda x: x+self.shift, a))
        a.byteswap()
        self.data = Data(a.tostring())
        self.changed = False
        return self.data

    def save(self):
        raise Exception('This is broken.')
        self.subloader.data = Data(array(self.typecode, map(lambda x: x-self.shift, array(self.typecode, self.data))).tostring())
        self.subloader.save()


class File(Loader):
    def __init__(self, filename):
        import os.path
        self.filename = os.path.join(current_path, filename)
        self.save_args(self.filename)

    def load(self):
        f = open(self.filename, "rb")
        self.data = Data(f.read())
        f.close()
        return self.data

    def save(self):
        f = open(self.filename, "wb")
        f.write(self.data)
        f.close()        


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

class ROM(Project):
    def __init__(self, filename):
        super(ROM, self).__init__()
        self.filename = filename

    def load(self):
        f = open(self.filename, "rb")
        self.data = {'data': Data(f.read())}
        f.close()

    def save(self):
        f = open(self.filename, "wb")
        f.write(self.data['data'])
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

    def splice(self, i, j, data):
        '''self[i:j] = data, except immutable'''
        new_data = Data(self[:i] + data + self[i+len(data):])
        return new_data

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


class LevelProcessor(object):
    pass


class BuildSmallBlocks(LevelProcessor):
    def __init__(self, block_size=16, background='shared'):
        self.block_size = block_size
        self.background = background
        if background == 'shared':
            self.planes = ({'mappings_small': 'mappings_small', 'blocks_small': 'blocks_small', 'blocks_small_data': 'blocks_small_data', 'dependencies': 'dependencies_small'},)
        else:
            self.planes = (
                {'mappings_small': 'mappings_small_foreground', 'blocks_small': 'blocks_small_foreground', 'blocks_small_data': 'blocks_small_data_foreground', 'dependencies': 'dependencies_small_foreground'},
                {'mappings_small': 'mappings_small_background', 'blocks_small': 'blocks_small_background', 'blocks_small_data': 'blocks_small_data_background', 'dependencies': 'dependencies_small_background'},
                )

    def process(self, level):
        '''Build 16x16 blocks'''
           
        for plane in self.planes:
            # Building 16x16 blocks is very expensive. 
            # See if they're in the cache.
            from cache import cache
            dependencies = (plane['mappings_small'], 'tiles', 'palette')
            dependencies = tuple(map(lambda x: level[x].signature, dependencies))
            level[plane['dependencies']] = dependencies
            if (plane['blocks_small_data'], dependencies) in cache:
                blocks_small_data = cache[(plane['blocks_small_data'], dependencies)]

            else:
                blocks_small_data = []
                for i in xrange(len(level[plane['mappings_small']].data)/8):
                    block = QtGui.QImage(self.block_size, self.block_size, QtGui.QImage.Format_ARGB32)
                    block.fill(0xff000000)
                    block_bits = array('B', '\0'*block.numBytes())
                    block_bytes_per_line = block.bytesPerLine()
                    for x in xrange(2):
                        for y in xrange(2):
                            flags, tile_id = divmod(level[plane['mappings_small']].data.word(i*8+y*4+x*2), 0x800)
                            flip_x, flip_y = flags & 0x1, flags & 0x2
                            palette_line = (flags & 0xc) >> 2

                            tile_data = level['tiles'].data[tile_id*0x20:(tile_id+1)*0x20]
                            tile_i = 0
                            for tile_byte in tile_data:
                                if isinstance(tile_byte, str):
                                    tile_byte = ord(tile_byte)
                                tile_y, tile_x = divmod(tile_i, 8)
                                for k in xrange(2):
                                    tyle_byte, palette_cell = divmod(tile_byte, 0x10)
                                    color = level['palette'].data[palette_line*0x10+palette_cell]
                                    set_x, set_y = tile_x+k, tile_y
                                    if flip_x:
                                        set_x = 7-set_x
                                    if flip_y:
                                        set_y = 7-set_y
                                    pixel_addr = (y*8+set_y)*block_bytes_per_line+(x*8+set_x)*4
                                    block_bits[pixel_addr+3] = (color >> 24) & 0xff
                                    block_bits[pixel_addr+2] = (color >> 16) & 0xff
                                    block_bits[pixel_addr+1] = (color >> 8) & 0xff
                                    block_bits[pixel_addr] = color & 0xff
                                tile_i += 2

                    blocks_small_data.append(block_bits.tostring())

                cache[(plane['blocks_small_data'], dependencies)] = blocks_small_data

            blocks_small = []
            for block in blocks_small_data:
                blocks_small.append(QtGui.QImage(block, self.block_size, self.block_size, QtGui.QImage.Format_ARGB32))
            level[plane['blocks_small_data']] = blocks_small_data
            level[plane['blocks_small']] = blocks_small
        return level


class BuildBigBlocks(LevelProcessor):
    def __init__(self, block_size=256, background='shared', get_flip=None):
        self.block_size = block_size
        self.background = background
        if get_flip is None:
            self.get_flip = lambda flags: (flags & 0x4, flags & 0x1)
        else:
            self.get_flip = get_flip

        if background == 'shared':
            self.planes = ({'blocks_small': 'blocks_small', 'mappings_big': 'mappings_big', 'blocks': 'blocks', 'dependencies_small': 'dependencies_small'},)
        else:
            self.planes = (
                {'blocks_small': 'blocks_small_foreground', 'mappings_big': 'mappings_big_foreground', 'blocks': 'blocks_foreground', 'dependencies_small': 'dependencies_small_foreground'},
                {'blocks_small': 'blocks_small_background', 'mappings_big': 'mappings_big_background', 'blocks': 'blocks_background', 'dependencies_small': 'dependencies_small_background'},
                )

    def process(self, level):
        '''Build 256x256 blocks'''
        for plane in self.planes:
            from cache import cache
            dependencies = (plane['mappings_big'],)
            dependencies = tuple(map(lambda x: level[x].signature, dependencies))
            dependencies += level[plane['dependencies_small']]
            blocks_big = []
            block = QtGui.QImage(self.block_size, self.block_size, QtGui.QImage.Format_ARGB32)
            block.fill(0xff000000)
            blocks_big.append(block)  # empty block
            if (plane['blocks'], dependencies) in cache:
                blocks_data = cache[(plane['blocks'], dependencies)]
                for block in blocks_data:
                    blocks_big.append(QtGui.QImage(block, self.block_size, self.block_size, QtGui.QImage.Format_ARGB32))
            else:
                blocks_big_data = []
                for i in xrange(len(level[plane['mappings_big']].data)/(self.block_size*2)):
                    block = QtGui.QImage(self.block_size, self.block_size, QtGui.QImage.Format_ARGB32)
                    block.fill(0x00000000)
                    painter = QtGui.QPainter(block)
                    for x in range(self.block_size/16):
                        for y in range(self.block_size/16):
                            flags, block_small_id = divmod(level[plane['mappings_big']].data.word(i*self.block_size*2+y*0x20+x*2), self.block_size*2)
                            flip_x, flip_y = self.get_flip(flags)
                            try:
                                painter.drawImage(x*16, y*16, level[plane['blocks_small']][block_small_id].mirrored(horizontal = flip_x, vertical = flip_y))
                            except IndexError:
                                pass

                    blocks_big.append(block)
                    blocks_big_data.append(block.bits().asstring(block.numBytes()))

                cache[(plane['blocks'], dependencies)] = blocks_big_data
            level[plane['blocks']] = blocks_big
        return level
