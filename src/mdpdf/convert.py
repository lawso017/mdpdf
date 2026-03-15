import subprocess
from pathlib import Path

from mdpdf.config import bundled_config
from mdpdf.naming import to_kebab

SKIP_DIRS = {"pdf", ".config", "diagrams", "__pycache__", ".git", "node_modules"}


def convert_file(md_path: Path, output_dir: Path, config_dir: Path) -> Path:
    """Convert one markdown file to PDF via pandoc. Returns output path."""
    output_name = to_kebab(md_path.stem) + ".pdf"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name
    header_path = config_dir / "pandoc-header.tex"
    if not header_path.exists():
        header_path = bundled_config() / "pandoc-header.tex"

    subprocess.run(
        [
            "pandoc", str(md_path),
            "-o", str(output_path),
            "--pdf-engine=lualatex",
            "-H", str(header_path),
            "-V", "geometry:margin=1in",
            "-V", "fontsize=11pt",
            "-V", "colorlinks=true",
            "-V", "linkcolor=blue",
            "--toc",
        ],
        check=True,
        cwd=str(md_path.parent),
    )

    return output_path


def convert_directory(
    target_path: Path, output_dir: Path, config_dir: Path, on_convert=None
) -> int:
    """Convert all .md files recursively, mirroring directory structure. Returns count."""
    count = 0
    for md_file in sorted(target_path.rglob("*.md")):
        # Skip files in excluded directories
        rel = md_file.relative_to(target_path)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue

        # Mirror directory structure in output
        rel_dir = rel.parent
        file_output_dir = output_dir / rel_dir if rel_dir != Path(".") else output_dir

        result = convert_file(md_file, file_output_dir, config_dir)
        if on_convert:
            on_convert(result)
        count += 1
    return count
