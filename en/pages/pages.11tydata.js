module.exports = {
  eleventyComputed: {
    // le pagine in en/pages/ escono sotto /en/: /en/testi.html, /en/giurisprudenza.html, ...
    permalink: (data) => `en/${data.page.fileSlug}.html`,
  },
};
