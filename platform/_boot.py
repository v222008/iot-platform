"""
MIT license
(C) Micropython team
(C) Konstantin Belyalov 2017-2018
"""
import esp
import gc
import logging
import machine
import uos


SEC_SIZE = const(4096)
META_SECTOR = 160  # 0xa0


class FlashBlockDev:
    """Class to emulate block device to use it as filesystem."""

    def __init__(self, start, size):
        """ start - start sector of FS
            size - size of filesystem in bytes
        """
        self.start = start
        self.size = size
        self.blocks = (self.size // SEC_SIZE)

    def readblocks(self, n, buf):
        esp.flash_read((n + self.start) * SEC_SIZE, buf)

    def writeblocks(self, n, buf):
        esp.flash_erase(n + self.start)
        esp.flash_write((n + self.start) * SEC_SIZE, buf)

    def ioctl(self, op, arg):
        if op == 4:  # BP_IOCTL_SEC_COUNT
            return self.blocks
        if op == 5:  # BP_IOCTL_SEC_SIZE
            return SEC_SIZE


# Set up UART
uos.dupterm(machine.UART(0, 115200), 1)
# Disable OS debug messages
# esp.osdebug(None)

print("\n\nBooting IOT platform....")

# Read FS metadata
meta_off = META_SECTOR * SEC_SIZE
while True:
    # Read FS params
    buf = bytearray(28)  # name / start sector / lenght / flags
    esp.flash_read(meta_off, buf)
    meta_off += 28
    if buf[0] == 0xff:
        # no more entries
        break
    mpoint = bytes(buf[:16]).decode().rstrip()
    fs_start = int.from_bytes(buf[16:20], 'big')
    fs_len = int.from_bytes(buf[20:24], 'big')
    readonly = bool(buf[25])
    print('Mount: "{}" start sec {}, length {}, readonly={}'.format(mpoint, fs_start, fs_len, readonly))
    # Mount filesystem
    flash = FlashBlockDev(fs_start, fs_len)
    uos.mount(flash, mpoint, readonly=readonly)

# Set up garbage collector
gc.threshold((gc.mem_free() + gc.mem_alloc()) // 4)

# .. And collect garbage after base initialization
gc.collect()

# Run device main
log = logging.Logger('BOOT')

try:
    import main
    main.main()
except KeyboardInterrupt:
    # Allow terminate execution by Ctrl+C - REPR will be activated
    pass
except Exception as e:
    log.exc(e, "main.main() unhandled exception, resetting device")
    machine.reset()
