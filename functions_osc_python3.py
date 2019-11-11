from pythonosc import udp_client


def create_client(ip, port):
    """Create a client for the UDP transfer"""
    client = udp_client.SimpleUDPClient(ip, port)
    return client


def create_and_send(ip, port, address, msg):
    """Create a client and send a message"""
    client = create_client(ip, port)
    client.send_message(address, msg)
    return None
