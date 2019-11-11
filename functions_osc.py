from oscpy.client import OSCClient


def create_client(ip, port):
    """Create the OSC client"""
    return OSCClient(ip, port)


def create_and_send(ip, port, address, msg):
    """Create a client and send a message"""
    osc = OSCClient(ip, port)
    osc.send_message(address, msg)
