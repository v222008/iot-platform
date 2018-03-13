"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import uasyncio as asyncio


# Async event loop
event_loop = asyncio.get_event_loop()


def __handler(config, pin):
    # Blink LED every 300ms in case of non configured device
    if not config.misc.configured():
        pin.value(not pin.value())
        event_loop.call_later_ms(300, __handler, config, pin)
    else:
        pin.on()
        event_loop.call_later(1, __handler, config, pin)


def start(config, pin):
    """Starts "status LED" routine. It does few things:
        1. Monitors for system state like enables / disables AP (misc.configured)
        2. Setup button single click < 5 sec: enters SETUP mode
           (resets mics.configured) and enables AP.
        3. Long click > 5 sec: performs device reset.
    Accepted args:
        - misc_config: configuration instance.
        - pbin [optional]: setup button PIN.
    """
    pin.init(pin.OUT)
    # Schedule first run very soon - 0.1 sec
    event_loop.call_later_ms(100, __handler, config, pin)
