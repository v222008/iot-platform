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
RESERVED_SECS = const(1)
START_SEC = esp.flash_user_start() // SEC_SIZE + RESERVED_SECS
BP_IOCTL_SEC_COUNT = const(4)
BP_IOCTL_SEC_SIZE = const(5)


log = logging.Logger('BOOT')


class CtrlFlashBlockDev:
    """Class to emulate block device to use it as filesystem."""

    def __init__(self):
        # 20K at the flash end is reserved for SDK params storage
        size = esp.flash_size() - (20 * 1024)
        self.blocks = size // SEC_SIZE - START_SEC

    def readblocks(self, n, buf):
        esp.flash_read((n + START_SEC) * SEC_SIZE, buf)

    def writeblocks(self, n, buf):
        esp.flash_erase(n + START_SEC)
        esp.flash_write((n + START_SEC) * SEC_SIZE, buf)

    def ioctl(self, op, arg):
        if op == BP_IOCTL_SEC_COUNT:
            return self.blocks
        if op == BP_IOCTL_SEC_SIZE:
            return SEC_SIZE


# Set up UART
uos.dupterm(machine.UART(0, 115200), 1)
# Disable OS debug messages
esp.osdebug(None)

print("\n\nBooting IOT platform....")

# Init filesystem
flash = CtrlFlashBlockDev()
uos.mount(flash, '/')

# Set up garbage collector
gc.threshold((gc.mem_free() + gc.mem_alloc()) // 4)

# .. And collect garbage after base initialization
gc.collect()

# Run device main
try:
    import main
    main.main()
except KeyboardInterrupt:
    # Allow terminate execution by Ctrl+C - REPR will be activated
    pass
except Exception as e:
    log.exc(e, "main.main() unhandled exception, resetting device")
    machine.reset()
