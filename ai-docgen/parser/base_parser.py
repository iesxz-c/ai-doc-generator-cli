import os
from abc import ABC, abstractmethod
from typing import Dict, List


class BaseParser(ABC):
    """
    Base parser providing a unified interface for all language parsers.
    Output shape must stay consistent across languages to keep downstream
    components (graph builder, summarizer, docs generator) simple.
    """

    @abstractmethod
    def parse_file(self, file_path: str) -> Dict:
        """Parse a single file and return a structured dictionary."""
        raise NotImplementedError

    @abstractmethod
    def extensions(self) -> List[str]:
        """Return the list of supported extensions for this parser."""
        raise NotImplementedError

    def walk_directory(self, root_path: str) -> List[Dict]:
        """
        Walk a directory and parse all supported files, returning aggregated
        results.
        """
        supported_exts = self.extensions()

        parsed_files: List[Dict] = []
        for root, _, files in os.walk(root_path):
            for file_name in files:
                if any(file_name.endswith(ext) for ext in supported_exts):
                    full_path = os.path.join(root, file_name)
                    parsed_files.append(self.parse_file(full_path))
        return parsed_files
