#!/usr/bin/env micropython
"""
Unittests for WiFi config util
MIT license
(C) Konstantin Belyalov 2017-2018
"""

import unittest
import ujson as json
from platform.utils.config import SimpleConfig
from platform.utils.wifi import WifiSetup


# Tests


class WiFiTests(unittest.TestCase):
    def setUp(self):
        self.cfg = SimpleConfig(autosave=False)
        self.wifi = WifiSetup(self.cfg)

    def testDefaultConfig(self):
        """Sanity test - just to make sure that default config OK"""
        res = json.loads(self.wifi.get())
        exp = {"connected": 0,
               "mac": "b4-75-0e-88-ed-e4",
               "mode": "802.11n",
               "status": "Not Connected",
               "ip": "", "netmask": "", "gateway": "", "dns": ""}
        self.assertEqual(res, exp)

    def testChangeSSID(self):
        """WiFi must be activated when changing ssid."""
        # Set SSID
        self.cfg.update({'wifi_ssid': 'junk', 'wifi_password': 'junk'})
        # Ensure that wifi got connected
        res = json.loads(self.wifi.get())
        exp = {"connected": 1,
               "mac": "b4-75-0e-88-ed-e4",
               "mode": "802.11n",
               "status": "Connected",
               "ip": "127.0.0.1",
               "netmask": "255.255.255.0",
               "gateway": "127.0.0.1",
               "dns": "8.8.8.8"}
        self.assertEqual(res, exp)
        # ... and lets disconnect from AP
        self.cfg.update({'wifi_ssid': '', 'wifi_password': ''})
        res = json.loads(self.wifi.get())
        exp = {"connected": 0,
               "mac": "b4-75-0e-88-ed-e4",
               "mode": "802.11n",
               "status": "Not Connected",
               "ip": "", "netmask": "", "gateway": "", "dns": ""}

    def testChangeWiFiMode(self):
        # Change WiFi mode
        self.cfg.update({'wifi_mode': '802.11b'})
        # Ensure that wifi got connected
        res = json.loads(self.wifi.get())
        exp = {"connected": 0,
               "mac": "b4-75-0e-88-ed-e4",
               "mode": "802.11b",
               "status": "Not Connected",
               "ip": "", "netmask": "", "gateway": "", "dns": ""}
        self.assertEqual(res, exp)

    def testInvalidWiFiMode(self):
        with self.assertRaises(ValueError):
            self.cfg.update({'wifi_mode': 'junk'})
        with self.assertRaises(ValueError):
            self.cfg.update({'wifi_mode': ''})

    def testScanAPs(self):
        """Scan APs test - mostly to test output format and activate/deactivate interface"""
        ap0 = {'ssid': 'iot1982',
               'auth_raw': 0,
               'channel': 11,
               'rssi': -44,
               'mac': '00-71-c2-54-51-82',
               'quality': 100,
               'auth': 'Open'}
        res = json.loads(self.wifi.get(data={'scan': 1, 'max_entries': 2}))
        self.assertEqual(len(res['access-points']), 2)
        self.assertEqual(res['access-points'][0], ap0)


if __name__ == '__main__':
    unittest.main()
