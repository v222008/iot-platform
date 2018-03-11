"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import network
import uasyncio as asyncio
import ubinascii


# Setup button pressed indicator
button_pressed = False
# Async event loop
event_loop = asyncio.get_event_loop()
# AP
ap_if = network.WLAN(network.AP_IF)


def __handler(misc_config):
    print("setup handler")
    # Turn on AP if device went into unconfigured mode
    # or user has pressed setup button
    if not misc_config.configured() and not ap_if.active():
        essid = b'LedController-%s' % ubinascii.hexlify(ap_if.config("mac")[-2:])
        ap_if.active(True)
        ap_if.config(essid=essid, authmode=network.AUTH_WPA_WPA2_PSK, password=b'ledledled')
        print('WiFi AP enabled')
    # Turn off AP when device has been successfully configured
    if misc_config.configured() and ap_if.active():
        ap_if.active(False)
        print('WiFi AP disabled')
    # Schedule next run in 1 sec
    event_loop.call_later(1, __handler, misc_config)


def start(misc_config):
    event_loop.call_soon(__handler, misc_config)
