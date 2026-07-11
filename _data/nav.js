// Menu di navigazione. Solo italiano per ora: quando arriveranno altre lingue,
// aggiungere chiavi 'en', 'fr', ... con la stessa struttura (come su sospermesso).
module.exports = {
  it: {
    dropdowns: [
      {
        label: 'Testi normativi',
        href: '/testi.html',
        items: [
          { label: 'Normativa UE', href: '/testi.html' },
          { label: 'Normativa italiana', href: '/norme-italiane.html' },
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
