// Traduzioni (fr) delle schede di content/normativa/: stesso nome file dell'originale.
module.exports = {
  lang: 'fr',
  tags: ['normativa_tradotte'],
  sezione: 'normativa',
  layout: 'layouts/circolare.liquid',
  eleventyComputed: {
    permalink: (data) => `fr/normativa/${data.page.fileSlug}.html`,
  },
};
