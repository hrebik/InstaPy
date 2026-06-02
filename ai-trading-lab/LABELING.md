# Labeling → validace (most stream ↔ engine)

Smyčka učení: při sledování streamu si značíš patterny → engine na stejných
časech ze **tvých** dat ověří, jestli to vidí taky. Z rozdílů ladíš prahy.

## 1. Záznam při sledování
Live (hodiny PC = tržní čas tvého Bookmap feedu):
```bash
python label.py absorption --side ask --price 21050 --note "vrchol, prodejci absorbují"
python label.py sweep --note "smetlo sell-side likviditu"
```
Z videa s konkrétním tržním časem (ET):
```bash
python label.py reversal --at "2026-06-02 15:30:00" --tz America/New_York
```
Label se přidá do `labels.ndjson` (nebo `--labels jmeno.ndjson`).

Typy: `absorption, sweep, refill, exhaustion, reversal, trend_up, trend_down`
(volné — přidej vlastní).

## 2. Validace proti datům
```bash
# DEMO na syntetice (žádné argumenty)
python validate_labels.py

# reálně: tvoje nahrávka z Bookmapu + tvoje labely
python validate_labels.py feed.ndjson labels.ndjson --tol 20
python validate_labels.py feed.ndjson labels.ndjson --tol 30 --match-side
```

Report ti řekne:
- **Recall** — kolik tvých labelů engine potvrdil (nízký = engine je moc přísný → změkčit prahy v `features/orderflow.py`).
- **Detekce navíc** — kde engine vidí absorpci, ale ty jsi nic neoznačil (možné falešné, nebo jsi to přehlédl → koukni a rozhodni).

## Klíčové: čas musí sedět
`t` v labelu i ve feedu musí být **stejné hodiny** (tržní/UTC epoch).
- Live: PC čas = čas exportu z Bookmapu → sedí samo.
- Z videa: zadej tržní čas události přes `--at` (+ `--tz`).
- Tolerance `--tol` pokrývá tvoji reakční dobu i drobný posun streamu.

## Jak z toho roste přesnost
1. Označíš sezení → `validate` → uvidíš miss/extra.
2. Doladíš `absorption_volume` / `price_window` v `features/orderflow.py`.
3. Opakuješ, dokud recall nesedí a falešných není moc.
4. Až bude engine spolehlivý, jeho výstup (Snapshot) jde do Claude orchestrátoru.
