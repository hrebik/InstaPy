# Bookmap L1 export add-on (most do Pythonu)

Cíl: malý Bookmap add-on, který odebírá obchody + hloubku a **zapisuje
normalizované eventy** (viz `../SCHEMA.md`) do ndjson souboru. Funguje stejně
živě i při přehrávání `.bmf` nahrávek v Replay módu — takže z něj generuješ
data live i z historie.

## Fakta o Bookmap API (ověřeno v dokumentaci)
- Bookmap je v jádru **Java**; add-ony se píšou v Javě a dodávají jako JAR.
- **L1 API** (Layer 1): odběr `DepthDataListener` (plná hloubka, MBP) a
  `TradesListener`. Existuje „Simplified Framework" — k dispozici v **Javě i Pythonu**.
- Bookmap sám nahrává **`.bmf`** feed soubory (hloubka + BBO) do `C:/Bookmap/Feeds/`
  a umí je přehrát v Replay módu → tvoje „nonstop zapnuté" = automatický záznam.
- **L0 API** (vlastní datový zdroj) vyžaduje schválení „Quant solution" — NEPOTŘEBUJEME.
- Javadoc je součástí instalace: `C:\Program Files\Bookmap\lib\bm-l1api-javadoc.jar`.
- Příklady: https://github.com/BookmapAPI/DemoStrategies

## Doporučený postup
1. Naklonuj `DemoStrategies`, vezmi nejjednodušší příklad strategie/indikátoru.
2. Implementuj `TradesListener` (a později `DepthDataListener`).
3. V callbacku zapiš řádek ndjson dle `SCHEMA.md` (append do souboru, flush po dávce).
   - `t`: použij čas eventu z Bookmapu v ns (ne wall-clock), ať replay sedí.
4. Build → JAR → vlož do Bookmap add-onů, zapni.
5. Pusť Replay nahrávky → vznikne `feed.ndjson` → `python ../run_replay.py feed.ndjson`.

## Náčrt (Java L1, pseudokód)
```java
public class NdjsonExporter implements TradesListener, DepthDataListener {
    private final BufferedWriter out; // append do feed.ndjson

    @Override public void onTrade(double price, int size, TradeInfo info) {
        String aggr = info.isBidAggressor ? "sell" : "buy"; // ověř ve své verzi
        write(String.format(
            "{\"t\":%d,\"type\":\"trade\",\"price\":%s,\"size\":%d,\"aggressor\":\"%s\"}",
            nowNs(), price, size, aggr));
    }

    @Override public void onDepth(boolean isBid, int price, int size) {
        write(String.format(
            "{\"t\":%d,\"type\":\"depth\",\"side\":\"%s\",\"price\":%d,\"size\":%d}",
            nowNs(), isBid ? "bid" : "ask", price, size));
    }
}
```

> Poznámka: přesné názvy callbacků/polí (`isBidAggressor`, jednotky ceny jako
> int×tick vs. double) se mezi verzemi API liší — drž se javadocu své instalace
> a `DemoStrategies`. Python pipeline je na tom nezávislá: stačí dodržet ndjson.

## Alternativa bez psaní add-onu (rychlý prototyp)
Pokud nechceš hned do Javy: nahraj v Bookmapu data, použij vestavěný
**export/recorder**, a napiš malý konvertor do `SCHEMA.md` formátu. Pro reálné
order-flow featury (absorpce z resting size) ale nakonec L1 add-on chceš —
dává nejčistší data.
