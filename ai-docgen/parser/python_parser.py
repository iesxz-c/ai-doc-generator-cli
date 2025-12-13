import os
from typing import Dict, List

from tree_sitter import Parser
from tree_sitter_python import language as python_language

try:
    from tree_sitter_languages import get_parser as get_ts_parser  # type: ignore
except ImportError:  # pragma: no cover
    get_ts_parser = None

from parser.base_parser import BaseParser


class PythonParser(BaseParser):
    """Tree-sitter based parser for Python files."""

    def __init__(self):
        self.parser = None
        if get_ts_parser:
            self.parser = get_ts_parser("python")
        else:
            candidate = Parser()
            if hasattr(candidate, "set_language"):
                candidate.set_language(python_language())
                self.parser = candidate

    def extensions(self) -> List[str]:
        return [".py"]

    def parse_file(self, path: str) -> Dict:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()

        try:
            if self.parser:
                tree = self.parser.parse(code.encode())
                root = tree.root_node

                imports = self._extract_imports(root, code)
                functions = self._extract_functions(root, code)
                classes = self._extract_classes(root, code)
                calls = self._extract_calls(root, code)

                ast_repr = root.sexp()
            else:
                # Fallback: stdlib ast parsing (no spans but keeps pipeline alive)
                import ast

                parsed = ast.parse(code)
                imports = [line.strip() for line in code.splitlines() if line.strip().startswith(("import ", "from "))]
                functions = []
                classes = []

                class FunctionVisitor(ast.NodeVisitor):
                    def visit_FunctionDef(self, node):  # type: ignore
                        functions.append({
                            "name": node.name,
                            "args": [a.arg for a in node.args.args],
                            "docstring": ast.get_docstring(node),
                            "span": None,
                        })
                        self.generic_visit(node)

                    def visit_AsyncFunctionDef(self, node):  # type: ignore
                        functions.append({
                            "name": node.name,
                            "args": [a.arg for a in node.args.args],
                            "docstring": ast.get_docstring(node),
                            "span": None,
                        })
                        self.generic_visit(node)

                    def visit_ClassDef(self, node):  # type: ignore
                        methods = []
                        for m in [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
                            methods.append({
                                "name": m.name,
                                "args": [a.arg for a in m.args.args],
                                "docstring": ast.get_docstring(m),
                                "span": None,
                            })
                        classes.append({
                            "name": node.name,
                            "docstring": ast.get_docstring(node),
                            "methods": methods,
                            "span": None,
                        })
                        self.generic_visit(node)

                FunctionVisitor().visit(parsed)
                calls = []
                ast_repr = "python-ast-fallback"
        except Exception as exc:  # pragma: no cover
            return {
                "file": os.path.abspath(path),
                "language": "python",
                "error": str(exc),
                "ast": None,
                "imports": [],
                "functions": [],
                "classes": [],
                "calls": [],
            }

        return {
            "file": os.path.abspath(path),
            "language": "python",
            "ast": ast_repr,
            "imports": imports,
            "functions": functions,
            "classes": classes,
            "calls": calls,
        }

    # ----------------- BASIC EXTRACTION HELPERS ---------------- #

    def _extract_imports(self, root, code: str) -> List[str]:
        imports: List[str] = []
        for node in root.children:
            if node.type in {"import_statement", "import_from_statement"}:
                imports.append(code[node.start_byte: node.end_byte].strip())
        return imports

    def _extract_functions(self, root, code: str) -> List[Dict]:
        functions: List[Dict] = []
        for node in root.children:
            if node.type == "function_definition":
                functions.append(self._parse_function(node, code))
        return functions

    def _extract_classes(self, root, code: str) -> List[Dict]:
        classes: List[Dict] = []
        for node in root.children:
            if node.type == "class_definition":
                classes.append(self._parse_class(node, code))
        return classes

    def _extract_calls(self, root, code: str) -> List[Dict]:
        calls: List[Dict] = []

        def _walk(node):
            if node.type == "call":
                target = None
                for child in node.children:
                    if child.type == "identifier":
                        target = code[child.start_byte: child.end_byte]
                        break
                calls.append({"target": target, "span": (node.start_point, node.end_point)})
            for child in node.children:
                _walk(child)

        _walk(root)
        return calls

    def _parse_function(self, node, code: str) -> Dict:
        name = self._extract_identifier(node, code)
        args = self._extract_args(node, code)
        doc = self._extract_docstring(node, code)

        return {
            "name": name,
            "args": args,
            "docstring": doc,
            "span": (node.start_point, node.end_point),
        }

    def _parse_class(self, node, code: str) -> Dict:
        name = self._extract_identifier(node, code)
        doc = self._extract_docstring(node, code)

        methods = []
        for child in node.children:
            if child.type == "function_definition":
                methods.append(self._parse_function(child, code))

        return {
            "name": name,
            "docstring": doc,
            "methods": methods,
            "span": (node.start_point, node.end_point),
        }

    # ------------------ LOW LEVEL NODE HELPERS ------------------ #

    def _extract_identifier(self, node, code: str):
        for child in node.children:
            if child.type == "identifier":
                return code[child.start_byte: child.end_byte]
        return None

    def _extract_args(self, node, code: str) -> List[str]:
        for child in node.children:
            if child.type == "parameters":
                text = code[child.start_byte: child.end_byte]
                text = text[1:-1].strip()  # remove parentheses
                if text:
                    return [p.strip() for p in text.split(",") if p.strip()]
        return []

    def _extract_docstring(self, node, code: str):
        for child in node.children:
            if child.type == "expression_statement":
                raw = code[child.start_byte: child.end_byte].strip()
                if raw.startswith('"""') or raw.startswith("'''"):
                    return raw.strip('"\'')
        return None
