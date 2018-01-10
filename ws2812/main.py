#!/usr/bin/env micropython
"""
WS2812 LED WiFi Enabled Controller for ESP8266
MIT license
(C) Konstantin Belyalov 2017-2018
"""

import network
import ubinascii as binascii
import ujson as json
import tinyweb


config_wifi_fn = 'wifi.json'
config_fn = 'config.json'


class api_test():
    """API to test LED strip connection"""

    def put(self, data):
        print(data)
        return {'message': 'success'}


class api_config():
    """API to manage config"""

    def put(self, data):
        print(data)
        return {'message': 'success'}


class api_wifi():
    """API to manage WiFi connectivity"""

    def __init__(self):
        self.auth_modes = ['open', 'WEP', 'WPA-PSK', 'WPA2-PSK', 'WPA/WPA2-PSK']
        self.statuses = ['Not Connected', 'Connecting', 'Wrong Password',
                         'No AP Found', 'Connection Failed', 'Connected']
        self.modes = ['', '802.11b', '802.11g', '802.11n']
        # Load current settings
        try:
            with open(config_wifi_fn, 'rb') as f:
                self.config = json.load(f)
                print('Loaded WiFi config: {}'.format(self.config))
        except (OSError, ValueError):
            # No config preset, create empty
            print('WiFi config not found / invalid, using default')
            self.config = {'ssid': '', 'password': '', 'mode': '802.11n'}
        # Set WiFi mode
        self.set_wifi_mode(self.config['mode'])
        # Activate WiFi client (station)
        self.iface = network.WLAN(network.STA_IF)
        self.iface.active(True)
        # Connect to AP, if setup done before
        self.connect()

    def save_config(self):
        with open(config_wifi_fn, 'wb') as f:
            f.write(json.dumps(self.config))

    def set_wifi_mode(self, mode):
        """Sets WiFi mode, e.g. 802.11b/g/n"""
        network.phy_mode(self.modes.index(mode))
        self.config['mode'] = mode

    def connect(self):
        # Connect to WiFi AP - if configured
        if self.config['ssid'] != '':
            self.iface.connect(self.config['ssid'], self.config['password'])

    def convert_mac(self, mac):
        """Converts mac address from binary repr to human-readable format"""
        hmac = binascii.hexlify(mac).decode()
        return '-'.join(hmac[i:i + 2] for i in range(0, len(hmac), 2))

    def get(self, data):
        """Get network configuration.
        Optional parameters:
            - scan: Perform AP scan. Returns list of accessible APs ordered by signal.
        """
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(True)
        res = {'ssid': self.config['ssid'],
               'status': self.statuses[sta_if.status()],
               'status_raw': sta_if.status(),
               'connected': sta_if.isconnected(),
               'ifconfig': {},
               'mac': self.convert_mac(sta_if.config('mac')),
               'mode': self.modes[network.phy_mode()],
               }
        ifc_raw = sta_if.ifconfig()
        for idx, it in enumerate(['ip', 'netmask', 'gateway', 'dns']):
            res['ifconfig'][it] = ifc_raw[idx]
        # Scan for WiFi networks, if desired
        if 'scan' in data:
            res['ssids'] = []
            ssids = sta_if.scan()
            # Sort APs by signal strength
            ssids.sort(key=lambda x: -x[3])
            for s in ssids:
                # Convert SNR to user readable value - quality
                asnr = abs(s[3])
                if asnr <= 30:
                    quality = 'Excellent'
                elif asnr in range(31, 62):
                    quality = 'Very Good'
                elif asnr in range(62, 72):
                    quality = 'Good'
                elif asnr in range(72, 87):
                    quality = 'Poor'
                else:
                    quality = 'Unusable'
                it = {'ssid': s[0].decode(),
                      'mac': self.convert_mac(s[1]),
                      'channel': s[2],
                      'snr': s[3],
                      'quality': quality,
                      'auth': self.auth_modes[s[4]],
                      'auth_raw': s[4]}
                res['ssids'].append(it)
        return res

    def post(self, data):
        """Connect to WiFi access point.
        Parameters:
            ssid - name of access point to connect to
            password - leave empty in case of unsecured AP
        """
        if 'ssid' not in data:
            return {'message': 'ssid is required'}, 400
        # Password is not requred for unsecured networks,
        # so add empty if not present.
        if 'password' not in data:
            data['password'] = ''
        # Save config
        self.config['ssid'] = data['ssid']
        self.config['password'] = data['password']
        self.save_config()
        return {'message': 'Connection to {} started'.format(data['ssid'])}

    def put(self, data):
        """Change WiFi mode
        Parameters:
            mode - change WiFi mode. Valid values are ['802.11b', '802.11g', '802.11n']
        """
        if 'mode' not in data:
            return {'message': 'mode is required'}, 400
        if data['mode'] not in self.modes:
            return {'message': 'Unknow mode. Valid values are {}'.format(self.modes[1:])}, 400
        self.set_wifi_mode(data['mode'])
        self.save_config()
        return {'message': 'changed to {}'.format(data['mode'])}


# Web Server
web = tinyweb.server.webserver()


# Index page - basically archive of all files :)
@web.route('/')
def index(req, resp):
    resp.add_header('Content-Encoding', 'gzip')
    yield from resp.send_file('index_all.html.gz', content_type='text/html')


# --- main starts here ---

# Add RestAPI resources
web.add_resource(api_test, '/v1/test')
web.add_resource(api_config, '/v1/config')
web.add_resource(api_wifi, '/v1/wifi')

web.run(host='0.0.0.0', port=8081)
