#!/usr/bin/env micropython
"""
RGB / RGBW LED WiFi Enabled Controller for ESP8266 (ESP32?)
Supported devices:
 - WS2812(b)

MIT license
(C) Konstantin Belyalov 2017-2018
"""

import machine
import sys
import tinyweb
import http
import config
import setup
import statusled
import utils
import utils.config
import micropython


# Setup button PIN, if present on device
setup_button = None
status_led_pin = None

# Deterimine run / device type
if sys.platform == 'linux' or sys.platform == 'darwin':
    # Emulatator mode. Emulate neopixel device
    emulator = True
    from ledstrip.neopixel import LedStrip
    led_strip = LedStrip(machine.Pin(4))
    device_name = 'Emulator For Neopixel Controller'
else:
    emulator = False
    # Allocate memory for ISR possible exception
    micropython.alloc_emergency_exception_buf(100)
    # Test for ws2812 like devices
    test_pin = machine.Pin(4, machine.Pin.IN)
    if test_pin.value() == 1:
        # WS2812 LED Controller Device
        from ledstrip.neopixel import LedStrip
        device_name = 'Neopixel LED Strip Controller'
        led_strip = LedStrip(machine.Pin(4))
        setup_button = machine.Pin(5)
        status_led_pin = machine.Pin(10)
    else:
        from ledstrip.neopixel import LedStrip
        device_name = 'Neopixel LED Strip Controller'
        led_strip = LedStrip(machine.Pin(4))
        # device_name = 'Unknown device'

# Configuration
config = utils.Config([config.Misc(device_name),
                       utils.config.Wifi(),
                       config.Mqtt(),
                       config.Http(),
                       ('led', led_strip)])

# Create Web Server / device routes
web = tinyweb.server.webserver()


@web.route('/')
def page_index(req, resp):
    """Index page - basically redirector to setup / dashboard"""
    if emulator:
        if config.misc.configured():
            yield from resp.redirect('/ui/dashboard.html')
        else:
            yield from resp.redirect('/ui/setup.html')
    else:
        if config.misc.configured():
            yield from resp.redirect('/dashboard')
        else:
            yield from resp.redirect('/setup')


@web.route('/setup')
def page_setup(req, resp):
    """Setup page. Send everything packed and gzipped at once."""
    yield from resp.send_file('setup_all.html.gz',
                              content_encoding='gzip',
                              content_type='text/html')


@web.route('/dashboard')
def page_dashboard(req, resp):
    """Dashboard page. The same idea as for setup page"""
    yield from resp.send_file('dashboard_all.html.gz',
                              content_encoding='gzip',
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
    print("Starting {}...".format(device_name))
    # Add RestAPI resources
    web.add_resource(http.LedStrip(led_strip), '/v1/ledstrip/on')
    web.add_resource(http.LedStripTest(led_strip), '/v1/ledstrip/test')
    web.add_resource(config, '/v1/config')
    web.add_resource(config.wifi, '/v1/wifi/scan')
    # Start setup routine
    setup.start(config, setup_button)
    # Start status LED routine, if board has it
    if status_led_pin:
        statusled.start(config, status_led_pin)

    # Run HTTP Server on 80 port for real devices.
    # Otherwiese use 8081 port
    if not emulator:
        web.run(host='0.0.0.0', port=80)
    else:
        web.run(host='0.0.0.0', port=8081)


if __name__ == '__main__':
    start()
