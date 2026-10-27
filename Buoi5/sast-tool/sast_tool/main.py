import argparse, json, sys
from pathlib import Path
from .ast_analyzer import ASTAnalyzer
from .security_rule_engine import SecurityRuleEngine
from .sarif_reporter import SarifReporter
from .code_quality_checker import CodeQualityChecker

def main(argv=None):
    parser=argparse.ArgumentParser(description="Quét SAST Python bằng AST; không thực thi mã")
    parser.add_argument("target"); parser.add_argument("--rules",default=str(Path(__file__).parents[1]/"rules/default_rules.json"))
    parser.add_argument("--sarif"); parser.add_argument("--quality",action="store_true")
    args=parser.parse_args(argv)
    try:
        engine=SecurityRuleEngine.from_file(args.rules); analyzer=ASTAnalyzer(engine); findings=analyzer.scan(args.target)
        for f in findings: print(f"{f.path}:{f.line}: {f.severity.upper()} {f.rule_id}: {f.message}")
        print(f"Tổng: {len(findings)} phát hiện")
        if args.sarif: SarifReporter.write(findings,args.sarif); print(f"SARIF: {args.sarif}")
        if args.quality:
            paths=Path(args.target).rglob("*.py") if Path(args.target).is_dir() else [Path(args.target)]
            for p in paths:
                fs=analyzer.analyze_file(p); print(json.dumps(CodeQualityChecker().analyze_file(p,fs),ensure_ascii=False))
        return 1 if findings else 0
    except (OSError,ValueError) as exc: print(f"Lỗi: {exc}",file=sys.stderr); return 2

if __name__=="__main__": raise SystemExit(main())
