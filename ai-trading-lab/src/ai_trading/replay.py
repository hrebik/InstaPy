"""Replay engine.

Přehrává nahrané eventy přesně v časovém pořadí přes feature engine.
Stejné rozhraní použije i živý feed (jen místo read_events dáš live stream).
"""
from __future__ import annotations

import heapq
from typing import Iterable, Iterator

from .events import Event, read_events


def ordered(events: Iterable[Event]) -> Iterator[Event]:
    """Zaručí chronologické pořadí podle `t`.

    Bookmap eventy chodí v pořadí, ale různé soubory/zdroje se mohou prokládat.
    Pro robustnost mergujeme přes haldu.
    """
    return iter(sorted(events, key=lambda e: e.t))


def merge(*streams: Iterable[Event]) -> Iterator[Event]:
    """Slije víc seřazených streamů do jednoho chronologického (k-way merge)."""
    return heapq.merge(*streams, key=lambda e: e.t)


def replay_file(path: str) -> Iterator[Event]:
    """Načte a chronologicky seřadí eventy z ndjson nahrávky."""
    return ordered(read_events(path))
