"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import uasyncio as asyncio
import logging


log = logging.getLogger('AMBIENT')


class AmbientLightAnalogSensor():
    def __init__(self, config, mqtt, pin):
        """Generic analog ambient sensor based on 5528 light resistor
        Arguments:
            config - SimpleConfig instance
            mqtt   - Instance of MQTT to send periodical updates
            pin    - ADC pin number. For ESP8266 only 0
        """
        self.mqtt = mqtt
        self.sensor = pin
        self.last_value = 0
        # Register config parameters
        self.cfg = config
        self.cfg.add_param('mqtt_topic_sensor_light', 'neopixel/sensor/light')
        self.cfg.add_param('sensor_ambient_interval', 60)
        self.cfg.add_param('sensor_ambient_threshold', 10)

    async def _handler(self):
        while True:
            try:
                value = self.sensor.read()
                diff = abs(value - self.last_value)
                if diff > self.cfg.sensor_ambient_threshold:
                    self.mqtt.publish(self.cfg.mqtt_topic_sensor_light, str(value), retain=True)
                self.last_value = value
                await asyncio.sleep(self.cfg.sensor_ambient_interval)
            except asyncio.CancelledError:
                # Coroutine has been canceled
                return
            except Exception as e:
                log.exc(e, "")

    def run(self, loop):
        self.loop = loop
        self.handler_task = self._handler()
        self.loop.create_task(self.handler_task)

    def shutdown(self):
        if self.handler_task:
            asyncio.cancel(self.handler_task)
