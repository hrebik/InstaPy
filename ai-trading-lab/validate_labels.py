#!/usr/bin/env python3
"""Porovná tvoje labely s detekcemi feature enginu nad nahrávkou.

Použití:
    python validate_labels.py feed.ndjson labels.ndjson
    python validate_labels.py feed.ndjson labels.ndjson --tol 30 --match-side

Bez argumentů spustí DEMO na syntetických datech (vygeneruje feed i labely
z absorpcí, které engine sám najde, a ukáže 100% recall).
"""
import argparse
import sys

from ai_trading.labels import Label, read_labels, append_label
from ai_trading.validate import validate, run_engine
from ai_trading.events import write_events
from ai_trading.feed_synthetic import synthetic_session


def demo() -> None:
    print("DEMO (syntetická data) — žádné argumenty zadány.\n")
    feed = "synthetic_feed.ndjson"
    labels_path = "synthetic_labels.ndjson"
    write_events(feed, synthetic_session())
    # „lidské" labely vyrobíme z absorpcí, co engine najde (posunuté o pár s),
    # ať demo ukáže reálné párování v toleranci.
    _, absorptions = run_engine(feed)
    open(labels_path, "w").close()
    for a in absorptions[:5]:
        append_label(labels_path, Label(t=a.t + 3_000_000_000, pattern="absorption",
                                        side=a.side, price=a.price, note="z videa"))
    rep = validate(feed, read_labels(labels_path), tol_s=20)
    print(rep.format())


def main() -> None:
    if len(sys.argv) == 1:
        demo()
        return
    p = argparse.ArgumentParser()
    p.add_argument("feed")
    p.add_argument("labels")
    p.add_argument("--tol", type=float, default=20.0, help="okno shody v sekundách")
    p.add_argument("--match-side", action="store_true", help="vyžaduj shodu bid/ask")
    args = p.parse_args()

    rep = validate(args.feed, read_labels(args.labels), tol_s=args.tol,
                   match_side=args.match_side)
    print(rep.format())


if __name__ == "__main__":
    main()
