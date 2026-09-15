import { createRequire } from 'module';
import markdownIt from 'markdown-it';
const require = createRequire(import.meta.url);

const mdRenderer = markdownIt({ html: true, linkify: true, typographer: true });

const vocabolarioTemi = require('./_data/vocabolarioTemi.js');
const slugPerTema = Object.fromEntries(vocabolarioTemi.map((t) => [t.label, t.slug]));
const { linkNorme, verificaHref } = require('./scripts/norme-linker.js');

const MESI = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno',
  'luglio', 'agosto', 'settembre', 'ottobre', 'novembre', 'dicembre'];

export default function (eleventyConfig) {
  eleventyConfig.ignores.add('node_modules/**');
  eleventyConfig.ignores.add('scripts/**');
  eleventyConfig.ignores.add('.claude/**');
  eleventyConfig.ignores.add('.git/**');
  // public/ e' copiato tale e quale: gli .md e .html interni (bundle testi
  // interattivi, diagramma) NON vanno processati come template
  eleventyConfig.ignores.add('public/**');
  // documentazione a livello root, non contenuto del sito
  eleventyConfig.ignores.add('*.md');

  // ---- filtri -----------------------------------------------------------
  eleventyConfig.addFilter('md', (str) => mdRenderer.render(str || ''));

  // label del macro-tema -> slug (per URL e data-temi); vedi _data/vocabolarioTemi.js
  eleventyConfig.addFilter('temaSlug', (label) => slugPerTema[label] || '');

  // 2026-05-12 -> "12 maggio 2026"
  eleventyConfig.addFilter('dataIt', (d) => {
    if (!d) return '';
    const dt = d instanceof Date ? d : new Date(d);
    return `${dt.getUTCDate()} ${MESI[dt.getUTCMonth()]} ${dt.getUTCFullYear()}`;
  });

  // ---- riferimenti normativi cliccabili nelle schede ------------------------
  // I layout delle schede racchiudono massima e corpo tra <!--norme:on--> e
  // <!--norme:off-->: lì le citazioni («art. 42, par. 1 Reg. (UE) 2024/1348»)
  // diventano a.xref verso il testo interattivo, con tooltip al passaggio del
  // mouse (src/scripts/norme-hover.js). Dettagli e limiti in scripts/norme-linker.js;
  // controllo mirato: npm run norme-check.
  const normeStats = [];
  eleventyConfig.addTransform('norme', function (content) {
    const out = (this.page && this.page.outputPath) || '';
    if (!out.endsWith('.html') || !content.includes('<!--norme:on')) return content;
    const st = { out, links: 0, impliciti: 0, warnings: [], orfani: [] };
    // le «Norme collegate» della scheda aiutano a risolvere le citazioni senza atto
    const hrefNorme = [...content.matchAll(/<a\s[^>]*href="(\/patto-interattivo\/[^"]+)"/g)].map((m) => m[1]);
    // `norme_impliciti: false` nel frontmatter (schede il cui oggetto è un atto senza testo
    // interattivo, es. il d.l. 100/2026): le citazioni senza atto restano testo
    content = content.replace(/<!--norme:on( impliciti=off)?-->([\s\S]*?)<!--norme:off-->/g, (m, off, inner) => {
      const r = linkNorme(inner, { hrefNorme, impliciti: !off });
      st.links += r.links; st.impliciti += r.impliciti;
      st.warnings.push(...r.warnings); st.orfani.push(...r.orfani);
      return r.html;
    });
    for (const m of content.matchAll(/<a\s[^>]*href="(\/patto-interattivo\/[^"]+)"/g)) {
      if (!verificaHref(m[1])) st.warnings.push(`href non risolve: ${m[1]}`);
    }
    normeStats.push(st);
    return content;
  });
  eleventyConfig.on('eleventy.after', () => {
    if (!normeStats.length) return;
    const tot = normeStats.reduce((a, s) => ({ l: a.l + s.links, i: a.i + s.impliciti, o: a.o + s.orfani.length }), { l: 0, i: 0, o: 0 });
    console.log(`[norme] ${normeStats.length} schede: ${tot.l} riferimenti linkati (${tot.i} dal contesto), ${tot.o} rimasti testo`);
    for (const s of normeStats) {
      for (const w of s.warnings) console.log(`[norme] ✖ ${s.out}: ${w}`);
      if (process.env.NORME_VERBOSE === '1') for (const o of s.orfani) console.log(`[norme] · ${s.out}: ${o}`);
    }
    normeStats.length = 0;
  });

  // ---- collezioni ---------------------------------------------------------
  // una scheda = un file .md in content/giurisprudenza/ o content/circolari/
  eleventyConfig.addCollection('giurisprudenza', (api) =>
    api.getFilteredByGlob('content/giurisprudenza/*.md').sort((a, b) => b.date - a.date));
  eleventyConfig.addCollection('circolari', (api) =>
    api.getFilteredByGlob('content/circolari/*.md').sort((a, b) => b.date - a.date));
  eleventyConfig.addCollection('dottrina', (api) =>
    api.getFilteredByGlob('content/dottrina/*.md').sort((a, b) => b.date - a.date));

  // ---- copie statiche -----------------------------------------------------
  eleventyConfig.addPassthroughCopy('src/styles');
  eleventyConfig.addPassthroughCopy('src/scripts');
  eleventyConfig.addPassthroughCopy('IMAGES');
  // il contenuto di public/ finisce alla RADICE del sito:
  // /patto-interattivo/, /diagramma/, /allegati/
  eleventyConfig.addPassthroughCopy({ 'public': '/' });
  eleventyConfig.addPassthroughCopy('robots.txt');

  return {
    dir: {
      input: '.',
      output: '_site',
      includes: '_includes',
    },
    // '11ty.js' serve solo per sitemap.11ty.js (genera /sitemap.xml)
    templateFormats: ['html', 'liquid', 'md', '11ty.js'],
    htmlTemplateEngine: 'liquid',
  };
}
