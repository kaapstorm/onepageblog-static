from pathlib import Path


def write(pages: dict[str, str], output_dir: Path) -> None:
    output_dir = Path(output_dir)
    for relative_path, content in pages.items():
        dest = output_dir / relative_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content, encoding="utf-8")
