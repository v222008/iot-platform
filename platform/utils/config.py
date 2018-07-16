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
        # Mandatory parameters
        self.add_param('hostname', 'unknown')

    def validate_value(self, name, value):
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
        # 1: type
        # 2: chksum (sum of name + type)
        meta = bytearray(3)
        while True:
            esp.flash_read(offset, meta)
            offset += 3
            # All 0xff indicates end of list
            if meta == b'\xff\xff\xff':
                break
            if sum(meta[:2]) != meta[2]:
                raise ConfigError('Malformed config')
            # read param name
            buf = bytearray(meta[0])
            esp.flash_read(offset, buf)
            offset += meta[0]
            name = bytes(buf).decode()
            # read value
            if meta[1] == 1:
                # type int
                buf = bytearray(4)
                esp.flash_read(offset, buf)
                offset += 4
                value = int.from_bytes(buf, 'big')
                # Respect sign
                if value > 0x7FFFFFFF:
                    value -= 0x100000000
            elif meta[1] == 2:
                # type string
                # read len
                buf = bytearray(1)
                esp.flash_read(offset, buf)
                offset += 1
                # read value
                if buf[0] > 0:
                    val = bytearray(buf[0])
                    esp.flash_read(offset, val)
                    value = bytes(val).decode()
                else:
                    value = ''
                offset += buf[0]
            elif meta[1] == 3:
                # type bool
                buf = bytearray(1)
                esp.flash_read(offset, buf)
                value = bool(buf[0])
                offset += 1
            elif meta[1] == 4:
                # None
                value = None
            else:
                raise ConfigError('Unknown {} value type'.format(meta[2]))
            validate_name(name)
            validate_value_type(value)
            self.validate_value(name, value)
            setattr(self, name, value)
        gc.collect()

    def save(self):
        """Save config (all sections) into file.
        Returns current size of config
        """
        esp.flash_erase(CONFIG_BLOCK)

        meta = bytearray(3)
        sector = bytearray()
        for k, v in self.__dict__.items():
            # skip class variables
            if k.startswith('_'):
                continue
            gc.collect()
            # metadata, bytes:
            # 0: name len
            # 1: type
            # 2: chksum (sum of name + type)
            # Param name len
            meta[0] = len(k)
            if isinstance(v, int):
                # type int
                meta[1] = 1
                data = v.to_bytes(4, 'big')
            elif isinstance(v, str):
                # type str
                vlen = len(v)
                if vlen > 255:
                    raise ConfigError('String value too long: {}'.format(k))
                meta[1] = 2
                data = bytearray(vlen + 1)
                data[0] = vlen
                data[1:] = v.encode()
            elif isinstance(v, bool):
                # type bool
                meta[1] = 3
                data = bytearray(1)
                data[0] = int(v)
            elif v is None:
                # None
                data = None
                meta[1] = 4
            else:
                raise ConfigError("Unsupported type {}".format(type(v)))
            meta[2] = sum(meta[:2])
            sector += meta
            sector += k.encode()
            # add data, if non zero / none
            if data is not None and len(data) > 0:
                sector += data
        sec_len = len(sector)
        if sec_len > 4000:
            raise ConfigError('config is too large')
        # Add padding - esp.flash_write() requires block to be modulo 4
        if sec_len % 4 != 0:
            sector += b'\xff' * (sec_len % 4)
        esp.flash_write(CONFIG_BLOCK * BLOCK_SIZE, sector)
        return len(sector)

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
