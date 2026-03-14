import re
from pathlib import Path

from mdpdf.naming import to_kebab

MERMAID_BLOCK_RE = re.compile(
    r"^```mermaid\s*\n(.*?)^```\s*$",
    re.MULTILINE | re.DOTALL,
)

HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$", re.MULTILINE)


def _find_preceding_heading(text: str, block_start: int) -> str | None:
    """Find the nearest heading before the given position."""
    preceding = text[:block_start]
    headings = list(HEADING_RE.finditer(preceding))
    if headings:
        return headings[-1].group(1).strip()
    return None


def extract_file(path: Path) -> int:
    """Extract mermaid blocks from one markdown file. Returns count extracted."""
    content = path.read_text()
    matches = list(MERMAID_BLOCK_RE.finditer(content))
    if not matches:
        return 0

    doc_stem = to_kebab(path.stem)
    diagrams_dir = path.parent / "diagrams"
    count = 0

    # Process in reverse so positions stay valid
    for i, match in enumerate(reversed(matches), 1):
        idx = len(matches) - i + 1
        mermaid_content = match.group(1).rstrip("\n")
        mmd_name = f"{doc_stem}-diagram-{idx}.mmd"
        mmd_path = diagrams_dir / mmd_name

        # Create diagrams dir only when needed
        diagrams_dir.mkdir(exist_ok=True)

        # Write .mmd only if content differs (idempotency)
        if not mmd_path.exists() or mmd_path.read_text().rstrip("\n") != mermaid_content:
            mmd_path.write_text(mermaid_content + "\n")

        # Determine alt text
        heading = _find_preceding_heading(content, match.start())
        alt_text = heading if heading else f"Diagram {idx}"

        # Replace block with image reference
        pdf_ref = f"![{alt_text}](diagrams/{doc_stem}-diagram-{idx}.pdf)"
        content = content[:match.start()] + pdf_ref + content[match.end():]
        count += 1

    path.write_text(content)
    return count


def extract_directory(path: Path, on_extract=None) -> int:
    """Recursively extract mermaid blocks from all .md files. Returns total count."""
    total = 0
    for md_file in sorted(path.rglob("*.md")):
        count = extract_file(md_file)
        if count and on_extract:
            on_extract(md_file, count)
        total += count
    return total
