#!/usr/bin/env bash
#
# setup-ai-trading-lab.sh
# -----------------------
# Jednorázový bootstrap skript, který:
#   1) založí soukromé GitHub repo "ai-trading-lab" (přes gh CLI),
#   2) vytvoří kompletní Python + Jupyter kostru projektu,
#   3) udělá první commit a pushne na GitHub,
#   4) nastaví venv a nainstaluje závislosti.
#
# Použití (na tvém PC):
#   chmod +x setup-ai-trading-lab.sh
#   ./setup-ai-trading-lab.sh
#
# Předpoklady:
#   - nainstalovaný git, python3, a GitHub CLI (gh) přihlášené přes `gh auth login`
#     (instalace gh: https://cli.github.com/)

set -euo pipefail

REPO_NAME="ai-trading-lab"
VISIBILITY="private"          # private | public
PYTHON_BIN="${PYTHON_BIN:-python3}"

echo "==> Zakládám projekt '${REPO_NAME}'"

if [ -d "${REPO_NAME}" ]; then
  echo "!! Složka '${REPO_NAME}' už existuje. Přejmenuj/smaž ji a spusť znovu."
  exit 1
fi

mkdir -p "${REPO_NAME}"
cd "${REPO_NAME}"

# --- struktura ---
mkdir -p src/ai_trading notebooks data tests .github/workflows

# --- README.md ---
cat > README.md <<'EOF'
# AI Trading Lab

Dílna na nástroje, strategie a backtesty pro algoritmické / AI obchodování.
Postupně sem přidáváme a ladíme jednotlivé nástroje.

## Struktura
- `src/ai_trading/` – znovupoužitelný kód (data, strategie, indikátory…)
- `notebooks/` – Jupyter notebooky pro výzkum a backtesty
- `data/` – lokální data (negitované, viz `.gitignore`)
- `tests/` – testy

## Rychlý start
```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # doplň své API klíče
jupyter lab                      # spustí notebooky
pytest                           # spustí testy
```

## Pravidla pro spolupráci
- Pracujeme ve větvích (`feature/nazev`), do `main` přes pull request.
- API klíče a tajemství **nikdy** necommitujeme – patří do `.env` (je v `.gitignore`).
- Před pushem: `git pull --rebase origin main`.
EOF

# --- .gitignore ---
cat > .gitignore <<'EOF'
# Python
__pycache__/
*.py[cod]
.venv/
venv/
*.egg-info/
.pytest_cache/
.ipynb_checkpoints/

# Tajemství / konfigurace
.env
*.key
secrets.*

# Data (necommitujeme velké/citlivé soubory)
data/*
!data/.gitkeep

# OS / editory
.DS_Store
.idea/
.vscode/
EOF

# --- requirements.txt ---
cat > requirements.txt <<'EOF'
# Jádro
numpy
pandas
python-dotenv

# Trh / data
yfinance
ccxt

# Analýza / vizualizace
matplotlib
ta

# Notebooky
jupyterlab
ipykernel

# Testy
pytest
EOF

# --- .env.example ---
cat > .env.example <<'EOF'
# Zkopíruj do .env a doplň reálné hodnoty. .env se NEcommituje.
EXCHANGE_API_KEY=
EXCHANGE_API_SECRET=
ALPHA_VANTAGE_KEY=
EOF

# --- balíček ---
cat > src/ai_trading/__init__.py <<'EOF'
"""AI Trading Lab – znovupoužitelné nástroje."""
__version__ = "0.0.1"
EOF

cat > src/ai_trading/config.py <<'EOF'
"""Načítání konfigurace a tajemství z .env."""
import os
from dotenv import load_dotenv

load_dotenv()

EXCHANGE_API_KEY = os.getenv("EXCHANGE_API_KEY", "")
EXCHANGE_API_SECRET = os.getenv("EXCHANGE_API_SECRET", "")
ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_KEY", "")
EOF

cat > src/ai_trading/data.py <<'EOF'
"""Stahování tržních dat."""
import pandas as pd
import yfinance as yf


def get_ohlcv(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Vrátí OHLCV data pro daný ticker přes yfinance."""
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=True)
    df.index.name = "date"
    return df
EOF

cat > src/ai_trading/strategy.py <<'EOF'
"""Ukázková strategie: křížení klouzavých průměrů (SMA crossover)."""
import pandas as pd


def sma_crossover_signals(close: pd.Series, fast: int = 20, slow: int = 50) -> pd.Series:
    """1 = long, -1 = short/flat, 0 = bez signálu (na začátku)."""
    sma_fast = close.rolling(fast).mean()
    sma_slow = close.rolling(slow).mean()
    signal = pd.Series(0, index=close.index)
    signal[sma_fast > sma_slow] = 1
    signal[sma_fast < sma_slow] = -1
    return signal
EOF

# --- test ---
cat > tests/test_smoke.py <<'EOF'
import pandas as pd
from ai_trading.strategy import sma_crossover_signals


def test_sma_crossover_runs():
    close = pd.Series(range(1, 101), dtype="float64")
    sig = sma_crossover_signals(close, fast=5, slow=10)
    assert len(sig) == len(close)
    assert set(sig.unique()).issubset({-1, 0, 1})
EOF

# --- pyproject (editovatelná instalace balíčku) ---
cat > pyproject.toml <<'EOF'
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "ai-trading-lab"
version = "0.0.1"
requires-python = ">=3.9"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
EOF

# --- ukázkový notebook ---
cat > notebooks/01_explore.ipynb <<'EOF'
{
 "cells": [
  {
   "cell_type": "markdown",
   "metadata": {},
   "source": ["# 01 – Explorace dat\n", "Ukázka: stáhni data a vykresli SMA crossover."]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import sys; sys.path.append('../src')\n",
    "from ai_trading.data import get_ohlcv\n",
    "from ai_trading.strategy import sma_crossover_signals\n",
    "\n",
    "df = get_ohlcv('BTC-USD', period='6mo')\n",
    "df['signal'] = sma_crossover_signals(df['Close'])\n",
    "df[['Close','signal']].tail()"
   ]
  }
 ],
 "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
 "nbformat": 4,
 "nbformat_minor": 5
}
EOF

# --- CI: spustí testy na každém push/PR ---
cat > .github/workflows/ci.yml <<'EOF'
name: CI
on:
  push:
    branches: [main]
  pull_request:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: pip install -e .
      - run: pytest -q
EOF

touch data/.gitkeep

# --- git init + GitHub repo + push ---
echo "==> Inicializuji git a zakládám GitHub repo (${VISIBILITY})"
git init -q
git add .
git commit -qm "Initial scaffold: Python + Jupyter AI trading lab"
git branch -M main

# gh repo create: založí repo, nastaví remote 'origin' a pushne
gh repo create "${REPO_NAME}" --"${VISIBILITY}" --source=. --remote=origin --push

# --- virtuální prostředí + závislosti ---
echo "==> Nastavuji virtuální prostředí"
"${PYTHON_BIN}" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q -e .

echo ""
echo "================================================================"
echo " Hotovo! Repo je na GitHubu a lokálně máš funkční projekt."
echo " Spusť:  cd ${REPO_NAME} && source .venv/bin/activate && jupyter lab"
echo "================================================================"
