const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

// Hash dei CSS/JS per il cache-busting ?v=<hash> (stesso meccanismo di sospermesso):
// ogni modifica ai file cambia l'hash e invalida la cache del browser.
function assetVersion() {
  const files = [
    'src/scripts/app.js',
    'src/scripts/mobile.js',
    'src/styles/main.css',
    'src/styles/components.css',
    'src/styles/mobile.css',
    'src/styles/mobile-fix.css',
    'src/styles/animations.css',
  ];
  const hash = crypto.createHash('md5');
  for (const f of files) {
    try {
      hash.update(fs.readFileSync(path.join(__dirname, '..', f)));
    } catch (e) {
      // ignora file mancanti
    }
  }
  return hash.digest('hex').slice(0, 8);
}

module.exports = {
  name: 'SOS Patto',
  // TODO: confermare il dominio esatto (registrato ma non ancora collegato)
  url: 'https://www.sospatto.it',
  email: 'alberto.pasquero@studiolegaleoltre.org',
  year: new Date().getFullYear(),
  defaultDescription:
    'SOS Patto — il Patto europeo su migrazione e asilo, spiegato: testi normativi interattivi, ' +
    'diagrammi delle procedure, giurisprudenza e circolari. Un progetto gratuito e senza fini di lucro.',
  assetVersion: assetVersion(),
};
