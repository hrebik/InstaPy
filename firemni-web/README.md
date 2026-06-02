# Firemní web s blogem (Astro + Decap CMS + AI)

Moderní, rychlý a levný náhrada za WordPress:

- **Astro** – staticky generovaný web (firemní stránky + blog). Bleskově rychlý, výborné SEO.
- **Obsah v Gitu** – články jsou Markdown soubory v `src/content/blog/`. Každý update jde přes GitHub.
- **Decap CMS** – klikací administrace na `/admin`, která commituje do GitHubu (web rozhraní jen když ho potřebuješ).
- **Cloudflare Pages** – hosting zdarma, automatický deploy při push, globální CDN (škáluje samo).
- **Claude API + GitHub Actions** – AI generování návrhů článků a automatika SEO/alt textů.

---

## 1. Rychlý start (lokálně)

Potřebuješ [Node.js](https://nodejs.org) 20+.

```bash
npm install
cp .env.example .env      # doplň ANTHROPIC_API_KEY (kvuli AI skriptum)
npm run dev               # web bezi na http://localhost:4321
```

Build pro produkci: `npm run build` (výsledek je ve složce `dist/`).

### Struktura

```
src/
  content/blog/      # ČLÁNKY (Markdown) – tady přibývá obsah
  pages/             # statické stránky (index, o-nas, kontakt, blog)
  layouts/ components/ styles/
public/
  admin/             # Decap CMS (klikací administrace)
  _redirects         # 301 redirecty pro migraci z WordPressu
scripts/             # AI skripty (generování + enrich)
.github/workflows/   # CI build + AI automatizace při PR
```

---

## 2. Založení GitHub repozitáře a první nasazení

Tento scaffold vznikl ve větvi `claude/wordpress-ai-migration-IMaa5` repozitáře InstaPy.
Přesuň ho do vlastního čistého repa:

```bash
# 1) Na github.com založ prázdný repozitář, např. "firemni-web" (bez README).

# 2) Lokálně zkopíruj jen tuto složku do nového repa:
cp -r firemni-web /cesta/k/firemni-web && cd /cesta/k/firemni-web
git init && git add . && git commit -m "init: firemni web (Astro + AI)"
git branch -M main
git remote add origin https://github.com/hrebik/firemni-web.git
git push -u origin main
```

> V `public/admin/config.yml` uprav `repo: hrebik/firemni-web` na svůj skutečný repozitář.

---

## 3. Hosting na Cloudflare Pages (zdarma)

1. [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
2. Vyber repozitář `firemni-web`.
3. Build nastavení:
   - **Framework preset:** Astro
   - **Build command:** `npm run build`
   - **Output directory:** `dist`
4. **Save and Deploy.** Od teď se každý push do `main` nasadí automaticky.
5. Doménu připojíš v **Custom domains** (Cloudflare ti dá DNS záznamy).

Cloudflare Pages má neomezený traffic i počet webů zdarma – ideální až budeš mít webů víc.

---

## 4. Klikací administrace (Decap CMS) na `/admin`

Decap CMS běží na `tvujweb.cz/admin/` a ukládá změny jako commity/PR do GitHubu.
Aby se editor mohl přihlásit přes GitHub, je potřeba **OAuth**. Nejjednodušší varianty:

- **Cloudflare Worker OAuth** – nasaď [`decap-proxy`](https://github.com/sterlingwes/decap-proxy) jako Worker a v Cloudflare nastav GitHub OAuth App. (Doporučeno, zůstaneš celý na Cloudflare.)
- Nebo použij hostovaný OAuth (Netlify Identity / jiný provider) dle dokumentace Decap CMS.

Postup (GitHub OAuth App):
1. GitHub → Settings → Developer settings → **OAuth Apps** → New.
2. Authorization callback URL = URL tvého OAuth Workeru.
3. `Client ID` a `Client Secret` vlož do konfigurace Workeru.

Detaily: <https://decapcms.org/docs/backends-overview/>. Bez OAuth funguje CMS i v **local backendu** pro testování (`npx decap-server` + `local_backend: true` v `config.yml`).

---

## 5. AI funkce

### Generování návrhu článku (na vyžádání)

```bash
npm run new-article -- "Jak jsme zrychlili web 5x a co to přineslo zákazníkům"
```

Vytvoří `src/content/blog/<slug>.md` jako **draft** (`draft: true`) – nic nejde online,
dokud článek neprojdeš, neupravíš a draft nepřepneš na `false`.

### Automatika SEO + alt textů (při PR)

Workflow `.github/workflows/ai-content.yml` se spustí při PR, který mění blog, a:
- doplní chybějící `description` (SEO meta),
- doplní `heroImageAlt` k obrázkům bez altu,
- výsledek commitne zpět do PR.

**Nastavení:** v GitHubu → repo → Settings → **Secrets and variables** → Actions →
přidej secret `ANTHROPIC_API_KEY`.

> Modely a cenu řídíš v `scripts/*.mjs` (výchozí `claude-opus-4-8`). Klíč získáš na
> <https://console.anthropic.com>. Generování článku stojí jednotky korun, SEO/alt texty haléře.

---

## 6. Migrace obsahu z WordPressu

1. **Export → Markdown.** Použij např. [`wordpress-export-to-markdown`](https://github.com/lonekorean/wordpress-export-to-markdown)
   (vezme WP export XML a vyrobí `.md` soubory + stáhne obrázky). Soubory dej do `src/content/blog/`,
   obrázky do `public/`.
2. **Doplň frontmatter** – každý článek potřebuje `title`, `description`, `pubDate` (schema viz `src/content/config.ts`).
   Chybějící `description` ti doplní AI workflow z bodu 5.
3. **Redirecty.** Stará WP URL → nová URL zapiš do `public/_redirects` (formát `/stara/ /nova/ 301`).
   Seznam starých URL získáš z `sitemap.xml` původního webu.
4. **Přepni doménu** na Cloudflare až bude nový web hotový.

---

## 7. Časem víc webů

Tento repozitář je zároveň **šablona**. Nový web:

1. Na GitHubu klikni **Use this template** (nebo repo naklonuj).
2. Změň obsah (`src/content`, `src/pages`), barvy (`src/styles/global.css`) a `repo:` v `public/admin/config.yml`.
3. Připoj na Cloudflare Pages (bod 3). Hotovo.

Sdílené části (AI skripty, komponenty) můžeš později vytáhnout do vlastního npm balíčku,
ať se opravy promítnou do všech webů najednou.
