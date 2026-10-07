"""Length-prefixed JSON avoids TCP packet boundary assumptions."""
import json
import struct

MAX_FRAME = 65536


def exact(sock, size):
    chunks = bytearray()
    while len(chunks) < size:
        data = sock.recv(size - len(chunks))
        if not data:
            raise EOFError('Connection closed')
        chunks.extend(data)
    return bytes(chunks)


def receive(sock):
    length = struct.unpack('!I', exact(sock, 4))[0]
    if not 0 < length <= MAX_FRAME:
        raise ValueError('Invalid frame length')
    obj = json.loads(exact(sock, length))
    if not isinstance(obj, dict):
        raise ValueError('Frame must be an object')
    return obj


def send(sock, obj):
    data = json.dumps(obj, ensure_ascii=False).encode('utf-8')
    if len(data) > MAX_FRAME:
        raise ValueError('Frame too large')
    sock.sendall(struct.pack('!I', len(data)) + data)
