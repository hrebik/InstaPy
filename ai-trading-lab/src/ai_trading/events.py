"""Normalizovaný order-flow event model.

Tohle je KONTRAKT mezi Bookmap export add-onem a Python pipeline.
Stejné eventy chodí živě i z replaye .bmf nahrávek.

Formát na disku: newline-delimited JSON (ndjson), jeden event na řádek,
seřazeno (nebo seřaditelné) podle pole `t` (epoch nanosekundy).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Iterator, Literal

Side = Literal["bid", "ask"]
Aggressor = Literal["buy", "sell"]


@dataclass(frozen=True)
class Trade:
    """Proběhlý obchod (z Bookmap TradesListener)."""
    t: int            # epoch ns
    price: float
    size: float
    aggressor: Aggressor  # kdo byl agresor (zvedl bid/ask)
    type: str = "trade"


@dataclass(frozen=True)
class Depth:
    """Update jedné úrovně knihy (z Bookmap DepthDataListener / MBP).

    size == 0 znamená, že úroveň zmizela.
    """
    t: int
    side: Side
    price: float
    size: float
    type: str = "depth"


@dataclass(frozen=True)
class BBO:
    """Best bid / best offer snapshot."""
    t: int
    bid: float
    bid_size: float
    ask: float
    ask_size: float
    type: str = "bbo"


Event = Trade | Depth | BBO

_DECODERS = {"trade": Trade, "depth": Depth, "bbo": BBO}


def to_json(event: Event) -> str:
    return json.dumps(asdict(event), separators=(",", ":"))


def from_json(line: str) -> Event:
    raw = json.loads(line)
    cls = _DECODERS[raw["type"]]
    return cls(**raw)


def write_events(path: str, events: Iterator[Event]) -> int:
    """Zapíše eventy do ndjson souboru. Vrací počet zapsaných."""
    n = 0
    with open(path, "w") as f:
        for ev in events:
            f.write(to_json(ev) + "\n")
            n += 1
    return n


def read_events(path: str) -> Iterator[Event]:
    """Čte eventy z ndjson souboru (lazy)."""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                yield from_json(line)
