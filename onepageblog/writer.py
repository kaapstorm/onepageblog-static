import shutil
from collections.abc import Iterable
from pathlib import Path


def write(pages: dict[str, str], output_dir: Path) -> None:
    output_dir = Path(output_dir)
    for relative_path, content in pages.items():
        dest = output_dir / relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")


def clean_stale_posts(output_dir: Path, current_slugs: Iterable[str]) -> list[str]:
    """Remove `posts/<slug>/` directories for slugs no longer present.

    Returns the list of slugs removed.
    """
    posts_root = Path(output_dir) / "posts"
    if not posts_root.is_dir():
        return []
    keep = set(current_slugs)
    removed: list[str] = []
    for entry in posts_root.iterdir():
        if entry.is_dir() and entry.name not in keep:
            shutil.rmtree(entry)
            removed.append(entry.name)
    return removed
