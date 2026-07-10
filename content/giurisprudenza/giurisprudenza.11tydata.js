module.exports = {
  tags: ['giurisprudenza'],
  layout: 'layouts/decisione.liquid',
  eleventyComputed: {
    permalink: (data) => `giurisprudenza/${data.page.fileSlug}.html`,
  },
};
