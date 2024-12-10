import ssl
import socket
from typing import Tuple


class SSLConnectionHandler:
    @staticmethod
    def create_ssl_context(is_server: bool = False, certfile: str = None, keyfile: str = None):
        context = ssl.create_default_context(
            ssl.Purpose.CLIENT_AUTH if is_server else ssl.Purpose.SERVER_AUTH
        )

        if is_server and certfile and keyfile:
            context.load_cert_chain(certfile=certfile, keyfile=keyfile)

        return context

    @staticmethod
    def wrap_socket(sock: socket.socket, context: ssl.SSLContext, server_side: bool = False) -> ssl.SSLSocket:
        return context.wrap_socket(
            sock,
            server_side=server_side,
            do_handshake_on_connect=True
        )

    @staticmethod
    def create_secure_socket(host: str, port: int, is_server: bool = False) -> Tuple[socket.socket, ssl.SSLContext]:
        context = SSLConnectionHandler.create_ssl_context(is_server)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if is_server:
            sock.bind((host, port))
            sock.listen(5)

        return sock, context