import json, tempfile, unittest
from pathlib import Path
from sast_tool.ast_analyzer import ASTAnalyzer
from sast_tool.security_rule_engine import SecurityRuleEngine
from sast_tool.code_quality_checker import CodeQualityChecker
from sast_tool.sarif_reporter import SarifReporter

DEFAULT=Path(__file__).parents[1]/"rules/default_rules.json"
class SastTests(unittest.TestCase):
    def setUp(self): self.engine=SecurityRuleEngine.from_file(DEFAULT); self.analyzer=ASTAnalyzer(self.engine)
    def test_detects_eval_exec_shell_sql(self):
        src="import subprocess\neval(x)\nexec(x)\nsubprocess.run(x, shell=True)\nc.execute(f'SELECT * FROM t WHERE id={x}')"
        ids={f.rule_id for f in self.analyzer.analyze_source(src)}
        self.assertEqual(ids,{"PY-EVAL","PY-EXEC","PY-SHELL","PY-SQL-FSTRING"})
    def test_safe_source(self): self.assertEqual([],self.analyzer.analyze_source("print('safe')\nsubprocess.run(['echo','ok'])"))
    def test_syntax_error(self): self.assertEqual("PY-SYNTAX",self.analyzer.analyze_source("def x(:")[0].rule_id)
    def test_unreadable_path(self): self.assertEqual("PY-READ",self.analyzer.analyze_file("missing-file-hopefully.py")[0].rule_id)
    def test_invalid_schema(self):
        with self.assertRaises(ValueError): SecurityRuleEngine.from_file(__file__)
        with self.assertRaises(ValueError): SecurityRuleEngine([{"id":"x","severity":"critical"}])
    def test_disabled_rule(self):
        engine=SecurityRuleEngine([{"id":"E","enabled":False,"calls":["eval"],"severity":"warning"}])
        self.assertEqual([],ASTAnalyzer(engine).analyze_source("eval(x)"))
    def test_sarif_json(self):
        payload=SarifReporter.build(self.analyzer.analyze_source("eval(x)","demo.py"))
        decoded=json.loads(json.dumps(payload)); self.assertEqual("2.1.0",decoded["version"])
        self.assertEqual(1,decoded["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]["startLine"])
    def test_quality_metrics(self):
        q=CodeQualityChecker().analyze_source("import os\ndef f(x):\n if x:\n  while x:\n   break\n")
        self.assertEqual(1,q["dependency_count"]); self.assertEqual(3,q["functions"][0]["cyclomatic_complexity"])
        self.assertEqual(2,q["functions"][0]["nested_depth"])

if __name__=="__main__": unittest.main()
