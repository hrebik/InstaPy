# AI Trading Lab

Poloautomatický obchodní systém pro futures (NQ/ES) postavený na **order-flow analýze**.
Deterministický feature engine počítá stav trhu; AI (Claude) nad tím dělá rozhodnutí
a zdůvodnění. Začínáme od dat a replaye, ne od živého obchodování.

## 📌 Projektový hub (Notion)
Struktura projektu, statusy tasků a co je hotové/chystá se:
**https://app.notion.com/p/377f864295a08133827edae136223e7e**
→ Po větším kroku aktualizuj status příslušného tasku (nebo o to požádej uživatele).

## 🏗️ Architektura
```
Bookmap (.bmf nahrávky, běží nonstop)
   │  Replay mód
   ▼
L1 export add-on  ──►  normalizované eventy (ndjson)   ← KONTRAKT mezi světy (SCHEMA.md)
   ▼
Python replay harness  ──►  feature engine (trend / volume profile / absorpce)
   ▼
Snapshot  ──►  (později) Claude orchestrátor + Discord
```
**Klíčový princip:** feature engine je úplně stejný kód živě i v replayi. Co se odladí
na nahrávkách, běží 1:1 živě.

## ⚙️ Zásady designu (DRŽ SE JICH)
- Feature engine je deterministický a rychlý — **žádný LLM uvnitř**.
- Live i replay sdílí stejný kód (liší se jen zdroj eventů).
- LLM (Claude) běží až nad `Snapshot` na rozhodovacím taktu, ne v horké smyčce.
- **Žádné živé obchodování** dřív, než engine spolehlivě potvrzuje ruční labely.

## 📁 Struktura repa
- `src/ai_trading/events.py` — kontrakt eventů (Trade/Depth/BBO, ndjson)
- `src/ai_trading/replay.py` — chronologický replay + k-way merge
- `src/ai_trading/feed_synthetic.py` — syntetická data pro vývoj bez Bookmapu
- `src/ai_trading/features/` — `trend.py`, `volume_profile.py`, `orderflow.py` (absorpce)
- `src/ai_trading/engine.py` — replay → features → `Snapshot`
- `src/ai_trading/labels.py` + `validate.py` — labeling a validace proti enginu
- `label.py`, `validate_labels.py`, `run_replay.py` — CLI
- `bookmap/README.md` — návod na L1 export add-on
- `SCHEMA.md`, `LABELING.md`, `README.md` — kontrakt, postupy, přehled

## 🧪 Vývojový workflow
- Pracuj na feature větvích, commituj s jasnými zprávami, pushuj.
- Nové featury **vždy s testem**.
- Spuštění testů (PowerShell / Windows):
  ```powershell
  $env:PYTHONPATH="src"; python -m pytest -q
  ```
  (Linux/macOS: `PYTHONPATH=src python -m pytest -q`)
- Demo: `python run_replay.py` · validace: `python validate_labels.py`
- Cílový stav: **8+ testů prochází**.

## 🎯 Aktuální priorita
**Bookmap L1 export add-on (Java skeleton)** — dle `bookmap/README.md` a `SCHEMA.md`.
Cíl: ze živého Bookmapu vznikne `feed.ndjson`, který prožene `python run_replay.py feed.ndjson`.

## 🧱 Konvence kódu
- **Python 3.10+**, type hints všude (`from __future__ import annotations`).
- **Stdlib-first** — závislost přidávej, jen když je vážně potřeba (engine běží na čisté stdlib).
- **Dataclasses** na datové struktury (`Trade`, `Snapshot`, `Candle`…); neměnné (`frozen=True`) tam, kde to dává smysl (eventy).
- **Malé, zaměřené moduly** — jeden feature = jeden soubor v `features/`. Žádné boží třídy.
- **Stav drž ve třídě featury** (`@dataclass` s `on_trade()` metodou), ne v globálech.
- **Komentáře a docstringy česky**, krátké a k věci (proč, ne co). Názvy symbolů anglicky.
- **Pojmenování:** moduly/funkce `snake_case`, třídy `PascalCase`, konstanty `UPPER_SNAKE`.
- **Čísla/prahy** dávej jako pojmenovaná pole dataclassu s defaultem (laditelné), ne magické konstanty v těle.
- **Žádný I/O ve feature enginu** — featury dostávají eventy, nevědí, odkud jsou (live vs replay).
- **Formát:** drž se PEP 8, řádek ~99 znaků.

### Jak přidat novou featuru (vzor)
1. Nový soubor `src/ai_trading/features/<jmeno>.py` — `@dataclass` s metodou `on_trade(self, tr: Trade)`.
2. Zapoj ji v `engine.py` (instanci v `__post_init__`, volání ve smyčce, výstup do `Snapshot`).
3. Přidej test do `tests/test_<jmeno>.py` — ověř na syntetickém feedu (`synthetic_session`).
4. Spusť testy, aktualizuj status tasku v Notion hubu.

## 🧰 Tech stack
Data: Bookmap L1 API → ndjson · Engine: Python (stdlib) + pytest ·
AI: Claude API (později) · Notifikace: Discord (později).
