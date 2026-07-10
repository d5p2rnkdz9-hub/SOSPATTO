module.exports = {
  eleventyComputed: {
    // le pagine in src/pages/ escono alla radice: /testi.html, /diagramma.html, ...
    permalink: (data) => {
      if (data.pagination) return data.permalink;
      return `${data.page.fileSlug}.html`;
    },
  },
};
