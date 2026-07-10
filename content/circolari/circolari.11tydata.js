module.exports = {
  tags: ['circolari'],
  layout: 'layouts/circolare.liquid',
  eleventyComputed: {
    permalink: (data) => `circolari/${data.page.fileSlug}.html`,
  },
};
