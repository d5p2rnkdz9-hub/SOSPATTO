module.exports = {
  eleventyComputed: {
    // le pagine in fr/pages/ escono sotto /fr/: /fr/testi.html, /fr/giurisprudenza.html, ...
    permalink: (data) => `fr/${data.page.fileSlug}.html`,
  },
};
