#!/usr/bin/env micropython
"""
Utilities for ESP based devices
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import gc
import logging
import network
import ubinascii as binascii


wifi_modes = ['', '802.11b', '802.11g', '802.11n']
auth_modes = ['Open', 'WEP', 'WPA-PSK', 'WPA2-PSK', 'WPA/WPA2-PSK']
statuses = ['Not Connected', 'Connecting', 'Wrong Password',
            'No AP Found', 'Connection Failed', 'Connected']


log = logging.Logger('WIFI')


def rssi_to_quality(rssi):
    """ Converts RSSI to user readable format - percentage"""
    if rssi <= -100:
        quality = 0
    elif rssi >= -50:
        quality = 100
    else:
        quality = 2 * (rssi + 100)
    return quality


def convert_mac(mac):
    """Converts mac address from binary to human-readable format"""
    hmac = binascii.hexlify(mac).decode()
    return '-'.join(hmac[i:i + 2] for i in range(0, len(hmac), 2))


def validate_wifi_mode(name, value):
    if value not in wifi_modes[1:]:
        raise ValueError('Invalid WiFi mode')


class WifiSetup():
    """ESP WiFi configuration for ESP8266 / ESP32"""

    def __init__(self, config):
        """ESP WiFi Configuration
        Arguments:
            config - SimpleConfig instance
        """
        # Register config parameters
        self.cfg = config
        self.cfg.add_param('wifi_ssid', '',
                           callback=self.ssid_changed,
                           group='wifi',
                           )
        self.cfg.add_param('wifi_password', '',
                           group='wifi',
                           )
        self.cfg.add_param('wifi_mode', '802.11n',
                           validator=validate_wifi_mode,
                           callback=self.mode_changed,
                           )
        self.sta_if = network.WLAN(network.STA_IF)

    def ssid_changed(self):
        """Config callback when either ssid or password changed"""
        if self.cfg.wifi_ssid == '':
            self.sta_if.active(False)
        else:
            self.sta_if.active(True)
            self.sta_if.connect(self.cfg.wifi_ssid, self.cfg.wifi_password)

    def mode_changed(self):
        """Config callback for wifi mode change"""
        network.phy_mode(wifi_modes.index(self.cfg.wifi_mode))

    async def get(self, data):
        # Base params
        if self.sta_if.active():
            status = statuses[self.sta_if.status()]
        else:
            status = statuses[0]
        yield '{{"connected":{:d},"mac":"{}","mode":"{}","status":"{}"'.format(
            self.sta_if.isconnected(),
            convert_mac(self.sta_if.config('mac')),
            wifi_modes[network.phy_mode()],
            status)
        ifc_raw = self.sta_if.ifconfig()
        for idx, it in enumerate(['ip', 'netmask', 'gateway', 'dns']):
            yield ',"{}":"{}"'.format(it, ifc_raw[idx])
        # If scan for networks desired
        if 'scan' in data:
            # Scan for WiFi networks. This is ~2 seconds blocking call.
            last_state = self.sta_if.active()
            self.sta_if.active(True)
            # Scan for WiFi networks
            yield ',"access-points":['
            ssids = self.sta_if.scan()
            # scan returns: (ssid, bssid, channel, rssi, authmode, hidden)
            # Sort APs by rssi, output up to N
            ssids.sort(key=lambda x: -x[3])
            cnt = 0
            gc.collect()
            for s in ssids:
                # Convert SNR to user readable value - quality
                quality = rssi_to_quality(s[3])
                if cnt > 0:
                    yield ',{'
                else:
                    yield '{'
                yield '"ssid":"{}","mac":"{}","channel":{},"quality":{},"auth":"{}"'.format(
                      s[0].decode(), convert_mac(s[1]), s[2], quality, auth_modes[s[4]])
                yield '}'
                cnt += 1
                gc.collect()
            yield ']'
            # If interface was disabled before - turn it off
            self.sta_if.active(last_state)
        yield '}'
