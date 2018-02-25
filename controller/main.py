#!/usr/bin/env micropython
"""
RGB / RGBW LED WiFi Enabled Controller for ESP8266 (ESP32?)
Supporter device:
 - WS2812(b)

MIT license
(C) Konstantin Belyalov 2017-2018
"""

import tinyweb
import machine
import esp
import time
from utils.wifi import WifiConfig
from utils.config import Config


led_pin = 4
# Neopixel color map: R -> 1, G -> 0, B -> 2, W = 3
color_order = (1, 0, 2, 3)
led_types = {'rgb': 3,
             'rgbw': 4,
             'rgbww': 4,
             'rgbnw': 4}


class LedTest():
    """API to test LED strip connection"""

    def put(self, data):
        # Validate input
        if 'type' not in data or 'cnt' not in data:
            return {'message': '"type" and "cnt" are required'}, 400
        tp = data['type']
        cnt = int(data['cnt'])
        if tp not in led_types:
            msg = 'Led type "{}" is unknown. Valid values: "{}"'.format(tp, led_types)
            return {'message': msg}, 400
        if cnt > 150 or cnt < 1:
            return {'message': 'invalid value for "cnt". Valid range is 1-150'}, 400
        pin = machine.Pin(led_pin)
        pin.init(pin.OUT)
        bpp = led_types[tp]
        for c in range(bpp):
            buf = bytearray(bpp * cnt)
            for i in range(cnt):
                buf[i * bpp + color_order[c]] = 255
                esp.neopixel_write(pin, buf, True)
                time.sleep_ms(10)
            time.sleep_ms(400)
        buf = bytearray(bpp * cnt)
        esp.neopixel_write(pin, buf, True)
        return {'message': 'success'}


class LedConfig():
    """ESP WiFi configuration for ESP8266 / ESP32"""

    def __init__(self):
        self.config = {'cnt': '', 'type': 'rgb'}

    def config_get(self):
        return self.config

    def config_replace(self, cfg):
        self.config = cfg

    def config_merge(self, cfg):
        self.config.update(cfg)


class MQTTConfig():
    """ESP WiFi configuration for ESP8266 / ESP32"""

    def __init__(self):
        self.config = {'host': '', 'username': '', 'password': '', 'client_id': '',
                       'status_topic': '', 'control_topic': '', 'enabled': False}

    def config_get(self):
        return self.config

    def config_replace(self, cfg):
        self.config = cfg

    def config_merge(self, cfg):
        self.config.update(cfg)


class HTTPConfig():
    """ESP WiFi configuration for ESP8266 / ESP32"""

    def __init__(self):
        self.config = {'username': '', 'password': '', 'enabled': False}

    def config_get(self):
        return self.config

    def config_replace(self, cfg):
        self.config = cfg

    def config_merge(self, cfg):
        self.config.update(cfg)


# Web Server
web = tinyweb.server.webserver()


# Index page - basically archive of all files :)
@web.route('/')
def index(req, resp):
    resp.add_header('Content-Encoding', 'gzip')
    yield from resp.send_file('index_all.html.gz', content_type='text/html')


# --- main starts here ---
wconfig = WifiConfig()
lconfig = LedConfig()
mconfig = MQTTConfig()
hconfig = HTTPConfig()
config = Config([('wifi', wconfig),
                 ('led', lconfig),
                 ('mqtt', mconfig),
                 ('http', hconfig)])

# Add RestAPI resources
web.add_resource(LedTest, '/v1/test')
web.add_resource(config, '/v1/config')
web.add_resource(wconfig, '/v1/wifi/scan')

web.run(host='0.0.0.0', port=8081)
