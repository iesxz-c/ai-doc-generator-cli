import argparse
import os
from pathlib import Path
from typing import List, Optional

# Load environment variables from .env file
try:
	from dotenv import load_dotenv  # type: ignore
	load_dotenv()
except ImportError:
	pass

from docs_generator.markdown_builder import MarkdownBuilder
from git_analyzer.git_history import describe_repo
from graph.knowledge_graph import build_graph, to_mermaid
from parser import JavaScriptParser, PythonParser
from summarizer.llm_summarizer import LLMSummarizer


def parse_code(repo_path: str):
	py_parser = PythonParser()
	js_parser = JavaScriptParser()

	parsed: List[dict] = []
	parsed.extend(py_parser.walk_directory(repo_path))
	parsed.extend(js_parser.walk_directory(repo_path))
	return parsed


def normalize_paths(parsed_files: List[dict], repo_path: str) -> List[dict]:
	"""Convert absolute file paths to repo-relative for cleaner output and graphs."""
	base = Path(repo_path).resolve()
	for info in parsed_files:
		try:
			rel = Path(info.get("file", "")).resolve().relative_to(base)
		except Exception:
			rel = Path(os.path.relpath(info.get("file", ""), base))
		info["file"] = str(rel).replace("\\", "/")
	return parsed_files


def load_gitignore(repo_path: str) -> Optional[str]:
	path = Path(repo_path) / ".gitignore"
	if path.exists():
		return path.read_text(encoding="utf-8")
	return None


def collect_stats(parsed_files: List[dict]) -> dict:
	files = len(parsed_files)
	functions = sum(len(f.get("functions", [])) for f in parsed_files)
	classes = sum(len(f.get("classes", [])) for f in parsed_files)
	imports = sum(len(f.get("imports", [])) for f in parsed_files)
	return {
		"files": files,
		"functions": functions,
		"classes": classes,
		"imports": imports,
	}


def build_folder_tree(root: str, max_depth: int = 4) -> str:
	"""Create a simple folder tree (excludes common noise)."""
	exclude = {".git", "__pycache__", ".mypy_cache", ".ruff_cache", "node_modules", "venv", "build"}
	root_path = Path(root).resolve()
	lines: List[str] = []

	for dirpath, dirnames, filenames in os.walk(root_path):
		rel = Path(dirpath).resolve().relative_to(root_path)
		depth = len(rel.parts)
		if depth > max_depth:
			dirnames[:] = []
			continue
		dirnames[:] = [d for d in dirnames if d not in exclude]
		indent = "    " * depth
		name = rel.name if rel.name else "."
		lines.append(f"{indent}{name}/")
		for f in sorted(filenames):
			if f.startswith('.'):
				continue
			lines.append(f"{indent}    {f}")

	return "\n".join(lines)


def build_run_instructions(parsed_files: List[dict]) -> List[dict]:
	"""Generate run instructions and dependency info for each file."""
	instructions: List[dict] = []
	
	for info in parsed_files:
		file_path = info.get("file", "")
		language = info.get("language", "")
		imports = info.get("imports", [])
		
		# Determine run command
		if language == "python":
			run_cmd = f"python {file_path}"
			deps = [imp for imp in imports if imp and not imp.startswith("_")]
			if not deps:
				deps = ["(no external dependencies)"]
		elif language == "javascript":
			run_cmd = f"node {file_path}"
			deps = [imp for imp in imports if imp and not imp.startswith("_")]
			if not deps:
				deps = ["(no external dependencies)"]
		else:
			run_cmd = f"<language-specific command> {file_path}"
			deps = imports if imports else ["(no external dependencies)"]
		
		instructions.append({
			"file": file_path,
			"language": language,
			"run_command": run_cmd,
			"dependencies": deps,
		})
	
	return instructions


def build_per_file_workflows(parsed_files: List[dict]) -> List[dict]:
	"""Create simple Mermaid flows per file showing defined symbols."""
	def sanitize(text: str) -> str:
		return text.replace(" ", "_").replace("/", "_").replace("\\", "_")

	workflows: List[dict] = []
	for info in parsed_files:
		file_id = sanitize(info.get("file", "file"))
		lines = ["flowchart TD", f"    {file_id}[{info.get('file', '')}]"]
		for fn in info.get("functions", []):
			fn_id = sanitize(f"{info.get('file','')}::{fn.get('name')}")
			lines.append(f"    {fn_id}[{fn.get('name')}()]")
			lines.append(f"    {file_id} --> {fn_id}")
		for cls in info.get("classes", []):
			cls_id = sanitize(f"{info.get('file','')}::class::{cls.get('name')}")
			lines.append(f"    {cls_id}[class {cls.get('name')}]")
			lines.append(f"    {file_id} --> {cls_id}")
		workflows.append({"file": info.get("file", ""), "mermaid": "\n".join(lines)})
	return workflows


def run_pipeline(repo_path: str, output_path: str) -> str:
	parsed_files = normalize_paths(parse_code(repo_path), repo_path)
	stats = collect_stats(parsed_files)
	git_info = describe_repo(repo_path)
	gitignore_text = load_gitignore(repo_path)
	graph = build_graph(parsed_files, git_info)
	mermaid = to_mermaid(graph)
	folder_tree = build_folder_tree(repo_path)
	per_file_workflows = build_per_file_workflows(parsed_files)
	run_instructions = build_run_instructions(parsed_files)

	# Load source code for each file and get purpose summaries
	base_path = Path(repo_path).resolve()
	file_purposes: List[dict] = []
	summarizer = LLMSummarizer()
	for info in parsed_files:
		try:
			abs_file_path = base_path / info.get("file", "")
			with open(abs_file_path, "r", encoding="utf-8", errors="ignore") as f:
				code = f.read()
			analysis = summarizer.summarize_file_purpose(info.get("file", ""), code)
			# analysis is now a dict with 'purpose', 'line_by_line', 'dry_run'
			file_purposes.append({
				"file": info.get("file", ""),
				"purpose": analysis.get("purpose", ""),
				"line_by_line": analysis.get("line_by_line", ""),
				"dry_run": analysis.get("dry_run", ""),
			})
		except Exception:
			file_purposes.append({
				"file": info.get("file", ""),
				"purpose": "Unable to analyze.",
				"line_by_line": "",
				"dry_run": "",
			})

	summaries = summarizer.generate_all(
		parsed_files=parsed_files,
		graph_mermaid=mermaid,
		git_insights=git_info,
		gitignore_text=gitignore_text,
		stats=stats,
	)

	md_builder = MarkdownBuilder()
	doc_content = md_builder.build(
		parsed_files=parsed_files,
		summaries=summaries,
		graph_mermaid=mermaid,
		git_insights=git_info,
		gitignore_text=gitignore_text,
		stats=stats,
		folder_tree=folder_tree,
		workflow_mermaid=DEFAULT_WORKFLOW_MERMAID,
		per_file_workflows=per_file_workflows,
		file_purposes=file_purposes,
		run_instructions=run_instructions,
	)
	md_builder.write(doc_content, output_path)

	return output_path


# Simple workflow diagram describing the pipeline steps
DEFAULT_WORKFLOW_MERMAID = """
flowchart TD
    A[Codebase + Git] --> B[Parsers (Python/JS/TS)]
    B --> C[Knowledge Graph]
    A --> D[Git History]
    D --> C
    C --> E[LLM Summarizer]
    E --> F[Docs Generator]
    C --> F
"""


def main():
	parser = argparse.ArgumentParser(description="AI DocGen pipeline")
	parser.add_argument("repo", help="Path to repo to document", nargs="?", default="sample_repo")
	parser.add_argument("--output", help="Output markdown path", default=os.path.join("build", "docs.md"))
	args = parser.parse_args()

	output_path = run_pipeline(args.repo, args.output)
	print(f"Documentation generated at {output_path}")


if __name__ == "__main__":
	main()
