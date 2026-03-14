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
```

## What it does

- **Extracts** inline mermaid code blocks from `.md` files into separate `.mmd` files in a `diagrams/` subdirectory
- **Renders** `.mmd` diagrams to PDF via mmdc (SVG) with tspan fix and rsvg-convert (PDF)
- **Converts** `.md` files to PDF via pandoc with LuaLaTeX, Noto fonts, and TOC

## Config

Place a `.config/` directory alongside your docs with:

- `mermaid.config.json` — Mermaid CLI configuration
- `pandoc-header.tex` — LuaLaTeX preamble (fonts, table formatting)

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

# Pull pre-built image from ghcr
make pull
```
