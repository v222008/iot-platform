"""
RGB / RGBW controller for NeoPixel LEDs like:
 - WS2812
 - WS2812b
 - WS2813
 - SK6812

MIT license
(C) Konstantin Belyalov 2017-2018
"""
import time
import esp
import uasyncio as asyncio


max_leds = 720

# Neopixel color map: R -> 1, G -> 0, B -> 2, W = 3
color_order = (1, 0, 2, 3)
led_types = {'rgb': 3,
             'rgbw': 4,
             'rgbww': 4,
             'rgbnw': 4}


class LedStrip():
    """Class to control LED Strip.
    Include config part as well
    """

    def __init__(self, pin):
        self.pin = pin
        self.pin.init(pin.OUT)
        self.type = None
        self.cnt = None
        self.defaults = {'cnt': '', 'type': ''}
        self.config = self.defaults.copy()

    def config_apply(self, cfg, merge=True):
        # Validate config before applying
        if merge:
            tmp = self.config.copy()
            tmp.update(cfg)
        else:
            tmp = cfg
        # Cross check parameters
        for key in tmp.keys():
            if key not in self.defaults:
                raise ValueError('Unknown parameter "{}"'.format(key))
        for key in self.defaults.keys():
            if key not in tmp:
                raise ValueError('Parameter "{}" is required'.format(key))
        # Re-initialize LED strip
        self.initialize(**tmp)
        # All ok, save config
        self.config = tmp

    def config_get(self):
        return self.config

    def config_replace(self, cfg):
        self.config_apply(cfg, False)

    def config_merge(self, cfg):
        self.config_apply(cfg)

    def initialize(self, type, cnt):
        if cnt is None:
            raise ValueError('Value for "cnt" is required')
        if type is None:
            raise ValueError('Value for "type" is required')
        if type not in led_types:
            raise ValueError('Unknow LED type "{}".'.format(type))
        cnt = int(cnt)
        if cnt > max_leds or cnt < 1:
            raise ValueError('Value for "cnt" out of valid range [1-{}]'.format(max_leds))
        self.type = type
        self.cnt = cnt
        self.color_cnt = led_types[type]
        self.buf = bytearray(self.color_cnt * self.cnt)

    def shutdown(self):
        self.type = None
        self.cnt = None
        self.buf = None

    def test(self, type, cnt):
        old_type = self.type
        old_cnt = self.cnt
        try:
            self.initialize(type, cnt)
            # Test all colors by enabling pixel by pixel
            for c in range(self.color_cnt):
                for i in range(self.cnt):
                    self.buf[i * self.color_cnt + color_order[c]] = 255
                    esp.neopixel_write(self.pin, self.buf, True)
                    time.sleep_ms(10)
                time.sleep_ms(400)
            # Turn all pixels off
            for i in range(self.color_cnt * self.cnt):
                self.buf[i] = 0
            esp.neopixel_write(self.pin, self.buf, True)
        finally:
            # restore original state
            if old_type:
                self.initialize(old_type, old_cnt)
            else:
                self.shutdown()

    def __change_color(self, data):
        print("changing color:", data)
        for rng, color in data:
            # In case of 4 color LED - process white color first
            # Neopixel color bytes: G -> 0, R -> 1, B -> 2, W = 3
            # HEX RBG: RRGGBBWW
            if self.color_cnt == 4:
                c3 = color & 0xff
                color = color >> 8
            # blue
            c2 = color & 0xff
            color = color >> 8
            # green
            c0 = color & 0xff
            # red
            c1 = color >> 8
            if self.color_cnt == 4:
                print(rng, c1, c0, c2, c3)
            else:
                print(rng, c1, c0, c2)
            for i in rng:
                idx = i * self.color_cnt
                self.buf[idx] = c0
                self.buf[idx + 1] = c1
                self.buf[idx + 2] = c2
                if self.color_cnt == 4:
                    self.buf[idx + 3] = c3
        esp.neopixel_write(self.pin, self.buf, True)

    def turn_on(self, data):
        # Non configured strip
        if self.type is None:
            raise Exception('LED Strip is not configured yet.')
        # In case of no input parameters - just use recent color map
        if not len(data):
            data = {'all': '#00ff00'}
        # Validate LED color ranges
        parsed = []
        for leds, hexcolor in data.items():
            if leds.lower() == 'all':
                r1 = 1
                r2 = self.cnt
            elif '-' in leds:
                arr = leds.split('-')
                if len(arr) > 2 or not arr[0].isdigit() or not arr[1].isdigit():
                    raise Exception('Invalid color range format')
                r1 = int(arr[0])
                r2 = int(arr[1])
            elif leds.isdigit():
                r1 = int(leds)
                r2 = r1
            else:
                raise Exception('Invalid color format')
            if r1 < 1:
                raise Exception('Range: "{}-{}" is invalid. Valid values are from 1 to {}'.format(r1 + 1, r2, self.cnt))
            # Validate / convert color to int
            idx = 0
            if hexcolor.startswith('#'):
                idx = 1
            elif hexcolor.startswith('0x'):
                idx = 2
            try:
                color = int(hexcolor[idx:], 16)
            except Exception:
                raise Exception('Invalid color format.')
            parsed.append((range(r1 - 1, r2), color))
        # Schedule color change soon
        loop = asyncio.get_event_loop()
        loop.call_soon(self.__change_color, parsed)

    def turn_off(self):
        pass
