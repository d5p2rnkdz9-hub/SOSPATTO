module.exports = {
  tags: ['giurisprudenza'],
  layout: 'layouts/decisione.liquid',
  eleventyComputed: {
    permalink: (data) => data.prePatto ? false : `giurisprudenza/${data.page.fileSlug}.html`,
  },
};
