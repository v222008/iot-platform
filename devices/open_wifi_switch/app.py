"""
Open WiFi 2 SSR relays switch

MIT license
(C) Konstantin Belyalov 2018
"""
import logging
import machine
import network
import gc

import tinyweb
import tinymqtt

from platform.switch.relay import Relay
from platform.led.status import StatusLed
from platform.utils import mac_last_digits, is_emulator
from platform.utils.config import SimpleConfig
from platform.utils.wifi import WifiSetup
from platform.utils.remotelogging import RemoteLogging


# Where status LED connected to
status_led_pin = const(13)
# Relay PINs
relays_pins = [12, 14]


class Status():
    def __init__(self, app):
        self.app = app

    async def get(self, data):
        """Returns current status"""
        yield '{"wifi":'
        yield from self.app.wifi.get(data)
        yield ',"memory":{{"allocated":{},"free":{}}}'.format(gc.mem_alloc(), gc.mem_free())
        for r in self.app.relays:
            yield ',"relay{}": {}'.format(r.num, r.state)
        yield '}'


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
                              'wifiswitch_{:s}'.format(mac_last_digits()))
        # Setup remote logging
        self.rlogging = RemoteLogging(self.config)
        # MQTT
        self.mqtt = tinymqtt.MQTTClient('wifiswitch-{:s}'.format(mac_last_digits()),
                                        server='192.168.1.1', port=3883,
                                        config=self.config)
        # Modules
        self.status = StatusLed(self.config, machine.Pin(status_led_pin))
        # self.setupbtn = SetupButton(self.config, machine.Pin(setup_btn_pin))
        # WebServer
        self.web = tinyweb.webserver(debug=True)
        # Relays
        self.relays = []
        for num, pin in enumerate(relays_pins):
            self.relays.append(Relay(num + 1,
                                     machine.Pin(pin),
                                     self.config,
                                     self.web,
                                     self.mqtt))

    def setup_wifi(self):
        # Setup AP parameters
        self.wifi = WifiSetup(self.config)
        ap_if = network.WLAN(network.AP_IF)
        ap_if.active(True)
        ap_if.config(essid=self.config.hostname,
                     authmode=network.AUTH_WPA_WPA2_PSK,
                     password=b'wifiswitch')
        ap_if.ifconfig(('192.168.168.1', '255.255.255.0', '192.168.168.1', '192.168.168.1'))
        ap_if.active(False)
        # Captive portal
        # platform.utils.captiveportal.enable(self.web, self.dns, '192.168.168.1')

    def setup_routes(self):
        @self.web.route('/restart')
        @self.web.route('/reset')
        async def page_restart(req, resp):
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
        # dport = 53
        if is_emulator():
            wport = 8080
            # dport = 5335
        # Start services
        # self.dns.run(host='0.0.0.0', port=dport, loop=self.loop)
        self.web.run(host='0.0.0.0', port=wport, loop_forever=False, loop=self.loop)
        self.mqtt.run(self.loop)
        # self.setupbtn.run(self.loop)
        self.status.run(self.loop)

    def stop(self):
        if not is_emulator():
            return
        for s in [self.web, self.mqtt, self.status]:
            s.shutdown()
