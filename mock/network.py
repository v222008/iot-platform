"""
WS2812 LED WiFi Enabled Controller for ESP8266
MIT license
(C) Konstantin Belyalov 2017-2018
"""

STA_IF = 1
network_phy_mode = 3


def phy_mode(mode=None):
    if mode:
        network_phy_mode = mode
    return network_phy_mode


class WLAN():
    def __init__(self, type):
        self.type = type

    def isconnected(self):
        return True

    def active(self, state=None):
        if state is None:
            return True

    def connect(sefl, ssid, passwd):
        pass

    def status(self):
        return 1

    def config(self, param):
        if param == 'mac':
            return b'\xb4u\x0e\x88\xed\xe4'

    def ifconfig(self):
        return ('1.1.1.10', '255.255.255.0', '1.1.1.1', '8.8.8.8')

    def scan(self):
        return [(b'HOME-A722', b'\xb4u\x0e\x88\xed\xe4', 1, -94, 4, 0),
                (b'xfinitywifi', b'x\xf2\x9e^\xfd\xba', 1, -75, 0, 0),
                (b'SBG658027', b' \x10z\x87E\x99', 1, -93, 3, 0),
                (b'sybil', b'\x90\x94\xe4\xae\xfa\x08', 3, -85, 4, 0),
                (b'homenet', b'\x84a\xa0!00', 3, -84, 4, 0),
                (b'kaltak_2.4', b'\xc0%\xe9\xff\xc7\xe8', 6, -95, 3, 0),
                (b'xfinitywifi', b'"\x86\x8c*\x8bV', 6, -80, 0, 0),
                (b'SneakerHead25', b'x\xf2\x9e^\xfd\xb8', 1, -77, 4, 0),
                (b'ATT7dzS43g', b'\xf8\x18\x97\xb1\x80\x8e', 10, -80, 3, 0),
                (b'xfinitywifi', b'T\xbe\xf7\xf7\x04\xca', 11, -97, 0, 0),
                (b'DV Home', b'\x00q\xc2TQ\x80', 11, -87, 4, 0),
                (b'xfinitywifi', b'\x00q\xc2TQ\x82', 11, -85, 0, 0),
                (b'Alex2018', b'`3K\xe8g\xf7', 11, -68, 3, 0),
                (b'Birb', b'\xa0\x04`\xc5\x9b\xc9', 11, -90, 3, 0)]
