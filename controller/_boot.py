"""
MIT license
(C) Micropython team
(C) Konstantin Belyalov 2017-2018
"""
import gc
import uos
import esp
import network
import ubinascii


class CtrlFlashBlockDev:
    """Class to emulate block device to use it as filesystem for RBG controller."""
    SEC_SIZE = 4096
    RESERVED_SECS = 1
    START_SEC = esp.flash_user_start() // SEC_SIZE + RESERVED_SECS

    def __init__(self):
        # 20K at the flash end is reserved for SDK params storage
        size = esp.flash_size() - (20 * 1024)
        self.blocks = size // self.SEC_SIZE - self.START_SEC

    def readblocks(self, n, buf):
        esp.flash_read((n + self.START_SEC) * self.SEC_SIZE, buf)

    def writeblocks(self, n, buf):
        esp.flash_erase(n + self.START_SEC)
        esp.flash_write((n + self.START_SEC) * self.SEC_SIZE, buf)

    def ioctl(self, op, arg):
        if op == 4:  # BP_IOCTL_SEC_COUNT
            return self.blocks
        if op == 5:  # BP_IOCTL_SEC_SIZE
            return self.SEC_SIZE


print("Booting RGB controller...")

# Init flash
# 20K at the flash end is reserved for SDK params storage
flash = CtrlFlashBlockDev()
uos.mount(flash, '/')

# Set up garbage collector
gc.threshold((gc.mem_free() + gc.mem_alloc()) // 4)
# .. And collect garbage after main initialization
gc.collect()

# Setup AP parameters
ap_if = network.WLAN(network.AP_IF)
essid = b'LedController-%s' % ubinascii.hexlify(ap_if.config("mac")[-2:])
ap_if.active(True)
ap_if.config(essid=essid, authmode=network.AUTH_WPA_WPA2_PSK, password=b'ledledled')
ap_if.ifconfig(('192.168.168.1', '255.255.255.0', '192.168.168.1', '192.168.168.1'))
ap_if.active(False)

# Run RGB controller
import main

main.start()
