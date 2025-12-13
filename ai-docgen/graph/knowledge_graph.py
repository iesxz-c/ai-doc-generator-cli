from typing import Dict, List


def build_graph(parsed_files: List[Dict], git_history: Dict) -> Dict:
	"""
	Build a lightweight knowledge graph represented as dictionaries.
	Nodes: files, functions, classes, commits
	Edges: imports, defines, calls, changed_by
	"""
	nodes: List[Dict] = []
	edges: List[Dict] = []

	# File nodes
	for file_info in parsed_files:
		file_id = file_info["file"]
		file_label = file_id
		nodes.append({"id": file_id, "label": file_label, "type": "file", "language": file_info.get("language")})

		# Functions
		for fn in file_info.get("functions", []):
			fn_id = f"{file_id}::func::{fn.get('name')}"
			fn_label = f"{fn.get('name')}()"
			nodes.append({"id": fn_id, "label": fn_label, "type": "function", "name": fn.get("name")})
			edges.append({"source": file_id, "target": fn_id, "type": "defines"})

		# Classes
		for cls in file_info.get("classes", []):
			cls_id = f"{file_id}::class::{cls.get('name')}"
			cls_label = f"class {cls.get('name')}"
			nodes.append({"id": cls_id, "label": cls_label, "type": "class", "name": cls.get("name")})
			edges.append({"source": file_id, "target": cls_id, "type": "defines"})

		# Imports
		for imp in file_info.get("imports", []):
			edges.append({"source": file_id, "target": imp, "type": "imports"})

		# Calls
		for call in file_info.get("calls", []):
			if call.get("target"):
				edges.append({"source": file_id, "target": call["target"], "type": "calls"})

	# Commits as nodes + change edges
	for commit in git_history.get("commits", []):
		commit_id = commit.get("hash")
		nodes.append({"id": commit_id, "label": commit.get("message", "commit"), "type": "commit"})
		for file_stat in commit.get("files", []):
			edges.append({"source": commit_id, "target": file_stat.get("path"), "type": "changed"})

	return {"nodes": nodes, "edges": edges}


def to_mermaid(graph: Dict) -> str:
	"""Render a simple Mermaid graph from the node/edge list."""
	lines = ["graph TD"]
	# Declare nodes with labels for readability
	for node in graph.get("nodes", []):
		nid = sanitize(node.get("id"))
		label = node.get("label", node.get("id", ""))
		lines.append(f"    {nid}[{label}]")

	# Edges
	for edge in graph.get("edges", []):
		src = sanitize(edge.get("source"))
		tgt = sanitize(edge.get("target"))
		label = edge.get("type", "edge")
		lines.append(f"    {src}--{label}-->{tgt}")
	return "\n".join(lines)


def sanitize(text: str) -> str:
	if text is None:
		return "unknown"
	return text.replace("::", "_").replace("/", "_").replace("\\", "_").replace(" ", "_")
