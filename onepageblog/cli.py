import argparse
import logging
import sys
import tomllib
from pathlib import Path

from .config import load_config
from .posts import load_posts
from .renderer import copy_static, render
from .writer import clean_stale_posts, write

log = logging.getLogger("onepageblog")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="onepageblog",
        description="Generate a static one-page blog.",
    )
    parser.add_argument("config", type=Path, help="Path to config.toml")
    verbosity = parser.add_mutually_exclusive_group()
    verbosity.add_argument(
        "-q", "--quiet", action="store_true", help="Suppress non-error output."
    )
    verbosity.add_argument(
        "-v", "--verbose", action="store_true", help="Emit debug output."
    )
    args = parser.parse_args()

    if args.quiet:
        level = logging.WARNING
    elif args.verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(level=level, format="%(message)s")

    try:
        config = load_config(args.config)
    except (KeyError, OSError, ValueError, tomllib.TOMLDecodeError) as e:
        log.error("Error loading config: %s", e)
        sys.exit(1)

    try:
        posts = load_posts(config.posts_dir)
    except (OSError, ValueError) as e:
        log.error("Error loading posts: %s", e)
        sys.exit(1)

    pages = render(config, posts)
    write(pages, config.output_dir)
    static_count = copy_static(config.output_dir)
    removed = clean_stale_posts(config.output_dir, (p.slug for p in posts))
    log.info(
        "Generated %d files in %s", len(pages) + static_count, config.output_dir
    )
    if removed:
        log.info("Removed %d stale post(s): %s", len(removed), ", ".join(removed))
