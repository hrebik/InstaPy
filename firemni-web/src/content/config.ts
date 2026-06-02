import { defineCollection, z } from "astro:content";

// Blog jako "content collection" = clanky jsou Markdown soubory v repu.
// Kazdy update obsahu jde pres Git (commit/PR) nebo pres klikaci CMS na /admin,
// ktery commitne za tebe. Schema nize hlida, ze kazdy clanek ma povinna pole.
const blog = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    // SEO popisek - muze ho doplnit AI automatizace (GitHub Action) pri PR.
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    author: z.string().default("Redakce"),
    // Hlavni obrazek + jeho alt text (alt muze doplnit AI).
    heroImage: z.string().optional(),
    heroImageAlt: z.string().optional(),
    tags: z.array(z.string()).default([]),
    // draft: true => clanek se nepublikuje (hodi se pro AI-generovane navrhy).
    draft: z.boolean().default(false),
  }),
});

export const collections = { blog };
