from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
import tomllib


@dataclass
class Config:
    site_title: str
    site_description: str
    site_url: str
    posts_dir: Path
    output_dir: Path
    default_author: str | None = None

    @property
    def base_url(self) -> str:
        return self.site_url.rstrip("/") + "/"


def load_config(path: Path) -> Config:
    path = Path(path)
    with open(path, "rb") as f:
        data = tomllib.load(f)
    base = path.parent
    site_url = data["site_url"]
    parsed = urlparse(site_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(
            f"site_url must be an absolute http(s) URL, got {site_url!r}"
        )
    return Config(
        site_title=data["site_title"],
        site_description=data["site_description"],
        site_url=site_url,
        posts_dir=(base / data.get("posts_dir", "posts")).resolve(),
        output_dir=(base / data.get("output_dir", "_output")).resolve(),
        default_author=data.get("default_author"),
    )
