// Traduzioni (fr) delle schede di giurisprudenza: stesso nome file dell'originale
// in content/giurisprudenza/ (regole in TRADUZIONI.md).
module.exports = {
  lang: 'fr',
  tags: ['giurisprudenza_tradotta'],
  layout: 'layouts/decisione.liquid',
  eleventyComputed: {
    permalink: (data) => `fr/giurisprudenza/${data.page.fileSlug}.html`,
  },
};
