from pythonosc import udp_client
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer


def create_client(ip, port):
    """Create a client for the UDP transfer"""
    client = udp_client.SimpleUDPClient(ip, port)
    return client


def create_send_close(ip, port, address, msg):
    """Create a client, send a message and kill the client"""
    client = create_client(ip, port)
    client.send_message(address, msg)
    client._sock.close()
    return client


def create_blocking_server(ip, port, addr):
    """Creates a blocking server and waits until it's prompted to close"""
    def listener(address, *args):
        """Close the server upon a message"""
        if args[0] == 'close_server':
            # shutdown server before closing (must be threading server)
            server.shutdown()

    # initialize and configure the dispatcher
    dispatcher = Dispatcher()
    dispatcher.map(addr, listener)
    # initialize the server
    server = ThreadingOSCUDPServer((ip, port), dispatcher)
    # Blocks forever
    server.serve_forever()
    # close the server
    server.server_close()
