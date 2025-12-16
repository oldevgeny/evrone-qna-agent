"""Knowledge base service for file operations."""

import asyncio
from pathlib import Path
from typing import ClassVar

from loguru import logger

from qna_agent.knowledge.config import get_knowledge_settings
from qna_agent.knowledge.exceptions import (
    FileNotFoundInKnowledgeBaseError,
    KnowledgeBaseReadError,
)


class KnowledgeService:
    """Service for knowledge base file operations."""

    ALLOWED_EXTENSIONS: ClassVar[set[str]] = {".txt", ".md", ".json", ".yaml", ".yml"}

    def __init__(self) -> None:
        self._settings = get_knowledge_settings()
        self._base_path = self._settings.knowledge_base_path.resolve()

    def _is_safe_path(self, filepath: Path) -> bool:
        """Check if filepath is within the knowledge base directory."""
        try:
            filepath.resolve().relative_to(self._base_path)
            return True
        except ValueError:
            return False

    def _get_allowed_files(self) -> list[Path]:
        """Get all allowed files in the knowledge base."""
        if not self._base_path.exists():
            return []

        files: list[Path] = []
        for ext in self.ALLOWED_EXTENSIONS:
            files.extend(self._base_path.glob(f"**/*{ext}"))

        return sorted(files)

    async def list_files(self) -> list[dict[str, str | int]]:
        """List all available files in the knowledge base."""
        files = await asyncio.to_thread(self._get_allowed_files)

        return [
            {
                "filename": str(f.relative_to(self._base_path)),
                "size": f.stat().st_size,
                "extension": f.suffix,
            }
            for f in files
            if f.is_file()
        ]

    async def read_file(self, filename: str) -> str:
        """Read the contents of a file from the knowledge base.

        Args:
            filename: Relative path to the file within the knowledge base

        Returns:
            File contents as a string

        Raises:
            FileNotFoundInKnowledgeBaseError: If file doesn't exist
            KnowledgeBaseReadError: If reading fails
        """
        filepath = self._base_path / filename

        if not self._is_safe_path(filepath):
            logger.warning(f"Attempted path traversal: {filename}")
            raise FileNotFoundInKnowledgeBaseError(filename)

        if not filepath.exists():
            raise FileNotFoundInKnowledgeBaseError(filename)

        if filepath.suffix not in self.ALLOWED_EXTENSIONS:
            raise FileNotFoundInKnowledgeBaseError(filename)

        try:
            content = await asyncio.to_thread(filepath.read_text, encoding="utf-8")
            return content
        except OSError as e:
            raise KnowledgeBaseReadError(filename, str(e)) from e

    async def search(self, query: str) -> list[dict[str, str]]:
        """Search for files containing the query string.

        Args:
            query: Search query string

        Returns:
            List of matching files with snippets
        """
        query_lower = query.lower()
        results: list[dict[str, str]] = []

        files = await asyncio.to_thread(self._get_allowed_files)

        for filepath in files:
            if not filepath.is_file():
                continue

            try:
                content = await asyncio.to_thread(filepath.read_text, encoding="utf-8")

                if query_lower in content.lower():
                    snippet = self._extract_snippet(content, query_lower)
                    results.append(
                        {
                            "filename": str(filepath.relative_to(self._base_path)),
                            "snippet": snippet,
                        }
                    )

            except OSError:
                logger.warning(f"Failed to read {filepath} during search")
                continue

        return results

    def _extract_snippet(
        self,
        content: str,
        query: str,
        context_chars: int = 100,
    ) -> str:
        """Extract a snippet around the first match."""
        content_lower = content.lower()
        pos = content_lower.find(query)

        if pos == -1:
            return content[:200] + "..." if len(content) > 200 else content

        start = max(0, pos - context_chars)
        end = min(len(content), pos + len(query) + context_chars)

        snippet = content[start:end]

        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet
