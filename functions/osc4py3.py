import osc4py3.as_allthreads as osc
from osc4py3 import oscbuildparse
import time

# define the type dictionary for message encoding
type_dict = {
    'int': 'i',
    'float': 'f',
    'str': 's',
}


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
        osc.osc_method('/ReleaseWait', self.release_wait)
        # register the simple read
        osc.osc_method('/SimpleRead', self.simple_read)
        # register the printing method
        osc.osc_method('/Print', self.print_message)

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
        msg = oscbuildparse.OSCMessage('/ReleaseWait', ',s', [source])
        osc.osc_send(msg, name)

    @staticmethod
    def send_message(name, address, message):
        """Send a general message"""
        # parse the types of the message
        # iterate through the data in the message
        type_string = [type_dict[el.__class__.__name__] for el in message]
        type_string = ',' + ''.join(type_string)
        # encode the message
        msg = oscbuildparse.OSCMessage(address, type_string, message)
        # send it
        osc.osc_send(msg, name)

    @staticmethod
    def print_message(msg):
        """Print the message received right away"""
        print(msg)
