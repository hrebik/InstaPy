"""Tick candles + detekce trendu (HH/HL struktura).

Tick candle = svíčka po N obchodech (ne po čase). Z dokončených svíček
sledujeme swing high/low a klasifikujeme trend.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

from ..events import Trade

TrendState = Literal["up", "down", "range"]


@dataclass
class Candle:
    open: float
    high: float
    low: float
    close: float
    volume: float
    n: int


@dataclass
class TrendDetector:
    ticks_per_candle: int = 50
    swing_lookback: int = 3  # kolik svíček zpět pro swing point

    _cur: Optional[Candle] = None
    candles: list[Candle] = field(default_factory=list)
    state: TrendState = "range"

    def on_trade(self, tr: Trade) -> Optional[Candle]:
        """Přidá obchod; vrací dokončenou svíčku, pokud se právě uzavřela."""
        if self._cur is None:
            self._cur = Candle(tr.price, tr.price, tr.price, tr.price, tr.size, 1)
            return None

        c = self._cur
        c.high = max(c.high, tr.price)
        c.low = min(c.low, tr.price)
        c.close = tr.price
        c.volume += tr.size
        c.n += 1

        if c.n >= self.ticks_per_candle:
            self.candles.append(c)
            self._cur = None
            self._update_trend()
            return c
        return None

    def _update_trend(self) -> None:
        cs = self.candles
        if len(cs) < self.swing_lookback + 1:
            return
        recent = cs[-(self.swing_lookback + 1):]
        highs = [c.high for c in recent]
        lows = [c.low for c in recent]
        higher_highs = highs[-1] > max(highs[:-1])
        higher_lows = lows[-1] > min(lows[:-1])
        lower_highs = highs[-1] < min(highs[:-1])
        lower_lows = lows[-1] < min(lows[:-1])

        if higher_highs and higher_lows:
            self.state = "up"
        elif lower_highs and lower_lows:
            self.state = "down"
        else:
            self.state = "range"
