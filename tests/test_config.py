import tempfile
from pathlib import Path

import pytest

from onepageblog.config import Config, load_config


VALID_TOML = """\
site_title = "Test Blog"
site_description = "A test blog"
site_url = "https://example.com"
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
    assert config.site_url == "https://example.com"


def test_load_config_resolves_paths_relative_to_config():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(VALID_TOML)
        config = load_config(path)
    assert config.posts_dir == Path(tmp) / "posts"
    assert config.output_dir == Path(tmp) / "output"


def test_load_config_defaults_paths():
    minimal_toml = (
        'site_title = "Test Blog"\n'
        'site_description = "A test blog"\n'
        'site_url = "https://example.com"\n'
    )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(minimal_toml)
        config = load_config(path)
    assert config.posts_dir == Path(tmp) / "posts"
    assert config.output_dir == Path(tmp) / "_output"


def test_base_url_trailing_slash():
    config = Config(
        site_title="T",
        site_description="D",
        site_url="https://example.com",
        posts_dir=Path("/tmp/posts"),
        output_dir=Path("/tmp/output"),
    )
    assert config.base_url == "https://example.com/"


def test_base_url_strips_trailing_slash_from_site_url():
    config = Config(
        site_title="T",
        site_description="D",
        site_url="https://example.com/",
        posts_dir=Path("/tmp/posts"),
        output_dir=Path("/tmp/output"),
    )
    assert config.base_url == "https://example.com/"


def test_invalid_site_url_raises():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(
            'site_title = "T"\n'
            'site_description = "D"\n'
            'site_url = "example.com"\n'
        )
        with pytest.raises(ValueError, match="site_url"):
            load_config(path)


def test_missing_field_raises():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "config.toml"
        path.write_text(
            'site_title = "Test"\n'
            'site_url = "https://example.com"\n'
            'posts_dir = "posts"\n'
            'output_dir = "output"\n'
        )
        with pytest.raises(KeyError):
            load_config(path)
