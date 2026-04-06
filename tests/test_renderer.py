from datetime import date
from pathlib import Path

from unmagic import fixture

from onepageblog.config import Config
from onepageblog.posts import Post
from onepageblog.renderer import render


@fixture
def config():
    yield Config(
        site_title="Test Blog",
        site_description="A test blog",
        parent_url="https://example.com",
        base_path="/blog/",
        posts_dir=Path("/tmp/posts"),
        output_dir=Path("/tmp/output"),
    )


@fixture
def posts():
    yield [
        Post(
            title="First Post",
            date=date(2024, 3, 15),
            author="Norman",
            slug="first-post",
            body_html="<p>Hello world.</p>",
            source_path=Path("/tmp/posts/first-post.md"),
        ),
        Post(
            title="Second Post",
            date=date(2024, 1, 1),
            author="Norman",
            slug="second-post",
            body_html="<p>Another post.</p>",
            source_path=Path("/tmp/posts/second-post.md"),
        ),
    ]


def test_render_returns_expected_keys():
    pages = render(config(), posts())
    expected = {
        "index.html",
        "feed.xml",
        "default.css",
        "fonts.css",
        "htmx.min.js",
        "alpinejs.min.js",
        "first-post/index.html",
        "first-post/ajax.html",
        "second-post/index.html",
        "second-post/ajax.html",
    }
    assert expected <= set(pages.keys())


def test_index_contains_post_titles():
    pages = render(config(), posts())
    assert "First Post" in pages["index.html"]
    assert "Second Post" in pages["index.html"]


def test_index_htmx_ajax_url():
    pages = render(config(), posts())
    assert "https://example.com/blog/first-post/ajax.html" in pages["index.html"]


def test_index_permalink_url():
    pages = render(config(), posts())
    assert "https://example.com/blog/first-post/" in pages["index.html"]


def test_post_page_contains_body():
    pages = render(config(), posts())
    assert "<p>Hello world.</p>" in pages["first-post/index.html"]


def test_post_page_has_back_link():
    pages = render(config(), posts())
    assert "https://example.com/blog/" in pages["first-post/index.html"]


def test_ajax_contains_body_only():
    pages = render(config(), posts())
    assert "<p>Hello world.</p>" in pages["first-post/ajax.html"]
    assert "<!DOCTYPE html>" not in pages["first-post/ajax.html"]


def test_ajax_contains_permalink():
    pages = render(config(), posts())
    assert "https://example.com/blog/first-post/" in pages["first-post/ajax.html"]


def test_feed_contains_post_items():
    pages = render(config(), posts())
    feed = pages["feed.xml"]
    assert "<title>First Post</title>" in feed
    assert "<link>https://example.com/blog/first-post/</link>" in feed
    assert "<![CDATA[<p>Hello world.</p>]]>" in feed


def test_feed_channel_fields():
    pages = render(config(), posts())
    feed = pages["feed.xml"]
    assert "<title>Test Blog</title>" in feed
    assert "<link>https://example.com/blog/</link>" in feed
    assert "<description>A test blog</description>" in feed


def test_feed_pubdate_rfc822_format():
    pages = render(config(), posts())
    feed = pages["feed.xml"]
    # 2024-03-15 is a Friday
    assert "<pubDate>Fri, 15 Mar 2024 00:00:00 +0000</pubDate>" in feed
    # 2024-01-01 is a Monday
    assert "<pubDate>Mon, 01 Jan 2024 00:00:00 +0000</pubDate>" in feed


def test_render_includes_font_files():
    pages = render(config(), posts())
    woff2_keys = [k for k in pages if k.endswith(".woff2")]
    assert len(woff2_keys) >= 5, f"Expected at least 5 .woff2 files, got: {woff2_keys}"


def test_render_returns_bytes_for_binary_files():
    pages = render(config(), posts())
    key = "fonts/lora-latin-400-normal.woff2"
    assert key in pages, "Expected lora-latin-400-normal.woff2 in rendered pages"
    content = pages[key]
    assert isinstance(content, bytes), f"{key} should be bytes"
    assert content[:4] == b"wOF2", f"{key} does not have WOFF2 magic bytes"
