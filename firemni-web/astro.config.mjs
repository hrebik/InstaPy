import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

// Zmen na svou produkcni domenu (kvuli sitemap.xml a canonical URL).
const SITE = process.env.SITE_URL || "https://www.tvujweb.cz";

// https://astro.build/config
export default defineConfig({
  site: SITE,
  integrations: [sitemap()],
  // Staticky vystup -> nasazeni na Cloudflare Pages je jen kopie souboru = zdarma a skaluje.
  output: "static",
});
