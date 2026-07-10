// Menu di navigazione. Solo italiano per ora: quando arriveranno altre lingue,
// aggiungere chiavi 'en', 'fr', ... con la stessa struttura (come su sospermesso).
module.exports = {
  it: {
    dropdowns: [
      {
        label: 'Testi normativi',
        href: '/testi.html',
        items: [
          { label: 'Tutti i testi', href: '/testi.html' },
          { label: 'Consultazione interattiva', href: '/patto-interattivo/index.html' },
          { label: 'Regolamento procedure', href: '/patto-interattivo/1348.html' },
          { label: 'Regolamento RAMM (Dublino)', href: '/patto-interattivo/1351.html' },
          { label: 'Regolamento screening', href: '/patto-interattivo/1356.html' },
          { label: 'Norme italiane novellate', href: '/testi.html#norme-italiane' },
        ],
      },
      {
        label: 'Diagramma',
        href: '/diagramma.html',
        items: [],
      },
      {
        label: 'Giurisprudenza',
        href: '/giurisprudenza.html',
        items: [],
      },
      {
        label: 'Circolari',
        href: '/circolari.html',
        items: [],
      },
      {
        label: 'Il progetto',
        href: '/il-progetto.html',
        items: [],
      },
    ],
  },
};
