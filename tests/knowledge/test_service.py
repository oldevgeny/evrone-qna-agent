"""Tests for KnowledgeService."""

from pathlib import Path
from unittest.mock import patch

import pytest

from qna_agent.knowledge.exceptions import FileNotFoundInKnowledgeBaseError
from qna_agent.knowledge.service import KnowledgeService


@pytest.fixture
def temp_knowledge_base(tmp_path: Path) -> Path:
    """Create a temporary knowledge base directory with test files."""
    kb_path = tmp_path / "knowledge"
    kb_path.mkdir()

    (kb_path / "test.txt").write_text("This is a test file with some content.")
    (kb_path / "sample.md").write_text("# Sample Markdown\n\nHello world!")
    (kb_path / "data.json").write_text('{"key": "value"}')
    (kb_path / "config.yaml").write_text("name: test")
    (kb_path / "script.py").write_text("print('hello')")

    return kb_path


@pytest.fixture
def knowledge_service(temp_knowledge_base: Path) -> KnowledgeService:
    """Create KnowledgeService with temp knowledge base."""
    with patch("qna_agent.knowledge.service.get_knowledge_settings") as mock_settings:
        mock_settings.return_value.knowledge_base_path = temp_knowledge_base
        return KnowledgeService()


@pytest.mark.anyio
async def test_list_files_returns_allowed_extensions(
    knowledge_service: KnowledgeService,
) -> None:
    """Test that list_files only returns files with allowed extensions."""
    files = await knowledge_service.list_files()
    filenames = [f["filename"] for f in files]

    assert "test.txt" in filenames
    assert "sample.md" in filenames
    assert "data.json" in filenames
    assert "config.yaml" in filenames
    assert "script.py" not in filenames


@pytest.mark.anyio
async def test_list_files_empty_directory(tmp_path: Path) -> None:
    """Test list_files with empty knowledge base."""
    empty_path = tmp_path / "empty_kb"
    empty_path.mkdir()

    with patch("qna_agent.knowledge.service.get_knowledge_settings") as mock_settings:
        mock_settings.return_value.knowledge_base_path = empty_path
        service = KnowledgeService()

    files = await service.list_files()
    assert files == []


@pytest.mark.anyio
async def test_list_files_missing_directory(tmp_path: Path) -> None:
    """Test list_files when knowledge base doesn't exist."""
    missing_path = tmp_path / "nonexistent"

    with patch("qna_agent.knowledge.service.get_knowledge_settings") as mock_settings:
        mock_settings.return_value.knowledge_base_path = missing_path
        service = KnowledgeService()

    files = await service.list_files()
    assert files == []


@pytest.mark.anyio
async def test_read_file_success(knowledge_service: KnowledgeService) -> None:
    """Test reading an existing file."""
    content = await knowledge_service.read_file("test.txt")
    assert "test file" in content


@pytest.mark.anyio
async def test_read_file_not_found(knowledge_service: KnowledgeService) -> None:
    """Test reading a non-existent file raises error."""
    with pytest.raises(FileNotFoundInKnowledgeBaseError) as exc_info:
        await knowledge_service.read_file("nonexistent.txt")

    assert "nonexistent.txt" in str(exc_info.value)


@pytest.mark.anyio
async def test_read_file_path_traversal_blocked(
    knowledge_service: KnowledgeService,
) -> None:
    """Test that path traversal attempts are blocked."""
    with pytest.raises(FileNotFoundInKnowledgeBaseError):
        await knowledge_service.read_file("../../../etc/passwd")


@pytest.mark.anyio
async def test_read_file_invalid_extension(
    knowledge_service: KnowledgeService,
) -> None:
    """Test that files with disallowed extensions are blocked."""
    with pytest.raises(FileNotFoundInKnowledgeBaseError):
        await knowledge_service.read_file("script.py")


@pytest.mark.anyio
async def test_search_returns_matches(knowledge_service: KnowledgeService) -> None:
    """Test search returns matching files."""
    results = await knowledge_service.search("test")

    assert len(results) >= 1
    filenames = [r["filename"] for r in results]
    assert "test.txt" in filenames


@pytest.mark.anyio
async def test_search_case_insensitive(knowledge_service: KnowledgeService) -> None:
    """Test that search is case insensitive."""
    results = await knowledge_service.search("HELLO")

    filenames = [r["filename"] for r in results]
    assert "sample.md" in filenames


@pytest.mark.anyio
async def test_search_no_matches(knowledge_service: KnowledgeService) -> None:
    """Test search with no matches returns empty list."""
    results = await knowledge_service.search("xyznonexistent123")
    assert results == []


@pytest.mark.anyio
async def test_search_snippet_extraction(knowledge_service: KnowledgeService) -> None:
    """Test that search returns snippets with context."""
    results = await knowledge_service.search("test")

    for result in results:
        if result["filename"] == "test.txt":
            assert "snippet" in result
            assert "test" in result["snippet"].lower()
            break
