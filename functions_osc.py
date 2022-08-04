from oscpy.client import OSCClient
from oscpy.server import OSCThreadServer


def create_client(ip, port):
    """Create the OSC client"""
    return OSCClient(ip, port)


def create_and_send(ip, port, address, msg):
    """Create a client and send a message"""
    osc = OSCClient(ip, port)
    osc.simple_send(address, msg)


def create_server():
    return OSCThreadServer()

