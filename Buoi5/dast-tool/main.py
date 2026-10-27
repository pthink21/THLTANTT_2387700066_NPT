"""Chạy minh họa các thành phần DAST trên dữ liệu tổng hợp an toàn."""
import json
from memory_analyzer import MemoryAnalyzer
from runtime_monitor import RuntimeMonitor
from security_behavior_checker import SecurityBehaviorChecker
from virtual_sandbox import VirtualSandbox

def main():
    monitor=RuntimeMonitor(); monitor.start(); monitor.record("process.spawn",{"name":"python-demo"})
    memory=MemoryAnalyzer(); memory.start(); sandbox=VirtualSandbox().run_demo("memory-growth")
    events=monitor.events(); result={"sandbox":sandbox,"memory":memory.snapshot(),"events":events,"alerts":SecurityBehaviorChecker().check(events)}
    print(json.dumps(result,ensure_ascii=False,indent=2)); monitor.stop()
if __name__=="__main__": main()
