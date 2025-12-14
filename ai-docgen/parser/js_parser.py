import os
from typing import Dict, List

from tree_sitter import Parser
from tree_sitter_javascript import language as js_language
from tree_sitter_typescript import language_typescript as ts_language

try:
    from tree_sitter_languages import get_parser as get_ts_parser  # type: ignore
except ImportError:  # pragma: no cover
    get_ts_parser = None

from parser.base_parser import BaseParser


class JavaScriptParser(BaseParser):
    """Tree-sitter based parser for JavaScript and TypeScript files."""

    def __init__(self):
        self.js_parser = None
        self.ts_parser = None

        if get_ts_parser:
            try:
                self.js_parser = get_ts_parser("javascript")
                self.ts_parser = get_ts_parser("typescript")
            except Exception:
                self.js_parser = None
                self.ts_parser = None
        else:
            try:
                js_candidate = Parser()
                ts_candidate = Parser()
                if hasattr(js_candidate, "set_language"):
                    js_candidate.set_language(js_language())
                    self.js_parser = js_candidate
                if hasattr(ts_candidate, "set_language"):
                    ts_candidate.set_language(ts_language())
                    self.ts_parser = ts_candidate
            except Exception:
                self.js_parser = None
                self.ts_parser = None

    def extensions(self) -> List[str]:
        return [".js", ".jsx", ".ts", ".tsx"]

    def parse_file(self, path: str) -> Dict:
        with open(path, "r", encoding="utf-8") as f:
            source = f.read()

        language = "typescript" if path.endswith((".ts", ".tsx")) else "javascript"

        parser = self._choose_parser(path)
        if parser:
            tree = parser.parse(source.encode())
            root = tree.root_node

            imports = self.extract_imports(source)
            functions = self.extract_functions(root, source)
            classes = self.extract_classes(root, source)
            calls = self.extract_calls(root, source)
            ast_repr = root.sexp()
        else:
            # Fallback: simple regex-based extraction for JS/TS
            imports = [line.strip() for line in source.splitlines() if line.strip().startswith(("import ", "export "))]
            functions = []
            classes = []
            calls = []
            for line in source.splitlines():
                stripped = line.strip()
                if stripped.startswith("function ") or stripped.startswith("const ") and "=>" in stripped:
                    name = stripped.split()[1].split("(")[0].replace("=", "")
                    functions.append({"name": name, "args": [], "docstring": None, "span": None})
                if stripped.startswith("class "):
                    name = stripped.split()[1].split("{")[0]
                    classes.append({"name": name, "methods": [], "docstring": None, "span": None})
            ast_repr = "js-ast-fallback"

        return {
            "file": os.path.abspath(path),
            "language": language,
            "ast": ast_repr,
            "imports": imports,
            "functions": functions,
            "classes": classes,
            "calls": calls,
        }

    # ============================================
    #                EXTRACTION
    # ============================================

    def extract_imports(self, code: str) -> List[str]:
        imports: List[str] = []
        for line in code.splitlines():
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("export "):
                imports.append(stripped)
        return imports

    def extract_functions(self, root, code: str) -> List[Dict]:
        functions: List[Dict] = []
        for node in root.children:
            if node.type in ("function_declaration", "method_definition", "arrow_function", "function"):  # type names vary slightly across grammars
                functions.append(self.parse_function(node, code))
        return functions

    def extract_classes(self, root, code: str) -> List[Dict]:
        classes: List[Dict] = []
        for node in root.children:
            if node.type == "class_declaration":
                classes.append(self.parse_class(node, code))
        return classes

    def extract_calls(self, root, code: str) -> List[Dict]:
        calls: List[Dict] = []

        def _walk(node):
            if node.type == "call_expression":
                name_node = node.child_by_field_name("function")
                target = self._text(name_node, code) if name_node else None
                calls.append({"target": target, "span": (node.start_point, node.end_point)})
            for child in node.children:
                _walk(child)

        _walk(root)
        return calls

    # ============================================
    #             PARSE INDIVIDUAL ITEMS
    # ============================================

    def parse_function(self, node, code: str) -> Dict:
        name_node = node.child_by_field_name("name") or node.child_by_field_name("identifier")
        params_node = node.child_by_field_name("parameters")

        name = self._text(name_node, code)
        params = self._text(params_node, code)

        args: List[str] = []
        if params.startswith("(") and ")" in params:
            raw = params[1:-1].strip()
            args = [p.strip() for p in raw.split(",") if p.strip()]

        return {
            "name": name,
            "args": args,
            "docstring": None,  # JS/TS lack inline docstrings
            "span": (node.start_point, node.end_point),
        }

    def parse_class(self, node, code: str) -> Dict:
        name_node = node.child_by_field_name("name")
        name = self._text(name_node, code)

        methods: List[Dict] = []
        body = node.child_by_field_name("body")
        if body:
            for child in body.children:
                if child.type == "method_definition":
                    methods.append(self.parse_method(child, code))

        return {
            "name": name,
            "methods": methods,
            "docstring": None,
            "span": (node.start_point, node.end_point),
        }

    def parse_method(self, node, code: str) -> Dict:
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")

        name = self._text(name_node, code)
        params = self._text(params_node, code)

        args: List[str] = []
        if params.startswith("(") and ")" in params:
            raw = params[1:-1].strip()
            args = [p.strip() for p in raw.split(",") if p.strip()]

        return {
            "name": name,
            "args": args,
            "docstring": None,
            "span": (node.start_point, node.end_point),
        }

    # ============================================
    #                HELPERS
    # ============================================

    def _text(self, node, code: str) -> str:
        if node is None:
            return ""
        return code[node.start_byte:node.end_byte]

    def _choose_parser(self, path: str):
        if path.endswith((".ts", ".tsx")):
            return self.ts_parser
        return self.js_parser
