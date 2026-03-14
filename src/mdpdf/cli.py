import shutil
from pathlib import Path

import click

from mdpdf.config import find_config
from mdpdf.convert import convert_directory, convert_file
from mdpdf.extract import extract_directory, extract_file
from mdpdf.render import render_all_diagrams


def _rel(path: Path, base: Path) -> str:
    """Return a display-friendly relative path, or the name if not relative."""
    try:
        return str(path.relative_to(base))
    except ValueError:
        return path.name


def _step(label: str) -> None:
    """Print a phase header."""
    click.secho(f"\n=> {label}", bold=True)


def _item(icon: str, message: str) -> None:
    """Print an indented progress line."""
    click.echo(f"   {icon} {message}")


def _clean(target: Path) -> None:
    """Remove generated pdf/ directories and diagram artifacts."""
    _step("Cleaning artifacts")
    removed = 0
    for pdf_dir in target.rglob("pdf"):
        if pdf_dir.is_dir():
            shutil.rmtree(pdf_dir)
            _item("-", f"Removed {_rel(pdf_dir, target)}/")
            removed += 1

    for diagrams_dir in target.rglob("diagrams"):
        if diagrams_dir.is_dir():
            for pdf in diagrams_dir.glob("*.pdf"):
                pdf.unlink()
                _item("-", f"Removed {_rel(pdf, target)}")
                removed += 1

    if removed == 0:
        _item(".", "Nothing to clean")


@click.command()
@click.argument("path", default=".", type=click.Path())
@click.option("--file", "file_mode", is_flag=True, help="Treat PATH as a single file")
@click.option("--clean", "clean_mode", is_flag=True, help="Remove generated artifacts")
@click.option("--extract-only", is_flag=True, help="Only extract mermaid diagrams")
@click.option("--no-extract", is_flag=True, help="Skip mermaid extraction step")
def main(path: str, file_mode: bool, clean_mode: bool, extract_only: bool, no_extract: bool) -> None:
    """Generate PDFs from Markdown documents with Mermaid diagram support.

    PATH defaults to current directory for recursive processing.
    """
    target = Path(path).resolve()

    if clean_mode:
        _clean(target)
        return

    if file_mode:
        if not target.is_file():
            raise click.BadParameter(f"Not a file: {target}", param_hint="PATH")
        config_dir = find_config(target.parent)

        if not no_extract:
            _step("Extracting diagrams")
            count = extract_file(target)
            if count:
                _item("+", f"{target.name}: {count} diagram(s)")
            else:
                _item(".", f"{target.name}: no diagrams found")

        if not extract_only:
            diagrams_dir = target.parent / "diagrams"
            if diagrams_dir.exists():
                _step("Rendering diagrams")
                rendered = render_all_diagrams(diagrams_dir, config_dir,
                    on_render=lambda p: _item(">", _rel(p, target.parent)))

            _step("Converting to PDF")
            cwd = Path.cwd()
            rel_dir = target.parent.relative_to(cwd)
            output_dir = cwd / "pdf" / rel_dir
            result = convert_file(target, output_dir, config_dir)
            _item(">", _rel(result, target.parent))
    else:
        if not target.is_dir():
            raise click.BadParameter(f"Not a directory: {target}", param_hint="PATH")
        config_dir = find_config(target)

        if not no_extract:
            _step("Extracting diagrams")
            count = extract_directory(target,
                on_extract=lambda p, n: _item("+", f"{_rel(p, target)}: {n} diagram(s)"))
            if count == 0:
                _item(".", "No diagrams found")

        if not extract_only:
            _step("Rendering diagrams")
            rendered = render_all_diagrams(target, config_dir,
                on_render=lambda p: _item(">", _rel(p, target)))
            if rendered == 0:
                _item(".", "No diagrams to render")

            _step("Converting to PDF")
            cwd = Path.cwd()
            rel_dir = target.relative_to(cwd)
            output_dir = cwd / "pdf" / rel_dir
            converted = convert_directory(target, output_dir, config_dir,
                on_convert=lambda p: _item(">", _rel(p, target)))
            if converted == 0:
                _item(".", "No documents found")

    click.secho("\nDone.", bold=True)
