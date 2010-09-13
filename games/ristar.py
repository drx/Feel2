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
        BuildSmallBlocks(background='separate'),
        BuildBigBlocks(background='separate', get_flip=lambda flags: (flags & 0x2, flags & 0x4)),
    ]

    editor_options = {
        'block_size': 256,
        'background_mappings': 'separate',
    }

    def get_levels(self):
        pointers = self.pointers[self.rom_version]
        data = self.data
        levels = []
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
                'mappings_big_foreground': StarCompressed(PointerArray(data, pointers['mappings_256_foreground'], level_id)),
                'mappings_big_background': StarCompressed(PointerArray(data, pointers['mappings_256_background'], tileset_id)),
                'mappings_small_foreground': StarCompressed(PointerArray(data, pointers['mappings_16_foreground'], tileset_id, alignment=8)),
                'mappings_small_background': ShiftedBy(StarCompressed(PointerArray(data, pointers['mappings_16_background'], tileset_id, alignment=8)), shift=background_offset, alignment=2),
                'objects': StarCompressed(RelativePointerArray(data, pointers['objects'], objectset_id, shift=2)),
                'level_collisions': StarCompressed(RelativePointerArray(data, pointers['level_collisions'], collisionset_id)),
                'collision_array': DataSlice(data, pointers['collision_array'], 0x3c0),
                'foreground': LevelLayout(PointerArray(data, pointers['layout_foreground'], level_id)),
                'background': LevelLayout(PointerArray(data, pointers['layout_background'], tileset_id)),
                'level_id': level_id
            }

            if level_id < 0x15:
                level['palette'] = MDPalette(RelativePointerArray(data, pointers['palettes'], level_id, length=0x80))
            else:
                # treasure palettes
                level['palette'] = MDPalette(
                    DataSlice(data, pointers['treasure_palettes_level']+0x40*((level_id-0x24)>>1), 0x40)
                     + StaticData('\0'*0x20)
                     + DataSlice(data, pointers['treasure_palette_main'], 0x20)
                    )

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

            levels.append(level)
        return levels

    def load(self):
        super(RistarROM, self).load()

        self.serial = self.data['data'][0x183:0x18a]
        self.date = self.data['data'][0x11d:0x120]
        if self.serial == 'G-4126 ':
            self.rom_version = 'jp'
        elif self.serial == 'MK-1555' and self.date == 'AUG':
            self.rom_version = 'us_aug'
        elif self.serial == 'MK-1555' and self.date == 'SEP':
            self.rom_version = 'us_sep'
        else:
            raise self.UnrecognizedROM()
