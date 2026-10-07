import json
import socket
import threading
import time
import pytest
from modules.filter_utils import TargetPolicy, parse_ports
from modules.audit import AuditLog
from modules.port_scanner import PortScanner, RateLimiter
from modules.banner_grabber import BannerGrabber
from modules.service_detector import ServiceDetector
from modules.vuln_checker import VulnChecker
from modules.network_mapper import NetworkMapper
from modules.email_sender import send_email
from engine import ReconEngine


@pytest.fixture
def audit(tmp_path):
    return AuditLog(tmp_path / 'audit.jsonl')


def test_port_ranges():
    assert parse_ports('22,80,8000-8002,80') == [22, 80, 8000, 8001, 8002]


@pytest.mark.parametrize('ports', ['0', '65536', '-1', 'a', '1-999', '', '80,,443'])
def test_bad_ports(ports):
    with pytest.raises(ValueError):
        parse_ports(ports)


def test_whitelist_and_blacklist():
    policy = TargetPolicy(['127.0.0.0/8'], ['127.0.0.2/32'])
    assert policy.resolve('localhost') == '127.0.0.1'
    for target in ('127.0.0.2', '192.0.2.1', '-sV'):
        with pytest.raises(ValueError):
            policy.resolve(target)


def test_rate_is_start_frequency():
    limiter = RateLimiter(20)
    started = time.perf_counter()
    for _ in range(4):
        limiter.wait()
    assert time.perf_counter() - started >= .145


def test_concurrent_rate_limit():
    limiter = RateLimiter(20)
    times = []
    def probe():
        limiter.wait()
        times.append(time.perf_counter())
    threads = [threading.Thread(target=probe) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()
    times.sort()
    assert times[-1] - times[0] >= .145


def test_tcp_open_closed_and_audit(audit):
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen()
    port = listener.getsockname()[1]
    scanner = PortScanner(RateLimiter(100), audit)
    assert scanner.probe('127.0.0.1', port)['state'] == 'open'
    listener.close()
    assert scanner.probe('127.0.0.1', port)['state'] == 'closed'
    records = [json.loads(x) for x in audit.path.read_text().splitlines()]
    assert len(records) == 4
    assert all('time' in x for x in records)


def test_udp_open_and_silence(audit):
    listener = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    listener.bind(('127.0.0.1', 0))
    port = listener.getsockname()[1]
    def echo():
        data, addr = listener.recvfrom(512)
        listener.sendto(data, addr)
    thread = threading.Thread(target=echo)
    thread.start()
    scanner = PortScanner(RateLimiter(100), audit, timeout=.1)
    assert scanner.probe('127.0.0.1', port, 'udp')['state'] == 'open'
    thread.join()
    assert scanner.probe('127.0.0.1', port, 'udp')['state'] == 'open|filtered'
    listener.close()


def test_banner_bounded(audit):
    listener = socket.socket()
    listener.bind(('127.0.0.1', 0))
    listener.listen()
    def greeting():
        conn, _ = listener.accept()
        with conn:
            conn.sendall(b'SSH-2.0-LabSSH_1.0\r\n' + b'x' * 10000)
    thread = threading.Thread(target=greeting)
    thread.start()
    text = BannerGrabber(RateLimiter(100), audit).grab('127.0.0.1', listener.getsockname()[1])
    thread.join()
    listener.close()
    assert text.startswith('SSH-2.0') and len(text) <= 4096


def test_http_and_ssh_fingerprint():
    detector = ServiceDetector()
    assert detector.detect(999, 'SSH-2.0-LabSSH_1.0')['name'] == 'ssh'
    result = detector.detect(999, 'HTTP/1.0 200 OK\r\nServer: LabHTTP/1.0\r\n')
    assert result['name'] == 'http' and result['version'] == 'LabHTTP/1.0'
    assert detector.detect(22, '')['name'] == 'unknown'


def test_cve_not_inferred_from_port():
    assert VulnChecker().check([{'port': 80, 'name': 'unknown', 'banner': '', 'evidence': 'none'}]) == []


def test_http_configuration_findings():
    results = VulnChecker().check([{'port': 8080, 'name': 'http', 'version': 'LabHTTP/1.0',
        'banner': 'HTTP/1.0 200 OK\r\nServer: LabHTTP/1.0\r\n', 'evidence': 'headers'}])
    assert len(results) == 2
    assert all(not x['confirmed_cve'] for x in results)


def test_mapper_rejects_large_and_blocked_subnets(audit):
    mapper = NetworkMapper(TargetPolicy(), PortScanner(RateLimiter(100), audit), audit)
    for cidr in ('127.0.0.0/24', '192.0.2.1/32'):
        with pytest.raises(ValueError):
            mapper.map(cidr, [80])


def test_email_header_injection_rejected(audit):
    with pytest.raises(ValueError):
        send_email('a@b.com\r\nBcc: x@y.com', 'report', audit)


def test_email_disabled_reported(audit, monkeypatch):
    monkeypatch.setenv('SMTP_MODE', 'disabled')
    assert send_email('thinh@localhost', 'report', audit)['status'] == 'not_configured'


def test_engine_busy_rejected(audit):
    engine = ReconEngine(log_path=audit.path)
    engine.lock.acquire()
    try:
        with pytest.raises(ValueError, match='running'):
            engine.run('127.0.0.1')
    finally:
        engine.lock.release()


def test_web_csrf_and_headers():
    from app import app
    client = app.test_client()
    response = client.get('/')
    assert response.status_code == 200
    assert response.headers['X-Content-Type-Options'] == 'nosniff'
    assert client.post('/scan', data={'target': '127.0.0.1'}).status_code == 403


def test_web_bad_target_with_valid_csrf():
    from app import app
    client = app.test_client()
    client.get('/')
    with client.session_transaction() as session:
        csrf = session['csrf']
    response = client.post('/scan', data={'csrf': csrf, 'target': '192.0.2.1', 'ports': '80'})
    assert response.status_code == 400 and b'whitelist' in response.data


def test_dns_rebinding_host_blocked():
    from app import app
    assert app.test_client().get('/', headers={'Host': 'attacker.example'}).status_code == 400


def test_nmap_xml_parsing_and_fixed_arguments(audit, monkeypatch):
    import subprocess
    from modules.nmap_adapter import NmapAdapter
    monkeypatch.setenv('NMAP_PATH', 'nmap')
    def run(args, **kwargs):
        assert args[-1] == '127.0.0.1'
        assert '-sT' in args and '--max-rate' in args
        assert kwargs.get('shell', False) is False
        return subprocess.CompletedProcess(args, 0, '<nmaprun><host><ports><port protocol="tcp" portid="8080"><state state="open"/><service name="http" product="LabHTTP" version="1.0"/></port></ports></host></nmaprun>', '')
    monkeypatch.setattr(subprocess, 'run', run)
    result = NmapAdapter(audit).scan('127.0.0.1', [8080], 10)
    assert result[0]['state'] == 'open' and result[0]['service']['version'] == '1.0'


def test_nmap_invalid_target_before_subprocess(audit, monkeypatch):
    from modules.nmap_adapter import NmapAdapter
    monkeypatch.setenv('NMAP_PATH', 'nmap')
    with pytest.raises(ValueError):
        NmapAdapter(audit).scan('--script=all', [80], 10)


def test_nmap_timeout_reported(audit, monkeypatch):
    import subprocess
    from modules.nmap_adapter import NmapAdapter
    monkeypatch.setenv('NMAP_PATH', 'nmap')
    def run(args, **kwargs):
        raise subprocess.TimeoutExpired(args, 40)
    monkeypatch.setattr(subprocess, 'run', run)
    with pytest.raises(ValueError, match='timed out'):
        NmapAdapter(audit).scan('127.0.0.1', [80], 10)


def test_xml_entities_rejected(audit, monkeypatch):
    import subprocess
    from modules.nmap_adapter import NmapAdapter
    from defusedxml.common import DefusedXmlException
    monkeypatch.setenv('NMAP_PATH', 'nmap')
    def run(args, **kwargs):
        return subprocess.CompletedProcess(args, 0, '<!DOCTYPE nmaprun [<!ENTITY x "unsafe">]><nmaprun>&x;</nmaprun>', '')
    monkeypatch.setattr(subprocess, 'run', run)
    with pytest.raises(DefusedXmlException):
        NmapAdapter(audit).scan('127.0.0.1', [80], 10)
