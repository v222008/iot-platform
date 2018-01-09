#!/usr/bin/env micropython
"""
WS2812 LED WiFi Enabled Controller for ESP8266
MIT license
(C) Konstantin Belyalov 2017-2018
"""

import network
import time
import tinyweb


# Temporary function to make debugging / testing easy
def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sta_if.connect('SSID', 'PWD')
        cnt = 0
        while not sta_if.isconnected():
            time.sleep(0.5)
            cnt += 1
            if cnt > 10:
                print("Unable to connect to wifi")
                break
    print('network config:', sta_if.ifconfig())


# Web Server
web = tinyweb.server.webserver()


# Index page - basically archive of all files :)
@web.route('/')
def index(req, resp):
    yield from resp.send_file('index_all.html.gz')


# --- main starts here ---

connect_wifi()


web.run(host='0.0.0.0', port=80)
