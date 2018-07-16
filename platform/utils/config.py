"""
Utilities for ESP based devices
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import esp
import gc


# Store config right before SDK params close to the end of flash
BLOCK_SIZE = const(4096)
SDK_BLOCKS = 19
CONFIG_BLOCK = (esp.flash_size() // BLOCK_SIZE) - SDK_BLOCKS


class ConfigError(Exception):
    pass


def validate_name(name):
    if len(name) > 32:
        raise ConfigError('Name too long')
    if name.startswith('_'):
        raise ConfigError('Name shouldnt start with underscore')
    if ' ' in name:
        raise ConfigError('Spaces arent allowed in name')


def validate_value_type(value):
    if isinstance(value, int):
        return
    elif isinstance(value, str):
        return
    elif isinstance(value, bool):
        return
    elif value is None:
        return
    else:
        raise ConfigError('Unsupported default value type')


class SimpleConfig():
    """Very simple and generic config class for ESP like devices.
    Aimed to be pretty simple and generic
    """

    def __init__(self, autosave=True):
        """Create instance of generic configuration.
        Arguments:
            autosave [opt]: Enable configuration autosave immediately after changes have been made.
        """
        self._autosave = autosave
        self._validators = {}
        self._callbacks = {}
        self._group_callbacks = {}

    def validate_value(self, name, value):
        # if len(value) > 192:
        #     raise ConfigError("Value too long")
        if name in self._validators:
            self._validators[name](name, value)

    def run_callbacks(self, params):
        cbs = {}
        for p in params:
            if p in self._callbacks:
                cb = self._callbacks[p]
                # cb = (cb_func, group_name)
                cbs[cb[1]] = cb[0]
        for cb in cbs.values():
            cb()

    def add_param(self, name, default, validator=None, callback=None, group=None):
        validate_name(name)
        validate_value_type(default)
        # Check for duplicates
        if name in self.__dict__:
            raise ConfigError('Param {} already exists'.format(name))
        # Validate default value
        if validator:
            validator(name, default)
            self._validators[name] = validator
        # All done, save
        if callback is None and group:
            callback = self._group_callbacks[group]
        if callback:
            if group is None:
                group = name
            self._group_callbacks[group] = callback
            self._callbacks[name] = (callback, group)
        setattr(self, name, default)

    def load(self):
        """Load config (all sections) from file"""
        offset = CONFIG_BLOCK * BLOCK_SIZE
        # metadata, bytes:
        # 0: name len
        # 1: value len
        # 2: type
        # 3: chksum (sum of name + value + type + chksum itself)
        meta = bytearray(4)
        print()
        while True:
            esp.flash_read(offset, meta)
            offset += 4
            # All 0xff indicates end of list
            if meta == b'\xff\xff\xff\xff':
                break
            if sum(meta[:3]) != meta[3]:
                raise ConfigError('Malformed config')
            # read param name
            buf = bytearray(meta[0])
            esp.flash_read(offset, buf)
            offset += meta[0] + (4 - meta[0] % 4)
            name = bytes(buf).decode()
            # read value
            buf = bytearray(meta[1])
            esp.flash_read(offset, buf)
            if meta[2] == 1:
                value = int.from_bytes(buf, 'big')
                # Respect sign
                if value > 0x7FFFFFFF:
                    value -= 0x100000000
                offset += 4
            elif meta[2] == 2:
                value = bytes(buf).decode()
                offset += meta[1] + (4 - meta[1] % 4)
            else:
                value = bool(buf[0])
                offset += 4
            validate_name(name)
            validate_value_type(value)
            self.validate_value(name, value)
            setattr(self, name, value)
        gc.collect()

    def save(self):
        """Save config (all sections) into file."""
        esp.flash_erase(CONFIG_BLOCK)
        start = CONFIG_BLOCK * BLOCK_SIZE
        offset = start

        meta = bytearray(4)
        for k, v in self.__dict__.items():
            # skip class variables
            if k.startswith('_'):
                continue
            if isinstance(v, int):
                data = v.to_bytes(4, 'big')
                meta[1] = 4
                meta[2] = 1
            elif isinstance(v, str):
                meta[1] = len(v)
                meta[2] = 2
                # add padding to value
                data = v.encode() + '\x00' * (4 - (len(v) % 4))
            else:
                meta[1] = 4
                meta[2] = 3
                if v:
                    data = b'\x01\x00\x00\x00'
                else:
                    data = b'\x00\x00\x00\x00'
            # metadata, bytes:
            # 0: name len
            # 1: value len
            # 2: type
            # 3: chksum (sum of name + value + type + chksum itself)
            meta[0] = len(k)
            meta[3] = sum(meta[:3])
            esp.flash_write(offset, meta)
            offset += 4
            # add padding to name
            name = k.encode() + '\x00' * (4 - (len(k) % 4))
            esp.flash_write(offset, name)
            offset += len(name)
            esp.flash_write(offset, data)
            offset += len(data)
            # Entire config should be less than 1 block (~4096)
            if offset - start > 4000:
                raise ConfigError('config is too large')
        gc.collect()

    def update(self, params):
        """Update single parameter"""

        # Validate all parameters before apply
        for name, value in params.items():
            validate_name(name)
            if name not in self.__dict__:
                raise ConfigError("Param {} doesn't exists".format(name))
            validate_value_type(value)
            if type(value) != type(getattr(self, name)):  # noqa
                raise ConfigError("Invalid value type (str/int/etc)")
            self.validate_value(name, value)
        # Update values
        for name, value in params.items():
            setattr(self, name, value)
        # Done, run callbacks
        self.run_callbacks(params.keys())
        if self._autosave:
            self.save()

    async def get(self, data):
        """Returns JSON representation of config"""
        yield '{'
        comma = ''
        for k, v in self.__dict__.items():
            # skip class variables
            if k.startswith('_'):
                continue
            if isinstance(v, bool):
                yield '{}"{}":{:b}'.format(comma, k, v)
            elif isinstance(v, int):
                yield '{}"{}":{}'.format(comma, k, v)
            else:
                yield '{}"{}":"{}"'.format(comma, k, v)
            comma = ','
        yield '}'

    def post(self, data):
        self.update(data)
        return {'message': 'config updated'}
