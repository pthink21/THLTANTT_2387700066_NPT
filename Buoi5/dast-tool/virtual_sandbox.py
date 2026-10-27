"""Subprocess giới hạn thời gian trong thư mục tạm; không phải OS/container sandbox."""
import subprocess, sys, tempfile
from pathlib import Path

class VirtualSandbox:
    def __init__(self, timeout_seconds=3, output_limit=4000): self.timeout=timeout_seconds; self.output_limit=output_limit
    def run_demo(self, demo="hello"):
        if demo not in {"hello","memory-growth","suspicious-event"}: raise ValueError("demo không nằm trong allow-list")
        snippets={"hello":"print('sandbox demo: hello')","memory-growth":"data = bytearray(1024 * 128); print('allocated demo bytes:', len(data))","suspicious-event":"print('sandbox demo: suspicious-event')"}
        temp_path = None
        with tempfile.TemporaryDirectory(prefix="buoi5-sandbox-") as tmp:
            temp_path = Path(tmp)
            try:
                proc=subprocess.run([sys.executable,"-I","-c",snippets[demo]],cwd=tmp,capture_output=True,text=True,
                                    timeout=self.timeout,check=False)
                result = {"returncode":proc.returncode,"stdout":proc.stdout[-self.output_limit:],"stderr":proc.stderr[-self.output_limit:],"timed_out":False,"isolation":"temporary cwd + allow-list + timeout; same OS identity, no syscall/resource namespace isolation"}
            except subprocess.TimeoutExpired:
                result = {"returncode":None,"stdout":"","stderr":"","timed_out":True,"isolation":"temporary cwd + allow-list + timeout; same OS identity, no syscall/resource namespace isolation"}
        result["workdir_cleaned"] = not temp_path.exists()
        return result
