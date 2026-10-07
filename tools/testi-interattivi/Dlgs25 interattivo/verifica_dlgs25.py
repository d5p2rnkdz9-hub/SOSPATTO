#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifica indipendente dei collegamenti del sito interattivo d.lgs. 25/2008.

Principio (come per il Patto, build_patto_interattivo / verifica_patto): NON riusa
la logica del builder. Rilegge le PAGINE GENERATE (index.html + assets/data.js) e:

  A. coerenza deterministica  — ogni <a> punta a un bersaglio esistente; nessun
     hover vuoto (simula app.js buildContent); href ben formati.
  B. classificazione "sospetti" — i casi che solo un giurista può decidere:
       * anaphora      : link risolto tramite «del medesimo/stesso/citato… atto»
       * cross-no-mention: link a un atto-fonte il cui nome non compare nel comma
       * unresolved    : «articolo N» NON collegato benché N esista in d.lgs.25 o
                         in un atto-fonte (possibile rinvio da collegare a mano)
  C. report           — REPORT_VERIFICA.md + verifica/suspects.jsonl + problems.json
                        (problems.json DEVE restare vuoto).

Uso:  python3 verifica_dlgs25.py
"""
import re, json, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
ORD = "bis|ter|quater|quinquies|sexies|septies|octies|novies|nonies|decies|undecies|duodecies|terdecies"

ANAPH = re.compile(r'(?:medesim[oa]|stess[oa]|citat[oa]|predett[oa]|suddett[oa]|dett[oa]|tal[ei])\s+'
                   r'(?:regolament|direttiv|decision|decreto|legge)', re.I)
ACT_NAME = re.compile(r'(?:regolament|direttiv|decision)\w*\s*\(?(?:UE|CE|CEE)?\)?\s*(?:n\.\s*)?\d{1,4}/\d{1,4}'
                      r'|decreto\s+legislativo|decreto-legge|\blegge\s+\d|regio\s+decreto'
                      r'|decreto\s+del\s+Presidente|d\.?\s*P\.?\s*R', re.I)


def load():
    html_s = open(os.path.join(HERE, 'index.html'), encoding='utf-8').read()
    js = open(os.path.join(HERE, 'assets', 'data.js'), encoding='utf-8').read()
    D = json.loads(js[js.index('window.PACTO=') + len('window.PACTO='):js.rindex(';')])['acts']
    return html_s, D


def comma_blocks(html_s):
    """Yield (scope_id, inner_html, plain_text) for every comma/rubrica/preambolo div."""
    for m in re.finditer(r'<div class="comma[^"]*" id="(art_[^"]+)">(.*?)</div>\s*(?=<div class="comma|'
                         r'<div class="eli-subdivision|<h2 class="capo|<p class="disclaimer|</main)',
                         html_s, re.S):
        inner = m.group(2)
        yield m.group(1), inner, html.unescape(re.sub(r'<[^>]+>', '', inner))


def link_iter(inner):
    for m in re.finditer(r'<a class="([^"]+)"((?:\s+data-[a-z]+="[^"]*")*)[^>]*?(?:href="([^"]*)")?[^>]*>(.*?)</a>',
                         inner, re.S):
        data = dict(re.findall(r'data-([a-z]+)="([^"]*)"', m.group(2)))
        yield dict(cls=m.group(1), data=data, href=m.group(3) or '',
                   text=html.unescape(re.sub(r'<[^>]+>', '', m.group(4))).strip(),
                   start=m.start(), end=m.end())


def main():
    html_s, D = load()
    os.makedirs(os.path.join(HERE, 'verifica'), exist_ok=True)
    page_ids = set(re.findall(r'id="art_([^"]+)"', html_s))
    self_arts = set(D['dlgs-2008-25']['articles'])
    core_arts = {k: set(v['articles']) for k, v in D.items() if k != 'dlgs-2008-25'}

    problems, suspects = [], []
    n_links = n_xref = n_ext = 0

    for scope, inner, plain in comma_blocks(html_s):
        names_in_comma = bool(ACT_NAME.search(plain))
        for L in link_iter(inner):
            n_links += 1
            cls, d, href, txt = L['cls'], L['data'], L['href'], L['text']
            is_ext = 'ext' in cls.split()
            act, art, par = d.get('act'), d.get('art'), d.get('par')

            # ---- A. coherence ----
            if 'xref' in cls and not is_ext:
                n_xref += 1
                if not act or act not in D:
                    problems.append(['act-assente-in-data', scope, txt, act]); continue
                if art:
                    if art not in D[act]['articles']:
                        problems.append(['articolo-assente-in-data', scope, txt, f'{act}/{art}'])
                    if act == 'dlgs-2008-25' and art not in page_ids:
                        problems.append(['ancora-interna-assente', scope, txt, art])
                    # tooltip non vuoto?
                    elif not D[act]['articles'][art].get('frags'):
                        problems.append(['tooltip-vuoto', scope, txt, f'{act}/{art}'])
                    # data-par presente ma assente fra i frammenti → solo avviso (ripiega su articolo)
                    if par and art in D[act]['articles']:
                        pars = {str(f[0]) for f in D[act]['articles'][art]['frags']}
                        if str(re.match(r'\d+', par).group()) not in pars:
                            suspects.append(dict(kind='par-non-evidenziabile', scope=scope, text=txt,
                                                 target=f'{act}/{art} par {par}'))
            else:
                n_ext += 1
                if href and not href.startswith(('http://', 'https://', '#')):
                    problems.append(['href-malformato', scope, txt, href])

            # ---- B. suspects (semantica) ----
            ctx = plain[max(0, plain.find(txt) - 60):plain.find(txt) + len(txt) + 50] if txt in plain else plain[:110]
            if 'xref' in cls and act:
                # anaphora: il comma contiene «medesimo/stesso… atto» vicino al link
                if ANAPH.search(ctx):
                    suspects.append(dict(kind='anaphora', scope=scope, act=act, art=art,
                                         text=txt, context=ctx.strip()))
                # link a un atto-fonte (extlocal) ma nessun nome d'atto nel comma
                elif act != 'dlgs-2008-25' and not names_in_comma:
                    suspects.append(dict(kind='cross-senza-menzione', scope=scope, act=act, art=art,
                                         text=txt, context=ctx.strip()))

        # ---- B. unresolved: «articolo N» fuori da un <a> ma N esiste da qualche parte ----
        for m in re.finditer(r'(?<![\w])articol[oi]\s+(\d{1,3}(?:-(?:%s))?)' % ORD, inner, re.I):
            # è dentro un <a>?
            before = inner[:m.start()]
            if before.count('<a ') > before.count('</a>'):
                continue
            num = m.group(1)
            tail = html.unescape(re.sub(r'<[^>]+>', ' ', inner[m.end():m.end() + 80]))
            in_self = num in self_arts
            in_core = any(num in s for s in core_arts.values())
            # se è seguito subito da un nome d'atto, è quasi certo un rinvio non collegato
            if (in_self or in_core) and re.match(r'^\s*(?:,?\s*(?:comma|commi|paragraf|letter)[^,.;]*)*,?\s*'
                                                 r'(?:del|della|dello|dei|degli|delle|di\s+cui)\s+'
                                                 r'(?:regolament|direttiv|decision|decreto|legge|present)', tail, re.I):
                suspects.append(dict(kind='unresolved-con-coda', scope=scope, art=num,
                                     text='articolo ' + num, context=(m.group(0) + tail)[:110].strip()))

    # ---- C. report ----
    with open(os.path.join(HERE, 'verifica', 'suspects.jsonl'), 'w', encoding='utf-8') as f:
        for s in suspects:
            f.write(json.dumps(s, ensure_ascii=False) + '\n')
    json.dump(problems, open(os.path.join(HERE, 'verifica', 'problems.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    by_kind = {}
    for s in suspects:
        by_kind.setdefault(s['kind'], []).append(s)
    lines = ['# Report verifica collegamenti — d.lgs. 25/2008 interattivo', '',
             f'Link totali: **{n_links}** ({n_xref} hover interni/atti-fonte, {n_ext} esterni semplici).', '',
             f'## A. Coerenza deterministica — **{len(problems)} problemi**'
             + ('  ✅' if not problems else '  ⚠️ DA CORREGGERE'), '']
    for p in problems[:80]:
        lines.append(f'- `{p[0]}` in {p[1]}: «{p[2]}» → {p[3]}')
    lines += ['', f'## B. Sospetti da revisione giurista — **{len(suspects)}**', '']
    for kind, items in sorted(by_kind.items()):
        lines.append(f'### {kind} ({len(items)})')
        for s in items[:60]:
            tgt = s.get('act', '') + ('/' + s['art'] if s.get('art') else '')
            lines.append(f'- {s["scope"]} · «{s.get("text","")}» {("→ " + tgt) if tgt else ""}  \n  _ctx_: {s.get("context","")}')
        lines.append('')
    open(os.path.join(HERE, 'REPORT_VERIFICA.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

    print(f"Link: {n_links} | problemi coerenza: {len(problems)} | sospetti: {len(suspects)}")
    print("Per tipo:", {k: len(v) for k, v in by_kind.items()})
    print("Scritti: REPORT_VERIFICA.md, verifica/suspects.jsonl, verifica/problems.json")


if __name__ == '__main__':
    main()
