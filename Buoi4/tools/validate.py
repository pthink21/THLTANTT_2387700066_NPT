"""Run independent suites, preserve exact stdout and structured results."""
import json
from pathlib import Path
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parents[1]
EVIDENCE = BASE / 'evidence'
EVIDENCE.mkdir(exist_ok=True)
commands = {
    'scanner-unittest': [sys.executable, '-X', 'utf8', '-m', 'unittest', 'discover', '-s', 'web-vuln-scanner/tests', '-t', 'web-vuln-scanner', '-v'],
    'jwt-pytest': [sys.executable, '-X', 'utf8', '-m', 'pytest', 'jwt-security-tools/tests', '-q', '-c', 'jwt-security-tools/pytest.ini', '--basetemp', 'working/pytest-' + str(time.time_ns()), '--junitxml', 'evidence/jwt-tests.xml'],
    'bandit': [sys.executable, '-X', 'utf8', '-m', 'bandit', '-r', 'web-vuln-scanner', 'jwt-security-tools', 'lab_target.py', 'run_lab.py', '-x', 'web-vuln-scanner/tests,jwt-security-tools/tests', '-f', 'json', '-o', 'evidence/bandit.json'],
}
results = {}
for label, cmd in commands.items():
    p = subprocess.run(cmd, cwd=BASE, capture_output=True, encoding='utf-8')
    output = p.stdout + p.stderr
    (EVIDENCE / (label + '.txt')).write_text(output, encoding='utf-8')
    results[label] = {'exit_code': p.returncode}
    print(label, 'PASS' if p.returncode == 0 else 'FAIL')
    if p.returncode:
        print(output)
(EVIDENCE / 'validation.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
raise SystemExit(any(value['exit_code'] for value in results.values()))
