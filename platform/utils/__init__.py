"""
Utilities for ESP based devices
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import network
import ubinascii
import sys


def mac_last_digits():
    """Returns last 4 digits of WiFi STA MAC address, e.g.:
    00:11:22:33:44:55 -> "4455"
    """
    return ubinascii.hexlify(network.WLAN(network.STA_IF).config("mac")[-2:])


def is_emulator():
    if sys.platform == 'linux' or sys.platform == 'darwin':
        return True
    return False
