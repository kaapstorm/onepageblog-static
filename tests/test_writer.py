import tempfile
from pathlib import Path

from onepageblog.writer import write


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
