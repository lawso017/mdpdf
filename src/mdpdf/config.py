from pathlib import Path

# Bundled config lives at the package root's sibling config/ directory
_PACKAGE_DIR = Path(__file__).resolve().parent
_BUNDLED_CONFIG = _PACKAGE_DIR.parent.parent / "config"


def bundled_config() -> Path:
    """Return the path to the bundled config directory."""
    return _BUNDLED_CONFIG


def find_config(target_path: Path, root: Path = Path("/workspace")) -> Path:
    """Search upward from target_path for .config/ with mermaid.config.json.

    Stops at root boundary. Falls back to bundled config.
    """
    target_path = target_path.resolve()
    root = root.resolve()
    current = target_path if target_path.is_dir() else target_path.parent

    while True:
        candidate = current / ".config"
        if candidate.is_dir() and (candidate / "mermaid.config.json").exists():
            return candidate
        if current == root or current == current.parent:
            break
        current = current.parent

    return _BUNDLED_CONFIG
