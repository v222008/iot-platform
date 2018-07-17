#!/usr/bin/env micropython
"""
Open Neopixel Controller

MIT license
(C) Konstantin Belyalov 2017-2018
"""

import logging
import micropython
import uasyncio as asyncio
from app import App


async def shutdown_wait():
    """Helper to make graceful app shutdown"""
    await asyncio.sleep_ms(100)


def main():
    # Some ports requires to allocate extra mem for exceptions
    if hasattr(micropython, 'alloc_emergency_exception_buf'):
        micropython.alloc_emergency_exception_buf(100)

    # Main loop
    try:
        loop = asyncio.get_event_loop()
        app = App(loop)
        app.run()
        loop.run_forever()
    except KeyboardInterrupt as e:
        pass
    except Exception as e:
        log = logging.Logger('main')
        log.exc(e, "Unhandled exception in main loop")

    # Gracefully stop app
    app.stop()
    loop.run_until_complete(shutdown_wait())


if __name__ == '__main__':
    main()
