"""
Open Neopixel Controller

MIT license
(C) Konstantin Belyalov 2017-2018
"""
import logging
import machine
import network
import gc

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


class Status():
    def __init__(self, app):
        self.app = app

    async def get(self, data):
        """Returns current status"""
        yield '{"wifi":'
        yield from self.app.wifi.get(data)
        yield ',"sensor": {"light":%s},' % self.app.ambi.last_value
        yield '"memory":{"allocated":%s,"free":%s},' % (gc.mem_alloc(), gc.mem_free())
        yield '"led": {"state":%d}}' % (self.app.neo.state())


class App():

    def __init__(self, loop):
        self.loop = loop
        self.log = logging.Logger('app')
        self.setup_modules()
        self.setup_wifi()
        self.setup_routes()

    def setup_modules(self):
        # Base config
        self.config = SimpleConfig()
        self.config.add_param('configured', False)
        self.config.add_param('hostname',
                              'neopixel_{:s}'.format(platform.utils.mac_last_digits()))
        # Setup remote logging
        self.rlogging = RemoteLogging(self.config)
        # MQTT
        self.mqtt = tinymqtt.MQTTClient('neopixelctrl-{:s}'.format(
            platform.utils.mac_last_digits()), config=self.config)
        # DNS
        self.dns = tinydns.Server(ttl=10)
        # Modules
        self.ambi = AmbientLightAnalogSensor(self.config, self.mqtt, machine.ADC(0))
        self.setupbtn = SetupButton(self.config, machine.Pin(setup_btn_pin))
        self.status = StatusLed(self.config, machine.Pin(status_led_pin))
        # WebServer
        self.web = tinyweb.webserver(debug=True)
        # LED strip handler (+ associated web routes)
        self.neo = NeopixelStrip(machine.Pin(neopixel_pin),
                                 self.config,
                                 self.web,
                                 self.mqtt,
                                 self.loop)

    def setup_wifi(self):
        # Setup AP parameters
        self.wifi = WifiSetup(self.config)
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(True)
        ap_if.config(essid=self.config.hostname,
                     authmode=network.AUTH_WPA_WPA2_PSK,
                     password=b'neopixel')
        ap_if.ifconfig(('192.168.168.1', '255.255.255.0', '192.168.168.1', '192.168.168.1'))
        ap_if.active(False)
        # Captive portal
        platform.utils.captiveportal.enable(self.web, self.dns, '192.168.168.1')

    def setup_routes(self):
        @self.web.route('/')
        async def index(self, req, resp):
            if self.config.configured:
                await resp.redirect('/dashboard')
            else:
                await resp.redirect('/setup')

        @self.web.route('/dashboard')
        async def page_dashboard(req, resp):
            await resp.send_file('dashboard_all.html.gz',
                                 content_encoding='gzip',
                                 content_type='text/html')

        @self.web.route('/setup')
        async def page_setup(req, resp):
            await resp.send_file('setup_all.html.gz',
                                 content_encoding='gzip',
                                 content_type='text/html')

        @self.web.route('/restart')
        @self.web.route('/reset')
        async def page_restart(req, resp):
            self.log.warning('Restart requested from WEB')
            machine.reset()

        # REST API pages
        self.web.add_resource(self.wifi, '/wifi')
        self.web.add_resource(self.config, '/config')
        self.web.add_resource(Status(self), '/status')

    def run(self):
        logging.basicConfig(level=logging.DEBUG)
        # Load configuration
        try:
            self.config.load()
        except Exception as e:
            self.log.warning('Config load failed: {}'.format(e))

        wport = 80
        dport = 53
        if platform.utils.is_emulator():
            wport = 8080
            dport = 5335
        # Start services
        self.dns.run(host='0.0.0.0', port=dport, loop=self.loop)
        self.web.run(host='0.0.0.0', port=wport, loop_forever=False, loop=self.loop)
        self.mqtt.run(self.loop)
        self.ambi.run(self.loop)
        self.setupbtn.run(self.loop)
        self.status.run(self.loop)

    def stop(self):
        if not platform.utils.is_emulator():
            return
        self.log.info('terminating...')
        for s in [self.web, self.dns, self.mqtt, self.ambi, self.setupbtn, self.status]:
            s.shutdown()
