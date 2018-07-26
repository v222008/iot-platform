#!/usr/bin/env micropython
"""
Home Magic mini LED Controller

MIT license
(C) Konstantin Belyalov 2017-2018
"""

import logging
import micropython
import machine
import network
import uasyncio as asyncio

import tinyweb
import tinydns
import tinymqtt

import platform.utils.captiveportal
from platform.btn.setup import SetupButton
from platform.utils.wifi import WifiSetup
from platform.utils.config import SimpleConfig

from strip import WhiteLedStrip


white_pin = const(13)
blue_pin = const(12)
red_pin = const(14)
green_pin = const(5)
status_led_pin = const(10)

log = logging.Logger('main')


async def shutdown_wait():
    """Helper to make graceful app shutdown"""
    await asyncio.sleep_ms(100)


def main():
    # Some ports requires to allocate extra mem for exceptions
    if hasattr(micropython, 'alloc_emergency_exception_buf'):
        micropython.alloc_emergency_exception_buf(100)

    loop = asyncio.get_event_loop()
    logging.basicConfig(level=logging.DEBUG)

    # Base config
    config = SimpleConfig()
    config.add_param('configured', False)
    wsetup = WifiSetup(config)

    # MQTT
    mqtt = tinymqtt.MQTTClient('LEDcontroller-{}'.format(
        platform.utils.mac_last_digits()), config=config)

    # DNS
    dns = tinydns.Server(ttl=10)

    # WebServer
    web = tinyweb.webserver()

    # Enable REST API for config & wifi
    web.add_resource(config, '/config')
    web.add_resource(wsetup, '/wifi')

    # Create LED strip handler
    WhiteLedStrip(machine.Pin(green_pin), config, web, mqtt, loop)

    # Peripheral modules
    setupbtn = SetupButton(config, None)

    # Other web routes
    @web.route('/')
    async def index(req, resp):
        if config.configured:
            await resp.redirect('/dashboard')
        else:
            await resp.redirect('/setup')

    @web.route('/dashboard')
    async def page_dashboard(req, resp):
        await resp.send_file('dashboard_all.html.gz',
                             content_encoding='gzip',
                             content_type='text/html')

    @web.route('/setup')
    async def page_setup(req, resp):
        await resp.send_file('setup_all.html.gz',
                             content_encoding='gzip',
                             content_type='text/html')

    # Setup AP parameters
    ap_if = network.WLAN(network.AP_IF)
    essid = b'LedCtrl-%s' % platform.utils.mac_last_digits()
    ap_if.active(True)
    ap_if.config(essid=essid, authmode=network.AUTH_WPA_WPA2_PSK, password=b'ledledled')
    ap_if.ifconfig(('192.168.168.1', '255.255.255.0', '192.168.168.1', '192.168.168.1'))
    ap_if.active(False)
    # Captive portal
    platform.utils.captiveportal.enable(web, dns, '192.168.168.1')

    # Load configuration
    try:
        config.load()
    except Exception as e:
        log.warning('Config load failed: {}'.format(e))
        pass

    # Main loop
    try:
        wport = 80
        dport = 53
        if platform.utils.is_emulator():
            wport = 8080
            dport = 5335
        # Start services
        dns.run(host='0.0.0.0', port=dport, loop=loop)
        web.run(host='0.0.0.0', port=wport, loop_forever=False, loop=loop)
        mqtt.run(loop)
        setupbtn.run(loop)

        # Run main loop
        loop.run_forever()
    except KeyboardInterrupt as e:
        if platform.utils.is_emulator():
            for s in [web, dns, mqtt]:
                s.shutdown()
            loop.run_until_complete(shutdown_wait())
        else:
            raise
    except Exception as e:
        log.exc(e, "Unhandled exception")


if __name__ == '__main__':
    main()
