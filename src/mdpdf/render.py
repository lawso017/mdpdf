import re
import subprocess
from pathlib import Path

from mdpdf.config import _BUNDLED_CONFIG

# tspan fix: remove x= attributes from tspan elements that cause misalignment
TSPAN_X_RE = re.compile(r'(<tspan[^>]*?) x="[^"]*"')


def _fix_tspan(svg_content: str) -> str:
    """Remove x attributes from tspan elements to fix text alignment."""
    return TSPAN_X_RE.sub(r"\1", svg_content)


def render_diagram(mmd_path: Path, config_dir: Path) -> Path:
    """Render a .mmd file to PDF via mmdc → tspan fix → rsvg-convert."""
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

        # Step 2: tspan post-process
        svg_content = tmp_svg.read_text()
        fixed_content = _fix_tspan(svg_content)
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


def render_all_diagrams(target_path: Path, config_dir: Path) -> int:
    """Find and render all .mmd files under target_path. Returns count."""
    count = 0
    for mmd_file in sorted(target_path.rglob("*.mmd")):
        render_diagram(mmd_file, config_dir)
        count += 1
    return count
