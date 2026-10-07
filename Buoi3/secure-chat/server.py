import argparse
import logging
import re
import socket
import ssl
import threading
import time
from pathlib import Path
from connection_manager import ConnectionManager
from room_manager import RoomManager
from protocol import receive

BASE = Path(__file__).resolve().parent
LOG = logging.getLogger('securechat')


class SecureChatServer:
    def __init__(self, host='127.0.0.1', port=8443, certs=BASE / 'certs'):
        certs = Path(certs)
        self.context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        self.context.minimum_version = ssl.TLSVersion.TLSv1_2
        self.context.load_cert_chain(str(certs / 'server/server.crt'), str(certs / 'server/server.key'))
        self.context.load_verify_locations(str(certs / 'ca/ca.crt'))
        self.context.verify_mode = ssl.CERT_REQUIRED
        self.connections = ConnectionManager()
        self.rooms = RoomManager()
        self.stop_event = threading.Event()
        self.slots = threading.BoundedSemaphore(64)
        self.listener = socket.socket()
        self.listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listener.bind((host, port))
        self.listener.listen(32)
        self.listener.settimeout(.3)
        self.port = self.listener.getsockname()[1]

    def serve_forever(self):
        LOG.info('LISTEN 127.0.0.1:%s mTLS required; relay has no room keys', self.port)
        while not self.stop_event.is_set():
            try:
                sock, addr = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            if not self.slots.acquire(blocking=False):
                sock.close()
                continue
            threading.Thread(target=self.handle, args=(sock, addr), daemon=True).start()

    def handle(self, raw, addr):
        name = None
        conn = None
        sock = raw
        try:
            raw.settimeout(5)
            sock = self.context.wrap_socket(raw, server_side=True)
            certificate = sock.getpeercert()
            identity = next(v for row in certificate['subject'] for k, v in row if k == 'commonName')
            if not re.fullmatch(r'[A-Za-z0-9_-]{1,32}', identity):
                raise ValueError('Invalid certificate identity')
            hello = receive(sock)
            if hello.get('type') != 'hello' or hello.get('name') != identity:
                raise ValueError('Name must match authenticated certificate identity')
            conn = self.connections.add(identity, sock, identity)
            name = identity
            room = hello.get('room', 'general')
            self.rooms.join(name, room)
            conn.send({'type': 'ready', 'name': name, 'room': room, 'tls': sock.version(), 'cipher': sock.cipher()[0]})
            LOG.info('AUTH %s room=%s TLS=%s', name, room, sock.version())
            sock.settimeout(300)
            last_message = 0.0
            while not self.stop_event.is_set():
                obj = receive(sock)
                kind = obj.get('type')
                if kind == 'join':
                    room = obj.get('room')
                    self.rooms.join(name, room)
                    conn.send({'type': 'joined', 'room': room})
                elif kind == 'rooms':
                    conn.send({'type': 'rooms', 'rooms': self.rooms.listing()})
                elif kind == 'message':
                    ciphertext = obj.get('ciphertext')
                    if not isinstance(ciphertext, str) or not 1 <= len(ciphertext) <= 16000:
                        raise ValueError('Invalid ciphertext')
                    if time.monotonic() - last_message < .05:
                        raise ValueError('Message rate exceeded')
                    last_message = time.monotonic()
                    envelope = {'type': 'message', 'sender': name, 'room': room, 'ciphertext': ciphertext}
                    for peer_name, peer in self.connections.snapshot().items():
                        if peer_name != name and peer_name in self.rooms.members(room):
                            try:
                                peer.send(envelope)
                            except OSError:
                                peer.sock.close()
                    LOG.info('RELAY sender=%s room=%s encrypted_bytes=%s', name, room, len(ciphertext))
                elif kind == 'quit':
                    break
                else:
                    raise ValueError('Unknown message type')
        except (OSError, EOFError, ValueError, KeyError, StopIteration) as exc:
            LOG.info('DISCONNECT/REJECT %s %s', name or addr, type(exc).__name__)
            if conn:
                try:
                    conn.send({'type': 'error', 'error': str(exc)})
                except OSError:
                    pass
        finally:
            if name:
                self.rooms.leave(name)
                self.connections.remove(name)
            sock.close()
            self.slots.release()

    def close(self):
        self.stop_event.set()
        self.listener.close()
        for conn in self.connections.snapshot().values():
            try:
                conn.sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            conn.sock.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--host', default='127.0.0.1')
    p.add_argument('--port', type=int, default=8443)
    args = p.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')
    server = SecureChatServer(args.host, args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
