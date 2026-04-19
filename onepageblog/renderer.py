import shutil
from datetime import date, datetime, time, timezone
from email.utils import format_datetime
from pathlib import Path

from jinja2 import Environment, PackageLoader

from .config import Config
from .posts import Post

_STATIC_DIR = Path(__file__).parent / "static"

_env = Environment(
    loader=PackageLoader("onepageblog", "templates"),
    autoescape=True,
)


def _rfc822_date(d: date) -> str:
    return format_datetime(datetime.combine(d, time.min, tzinfo=timezone.utc))


_env.filters["rfc822_date"] = _rfc822_date


def render(config: Config, posts: list[Post]) -> dict[str, str]:
    pages: dict[str, str] = {
        "index.html": _env.get_template("index.html.j2").render(
            config=config, posts=posts
        ),
        "feed.xml": _env.get_template("feed.xml.j2").render(
            config=config, posts=posts
        ),
    }
    for post in posts:
        pages[f"posts/{post.slug}/index.html"] = _env.get_template(
            "post.html.j2"
        ).render(config=config, post=post)
        pages[f"posts/{post.slug}/ajax.html"] = _env.get_template(
            "ajax.html.j2"
        ).render(config=config, post=post)
    return pages


def copy_static(output_dir: Path) -> int:
    """Copy bundled static assets (CSS, JS, fonts) into output_dir. Returns count."""
    output_dir = Path(output_dir)
    count = 0
    for src in _STATIC_DIR.rglob("*"):
        if not src.is_file():
            continue
        rel = src.relative_to(_STATIC_DIR)
        dest = output_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        count += 1
    return count
