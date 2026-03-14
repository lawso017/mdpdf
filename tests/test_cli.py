from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from mdpdf.cli import main


@patch("mdpdf.cli.convert_directory")
@patch("mdpdf.cli.render_all_diagrams")
@patch("mdpdf.cli.extract_directory")
@patch("mdpdf.cli.find_config")
def test_default_recursive(mock_config, mock_extract, mock_render, mock_convert, tmp_path):
    mock_config.return_value = tmp_path
    mock_extract.return_value = 0
    mock_render.return_value = 0
    mock_convert.return_value = 0

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(main, [])
    assert result.exit_code == 0


@patch("mdpdf.cli.convert_directory")
@patch("mdpdf.cli.render_all_diagrams")
@patch("mdpdf.cli.extract_directory")
@patch("mdpdf.cli.find_config")
def test_dir_argument(mock_config, mock_extract, mock_render, mock_convert, tmp_path):
    sub = tmp_path / "org"
    sub.mkdir()
    mock_config.return_value = tmp_path
    mock_extract.return_value = 0
    mock_render.return_value = 0
    mock_convert.return_value = 0

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        Path(td, "org").mkdir(exist_ok=True)
        result = runner.invoke(main, ["org"])
    assert result.exit_code == 0
    # extract_directory should have been called
    mock_extract.assert_called_once()


@patch("mdpdf.cli.convert_file")
@patch("mdpdf.cli.render_all_diagrams")
@patch("mdpdf.cli.extract_file")
@patch("mdpdf.cli.find_config")
def test_file_flag(mock_config, mock_extract, mock_render, mock_convert, tmp_path):
    mock_config.return_value = tmp_path
    mock_extract.return_value = 1
    mock_render.return_value = 0
    mock_convert.return_value = tmp_path / "pdf" / "doc.pdf"

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        Path(td, "doc.md").write_text("# Hello\n")
        result = runner.invoke(main, ["--file", "doc.md"])
    assert result.exit_code == 0
    mock_extract.assert_called_once()


@patch("mdpdf.cli._clean")
def test_clean_flag(mock_clean, tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(main, ["--clean"])
    assert result.exit_code == 0
    mock_clean.assert_called_once()


@patch("mdpdf.cli.convert_directory")
@patch("mdpdf.cli.render_all_diagrams")
@patch("mdpdf.cli.extract_directory")
@patch("mdpdf.cli.find_config")
def test_extract_only_flag(mock_config, mock_extract, mock_render, mock_convert, tmp_path):
    mock_config.return_value = tmp_path
    mock_extract.return_value = 2

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(main, ["--extract-only"])
    assert result.exit_code == 0
    mock_extract.assert_called_once()
    mock_render.assert_not_called()
    mock_convert.assert_not_called()


@patch("mdpdf.cli.convert_directory")
@patch("mdpdf.cli.render_all_diagrams")
@patch("mdpdf.cli.extract_directory")
@patch("mdpdf.cli.find_config")
def test_no_extract_flag(mock_config, mock_extract, mock_render, mock_convert, tmp_path):
    mock_config.return_value = tmp_path
    mock_render.return_value = 0
    mock_convert.return_value = 0

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(main, ["--no-extract"])
    assert result.exit_code == 0
    mock_extract.assert_not_called()
    mock_render.assert_called_once()
    mock_convert.assert_called_once()


@patch("mdpdf.cli.convert_file")
@patch("mdpdf.cli.render_all_diagrams")
@patch("mdpdf.cli.extract_file")
@patch("mdpdf.cli.find_config")
def test_file_flag_preserves_relative_path(mock_config, mock_extract, mock_render, mock_convert, tmp_path):
    """mdpdf --file subdir/doc.md should output to <cwd>/pdf/subdir/, not <cwd>/subdir/pdf/."""
    mock_config.return_value = tmp_path
    mock_extract.return_value = 0
    mock_render.return_value = 0

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        cwd = Path(td)
        subdir = cwd / "subdir"
        subdir.mkdir()
        (subdir / "doc.md").write_text("# Hello\n")
        mock_convert.return_value = cwd / "pdf" / "subdir" / "doc.pdf"
        result = runner.invoke(main, ["--file", "subdir/doc.md"])

    assert result.exit_code == 0
    call_args = mock_convert.call_args
    actual_output_dir = call_args[0][1]
    expected_output_dir = Path(td).resolve() / "pdf" / "subdir"
    assert actual_output_dir == expected_output_dir, f"Expected {expected_output_dir}, got {actual_output_dir}"


@patch("mdpdf.cli.convert_directory")
@patch("mdpdf.cli.render_all_diagrams")
@patch("mdpdf.cli.extract_directory")
@patch("mdpdf.cli.find_config")
def test_dir_argument_preserves_relative_path(mock_config, mock_extract, mock_render, mock_convert, tmp_path):
    """mdpdf subdir should output to <cwd>/pdf/subdir/, not <cwd>/subdir/pdf/."""
    mock_config.return_value = tmp_path
    mock_extract.return_value = 0
    mock_render.return_value = 0
    mock_convert.return_value = 0

    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        cwd = Path(td)
        subdir = cwd / "subdir"
        subdir.mkdir()
        result = runner.invoke(main, ["subdir"])

    assert result.exit_code == 0
    call_args = mock_convert.call_args
    actual_output_dir = call_args[0][1]
    expected_output_dir = Path(td).resolve() / "pdf" / "subdir"
    assert actual_output_dir == expected_output_dir, f"Expected {expected_output_dir}, got {actual_output_dir}"


def test_invalid_path():
    runner = CliRunner()
    result = runner.invoke(main, ["--file", "/nonexistent/path/file.md"])
    assert result.exit_code != 0
