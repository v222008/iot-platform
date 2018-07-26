"""
Magic LED Controller

MIT license
(C) Konstantin Belyalov 2017-2018
"""
import logging
import machine
import ujson as json
import uasyncio as asyncio

log = logging.getLogger('LEDSTRIP')


class StripError(Exception):
    pass


class NoSuchEffectError(Exception):
    pass


class WhiteLedStrip():
    def __init__(self, pin, config, web, mqtt, loop):
        self.cfg = config
        self.effects = ['on', 'off', 'fade']
        # Params
        self.cfg.add_param('led_last_brightness', '100')
        # MQTT
        self.mqtt = mqtt
        self.cfg.add_param('mqtt_topic_led_status', 'lights')
        # Control topic. We need to get notified to re-subscribe on it
        self.cfg.add_param('mqtt_topic_led_control', 'lights/set',
                           callback=self._mqtt_config_changed,
                           group='mqtt_config')
        self.pwm = machine.PWM(pin, freq=1000)
        # Animation - e.g. fade effect
        self.anim = None
        # Web endpoints
        for act in self.effects:
            web.add_resource(self, '/{}'.format(act), action=act)
        self.loop = loop

    def _extract_brightness(self, data):
        brightness = self.cfg.led_last_brightness
        if 'brightness' in data:
            brightness = int(data['brightness'])
            if brightness > 100 or brightness < 0:
                raise ValueError('Invalid value {}, must be in range [0-100].')
        return brightness

    def _mqtt_config_changed(self):
        """Callback when mqtt control topic changed"""
        self.mqtt.subscribe(self.cfg.mqtt_topic_led_control, self.mqtt_control)

    def _publish_mqtt_state(self, state):
        self.mqtt.publish(self.cfg.mqtt_topic_led_status, str(state), retain=True)

    def on(self, data):
        val = self._extract_brightness(data)
        self.pwm.duty(val * 1024 // 100)
        self._publish_mqtt_state(val)
        self.cfg.led_last_brightness = val

    def off(self, data):
        self.pwm.duty(0)
        self._publish_mqtt_state(0)

    async def _fade_effect(self, new_brightness, length, delay):
        # Run effect
        val = self.cfg.led_last_brightness
        inc = (new_brightness - val) // length
        for step in range(length):
            val += inc
            self.pwm.duty(val * 1024 // 100)
            await asyncio.sleep_ms(delay)
        # Finally after effect finished - publish mqtt status update
        self._publish_mqtt_state(new_brightness)
        self.cfg.led_last_brightness = new_brightness

    def fade(self, data):
        val = self._extract_brightness(data)
        length = data.get('length', 20)
        delay = data.get('delay', 20)
        if self.anim:
            asyncio.cancel(self.anim)
        self.loop.create_task(self._fade_effect(val,
                                                length, delay))

    def process_command(self, data, action):
        # by default - all pixels
        if not hasattr(self, action):
            raise NoSuchEffectError('No such effect {}'.format(action))
        act = getattr(self, action)
        act(data)

    def post(self, data, action):
        try:
            self.process_command(data, action)
            return {'message': 'success'}
        except NoSuchEffectError as e:
            return {'message': e}, 404
        except ValueError as e:
            return {'message': e}, 400
        except Exception as e:
            log.exc(e, "Unhandled exception")

    def get(self, data, action):
        return self.post(data, action)

    def mqtt_control(self, data):
        # First case is pretty simple - brightness as value
        try:
            val = int(data)
            self.process_command({'brightness': val}, 'fade')
            return
        except ValueError:
            pass
        except Exception as e:
            log.exc(e, "Unhandled exception")
            return

        # One more chance - try to use it as JSON
        try:
            js = json.loads(data)
            act = js.get('effect', 'fade')
            self.process_command(js, act)
            return
        except ValueError:
            pass
        except Exception as e:
            log.exc(e, "Unhandled exception")
