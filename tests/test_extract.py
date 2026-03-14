import time
from pathlib import Path

from mdpdf.extract import extract_file, extract_directory


def test_single_mermaid_block(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text(
        "# Title\n\n"
        "### Flow\n\n"
        "```mermaid\n"
        "graph TD\n"
        "    A --> B\n"
        "```\n\n"
        "End.\n"
    )
    count = extract_file(md)
    assert count == 1
    mmd = tmp_path / "diagrams" / "doc-diagram-1.mmd"
    assert mmd.exists()
    assert "graph TD" in mmd.read_text()
    # Check replacement in markdown
    content = md.read_text()
    assert "```mermaid" not in content
    assert "![Flow](diagrams/doc-diagram-1.pdf)" in content


def test_multiple_mermaid_blocks(tmp_path):
    md = tmp_path / "multi.md"
    md.write_text(
        "### First\n\n```mermaid\ngraph TD\n    A-->B\n```\n\n"
        "### Second\n\n```mermaid\nsequenceDiagram\n    A->>B: Hi\n```\n\n"
        "### Third\n\n```mermaid\npie\n    title Pets\n```\n"
    )
    count = extract_file(md)
    assert count == 3
    for i in range(1, 4):
        assert (tmp_path / "diagrams" / f"multi-diagram-{i}.mmd").exists()


def test_no_mermaid_blocks(tmp_path):
    md = tmp_path / "plain.md"
    original = "# No diagrams\n\nJust text.\n"
    md.write_text(original)
    count = extract_file(md)
    assert count == 0
    assert md.read_text() == original
    assert not (tmp_path / "diagrams").exists()


def test_alt_text_from_heading(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text(
        "### My Heading\n\n```mermaid\ngraph TD\n    A-->B\n```\n"
    )
    extract_file(md)
    assert "![My Heading](diagrams/doc-diagram-1.pdf)" in md.read_text()


def test_alt_text_fallback(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("```mermaid\ngraph TD\n    A-->B\n```\n")
    extract_file(md)
    assert "![Diagram 1](diagrams/doc-diagram-1.pdf)" in md.read_text()


def test_diagrams_dir_created(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("```mermaid\ngraph TD\n    A-->B\n```\n")
    extract_file(md)
    assert (tmp_path / "diagrams").is_dir()


def test_idempotent_no_inline_mermaid(tmp_path):
    md = tmp_path / "doc.md"
    content = "# Title\n\n![Flow](diagrams/doc-diagram-1.pdf)\n"
    md.write_text(content)
    count = extract_file(md)
    assert count == 0
    assert md.read_text() == content


def test_idempotent_existing_mmd(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("```mermaid\ngraph TD\n    A-->B\n```\n")
    diagrams = tmp_path / "diagrams"
    diagrams.mkdir()
    mmd = diagrams / "doc-diagram-1.mmd"
    mmd.write_text("graph TD\n    A-->B\n")
    original_mtime = mmd.stat().st_mtime
    time.sleep(0.05)
    extract_file(md)
    assert mmd.stat().st_mtime == original_mtime


def test_mmd_content_no_fences(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("```mermaid\ngraph TD\n    A-->B\n```\n")
    extract_file(md)
    mmd_content = (tmp_path / "diagrams" / "doc-diagram-1.mmd").read_text()
    assert "```" not in mmd_content
    assert mmd_content.strip() == "graph TD\n    A-->B"


def test_preserves_surrounding_content(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text(
        "Before text.\n\n"
        "```mermaid\ngraph TD\n    A-->B\n```\n\n"
        "After text.\n"
    )
    extract_file(md)
    content = md.read_text()
    assert content.startswith("Before text.\n")
    assert content.endswith("After text.\n")


def test_non_mermaid_code_blocks(tmp_path):
    md = tmp_path / "doc.md"
    original = "```bash\necho hello\n```\n\n```python\nprint(1)\n```\n"
    md.write_text(original)
    count = extract_file(md)
    assert count == 0
    assert md.read_text() == original


def test_extract_directory_recursive(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "a.md").write_text("```mermaid\ngraph TD\n    A-->B\n```\n")
    (sub / "b.md").write_text("```mermaid\npie\n    title X\n```\n")
    count = extract_directory(tmp_path)
    assert count == 2
    assert (tmp_path / "diagrams" / "a-diagram-1.mmd").exists()
    assert (sub / "diagrams" / "b-diagram-1.mmd").exists()


def test_extract_single_file(tmp_path):
    (tmp_path / "a.md").write_text("```mermaid\ngraph TD\n    A-->B\n```\n")
    (tmp_path / "b.md").write_text("```mermaid\npie\n    title X\n```\n")
    count = extract_file(tmp_path / "a.md")
    assert count == 1
    # b.md should be untouched
    assert "```mermaid" in (tmp_path / "b.md").read_text()
