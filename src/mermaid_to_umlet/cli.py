from __future__ import annotations

import argparse
from pathlib import Path

from .converter import convert_text
from .parser import MermaidParseError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert Mermaid classDiagram source to UMLet UXF")
    parser.add_argument("input", type=Path, help="Mermaid input file (.mmd or .md)")
    parser.add_argument("-o", "--output", type=Path, help="Output .uxf file")
    parser.add_argument(
        "--layout",
        choices=("hierarchical", "grid"),
        default="hierarchical",
        help="Layout strategy (default: hierarchical)",
    )
    parser.add_argument("--columns", type=int, default=3, help="Grid columns; ignored by hierarchical layout")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = args.output or args.input.with_suffix(".uxf")
    try:
        source = args.input.read_text(encoding="utf-8")
        uxf = convert_text(source, columns=args.columns, layout=args.layout)
        output.write_text(uxf, encoding="utf-8")
    except (OSError, MermaidParseError, ValueError) as exc:
        raise SystemExit(f"error: {exc}") from exc
    print(f"Created {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
