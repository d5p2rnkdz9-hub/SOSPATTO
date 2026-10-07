#!/usr/bin/env python3
"""Ricerca nella KB SOS Patto.

  kb.py cerca REGEX [-s SEZ] [-n MAX] [-C]   cerca (case/accenti/apostrofi-insensitive)
  kb.py art ATTO N [PAR]                     stampa un articolo (es. art 1348 13 8; art dlgs25 35-bis)
  kb.py cons ATTO N                          stampa un considerando
  kb.py giur ATTO N                          schede che richiamano la norma + richiami nei testi integrali
  kb.py schede [-s norm|giur|circ|dottr] [-t TEMA] elenca le schede (data, file, titolo)

SEZ: ue | it | norme (=ue+it) | norm (schede di atti italiani, es. D.M.) | giur | circ | dottr | ext | tutto (default: tutto)
Le righe normative iniziano col tag di citazione, es. [1348 art.13 par.8 lett.a].
Alla fine di `cerca` una tabella di COPERTURA elenca anche gli atti con 0 risultati.
"""
import os
import re
import sys
import unicodedata
from pathlib import Path

KB = Path(os.environ.get('SOSPATTO_KB', Path(__file__).resolve().parent.parent.parent / 'kb'))  # <repo>/kb, generata da build_kb.py
SEZ = {
    'ue': ['1-norme-ue'], 'it': ['2-norme-italiane'], 'norme': ['1-norme-ue', '2-norme-italiane'],
    'giur': ['3-giurisprudenza'], 'circ': ['4-circolari-prassi'], 'dottr': ['5-dottrina'],
    'norm': ['2-normativa-schede'],
    'ext': ['6-atti-collegati'],
    'tutto': ['1-norme-ue', '2-norme-italiane', '2-normativa-schede', '3-giurisprudenza', '4-circolari-prassi', '5-dottrina', '6-atti-collegati'],
}
CORE = ['1346', '1347', '1348', '1349', '1350', '1351', '1352', '1356', '1358', '1359',
        'dl-100-2026', 'dlgs-25-2008', 'dlgs-142-2015', 'dlgs-286-1998', 'dlgs-251-2007']
PREF = {'dl100': 'dl-100-2026', 'dlgs25': 'dlgs-25-2008', 'dlgs142': 'dlgs-142-2015',
        'dlgs286': 'dlgs-286-1998', 'dlgs251': 'dlgs-251-2007'}


def fold(s, lower=True):
    s = s.replace('’', "'").replace('‘', "'").replace('\xa0', ' ')
    s = unicodedata.normalize('NFD', s)
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    s = re.sub(r"(?<=[aeiou])'(?=\W|$)", '', s)  # Normattiva: e' → e, puo' → puo
    return s.lower() if lower else s


def files(sez):
    for d in SEZ[sez]:
        yield from sorted((KB / d).glob('*.md'))


def act_file(atto):
    atto = PREF.get(atto, atto)
    for d in ('1-norme-ue', '2-norme-italiane', '6-atti-collegati'):
        for f in (KB / d).glob('*.md'):
            if f.stem == atto or f.stem.startswith(atto + '-'):
                return f
    sys.exit(f'Atto non trovato: {atto}')


def cerca(pat, sez='tutto', maxper=40, ctx=False):
    rx = re.compile(fold(pat, lower=False), re.I)
    cov = {}
    tot = 0
    for f in files(sez):
        lines = f.read_text(encoding='utf-8').split('\n')
        hits, sect, page = [], '', ''
        for i, ln in enumerate(lines):
            if ln.startswith('## '):
                sect = ln[3:]
            elif ln.startswith('[p. '):
                page = ln.split(']')[0] + ']'
            if rx.search(fold(ln)):
                hits.append((i, ln, sect, page))
        key = f.stem
        cov[key] = len(hits)
        if not hits:
            continue
        tot += len(hits)
        title = lines[0].lstrip('# ')[:150]
        print(f'\n=== {f.relative_to(KB)} — {title}  ({len(hits)} righe)')
        for i, ln, sect, page in hits[:maxper]:
            loc = ''
            if not ln.startswith('['):
                loc = f'{{{sect[:70]}}} ' + (page + ' ' if page and 'Testo integrale' in sect else '')
            s = ln
            if len(s) > 400:
                m = rx.search(fold(s))
                a = max(0, m.start() - 180) if m else 0
                s = ('…' if a else '') + s[a:a + 400] + '…'
            print(f'{i + 1:>5}: {loc}{s}')
            if ctx and not ln.startswith('['):
                for j in (i - 1, i + 1):
                    if 0 <= j < len(lines) and lines[j].strip():
                        print(f'{j + 1:>5}  | {lines[j][:300]}')
        if len(hits) > maxper:
            print(f'       … altre {len(hits) - maxper} righe (usa -n)')
    print(f'\n--- COPERTURA «{pat}» ({tot} righe) ---')
    if sez in ('tutto', 'norme', 'ue', 'it'):
        for c in CORE:
            k = next((k for k in cov if k == c or k.startswith(c + '-')), None)
            if k is not None:
                print(f'  {c:<14} {cov[k]:>4}' + ('   ← nessun risultato: cercare per rinvio/sinonimi prima di escluderlo' if cov[k] == 0 else ''))
    for lab, d in (('giurisprudenza', '3-giurisprudenza'), ('circolari', '4-circolari-prassi'),
                   ('dottrina', '5-dottrina'), ('atti collegati', '6-atti-collegati')):
        if d in SEZ[sez]:
            n = sum(1 for f in (KB / d).glob('*.md') if cov.get(f.stem))
            print(f'  {lab:<14} {n:>4} file')


def art(atto, n, par=None):
    f = act_file(atto)
    lines = f.read_text(encoding='utf-8').split('\n')
    hd = re.compile(rf'^## (Articolo|Art\.) {re.escape(n)}( |$)')
    out, on = [], False
    for ln in lines:
        if ln.startswith('## ') or ln.startswith('### '):
            if on and not hd.match(ln):
                break
            on = bool(hd.match(ln))
        if on:
            if par and ln.startswith('[') and not re.search(rf' (par|c)\.{re.escape(par)}[ \]]', ln.split(']')[0] + ']'):
                continue
            out.append(ln)
    print(f'({f.relative_to(KB)})')
    print('\n'.join(out) if out else f'Articolo {n} non trovato in {f.name}')


def cons(atto, n):
    f = act_file(atto)
    for ln in f.read_text(encoding='utf-8').split('\n'):
        if ln.startswith(f'[{atto} cons.{n}]'):
            print(f'({f.relative_to(KB)})\n{ln}')
            return
    print('Considerando non trovato')


def giur(atto, n):
    idx = (KB / 'INDICE-norme-citate.md').read_text(encoding='utf-8').split('\n')
    sect = None
    print(f'# Schede che citano {atto} art. {n} (campo norme):')
    for ln in idx:
        if ln.startswith('## '):
            sect = ln[3:]
        elif sect == atto and ln.startswith(f'- art. {n}:'):
            for x in ln.split(': ', 1)[1].split('; '):
                print('  -', x)
    names = {'1346': r'2024/1346|direttiva accoglienza', '1347': r'2024/1347|regolamento qualifiche',
             '1348': r'2024/1348|regolamento procedure|\bapr\b', '1349': r'2024/1349', '1350': r'2024/1350',
             '1351': r'2024/1351|ramm', '1356': r'2024/1356|screening', '1358': r'2024/1358|eurodac',
             '1359': r'2024/1359', 'dlgs25': r'25/2008|d\.? ?lgs\.? n?\.? ?25', 'dlgs142': r'142/2015',
             'dlgs286': r'286/1998|t\.u\.', 'dlgs251': r'251/2007', 'dl100': r'100/2026'}
    act_rx = re.compile(names.get(atto, re.escape(atto)))
    art_rx = re.compile(rf'\bart(icol[oi]|t)?\.?\s*{re.escape(fold(n))}(?![\d\-])')
    print(f'\n# Richiami nel testo (schede + testi integrali), stessa riga con l\'atto:')
    for d in ('3-giurisprudenza', '4-circolari-prassi', '5-dottrina'):
        for f in sorted((KB / d).glob('*.md')):
            page = ''
            for i, ln in enumerate(f.read_text(encoding='utf-8').split('\n')):
                if ln.startswith('[p. '):
                    page = ln.split(']')[0] + ']'
                fl = fold(ln)
                if art_rx.search(fl) and act_rx.search(fl):
                    m = art_rx.search(fl)
                    a = max(0, m.start() - 150)
                    print(f'  {f.relative_to(KB)}:{i + 1} {page} …{ln[a:a + 300]}…')


def schede(sez='tutto', tema=None):
    for d in SEZ[sez] if sez != 'tutto' else ['2-normativa-schede', '3-giurisprudenza', '4-circolari-prassi', '5-dottrina']:
        rows = []
        for f in (KB / d).glob('*.md'):
            txt = f.read_text(encoding='utf-8')
            m = re.search(r'^- Data: (\S+)', txt, re.M)
            t = re.search(r'^- Temi: (.*)$', txt, re.M)
            if tema and not (t and fold(tema) in fold(t.group(1))):
                continue
            rows.append((m.group(1) if m else '', f.relative_to(KB), txt.split('\n', 1)[0][2:160]))
        for r in sorted(rows):
            print(f'{r[0]}  {r[1]}  {r[2]}')


def main(a):
    if not a or a[0] in ('-h', '--help'):
        print(__doc__)
        return
    cmd, rest = a[0], a[1:]
    opts = {'-s': 'tutto', '-n': '40', '-t': None}
    flags, pos, i = set(), [], 0
    while i < len(rest):
        if rest[i] in opts:
            opts[rest[i]] = rest[i + 1]
            i += 2
        elif rest[i] == '-C':
            flags.add('C')
            i += 1
        else:
            pos.append(rest[i])
            i += 1
    if cmd == 'cerca':
        cerca(' '.join(pos), opts['-s'], int(opts['-n']), 'C' in flags)
    elif cmd == 'art':
        art(*pos[:3])
    elif cmd == 'cons':
        cons(*pos[:2])
    elif cmd == 'giur':
        giur(*pos[:2])
    elif cmd == 'schede':
        schede(opts['-s'], opts['-t'])
    else:
        print(__doc__)


if __name__ == '__main__':
    main(sys.argv[1:])
