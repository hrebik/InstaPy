"""Volume profile: POC a value area.

Akumuluje obchodovaný objem po cenových úrovních. POC = cena s největším
objemem. Value area = pásmo kolem POC pokrývající `value_area_pct` objemu.
Odpovídá na: kde jsme (vs value area) a kam míříme.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

from ..events import Trade


@dataclass
class VolumeProfile:
    tick: float = 0.25
    value_area_pct: float = 0.70

    _vol: dict[float, float] = field(default_factory=lambda: defaultdict(float))

    def on_trade(self, tr: Trade) -> None:
        bucket = round(tr.price / self.tick) * self.tick
        self._vol[round(bucket, 4)] += tr.size

    @property
    def poc(self) -> Optional[float]:
        if not self._vol:
            return None
        return max(self._vol.items(), key=lambda kv: kv[1])[0]

    def value_area(self) -> Optional[tuple[float, float]]:
        """Vrátí (low, high) value area; expanduje od POC k většímu sousedovi."""
        if not self._vol:
            return None
        total = sum(self._vol.values())
        target = total * self.value_area_pct
        prices = sorted(self._vol)
        poc_i = prices.index(self.poc)
        lo = hi = poc_i
        acc = self._vol[prices[poc_i]]
        while acc < target and (lo > 0 or hi < len(prices) - 1):
            below = self._vol[prices[lo - 1]] if lo > 0 else -1
            above = self._vol[prices[hi + 1]] if hi < len(prices) - 1 else -1
            if above >= below:
                hi += 1
                acc += max(above, 0)
            else:
                lo -= 1
                acc += max(below, 0)
        return prices[lo], prices[hi]

    def location(self, price: float) -> str:
        """Kde je cena vůči value area: 'above' / 'inside' / 'below'."""
        va = self.value_area()
        if va is None:
            return "unknown"
        lo, hi = va
        if price > hi:
            return "above"
        if price < lo:
            return "below"
        return "inside"
