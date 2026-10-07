import socket
import ssl
import struct
import threading
import time
import pytest
from cryptography.fernet import InvalidToken
from client import SecureChatClient
from server import SecureChatServer
from make_certs import generate
from message_encryption import MessageEncryption
from room_manager import RoomManager
from connection_manager import ConnectionManager
from protocol import receive, send, MAX_FRAME


@pytest.fixture(scope='module')
def chat(tmp_path_factory):
    certs = tmp_path_factory.mktemp('pki') / 'certs'
    generate(certs)
    server = SecureChatServer(port=0, certs=certs)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    yield server, certs
    server.close()
    worker.join(timeout=2)


def test_unicode_encryption():
    cipher = MessageEncryption(MessageEncryption.generate_key())
    text = 'Nguyễn Phúc Thịnh — 2387700066'
    encrypted = cipher.encrypt(text)
    assert text not in encrypted
    assert cipher.decrypt(encrypted) == text


def test_wrong_key_rejected():
    a, b = [MessageEncryption(MessageEncryption.generate_key()) for _ in range(2)]
    with pytest.raises(InvalidToken):
        b.decrypt(a.encrypt('private'))


def test_tamper_rejected():
    cipher = MessageEncryption(MessageEncryption.generate_key())
    encrypted = cipher.encrypt('private')
    with pytest.raises(InvalidToken):
        cipher.decrypt(encrypted[:30] + ('A' if encrypted[30] != 'A' else 'B') + encrypted[31:])


def test_fragmented_frame():
    a, b = socket.socketpair()
    try:
        payload = b'{"type":"test"}'
        wire = struct.pack('!I', len(payload)) + payload
        def writer():
            for byte in wire:
                a.sendall(bytes([byte]))
        t = threading.Thread(target=writer)
        t.start()
        assert receive(b) == {'type': 'test'}
        t.join()
    finally:
        a.close()
        b.close()


def test_oversized_frame_rejected():
    a, b = socket.socketpair()
    try:
        a.sendall(struct.pack('!I', MAX_FRAME + 1))
        with pytest.raises(ValueError):
            receive(b)
    finally:
        a.close()
        b.close()


def test_two_way_tls_and_room_isolation(chat):
    server, certs = chat
    key = MessageEncryption.generate_key()
    a = SecureChatClient('alice', key, port=server.port, certs=certs)
    b = SecureChatClient('bob', key, port=server.port, certs=certs)
    c = SecureChatClient('charlie', key, port=server.port, certs=certs, room='private')
    try:
        assert a.ready['tls'] in ('TLSv1.2', 'TLSv1.3')
        a.send_message('Xin chào Bob')
        assert b.receive_message()['text'] == 'Xin chào Bob'
        b.send_message('Xin chào Alice')
        assert a.receive_message()['text'] == 'Xin chào Alice'
        c.sock.settimeout(.2)
        with pytest.raises(socket.timeout):
            c.receive_message()
    finally:
        a.close(); b.close(); c.close()
    for _ in range(50):
        if not server.connections.snapshot():
            break
        time.sleep(.01)
    assert not server.connections.snapshot()
    assert not server.rooms.listing()


def test_missing_client_cert_rejected(chat):
    server, certs = chat
    context = ssl.create_default_context(cafile=str(certs / 'ca/ca.crt'))
    with socket.create_connection(('127.0.0.1', server.port)) as raw:
        with pytest.raises((ssl.SSLError, ConnectionResetError, EOFError)):
            with context.wrap_socket(raw, server_hostname='localhost') as secured:
                send(secured, {'type': 'hello', 'name': 'alice'})
                receive(secured)


def test_wrong_hostname_rejected(chat):
    server, certs = chat
    context = ssl.create_default_context(cafile=str(certs / 'ca/ca.crt'))
    with socket.create_connection(('127.0.0.1', server.port)) as raw:
        with pytest.raises(ssl.SSLCertVerificationError):
            context.wrap_socket(raw, server_hostname='fake.example')


def test_untrusted_ca_rejected(chat):
    server, _ = chat
    context = ssl.create_default_context()
    with socket.create_connection(('127.0.0.1', server.port)) as raw:
        with pytest.raises(ssl.SSLCertVerificationError):
            context.wrap_socket(raw, server_hostname='localhost')


def test_certificate_identity_cannot_be_spoofed(chat):
    server, certs = chat
    context = ssl.create_default_context(cafile=str(certs / 'ca/ca.crt'))
    context.load_cert_chain(str(certs / 'alice/alice.crt'), str(certs / 'alice/alice.key'))
    with socket.create_connection(('127.0.0.1', server.port)) as raw:
        with context.wrap_socket(raw, server_hostname='localhost') as secured:
            send(secured, {'type': 'hello', 'name': 'bob', 'room': 'general'})
            with pytest.raises(EOFError):
                receive(secured)


def test_duplicate_connection_rejected():
    manager = ConnectionManager()
    manager.add('alice', None, 'alice')
    with pytest.raises(ValueError):
        manager.add('alice', None, 'alice')


def test_replayed_ciphertext_rejected():
    a, b = socket.socketpair()
    client = SecureChatClient.__new__(SecureChatClient)
    client.sock = b
    client.encryption = MessageEncryption(MessageEncryption.generate_key())
    client.seen = set()
    envelope = {'type': 'message', 'ciphertext': client.encryption.encrypt('hello')}
    try:
        send(a, envelope)
        assert client.receive_message()['text'] == 'hello'
        send(a, envelope)
        with pytest.raises(ValueError, match='Replayed'):
            client.receive_message()
    finally:
        a.close(); b.close()


def test_room_switch_and_cleanup():
    rooms = RoomManager()
    rooms.join('alice', 'general')
    rooms.join('alice', 'private')
    assert rooms.members('general') == set()
    assert rooms.members('private') == {'alice'}
    rooms.leave('alice')
    assert rooms.listing() == {}


@pytest.mark.parametrize('name', ['', '../etc', 'x' * 33])
def test_bad_room_rejected(name):
    with pytest.raises(ValueError):
        RoomManager().join('alice', name)
