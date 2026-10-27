"""Nhận diện mẫu cấu trúc AST có rủi ro."""
import ast

def dotted_name(node):
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute):
        parent = dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""

class VulnPatternMatcher(ast.NodeVisitor):
    def __init__(self, rules):
        self.rules = rules
        self.matches = []
        self.interpolated_names = set()

    def visit_Assign(self, node):
        if isinstance(node.value, (ast.JoinedStr, ast.BinOp)):
            self.interpolated_names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        self.generic_visit(node)

    def visit_Call(self, node):
        name = dotted_name(node.func)
        for rule in self.rules:
            matched = name in rule.get("calls", [])
            if rule.get("sql_interpolation") and name.rsplit(".", 1)[-1] in {"execute", "executemany"}:
                matched = any(isinstance(arg, (ast.JoinedStr, ast.BinOp)) or
                              (isinstance(arg, ast.Name) and arg.id in self.interpolated_names)
                              for arg in node.args[:1])
            if rule["id"] == "PY-SHELL" and name in rule.get("calls", []):
                matched = any(k.arg == "shell" and isinstance(k.value, ast.Constant) and k.value.value is True for k in node.keywords)
            if matched:
                self.matches.append((rule, node.lineno, name))
        self.generic_visit(node)
