import re


def sanitize_template_name(name: str) -> str:
    """Sanitize a template name for safe storage/use as an identifier."""

    if name is None:
        return "default_template"

    name = str(name).strip()

    if not name:
        return "default_template"

    name = re.sub(r"[^a-zA-Z0-9_-]+", "_", name)
    name = re.sub(r"_+", "_", name)
    name = name.strip("_")

    return name or "default_template"
