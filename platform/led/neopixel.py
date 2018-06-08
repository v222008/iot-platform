"""
RGB / RGBW controller for NeoPixel LEDs like:
 - WS2812
 - WS2812b
 - WS2813
 - SK6812

MIT license
(C) Konstantin Belyalov 2017-2018
"""
import esp
import uasyncio as asyncio


def validator_cnt(name, value):
    if value not in range(1, 501):
        raise ValueError('Invalid neopixel LED count (1-500 supported)')


def validator_colors(name, value):
    if value not in [3, 4]:
        raise ValueError('Invalid neopixel color count (valid 3 or 4)')


class Neopixel():
    """Class to control Neopixels."""

    def __init__(self, pin, config, loop=None):
        self.pin = pin
        self.pin.init(pin.OUT)
        self.type = None
        self.cnt = None
        self.cfg = config
        self.cfg.add_param('neopixel_cnt', 1,
                           validator=validator_cnt,
                           callback=self.reconfigure, group='neopix')
        self.cfg.add_param('neopixel_colors', 3,
                           validator=validator_colors,
                           callback=self.reconfigure, group='neopix')
        if loop is None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        # Animation coro
        self.anim = None
        self.reconfigure()

    def reconfigure(self):
        self.cnt = self.cfg.neopixel_cnt
        self.colors = self.cfg.neopixel_colors
        print('reconf {} pixes with {} col'.format(self.cnt, self.colors))
        self.buf = bytearray(self.colors * self.cnt)

    def __change_color(self, pixels):
        col = bytearray(4)
        for leds, color in pixels:
            # Neopixel color bytes: G -> 0, R -> 1, B -> 2, W = 3
            col[0] = color[1]
            col[1] = color[0]
            col[2:4] = color[2:4]
            # Check range. None - means all pixels
            if not leds:
                leds = range(0, self.cnt)
            for l in leds:
                idx = l * self.colors
                self.buf[idx:idx + self.colors] = col[:self.colors]
        # print(self.buf)
        esp.neopixel_write(self.pin, self.buf, True)

    def set_color(self, pixels):
        self.__change_color(pixels)

    def set_color_all(self, color):
        self.__change_color([(range(self.cnt), color)])

    async def __fade_effect(self, pixels, length, delay):
        # Create black mask
        current = []
        increments = []

        for leds, color in pixels:
            # Calculate increments based on fade length
            inc_color = bytearray(color)
            for i, c in enumerate(inc_color):
                inc_color[i] = color[i] // length
            increments.append(inc_color)
            # Fill with black
            current.append((leds, b'\x00' * 4))
        for step in range(length):
            # increase colors
            for idx, pxl in enumerate(current):
                newcol = bytearray(pxl[1])
                for i, c in enumerate(newcol):
                    newcol[i] = c + increments[idx][i]
                current[idx] = (pxl[0], newcol)
            self.__change_color(current)
            await asyncio.sleep_ms(delay)

    def fade_in(self, pixels, length=5, delay=50):
        if self.anim:
            asyncio.cancel(self.anim)
        self.loop.create_task(self.__fade_effect(pixels, length, delay))

    def fade_out(self, pixels, length=5, delay=50):
        if self.anim:
            asyncio.cancel(self.anim)
        self.loop.create_task(self.__fade_in(pixels, length, delay))
