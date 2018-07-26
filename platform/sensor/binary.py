"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import logging
import uasyncio as asyncio


log = logging.getLogger('BINARY_SENSOR')


class BinarySensor():
    def __init__(self, pin, config, mqtt, param_name):
        """Binary sensor. Simply reports whenever GPIO state changed
        Args:
            - pin: GPIO to listen on
            - config: instance of config class
            - mqtt: instance of tinymqtt
            - param_name: name of config parameter to get MQTT topic from
        """
        self.cfg = config
        self.pin = pin
        self.mqtt = mqtt
        self.param_name = param_name
        self.value = pin.value()
        # For ISR - to schedule handler resume only once
        self.scheduled = False

    def _ISR_hander(self, pin):
        """ISR for GPIO. We want to be notified when level changed
        so we can report changes.
        Since it is ISR handler it should be as short as possible
        so all relevant work will be done in __handler ASAP.
        """
        if not self.scheduled:
            self.scheduled = True
            self.loop.call_soon(self.handler_task)

    async def _handler(self):
        while True:
            try:
                self.scheduled = False
                curval = self.pin.value()
                if curval != self.value:
                    self.value = curval
                    # send update
                    self.mqtt.publish(self.cfg.value(self.param_name), str(self.value), retain=True)
                # Suspend until ISR triggered
                yield False
            except asyncio.CancelledError:
                # Coroutine has been canceled
                return
            except Exception as e:
                log.exc(e, "")

    def run(self, loop):
        self.loop = loop
        self.handler_task = self._handler()
        self.pin.init(self.pin.IN, pull=self.pin.PULL_UP)
        self.pin.irq(trigger=self.pin.IRQ_RISING | self.pin.IRQ_FALLING,
                     handler=self._ISR_hander)
        self.loop.create_task(self.handler_task)

    def shutdown(self):
        self.pin.irq(trigger=0)
        if self.handler_task:
            asyncio.cancel(self.handler_task)
