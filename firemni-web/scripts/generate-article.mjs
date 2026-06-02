#!/usr/bin/env node
// Vygeneruje NAVRH clanku ve formatu Markdown pomoci Claude API.
// Vystup ulozi jako draft (draft: true) do src/content/blog/ -> nic nejde
// online bez tveho schvaleni. Spousteni:
//
//   npm run new-article -- "Tema clanku, klidne i s osnovou"
//
// Vyzaduje ANTHROPIC_API_KEY (viz .env.example).

import Anthropic from "@anthropic-ai/sdk";
import { writeFile, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const BLOG_DIR = join(__dirname, "..", "src", "content", "blog");

const topic = process.argv.slice(2).join(" ").trim();
if (!topic) {
  console.error('Pouziti: npm run new-article -- "Tema clanku"');
  process.exit(1);
}

// Z titulku udelame URL-friendly slug (vcetne odstraneni ceske diakritiky).
function slugify(text) {
  return text
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/(^-|-$)/g, "")
    .slice(0, 60);
}

const client = new Anthropic(); // cte ANTHROPIC_API_KEY z prostredi

// Strukturovany vystup: model vrati presne tato pole -> zadne parsovani "od oka".
const schema = {
  type: "object",
  properties: {
    title: { type: "string" },
    description: { type: "string" }, // SEO popisek, ~150 znaku
    tags: { type: "array", items: { type: "string" } },
    body: { type: "string" }, // telo clanku v Markdownu (bez H1 nadpisu)
  },
  required: ["title", "description", "tags", "body"],
  additionalProperties: false,
};

console.log(`Generuji navrh clanku na tema: ${topic}\n`);

const response = await client.messages.create({
  model: "claude-opus-4-8",
  max_tokens: 16000,
  thinking: { type: "adaptive" },
  output_config: { effort: "high", format: { type: "json_schema", schema } },
  system:
    "Jsi zkuseny cesky copywriter pro firemni blog. Pises vecne, srozumitelne, " +
    "bez prazdnych frazi a klise. Telo clanku pis v Markdownu s podnadpisy (##), " +
    "odstavci a obcas odrazkami. Nepridavej H1 nadpis (titulek je samostatne pole).",
  messages: [
    {
      role: "user",
      content: `Napis navrh clanku na firemni blog. Tema/osnova:\n\n${topic}`,
    },
  ],
});

// Pri output_config.format je prvni text blok validni JSON dle schematu.
const jsonText = response.content.find((b) => b.type === "text")?.text ?? "{}";
const article = JSON.parse(jsonText);

const today = new Date().toISOString().slice(0, 10);
const slug = slugify(article.title || topic);

// Frontmatter + telo. draft: true => clanek se zatim nepublikuje.
const frontmatter = [
  "---",
  `title: ${JSON.stringify(article.title)}`,
  `description: ${JSON.stringify(article.description)}`,
  `pubDate: ${today}`,
  `author: "Redakce"`,
  `tags: ${JSON.stringify(article.tags ?? [])}`,
  `draft: true`,
  "---",
  "",
].join("\n");

await mkdir(BLOG_DIR, { recursive: true });
const filePath = join(BLOG_DIR, `${slug}.md`);
await writeFile(filePath, frontmatter + article.body + "\n", "utf8");

console.log(`Hotovo. Navrh ulozen jako DRAFT:\n  ${filePath}\n`);
console.log(
  "Dalsi kroky: clanek si projdi/uprav, zmen 'draft: true' na 'false' a commitni (nebo otevri PR).",
);
