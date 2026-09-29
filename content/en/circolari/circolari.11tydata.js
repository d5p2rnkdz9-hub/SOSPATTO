// Traduzioni (en) delle schede delle circolari: stesso nome file dell'originale
// in content/circolari/ (regole in TRADUZIONI.md).
module.exports = {
  lang: 'en',
  tags: ['circolari_tradotte'],
  layout: 'layouts/circolare.liquid',
  eleventyComputed: {
    permalink: (data) => `en/circolari/${data.page.fileSlug}.html`,
  },
};
