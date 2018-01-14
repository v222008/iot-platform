#!/usr/bin/env micropython
"""
WS2812 LED WiFi Enabled Controller for ESP8266
MIT license
(C) Konstantin Belyalov 2017-2018
"""

import tinyweb
from utils.wifi import wifi_config
from utils.config import generic_config


class led_test():
    """API to test LED strip connection"""

    def put(self, data):
        print(data)
        return {'message': 'success'}


# Web Server
web = tinyweb.server.webserver()


# Index page - basically archive of all files :)
@web.route('/')
def index(req, resp):
    resp.add_header('Content-Encoding', 'gzip')
    yield from resp.send_file('index_all.html.gz', content_type='text/html')


# --- main starts here ---
wconfig = wifi_config()
config = generic_config([('wifi', wconfig)])

# Add RestAPI resources
# web.add_resource(led_test, '/v1/test')
web.add_resource(config, '/v1/config')
web.add_resource(wconfig, '/v1/wifi/scan')

web.run(host='0.0.0.0', port=8081)
