"""Xuất SARIF 2.1.0."""
import json
from pathlib import Path

LEVEL = {"error":"error", "warning":"warning", "note":"note"}
class SarifReporter:
    @staticmethod
    def build(findings):
        rules = {}
        results = []
        for f in findings:
            rid = f.rule_id; rules[rid] = {"id":rid,"shortDescription":{"text":f.message}}
            result = {"ruleId":rid,"level":LEVEL.get(f.severity,"warning"),"message":{"text":f.message},
                      "locations":[{"physicalLocation":{"artifactLocation":{"uri":str(Path(f.path).as_posix())},
                      "region":{"startLine":max(1,int(f.line))}}}]}
            results.append(result)
        return {"version":"2.1.0","$schema":"https://json.schemastore.org/sarif-2.1.0.json",
                "runs":[{"tool":{"driver":{"name":"buoi5-sast","rules":list(rules.values())}},"results":results}]}

    @classmethod
    def write(cls, findings, path):
        payload = cls.build(findings); Path(path).write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8"); return payload
