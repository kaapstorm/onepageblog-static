import tempfile
from pathlib import Path

import pytest

from onepageblog.config import Config, load_config


VALID_TOML = """\
site_title = "Test Blog"
site_description = "A test blog"
parent_url = "https://example.com"
base_path = "/blog/"
posts_dir = "posts"
output_dir = "output"
"""


def test_load_config_fields():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(VALID_TOML)
        config = load_config(path)
    assert isinstance(config, Config)
    assert config.site_title == "Test Blog"
    assert config.site_description == "A test blog"
    assert config.parent_url == "https://example.com"
    assert config.base_path == "/blog/"


def test_load_config_resolves_paths_relative_to_config():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(VALID_TOML)
        config = load_config(path)
    assert config.posts_dir == Path(tmp) / "posts"
    assert config.output_dir == Path(tmp) / "output"


def test_base_url_trailing_slash():
    config = Config(
        site_title="T",
        site_description="D",
        parent_url="https://example.com",
        base_path="/blog/",
        posts_dir=Path("/tmp/posts"),
        output_dir=Path("/tmp/output"),
    )
    assert config.base_url == "https://example.com/blog/"


def test_base_url_normalises_slashes():
    config = Config(
        site_title="T",
        site_description="D",
        parent_url="https://example.com/",
        base_path="blog",
        posts_dir=Path("/tmp/posts"),
        output_dir=Path("/tmp/output"),
    )
    assert config.base_url == "https://example.com/blog/"


def test_missing_field_raises():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(
            'site_title = "Test"\n'
            'parent_url = "https://example.com"\n'
            'base_path = "/blog/"\n'
            'posts_dir = "posts"\n'
            'output_dir = "output"\n'
        )
        with pytest.raises(KeyError):
            load_config(path)
