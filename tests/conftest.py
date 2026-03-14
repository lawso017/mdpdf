import pytest


@pytest.fixture
def sample_md_with_mermaid(tmp_path):
    """Create a markdown file with a mermaid code block."""
    content = """# My Document

Some introductory text.

### Architecture Overview

```mermaid
graph TD
    A[Client] --> B[Server]
    B --> C[Database]
```

More text after the diagram.
"""
    md_file = tmp_path / "my-document.md"
    md_file.write_text(content)
    return md_file


@pytest.fixture
def sample_md_no_mermaid(tmp_path):
    """Create a markdown file with no mermaid blocks."""
    content = """# Plain Document

Just some text.

```bash
echo "hello"
```

More text.
"""
    md_file = tmp_path / "plain.md"
    md_file.write_text(content)
    return md_file
