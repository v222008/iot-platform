"""
MIT license
(C) Konstantin Belyalov 2017-2018
"""


class MQTTConfig():
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


class HTTPConfig():
    """ESP WiFi configuration for ESP8266 / ESP32"""

    def __init__(self):
        self.config = {'username': '', 'password': '', 'enabled': False}

    def config_get(self):
        return self.config

    def config_replace(self, cfg):
        self.config = cfg

    def config_merge(self, cfg):
        self.config.update(cfg)
