"""Layout check for a generated PDF: text past the page margin, and words printed on top
of each other (a table cell spilling into the next column, colliding diagram labels).

It reads word boxes from `pdftotext -bbox` (poppler-utils, installed in the image).
"""
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

MARGIN_PT = 72      # mdpdf sets geometry:margin=1in
TOLERANCE_PT = 6    # justified lines and italics overshoot slightly
ROTATED_SLACK_PT = 50

PAGE_RE = re.compile(r'<page width="([\d.]+)" height="([\d.]+)">(.*?)</page>', re.DOTALL)
WORD_RE = re.compile(
    r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>'
)


@dataclass(frozen=True)
class Problem:
    page: int
    kind: str  # "past margin" or "overlap"
    text: str

    def __str__(self) -> str:
        return f"p{self.page}: {self.kind}: {self.text}"


def find_problems(bbox_html: str) -> list[Problem]:
    """Problems in `pdftotext -bbox` output, in page order."""
    problems: list[Problem] = []
    for number, (w, _h, body) in enumerate(PAGE_RE.findall(bbox_html), 1):
        width = float(w)
        words = [(float(a), float(b), float(c), float(d), t) for a, b, c, d, t in WORD_RE.findall(body)]
        if not words:
            continue
        # A landscape page (pdflscape rotates it) reports coordinates beyond the portrait
        # width; its margins differ, so only the overlap check applies there.
        rotated = max(x1 for _, _, x1, _, _ in words) > width + ROTATED_SLACK_PT
        if not rotated:
            for x0, _, x1, _, text in words:
                if x1 > width - MARGIN_PT + TOLERANCE_PT or x0 < MARGIN_PT - TOLERANCE_PT:
                    problems.append(Problem(number, "past margin", text))
        ordered = sorted(words, key=lambda wd: (wd[1], wd[0]))
        for i, a in enumerate(ordered):
            for b in ordered[i + 1:i + 60]:
                if b[1] > a[3]:
                    break
                dx = min(a[2], b[2]) - max(a[0], b[0])
                dy = min(a[3], b[3]) - max(a[1], b[1])
                # Word boxes include ascenders and descenders, so adjacent lines overlap a
                # little; a real collision overlaps by a large part of the box height.
                height = min(a[3] - a[1], b[3] - b[1])
                if dx > 1.5 and dy > 0.4 * height:
                    problems.append(Problem(number, "overlap", f"{a[4]} / {b[4]}"))
    return problems


def check_pdf(pdf: Path) -> list[Problem]:
    """Run the layout check on a PDF."""
    result = subprocess.run(
        ["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True, check=True
    )
    return find_problems(result.stdout)
