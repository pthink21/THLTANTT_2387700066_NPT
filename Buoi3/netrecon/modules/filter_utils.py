import ipaddress
import socket


class TargetPolicy:
    def __init__(self, whitelist=('127.0.0.0/8',), blacklist=()):
        self.whitelist = [ipaddress.ip_network(x.strip(), strict=False) for x in whitelist if x.strip()]
        self.blacklist = [ipaddress.ip_network(x.strip(), strict=False) for x in blacklist if x.strip()]

    def permits(self, address):
        ip = ipaddress.ip_address(address)
        return (any(ip in net for net in self.whitelist)
                and not any(ip in net for net in self.blacklist))

    def resolve(self, target):
        if not isinstance(target, str) or not target or len(target) > 253 or target.startswith('-'):
            raise ValueError('Invalid target')
        try:
            addresses = {row[4][0] for row in socket.getaddrinfo(target, None, socket.AF_INET, socket.SOCK_STREAM)}
        except socket.gaierror as exc:
            raise ValueError('Cannot resolve target') from exc
        if not addresses or not all(self.permits(ip) for ip in addresses):
            raise ValueError('Target blocked by whitelist/blacklist')
        return sorted(addresses)[0]  # Pin the validated IP; never resolve again downstream.


def parse_ports(value):
    ports = set()
    for item in str(value).split(','):
        item = item.strip()
        if not item:
            raise ValueError('Empty port')
        if '-' in item:
            start, end = map(int, item.split('-'))
            if not 1 <= start <= end <= 65535 or end - start > 255:
                raise ValueError('Invalid or excessive port range')
            ports.update(range(start, end + 1))
        else:
            number = int(item)
            if not 1 <= number <= 65535:
                raise ValueError('Port must be 1-65535')
            ports.add(number)
    if len(ports) > 256:
        raise ValueError('Maximum 256 ports per request')
    return sorted(ports)
