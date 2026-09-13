"""Command-line entry point: `cartocrisp <link> -o output.svg` or `cartocrisp web`."""
import argparse
import os
import sys
from pathlib import Path

from cartocrisp.i18n import DEFAULT_LOCALE, SUPPORTED_LOCALES, translate
from cartocrisp.pipeline import GenerateOptions, GenerationError, generate


def detect_locale() -> str:
    # locale.getdefaultlocale() is deprecated (and removed in newer CPython),
    # so read the POSIX locale env vars directly; Windows just falls through
    # to DEFAULT_LOCALE, which is an acceptable default.
    env_value = os.environ.get("LC_ALL") or os.environ.get("LANG") or os.environ.get("LANGUAGE") or ""
    lang = env_value.split("_")[0].split(".")[0].lower()
    return lang if lang in SUPPORTED_LOCALES else DEFAULT_LOCALE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cartocrisp", description="Generate a crisp vector map snapshot from a map link."
    )
    parser.add_argument("link", help="Google Maps URL, OpenStreetMap URL, or 'lat,lon,zoom'")
    parser.add_argument("-o", "--output", required=True, help="Output file path (.svg or .pdf)")
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=1200)
    parser.add_argument("--lang", choices=SUPPORTED_LOCALES, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])

    if argv and argv[0] == "web":
        from cartocrisp.web.server import run_server

        run_server()
        return 0

    parser = build_parser()
    args = parser.parse_args(argv)
    locale = args.lang or detect_locale()
    output_path = Path(args.output)
    fmt = "pdf" if output_path.suffix.lower() == ".pdf" else "svg"

    options = GenerateOptions(
        output_path=output_path, width_px=args.width, height_px=args.height, fmt=fmt, locale=locale
    )

    try:
        generate(args.link, options)
    except GenerationError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    print(translate(locale, "generate.success", path=str(output_path)))
    return 0
