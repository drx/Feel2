import struct
from array import array
from compression.exceptions import *

def decompress(compressed):
    pointer = {'value': 0}
    compressed_array = array('B', compressed)

    output = [] 

    def get_byte():
        val = compressed_array[pointer['value']]
        pointer['value'] += 1
        return val

    def get_word():        
        val = (compressed_array[pointer['value']+1]<<8) + compressed_array[pointer['value']]
        pointer['value'] += 2
        return val

    bit_field = get_word()
    bfp = 0

    while True:
        bit = bool(bit_field & (1 << bfp))
        bfp += 1
        if bfp >= 16:
            bit_field = get_word()
            bfp = 0
        if bit:
            output.append(get_byte())
        else:
            bit = bool(bit_field & (1 << bfp))
            bfp += 1
            if bfp >= 16:
                bit_field = get_word()
                bfp = 0
            if bit:
                low = get_byte()
                high = get_byte()
                count = high & 0x7
                if count == 0:
                    count = get_byte()
                    if count == 0:
                        break
                    if count == 1:
                        continue
                else:
                    count += 1
                offset = ((0xf8 & high) << 5) | low
                offset = 0x2000 - offset
            else:
                bit = bool(bit_field & (1 << bfp))
                bfp += 1
                low = 1 if bit else 0
                if bfp >= 16:
                    bit_field = get_word()
                    bfp = 0
                bit = bool(bit_field & (1 << bfp))
                bfp += 1
                high = 1 if bit else 0
                if bfp >= 16:
                    bit_field = get_word()
                    bfp = 0

                count = low*2 + high + 1
                offset = 0x100 - get_byte()

            for i in xrange(count+1):
                output.append(output[-offset])
             

    return ''.join(map(lambda x: struct.pack('>B', x), output))
