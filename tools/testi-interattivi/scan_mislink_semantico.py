#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scan semantico dei mislink «self» nei 4 siti interattivi.

Pattern (lo stesso che a giugno trovo' 15 bug nel 286 e 1 nel 142): un
<a class="xref" data-act="<SELF>">articolo N</a> seguito — dopo soli
qualificatori (comma/lettera/paragrafo/punto/numero + numeri/lettere) — da un
connettore del/della/… che nomina un ALTRO atto, senza un altro «articol» in
mezzo: il rinvio appartiene all'atto nominato, non all'atto ospite.

Implementazione a camminata di token (niente regex backtracking).
Falsi positivi esclusi: «del presente decreto», l'atto ospite nominato per
esteso (numero/anno propri da sites.json), anafora compatibile col tipo self.

Uso: python3 scan_mislink_semantico.py [--outdir nm_fresh_20260710]
Output: <outdir>/reports/mislinks.jsonl + stampa. Atteso: 0 hit.
"""
import argparse, html, json, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
SITES = json.load(open(os.path.join(ROOT, 'sites.json'), encoding='utf-8'))

QUAL_WORDS = {'comma', 'commi', 'lettera', 'lettere', 'lett.', 'paragrafo',
              'paragrafi', 'punto', 'punti', 'numero', 'numeri',
              'da', 'a', 'e', 'ed', 'o', 'od', 'nonche\''}
CONN_WORDS = {'del', 'dello', 'della', 'dei', 'degli', 'delle'}
RE_NUMTOK = re.compile(r"^\(?\d{1,3}(?:-\w+)?(?:\.\d+)?\)?[,;.]?$|^[a-z](?:-\w+)?\)[,;.]?$", re.I)
RE_ACT = re.compile(r'(?i)^(regolament|direttiv|decision|legge|decreto|regio|testo)')
RE_ANAPH = re.compile(r'(?i)^(medesim|stess|citat|predett|suddett)')

def comma_blocks(html_s):
    for m in re.finditer(r'<div class="comma[^"]*" id="(art_[^"]+)">(.*?)</div>\s*(?=<div class="comma|'
                         r'<div class="eli-subdivision|<h2 class="capo|<p class="disclaimer|</main)',
                         html_s, re.S):
        yield m.group(1), m.group(2)

def plain(s):
    # il testo BARRATO (<del>) non fa parte del testo finale: tenerlo nel tail
    # produce falsi positivi (es. «articolo 5-sexies» + coda del testo soppresso)
    s = re.sub(r'(?s)<del\b[^>]*>.*?</del>', ' ', s)
    return html.unescape(re.sub(r'<[^>]+>', ' ', s))

def mislink_tail(tail, self_num, self_year):
    """Ritorna la descrizione dell'atto nominato se il rinvio appartiene a un
    altro atto; None se il seguito non e' un tail d'atto o e' il self."""
    toks = tail.split()[:18]
    i = 0
    while i < len(toks):
        t = toks[i]
        if t.lower().strip('.,;') in QUAL_WORDS or RE_NUMTOK.match(t) or t in (',', ';'):
            i += 1
            continue
        break
    if i >= len(toks):
        return None
    conn = toks[i].lower().rstrip(',')
    if conn not in CONN_WORDS and not conn.startswith("dell'"):
        return None
    if conn.startswith("dell'") and len(conn) > 5:
        # «dell'articolo» / «dell'atto»: c'e' un altro sostantivo attaccato
        rest = conn[5:]
        if rest.startswith('articol'):
            return None
        toks.insert(i + 1, rest)
    j = i + 1
    anaph = False
    if j < len(toks) and RE_ANAPH.match(toks[j]):
        anaph = True
        j += 1
    if j >= len(toks):
        return None
    nxt = toks[j].lower()
    if nxt.startswith('present') or nxt.startswith('articol'):
        return None
    if not RE_ACT.match(toks[j]):
        return None
    named = ' '.join(toks[j:j + 12])
    # atto ospite nominato per esteso
    if re.search(r'\bn\.\s*%s\b' % re.escape(self_num), named) or self_year in named:
        return None
    # anafora del tipo compatibile col self («del medesimo decreto») senza numero
    if anaph and nxt.startswith('decreto'):
        return None
    return named

def scan_site(key, cfg):
    idx = os.path.join(ROOT, cfg['src'], 'index.html')
    html_s = open(idx, encoding='utf-8').read()
    self_num, self_year = cfg['it'][1], cfg['date'][:4]
    hits = []
    n_checked = 0
    for scope, inner in comma_blocks(html_s):
        for m in re.finditer(r'<a class="xref[^"]*" data-act="%s"[^>]*>(.*?)</a>' % re.escape(key),
                             inner, re.S):
            txt = plain(m.group(1)).strip()
            if not re.match(r'(?i)articol', txt):
                continue
            n_checked += 1
            tail = re.sub(r'\s+', ' ', plain(inner[m.end():m.end() + 420]))
            named = mislink_tail(tail, self_num, self_year)
            if named:
                hits.append(dict(site=key, scope=scope, text=txt,
                                 named=named[:100], tail=tail[:140].strip()))
    return n_checked, hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--outdir', default='nm_fresh_20260710')
    args = ap.parse_args()
    all_hits = []
    for key, cfg in SITES['acts'].items():
        n, hits = scan_site(key, cfg)
        print('%s: %d link self esaminati, %d mislink sospetti' % (key, n, len(hits)))
        all_hits += hits
    rdir = os.path.join(ROOT, args.outdir, 'reports')
    os.makedirs(rdir, exist_ok=True)
    with open(os.path.join(rdir, 'mislinks.jsonl'), 'w', encoding='utf-8') as f:
        for h in all_hits:
            f.write(json.dumps(h, ensure_ascii=False) + '\n')
    print('TOTALE mislink sospetti: %d' % len(all_hits))
    for h in all_hits:
        print(' - [%s] %s «%s» → nominato: %s' % (h['site'], h['scope'], h['text'], h['named'][:80]))

if __name__ == '__main__':
    main()
