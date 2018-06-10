"""
Neopixel Controller

MIT license
(C) Konstantin Belyalov 2017-2018
"""
import logging
import ujson as json
import sys
from platform.led.neopixel import Neopixel


log = logging.getLogger('LEDSTRIP')


class StripError(Exception):
    pass


class NeopixelStrip(Neopixel):
    def __init__(self, pin, config, web, mqtt, loop):
        super().__init__(pin, config, loop)
        # Params
        self.cfg.add_param('led_last_on_color', '#ffffffff')
        # MQTT
        self.mqtt = mqtt
        self.cfg.add_param('mqtt_topic_led_status', 'neopixel/led')
        # Control topic. We need to get notified to re-subscribe on it
        self.cfg.add_param('mqtt_topic_led_control', 'neopixel/led/set',
                           callback=self.mqtt_config_changed,
                           group='mqtt_config')
        # Web endpoints
        for act in ['on', 'off', 'fade']:
            web.add_resource(self, '/{}'.format(act), action=act)

    def mqtt_config_changed(self):
        """Callback when mqtt control topic changed"""
        self.mqtt.subscribe(self.cfg.mqtt_topic_led_control, self.mqtt_control)

    def on(self, data):
        if 'color' not in data:
            color = self.cfg.led_last_on_color
        else:
            color = data['color']
        self.cfg.led_last_on_color = color
        pixels = data.get('pixels', {'all': color})
        print('on', pixels)
        self.set_color(pixels)

    def off(self, data):
        # Set all to black = turn off
        self.set_color_all(b'\x00\x00\x00\x00')

    def fade(self, data):
        if 'color' not in data:
            color = self.cfg.led_last_on_color
        else:
            color = data['color']
            self.cfg.led_last_on_color = color
        pixels = data.get('pixels', {'all': color})
        length = data.get('length', 20)
        delay = data.get('delay', 20)
        print('fade', pixels, length, delay, data)
        self.fade_effect(pixels, length, delay)

    def process_command(self, data, action):
        # by default - all pixels
        if not hasattr(self, action):
            raise StripError('No such effect {}'.format(action))
        act = getattr(self, action)
        act(data)

    def post(self, data, action):
        try:
            self.process_command(data, action)
            return {'message': 'color changed'}
        except StripError as e:
            return {'message': e}, 404

    def get(self, data, action):
        return self.post(data, action)

    def mqtt_control(self, data):
        try:
            js = json.loads(data)
            act = js.get('effect', 'on')
            self.process_command(js, act)
        except Exception as e:
            log.error(e)
            sys.print_exception(e)