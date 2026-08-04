#!/usr/bin/env python3
"""Rychlý zápis labelu při sledování streamu / dat.

Příklady:
    # teď (živé sledování, hodiny PC = tržní čas feedu)
    python label.py absorption --side ask --price 21050 --note "vrchol, prodejci absorbují"

    # konkrétní tržní čas (ET) z videa
    python label.py reversal --at "2026-06-02 15:30:00" --tz America/New_York

    # vlastní soubor labelů
    python label.py sweep --labels session_2026-06-02.ndjson
"""
import argparse
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from ai_trading.labels import Label, append_label, PATTERNS

NS = 1_000_000_000


def parse_time_ns(at: str | None, tz: str) -> int:
    if at is None:
        return time.time_ns()
    dt = datetime.strptime(at, "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo(tz))
    return int(dt.timestamp() * NS)


def main() -> None:
    p = argparse.ArgumentParser(description="Zapiš order-flow label")
    p.add_argument("pattern", help=f"typ patternu (např. {', '.join(PATTERNS)})")
    p.add_argument("--side", choices=["bid", "ask"], default=None)
    p.add_argument("--price", type=float, default=None)
    p.add_argument("--note", default="")
    p.add_argument("--at", default=None, help='tržní čas "YYYY-MM-DD HH:MM:SS" (jinak teď)')
    p.add_argument("--tz", default="America/New_York", help="časové pásmo pro --at")
    p.add_argument("--labels", default="labels.ndjson")
    args = p.parse_args()

    t = parse_time_ns(args.at, args.tz)
    label = Label(t=t, pattern=args.pattern, side=args.side, price=args.price, note=args.note)
    append_label(args.labels, label)
    when = datetime.fromtimestamp(t / NS).isoformat(timespec="seconds")
    print(f"✓ {args.pattern} @ {when}  → {args.labels}")


if __name__ == "__main__":
    main()
