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


def _cmd_for(tmp_path, md_text, mock_subprocess, **kwargs):
    md = tmp_path / "doc.md"
    md.write_text(md_text)
    config_dir = tmp_path / "config"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "pandoc-header.tex").write_text("% user header")
    mock_subprocess.run.return_value = MagicMock(returncode=0)
    convert_file(md, tmp_path / "pdf", config_dir, **kwargs)
    return mock_subprocess.run.call_args[0][0]


def _headers(cmd):
    return [cmd[i + 1] for i, a in enumerate(cmd) if a == "-H"]


@patch("mdpdf.convert.subprocess")
def test_convert_applies_the_bundled_layout_filter(mock_subprocess, tmp_path):
    cmd = _cmd_for(tmp_path, "# Hello\n", mock_subprocess)
    i = cmd.index("--lua-filter")
    assert cmd[i + 1].endswith("filters/mdpdf.lua")


@patch("mdpdf.convert.subprocess")
def test_core_header_is_included_before_a_user_header(mock_subprocess, tmp_path):
    headers = _headers(_cmd_for(tmp_path, "# Hello\n", mock_subprocess))
    assert headers[0].endswith("mdpdf-core.tex")
    assert headers[1].endswith("config/pandoc-header.tex")


@patch("mdpdf.convert.subprocess")
def test_front_matter_banner_adds_a_banner_header(mock_subprocess, tmp_path):
    md = '---\ntitle: "T"\nbanner: "DRAFT for review -- not for submission"\n---\n\n# Hello\n'
    headers = _headers(_cmd_for(tmp_path, md, mock_subprocess))
    assert [Path(h).name for h in headers].count("banner.tex") == 1


@patch("mdpdf.convert.subprocess")
def test_banner_header_content(mock_subprocess, tmp_path):
    seen = {}

    def run(cmd, **kwargs):
        for i, a in enumerate(cmd):
            if a == "-H" and Path(cmd[i + 1]).name == "banner.tex":
                seen["tex"] = open(cmd[i + 1]).read()
        return MagicMock(returncode=0)

    mock_subprocess.run.side_effect = run
    md = tmp_path / "doc.md"
    md.write_text('---\nbanner: "DRAFT_1 & co"\n---\n\nText.\n')
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    convert_file(md, tmp_path / "pdf", config_dir)
    assert "AddToShipoutPictureFG" in seen["tex"]
    assert r"DRAFT\_1 \& co" in seen["tex"]


@patch("mdpdf.convert.subprocess")
def test_banner_option_overrides_front_matter(mock_subprocess, tmp_path):
    seen = {}

    def run(cmd, **kwargs):
        for i, a in enumerate(cmd):
            if a == "-H" and Path(cmd[i + 1]).name == "banner.tex":
                seen["tex"] = open(cmd[i + 1]).read()
        return MagicMock(returncode=0)

    mock_subprocess.run.side_effect = run
    md = tmp_path / "doc.md"
    md.write_text('---\nbanner: "from front matter"\n---\n\nText.\n')
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    convert_file(md, tmp_path / "pdf", config_dir, banner="from the option")
    assert "from the option" in seen["tex"]


@patch("mdpdf.convert.subprocess")
def test_no_banner_means_no_banner_header(mock_subprocess, tmp_path):
    headers = _headers(_cmd_for(tmp_path, "# Hello\n", mock_subprocess))
    assert "banner.tex" not in [Path(h).name for h in headers]
