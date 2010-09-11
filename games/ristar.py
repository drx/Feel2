from editor import Pane as BasePane, Canvas as BaseCanvas, Editor as BaseEditor, LevelSelector as BaseLevelSelector
from PyQt4 import QtGui, QtCore
from loaders import *


class RistarROM(ROM):
    pointers = {
        'jp': {
            'palettes': 0x11c1b8,
            'treasure_palette_main': 0xf00c,
            'treasure_palettes_level': 0xf02c,
            'mappings_256_foreground': 0x163716,
            'mappings_256_background': 0x1853b0,
            'mappings_16_foreground': 0x11c764,
            'mappings_16_background': 0x11c814,
            'mappings_16_background_offset': 0x13ada,
            'tiles_foreground': 0x129270,
            'tiles_background': 0x1292c8,
            'objects': 0x5e4,
            'layout_foreground': 0x188492,
            'layout_background': 0x188552,
            'flora_hack': 0x129320,
            'level_collisions': 0x188baa,
            'collision_array': 0x1e97a,
        },
    }
    level_names = {
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

    level_processors = [
        build_blocks_16,
        build_blocks_256,
    ]

    def get_levels(self):
        pointers = self.pointers[self.rom_version]
        data = self.data
        levels = {}
        for level_id in self.level_names:
            if level_id >= 0x24:
                tileset_id = 0x15
                objectset_id = level_id+4
                collisionset_id = 0x29
            else:
                tileset_id = level_id
                objectset_id = level_id
                collisionset_id = level_id
            background_offset = DataArray(data, pointers['mappings_16_background_offset'], tileset_id, alignment=2, length=2).load()
            level = {
                'palette': MDPalette(RelativePointerArray(data, pointers['palettes'], level_id, length=0x80)),
                'mappings_256_foreground': StarCompressed(PointerArray(data, pointers['mappings_256_foreground'], level_id)),
                'mappings_256_background': StarCompressed(PointerArray(data, pointers['mappings_256_background'], level_id)),
                'mappings_16_foreground': StarCompressed(PointerArray(data, pointers['mappings_16_foreground'], tileset_id, alignment=8)),
                'mappings_16_background': ShiftedBy(StarCompressed(PointerArray(data, pointers['mappings_16_background'], tileset_id, alignment=8)), shift=background_offset, alignment=2),
                'objects': StarCompressed(RelativePointerArray(data, pointers['objects'], level_id, shift=2)),
                'level_collisions': StarCompressed(RelativePointerArray(data, pointers['level_collisions'], level_id)),
                'collision_array': DataSlice(data, pointers['collision_array'], 0x3c0),
                'foreground': LevelLayout(PointerArray(data, pointers['layout_foreground'], level_id)),
                'background': LevelLayout(PointerArray(data, pointers['layout_background'], level_id)),
            }

            if tileset_id in (0, 1):
                foreground_tiles = StarCompressed(DataSlice(data, pointers['flora_hack'], 0x10000))
                foreground_tiles += StarCompressed(PointerArray(data, pointers['tiles_foreground'], tileset_id))
                background_tiles = NemesisCompressed(PointerArray(data, pointers['tiles_background'], tileset_id))
                if tileset_id == 0:
                    foreground_tiles = StaticData('\0'*0x40)+foreground_tiles
            elif 1 < tileset_id < 0x15:
                foreground_tiles = NemesisCompressed(PointerArray(data, pointers['tiles_foreground'], tileset_id))
                background_tiles = NemesisCompressed(PointerArray(data, pointers['tiles_background'], tileset_id))
            else:
                foreground_tiles = StarCompressed(PointerArray(data, pointers['tiles_foreground'], tileset_id))
                background_tiles = StarCompressed(PointerArray(data, pointers['tiles_background'], tileset_id))
           
            level['tiles'] = foreground_tiles + background_tiles 

            """
            foreground_tile_data = load(pointer_array('tiles_foreground', tileset_id))
            background_tile_data = load(pointer_array('tiles_background', tileset_id))
            if tileset_id in (0, 1):
                foreground_tiles = star.decompress(load(pointers['flora_hack'])) + star.decompress(foreground_tile_data)
                if tileset_id == 0:
                    foreground_tiles = '\0'*0x40+foreground_tiles
                background_tiles = nemesis.decompress(background_tile_data)
            elif tileset_id == 0x15:
                foreground_tiles = star.decompress(foreground_tile_data)
                background_tiles = star.decompress(background_tile_data)
            else:
                foreground_tiles = nemesis.decompress(foreground_tile_data)
                background_tiles = nemesis.decompress(background_tile_data)
            """

            #level['tiles'] = foreground_tiles.ljust(background_offset*0x20, '\0') + background_tiles

            levels[level_id] = level
        return levels

    def load(self):
        super(RistarROM, self).load()

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

    def old_load_level(self, level_id):
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


        def load(address, length=None):
            if length is None:
                return self.data[address:]
            else:
                return self.data[address:address+length]

        def pointer_array(key, index, alignment=4):
            return self.data.dword(pointers[key]+index*alignment)

        def pointer_relative_array(key, index, alignment=2):
            return pointers[key] + self.data.word(pointers[key]+index*2)

        background_offset = self.data.word(pointers['mappings_16_background_offset']+tileset_id*2)

        foreground_tile_data = load(pointer_array('tiles_foreground', tileset_id))
        background_tile_data = load(pointer_array('tiles_background', tileset_id))
        if tileset_id in (0, 1):
            foreground_tiles = star.decompress(load(pointers['flora_hack'])) + star.decompress(foreground_tile_data)
            if tileset_id == 0:
                foreground_tiles = '\0'*0x40+foreground_tiles
            background_tiles = nemesis.decompress(background_tile_data)
        elif tileset_id == 0x15:
            foreground_tiles = star.decompress(foreground_tile_data)
            background_tiles = star.decompress(background_tile_data)
        else:
            foreground_tiles = nemesis.decompress(foreground_tile_data)
            background_tiles = nemesis.decompress(background_tile_data)

        level['tiles'] = foreground_tiles.ljust(background_offset*0x20, '\0') + background_tiles

        level['mappings_256_foreground'] = Data(star.decompress(load(pointer_array('mappings_256_foreground', level_id))))
        level['mappings_256_background'] = Data(star.decompress(load(pointer_array('mappings_256_background', level_id))))
        level['mappings_16_foreground'] = Data(star.decompress(load(pointer_array('mappings_16_foreground', tileset_id, alignment=8))))
        mappings_16_background = Data(star.decompress(load(pointer_array('mappings_16_background', tileset_id, alignment=8))))
        level['mappings_16_background'] = Data(''.join(map(lambda x: struct.pack('>H',x+background_offset), [mappings_16_background.word(i*2) for i in xrange(len(mappings_16_background)/2)])))
        try:
            level['objects'] = Data(star.decompress(load(pointer_relative_array('objects', objectset_id)+2)))
        except:
            pass
        level['level_collisions'] = Data(star.decompress(load(pointer_relative_array('level_collisions', objectset_id))))
        level['collision_array'] = load(pointers['collision_array'], 0x3c0)

        if level_id < 0x15:
            md_palette = load(pointer_relative_array('palettes', level_id), 0x80)
        else:
            md_palette = load(pointer_array('treasure_palettes_level', level_id-0x24, 0x20)) + '\0'*0x20 + load(pointers['treasure_palette_main'], 0x20)

        level['palette'] = RistarROM.palette_md_to_rgb(md_palette)

        def load_layout(address):
            x, y = self.data[address]+1, self.data[address+1]+1
            address += 2
       
            layout = []
            for cur_y in xrange(y):
                layout_line = []
                for cur_x in xrange(x):
                    layout_line.append(self.data[address])
                    address += 1
                layout.append(layout_line)

            return {'x': x, 'y': y, 'layout': layout}

        level['foreground'] = load_layout(pointer_array('layout_foreground', level_id))
        level['background'] = load_layout(pointer_array('layout_background', level_id))

        '''Build 16x16 blocks'''
        for plane in ('foreground', 'background'):
            blocks_16 = []
            for i in xrange(len(level['mappings_16_'+plane])/8):
                block = QtGui.QImage(16, 16, QtGui.QImage.Format_ARGB32)
                block.fill(0xff000000)
                for x in range(2):
                    for y in range(2):
                        flags, tile_id = divmod(level['mappings_16_'+plane].word(i*8+y*4+x*2), 0x800)
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
            level['blocks_16_'+plane] = blocks_16

        '''Build 256x256 blocks'''
        for plane in ('foreground', 'background'):
            blocks_256 = []
            block = QtGui.QImage(256, 256, QtGui.QImage.Format_ARGB32)
            block.fill(0xff000000)
            blocks_256.append(block)  # empty block
            for i in xrange(len(level['mappings_256_'+plane])/0x200):
                block = QtGui.QImage(256, 256, QtGui.QImage.Format_ARGB32)
                block.fill(0x00000000)
                painter = QtGui.QPainter(block)
                for x in range(16):
                    for y in range(16):
                        flags, block_16_id = divmod(level['mappings_256_'+plane].word(i*0x200+y*0x20+x*2), 0x200)
                        flip_x, flip_y = bool(flags & 0x2), bool(flags & 0x4)
                        try:
                            painter.drawImage(x*16, y*16, level['blocks_16_'+plane][block_16_id].mirrored(horizontal = flip_x, vertical = flip_y))
                        except IndexError:
                            pass

                blocks_256.append(block)
            level['blocks_'+plane] = blocks_256

        return level


