"""
Mock classes / functions for ESP based devices
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import utime as time


STA_IF = 1
AP_IF = 2

AUTH_WPA_WPA2_PSK = 11

network_phy_mode = 3


def phy_mode(mode=None):
    global network_phy_mode
    if mode:
        network_phy_mode = mode
    return network_phy_mode


class WLAN():
    def __init__(self, type):
        self.type = type
        self._status = 0
        self.state = False
        self.connected = False
        self.icfg = ('127.0.0.1', '255.255.255.0', '127.0.0.1', '8.8.8.8')

    def isconnected(self):
        return self.connected

    def active(self, state=None):
        if state is not None:
            if not state:
                self.connected = False
                self._status = 0
            self.state = state
        return self.state

    def connect(self, ssid, passwd):
        self.connected = True
        self._status = 5

    def status(self):
        return self._status

    def config(self, param=None, essid=None, authmode=None, password=None):
        if param == 'mac':
            return b'\xb4u\x0e\x88\xed\xe4'

    def ifconfig(self, config=None):
        if config:
            self.icfg = config
            return
        if self.connected:
            return self.ifcg
        else:
            return ('', '', '', '')

    def scan(self):
        time.sleep(1)
        return [(b'HOME-A722', b'\xb4u\x0e\x88\xed\xe4', 1, -94, 4, 0),
                (b'xfinitywifi', b'x\xf2\x9e^\xfd\xba', 1, -75, 0, 0),
                (b'SBG658027', b' \x10z\x87E\x99', 1, -93, 3, 0),
                (b'sybil', b'\x90\x94\xe4\xae\xfa\x08', 3, -85, 4, 0),
                (b'homenet', b'\x84a\xa0!00', 3, -84, 4, 0),
                (b'kaltak_2.4', b'\xc0%\xe9\xff\xc7\xe8', 6, -95, 3, 0),
                (b'SneakerHead25', b'x\xf2\x9e^\xfd\xb8', 1, -77, 4, 0),
                (b'ATT7dzS43g', b'\xf8\x18\x97\xb1\x80\x8e', 10, -80, 3, 0),
                (b'xfinitywifi', b'T\xbe\xf7\xf7\x04\xca', 11, -97, 0, 0),
                (b'DV Home', b'\x00q\xc2TQ\x80', 11, -87, 4, 0),
                (b'iot1982', b'\x00q\xc2TQ\x82', 11, -44, 0, 0),
                (b'Alex2018', b'`3K\xe8g\xf7', 11, -68, 3, 0),
                (b'Birb', b'\xa0\x04`\xc5\x9b\xc9', 11, -90, 3, 0)]
