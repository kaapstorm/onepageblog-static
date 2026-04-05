from dataclasses import dataclass
from pathlib import Path
import tomllib
from urllib.parse import urljoin


@dataclass
class Config:
    site_title: str
    site_description: str
    parent_url: str
    base_path: str
    posts_dir: Path
    output_dir: Path

    @property
    def base_url(self) -> str:
        parent = self.parent_url.rstrip("/") + "/"
        path = self.base_path.strip("/")
        return urljoin(parent, path + "/" if path else "")


def load_config(path: Path) -> Config:
    path = Path(path)
    with open(path, "rb") as f:
        data = tomllib.load(f)
    base = path.parent
    return Config(
        site_title=data["site_title"],
        site_description=data["site_description"],
        parent_url=data["parent_url"],
        base_path=data["base_path"],
        posts_dir=(base / data["posts_dir"]).resolve(),
        output_dir=(base / data["output_dir"]).resolve(),
    )
