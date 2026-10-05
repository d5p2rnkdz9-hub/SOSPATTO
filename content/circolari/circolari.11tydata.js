module.exports = {
  tags: ['circolari'],
  layout: 'layouts/circolare.liquid',
  eleventyComputed: {
    permalink: (data) => data.prePatto ? false : `circolari/${data.page.fileSlug}.html`,
  },
};
