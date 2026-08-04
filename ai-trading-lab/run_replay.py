#!/usr/bin/env python3
"""Demo: vygeneruje syntetickou session, uloží ji a přehraje přes engine.

Spuštění:
    python run_replay.py                 # syntetická data
    python run_replay.py path/to/feed.ndjson   # reálná nahrávka z Bookmapu
"""
import sys

from ai_trading.engine import Engine, Snapshot
from ai_trading.events import write_events, read_events
from ai_trading.feed_synthetic import synthetic_session
from ai_trading.replay import ordered


def main() -> None:
    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(f"Přehrávám nahrávku: {path}")
        events = ordered(read_events(path))
    else:
        path = "synthetic_feed.ndjson"
        n = write_events(path, synthetic_session())
        print(f"Vygeneroval jsem {n} syntetických eventů → {path}")
        events = ordered(read_events(path))

    engine = Engine()
    snapshots: list[Snapshot] = []
    engine.run(events, on_snapshot=lambda s: (snapshots.append(s), print(s.summary())))

    print(f"\n=== {len(snapshots)} snapshotů ===")
    if snapshots:
        trends = [s.trend for s in snapshots]
        print("Sekvence trendu:", " ".join(trends))
        absb = [s.last_absorption for s in snapshots if s.last_absorption]
        print(f"Detekováno absorpcí: {len(absb)}")


if __name__ == "__main__":
    main()
