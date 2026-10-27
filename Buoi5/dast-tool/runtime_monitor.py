import threading
from datetime import datetime, timezone

class RuntimeMonitor:
    def __init__(self, max_events=500):
        self._events=[]; self._lock=threading.Lock(); self.max_events=max_events; self.started=False
    def start(self): self.started=True; return self.record("monitor.started",{"scope":"demo-process"})
    def stop(self):
        if self.started: self.record("monitor.stopped",{}); self.started=False
    def record(self, event_type, metadata=None):
        if not isinstance(event_type,str) or not event_type or len(event_type)>80: raise ValueError("event_type không hợp lệ")
        event={"timestamp":datetime.now(timezone.utc).isoformat(),"type":event_type,"metadata":metadata or {}}
        with self._lock:
            self._events.append(event); self._events=self._events[-self.max_events:]
        return event
    def events(self):
        with self._lock: return list(self._events)
