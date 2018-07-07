"""
Mock classes / functions for ESP based devices
MIT license
(C) Konstantin Belyalov 2017-2018
"""


def unique_id():
    return b'__unix__'


def reset():
    print("(reset)")


pinvals = {}


class ADC():
    def __init__(self, num):
        self.num = num
        self.val = 0

    def read(self):
        return self.val


class PWM():
    def __init__(self, pin, freq=1000):
        self.pin = pin
        self.freq = freq
        self.duty_val = 0

    def duty(self, val):
        self.duty_val = val
        print("PWM to", val)


class Pin():
    IN = 0
    OUT = 1
    IRQ_FALLING = 2
    IRQ_RISING = 3

    def __init__(self, *args):
        self.idx = args[0]
        if self.idx not in pinvals:
            pinvals[self.idx] = 0

    def init(self, *args):
        pass

    def on(self):
        pinvals[self.idx] = 1

    def off(self):
        pinvals[self.idx] = 0

    def value(self, newval=None):
        if newval is None:
            return pinvals[self.idx]
        pinvals[self.idx] = newval

    def irq(self, trigger=None, handler=None):
        pass


class SPI():
    def __init__(self, idx):
        pass

    def write(self, frame):
        pass

    def read(self, cnt):
        return bytearray(cnt)
