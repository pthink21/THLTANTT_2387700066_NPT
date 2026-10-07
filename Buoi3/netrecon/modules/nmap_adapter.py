import os
import ipaddress
import shutil
# Only a local executable with an argument list; shell is never used.
import subprocess  # nosec B404
from defusedxml import ElementTree as ET


class NmapAdapter:
    def __init__(self, audit):
        self.audit = audit
        self.binary = os.getenv('NMAP_PATH') or shutil.which('nmap')

    def scan(self, address, ports, rate, technique='connect'):
        address = str(ipaddress.IPv4Address(address))
        if not ports or len(ports) > 256 or any(type(p) is not int or not 1 <= p <= 65535 for p in ports):
            raise ValueError('Invalid Nmap ports')
        if not .5 <= float(rate) <= 100:
            raise ValueError('Invalid Nmap rate')
        if not self.binary:
            raise ValueError('Nmap unavailable; install Nmap or set NMAP_PATH')
        if technique not in ('connect', 'syn'):
            raise ValueError('Nmap technique must be connect or syn')
        args = [self.binary, '-sT' if technique == 'connect' else '-sS', '-Pn', '-n', '-sV',
                '--version-light', '--max-rate', str(rate), '--max-retries', '1', '--host-timeout', '30s',
                '-p', ','.join(map(str, ports)), '-oX', '-', address]
        self.audit.write('nmap_start', target=address, technique=technique, rate=rate)
        try:
            # The target is a pinned IPv4 literal, ports/rate/technique are bounded above.
            run = subprocess.run(args, capture_output=True, text=True, timeout=40, check=False)  # nosec B603
        except subprocess.TimeoutExpired as exc:
            self.audit.write('nmap_timeout', target=address)
            raise ValueError('Nmap timed out after 40 seconds') from exc
        if run.returncode:
            self.audit.write('nmap_error', target=address, returncode=run.returncode)
            raise ValueError('Nmap failed: ' + run.stderr[-500:])
        root = ET.fromstring(run.stdout)
        results = []
        for p in root.findall('.//host/ports/port'):
            service, state = p.find('service'), p.find('state')
            results.append({'port': int(p.attrib['portid']), 'protocol': p.attrib['protocol'],
                'state': state.attrib['state'], 'service': dict(service.attrib) if service is not None else {}})
        self.audit.write('nmap_result', target=address, ports=len(results))
        return results
