import os
from typing import Dict, List, Optional


class MarkdownBuilder:
	"""Generate structured Markdown documentation from parsed data and summaries."""

	def build(
		self,
		parsed_files: List[Dict],
		summaries: Dict,
		graph_mermaid: str,
		git_insights: Dict,
		gitignore_text: Optional[str],
		stats: Dict,
		folder_tree: str,
		workflow_mermaid: str,
		per_file_workflows: List[Dict],
		file_purposes: List[Dict],
		run_instructions: Optional[List[Dict]] = None,
	) -> str:
		lines: List[str] = []

		lines.append("# Project Documentation\n")

		lines.append("## Project Overview")
		lines.append(summaries.get("Project", ""))
		lines.append("")

		lines.append("## Architecture Overview")
		lines.append("```mermaid")
		lines.append(graph_mermaid)
		lines.append("```")
		lines.append("")

		lines.append("## Stats")
		lines.append(f"- Files: {stats.get('files', 0)}")
		lines.append(f"- Functions: {stats.get('functions', 0)}")
		lines.append(f"- Classes: {stats.get('classes', 0)}")
		lines.append(f"- Imports: {stats.get('imports', 0)}")
		lines.append("")

		lines.append("## Folder Structure")
		lines.append("```\n" + folder_tree.strip() + "\n```")
		lines.append("")

		lines.append("## Per-File Workflows")
		for wf in per_file_workflows:
			lines.append(f"### {wf.get('file')}")
			lines.append("```mermaid")
			lines.append(wf.get("mermaid", ""))
			lines.append("```")
			lines.append("")

		lines.append("## Modules")
		for file_info in parsed_files:
			rel_path = file_info.get("file")
			lines.append(f"### {rel_path}")
			lines.append(f"Language: {file_info.get('language')}")
			lines.append("")

			# Include file purpose from Gemini
			for fp in file_purposes:
				if fp.get("file") == rel_path:
					lines.append("#### What This File Does")
					lines.append(fp.get("purpose", ""))
					lines.append("")
					
					if fp.get("line_by_line"):
						lines.append("#### Line-by-Line Explanation")
						# Format as bullet points to preserve line structure
						for line_item in fp.get("line_by_line", "").split("\n"):
							if line_item.strip():
								lines.append(f"- {line_item.strip()}")
						lines.append("")
					
					if fp.get("dry_run"):
						lines.append("#### Dry Run / Execution Trace")
						lines.append("```")
						lines.append(fp.get("dry_run", ""))
						lines.append("```")
						lines.append("")
					break

			lines.append("#### Imports")
			for imp in file_info.get("imports", []):
				lines.append(f"- {imp}")
			if not file_info.get("imports"):
				lines.append("- None")

			lines.append("\n#### Functions")
			for fn in file_info.get("functions", []):
				doc = fn.get("docstring") or "(no docstring)"
				lines.append(f"- {fn.get('name')}({', '.join(fn.get('args', []))}) — {doc}")
			if not file_info.get("functions"):
				lines.append("- None")

			lines.append("\n#### Classes")
			for cls in file_info.get("classes", []):
				lines.append(f"- {cls.get('name')}")
			if not file_info.get("classes"):
				lines.append("- None")

			lines.append("")

		lines.append("## Summaries")
		
		lines.append("### Architecture")
		arch_summary = summaries.get("Architecture", "")
		if arch_summary and "graph TD" in arch_summary:
			# If it contains Mermaid code, wrap it
			lines.append("```mermaid")
			lines.append(arch_summary)
			lines.append("```")
		else:
			lines.append(arch_summary if arch_summary else "No architecture summary available.")
		lines.append("")
		
		lines.append("### Files")
		files_summary = summaries.get("Files", "")
		if files_summary:
			# Format as a proper list
			for line in files_summary.split("\n"):
				if line.strip():
					lines.append(f"- {line.strip()}")
		else:
			lines.append("No file summary available.")
		lines.append("")
		
		lines.append("### Functions")
		funcs_summary = summaries.get("Functions", "")
		if funcs_summary:
			# Format as a proper list with better structure
			for line in funcs_summary.split("\n"):
				if line.strip():
					lines.append(f"- {line.strip()}")
		else:
			lines.append("No function summary available.")
		lines.append("")
		
		lines.append("### Changes")
		changes_summary = summaries.get("Changes", "")
		if changes_summary:
			for line in changes_summary.split("\n"):
				if line.strip():
					lines.append(f"- {line.strip()}")
		else:
			lines.append("No recent changes summary available.")
		lines.append("")
		
		lines.append("### Gitignore")
		gitignore_summary = summaries.get("Gitignore", "")
		lines.append(gitignore_summary if gitignore_summary else "No .gitignore summary available.")
		lines.append("")

		lines.append("## Git Insights")
		commits = git_insights.get("commits", [])
		if commits:
			for commit in commits:
				lines.append(f"- {commit.get('hash')[:7]}: {commit.get('message')} ({commit.get('date')})")
		else:
			lines.append("- Not a git repository (no commit history available)")

		# Add run instructions section
		if run_instructions:
			lines.append("")
			lines.append("## How to Run")
			for inst in run_instructions:
				lines.append(f"### {inst.get('file', '')}")
				lines.append(f"**Command:** `{inst.get('run_command', '')}`")
				lines.append("")
				lines.append("**Dependencies:**")
				for dep in inst.get("dependencies", []):
					lines.append(f"- {dep}")
				lines.append("")

		return "\n".join(lines)

	def write(self, content: str, output_path: str) -> None:
		os.makedirs(os.path.dirname(output_path), exist_ok=True)
		with open(output_path, "w", encoding="utf-8") as f:
			f.write(content)
