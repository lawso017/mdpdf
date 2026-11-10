"""Tests for the bundled Lua filter (config/filters/mdpdf.lua).

They run pandoc to LaTeX (no PDF engine needed). The filter must work on the pandoc in
the image (2.17) and on newer local pandoc (3.x), so nothing here depends on the
version's figure or table representation.
"""
import re
import shutil
import subprocess

import pytest

from mdpdf.config import bundled_config

pytestmark = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")

FILTER = bundled_config() / "filters" / "mdpdf.lua"


def to_latex(md: str) -> str:
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "latex", "--lua-filter", str(FILTER)],
        input=md, capture_output=True, text=True, check=True,
    )
    return result.stdout


# Inline code -----------------------------------------------------------------

def test_inline_code_breaks_after_path_separators():
    out = to_latex("See `modules/aws/ecs/main.tf:438-556` here.\n")
    assert r"\texttt{modules/\allowbreak{}aws/\allowbreak{}ecs/" in out
    assert r"main.\allowbreak{}tf:\allowbreak{}438-\allowbreak{}556}" in out


def test_inline_code_escapes_latex_specials():
    out = to_latex("Run `a_b#c%d&e$f{g}h~i^j\\k`.\n")
    assert r"\_" in out and r"\#" in out and r"\%" in out and r"\&" in out and r"\$" in out
    assert r"\{" in out and r"\}" in out
    assert r"\textasciitilde{}" in out and r"\textasciicircum{}" in out and r"\textbackslash{}" in out


def test_long_unbroken_run_breaks_every_16_characters():
    digest = "afb711a07ab3a1e0f9b26709a30b5dc8bd28a21b836c00a4713ca72947869a1e"
    out = to_latex(f"Digest `{digest}`.\n")
    assert r"afb711a07ab3a1e0\allowbreak{}f9b26709a30b5dc8\allowbreak{}" in out


def test_code_in_heading_is_left_alone():
    out = to_latex("## EP-04: web app (`portal.env/x`)\n\nText.\n")
    heading = next(line for line in out.splitlines() if "EP-04" in line)
    assert r"\allowbreak" not in heading


def test_code_blocks_are_untouched():
    out = to_latex("```\nmodules/aws/ecs/main.tf\n```\n")
    assert r"\allowbreak" not in out


# Headings ----------------------------------------------------------------------

def test_headings_are_kept_with_what_follows():
    out = to_latex("Intro.\n\n## Section\n\nBody.\n\n### Sub\n\nMore.\n")
    assert out.count(r"\needspace{") == 2
    assert out.index(r"\needspace{") < out.index(r"\subsection{Section}")


# Tables ------------------------------------------------------------------------

LONG = "word " * 30

def _widths(out: str) -> list[float]:
    # pandoc 2.x and 3.x both write the relative width as a decimal inside the column spec
    return [float(w) for w in re.findall(r"\\real\{([0-9.]+)\}", out)]


def test_equal_dash_table_gets_content_based_widths():
    md = (
        "| ID | Description |\n|---|---|\n"
        f"| G-01 | {LONG} |\n| G-02 | {LONG} |\n"
    )
    widths = _widths(to_latex(md))
    assert len(widths) == 2
    assert widths[0] < 0.2 < widths[1]


def test_label_column_keeps_room_for_its_longest_word():
    md = (
        "| Control | What exists | Evidence |\n|---|---|---|\n"
        f"| Authentication | {LONG} | {LONG} |\n| Authorization and tenant isolation | {LONG} | {LONG} |\n"
    )
    widths = _widths(to_latex(md))
    # "Authentication" (14 characters) needs about an inch at the table font
    assert widths[0] >= 0.15


def test_explicit_dash_ratios_are_respected():
    md = (
        "| ID | Description |\n|------------|--|\n"
        f"| G-01 | {LONG} |\n"
    )
    widths = _widths(to_latex(md))
    assert widths[0] > widths[1]


# Landscape figures -------------------------------------------------------------

def test_landscape_image_goes_on_its_own_landscape_page_with_its_caption():
    md = (
        "Text before.\n\n"
        "![Architecture](diagrams/doc-diagram-1.pdf){.landscape}\n\n"
        "Figure 1. The architecture. Source in `diagrams/arch.mmd`.\n\n"
        "Text after.\n"
    )
    out = to_latex(md)
    assert r"\afterpage{" in out and r"\begin{landscape}" in out
    page = out[out.index(r"\afterpage{"):out.index(r"\end{landscape}")]
    assert r"\includegraphics" in page and "diagrams/doc-diagram-1.pdf" in page
    assert "Figure 1. The architecture." in page
    assert out.count("Figure 1. The architecture.") == 1
    assert out.index("Text after.") > out.index(r"\end{landscape}")


def test_landscape_image_without_figure_paragraph_uses_its_alt_text():
    md = "![Data flows](diagrams/df.pdf){.landscape}\n\nOrdinary text.\n"
    out = to_latex(md)
    page = out[out.index(r"\afterpage{"):out.index(r"\end{landscape}")]
    assert "Data flows" in page
    assert "Ordinary text." not in page


def test_ordinary_image_is_not_made_landscape():
    out = to_latex("![Diagram](diagrams/d.pdf)\n")
    assert r"\begin{landscape}" not in out


def test_code_heavy_column_is_measured_by_its_code():
    # Inline code becomes raw LaTeX in another pass; widths must be measured before that,
    # or a column of paths looks empty and gets squeezed.
    path = "`uai-infra/terraform/modules/aws/ecs/main.tf:438-556`; `silmaril-api/app/src/auth/middleware.py:549-586`"
    md = (
        "| Control | What exists | Evidence |\n|---|---|---|\n"
        f"| Authentication | Short text here. | {path} |\n| MFA | Short text. | {path} |\n"
    )
    widths = _widths(to_latex(md))
    assert widths[2] > widths[1]
