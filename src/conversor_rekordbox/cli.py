from __future__ import annotations

import argparse
from pathlib import Path

from .converter import Format, convert_library


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convierte bibliotecas entre Rekordbox, Serato y Engine DJ",
    )
    parser.add_argument("input", type=Path, help="Archivo de entrada")
    parser.add_argument("output", type=Path, help="Archivo de salida")
    parser.add_argument(
        "--input-format",
        choices=[f.value for f in Format],
        help="Forzar el formato de entrada",
    )
    parser.add_argument(
        "--output-format",
        choices=[f.value for f in Format],
        help="Forzar el formato de salida",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_format = Format(args.input_format) if args.input_format else None
    output_format = Format(args.output_format) if args.output_format else None

    convert_library(
        input_path=args.input,
        output_path=args.output,
        input_format=input_format,
        output_format=output_format,
    )

    print(f"Conversión completada: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
