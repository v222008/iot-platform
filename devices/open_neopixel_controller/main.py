#!/usr/bin/env micropython
"""
Neopixel Controller

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
from platform.led.status import StatusLed
from platform.utils.wifi import WifiSetup
from platform.utils.config import SimpleConfig
from platform.utils.remotelogging import RemoteLogging
from platform.sensor.ambient import AmbientLightAnalogSensor

from strip import NeopixelStrip


neopixel_pin = const(4)
setup_btn_pin = const(5)
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
    # Setup default hostname
    config.hostname = 'NeoPixel_{}'.format(platform.utils.mac_last_digits())
    wsetup = WifiSetup(config)

    # Setup remote logging
    RemoteLogging(config)

    # MQTT
    mqtt = tinymqtt.MQTTClient('neopixelcontroller-{}'.format(
        platform.utils.mac_last_digits()), config=config)

    # DNS
    dns = tinydns.Server(ttl=10)

    # WebServer
    web = tinyweb.webserver(debug=True)

    # Modules
    ambi = AmbientLightAnalogSensor(config, mqtt, machine.ADC(0))
    setupbtn = SetupButton(config, machine.Pin(setup_btn_pin))
    status = StatusLed(config, machine.Pin(status_led_pin))

    # Enable REST API for config & wifi
    web.add_resource(config, '/config')
    web.add_resource(wsetup, '/wifi')

    # Create LED strip handler
    NeopixelStrip(machine.Pin(neopixel_pin), config, web, mqtt, loop)

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

    @web.route('/restart')
    async def page_restart(req, resp):
        machine.reset()

    # Setup AP parameters
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(True)
    ap_if.config(essid=config.hostname, authmode=network.AUTH_WPA_WPA2_PSK, password=b'neopixel')
    ap_if.ifconfig(('192.168.168.1', '255.255.255.0', '192.168.168.1', '192.168.168.1'))
    ap_if.active(False)

    # Captive portal
    platform.utils.captiveportal.enable(web, dns, '192.168.168.1')

    # Load configuration
    try:
        config.load()
    except Exception as e:
        log.warning('Config load failed: {}'.format(e))

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
        ambi.run(loop)
        setupbtn.run(loop)
        status.run(loop)

        # Run main loop
        loop.run_forever()
    except KeyboardInterrupt as e:
        if platform.utils.is_emulator():
            print('terminating...')
            for s in [web, dns, mqtt, ambi, setupbtn, status]:
                s.shutdown()
            loop.run_until_complete(shutdown_wait())
            print('Done')
        else:
            raise
    except Exception as e:
        log.exc(e, "Unhandled exception in main loop")


if __name__ == '__main__':
    main()
