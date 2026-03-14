import re


def to_kebab(name: str) -> str:
    """Convert a filename stem to lowercase-kebab-case."""
    # Insert hyphen before uppercase letters that follow lowercase letters
    name = re.sub(r"([a-z])([A-Z])", r"\1-\2", name)
    # Insert hyphen between consecutive uppercase followed by lowercase
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1-\2", name)
    # Replace spaces and underscores with hyphens
    name = re.sub(r"[\s_]+", "-", name)
    # Collapse consecutive hyphens
    name = re.sub(r"-+", "-", name)
    # Lowercase and strip
    name = name.lower().strip("-")
    return name
