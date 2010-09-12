import struct
from array import array
from compression.exceptions import *

def decompress(compressed):
    pointer = {'value': 0}
    compressed_array = array('B', compressed)

    def get_byte():
        try:
            val = compressed_array[pointer['value']]
        except Exception:
            val = 0
        pointer['value'] += 1
        return val

    def get_word():        
        val = (compressed_array[pointer['value']]<<8) + compressed_array[pointer['value']+1]
        pointer['value'] += 2
        return val

    remaining_bits = {'value': 8}
    input_buffer = {'value': None}
    def get_bits(n):
        if input_buffer['value'] is None:
            input_buffer['value'] = get_byte()
        value = 0
        if n > remaining_bits['value']:
            value = input_buffer['value'] >> (8 - n)
            input_buffer['value'] = get_byte()
            value |= ((input_buffer['value'] & (0xFF << (8 - n + remaining_bits['value']))) >> (8 - n + remaining_bits['value'])) 
            input_buffer['value'] <<= (n - remaining_bits['value'])
            remaining_bits['value'] = 8 - (n - remaining_bits['value'])
        else:
            value = (input_buffer['value'] & (0xFF << (8 - n))) >> (8 - n)
            remaining_bits['value'] -= n
            input_buffer['value'] <<= n
        input_buffer['value'] &= 0xff
        return value

    def get_value():
        addvalue = 0
        for loopcount in xrange(5):
            if ((bitmask >> (4-loopcount))&0x01) != 0:
                addvalue |= get_bits(1) << (0xF - loopcount)
        if packet_length > 8:
            outvalue = get_bits(packet_length - 8) << 8
            outvalue |= get_bits(8)
        else:
            outvalue = get_bits(packet_length)
        outvalue &= (0xffff ^ (0xffff << packet_length))
        outvalue += addvalue
        return outvalue

    processed_bits = 0
    packet_length = 0
    mode = 0
    output_repeatcount = 0
    bits_remaining_postfunc = 0
    bitmask = 0
    input_stream = 0
    incrementing_value = 0
    common_value = 0
    addvalue = 0
    outvalue = 0
    offset = 0
    outoffset = 0
    done = False
    

    output = []
    padding = []

    loopcount = 0

    packet_length = get_byte()
    bitmask = get_byte()
    incrementing_value = get_word()
    common_value = get_word()

    while not done:
        if get_bits(1) == 1:
            mode = get_bits(2)
            if mode <= 2:
                output_repeatcount = get_bits(4)
                outvalue = get_value()
                for i in xrange(output_repeatcount+1):
                    output.append((outvalue>>8)&0xff)
                    output.append(outvalue & 0xff)
                    if mode == 1:
                        outvalue += 1
                    elif mode == 2:
                        outvalue -= 1
            if mode == 3:
                output_repeatcount = get_bits(4)
                if output_repeatcount != 0x0f:
                    for i in xrange(output_repeatcount+1):
                        outvalue = get_value()
                        output.append((outvalue>>8)&0xff)
                        output.append(outvalue & 0xff)                    
                else:
                    done = True
        else:
            if get_bits(1) == 0:
                output_repeatcount = get_bits(4)
                for i in xrange(output_repeatcount+1):
                    output.append((incrementing_value>>8)&0xff)
                    output.append(incrementing_value & 0xff)                    
                    incrementing_value += 1
            else:
                output_repeatcount = get_bits(4)
                for i in xrange(output_repeatcount+1):
                    output.append((common_value>>8)&0xff)
                    output.append(common_value & 0xff)                    

    return ''.join(map(lambda x: struct.pack('>B', x), output))
