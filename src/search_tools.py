import re
import subprocess
from pathlib import Path

from src.enterprise_sdk import MockEnterpriseSDK
from src.logging_system import get_logger
from src.storage import LocalDatabase, LocalKeywordIndex, LocalVectorStore


class SearchTools:
    def __init__(self):
        self.logger = get_logger(__name__)
        self.database = LocalDatabase()
        self.vector_store = LocalVectorStore()
        self.keyword_index = LocalKeywordIndex()
        self.enterprise = MockEnterpriseSDK()

    def search(self, source, query, limit=5):
        self.logger.info("search source=%s query=%s", source, query)

        if source == "database":
            return self.database.search(query, limit)
        if source == "vector":
            return self.vector_store.search(query, limit)
        if source == "keyword":
            return self.keyword_index.search(query, limit)
        if source == "enterprise":
            return self.search_enterprise(query, limit)
        if source == "code":
            return self.search_code(query, limit)

        return [{"error": f"Unknown search source: {source}"}]

    def search_enterprise(self, query, limit=5):
        tickets = self.enterprise.search_tickets(query, limit)
        people = self.enterprise.search_people(query, limit)
        return {
            "tickets": tickets,
            "people": people,
        }

    def search_code(self, query, limit=5):
        try:
            completed = subprocess.run(
                [
                    "git",
                    "grep",
                    "-n",
                    "--untracked",
                    query,
                    "--",
                    ".",
                    ":(exclude)logs/*",
                    ":(exclude)data/*",
                    ":(exclude)**/__pycache__/*",
                ],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                check=False,
            )
        except Exception as exc:
            return [{"error": str(exc)}]

        if completed.returncode not in (0, 1):
            return [{"error": completed.stderr.strip()}]

        lines = completed.stdout.strip().splitlines()
        if lines:
            return [{"match": line} for line in lines[:limit]]

        return self.search_code_tokens(query, limit)

    def search_code_tokens(self, query, limit=5):
        root = Path.cwd()
        tokens = re.findall(r"[a-zA-Z0-9_]+", query.lower())
        ignored_dirs = {".git", "__pycache__", "data", "logs"}
        allowed_suffixes = {".py", ".md", ".json", ".txt", ".yml", ".yaml", ".toml"}
        results = []

        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in allowed_suffixes:
                continue
            if any(part in ignored_dirs for part in path.parts):
                continue

            relative = path.relative_to(root)
            text = path.read_text("utf-8", errors="replace")
            searchable = f"{relative}\n{text}".lower()
            score = sum(1 for token in tokens if token in searchable)

            if score:
                line = self._first_matching_line(text, tokens)
                results.append(
                    {
                        "file": str(relative),
                        "score": score,
                        "match": line,
                    }
                )

        return sorted(results, key=lambda item: item["score"], reverse=True)[:limit]

    def _first_matching_line(self, text, tokens):
        for line_number, line in enumerate(text.splitlines(), start=1):
            line_lower = line.lower()
            if any(token in line_lower for token in tokens):
                return f"{line_number}: {line.strip()}"
        return ""
