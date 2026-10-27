"""Tải và kiểm tra cấu hình luật JSON."""
import json
from pathlib import Path

SEVERITIES = {"error", "warning", "note"}

class SecurityRuleEngine:
    def __init__(self, rules):
        if not isinstance(rules, list):
            raise ValueError("rules phải là danh sách")
        seen = set()
        for rule in rules:
            if not isinstance(rule, dict) or not isinstance(rule.get("id"), str) or not rule["id"]:
                raise ValueError("mỗi rule cần id dạng chuỗi")
            if rule["id"] in seen:
                raise ValueError(f"rule id trùng: {rule['id']}")
            seen.add(rule["id"])
            if not isinstance(rule.get("enabled", True), bool):
                raise ValueError(f"{rule['id']}: enabled phải là boolean")
            if rule.get("severity", "warning") not in SEVERITIES:
                raise ValueError(f"{rule['id']}: severity không hợp lệ")
            if not isinstance(rule.get("description", ""), str):
                raise ValueError(f"{rule['id']}: description phải là chuỗi")
            if not isinstance(rule.get("calls", []), list) or any(not isinstance(x, str) for x in rule.get("calls", [])):
                raise ValueError(f"{rule['id']}: calls phải là danh sách chuỗi")
        self.rules = rules

    @classmethod
    def from_file(cls, path):
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"không đọc được rules: {exc}") from exc
        if not isinstance(data, dict) or data.get("version") != 1:
            raise ValueError("schema rules cần object version=1")
        return cls(data.get("rules"))

    def enabled_rules(self):
        return [rule for rule in self.rules if rule.get("enabled", True)]
