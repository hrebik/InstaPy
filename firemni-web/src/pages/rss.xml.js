import rss from "@astrojs/rss";
import { getCollection } from "astro:content";

export async function GET(context) {
  const posts = await getCollection("blog", ({ data }) => !data.draft);
  return rss({
    title: "Tvoje Firma – Blog",
    description: "Články, novinky a tipy z naší branže.",
    site: context.site,
    items: posts
      .sort((a, b) => b.data.pubDate - a.data.pubDate)
      .map((post) => ({
        title: post.data.title,
        pubDate: post.data.pubDate,
        description: post.data.description,
        link: `/blog/${post.slug}/`,
      })),
  });
}
