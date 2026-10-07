import socket


class BannerGrabber:
    def __init__(self, limiter, audit, timeout=.5):
        self.limiter, self.audit, self.timeout = limiter, audit, timeout

    def grab(self, address, port):
        self.limiter.wait()
        self.audit.write('banner_start', target=address, port=port)
        banner = ''
        try:
            with socket.create_connection((address, port), timeout=self.timeout) as sock:
                sock.settimeout(self.timeout)
                try:
                    data = sock.recv(4096)  # Greeting first: SSH, FTP, SMTP.
                except socket.timeout:
                    sock.sendall(b'HEAD / HTTP/1.0\r\nHost: localhost\r\nConnection: close\r\n\r\n')
                    data = sock.recv(4096)
                banner = data.decode('utf-8', errors='replace')
                banner = ''.join(c if c in '\r\n\t' or ord(c) >= 32 else '?' for c in banner)
        except OSError as exc:
            banner = f'No readable banner ({type(exc).__name__})'
        self.audit.write('banner_result', target=address, port=port, bytes=len(banner))
        return banner
