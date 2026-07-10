import { createRequire } from 'module';
import markdownIt from 'markdown-it';
const require = createRequire(import.meta.url);

const mdRenderer = markdownIt({ html: true, linkify: true, typographer: true });

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

  // 2026-05-12 -> "12 maggio 2026"
  eleventyConfig.addFilter('dataIt', (d) => {
    if (!d) return '';
    const dt = d instanceof Date ? d : new Date(d);
    return `${dt.getUTCDate()} ${MESI[dt.getUTCMonth()]} ${dt.getUTCFullYear()}`;
  });

  // ---- collezioni ---------------------------------------------------------
  // una scheda = un file .md in content/giurisprudenza/ o content/circolari/
  eleventyConfig.addCollection('giurisprudenza', (api) =>
    api.getFilteredByGlob('content/giurisprudenza/*.md').sort((a, b) => b.date - a.date));
  eleventyConfig.addCollection('circolari', (api) =>
    api.getFilteredByGlob('content/circolari/*.md').sort((a, b) => b.date - a.date));

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
    templateFormats: ['html', 'liquid', 'md'],
    htmlTemplateEngine: 'liquid',
  };
}
