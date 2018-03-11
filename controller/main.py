#!/usr/bin/env micropython
"""
RGB / RGBW LED WiFi Enabled Controller for ESP8266 (ESP32?)
Supported devices:
 - WS2812(b)

MIT license
(C) Konstantin Belyalov 2017-2018
"""

import tinyweb
import machine
import http
import config
import setup
from utils.wifi import WifiConfig
from utils.config import Config


# Config parts
wifi_config = WifiConfig()
mqtt_config = config.MQTT()
http_config = config.HTTP()
misc_config = config.Misc()

# Deterimine run / device type
if machine.unique_id() == b'__unix__':
    emulator = True
    # Emulate ws2812 device
    from ledstrip.ws2812 import LedStrip
    led_strip = LedStrip(machine.Pin(4))
    device_name = 'Emulator For Neopixel Controller'
else:
    emulator = False
    # Test for ws2812 like devices
    test_pin = machine.Pin(4, machine.Pin.IN)
    if test_pin.value() == 1:
        from ledstrip.ws2812 import LedStrip
        led_strip = LedStrip(machine.Pin(4))
        device_name = 'Neopixel LED Strip Controller'
    else:
        print('Unknown device')

# Joined config
all_config = Config([('wifi', wifi_config),
                     ('led', led_strip),
                     ('mqtt', mqtt_config),
                     ('http', http_config),
                     ('misc', misc_config)])

# Create Web Server / device routes
web = tinyweb.server.webserver()


@web.route('/')
def page_index(req, resp):
    """Index page - basically redirector to setup / dashboard"""
    if emulator:
        if misc_config.configured():
            yield from resp.redirect('/ui/dashboard.html')
        else:
            yield from resp.redirect('/ui/setup.html')
    else:
        if misc_config.configured():
            yield from resp.redirect('/dashboard')
        else:
            yield from resp.redirect('/setup')


@web.route('/setup')
def page_setup(req, resp):
    """Setup page. Send everything packed and gzipped at once."""
    yield from resp.send_file('setup_all.html.gz', content_encoding='gzip',
                                                   content_type='text/html')


@web.route('/dashboard')
def page_dashboard(req, resp):
    """Dashboard page. The same idea as for setup page"""
    yield from resp.send_file('dashboard_all.html.gz', content_encoding='gzip',
                                                       content_type='text/html')

# Emulator routes
@web.route('/ui/<fn>')
@web.route('/ui/css/<fn>')
@web.route('/ui/js/<fn>')
@web.route('/ui/js/vendor/<fn>')
def page_emulator(req, resp, fn):
    """Convenient routes when running through 'emulator', e.g. development."""
    yield from resp.send_file('..' + req.path.decode(), max_age=0)


def start():
    """Main function - entry point"""
    print("Starting LED Controller...")

    # Set device name
    all_config.update({'misc': {'device': device_name}})

    # Add RestAPI resources
    web.add_resource(http.LedStrip(led_strip), '/v1/ledstrip/on')
    web.add_resource(http.LedStripTest(led_strip), '/v1/ledstrip/test')
    web.add_resource(all_config, '/v1/config')
    web.add_resource(wifi_config, '/v1/wifi/scan')

    # Set up setup button task
    setup.start(misc_config)

    # Run HTTP Server on 80 port for real devices.
    # Otherwiese use 8081 port
    if not emulator:
        web.run(host='0.0.0.0', port=80)
    else:
        web.run(host='0.0.0.0', port=8081)


if __name__ == '__main__':
    start()
