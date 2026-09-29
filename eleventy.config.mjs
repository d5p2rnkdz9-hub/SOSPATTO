import { createRequire } from 'module';
import markdownIt from 'markdown-it';
const require = createRequire(import.meta.url);

const mdRenderer = markdownIt({ html: true, linkify: true, typographer: true });

const vocabolarioTemi = require('./_data/vocabolarioTemi.js');
const slugPerTema = Object.fromEntries(vocabolarioTemi.map((t) => [t.label, t.slug]));
const temaPerLabel = Object.fromEntries(vocabolarioTemi.map((t) => [t.label, t]));
const i18n = require('./_data/i18n.js');
const LINGUE_TRADOTTE = i18n.lingue.map((l) => l.code).filter((c) => c !== 'it');
const RE_PREFISSO = new RegExp(`^/(${LINGUE_TRADOTTE.join('|')})(?=/)`);
const DATE_FMT = {
  en: new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }),
  fr: new Intl.DateTimeFormat('fr-FR', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }),
};
const { linkNorme, verificaHref } = require('./scripts/norme-linker.js');
const { injectDir, devMiddleware } = require('./scripts/versioni-inject.js');

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
  const dataIt = (d) => {
    if (!d) return '';
    const dt = d instanceof Date ? d : new Date(d);
    return `${dt.getUTCDate()} ${MESI[dt.getUTCMonth()]} ${dt.getUTCFullYear()}`;
  };
  eleventyConfig.addFilter('dataIt', dataIt);

  // ---- lingue (regole in TRADUZIONI.md) --------------------------------------
  // {{ page.date | data: lang }} -> "12 maggio 2026" / "12 May 2026" / "12 mai 2026"
  eleventyConfig.addFilter('data', (d, lang) => {
    if (!d || !DATE_FMT[lang]) return dataIt(d);
    return DATE_FMT[lang].format(d instanceof Date ? d : new Date(d));
  });
  // label italiana del tema -> label nella lingua della pagina
  eleventyConfig.addFilter('temaLabel', (label, lang) => (temaPerLabel[label] && temaPerLabel[label][lang]) || label);
  // autorità (campo `corte`, in italiano) -> nome nella lingua; `breve` per le chip dei filtri
  eleventyConfig.addFilter('corte', (nome, lang, breve) => {
    const t = i18n.corti[nome] && i18n.corti[nome][lang];
    if (t) return t[breve ? 1 : 0];
    if (!breve) return nome;
    return String(nome).replace('Tribunale di ', 'Trib. ').replace(/Corte d'[Aa]ppello di /, 'App. ').replace(/Corte di [Cc]assazione/, 'Cassazione');
  });
  // percorso italiano -> stesso percorso nella lingua: '/giurisprudenza.html' | langUrl: 'en'
  const langUrl = (url, lang) => {
    const base = String(url || '/').replace(RE_PREFISSO, '');
    return !lang || lang === 'it' ? base : `/${lang}${base}`;
  };
  eleventyConfig.addFilter('langUrl', langUrl);
  // URL di questa pagina in un'altra lingua, se esiste; altrimenti la home di quella lingua.
  // {{ page.url | altUrl: 'en', collections.all }}
  let urlCache = { src: null, set: null };
  eleventyConfig.addFilter('altUrl', (url, lang, all) => {
    if (urlCache.src !== all) urlCache = { src: all, set: new Set((all || []).map((p) => p.url)) };
    const target = langUrl(url, lang);
    if (urlCache.set.has(target)) return target;
    return lang === 'it' ? '/' : `/${lang}/`;
  });
  eleventyConfig.addFilter('haAlt', (url, lang, all) => {
    if (urlCache.src !== all) urlCache = { src: all, set: new Set((all || []).map((p) => p.url)) };
    return urlCache.set.has(langUrl(url, lang));
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
    const lingua = (/^(?:\.\/)?_site\/(en|fr)\//.exec(out) || [])[1] || 'it';
    // le «Norme collegate» della scheda aiutano a risolvere le citazioni senza atto
    const hrefNorme = [...content.matchAll(/<a\s[^>]*href="(\/patto-interattivo\/[^"]+)"/g)].map((m) => m[1]);
    // `norme_impliciti: false` nel frontmatter (schede il cui oggetto è un atto senza testo
    // interattivo, es. il d.l. 100/2026): le citazioni senza atto restano testo
    content = content.replace(/<!--norme:on( impliciti=off)?-->([\s\S]*?)<!--norme:off-->/g, (m, off, inner) => {
      const r = linkNorme(inner, { hrefNorme, impliciti: !off, lang: lingua });
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

  // ---- selettore Nuovo / Vecchio / Modifiche, per articolo -------------------
  // Il bundle public/patto-interattivo/ è generato a monte e si ricopia con rsync:
  // il selettore si aggiunge qui, alle copie in _site/ (e al volo nel --serve, che
  // serve public/ senza copiarlo). Dettagli in scripts/versioni-inject.js.
  eleventyConfig.on('eleventy.after', ({ dir }) => {
    const fatti = injectDir(dir.output);
    if (fatti.length) console.log(`[versioni] selettore nuovo/vecchio/modifiche in ${fatti.join(', ')}`);
  });
  eleventyConfig.setServerOptions({ middleware: [devMiddleware] });

  // ---- collezioni ---------------------------------------------------------
  // una scheda = un file .md in content/giurisprudenza/ o content/circolari/
  eleventyConfig.addCollection('giurisprudenza', (api) =>
    api.getFilteredByGlob('content/giurisprudenza/*.md').sort((a, b) => b.date - a.date));
  eleventyConfig.addCollection('circolari', (api) =>
    api.getFilteredByGlob('content/circolari/*.md').sort((a, b) => b.date - a.date));
  eleventyConfig.addCollection('dottrina', (api) =>
    api.getFilteredByGlob('content/dottrina/*.md').sort((a, b) => b.date - a.date));
  // versioni tradotte: giurisprudenza_en, circolari_fr, ... Per ogni scheda italiana
  // la traduzione se c'è, altrimenti l'italiana (la card porta allora all'originale).
  for (const sez of ['giurisprudenza', 'circolari', 'dottrina']) {
    for (const lang of LINGUE_TRADOTTE) {
      eleventyConfig.addCollection(`${sez}_${lang}`, (api) => {
        const tr = new Map(api.getFilteredByGlob(`content/${lang}/${sez}/*.md`).map((p) => [p.page.fileSlug, p]));
        return api.getFilteredByGlob(`content/${sez}/*.md`)
          .map((p) => tr.get(p.page.fileSlug) || p)
          .sort((a, b) => b.date - a.date);
      });
    }
  }

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
