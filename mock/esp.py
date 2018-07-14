"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""

BLOCKS = 10
BLOCK_SIZE = 4096

fmemory = bytearray(BLOCKS * BLOCK_SIZE)


def neopixel_write(*args):
    print('neopixel_write')


def flash_size():
    return BLOCKS * BLOCK_SIZE


def flash_erase(block):
    fmemory[block * BLOCK_SIZE:(block + 1) * BLOCK_SIZE] = b'\xff' * BLOCK_SIZE


def flash_write(off, buf):
    if isinstance(buf, str):
        fmemory[off:off + len(buf)] = buf.encode()
    else:
        fmemory[off:off + len(buf)] = buf


def flash_read(off, buf):
    buf[0:len(buf)] = fmemory[off:off + len(buf)]
