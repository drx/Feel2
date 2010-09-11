import struct
from array import array
from compression.exceptions import *

def decompress(compressed):
    input_ptr = {'value': 0}
    bit_count = {'value': 8}
    compressed_array = array('B', compressed)
    uncompressed = []

    def get_byte():
        val = compressed_array[input_ptr['value']]
        input_ptr['value'] += 1
        return val

    def get_word():        
        val = (compressed_array[input_ptr['value']]<<8) + compressed_array[input_ptr['value']+1]
        input_ptr['value'] += 2
        return val

    def get_ctrl_bit(ctrl_byte):
        bit_count['value'] -= 1
        if bit_count['value'] < 0:
            ctrl_byte = get_byte()
            bit_count['value'] = 7
        return ctrl_byte & 0x80, (ctrl_byte << 1)&0xff

    ctrl_byte = get_byte()

    while True:
        ctrl_bit, ctrl_byte = get_ctrl_bit(ctrl_byte)

        if ctrl_bit:
            uncompressed.append(get_byte())
            continue

        ctrl_bit, ctrl_byte = get_ctrl_bit(ctrl_byte)

        if ctrl_bit:
            b1 = get_byte()
            b2 = get_byte()
            repeat_offset = b2
            repeat_offset <<= 8
            repeat_offset += b1
            raw_copy_count = repeat_offset
            if not raw_copy_count:
                break
            repeat_offset >>= 3
            raw_copy_count &= 7

            repeat_offset = 0x2000-repeat_offset

            if raw_copy_count:
                raw_copy_count += 1
            else:
                raw_copy_count = (raw_copy_count&0xff00) | get_byte()
        else:
            raw_copy_count = 0

            ctrl_bit, ctrl_byte = get_ctrl_bit(ctrl_byte)
            if ctrl_bit:
                raw_copy_count += 1

            raw_copy_count *= 2
            ctrl_bit, ctrl_byte = get_ctrl_bit(ctrl_byte)
            if ctrl_bit:
                raw_copy_count += 1
           
            repeat_offset = 0x100 - get_byte()
            raw_copy_count += 1

        output_repeat_addr = len(uncompressed)-repeat_offset
        for i in xrange(raw_copy_count+1):
            try:
                byte = uncompressed[output_repeat_addr]
            except IndexError:
                byte = 0
            uncompressed.append(byte)
            output_repeat_addr += 1
        
    return ''.join(map(lambda x: struct.pack('>B', x), uncompressed))
