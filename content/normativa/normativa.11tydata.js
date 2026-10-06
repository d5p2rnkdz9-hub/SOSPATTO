// Atti normativi SENZA testo interattivo (oggi il D.M. zone di frontiera): scheda con il PDF
// ufficiale, raggiungibile dalla card in «Normativa italiana» (_data/testi.js), MAI fra le
// circolari (REDAZIONE.md § 7). Decreti-legge, d.lgs. e leggi hanno invece il testo interattivo.
module.exports = {
  tags: ['normativa'],
  sezione: 'normativa',
  layout: 'layouts/circolare.liquid',
  eleventyComputed: {
    permalink: (data) => `normativa/${data.page.fileSlug}.html`,
  },
};
