# -*- coding: utf-8 -*-
#
# escpos/network.py
#
# Copyright 2015 Base4 Sistemas Ltda ME
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import select
import socket


DEFAULT_READ_BUFSIZE = 4096


class NetworkConnection(object):
    """Implements a simple network TCP/IP connection."""


    @staticmethod
    def create(setting):
        """Instantiate a :class:`NetworkConnection` object based on given
        host name and port number (eg. ``192.168.0.205:9100``).
        """
        host, port = setting.rsplit(':', 1)
        return NetworkConnection(host, int(port))


    def __init__(self, host, port,
            address_family=socket.AF_INET,
            socket_type=socket.SOCK_STREAM,
            select_timeout=1.0,
            read_buffer_size=DEFAULT_READ_BUFSIZE):

        super(NetworkConnection, self).__init__()

        self.socket = None
        self.host_name = host
        self.port_number = port
        self.address_family = address_family
        self.socket_type = socket_type
        self.select_timeout = select_timeout
        self.read_buffer_size = read_buffer_size


    def _raise_with_details(self, message, exctype=RuntimeError):
        raise exctype('{}: {!r} (host={!r}, port={!r}, '
                'socket address family={!r}, socket type={!r})'.format(
                        message,
                        self.socket,
                        self.host_name,
                        self.port_number,
                        self.address_family,
                        self.socket_type))


    def _reconnect(self):
        if self.socket is not None:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
        self.catch()


    def _assert_writable(self):
        # check if we can write to socket; if not, make one attempt to
        # reconnect before raising a run-time exception
        for tries in xrange(2):
            readable, writable, in_error = select.select(
                    [],
                    [self.socket,],
                    [self.socket,], self.select_timeout)
            if writable:
                break
            else:
                self._reconnect()
        else:
            self._raise_with_details('cannot read from socket')


    def _assert_readable(self):
        # check if we can read from socket; if not, make one attempt to
        # reconnect before raising a run-time exception
        for tries in xrange(2):
            readable, writable, in_error = select.select(
                    [self.socket,],
                    [],
                    [self.socket,], self.select_timeout)
            if readable:
                break
            else:
                self._reconnect()
        else:
            self._raise_with_details('cannot read from socket')


    def catch(self):
        self.socket = socket.socket(self.address_family, self.socket_type)
        self.socket.connect((self.host_name, self.port_number))


    def write(self, data):
        self._assert_writable()
        totalsent = 0
        while totalsent < len(data):
            sent = self.socket.send(data[totalsent:])
            if sent == 0:
                self._raise_with_details('socket connection broken')
            totalsent += sent


    def read(self):
        try:
            self._assert_readable()
            return self.socket.recv(self.read_buffer_size)
        except:
            return ''
