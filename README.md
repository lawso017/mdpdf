# mdpdf

Dockerized Markdown-to-PDF CLI with Mermaid diagram support.

Converts Markdown documents to high-quality PDFs using pandoc + LuaLaTeX, with automatic Mermaid diagram extraction and rendering via mmdc + rsvg-convert. All dependencies are containerized — no local installs needed beyond Docker.

## Installation

### macOS / Linux

```bash
git clone <repo> ~/dev/mdpdf
cd ~/dev/mdpdf
make pull      # pull pre-built image from ghcr (or: make build)
make install   # copies wrapper to /usr/local/bin
```

### Windows

```powershell
docker pull ghcr.io/lawso017/mdpdf:latest
# Copy mdpdf.cmd to a directory on your PATH (e.g. C:\Users\<you>\bin\)
copy mdpdf.cmd C:\Users\<you>\bin\
```

## Usage

```bash
cd ~/dev/project/docs

# Process all markdown files recursively
mdpdf

# Process a specific subdirectory
mdpdf org

# Process a single file
mdpdf --file org/org-chart.md

# Only extract inline mermaid blocks (no PDF generation)
mdpdf --extract-only

# Skip mermaid extraction (only render diagrams + convert markdown)
mdpdf --no-extract

# Remove generated artifacts
mdpdf --clean

# Print a line at the top of every page (or set `banner:` in the front matter)
mdpdf --file report.md --banner "DRAFT for review"

# Fail if any text runs past the margin or prints over other text
mdpdf --file report.md --check
```

## What it does

- **Extracts** inline mermaid code blocks from `.md` files into separate `.mmd` files in a `diagrams/` subdirectory
- **Renders** `.mmd` diagrams to PDF via mmdc (SVG) and rsvg-convert (PDF), with `xml:space="preserve"` so words in labels keep their spaces
- **Replaces** extracted mermaid code blocks with links to newly-rendered PDF diagrams for inline rendering
- **Converts** `.md` files to PDF via pandoc with LuaLaTeX, Noto fonts, and TOC

## Layout

A bundled Lua filter (`config/filters/mdpdf.lua`) handles the layouts that otherwise overflow:

- **Long inline code wraps.** Paths, URLs and digests in backticks may break after `/ . : _ , - = (` and every 16 characters of an unbroken run, so they stay inside table cells and margins. Code in headings is left alone (the PDF bookmarks need plain text).
- **Table column widths follow the content.** When a table's separator row gives every column the same dashes (`|---|---|---|`), each column gets a width from its content, with room for its longest word. Unequal dashes (`|--|--------|`) are kept as the author's choice.
- **Headings stay with what follows** instead of being stranded at the foot of a page.
- **Wide diagrams on a landscape page.** Add the mermaid comment `%% mdpdf: landscape` inside a mermaid block. The diagram goes on a landscape page of its own, after the text that fills the current page. A paragraph right after the block that starts with "Figure" moves with it as its caption. GitHub ignores the comment.
- **Banner.** `banner: "..."` in the front matter, or `--banner`, prints a line at the top of every page.
- **`--check`** reads the finished PDF and reports any word past the 1in margin or printed over another word (landscape pages are checked for overlaps only). It exits non-zero when it finds one.

`config/mdpdf-core.tex` holds what the filter needs and is always included, before your own `.config/pandoc-header.tex`.

## Config

Place a `.config/` directory alongside your docs with:

- `mermaid.config.json` — Mermaid CLI configuration
- `pandoc-header.tex` — LuaLaTeX preamble (fonts, table formatting). It replaces the bundled style header; `mdpdf-core.tex` is still included first

If not found, bundled defaults are used.

## Development

```bash
# Run unit tests (no Docker needed)
make test

# Run integration tests (requires Docker)
make test-integration

# Run all tests
make test-all

# Build Docker image locally
make build

# Build and test a local image without touching the published tag
make build IMAGE=mdpdf:dev && make test-integration IMAGE=mdpdf:dev
MDPDF_IMAGE=mdpdf:dev mdpdf --file doc.md   # use it through the wrapper

# Pull pre-built image from ghcr
make pull
```
