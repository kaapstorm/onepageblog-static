from dataclasses import dataclass
from datetime import date
from pathlib import Path

import markdown
import yaml


@dataclass
class Post:
    title: str
    date: date
    author: str
    slug: str
    body_html: str
    source_path: Path


def load_posts(posts_dir: Path) -> list[Post]:
    posts = [_parse_post(p) for p in sorted(Path(posts_dir).glob("*.md"))]
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


def _parse_post(path: Path) -> Post:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"{path}: missing frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{path}: malformed frontmatter")
    _, raw_front, body = parts
    meta = yaml.safe_load(raw_front)
    for field in ("title", "date", "author"):
        if field not in meta:
            raise ValueError(f"{path}: missing required frontmatter field '{field}'")
    post_date = meta["date"]
    if isinstance(post_date, str):
        post_date = date.fromisoformat(post_date)
    return Post(
        title=meta["title"],
        date=post_date,
        author=meta["author"],
        slug=path.stem,
        body_html=markdown.markdown(body.strip()),
        source_path=path,
    )
