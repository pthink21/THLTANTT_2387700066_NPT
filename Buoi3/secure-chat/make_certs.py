"""Create a lab CA, SAN server certificate, and distinct mTLS client identities."""
import argparse
import ipaddress
from datetime import datetime, timedelta, timezone
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID

BASE = Path(__file__).resolve().parent


def generate(output=BASE / 'certs'):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Certificate directory is not empty; refusing to replace identities')
    now = datetime.now(timezone.utc)
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    ca_name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'Nguyen Phuc Thinh 2387700066 Lab CA')])
    ca = (x509.CertificateBuilder().subject_name(ca_name).issuer_name(ca_name)
          .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
          .not_valid_before(now - timedelta(minutes=5)).not_valid_after(now + timedelta(days=3650))
          .add_extension(x509.BasicConstraints(ca=True, path_length=0), critical=True)
          .add_extension(x509.KeyUsage(False, False, False, False, False, True, True, False, False), critical=True)
          .sign(ca_key, hashes.SHA256()))

    def save(name, key, cert):
        folder = output / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / f'{name}.key').write_bytes(key.private_bytes(serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        (folder / f'{name}.crt').write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    save('ca', ca_key, ca)
    for name in ['server', 'alice', 'bob', 'charlie']:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'localhost' if name == 'server' else name)])
        builder = (x509.CertificateBuilder().subject_name(subject).issuer_name(ca_name)
                   .public_key(key.public_key()).serial_number(x509.random_serial_number())
                   .not_valid_before(now - timedelta(minutes=5)).not_valid_after(now + timedelta(days=365))
                   .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
                   .add_extension(x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH if name == 'server'
                                                        else ExtendedKeyUsageOID.CLIENT_AUTH]), critical=False))
        if name == 'server':
            builder = builder.add_extension(x509.SubjectAlternativeName([
                x509.DNSName('localhost'), x509.IPAddress(ipaddress.ip_address('127.0.0.1'))]), critical=False)
        save(name, key, builder.sign(ca_key, hashes.SHA256()))
    print(f'Created CA + server SAN + alice/bob/charlie client certificates: {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=BASE / 'certs')
    generate(parser.parse_args().output)
