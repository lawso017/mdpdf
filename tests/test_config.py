from pathlib import Path

from mdpdf.config import find_config


def test_finds_config_in_target_dir(tmp_path):
    config_dir = tmp_path / ".config"
    config_dir.mkdir()
    (config_dir / "mermaid.config.json").write_text("{}")
    result = find_config(tmp_path, root=tmp_path)
    assert result == config_dir


def test_finds_config_in_parent(tmp_path):
    config_dir = tmp_path / ".config"
    config_dir.mkdir()
    (config_dir / "mermaid.config.json").write_text("{}")
    child = tmp_path / "sub" / "deep"
    child.mkdir(parents=True)
    result = find_config(child, root=tmp_path)
    assert result == config_dir


def test_stops_at_root(tmp_path):
    # Config exists above root — should not be found
    above = tmp_path / ".config"
    above.mkdir()
    (above / "mermaid.config.json").write_text("{}")
    root = tmp_path / "workspace"
    root.mkdir()
    target = root / "project"
    target.mkdir()
    result = find_config(target, root=root)
    assert result != above


def test_falls_back_to_bundled(tmp_path):
    result = find_config(tmp_path, root=tmp_path)
    # Should return the bundled config path
    assert result.name == "config"
    assert (result / "mermaid.config.json").exists()
