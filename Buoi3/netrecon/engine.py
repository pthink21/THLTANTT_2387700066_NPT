import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
from modules.audit import AuditLog
from modules.filter_utils import TargetPolicy, parse_ports
from modules.port_scanner import PortScanner, RateLimiter
from modules.banner_grabber import BannerGrabber
from modules.service_detector import ServiceDetector
from modules.vuln_checker import VulnChecker
from modules.network_mapper import NetworkMapper
from modules.nmap_adapter import NmapAdapter
from modules.email_sender import send_email

BASE = Path(__file__).resolve().parent
load_dotenv(BASE / '.env')
MODES = ('scan', 'service', 'banner', 'map', 'vuln', 'all')


class ReconEngine:
    def __init__(self, policy=None, log_path=None):
        self.policy = policy or TargetPolicy(os.getenv('WHITELIST', '127.0.0.0/8').split(','),
                                              os.getenv('BLACKLIST', '').split(','))
        self.audit = AuditLog(log_path or BASE / 'logs/netrecon.jsonl')
        self.lock = threading.Lock()

    def run(self, target, ports='22,80,443', mode='all', protocol='tcp', rate=10,
            subnet=None, technique='connect', email=''):
        if not self.lock.acquire(blocking=False):
            raise ValueError('A scan is running; retry after it finishes')
        try:
            return self._run(target, ports, mode, protocol, rate, subnet, technique, email)
        except (ValueError, OSError) as exc:
            self.audit.write('request_rejected', reason=type(exc).__name__)
            raise
        finally:
            self.lock.release()

    def _run(self, target, ports, mode, protocol, rate, subnet, technique, email):
        if mode not in MODES or protocol not in ('tcp', 'udp') or technique not in ('connect', 'nmap-connect', 'syn'):
            raise ValueError('Invalid mode, protocol or technique')
        address = self.policy.resolve(target)
        numbers = parse_ports(ports)
        limiter = RateLimiter(rate)
        scanner = PortScanner(limiter, self.audit)
        self.audit.write('scan_start', target=address, ports=numbers, mode=mode, protocol=protocol, rate=rate)
        report = {'student': 'NGUYỄN PHÚC THỊNH', 'student_id': '2387700066',
                  'time': datetime.now(timezone.utc).isoformat(), 'target': target, 'address': address,
                  'mode': mode, 'protocol': protocol, 'rate': float(rate), 'technique': technique,
                  'ports': [], 'services': [], 'findings': [], 'network': None}
        if technique != 'connect' and protocol != 'tcp':
            raise ValueError('Nmap techniques in this app require TCP')
        if technique == 'connect':
            report['ports'] = scanner.scan(address, numbers, protocol)
        else:
            report['ports'] = NmapAdapter(self.audit).scan(address, numbers, float(rate),
                                      'syn' if technique == 'syn' else 'connect')
        opened = [p['port'] for p in report['ports'] if p['state'] == 'open']
        if protocol == 'tcp' and mode in ('all', 'service', 'banner', 'vuln'):
            grabber, detector = BannerGrabber(limiter, self.audit), ServiceDetector()
            for port in opened:
                banner = grabber.grab(address, port)
                report['services'].append({'port': port, 'banner': banner, **detector.detect(port, banner)})
        if mode in ('all', 'vuln'):
            report['findings'] = VulnChecker().check(report['services'])
        if mode in ('all', 'map'):
            report['network'] = NetworkMapper(self.policy, scanner, self.audit).map(subnet or address + '/32', numbers)
        report['email'] = send_email(email, json.dumps(report, ensure_ascii=False, indent=2), self.audit)
        self.audit.write('scan_complete', target=address, open_ports=opened, findings=len(report['findings']))
        return report
