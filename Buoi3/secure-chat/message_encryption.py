"""Room keys are provisioned out-of-band; the relay never receives them."""
from cryptography.fernet import Fernet


class MessageEncryption:
    def __init__(self, key: bytes):
        self.cipher = Fernet(key)

    @staticmethod
    def generate_key():
        return Fernet.generate_key()

    def encrypt(self, message: str) -> str:
        return self.cipher.encrypt(message.encode('utf-8')).decode('ascii')

    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode('ascii')).decode('utf-8')
