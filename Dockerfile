FROM node:22-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# Minimal system packages — no texlive-fonts-extra or texlive-latex-extra
RUN apt-get update && apt-get install -y --no-install-recommends \
    pandoc \
    texlive-luatex \
    texlive-latex-recommended \
    librsvg2-bin \
    fontconfig \
    fonts-noto \
    fonts-noto-extra \
    fonts-noto-color-emoji \
    chromium \
    && rm -rf /var/lib/apt/lists/* \
    && luaotfload-tool --update

# Mermaid CLI
RUN npm install -g @mermaid-js/mermaid-cli

# Puppeteer config for containerized Chromium
RUN echo "module.exports = { \
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'], \
    executablePath: '/usr/bin/chromium' \
};" > /root/.puppeteerrc.cjs

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project and install
WORKDIR /opt/mdpdf
COPY pyproject.toml uv.lock README.md ./
COPY src/ src/
RUN uv sync --frozen --no-dev

# Copy bundled config
COPY config/ config/

# Copy tests for integration testing
COPY tests/ tests/

WORKDIR /workspace

ENTRYPOINT ["uv", "run", "--project", "/opt/mdpdf", "mdpdf"]
