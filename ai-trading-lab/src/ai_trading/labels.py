"""Ruční labely (anotace) order-flow patternů.

Při sledování streamu (nebo vlastních dat) si zapisuješ, co vidíš:
čas + typ patternu. Validátor to pak porovná s tím, co najde engine.

Formát: ndjson, 1 label/řádek. Pole `t` = epoch nanosekundy (stejný
hodinový čas jako feed — tj. tržní/UTC, ne sekundy od startu videa).
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from typing import Iterator, Optional

# Typy patternů, které sledujeme. Volné — můžeš přidat vlastní.
PATTERNS = (
    "absorption",   # pohlcení agresorů na úrovni (vyčerpání)
    "sweep",        # smetení likvidity přes několik úrovní
    "refill",       # úroveň se opakovaně doplňuje (silná obrana)
    "exhaustion",   # vyčerpání trendu
    "reversal",     # obrat
    "trend_up",
    "trend_down",
)


@dataclass(frozen=True)
class Label:
    t: int                         # epoch ns
    pattern: str
    side: Optional[str] = None     # 'bid' | 'ask'
    price: Optional[float] = None
    note: str = ""


def to_json(label: Label) -> str:
    return json.dumps(asdict(label), separators=(",", ":"))


def from_json(line: str) -> Label:
    return Label(**json.loads(line))


def append_label(path: str, label: Label) -> None:
    with open(path, "a") as f:
        f.write(to_json(label) + "\n")


def read_labels(path: str) -> list[Label]:
    out: list[Label] = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(from_json(line))
    return out
