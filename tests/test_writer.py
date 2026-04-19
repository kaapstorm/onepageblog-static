import tempfile
from pathlib import Path

from onepageblog.writer import clean_stale_posts, write



def test_write_creates_files():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        write(
            {
                "index.html": "<html>index</html>",
                "my-post/index.html": "<html>post</html>",
                "my-post/ajax.html": "<p>body</p>",
            },
            d,
        )
        assert (d / "index.html").read_text() == "<html>index</html>"
        assert (d / "my-post" / "index.html").read_text() == "<html>post</html>"
        assert (d / "my-post" / "ajax.html").read_text() == "<p>body</p>"


def test_write_creates_nested_subdirectories():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        write({"deep/nested/file.html": "content"}, d)
        assert (d / "deep" / "nested" / "file.html").read_text() == "content"


def test_write_overwrites_existing_file():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "index.html").write_text("old content")
        write({"index.html": "new content"}, d)
        assert (d / "index.html").read_text() == "new content"


def test_write_creates_output_dir_if_missing():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp) / "new_output"
        write({"index.html": "hello"}, d)
        assert (d / "index.html").read_text() == "hello"


def test_clean_stale_posts_removes_missing_slugs():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "posts" / "keep").mkdir(parents=True)
        (d / "posts" / "keep" / "index.html").write_text("x")
        (d / "posts" / "stale").mkdir(parents=True)
        (d / "posts" / "stale" / "index.html").write_text("x")
        removed = clean_stale_posts(d, ["keep"])
        assert removed == ["stale"]
        assert (d / "posts" / "keep").is_dir()
        assert not (d / "posts" / "stale").exists()


def test_clean_stale_posts_with_no_posts_dir():
    with tempfile.TemporaryDirectory() as tmp:
        assert clean_stale_posts(Path(tmp), ["anything"]) == []


