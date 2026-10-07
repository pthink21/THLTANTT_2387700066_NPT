import argparse
import socket
import ssl
import threading
from pathlib import Path
from cryptography.fernet import InvalidToken
from message_encryption import MessageEncryption
from protocol import send, receive

BASE = Path(__file__).resolve().parent


class SecureChatClient:
    def __init__(self, name, key, host='localhost', port=8443, room='general', certs=BASE / 'certs'):
        self.name = name
        self.room = room
        self.encryption = MessageEncryption(key)
        certs = Path(certs)
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=str(certs / 'ca/ca.crt'))
        context.minimum_version = ssl.TLSVersion.TLSv1_2
        context.load_cert_chain(str(certs / name / f'{name}.crt'), str(certs / name / f'{name}.key'))
        raw = socket.create_connection((host, port), timeout=5)
        try:
            self.sock = context.wrap_socket(raw, server_hostname=host)
            send(self.sock, {'type': 'hello', 'name': name, 'room': room})
            self.ready = receive(self.sock)
            if self.ready.get('type') != 'ready':
                raise ValueError(self.ready)
        except Exception:
            raw.close()
            raise
        self.sock.settimeout(300)
        self.seen = set()

    def send_message(self, message):
        send(self.sock, {'type': 'message', 'ciphertext': self.encryption.encrypt(message)})

    def receive_message(self):
        obj = receive(self.sock)
        if obj.get('type') == 'message':
            ciphertext = obj['ciphertext']
            if ciphertext in self.seen:
                raise ValueError('Replayed message rejected')
            text = self.encryption.decrypt(ciphertext)
            self.seen.add(ciphertext)
            if len(self.seen) > 10000:
                raise ValueError('Replay cache full; reconnect to start a new session')
            obj['text'] = text
        return obj

    def join(self, room, key):
        self.encryption = MessageEncryption(key)
        self.room = room
        send(self.sock, {'type': 'join', 'room': room})

    def close(self):
        try:
            send(self.sock, {'type': 'quit'})
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        self.sock.close()


def main():
    p = argparse.ArgumentParser(description='mTLS + room E2EE chat')
    p.add_argument('--name', required=True, choices=['alice', 'bob', 'charlie'])
    p.add_argument('--host', default='localhost')
    p.add_argument('--port', type=int, default=8443)
    p.add_argument('--room', default='general')
    p.add_argument('--key-file', type=Path, required=True)
    args = p.parse_args()
    client = SecureChatClient(args.name, args.key_file.read_bytes().strip(), args.host, args.port, args.room)
    print('CONNECTED', client.ready, '\nCommands: /rooms, /join ROOM KEY_FILE, /quit')

    def reader():
        try:
            while True:
                obj = client.receive_message()
                print(f"\n[{obj.get('room', '')}] {obj.get('sender', 'server')}: {obj.get('text', obj)}")
        except (OSError, EOFError, InvalidToken, ValueError) as exc:
            print('Receive ended:', type(exc).__name__)

    threading.Thread(target=reader, daemon=True).start()
    try:
        while True:
            text = input('> ')
            if text == '/quit':
                break
            if text == '/rooms':
                send(client.sock, {'type': 'rooms'})
            elif text.startswith('/join '):
                _, room, filename = text.split(maxsplit=2)
                client.join(room, Path(filename).read_bytes().strip())
            else:
                client.send_message(text)
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        client.close()


if __name__ == '__main__':
    main()
