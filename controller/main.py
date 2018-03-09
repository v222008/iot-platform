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
from ledstrip.ws2812 import LedStrip
import http
import config
from utils.wifi import WifiConfig
from utils.config import Config


# Here will be some code to import proper LED strip handler
led_pin = 4
led_strip = LedStrip(machine.Pin(led_pin))

# Config parts
wifi_config = WifiConfig()
mqtt_config = config.MQTT()
http_config = config.HTTP()
misc_config = config.Misc()

# Joined config
all_config = Config([('wifi', wifi_config),
                     ('led', led_strip),
                     ('mqtt', mqtt_config),
                     ('http', http_config),
                     ('misc', misc_config)])

# Create Web Server
web = tinyweb.server.webserver()


# Index page - redirector to setup / dashboard
@web.route('/')
def page_index(req, resp):
    if misc_config['configured']:
        yield from resp.redirect('/dashboard')
    else:
        yield from resp.redirect('/setup')


@web.route('/setup')
def page_setup(req, resp):
    resp.add_header('Content-Encoding', 'gzip')
    yield from resp.send_file('setup_all.html.gz', content_type='text/html')


@web.route('/dashboard')
def page_dashboard(req, resp):
    resp.add_header('Content-Encoding', 'gzip')
    yield from resp.send_file('dashboard_all.html.gz', content_type='text/html')


def start():
    """Main function - entry point"""
    print("Starting RBG LED Controller...")

    # Add RestAPI resources
    web.add_resource(http.LedStrip(led_strip), '/v1/ledstrip/on')
    web.add_resource(http.LedStripTest(led_strip), '/v1/ledstrip/test')
    web.add_resource(all_config, '/v1/config')
    web.add_resource(wifi_config, '/v1/wifi/scan')

    web.run(host='0.0.0.0', port=8081)


if __name__ == '__main__':
    start()
