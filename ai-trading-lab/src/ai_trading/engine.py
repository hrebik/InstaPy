"""Engine: spojuje replay → feature engine → Snapshot.

Snapshot je přesně to, co později poletí do Claude orchestrátoru a do
Discordu. Vzniká na rozhodovacím taktu (uzavření tick candle) — NE na každý
tick, aby LLM nebyl v horké smyčce.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from .events import Event, Trade
from .features.trend import TrendDetector, TrendState
from .features.volume_profile import VolumeProfile
from .features.orderflow import OrderFlow, AbsorptionEvent


@dataclass
class Snapshot:
    t: int
    price: float
    trend: TrendState
    poc: Optional[float]
    value_area: Optional[tuple[float, float]]
    location: str               # kde je cena vůči value area
    cum_delta: float
    last_absorption: Optional[AbsorptionEvent]

    def summary(self) -> str:
        va = f"{self.value_area[0]}–{self.value_area[1]}" if self.value_area else "—"
        absb = f" ABSORPCE@{self.last_absorption.price}({self.last_absorption.side})" \
            if self.last_absorption else ""
        return (
            f"[{self.t}] {self.price} | trend={self.trend} | "
            f"POC={self.poc} VA={va} loc={self.location} | "
            f"Δ={self.cum_delta:+.0f}{absb}"
        )


@dataclass
class Engine:
    tick: float = 0.25
    ticks_per_candle: int = 50

    def __post_init__(self) -> None:
        self.trend = TrendDetector(ticks_per_candle=self.ticks_per_candle)
        self.vp = VolumeProfile(tick=self.tick)
        self.of = OrderFlow()
        self._last_price = 0.0
        self._last_absorption: Optional[AbsorptionEvent] = None

    def run(
        self, events: Iterable[Event], on_snapshot: Callable[[Snapshot], None]
    ) -> int:
        """Prožene eventy a na každé uzavřené svíčce zavolá on_snapshot.

        Vrací počet vygenerovaných snapshotů.
        """
        n = 0
        for ev in events:
            if not isinstance(ev, Trade):
                continue
            self._last_price = ev.price
            self.vp.on_trade(ev)
            absorption = self.of.on_trade(ev)
            if absorption is not None:
                self._last_absorption = absorption
            candle = self.trend.on_trade(ev)
            if candle is not None:
                on_snapshot(self._snapshot(ev))
                self._last_absorption = None  # spotřebováno do snapshotu
                n += 1
        return n

    def _snapshot(self, ev: Trade) -> Snapshot:
        return Snapshot(
            t=ev.t,
            price=self._last_price,
            trend=self.trend.state,
            poc=self.vp.poc,
            value_area=self.vp.value_area(),
            location=self.vp.location(self._last_price),
            cum_delta=self.of.cum_delta,
            last_absorption=self._last_absorption,
        )
