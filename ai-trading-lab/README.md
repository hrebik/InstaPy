# AI Trading Lab — Order-flow Replay Starter

První milník: **replay/backtest harness + feature engine** nad order-flow daty.
Běží na syntetickém feedu hned teď (bez Bookmapu); reálná data se zapojí na
stejný vstup.

## Princip
```
Bookmap (.bmf nahrávky)  ──Replay──►  L1 export add-on  ──►  eventy (ndjson)
                                                                    │
                                          STEJNÝ KÓD živě i v replayi
                                                                    ▼
                                   replay harness ─► feature engine ─► Snapshot
                                   (trend / volume profile / absorpce)     │
                                                          (později) Claude + Discord
```

## Rychlý start
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .

python run_replay.py                  # syntetická session
python run_replay.py feed.ndjson      # reálná nahrávka z Bookmapu
python validate_labels.py             # DEMO labeling↔engine validace
pytest -q
```

## Labeling ↔ validace (most ze streamu)
Při sledování streamu si značíš patterny, engine je ověří z tvých dat — viz
[`LABELING.md`](LABELING.md). `label.py` zapisuje, `validate_labels.py` porovnává.

## Co engine počítá (deterministicky, žádný LLM)
| Modul | Co dělá | Odpovídá na |
|---|---|---|
| `features/trend.py` | tick candles + HH/HL struktura | up / down / range |
| `features/volume_profile.py` | POC, value area | kde jsme, kam míříme |
| `features/orderflow.py` | kumulativní delta, **absorpce** | likvidita, vyčerpání |

`engine.py` je spojí a na uzavření každé tick-candle vyrobí `Snapshot` —
přesně to, co později poletí do Claude orchestrátoru a na Discord.

## Struktura
```
src/ai_trading/
  events.py            # KONTRAKT: normalizované eventy (Trade/Depth/BBO) + ndjson
  replay.py            # chronologický replay + k-way merge streamů
  feed_synthetic.py    # syntetická session pro vývoj bez Bookmapu
  engine.py            # replay → features → Snapshot
  features/            # trend, volume_profile, orderflow(absorpce)
bookmap/               # jak napsat L1 export add-on (Bookmap → ndjson)
tests/
run_replay.py
```

## Další kroky
1. Bookmap L1 export add-on (`bookmap/README.md`) → reálné `feed.ndjson`.
2. Ladit prahy feature engine na reálných nahrávkách proti vlastnímu čtení.
3. Risk manager + trade journal.
4. Claude orchestrátor (Snapshot → rozhodnutí + zdůvodnění) + Discord bot.
