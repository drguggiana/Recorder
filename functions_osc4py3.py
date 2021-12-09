import osc4py3.as_allthreads as osc
from osc4py3 import oscbuildparse
import time


class OSCManager:

    def __init__(self):
        """Construct the object"""
        # initialize wait variable
        self.wait_var = {}

        # initialize the simple read
        self.simple_message = 0

        # Start up the OSC subfunctions
        osc.osc_startup()

    @staticmethod
    def stop():
        """Stop the OSC subfunctions"""
        osc.osc_terminate()

    def create_server(self, ip, port, name):
        """Create a server"""
        # create the server
        osc.osc_udp_server(ip, port, name)
        # register the wait for event pattern
        osc.osc_method('/release_wait', self.release_wait)
        # register the simple read
        osc.osc_method('/simple_read', self.simple_read)

    @staticmethod
    def bind(address, fct):
        """Register a custom function"""
        osc.osc_method(address, fct)

    @staticmethod
    def create_client(ip, port, name):
        """Create a client"""
        osc.osc_udp_client(ip, port, name)

    def wait_for_message(self, source):
        """Wait for a given message with a previously created server"""
        self.wait_var[source] = 0
        # stay here until the release message is received
        while self.wait_var[source] == 0:
            # wait for 10 ms and keep iterating
            time.sleep(0.01)
        # reset the variable once we exit the loop
        self.wait_var[source] = 0

    def release_wait(self, source):
        """Once called, release the wait"""
        self.wait_var[source] = 1

    @staticmethod
    def simple_send(name, address, message):
        """Send an integer message using the created client"""
        msg = oscbuildparse.OSCMessage(address, ',i', [message])
        osc.osc_send(msg, name)

    def simple_read(self, msg):
        """Read the value of a message and store in the instance"""
        self.simple_message = msg

    @staticmethod
    def send_release(name, source):
        """Message to release a given server in wait mode"""
        msg = oscbuildparse.OSCMessage('/release_wait', ',s', [source])
        osc.osc_send(msg, name)
