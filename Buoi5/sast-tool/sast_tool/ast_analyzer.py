"""AST analyzer; tuyệt đối không import hay thực thi file được quét."""
import ast
from dataclasses import asdict, dataclass
from pathlib import Path
from .security_rule_engine import SecurityRuleEngine
from .vuln_pattern_matcher import VulnPatternMatcher

@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    message: str
    path: str
    line: int

class ASTAnalyzer:
    def __init__(self, rules):
        self.engine = rules if isinstance(rules, SecurityRuleEngine) else SecurityRuleEngine(rules)

    def analyze_source(self, source, path="<memory>"):
        try: tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            return [Finding("PY-SYNTAX", "error", f"Lỗi cú pháp Python: {exc.msg}", str(path), exc.lineno or 1)]
        matcher = VulnPatternMatcher(self.engine.enabled_rules()); matcher.visit(tree)
        unique = {}
        for rule, line, name in matcher.matches:
            key = (rule["id"], line)
            unique[key] = Finding(rule["id"], rule.get("severity", "warning"), rule.get("description", name), str(path), line)
        return list(unique.values())

    def analyze_file(self, path):
        p = Path(path)
        try: source = p.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            return [Finding("PY-READ", "error", f"Không đọc được tệp: {exc}", str(p), 1)]
        return self.analyze_source(source, str(p))

    def scan(self, target):
        p = Path(target)
        files = sorted(p.rglob("*.py")) if p.is_dir() else [p]
        return [finding for file in files for finding in self.analyze_file(file)]

def finding_dict(finding): return asdict(finding)
