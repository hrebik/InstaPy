# Bookmap ndjson export add-on

L1 API add-on, který odebírá **Trades + Depth** a zapisuje je do ndjson dle
[`../../SCHEMA.md`](../../SCHEMA.md). Funguje živě i v **Replay** módu.

Výstup: `~/ai-trading-lab-feeds/<alias>.ndjson` (Windows: `C:\Users\<ty>\ai-trading-lab-feeds\`).

## Předpoklady
- **JDK 11+** (`java -version`). Když chybí: `winget install --id EclipseAdoptium.Temurin.17.JDK`
- **Gradle** (nebo použij systémový). Když chybí: `winget install --id Gradle.Gradle`
- Nainstalovaný **Bookmap** s API knihovnami (`C:\Program Files\Bookmap\lib`).

## Build
```powershell
cd "E:\Trading\AITRADING LAB\bookmap\addon"
gradle jar
```
Výsledek: `build\libs\ndjson-exporter-0.1.0.jar`.

### Když build spadne na Bookmap API dependency
Verze `com.bookmap.api:api-core:7.4.0.79` v `build.gradle` nemusí sedět na tvůj
Bookmap. Dvě řešení:
1. **Slaď verzi** — mrkni do `C:\Program Files\Bookmap\lib` na číslo verze a uprav `build.gradle`.
2. **Použij lokální JAR** — v `build.gradle` zakomentuj `compileOnly 'com.bookmap...'`
   a odkomentuj řádek `compileOnly files('C:/Program Files/Bookmap/lib/bm-l1api.jar')`
   (název JARu uprav dle skutečnosti).

## Instalace do Bookmapu
1. Bookmap → **Settings (⚙)** → **Configure API plugins** (nebo „Add-ons manager").
2. **Add** → vyber `ndjson-exporter-0.1.0.jar`.
3. Zapni add-on **„AI Trading Lab — ndjson export"** a přiřaď ho k instrumentu (NQ).
4. Add-on začne zapisovat do `~/ai-trading-lab-feeds/<alias>.ndjson`.

## Ověření propojení s Python pipeline
```powershell
# zkopíruj nahraný feed do repa a prožeň enginem
Copy-Item "$HOME\ai-trading-lab-feeds\*.ndjson" "E:\Trading\AITRADING LAB\feed.ndjson"
cd "E:\Trading\AITRADING LAB"
python run_replay.py feed.ndjson
```
Měl bys vidět snapshoty (trend / POC / delta / absorpce) z reálných dat.

## Nahrání historie (Replay)
Bookmap sám nahrává `.bmf` do `C:/Bookmap/Feeds/`. Pusť **Replay** té nahrávky
se zapnutým add-onem → vznikne ndjson z historických dat, stejný formát jako živě.

## Poznámky k API
- Časy bereme z `TimeListener.onTimestamp` (feed-time) → sedí i v replayi.
- `onDepth` dává cenu jako `int` v jednotkách `pips` → převádíme `price * pips`.
- `TradeInfo.isBidAggressor == true` → agresivní prodej (`aggressor: "sell"`).
- Přesné signatury ověř v `bm-l1api-javadoc.jar` a v příkladech
  [BookmapAPI/DemoStrategies](https://github.com/BookmapAPI/DemoStrategies).
