// Genera /sitemap.xml (dichiarata in robots.txt).
// Due fonti di URL:
//   1. le pagine Eleventy (collections.all): home, pagine in src/pages/,
//      schede giurisprudenza/circolari — escluse le schede campione
//      (frontmatter `esempio: true`) e le pagine con `sitemap: false`;
//   2. i file .html copiati tali e quali da public/ (bundle patto-interattivo),
//      enumerati direttamente da filesystem perche' Eleventy li ignora —
//      esclusi il redirect meta-refresh /patto-interattivo/index.html,
//      la pagina tecnica /patto-interattivo/audit.html e il contenuto
//      dell'iframe /diagramma/index.html (duplicato di /diagramma.html).
const fs = require('fs');
const path = require('path');

const SITE = 'https://www.sospatto.it';

// percorsi (relativi a public/) da NON mettere in sitemap
const ESCLUSI_PUBLIC = new Set([
  'patto-interattivo/index.html', // redirect meta-refresh verso 1348.html
  'patto-interattivo/audit.html', // pagina tecnica di verifica del bundle
  'diagramma/index.html',         // iframe interno di /diagramma.html
]);

// escaping XML minimo per gli URL (& nei nomi file, per sicurezza)
const xmlEscape = (s) =>
  s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
   .replace(/"/g, '&quot;').replace(/'/g, '&apos;');

// Date -> "YYYY-MM-DD"
const isoDay = (d) => new Date(d).toISOString().slice(0, 10);

// raccoglie ricorsivamente i file .html sotto una cartella
function htmlSotto(dir) {
  const out = [];
  for (const voce of fs.readdirSync(dir, { withFileTypes: true })) {
    const pieno = path.join(dir, voce.name);
    if (voce.isDirectory()) out.push(...htmlSotto(pieno));
    else if (voce.isFile() && voce.name.endsWith('.html')) out.push(pieno);
  }
  return out;
}

class Sitemap {
  data() {
    return {
      permalink: '/sitemap.xml',
      eleventyExcludeFromCollections: true,
    };
  }

  render({ collections }) {
    const voci = [];

    // 1. pagine Eleventy
    for (const pagina of collections.all) {
      if (!pagina.url) continue;
      if (pagina.data.sitemap === false) continue;
      if (pagina.data.esempio) continue; // schede campione fittizie
      voci.push({
        loc: SITE + pagina.url,
        lastmod: isoDay(pagina.date),
      });
    }

    // 2. file statici copiati da public/
    const radicePublic = path.join(__dirname, 'public');
    for (const file of htmlSotto(radicePublic)) {
      const rel = path.relative(radicePublic, file).split(path.sep).join('/');
      if (ESCLUSI_PUBLIC.has(rel)) continue;
      voci.push({
        loc: `${SITE}/${rel}`,
        lastmod: isoDay(fs.statSync(file).mtime),
      });
    }

    voci.sort((a, b) => a.loc.localeCompare(b.loc));

    const corpo = voci
      .map((v) => `  <url>\n    <loc>${xmlEscape(v.loc)}</loc>\n    <lastmod>${v.lastmod}</lastmod>\n  </url>`)
      .join('\n');

    return `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${corpo}\n</urlset>\n`;
  }
}

module.exports = Sitemap;
