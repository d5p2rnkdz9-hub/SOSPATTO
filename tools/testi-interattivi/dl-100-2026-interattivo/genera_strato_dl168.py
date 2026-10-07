#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera amendments_dl168.json: lo strato del d.l. 29 settembre 2026, n. 168 (art. 4, comma 1)
sul d.l. 100/2026, confrontando lo snapshot Normattiva del 29/9/2026 (testo con il d.l. 144) con
quello del 6/10/2026 (vigente). Le (( )) di Normattiva si tolgono come in genera_strato_dl144.py.

  a) art. 17, comma 1: «31 ottobre 2026» → «30 aprile 2027»
  b) art. 17, comma 3: inserito il periodo su equivalenza, validità annuale e lavoro
     → substitute sul comma intero (il motore ne fa il diff parola per parola)
"""
import importlib.util, os, glob, json, re, io, contextlib
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('b', os.path.join(HERE, 'build_dl100.py'))
b = importlib.util.module_from_spec(spec)
with contextlib.redirect_stdout(io.StringIO()):
    spec.loader.exec_module(b)

def load(d):
    out = {}
    for f in glob.glob(os.path.join(HERE, '..', d, 'a_*.html')):
        a = b.parse_decree_article(open(f, encoding='utf-8').read())
        if a:
            out[a['label']] = a
    return out

def pulisci(t):
    return re.sub(r'\(\((.*?)\)\)', r'\1', t, flags=re.S)

O, N = load('nm_fresh_20260929/dl100'), load('nm_fresh_20261006/dl100')
com = lambda a, n: next(c for c in a['commi'] if c['num'] == n)
SRC = 'art. 4, comma 1, lettera %s, d.l. 168/2026'
ams = [
    {'id': '168-a', 'letter': '168 art. 4 a)', 'src': SRC % 'a)', 'op': 'substitute',
     'target': {'art': '17', 'comma': '1'},
     'pairs': [[com(O['17'], '1')['text'], pulisci(com(N['17'], '1')['text'])]]},
    {'id': '168-b', 'letter': '168 art. 4 b)', 'src': SRC % 'b)', 'op': 'substitute',
     'target': {'art': '17', 'comma': '3'},
     'pairs': [[com(O['17'], '3')['text'], pulisci(com(N['17'], '3')['text'])]]},
]
out = {'_atto': 'd.l. 168/2026', '_nome': 'd.l. 29 settembre 2026, n. 168', '_data': '2026-09-30',
       '_source': "Art. 4, comma 1, d.l. 29 settembre 2026, n. 168 (G.U. n. 226 del 29/9/2026, in vigore dal 30/9/2026). "
                  'Generato da genera_strato_dl168.py confrontando nm_fresh_20260929/dl100 e nm_fresh_20261006/dl100.',
       'amendments': ams}
json.dump(out, open(os.path.join(HERE, 'amendments_dl168.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('scritto amendments_dl168.json:', [a['id'] for a in ams])
