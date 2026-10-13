import argparse
import json
from pathlib import Path
from engine import scan


def main():
    parser = argparse.ArgumentParser(description='WebVulnScanner — isolated authorized lab')
    parser.add_argument('--url', default='http://127.0.0.1:5102/page?id=1')
    parser.add_argument('--scanners', nargs='+', default=['xss', 'sql', 'csrf', 'ssrf'])
    parser.add_argument('--output', type=Path)
    parser.add_argument('--summary', action='store_true')
    args = parser.parse_args()
    report = scan(args.url, args.scanners)
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.summary:
        print('WebVulnScanner — Nguyễn Phúc Thịnh — 2387700066')
        print('Target:', report['target'])
        print('Complete:', report['complete'], '| Findings:', report['count'])
        for finding in report['vulnerabilities']:
            print(f"{finding['type']} | {finding['risk']} | {finding['confidence']} | {finding['desc']}")
        for error in report['errors']:
            print(error)
    else:
        print(text)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding='utf-8')
    return 0 if report['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
