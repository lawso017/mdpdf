import shutil
from pathlib import Path

import click

from mdpdf.config import find_config
from mdpdf.convert import convert_directory, convert_file
from mdpdf.extract import extract_directory, extract_file
from mdpdf.render import render_all_diagrams


def _clean(target: Path) -> None:
    """Remove generated pdf/ directories and diagram artifacts."""
    # Remove pdf/ directories
    for pdf_dir in target.rglob("pdf"):
        if pdf_dir.is_dir():
            shutil.rmtree(pdf_dir)
            click.echo(f"Removed {pdf_dir}")

    # Remove generated diagram PDFs (in diagrams/ directories)
    for diagrams_dir in target.rglob("diagrams"):
        if diagrams_dir.is_dir():
            for pdf in diagrams_dir.glob("*.pdf"):
                pdf.unlink()
                click.echo(f"Removed {pdf}")


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
            count = extract_file(target)
            click.echo(f"Extracted {count} diagram(s) from {target.name}")

        if not extract_only:
            # Render diagrams in the file's directory
            diagrams_dir = target.parent / "diagrams"
            if diagrams_dir.exists():
                rendered = render_all_diagrams(diagrams_dir, config_dir)
                click.echo(f"Rendered {rendered} diagram(s)")

            output_dir = target.parent / "pdf"
            result = convert_file(target, output_dir, config_dir)
            click.echo(f"Created {result}")
    else:
        if not target.is_dir():
            raise click.BadParameter(f"Not a directory: {target}", param_hint="PATH")
        config_dir = find_config(target)

        if not no_extract:
            count = extract_directory(target)
            click.echo(f"Extracted {count} diagram(s)")

        if not extract_only:
            rendered = render_all_diagrams(target, config_dir)
            click.echo(f"Rendered {rendered} diagram(s)")

            output_dir = target / "pdf"
            converted = convert_directory(target, output_dir, config_dir)
            click.echo(f"Converted {converted} document(s)")
