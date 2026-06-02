"""Validace: porovná ruční labely s tím, co najde feature engine.

Smyčka učení: ty si při sledování označíš patterny → tady ověříš, kolik
z nich engine na stejných časech taky vidí (a kde střílí navíc). Z toho
ladíš prahy v `features/` proti svému čtení.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .engine import Engine, Snapshot
from .features.orderflow import AbsorptionEvent
from .labels import Label
from .replay import replay_file

NS = 1_000_000_000


@dataclass
class Match:
    label: Label
    detected_t: Optional[int]   # čas nejbližší detekce enginu (None = miss)
    delta_s: Optional[float]    # rozdíl v sekundách


@dataclass
class Report:
    matched: list[Match]        # label, který engine potvrdil (true positive)
    missed: list[Match]         # label, který engine NEnašel (false negative)
    extra_detections: int       # detekce enginu bez odpovídajícího labelu (možný FP)
    total_engine_absorptions: int

    @property
    def recall(self) -> float:
        n = len(self.matched) + len(self.missed)
        return len(self.matched) / n if n else 0.0

    def format(self) -> str:
        lines = ["=== Validace labelů vs engine ==="]
        lines.append(
            f"Recall (engine potvrdil tvoje labely): "
            f"{len(self.matched)}/{len(self.matched) + len(self.missed)} "
            f"= {self.recall:.0%}"
        )
        lines.append(
            f"Detekcí enginu bez tvého labelu (možné falešné/nepokryté): "
            f"{self.extra_detections} z {self.total_engine_absorptions}"
        )
        if self.missed:
            lines.append("\nEngine NEzachytil (zvážit změkčení prahů):")
            for m in self.missed:
                lines.append(f"  · {m.label.pattern}@{m.label.price} t={m.label.t} {m.label.note}")
        if self.matched:
            lines.append("\nPotvrzeno:")
            for m in self.matched:
                lines.append(
                    f"  ✓ {m.label.pattern}@{m.label.price} "
                    f"(Δ={m.delta_s:+.1f}s) {m.label.note}"
                )
        return "\n".join(lines)


def run_engine(feed_path: str) -> tuple[list[Snapshot], list[AbsorptionEvent]]:
    engine = Engine()
    snaps: list[Snapshot] = []
    engine.run(replay_file(feed_path), snaps.append)
    return snaps, engine.of.absorptions


def validate(
    feed_path: str,
    labels: list[Label],
    tol_s: float = 20.0,
    match_side: bool = False,
) -> Report:
    """Porovná absorpční labely s detekcemi enginu v okně ±tol_s."""
    _, absorptions = run_engine(feed_path)
    tol_ns = tol_s * NS

    abs_labels = [l for l in labels if l.pattern == "absorption"]
    used: set[int] = set()
    matched: list[Match] = []
    missed: list[Match] = []

    for lab in abs_labels:
        best: Optional[tuple[int, int]] = None  # (index, dt_ns)
        for i, det in enumerate(absorptions):
            if i in used:
                continue
            if match_side and lab.side and det.side != lab.side:
                continue
            dt = abs(det.t - lab.t)
            if dt <= tol_ns and (best is None or dt < best[1]):
                best = (i, dt)
        if best is not None:
            i = best[0]
            used.add(i)
            matched.append(Match(lab, absorptions[i].t, (absorptions[i].t - lab.t) / NS))
        else:
            missed.append(Match(lab, None, None))

    return Report(
        matched=matched,
        missed=missed,
        extra_detections=len(absorptions) - len(used),
        total_engine_absorptions=len(absorptions),
    )
