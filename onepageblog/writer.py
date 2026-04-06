from pathlib import Path


def write(pages: dict[str, str | bytes], output_dir: Path) -> None:
    output_dir = Path(output_dir)
    for relative_path, content in pages.items():
        dest = output_dir / relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            dest.write_bytes(content)
        else:
            dest.write_text(content, encoding="utf-8")
