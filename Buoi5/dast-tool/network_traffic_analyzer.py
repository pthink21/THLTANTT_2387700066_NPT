import socket

class NetworkTrafficAnalyzer:
    """Theo dõi metadata socket được ứng dụng demo báo về; không sniff gói tin."""
    def __init__(self): self.available=True
    def connections(self):
        try:
            rows=[]
            for item in socket.getaddrinfo("localhost",None):
                rows.append({"family":str(item[0]),"socket_type":str(item[1]),"protocol":str(item[2]),"host":"localhost"})
            return {"available":True,"source":"getaddrinfo metadata demo","connections":rows[:20],"payload_collected":False}
        except OSError as exc:
            self.available=False; return {"available":False,"source":"unavailable","connections":[],"error":str(exc),"payload_collected":False}
    def record_connection(self, host, port, event_sink):
        if host not in {"127.0.0.1","localhost","::1"} or not isinstance(port,int) or not 1<=port<=65535:
            raise ValueError("chỉ cho phép endpoint loopback hợp lệ")
        return event_sink.record("network.connection.metadata",{"host":host,"port":port})
