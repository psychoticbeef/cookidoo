#!/usr/bin/env python3
"""Apply Laplace plus-two smoothing to a 1-5 star rating."""

from __future__ import annotations

import argparse
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


MIN_RATING = Decimal("1.0")
MAX_RATING = Decimal("5.0")
ONE_DECIMAL = Decimal("0.1")


def parse_rating(value: str) -> Decimal:
    if not re.fullmatch(r"\d+(?:\.\d)?", value):
        raise argparse.ArgumentTypeError("rating must use at most one digit after the decimal point")

    try:
        rating = Decimal(value)
    except InvalidOperation as exc:
        raise argparse.ArgumentTypeError("rating must be a number from 1.0 to 5.0") from exc

    if rating < MIN_RATING or rating > MAX_RATING:
        raise argparse.ArgumentTypeError("rating must be between 1.0 and 5.0")

    if rating != rating.quantize(ONE_DECIMAL):
        raise argparse.ArgumentTypeError("rating must use at most one digit after the decimal point")

    return rating


def parse_count(value: str) -> int:
    try:
        count = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("n must be a non-negative integer") from exc

    if str(count) != value:
        raise argparse.ArgumentTypeError("n must be a non-negative integer")

    if count < 0:
        raise argparse.ArgumentTypeError("n must be a non-negative integer")

    return count


def smoothed_rating(rating: Decimal, count: int) -> Decimal:
    total = rating * count
    adjusted = (total + Decimal("6.0")) / Decimal(count + 2)
    return adjusted.quantize(ONE_DECIMAL, rounding=ROUND_HALF_UP)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Smooth a 1-5 star rating with Laplace's plus-two rule.",
    )
    parser.add_argument("rating", type=parse_rating, help="average rating from 1.0 to 5.0")
    parser.add_argument("n", type=parse_count, help="non-negative rating count")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    print(smoothed_rating(args.rating, args.n))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
