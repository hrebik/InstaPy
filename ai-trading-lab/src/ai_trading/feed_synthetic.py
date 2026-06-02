"""Syntetický order-flow feed.

Generuje věrohodnou session (trend + obraty + absorpce), aby šel celý
pipeline rozjet a testovat BEZ Bookmapu. Reálná data se pak jen zamění
za výstup z Bookmap export add-onu — stejný formát eventů.
"""
from __future__ import annotations

import random
from typing import Iterator

from .events import Event, Trade, BBO

NS = 1_000_000_000


def synthetic_session(
    seed: int = 7,
    start_price: float = 5000.0,
    tick: float = 0.25,
    n_trades: int = 4000,
) -> Iterator[Event]:
    """Vygeneruje session: up-trend → absorpce/obrat → down-trend.

    Vkládá Trade i BBO eventy. Absorpční fáze = hodně objemu na jedné ceně
    bez posunu (resting size se „dojídá"), pak obrat.
    """
    rng = random.Random(seed)
    price = start_price
    t = 0

    def emit_bbo() -> BBO:
        return BBO(
            t=t,
            bid=round(price - tick, 2),
            bid_size=rng.randint(20, 200),
            ask=round(price + tick, 2),
            ask_size=rng.randint(20, 200),
        )

    for i in range(n_trades):
        t += rng.randint(10_000_000, 50_000_000)  # 10–50 ms mezi eventy

        frac = i / n_trades
        if frac < 0.45:
            drift, buy_bias = +0.55, 0.62      # up-trend
        elif frac < 0.55:
            drift, buy_bias = 0.0, 0.50        # absorpce na vrcholu
        else:
            drift, buy_bias = -0.55, 0.38      # down-trend

        aggressor = "buy" if rng.random() < buy_bias else "sell"

        # absorpční pásmo: hodně objemu, cena se skoro nehne (drží na úrovni)
        if 0.45 <= frac < 0.55:
            size = rng.randint(50, 400)
            move = tick if rng.random() < 0.05 else 0.0
        else:
            size = rng.randint(1, 60)
            move = tick if rng.random() < abs(drift) else 0.0

        # agresor určuje směr; čistý drift vzniká z buy_bias výše
        price += move if aggressor == "buy" else -move
        price = round(price / tick) * tick

        yield Trade(t=t, price=round(price, 2), size=size, aggressor=aggressor)
        if i % 5 == 0:
            yield emit_bbo()
