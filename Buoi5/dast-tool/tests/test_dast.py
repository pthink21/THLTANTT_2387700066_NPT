import unittest
from app import create_app
from memory_analyzer import MemoryAnalyzer
from network_traffic_analyzer import NetworkTrafficAnalyzer
from runtime_monitor import RuntimeMonitor
from security_behavior_checker import SecurityBehaviorChecker
from virtual_sandbox import VirtualSandbox

class DastTests(unittest.TestCase):
    def test_runtime_events_and_cap(self):
        m=RuntimeMonitor(max_events=2); m.start(); m.record("one"); m.record("two"); self.assertEqual(2,len(m.events()))
        self.assertTrue(m.events()[0]["timestamp"].endswith("+00:00"))
    def test_memory_snapshot(self):
        m=MemoryAnalyzer(growth_threshold_bytes=0); m.start(); self.assertTrue(m.snapshot()["growth_suspected"])
        self.assertIn("không chứng minh",m.snapshot()["interpretation"])
    def test_network_scope_and_fallback(self):
        n=NetworkTrafficAnalyzer(); self.assertFalse(n.connections()["payload_collected"])
        with self.assertRaises(ValueError): n.record_connection("example.com",80,RuntimeMonitor())
    def test_behavior_alert(self):
        self.assertEqual(1,len(SecurityBehaviorChecker().check([{"type":"command.shell","timestamp":"now"}])))
    def test_sandbox_allowlist_and_cleanup(self):
        result=VirtualSandbox().run_demo(); self.assertEqual(0,result["returncode"]); self.assertTrue(result["workdir_cleaned"])
        with self.assertRaises(ValueError): VirtualSandbox().run_demo("arbitrary")
        self.assertIn("no syscall",result["isolation"])
    def test_api_health_event_validation_alert_status(self):
        client=create_app().test_client()
        self.assertEqual(200,client.get("/api/health").status_code)
        self.assertEqual(400,client.get("/api/events?limit=999").status_code)
        self.assertEqual(400,client.post("/api/demo/event",json={"type":"exec","cmd":"bad"}).status_code)
        self.assertEqual(201,client.post("/api/demo/event",json={"type":"command.shell"}).status_code)
        self.assertEqual(1,len(client.get("/api/alerts").json["alerts"]))
        self.assertEqual(200,client.get("/api/status").status_code)

if __name__=="__main__": unittest.main()
