from datetime import datetime
from typing import Dict, List, Optional

from git import Repo, InvalidGitRepositoryError


class GitHistoryAnalyzer:
	"""Lightweight Git history miner for commit metadata and hotspots."""

	def __init__(self, repo_path: str):
		self.repo = Repo(repo_path)

	def latest_commits(self, limit: int = 20) -> List[Dict]:
		commits = []
		for commit in list(self.repo.iter_commits("HEAD", max_count=limit)):
			commits.append(
				{
					"hash": commit.hexsha,
					"author": commit.author.name,
					"email": commit.author.email,
					"date": datetime.fromtimestamp(commit.committed_date).isoformat(),
					"message": commit.message.strip(),
					"files": self._files_for_commit(commit),
				}
			)
		return commits

	def diff_between(self, rev_a: str, rev_b: str = "HEAD") -> List[Dict]:
		"""Return list of changed files with stats between two revisions."""
		diffs = self.repo.git.diff(f"{rev_a}..{rev_b}", name_status=True).splitlines()
		results: List[Dict] = []
		for line in diffs:
			if not line.strip():
				continue
			status, path = line.split("\t", 1)
			results.append({"status": status, "path": path})
		return results

	def hotspot_files(self, limit: int = 10) -> List[Dict]:
		"""
		Simple hotspot heuristic: count number of commits touching each file
		and return the top N.
		"""
		counts: Dict[str, int] = {}
		for commit in self.repo.iter_commits():
			for file_path in commit.stats.files.keys():
				counts[file_path] = counts.get(file_path, 0) + 1

		ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
		return [{"file": path, "touches": count} for path, count in ranked[:limit]]

	def _files_for_commit(self, commit) -> List[Dict]:
		files = []
		for path, stats in commit.stats.files.items():
			files.append({
				"path": path,
				"insertions": stats.get("insertions", 0),
				"deletions": stats.get("deletions", 0),
				"lines": stats.get("lines", 0),
			})
		return files


def describe_repo(repo_path: str) -> Dict:
	try:
		analyzer = GitHistoryAnalyzer(repo_path)
		commits = analyzer.latest_commits(limit=10)
		hotspots = analyzer.hotspot_files(limit=10)
		return {"commits": commits, "hotspots": hotspots}
	except InvalidGitRepositoryError:
		return {"commits": [], "hotspots": []}
