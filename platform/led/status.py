"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import logging
import uasyncio as asyncio


log = logging.getLogger('LED')


class StatusLed():
    def __init__(self, config, pin):
        """Status LED routine: It does few things:
            1. Turns LED on when system is OK
            2. Make LED blinks whenever system in unconfigured mode
        Args:
            - config: configuration instance.
            - pin: Pin where LED connected to.
        """
        self.cfg = config
        self.pin = pin

    async def _handler(self):
        while True:
            try:
                # Schedule next run in 1 sec
                if not self.cfg.configured:
                    self.pin.value(not self.pin.value())
                    # sleep for 300ms
                    yield 300
                    # await asyncio.sleep_ms(300)
                else:
                    self.pin.on()
                    await asyncio.sleep(1)
            except asyncio.CancelledError:
                # Coroutine has been canceled
                return
            except Exception as e:
                log.exc(e, "")

    def run(self, loop):
        self.loop = loop
        self.handler_task = self._handler()
        self.pin.init(self.pin.OUT)
        self.loop.create_task(self.handler_task)

    def shutdown(self):
        if self.handler_task:
            asyncio.cancel(self.handler_task)
