"""Stage only source, reports and approved screenshots into the target clone."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

BASE = Path(__file__).resolve().parents[1]
CLONE = BASE / 'working/publish'
TARGET = 'https://github.com/pthink21/THLTANTT_2387700066_NPT.git'
remote = subprocess.check_output(['git', '-C', str(CLONE), 'remote', 'get-url', 'origin'], text=True).strip()
if remote != TARGET:
    raise RuntimeError('Repository đích không đúng')

root_files = ['.gitignore', 'README.md', 'REPORT.md', 'requirements.txt', 'requirements-dev.txt',
              'requirements-lock.txt', 'lab_target.py', 'run_lab.py']
source_dirs = ['web-vuln-scanner', 'jwt-security-tools', 'tools', 'evidence', 'screenshots']
excluded = {'__pycache__', '.pytest_cache', '.venv', 'working', 'runtime'}
files = [BASE / name for name in root_files]
for directory in source_dirs:
    files.extend(file for file in (BASE / directory).rglob('*') if file.is_file()
                 and not any(part in excluded for part in file.relative_to(BASE).parts))

secrets = []
key_file = BASE / 'runtime/jwt-key.txt'
if key_file.exists():
    secrets.append(key_file.read_text(encoding='utf-8').strip())
token_file = BASE / 'runtime/tokens.json'
if token_file.exists():
    secrets.extend(json.loads(token_file.read_text(encoding='utf-8')).values())
issues = []
jwt_pattern = re.compile(r'eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}')
text_count = 0
for file in files:
    if file.suffix.lower() in {'.py','.txt','.md','.json','.jsonl','.xml','.ini','.html'} or file.name == '.gitignore':
        text_count += 1
        value = file.read_text(encoding='utf-8')
        if any(secret and secret in value for secret in secrets) or jwt_pattern.search(value):
            issues.append(str(file.relative_to(BASE)))
if issues:
    raise RuntimeError({'secret_or_token_found_in': issues})

manifest = json.loads((BASE / 'evidence/screenshot-manifest.json').read_text(encoding='utf-8'))
for entry in manifest:
    data = (BASE / 'screenshots' / entry['file']).read_bytes()
    if hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise RuntimeError('Screenshot manifest không khớp')
if len(manifest) != 15:
    raise RuntimeError('Thiếu ảnh')

review = {'target': TARGET, 'text_files_checked': text_count,
          'runtime_secrets_found': 0, 'full_jwt_strings_found': 0,
          'screenshots_verified': len(manifest),
          'excluded': sorted(excluded), 'status': 'PASS'}
review_file = BASE / 'evidence/publication-review.json'
review_file.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding='utf-8')
if review_file not in files:
    files.append(review_file)
destination = CLONE / 'Buoi4'
for source in files:
    dest = destination / source.relative_to(BASE)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)

readme = CLONE / 'README.md'
value = readme.read_text(encoding='utf-8')
if '## Buổi 4 — Bảo mật Web App và API' not in value:
    value += '''

---

## Buổi 4 — Bảo mật Web App và API

**Nguyễn Phúc Thịnh — MSSV 2387700066.** WebVulnScanner (XSS, SQLi, CSRF, SSRF) và JWTSecure (JWT validation, offline wordlist test, OAuth Code + PKCE, token rotation/revocation, API gateway).

Kết quả thực hành: **60/60 test đạt**, kiểm thử HTTP và Chrome đạt; **15 ảnh thao tác thật gồm 7 ảnh Windows CMD**. Khóa/token runtime được loại khỏi Git.

📁 [Buoi4](Buoi4) · 📖 [Hướng dẫn và ảnh](Buoi4/README.md) · 📝 [Báo cáo](Buoi4/REPORT.md)

![Lab 04 — WebVulnScanner](Buoi4/screenshots/08-web-scanner.png)
'''
    readme.write_text(value, encoding='utf-8')
print(json.dumps(review, ensure_ascii=False, indent=2))
print('Prepared', len(files), 'Lab 04 files and updated repository README.')
