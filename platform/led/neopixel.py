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
        raise ValueError('Invalid config')


def validator_colors(name, value):
    if value not in [3, 4]:
        raise ValueError('Invalid config')


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

    def parse_pixels_format(self, data):
        parsed = []
        for leds, hexcolor in data.items():
            # Convert hex color to int
            try:
                if hexcolor.startswith('#'):
                    hexcolor = hexcolor[1:]
                bcolor = int(hexcolor, 16).to_bytes(4, 'big')
            except ValueError:
                raise ValueError('Invalid color')
            # All pixels
            if leds.lower() == 'all':
                parsed.append((range(self.cnt), bcolor))
                continue
            # Range, e.g. "1-10"
            if '-' in leds:
                arr = leds.split('-')
                if len(arr) > 2 or not arr[0].isdigit() or not arr[1].isdigit():
                    raise ValueError('Invalid range')
                r1 = int(arr[0])
                r2 = int(arr[1])
            elif leds.isdigit():
                r1 = int(leds)
                r2 = r1
            else:
                raise ValueError('Invalid color')
            if r1 < 1:
                raise ValueError('Invalid range')
            parsed.append((range(r1 - 1, r2), bcolor))
        return parsed

    def reconfigure(self):
        self.cnt = self.cfg.neopixel_cnt
        self.colors = self.cfg.neopixel_colors
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
                leds = range(self.cnt)
            for l in leds:
                idx = l * self.colors
                self.buf[idx:idx + self.colors] = col[:self.colors]
        esp.neopixel_write(self.pin, self.buf, True)

    def set_color(self, pixels):
        self.__change_color(self.parse_pixels_format(pixels))

    def set_color_all(self, color):
        self.__change_color([(range(self.cnt), color)])

    async def __fade_effect(self, pixels, length, delay, callback):
        incs = bytearray(self.colors * self.cnt)
        col = bytearray(4)
        # Calculate increments (decrements) for each color
        # range -> color, e.g.:
        # [(range(0, 5), b'\xff\xff\xff\xff')]
        for leds, color in pixels:
            # convert color
            col[0] = color[1]
            col[1] = color[0]
            col[2:4] = color[2:4]
            if not leds:
                leds = range(0, self.cnt)
            for l in leds:
                for c in range(self.colors):
                    idx = l * self.colors + c
                    incval = int((col[c] - self.buf[idx]) / length)
                    incs[idx] = incval
        # Run effect
        for step in range(length):
            for leds, color in pixels:
                if not leds:
                    leds = range(0, self.cnt)
                for l in leds:
                    for c in range(self.colors):
                        idx = l * self.colors + c
                        self.buf[idx] += incs[idx]
            esp.neopixel_write(self.pin, self.buf, True)
            await asyncio.sleep_ms(delay)
        # Set final (desired) color
        self.__change_color(pixels)
        # Run finish callback, if any
        if callback:
            callback()

    def fade_effect(self, pixels, length=5, delay=50, callback=None):
        if self.anim:
            asyncio.cancel(self.anim)
        self.loop.create_task(self.__fade_effect(self.parse_pixels_format(pixels),
                                                 length, delay, callback))
