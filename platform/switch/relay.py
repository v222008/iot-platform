"""
MIT license
(C) Konstantin Belyalov 2018
"""
import logging


log = logging.getLogger('RELAY')
onoff = ['off', 'on']


class Relay():
    def __init__(self, num, pin, config, web, mqtt):
        """Relay module - to operate with relays connected to GPIO
        Args:
            - num: relay number (1, 2, 3, etc)
            - pin: PIN where relay connected to
            - config: instance of config class
            - web: instance of tinyweb
            - mqtt: instance of tinymqtt
        """
        self.cfg = config
        self.pin = pin
        self.pin.init(pin.OUT)
        self.num = num
        # Turned off by default
        self.state = 0

        # MQTT
        self.mqtt = mqtt
        self.cfg.add_param('mqtt_topic_relay{}_status'.format(self.num), 'relay{}'.format(self.num))
        self.cfg.add_param('mqtt_topic_relay{}_control'.format(self.num), 'relay{}/set'.format(self.num),
                           callback=self.mqtt_config_changed,
                           group='mqtt_config')
        # Web endpoints
        web.add_resource(self, '/relay{}/on'.format(self.num), state=1)
        web.add_resource(self, '/relay{}/off'.format(self.num), state=0)

    def mqtt_config_changed(self):
        """Callback when mqtt control topic changed"""
        self.mqtt.subscribe(self.cfg.value('mqtt_topic_relay{}_control'.format(self.num)),
                            self.mqtt_control)

    def change_state(self, _state):
        self.state = int(_state)
        if self.state < 0 or self.state > 1:
            raise ValueError('Invalid state')
        self.pin.value(self.state)
        log.info('Relay{} turned {}'.format(self.num, onoff[self.state]))
        # publish update to mqtt
        self.mqtt.publish(self.cfg.value('mqtt_topic_relay{}_status'.format(self.num)),
                          str(self.state),
                          retain=True)

    def post(self, data, state):
        try:
            self.change_state(state)
            return {'message': 'OK'}
        except ValueError as e:
            return {'message': e}, 400
        except Exception as e:
            log.exc(e, "Unhandled exception")

    def get(self, data, state):
        return self.post(data, state)

    def mqtt_control(self, state):
        try:
            self.change_state(state)
        except ValueError as e:
            pass
        except Exception as e:
            log.exc(e, "Unhandled exception")
