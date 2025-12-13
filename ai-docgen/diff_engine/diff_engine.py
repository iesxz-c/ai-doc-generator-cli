from typing import Dict, List

from git import Repo


class DiffEngine:
	"""Thin wrapper around git diff to surface changed files and hunks."""

	def __init__(self, repo_path: str):
		self.repo = Repo(repo_path)

	def changed_files(self, base: str = "HEAD~1", head: str = "HEAD") -> List[str]:
		diff_index = self.repo.commit(base).diff(head)
		return [d.b_path or d.a_path for d in diff_index]

	def summarize_diff(self, base: str = "HEAD~1", head: str = "HEAD") -> List[Dict]:
		diff_index = self.repo.commit(base).diff(head, create_patch=True)
		summary: List[Dict] = []
		for diff in diff_index:
			summary.append(
				{
					"path": diff.b_path or diff.a_path,
					"change_type": diff.change_type,
					"patch": diff.diff.decode("utf-8", errors="ignore"),
				}
			)
		return summary
