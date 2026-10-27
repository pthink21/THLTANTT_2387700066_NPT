"""Chỉ số heuristic, không phải chứng minh chất lượng hoặc bảo mật."""
import ast
from pathlib import Path

class CodeQualityChecker:
    BRANCHES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.ExceptHandler, ast.comprehension, ast.Match)
    NESTED = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try, ast.Match)

    def analyze_source(self, source, path="<memory>", findings=None):
        tree = ast.parse(source)
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                complexity = 1 + sum(isinstance(n, self.BRANCHES) for n in ast.walk(node))
                depth = self._depth(node)
                functions.append({"name":node.name,"line":node.lineno,"cyclomatic_complexity":complexity,
                                  "length_lines":(node.end_lineno or node.lineno)-node.lineno+1,"nested_depth":depth})
        imports = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)) and n.names}
        smells = len(findings or [])
        loc = max(1, len(source.splitlines()))
        return {"path":str(path),"functions":functions,"dependency_count":len(imports),
                "security_smell_count":smells,"security_smell_density_per_100_loc":round(smells*100/loc, 2)}

    def _depth(self, fn):
        maximum = 0
        def walk(node, depth):
            nonlocal maximum
            for child in ast.iter_child_nodes(node):
                d = depth + isinstance(child, self.NESTED)
                maximum = max(maximum, d); walk(child, d)
        walk(fn, 0); return maximum

    def analyze_file(self, path, findings=None):
        return self.analyze_source(Path(path).read_text(encoding="utf-8"), path, findings)
