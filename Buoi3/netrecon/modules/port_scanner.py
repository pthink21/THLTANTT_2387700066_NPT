import errno
import socket
import threading
import time


class RateLimiter:
    """Serializes start times, including banner probes and concurrent web requests."""
    def __init__(self, rate):
        self.rate = float(rate)
        if not 0.5 <= self.rate <= 100:
            raise ValueError('Rate must be 0.5-100 probes/second')
        self.lock = threading.Lock()
        self.next = 0.0

    def wait(self):
        with self.lock:
            now = time.perf_counter()
            delay = max(0, self.next - now)
            if delay:
                time.sleep(delay)
            self.next = time.perf_counter() + 1 / self.rate


class PortScanner:
    def __init__(self, limiter, audit, timeout=3):
        self.limiter, self.audit, self.timeout = limiter, audit, timeout

    def probe(self, address, port, protocol='tcp'):
        self.limiter.wait()
        started = time.monotonic()
        state, reason = 'filtered', 'timeout/no response'
        self.audit.write('probe_start', target=address, port=port, protocol=protocol)
        try:
            kind = socket.SOCK_STREAM if protocol == 'tcp' else socket.SOCK_DGRAM
            with socket.socket(socket.AF_INET, kind) as sock:
                sock.settimeout(self.timeout)
                if protocol == 'tcp':
                    sock.connect((address, port))
                    state, reason = 'open', 'TCP connection accepted'
                else:
                    sock.connect((address, port))
                    sock.send(b'NETRECON-LAB')
                    sock.recv(512)
                    state, reason = 'open', 'UDP response received'
        except (ConnectionRefusedError, ConnectionResetError):
            state, reason = 'closed', 'connection refused/reset'
        except socket.timeout:
            if protocol == 'udp':
                state, reason = 'open|filtered', 'UDP silence is inconclusive'
        except OSError as exc:
            if exc.errno in (errno.ECONNREFUSED, 10061):
                state, reason = 'closed', 'connection refused'
            else:
                reason = type(exc).__name__
        result = {'port': port, 'protocol': protocol, 'state': state, 'reason': reason,
                  'duration_ms': round((time.monotonic() - started) * 1000, 2)}
        self.audit.write('probe_result', target=address, **result)
        return result

    def scan(self, address, ports, protocol='tcp'):
        if protocol not in ('tcp', 'udp'):
            raise ValueError('Protocol must be tcp or udp')
        return [self.probe(address, port, protocol) for port in ports]
