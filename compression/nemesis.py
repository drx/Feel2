import struct
from compression.exceptions import *

def decompress(compressed):
    pointer = {'value': 0}

    def get_next_byte():
        val = compressed[pointer['value']]
        pointer['value'] += 1
        return val

    def get_next_word():        
        val = struct.unpack('>H', compressed[pointer['value']:pointer['value']+2])[0]
        pointer['value'] += 2
        return val

    rtiles = get_next_word()
    alt_out, rtiles = divmod(rtiles, 0x8000)
    tiles = []    
    
    '''Stage 1'''
    buf = '\x01'*0x200
    in_val = get_next_byte()
    while in_val != 0xFF:
        if in_val > 0x7F:
            out_val, in_val = in_val, get_next_byte()

        num_times = 0x08 - (in_val & 0x0F);
        in_val = ((in_val & 0xF0) >> 4) + ((in_val & 0x0F) << 4)
        out_val = (out_val & 0x0F) + (in_val << 4)
        offset = get_next_byte() * (1<<(num_times+1))
        if (offset >= 0x200):
            raise DecompressionError("Wrong offset: ({offset})".format(offset=offset))

        num_times = 1<<num_times
        for i in xrange(num_times):
            buf = buf[:offset] + struct.pack('>H', out_val) + buf[offset+2:]
            offset += 2

        in_val = get_next_byte()

    '''Stage 2'''
    rom_mod = 0x10;
    alt_out_val = 0;
    num_times = 0;
    rom_val = get_next_word()

    for i in xrange(rtiles):
        for j in xrange(8):  # lines
            out_val = 0
            for k in xrange(8):  # nibbles
                num_times -= 1
                if num_times == -1:
                    mode_val = rom_val / (1 <<(rom_mod - 8))
                    if mode_val & 0x00FF >= 0xFC:
                        if rom_mod < 0x0F:
                            rom_mod += 8
                            rom_val = (rom_val << 8) + get_next_byte()
                            rom_val &= 0xFFFF
                        rom_mod -= 0x0D
                        num_times = ((rom_val / (1<<rom_mod))&0x70) >> 4
                        next_out = (rom_val / (1<<rom_mod))&0x0F
                    else:
                        bufferoffset = (mode_val & 0xFF) * 2
                        rom_mod -= ord(buf[bufferoffset])
                        num_times = (ord(buf[bufferoffset+1]) & 0xF0) >> 4
                        next_out = ord(buf[bufferoffset+1]) & 0x0F
                    if rom_mod < 9:
                        rom_mod += 8
                        rom_val = (rom_val << 8) + get_next_byte()
                        rom_val &= 0xFFFF
                out_val = (out_val << 4) + next_out
                out_val &= 0xFFFFFFFF

            if alt_out:
                alt_out_val = alt_out_val ^ out_val
                tiles.append(alt_out_val)
            else:
                tiles.append(out_val)

    return ''.join(map(lambda x: struct.pack('>I', x), tiles))
