from pathlib import Path
from unittest.mock import patch, MagicMock

from mdpdf.convert import convert_file, convert_directory


@patch("mdpdf.convert.subprocess")
def test_convert_calls_pandoc(mock_subprocess, tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("# Hello\n")
    output_dir = tmp_path / "pdf"
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "pandoc-header.tex").write_text("")

    mock_subprocess.run.return_value = MagicMock(returncode=0)

    convert_file(md, output_dir, config_dir)

    cmd = mock_subprocess.run.call_args[0][0]
    assert "pandoc" in cmd[0]
    assert "--pdf-engine=lualatex" in cmd
    assert any("pandoc-header.tex" in str(a) for a in cmd)
    assert any("Noto Sans Mono" in str(a) for a in cmd)


@patch("mdpdf.convert.subprocess")
def test_convert_creates_output_dir(mock_subprocess, tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("# Hello\n")
    output_dir = tmp_path / "pdf" / "nested"
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "pandoc-header.tex").write_text("")

    mock_subprocess.run.return_value = MagicMock(returncode=0)

    convert_file(md, output_dir, config_dir)

    assert output_dir.exists()


@patch("mdpdf.convert.subprocess")
def test_convert_mirrors_directory_structure(mock_subprocess, tmp_path):
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    md = sub / "doc.md"
    md.write_text("# Hello\n")
    output_dir = tmp_path / "pdf"
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "pandoc-header.tex").write_text("")

    mock_subprocess.run.return_value = MagicMock(returncode=0)

    convert_directory(tmp_path, output_dir, config_dir)

    cmd = mock_subprocess.run.call_args[0][0]
    # Output should mirror structure: pdf/a/b/doc.pdf
    output_arg = None
    for i, arg in enumerate(cmd):
        if arg == "-o":
            output_arg = cmd[i + 1]
            break
    assert output_arg is not None
    assert "a" in output_arg and "b" in output_arg


@patch("mdpdf.convert.subprocess")
def test_convert_skips_pdf_and_config_dirs(mock_subprocess, tmp_path):
    # Create files in directories that should be skipped
    pdf_dir = tmp_path / "pdf"
    pdf_dir.mkdir()
    (pdf_dir / "old.md").write_text("# Old\n")

    config_dir = tmp_path / ".config"
    config_dir.mkdir()
    (config_dir / "notes.md").write_text("# Notes\n")

    diagrams_dir = tmp_path / "diagrams"
    diagrams_dir.mkdir()
    (diagrams_dir / "readme.md").write_text("# Diagrams\n")

    # Create a valid file
    (tmp_path / "doc.md").write_text("# Doc\n")

    mock_subprocess.run.return_value = MagicMock(returncode=0)

    count = convert_directory(tmp_path, tmp_path / "pdf", config_dir)
    assert count == 1


@patch("mdpdf.convert.subprocess")
def test_convert_output_filename_kebab(mock_subprocess, tmp_path):
    md = tmp_path / "My Document.md"
    md.write_text("# Hello\n")
    output_dir = tmp_path / "pdf"
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "pandoc-header.tex").write_text("")

    mock_subprocess.run.return_value = MagicMock(returncode=0)

    result = convert_file(md, output_dir, config_dir)
    assert result.name == "my-document.pdf"
