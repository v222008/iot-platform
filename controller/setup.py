"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import machine
import network
import uasyncio as asyncio
import utime as time
import utils.dns


# Setup button indicators
button_pressed = None
button_released = None
# AP
ap_if = network.WLAN(network.AP_IF)
ap_activated = False
# Async event loop
event_loop = asyncio.get_event_loop()


def __handler(config):
    global button_pressed, button_released, ap_activated
    if button_pressed:
        # perform reset if button pressed for 5+ seconds
        if time.time() - button_pressed > 5:
            machine.reset()
        # just single press/release for less than 5 sec
        if button_released:
            # Cleanup ISR event
            button_pressed = None
            button_released = None
            print("Entering setup mode...")
            config.update({'misc': {'configured': False}})
    # Turn on AP if device went into unconfigured mode
    # or user has pressed setup button
    if not config.misc.configured() and not ap_activated:
        print('Unconfigured system, enabling WiFi AP')
        ap_if.active(True)
        ap_activated = True
    # Turn off AP when device has been successfully configured
    if config.misc.configured() and ap_if.active():
        ap_if.active(False)
        ap_activated = False
        print('System has been configured, WiFi AP disabled')
    # Schedule next run in 1 sec
    event_loop.call_later(1, __handler, config)


def buttonISR(pin):
    """ISR for setup button.
    We just want to measure depress duration.
    Since it is ISR handler it should be as short as possible
    so all relevant work will be done in __handler ASAP.
    """
    global button_pressed, button_released
    if button_pressed:
        button_released = time.time()
    else:
        button_pressed = time.time()


def start(config, bpin=None):
    """Starts "setup" routine. It does few things:
        1. Monitors for system state like enables / disables AP (misc.configured)
        2. Setup button single click < 5 sec: enters SETUP mode
           (resets mics.configured) and enables AP.
        3. Long click > 5 sec: performs device reset.
    Accepted args:
        - misc_config: configuration instance.
        - pbin [optional]: setup button PIN.
    """
    if bpin:
        bpin.irq(trigger=bpin.IRQ_RISING | bpin.IRQ_FALLING, handler=buttonISR)
    # Schedule first run in 0.2 sec - to let system initialize everything
    event_loop.call_later_ms(250, __handler, config)
