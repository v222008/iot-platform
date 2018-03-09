"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""


class MQTT():
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


class HTTP():
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

    def __init__(self):
        self.config = {'configured': False}

    def config_get(self):
        return self.config

    def config_replace(self, cfg):
        self.config = cfg

    def config_merge(self, cfg):
        self.config.update(cfg)
