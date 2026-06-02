# Event kontrakt (Bookmap ↔ Python)

Newline-delimited JSON (ndjson), 1 event/řádek, pole `t` = epoch **nanosekundy**.
Tohle je jediné rozhraní mezi Bookmapem a Python pipeline — když ho dodržíš,
je jedno, jestli data tečou živě nebo z replaye.

## Trade (proběhlý obchod)
```json
{"t": 1717352000000000000, "type": "trade", "price": 5000.25, "size": 12, "aggressor": "buy"}
```
- `aggressor`: `"buy"` (agresor zvedl ask) / `"sell"` (agresor srazil bid)
- Mapování z Bookmapu: `TradesListener.onTrade(price, size, tradeInfo)` →
  `aggressor = "buy" if tradeInfo.isBidAggressor == false else ...`
  (v Bookmapu `isOtc`/`isBidAggressor`; ověř ve verzi svého API).

## Depth (update úrovně knihy, MBP)
```json
{"t": 1717352000000000000, "type": "depth", "side": "bid", "price": 4999.75, "size": 340}
```
- `size == 0` → úroveň zmizela.
- Mapování: `DepthDataListener.onDepth(isBid, price, size)`.

## BBO (best bid/offer)
```json
{"t": 1717352000000000000, "type": "bbo", "bid": 4999.75, "bid_size": 120, "ask": 5000.0, "ask_size": 95}
```

## Pravidla
- Eventy by měly chodit v pořadí podle `t`; harness je pro jistotu stejně seřadí.
- Ceny zaokrouhluj na tick instrumentu (ES = 0.25).
- Pro absorpci/likviditu je klíčový **Depth** (resting size) + **Trade** (co se sní).
  V prvním milníku stačí Trade; Depth zapojíme při ladění absorpce na reálných datech.
