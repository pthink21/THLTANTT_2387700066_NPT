import threading
from dataclasses import dataclass, field
from protocol import send


@dataclass
class Connection:
    name: str
    sock: object
    identity: str
    lock: object = field(default_factory=threading.Lock)

    def send(self, obj):
        with self.lock:
            send(self.sock, obj)


class ConnectionManager:
    def __init__(self, capacity=64):
        self.clients = {}
        self.lock = threading.RLock()
        self.capacity = capacity

    def add(self, name, sock, identity):
        with self.lock:
            if name in self.clients or len(self.clients) >= self.capacity:
                raise ValueError('Duplicate identity or server capacity reached')
            connection = Connection(name, sock, identity)
            self.clients[name] = connection
            return connection

    def remove(self, name):
        with self.lock:
            return self.clients.pop(name, None)

    def snapshot(self):
        with self.lock:
            return dict(self.clients)
