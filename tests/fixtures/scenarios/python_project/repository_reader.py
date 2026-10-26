"""Representative source used by runtime acceptance tests."""

from pathlib import Path


class RepositoryReader:
    def read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")
