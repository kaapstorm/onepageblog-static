import argparse
import sys
import tomllib
from pathlib import Path

from .config import load_config
from .posts import load_posts
from .renderer import copy_static, render
from .writer import clean_stale_posts, write


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="onepageblog",
        description="Generate a static one-page blog.",
    )
    parser.add_argument("config", type=Path, help="Path to config.toml")
    args = parser.parse_args()

    try:
        config = load_config(args.config)
    except (KeyError, OSError, ValueError, tomllib.TOMLDecodeError) as e:
        print(f"Error loading config: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        posts = load_posts(config.posts_dir)
    except (OSError, ValueError) as e:
        print(f"Error loading posts: {e}", file=sys.stderr)
        sys.exit(1)

    pages = render(config, posts)
    write(pages, config.output_dir)
    static_count = copy_static(config.output_dir)
    removed = clean_stale_posts(config.output_dir, (p.slug for p in posts))
    print(f"Generated {len(pages) + static_count} files in {config.output_dir}")
    if removed:
        print(f"Removed {len(removed)} stale post(s): {', '.join(removed)}")
