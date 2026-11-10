import re
import subprocess
import tempfile
from pathlib import Path

from mdpdf.config import bundled_config
from mdpdf.naming import to_kebab

SKIP_DIRS = {"pdf", ".config", "diagrams", "__pycache__", ".git", "node_modules"}

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n(?:---|\.\.\.)\s*\n", re.DOTALL)
BANNER_RE = re.compile(r"""^banner:\s*(?:"((?:[^"\\]|\\.)*)"|'([^']*)'|(.+?))\s*$""", re.MULTILINE)
LATEX_SPECIALS = {
    "\\": r"\textbackslash{}", "{": r"\{", "}": r"\}", "_": r"\_", "#": r"\#",
    "%": r"\%", "&": r"\&", "$": r"\$", "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
}


def front_matter_banner(md_text: str) -> str | None:
    """The `banner:` value from a document's YAML front matter, if any."""
    fm = FRONT_MATTER_RE.match(md_text)
    if not fm:
        return None
    m = BANNER_RE.search(fm.group(1))
    if not m:
        return None
    value = next(g for g in m.groups() if g is not None)
    return value.replace('\\"', '"')


def banner_header(text: str) -> str:
    """LaTeX that prints `text` centred at the top of every page."""
    escaped = "".join(LATEX_SPECIALS.get(ch, ch) for ch in text)
    return (
        "\\AddToShipoutPictureFG{\\AtPageUpperLeft{\\raisebox{-1.6\\baselineskip}"
        "{\\makebox[\\paperwidth]{\\small " + escaped + "}}}}\n"
    )


def convert_file(
    md_path: Path, output_dir: Path, config_dir: Path, *, toc: bool = True, banner: str | None = None
) -> Path:
    """Convert one markdown file to PDF via pandoc. Returns output path.

    `banner` (or the document's `banner:` front matter) is printed at the top of every page.
    """
    output_name = to_kebab(md_path.stem) + ".pdf"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name
    header_path = config_dir / "pandoc-header.tex"
    if not header_path.exists():
        header_path = bundled_config() / "pandoc-header.tex"

    banner = banner if banner is not None else front_matter_banner(md_path.read_text())

    cmd = [
        "pandoc", str(md_path),
        "-o", str(output_path),
        "--pdf-engine=lualatex",
        "--lua-filter", str(bundled_config() / "filters" / "mdpdf.lua"),
        "-H", str(bundled_config() / "mdpdf-core.tex"),
        "-H", str(header_path),
        "-V", "geometry:margin=1in",
        "-V", "fontsize=11pt",
        "-V", "colorlinks=true",
        "-V", "linkcolor=blue",
    ]
    if toc:
        cmd.append("--toc")

    with tempfile.TemporaryDirectory(prefix="mdpdf-") as tmp:
        if banner:
            banner_path = Path(tmp) / "banner.tex"
            banner_path.write_text(banner_header(banner))
            cmd[cmd.index(str(header_path)) + 1:cmd.index(str(header_path)) + 1] = ["-H", str(banner_path)]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(md_path.parent),
        )
    if result.returncode != 0:
        raise RuntimeError(
            f"pandoc failed (exit {result.returncode}) for {md_path}\n"
            f"stderr:\n{result.stderr}"
        )

    return output_path


def convert_directory(
    target_path: Path, output_dir: Path, config_dir: Path, on_convert=None, *, toc: bool = True,
    banner: str | None = None,
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

        result = convert_file(md_file, file_output_dir, config_dir, toc=toc, banner=banner)
        if on_convert:
            on_convert(result)
        count += 1
    return count
