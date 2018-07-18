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
        if isinstance(hostname, str):
            self.hostname = hostname.encode()
        else:
            self.hostname = hostname
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
            # Print to console
            for m in self.buf[1:]:
                print(m.decode(), end='')
            print()
            # Send message, ignore any errors
            try:
                msg = b''.join(self.buf)
                self.socket.sendto(msg, self.addr)
            except Exception:
                pass
            # Reset buffer
            self.buf = [self.header]
        gc.collect()


def config_cb():
    pass


class RemoteLogging():
    def __init__(self, config):
        """Enable Remote Logging to rsyslog as well as to console
            Arguments:
                config - SimpleConfig (from utils/config.py)
        """
        config.add_param('remote_logging_on', False, callback=self.callback)
        config.add_param('remote_logging_ip', 'localhost')
        config.add_param('remote_logging_port', 514)
        self.cfg = config

    def callback(self):
        if self.cfg.remote_logging_on:
            # Enable remote logging
            self.stream = RemoteStream(self.cfg.hostname,
                                       self.cfg.remote_logging_ip,
                                       self.cfg.remote_logging_port)
            logging._stream = self.stream
            print('Remote logging enabled to {}:{}'.format(self.cfg.remote_logging_ip,
                                                           self.cfg.remote_logging_port))
        else:
            # Disable
            print('Remote logging disabled')
            logging._stream = sys.stderr
