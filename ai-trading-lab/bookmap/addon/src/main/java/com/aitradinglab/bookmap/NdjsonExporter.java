package com.aitradinglab.bookmap;

import java.io.IOException;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;

import velox.api.layer1.annotations.Layer1ApiVersion;
import velox.api.layer1.annotations.Layer1ApiVersionValue;
import velox.api.layer1.annotations.Layer1SimpleAttachable;
import velox.api.layer1.annotations.Layer1StrategyName;
import velox.api.layer1.data.InstrumentInfo;
import velox.api.layer1.data.TradeInfo;
import velox.api.layer1.simplified.Api;
import velox.api.layer1.simplified.CustomModule;
import velox.api.layer1.simplified.DepthDataListener;
import velox.api.layer1.simplified.InitialState;
import velox.api.layer1.simplified.TimeListener;
import velox.api.layer1.simplified.TradesListener;

/**
 * Bookmap L1 export add-on — zapisuje order-flow eventy do ndjson.
 *
 * Formát 1:1 dle ../../SCHEMA.md (Trade / Depth), pole `t` = epoch nanosekundy.
 * Funguje stejně živě i v Replay módu (přehrávání .bmf nahrávek), protože bere
 * čas z feedu (TimeListener), ne wall-clock.
 *
 * Výstup: ~/ai-trading-lab-feeds/<alias>.ndjson  (append, jeden soubor na instrument)
 *
 * POZOR: přesné názvy tříd/polí (TradeInfo.isBidAggressor, InstrumentInfo.pips)
 * se mohou mezi verzemi Bookmap API mírně lišit — ověř proti javadocu své
 * instalace (C:\Program Files\Bookmap\lib\bm-l1api-javadoc.jar) a DemoStrategies.
 */
@Layer1SimpleAttachable
@Layer1StrategyName("AI Trading Lab — ndjson export")
@Layer1ApiVersion(Layer1ApiVersionValue.VERSION2)
public class NdjsonExporter implements CustomModule, TradesListener, DepthDataListener, TimeListener {

    private static final long FLUSH_EVERY = 500;

    private Writer out;
    private double pips = 1.0;               // velikost ticku pro převod int ceny z onDepth
    private volatile long currentTimeNs = 0; // poslední známý čas z feedu (funguje i v replayi)
    private long sinceFlush = 0;

    @Override
    public void initialize(String alias, InstrumentInfo info, Api api, InitialState initialState) {
        this.pips = info.pips;
        try {
            Path dir = Paths.get(System.getProperty("user.home"), "ai-trading-lab-feeds");
            Files.createDirectories(dir);
            String safe = alias.replaceAll("[^A-Za-z0-9._-]", "_");
            Path file = dir.resolve(safe + ".ndjson");
            out = Files.newBufferedWriter(file, StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND);
            System.out.println("[ndjson-export] zapisuji do " + file);
        } catch (IOException e) {
            throw new RuntimeException("[ndjson-export] nelze otevřít výstupní soubor", e);
        }
    }

    /** Čas z feedu — poslední timestamp použijeme pro následující eventy. */
    @Override
    public void onTimestamp(long nanoseconds) {
        this.currentTimeNs = nanoseconds;
    }

    @Override
    public void onTrade(double price, int size, TradeInfo tradeInfo) {
        // isBidAggressor == true → agresivní PRODEJ (agresor srazil bid)
        String aggressor = tradeInfo.isBidAggressor ? "sell" : "buy";
        write("{\"t\":" + currentTimeNs
                + ",\"type\":\"trade\",\"price\":" + price
                + ",\"size\":" + size
                + ",\"aggressor\":\"" + aggressor + "\"}");
    }

    @Override
    public void onDepth(boolean isBid, int price, int size) {
        // v simplified API je cena v onDepth celočíselná v jednotkách pips
        double realPrice = price * pips;
        write("{\"t\":" + currentTimeNs
                + ",\"type\":\"depth\",\"side\":\"" + (isBid ? "bid" : "ask")
                + "\",\"price\":" + realPrice
                + ",\"size\":" + size + "}");
    }

    private synchronized void write(String line) {
        if (out == null) {
            return;
        }
        try {
            out.write(line);
            out.write('\n');
            if (++sinceFlush >= FLUSH_EVERY) {
                out.flush();
                sinceFlush = 0;
            }
        } catch (IOException e) {
            // neshazuj Bookmap kvůli I/O; jen zaloguj
            System.err.println("[ndjson-export] zápis selhal: " + e.getMessage());
        }
    }

    @Override
    public void stop() {
        synchronized (this) {
            if (out != null) {
                try {
                    out.flush();
                    out.close();
                } catch (IOException ignored) {
                    // konec
                }
                out = null;
            }
        }
    }
}
