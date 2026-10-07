#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Compone public/patto-interattivo/ dai generatori di questa cartella.

    python3 tools/testi-interattivi/assemble.py            # build completa + copia
    python3 tools/testi-interattivi/assemble.py --no-build # solo copia (output già pronti)
    python3 tools/testi-interattivi/assemble.py --no-patto # salta il builder del Patto (12 s)

Passi:
  1. build del Patto (`Testi definitivi Regolamenti/build_patto_interattivo.py`, da EUR-Lex);
  2. due passate dei builder delle leggi italiane elencati in `sites.json` (due perché ogni
     testo porta nelle anteprime gli articoli degli altri);
  3. copia nel bundle dei SOLI file di contenuto:
       - Patto: le pagine `<num>.html`, `ext-*.html`, `audit.html`, `assets/data.js`,
         `assets/data-ext/`; la hub `index.html` solo se nel bundle manca (lì è un redirect
         a /testi.html, lo mantiene `scripts/inject_bundle_logo.py`);
       - leggi: `<slug>/index.html`, `assets/data.js`, `assets/amend.css`, `assets/data-ext/`.
     `style.css` e `app.js` del bundle NON si toccano: sono di SOS Patto (tema blu,
     blocco `sospatto:brand`), i generatori portano ancora il tema di origine.
  4. pagine del Patto: breadcrumb «⌂ Patto UE › <atto>» nella topbar e link «⌂ Patto UE»
     nel pannello a comparsa, come facevano le leggi (ereditato da assemble_deploy.py).

Dopo: `npm run retheme && npm run seo && npm run logo` (meta SEO, logo, «⌂ SOS Patto»,
cache-buster). `npm run testi` fa tutto in sequenza. Controllo finale:
`git status --short public/patto-interattivo` deve mostrare solo contenuto davvero nuovo.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
BUNDLE = os.path.join(REPO, 'public', 'patto-interattivo')
SITES = json.load(open(os.path.join(HERE, 'sites.json'), encoding='utf-8'))
PACT_SRC = os.path.join(HERE, SITES['pact_src'])
PACT_BUILDER = os.path.join(os.path.dirname(PACT_SRC), 'build_patto_interattivo.py')


def sh(script, cwd):
    r = subprocess.run([sys.executable, script], cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit('  ! build fallita: %s\n%s' % (os.path.join(cwd, script), r.stdout[-2000:] + r.stderr[-2000:]))


def build_pact():
    print('1) Patto (10 atti + atti esterni)…')
    sh(os.path.basename(PACT_BUILDER), os.path.dirname(PACT_BUILDER))


def build_laws():
    builders = []
    for key, m in SITES['acts'].items():
        d = os.path.join(HERE, m['src'])
        scr = glob.glob(os.path.join(d, 'build_dl*.py'))
        if not scr:
            sys.exit('  ! nessun build script in %s' % d)
        os.makedirs(os.path.join(d, 'assets'), exist_ok=True)
        builders.append((d, os.path.basename(scr[0])))
    for p in (1, 2):
        for d, scr in builders:
            sh(scr, d)
        print('2) passata %d: ricostruiti %d testi' % (p, len(builders)))


def copy_file(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def copy_dir(src, dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns('.DS_Store', '* [0-9]*'))


HOME_OLD = '<a class="home" href="index.html">&#8962; Indice</a>'


def enhance_pact_page(path):
    """Breadcrumb + link al Patto nel pannello (idempotente)."""
    h = orig = open(path, encoding='utf-8').read()
    if HOME_OLD in h and 'home-here' not in h:
        mt = re.search(r'<title>(.*?)</title>', h, re.S)
        label = (mt.group(1).split(' — ')[0].strip() if mt else '')
        h = h.replace(HOME_OLD, '<a class="home" href="index.html">&#8962; Patto UE</a> '
                                '<a class="home-here" href="#top">%s</a>' % label, 1)
    if '<div class="panel-foot">' in h and 'panel-home' not in h:
        h = h.replace('<div class="panel-foot">',
                      '<div class="panel-foot"><a class="panel-home" href="index.html">&#8962; Patto UE</a>', 1)
    if h != orig:
        open(path, 'w', encoding='utf-8').write(h)


def copy_pact():
    n = 0
    for src in sorted(glob.glob(os.path.join(PACT_SRC, '*.html'))):
        name = os.path.basename(src)
        dst = os.path.join(BUNDLE, name)
        if name == 'index.html':
            if os.path.exists(dst):
                continue          # la hub del sito è un redirect: non si sovrascrive
        copy_file(src, dst)
        if name != 'index.html':
            enhance_pact_page(dst)
        n += 1
    copy_file(os.path.join(PACT_SRC, 'assets', 'data.js'), os.path.join(BUNDLE, 'assets', 'data.js'))
    ext = os.path.join(PACT_SRC, 'assets', 'data-ext')
    if os.path.isdir(ext):
        copy_dir(ext, os.path.join(BUNDLE, 'assets', 'data-ext'))
    print('3) Patto: %d pagine, assets/data.js, assets/data-ext/' % n)


def copy_law(m):
    src = os.path.join(HERE, m['src'])
    dst = os.path.join(BUNDLE, m['slug'])
    copy_file(os.path.join(src, 'index.html'), os.path.join(dst, 'index.html'))
    for f in ('data.js', 'amend.css'):
        p = os.path.join(src, 'assets', f)
        if os.path.exists(p):
            copy_file(p, os.path.join(dst, 'assets', f))
    ext = os.path.join(src, 'assets', 'data-ext')
    if os.path.isdir(ext):
        copy_dir(ext, os.path.join(dst, 'assets', 'data-ext'))
    for f in ('style.css', 'app.js'):          # tema: se manca (cartella nuova) parte da quello delle leggi
        p = os.path.join(dst, 'assets', f)
        if not os.path.exists(p):
            copy_file(os.path.join(BUNDLE, 'dlgs-251-2007', 'assets', f), p)
            print('   ! %s/assets/%s mancava: copiato da dlgs-251-2007' % (m['slug'], f))
    print('   + %s/  (%s)' % (m['slug'], m['label']))


def main(argv):
    if '--no-build' not in argv:
        if '--no-patto' not in argv:
            build_pact()
        build_laws()
    if not os.path.isdir(BUNDLE):
        sys.exit('bundle non trovato: %s' % BUNDLE)
    copy_pact()
    for key, m in SITES['acts'].items():
        copy_law(m)
    print('Fatto. Ora: npm run retheme && npm run seo && npm run logo  '
          '(poi git status --short public/patto-interattivo)')


if __name__ == '__main__':
    main(sys.argv[1:])
