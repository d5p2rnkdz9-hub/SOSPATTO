// Traduzioni (en) delle schede di giurisprudenza: stesso nome file dell'originale
// in content/giurisprudenza/ (regole in TRADUZIONI.md).
module.exports = {
  lang: 'en',
  tags: ['giurisprudenza_tradotta'],
  layout: 'layouts/decisione.liquid',
  eleventyComputed: {
    permalink: (data) => data.prePatto ? false : `en/giurisprudenza/${data.page.fileSlug}.html`,
  },
};
