"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import logging
import machine
import network
import uasyncio as asyncio
import utime as time

from platform.exclog import log_exception


log = logging.getLogger('SETUP_BTN')


class SetupButton():
    def __init__(self, config, btn_pin=None):
        """Setup button routine. It does few things:
            1. Monitors config and enables / disables AP (when unconfigured system)
            2. Setup button single click < 5 sec: enters SETUP mode
               (resets mics.configured) and enables AP.
            3. Long click > 5 sec: performs device reset.
        Args:
            - config: instance of config class
        Optional args:
            - btn_pin: PIN where button connected to
        """
        self.cfg = config
        self.btn_pin = btn_pin
        self.button_pressed = None
        self.button_released = None
        self.ap_activated = False
        self.ap_if = network.WLAN(network.AP_IF)

    def _ISR_hander(self, pin):
        """ISR for setup button.
        We just want to measure depress duration.
        Since it is ISR handler it should be as short as possible
        so all relevant work will be done in __handler ASAP.
        """
        if self.button_pressed:
            self.button_released = time.time()
        else:
            self.button_pressed = time.time()

    async def _handler(self):
        while True:
            try:
                if self.button_pressed:
                    # perform reset if button pressed for 5+ seconds
                    if time.time() - self.button_pressed > 5:
                        machine.reset()
                    # just single press/release for less than 5 sec
                    if self.button_released:
                        # Cleanup ISR event
                        self.button_pressed = False
                        self.button_released = False
                        log.info("Setup button pressed, entering setup mode...")
                        self.cfg.configured = False
                # Turn on AP if device went into unconfigured mode
                # or user has pressed setup button
                if not self.cfg.configured and not self.ap_activated:
                    log.info('Unconfigured system, WiFi AP enabled')
                    self.ap_if.active(True)
                    self.ap_activated = True
                # Turn off AP when device has been successfully configured
                if self.cfg.configured and self.ap_if.active():
                    self.ap_if.active(False)
                    self.ap_activated = False
                    log.info('System has been configured, WiFi AP disabled')
                # Schedule next run in 1 sec
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                # Coroutine has been canceled
                log.debug("SetupButton stopped")
                return
            except Exception as e:
                log_exception(e)

    def run(self, loop):
        self.loop = loop
        self.handler_task = self._handler()
        if self.btn_pin:
            self.btn_pin.init(machine.Pin.IN)
            self.btn_pin.irq(trigger=machine.Pin.IRQ_RISING | machine.Pin.IRQ_FALLING,
                             handler=self._ISR_hander)
        self.loop.create_task(self.handler_task)

    def shutdown(self):
        if self.btn_pin:
            self.btn_pin.irq(trigger=0)
        if self.handler_task:
            asyncio.cancel(self.handler_task)
