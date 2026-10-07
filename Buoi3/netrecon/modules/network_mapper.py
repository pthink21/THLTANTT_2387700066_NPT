import ipaddress


class NetworkMapper:
    def __init__(self, policy, scanner, audit):
        self.policy, self.scanner, self.audit = policy, scanner, audit

    def map(self, cidr, ports):
        network = ipaddress.ip_network(cidr, strict=False)
        if network.version != 4 or network.num_addresses > 16:
            raise ValueError('Discovery accepts IPv4 subnets with at most 16 addresses')
        addresses = [str(ip) for ip in network.hosts()]
        if not all(self.policy.permits(ip) for ip in addresses):
            raise ValueError('Subnet blocked by whitelist/blacklist')
        self.audit.write('map_start', subnet=str(network))
        nodes = []
        for address in addresses:
            open_ports = [p['port'] for p in self.scanner.scan(address, ports[:8]) if p['state'] == 'open']
            if open_ports:
                nodes.append({'id': address, 'open_ports': open_ports})
        return {'subnet': str(network), 'nodes': nodes,
                'edges': [{'source': 'scanner', 'target': n['id']} for n in nodes],
                'method': 'TCP discovery; a silent host may still be alive; edges show reachability, not physical topology'}
