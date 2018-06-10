"""
Utilities for ESP based devices
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import gc
import logging
import ujson as json


class ConfigError(Exception):
    pass


def validate_name(name):
    if name.startswith('_'):
        raise ConfigError('Name should not start with underscore')
    if ' ' in name:
        raise ConfigError('Spaces are not allowed in param name')


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

    def __init__(self, filename='config.json', autosave=True):
        """Create instance of generic configuration.
        Arguments:
            filename [opt]: Configuration filename.
            autoload [opt]: Read configuration immediately. Requires "section" to be defined.
            autosave [opt]: Enable configuration autosave immediately after changes have been made.
        """
        self._log = logging.getLogger('MQTT')
        self._filename = filename
        self._autosave = autosave
        self._validators = {}
        self._callbacks = {}
        self._group_callbacks = {}

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

    def get_params(self):
        res = {}
        for k, v in self.__dict__.items():
            if k.startswith('_'):
                continue
            res[k] = v
        return res

    def get_json(self):
        return json.dumps(self.get_params())

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
        with open(self._filename, 'rb') as f:
            cfg = json.load(f)
        # Verify config
        for name, value in cfg.items():
            validate_name(name)
            validate_value_type(value)
            self.validate_value(name, value)
        # Apply config
        for name, value in cfg.items():
            setattr(self, name, value)
        gc.collect()
        # Done, call callbacks for changed params
        self.run_callbacks(cfg.keys())

    def save(self):
        """Save config (all sections) into file."""
        with open(self._filename, 'wb') as f:
            f.write(self.get_json())
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

    def get(self, data=None):
        return self.get_json()

    def post(self, data):
        try:
            self.update(data)
        except Exception as e:
            return {'message': str(e)}, 400
        return {'message': 'succeed'}
