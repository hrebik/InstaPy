#!/usr/bin/env node
// AI AUTOMATIZACE PROVOZU (spousti GitHub Action pri PR).
// Projde clanky v src/content/blog/ a doplni chybejici:
//   - SEO popisek (description), pokud chybi nebo je prazdny
//   - alt text k hlavnimu obrazku (heroImageAlt), pokud je heroImage bez altu
// Zmenene soubory zapise zpet; Action je pak commitne do PR.
//
// Zamerne NEpise zadny novy obsah ani nemeni telo clanku - jen metadata.
// Vyzaduje ANTHROPIC_API_KEY (v Action jako secret).

import Anthropic from "@anthropic-ai/sdk";
import { readFile, writeFile, readdir } from "node:fs/promises";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const BLOG_DIR = join(__dirname, "..", "src", "content", "blog");

// Minimalni cteni frontmatteru (bez YAML zavislosti) - staci na nase pole.
function splitFrontmatter(raw) {
  const m = raw.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  if (!m) return null;
  return { fm: m[1], body: m[2] };
}
function getField(fm, key) {
  const m = fm.match(new RegExp(`^${key}:\\s*(.*)$`, "m"));
  if (!m) return undefined;
  return m[1].trim().replace(/^["']|["']$/g, "");
}
function setOrInsertField(fm, key, value) {
  const line = `${key}: ${JSON.stringify(value)}`;
  if (new RegExp(`^${key}:`, "m").test(fm)) {
    return fm.replace(new RegExp(`^${key}:.*$`, "m"), line);
  }
  return `${fm}\n${line}`;
}

const client = new Anthropic();

async function ask(system, user) {
  const res = await client.messages.create({
    model: "claude-opus-4-8",
    max_tokens: 400,
    system,
    messages: [{ role: "user", content: user }],
  });
  return res.content.find((b) => b.type === "text")?.text.trim() ?? "";
}

const files = (await readdir(BLOG_DIR)).filter((f) => f.endsWith(".md"));
let changed = 0;

for (const file of files) {
  const path = join(BLOG_DIR, file);
  const raw = await readFile(path, "utf8");
  const parsed = splitFrontmatter(raw);
  if (!parsed) continue;

  let { fm } = parsed;
  const { body } = parsed;
  const title = getField(fm, "title") ?? file;
  let touched = false;

  // 1) Chybejici SEO popisek -> vygeneruj z titulku a uvodu clanku.
  const description = getField(fm, "description");
  if (!description) {
    const excerpt = body.replace(/\s+/g, " ").slice(0, 1200);
    const seo = await ask(
      "Jsi SEO specialista. Vrat POUZE jednu vetu cesky, max 155 znaku, " +
        "bez uvozovek, jako meta description pro vyhledavace.",
      `Titulek: ${title}\n\nUvod clanku: ${excerpt}`,
    );
    if (seo) {
      fm = setOrInsertField(fm, "description", seo.slice(0, 160));
      touched = true;
      console.log(`[${file}] doplnen SEO popisek`);
    }
  }

  // 2) heroImage bez altu -> dogeneruj alt text.
  const heroImage = getField(fm, "heroImage");
  const heroAlt = getField(fm, "heroImageAlt");
  if (heroImage && !heroAlt) {
    const alt = await ask(
      "Vrat POUZE strucny cesky alt text k obrazku (max 100 znaku, bez uvozovek), " +
        "vystizny pro pristupnost a SEO.",
      `Clanek s titulkem "${title}". Hlavni obrazek: ${heroImage}`,
    );
    if (alt) {
      fm = setOrInsertField(fm, "heroImageAlt", alt.slice(0, 120));
      touched = true;
      console.log(`[${file}] doplnen alt text obrazku`);
    }
  }

  if (touched) {
    await writeFile(path, `---\n${fm}\n---\n${body}`, "utf8");
    changed++;
  }
}

console.log(`Hotovo. Upraveno souboru: ${changed}.`);
