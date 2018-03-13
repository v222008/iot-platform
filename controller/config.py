"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""


class Mqtt():
    """MQTT Configuration"""

    def __init__(self):
        self.config = {'host': '', 'username': '', 'password': '', 'client_id': '',
                       'status_topic': '', 'control_topic': '', 'enabled': False}

    def config_get(self):
        return self.config

    def config_replace(self, cfg):
        self.config = cfg

    def config_merge(self, cfg):
        self.config.update(cfg)


class Http():
    """HTTP configuration, like username / password, endpoints, etc"""

    def __init__(self):
        self.config = {'username': '', 'password': '', 'enabled': False}

    def config_get(self):
        return self.config

    def config_replace(self, cfg):
        self.config = cfg

    def config_merge(self, cfg):
        self.config.update(cfg)


class Misc():
    """All other, non categorized params"""

    def __init__(self, device='Unknown'):
        self.config = {'device': device, 'configured': False}

    def configured(self):
        return self.config['configured']

    def config_get(self):
        return self.config

    def config_apply(self, cfg, merge=True):
        if merge:
            self.config.update(cfg)
        else:
            self.config = cfg
        self.config['configured'] = int(self.config['configured'])

    def config_replace(self, cfg):
        self.config_apply(cfg, False)

    def config_merge(self, cfg):
        self.config_apply(cfg)
