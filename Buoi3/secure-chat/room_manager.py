import re
import threading


class RoomManager:
    def __init__(self, max_rooms=128):
        self.rooms = {}
        self.lock = threading.RLock()
        self.max_rooms = max_rooms

    def join(self, name, room):
        if not isinstance(room, str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,32}', room):
            raise ValueError('Room must contain 1-32 letters, digits, underscores or hyphens')
        with self.lock:
            if room not in self.rooms and len(self.rooms) >= self.max_rooms:
                raise ValueError('Room limit reached')
            self.leave(name)
            self.rooms.setdefault(room, set()).add(name)

    def leave(self, name):
        with self.lock:
            for room in list(self.rooms):
                self.rooms[room].discard(name)
                if not self.rooms[room]:
                    del self.rooms[room]

    def members(self, room):
        with self.lock:
            return set(self.rooms.get(room, set()))

    def listing(self):
        with self.lock:
            return {room: len(users) for room, users in self.rooms.items()}
