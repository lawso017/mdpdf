import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def workspace(tmp_path):
    """Create a workspace with sample markdown and mermaid content."""
    doc = tmp_path / "doc.md"
    doc.write_text(
        "# Test Document\n\n"
        "Some text.\n\n"
        "### Architecture\n\n"
        "```mermaid\n"
        "graph TD\n"
        "    A[Client] --> B[Server]\n"
        "    B --> C[Database]\n"
        "```\n\n"
        "More text.\n"
    )
    return tmp_path


def _run_mdpdf(workspace, *args):
    """Run mdpdf CLI in the workspace."""
    cmd = ["uv", "run", "--project", "/opt/mdpdf", "mdpdf"] + list(args)
    return subprocess.run(cmd, cwd=str(workspace), capture_output=True, text=True)


def test_full_pipeline(workspace):
    result = _run_mdpdf(workspace)
    assert result.returncode == 0, f"stderr: {result.stderr}"

    # Mermaid should be extracted
    mmd = workspace / "diagrams" / "doc-diagram-1.mmd"
    assert mmd.exists()

    # Diagram PDF should be rendered
    diagram_pdf = workspace / "diagrams" / "doc-diagram-1.pdf"
    assert diagram_pdf.exists()

    # Document PDF should be created
    doc_pdf = workspace / "pdf" / "doc.pdf"
    assert doc_pdf.exists()

    # Markdown should have image ref, not mermaid block
    content = (workspace / "doc.md").read_text()
    assert "```mermaid" not in content
    assert "![Architecture](diagrams/doc-diagram-1.pdf)" in content


def test_dir_targeting(workspace):
    sub = workspace / "sub"
    sub.mkdir()
    (sub / "sub-doc.md").write_text(
        "# Sub\n\n```mermaid\ngraph TD\n    X-->Y\n```\n"
    )
    result = _run_mdpdf(workspace, "sub")
    assert result.returncode == 0

    # Only sub/ should be processed
    assert (sub / "diagrams" / "sub-doc-diagram-1.mmd").exists()
    # Root doc should still have mermaid block
    assert "```mermaid" in (workspace / "doc.md").read_text()


def test_file_targeting(workspace):
    (workspace / "other.md").write_text(
        "# Other\n\n```mermaid\ngraph TD\n    X-->Y\n```\n"
    )
    result = _run_mdpdf(workspace, "--file", "doc.md")
    assert result.returncode == 0

    # Only doc.md should be processed
    assert "```mermaid" not in (workspace / "doc.md").read_text()
    assert "```mermaid" in (workspace / "other.md").read_text()


def test_clean(workspace):
    # First generate artifacts
    _run_mdpdf(workspace)
    assert (workspace / "pdf").exists()

    # Then clean
    result = _run_mdpdf(workspace, "--clean")
    assert result.returncode == 0
    assert not (workspace / "pdf").exists()


def test_extract_only(workspace):
    result = _run_mdpdf(workspace, "--extract-only")
    assert result.returncode == 0

    # Mermaid extracted
    assert (workspace / "diagrams" / "doc-diagram-1.mmd").exists()
    # No PDFs generated
    assert not (workspace / "pdf").exists()
    assert not (workspace / "diagrams" / "doc-diagram-1.pdf").exists()


def test_config_auto_detection(workspace):
    config_dir = workspace / ".config"
    config_dir.mkdir()
    (config_dir / "mermaid.config.json").write_text(
        '{"htmlLabels": false, "flowchart": {"htmlLabels": false}}'
    )
    (config_dir / "pandoc-header.tex").write_text(
        "\\usepackage{fontspec}\n"
        "\\setmainfont{Noto Sans}\n"
    )
    result = _run_mdpdf(workspace)
    assert result.returncode == 0


def test_config_fallback(workspace):
    # No .config/ directory — should use bundled defaults
    result = _run_mdpdf(workspace)
    assert result.returncode == 0


def test_idempotent(workspace):
    # First run
    _run_mdpdf(workspace)
    content_after_first = (workspace / "doc.md").read_text()

    # Second run
    _run_mdpdf(workspace)
    content_after_second = (workspace / "doc.md").read_text()

    assert content_after_first == content_after_second
