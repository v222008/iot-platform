"""
Utilities for ESP based devices
MIT license
(C) Konstantin Belyalov 2017-2018
"""
import gc
import logging
import uio
import usocket as socket
import sys


class RemoteStream(uio.IOBase):
    def __init__(self, hostname, ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.hostname = hostname.encode()
        self.addr = socket.getaddrinfo(ip, port)[0][-1]
        self.header = b'\x3c\x31\x33\x34\x3eJan 11 11:11:11 ' + self.hostname + b' python: '
        self.buf = [self.header]

    def write(self, _msg):
        # Buffering message until '\n' received
        send = False
        if isinstance(_msg, str):
            if _msg != '\n':
                self.buf.append(_msg.encode())
            if _msg[-1] == '\n':
                send = True
        elif isinstance(_msg, bytes) or isinstance(_msg, bytearray):
            if _msg != b'\n':
                self.buf.append(bytes(_msg))
            if _msg[-1] == 10:
                send = True
        if send:
            # Send message
            msg = b''.join(self.buf)
            print(msg.decode())
            self.socket.sendto(msg, self.addr)
            # Reset buffer
            self.buf = [self.header]
            gc.collect()


def config_cb():
    pass


class RemoteLogging():
    def __init__(self, hostname, config):
        """Enable Remote Logging to rsyslog as well as to console
            Arguments:
                name - system name (e.g. esp-010101)
                config - SimpleConfig (from utils/config.py)
        """
        config.add_param('remote_logging_ip', '',
                         callback=self.callback,
                         group='rlogging')
        config.add_param('remote_logging_port', 0,
                         callback=self.callback,
                         group='rlogging')
        self.cfg = config
        self.hostname = hostname

    def callback(self):
        if self.cfg.remote_logging_port > 0 \
                and self.cfg.remote_logging_ip != '':
            # Enable remote logging
            self.stream = RemoteStream(self.hostname,
                                       self.cfg.remote_logging_ip,
                                       self.cfg.remote_logging_port)
            logging._stream = self.stream
        else:
            # Disable
            logging._stream = sys.stderr
