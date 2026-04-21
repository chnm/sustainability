// Build the Pagefind index from data/items.json.
// Invoked at image-build time (see Dockerfile's `index` stage) and runnable
// locally as `node pagefind_index.js`.
//
// Replaces the HTML-crawl mode of `npx pagefind` — no theme-coupled
// selectors, no data-pagefind-* annotation pass, tiny index, real facets.

import { createIndex } from "pagefind";
import { readFile } from "node:fs/promises";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const siteRoot = resolve(process.argv[2] ?? here);
const outputPath = resolve(process.argv[3] ?? `${siteRoot}/pagefind`);
const itemsPath = `${siteRoot}/data/items.json`;

const stripHtml = (s = "") => s.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();

const items = JSON.parse(await readFile(itemsPath, "utf8"));
const { errors: createErrors, index } = await createIndex({});
if (createErrors?.length) {
  console.error("createIndex errors:", createErrors);
  process.exit(1);
}

let indexed = 0;
for (const item of items) {
  if (!item.public) continue;

  const contentParts = [
    item.title,
    stripHtml(item.description),
    ...(item.creators ?? []).map(stripHtml),
    ...(item.subjects ?? []).map(stripHtml),
    stripHtml(item.rights),
    stripHtml(item.coverage),
    item.collection_name,
    item.type_name,
    ...(item.tags ?? []),
  ].filter(Boolean);

  const filters = {};
  if (item.type_name) filters.type = [item.type_name];
  if (item.collection_name) filters.collection = [item.collection_name];
  if (item.tags?.length) filters.tags = item.tags;

  const meta = {
    title: item.title || `Item ${item.id}`,
  };
  if (item.thumbnail) meta.image = item.thumbnail;

  const { errors: addErrors } = await index.addCustomRecord({
    url: `/items/show/${item.id}.html`,
    content: contentParts.join("\n"),
    language: "en",
    meta,
    filters,
    sort: {
      added: item.added || "",
      modified: item.modified || "",
    },
  });
  if (addErrors?.length) {
    console.error(`addCustomRecord errors for item ${item.id}:`, addErrors);
    process.exit(1);
  }
  indexed++;
}

const { errors: writeErrors } = await index.writeFiles({ outputPath });
if (writeErrors?.length) {
  console.error("writeFiles errors:", writeErrors);
  process.exit(1);
}

console.log(`indexed=${indexed} out=${outputPath}`);
