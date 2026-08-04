"""Order flow: kumulativní delta, imbalance, detekce absorpce.

Absorpce = na dané ceně se zobchoduje velký objem, ale cena se nehne
(pasivní strana „pohlcuje" agresory). Klasický signál vyčerpání trendu.
Tady je rozumná heuristika — laditelná na reálných nahrávkách.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from ..events import Trade


@dataclass
class AbsorptionEvent:
    t: int
    price: float
    volume: float
    side: str          # 'bid' (pohlcují kupci dole) / 'ask' (prodejci nahoře)


@dataclass
class OrderFlow:
    # absorpce: objem na jedné ceně >= threshold a cena se přitom nehnula
    absorption_volume: float = 800.0
    price_window: int = 10          # přes kolik obchodů sledujeme „nehnutí"

    cum_delta: float = 0.0
    _level_price: Optional[float] = None
    _level_vol: float = 0.0
    _level_buy: float = 0.0
    _level_sell: float = 0.0
    _trades_at_level: int = 0
    absorptions: list[AbsorptionEvent] = field(default_factory=list)

    def on_trade(self, tr: Trade) -> Optional[AbsorptionEvent]:
        signed = tr.size if tr.aggressor == "buy" else -tr.size
        self.cum_delta += signed

        if tr.price != self._level_price:
            self._reset_level(tr)
            return None

        self._level_vol += tr.size
        self._trades_at_level += 1
        if tr.aggressor == "buy":
            self._level_buy += tr.size
        else:
            self._level_sell += tr.size

        if (
            self._level_vol >= self.absorption_volume
            and self._trades_at_level >= self.price_window
        ):
            # která strana pohlcuje = menšinový agresor (pasivní vítězí)
            side = "ask" if self._level_buy > self._level_sell else "bid"
            ev = AbsorptionEvent(tr.t, tr.price, self._level_vol, side)
            self.absorptions.append(ev)
            self._reset_level(tr)  # ať to nestřílí pořád dokola
            return ev
        return None

    def _reset_level(self, tr: Trade) -> None:
        self._level_price = tr.price
        self._level_vol = tr.size
        self._level_buy = tr.size if tr.aggressor == "buy" else 0.0
        self._level_sell = tr.size if tr.aggressor == "sell" else 0.0
        self._trades_at_level = 1
