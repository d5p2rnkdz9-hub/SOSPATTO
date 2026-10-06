// Traduzioni (en) delle schede di content/normativa/: stesso nome file dell'originale.
module.exports = {
  lang: 'en',
  tags: ['normativa_tradotte'],
  sezione: 'normativa',
  layout: 'layouts/circolare.liquid',
  eleventyComputed: {
    permalink: (data) => `en/normativa/${data.page.fileSlug}.html`,
  },
};
