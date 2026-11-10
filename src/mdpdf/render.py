import re
import subprocess
from pathlib import Path

from mdpdf.config import _BUNDLED_CONFIG

SVG_OPEN_RE = re.compile(r"<svg(?![^>]*xml:space=)")


def _prepare_svg(svg_content: str) -> str:
    """Make mermaid's SVG render faithfully in rsvg-convert.

    mermaid writes each word of a label as a <tspan> with a leading space; rsvg drops
    that whitespace unless the document says xml:space="preserve", so words run
    together. The tspan x= positions are kept: removing them (as earlier versions did)
    shifts the second line of a multi-line label off centre.
    """
    return SVG_OPEN_RE.sub('<svg xml:space="preserve"', svg_content, count=1)


def render_diagram(mmd_path: Path, config_dir: Path) -> Path:
    """Render a .mmd file to PDF via mmdc → SVG preparation → rsvg-convert."""
    mmd_path = mmd_path.resolve()
    stem = mmd_path.stem
    parent = mmd_path.parent
    tmp_svg = parent / f"{stem}-tmp.svg"
    fixed_svg = parent / f"{stem}-fixed.svg"
    output_pdf = parent / f"{stem}.pdf"
    mermaid_config = config_dir / "mermaid.config.json"
    # Puppeteer config is Docker infrastructure — check user config first, then bundled
    puppeteer_config = config_dir / "puppeteer.json"
    if not puppeteer_config.exists():
        puppeteer_config = _BUNDLED_CONFIG / "puppeteer.json"

    try:
        # Step 1: mmdc → SVG
        mmdc_cmd = [
            "mmdc", "-i", str(mmd_path), "-o", str(tmp_svg),
            "-e", "svg", "-b", "white", "-c", str(mermaid_config),
        ]
        if puppeteer_config.exists():
            mmdc_cmd.extend(["-p", str(puppeteer_config)])
        subprocess.run(mmdc_cmd, check=True)

        # Step 2: SVG preparation for rsvg
        svg_content = tmp_svg.read_text()
        fixed_content = _prepare_svg(svg_content)
        fixed_svg.write_text(fixed_content)

        # Step 3: rsvg-convert → PDF
        subprocess.run(
            [
                "rsvg-convert", "-f", "pdf", "-o", str(output_pdf),
                str(fixed_svg),
            ],
            check=True,
        )
    finally:
        # Clean up temp files
        tmp_svg.unlink(missing_ok=True)
        fixed_svg.unlink(missing_ok=True)

    return output_pdf


def render_all_diagrams(target_path: Path, config_dir: Path, on_render=None) -> int:
    """Find and render all .mmd files under target_path. Returns count."""
    count = 0
    for mmd_file in sorted(target_path.rglob("*.mmd")):
        result = render_diagram(mmd_file, config_dir)
        if on_render:
            on_render(result)
        count += 1
    return count
