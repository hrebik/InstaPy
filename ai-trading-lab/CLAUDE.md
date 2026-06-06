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

## 🧰 Tech stack
Data: Bookmap L1 API → ndjson · Engine: Python (stdlib) + pytest ·
AI: Claude API (později) · Notifikace: Discord (později).
