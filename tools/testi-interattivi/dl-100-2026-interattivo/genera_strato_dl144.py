#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera amendments_dl144.json: lo strato del d.l. 7 agosto 2026, n. 144 (art. 7, comma 1)
sul d.l. 100/2026, confrontando lo snapshot Normattiva del 10/7/2026 (testo originario) con
quello del 29/9/2026 (vigente). Le (( )) di Normattiva, che marcano il testo modificato, si
tolgono: nella pagina lo segna l'evidenziazione. Rieseguire solo se cambia uno dei due snapshot.

  a) art. 1, comma 3, lett. b): inseriti «ecclesiastico,» e «privato e processuale»
     → substitute sul comma intero (il motore ne fa il diff parola per parola)
  b) art. 2, comma 5 soppresso → repeal_comma
  c) art. 16 sostituito → replace_article
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

O, N = load('nm_fresh_20260710/dl100'), load('nm_fresh_20260929/dl100')
com = lambda a, n: next(c for c in a['commi'] if c['num'] == n)
SRC = 'art. 7, comma 1, lettera %s, d.l. 144/2026'
ams = [
    {'id': '144-a', 'letter': '144 art. 7 a)', 'src': SRC % 'a)', 'op': 'substitute',
     'target': {'art': '1', 'comma': '3'},
     'pairs': [[com(O['1'], '3')['text'], pulisci(com(N['1'], '3')['text'])]]},
    {'id': '144-b', 'letter': '144 art. 7 b)', 'src': SRC % 'b)', 'op': 'repeal_comma',
     'target': {'art': '2'}, 'commi': ['5']},
    {'id': '144-c', 'letter': '144 art. 7 c)', 'src': SRC % 'c)', 'op': 'replace_article',
     'target': {'art': '16'}, 'rubrica': pulisci(N['16']['rubrica']),
     'commi': [{'num': c['num'], 'text': pulisci(c['text'])} for c in N['16']['commi']]},
]
out = {'_atto': 'd.l. 144/2026', '_nome': 'd.l. 7 agosto 2026, n. 144', '_data': '2026-08-08',
       '_source': "Art. 7, comma 1, d.l. 7 agosto 2026, n. 144 (G.U. n. 182 del 7/8/2026, in vigore dall'8/8/2026). "
                  'Generato da genera_strato_dl144.py confrontando nm_fresh_20260710/dl100 e nm_fresh_20260929/dl100.',
       'amendments': ams}
json.dump(out, open(os.path.join(HERE, 'amendments_dl144.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('scritto amendments_dl144.json:', [a['id'] for a in ams], '| art. 16 commi nuovi:', len(ams[2]['commi']))
