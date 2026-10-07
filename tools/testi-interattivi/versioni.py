# -*- coding: utf-8 -*-
"""
Versioni degli articoli — motore condiviso dai build_dlgs*.py (e da build_dl100.py).

Si aggancia a un builder con  versioni.install(globals(), HERE)  dopo le definizioni
(sostituisce render_segments e avvolge render_article per nome, così render_comma /
build_site dei builder usano le versioni nuove senza toccarli) e, in main(), con
versioni.apply_layers(globals(), arts, rep, HERE) subito dopo apply_amendments().

1. RINVII PER VERSIONE. Un comma novellato ha due letture: il testo nuovo (normal+ins)
   e quello vecchio (normal+del). I rinvii si risolvono su ENTRAMBE e i pezzi si emettono
   segmento per segmento, così ogni link porta al bersaglio della sua versione:
     «regolamento (UE) ~~n. 604/2013~~ 2024/1351» → nel nuovo 2024/1351, nel vecchio 604/2013.
   Un pezzo di testo comune ai due testi ma linkato a bersagli diversi porta nel <a> il
   bersaglio nuovo e in data-alt il tag <a> del vecchio; linkato in una sola versione porta
   data-v="new" / data-v="old" (nell'altra il sito lo rende inerte). Tutto ciò che è dentro
   <ins> è solo del nuovo, dentro <del> solo del vecchio.

2. MODIFICHE A STRATI. amendments.json è lo strato del d.l. 100/2026. Ogni file
   amendments_<atto>.json nella cartella del builder è uno strato successivo, in ordine di
   "_data" (entrata in vigore):
     {"_atto": "d.lgs. 115/2026", "_nome": "d.lgs. 12 giugno 2026, n. 115",
      "_data": "2026-07-16", "amendments": [ ... stesse op di amendments.json, "src" esplicito ]}
   Per ogni articolo che lo strato tocca, il confronto mostrato diventa quello tra la versione
   immediatamente precedente (lo strato prima, "consolidato") e la nuova: la versione
   precedente di un articolo è sempre quella subito prima della sua ultima modifica.

3. STORIA. Ogni articolo modificato riceve sotto la rubrica
     <p class="amd-storia">Modificato dal d.l. 12 giugno 2026, n. 100 (art. 11) e dal …</p>
   e sul <div> data-ultima="<nome dell'ultimo atto>": il sito (versioni-testo.js di SOS Patto)
   ci aggancia il selettore Nuovo / Vecchio / Modifiche per articolo.
"""
import glob, html, json, os, re

ACT_NAMES = {
    'd.l. 100/2026': 'd.l. 12 giugno 2026, n. 100',
    'd.lgs. 115/2026': 'd.lgs. 12 giugno 2026, n. 115',
    'd.l. 144/2026': 'd.l. 7 agosto 2026, n. 144',
    'd.l. 168/2026': 'd.l. 29 settembre 2026, n. 168',
}
_A_ONE = re.compile(r'^(<a\s[^>]*>)([^<]*)</a>$')
_SRC_ACT = re.compile(r'((?:d\.l\.|d\.lgs\.|l\.)\s*\d+/\d{4})\s*$')
_SRC_ART = re.compile(r'^\s*art\.\s*([\w.-]+)')


def src_act(src):
    m = _SRC_ACT.search(src or '')
    return m.group(1) if m else None


# ---------------------------------------------------------------- 1. rinvii per versione
def _span_at(spans, x):
    for sp in spans:
        if sp[0] <= x < sp[1]:
            return sp
    return None


def _anchor(sp, text, extra=''):
    """<a> del span `sp` con il solo testo `text` (un pezzo del span)."""
    m = _A_ONE.match(sp[2])
    if not m:                                   # span non riducibile a un <a> semplice
        return None
    tag = m.group(1)
    if extra:
        tag = tag[:-1] + extra + '>'
    return tag + html.escape(text) + '</a>'


def make_render_segments(g):
    strip_notes, ins_open = g['strip_notes'], g['_ins_open']

    def render_segments(segs, lk, plain=False):
        items, pos_n, pos_o, new_parts, old_parts = [], 0, 0, [], []
        for k, t, s in segs:
            if not t or (plain and k == 'del'):
                continue
            it = {'k': k, 't': t, 's': s, 'n': None, 'o': None}
            if k != 'del':
                it['n'] = pos_n; pos_n += len(t); new_parts.append(t)
            if k != 'ins':
                it['o'] = pos_o; pos_o += len(t); old_parts.append(t)
            items.append(it)
        new_full, old_full = ''.join(new_parts), ''.join(old_parts)
        two = not plain and any(it['k'] != 'normal' for it in items)
        st0 = (dict(lk._occ), lk.last_act, lk.last_art)
        nsp = lk.link_spans(new_full)
        osp = []
        if two:                                  # seconda lettura, dallo stesso stato del linker
            st1 = (lk._occ, lk.last_act, lk.last_art)
            lk._occ, lk.last_act, lk.last_art = dict(st0[0]), st0[1], st0[2]
            osp = lk.link_spans(old_full)
            lk._occ, lk.last_act, lk.last_art = st1

        def cuts(base, spans, L):
            c = set()
            if base is None:
                return c
            for s_, e_, _ in spans:
                for b in (s_ - base, e_ - base):
                    if 0 < b < L:
                        c.add(b)
            return c

        res = []
        for it in items:
            k, t, L = it['k'], it['t'], len(it['t'])
            pts = sorted({0, L} | cuts(it['n'], nsp, L) | cuts(it['o'], osp, L))
            out = []
            for a, b in zip(pts, pts[1:]):
                piece = t[a:b]
                N = _span_at(nsp, it['n'] + a) if it['n'] is not None else None
                O = _span_at(osp, it['o'] + a) if it['o'] is not None else None
                if k == 'ins' or not two:
                    O = None
                if k == 'del':
                    N = None
                h = None
                # pezzo non finale di un rinvio spezzato: la freccia ↗ del CSS solo sull'ultimo
                fin = ''
                if N and it['n'] is not None and it['n'] + b != N[1]:
                    fin += ' data-fn="0"'
                if O and it['o'] is not None and it['o'] + b != O[1]:
                    fin += ' data-fo="0"'
                if N and O:
                    tn, to = _A_ONE.match(N[2]), _A_ONE.match(O[2])
                    if tn and to and tn.group(1) == to.group(1):
                        h = _anchor(N, piece, fin)
                    elif tn and to:
                        h = _anchor(N, piece, ' data-alt="%s"' % html.escape(to.group(1), quote=True) + fin)
                elif N:
                    h = _anchor(N, piece, (' data-v="new"' if k == 'normal' and two else '') + fin)
                elif O:
                    h = _anchor(O, piece, (' data-v="old"' if k == 'normal' else '') + fin)
                if h is not None and not piece.strip():
                    h = html.escape(piece)       # un pezzo di solo spazio non fa un link a sé
                if h is None and (N or O) and piece.strip():
                    sp = N or O                  # fallback: il span intero, se il pezzo è tutto il span
                    base = it['n'] if N else it['o']
                    if sp[0] == base + a and sp[1] == base + b:
                        h = sp[2]
                    else:
                        print('  ATTENZIONE: rinvio non divisibile per versione:', repr(piece))
                out.append(h if h is not None else html.escape(piece))
            body = ''.join(out)
            if k == 'ins':
                res.append(ins_open(it['s']) + body + '</ins>')
            elif k == 'del':
                s = it['s']
                tt = html.escape('Soppresso/sostituito da ' + s) if s else ''
                res.append('<del class="amd-del" data-amd="%s" title="%s">%s</del>'
                           % (html.escape(s or ''), tt, body))
            else:
                res.append(body)
        return strip_notes(''.join(res))

    return render_segments


# ---------------------------------------------------------------- 2. strati
def _consolidate(g, art):
    """La versione nuova dell'articolo diventa il testo di partenza (niente più ins/del)."""
    seg_text = g['seg_text']
    art['commi'] = [c for c in art['commi'] if not c.get('abrogato')]
    for c in art['commi']:
        c['text'] = seg_text(c)
        c['segments'] = [('normal', c['text'], None)]
        c['numkind'] = 'keep'
    rub = ''.join(t for k, t, _ in art.get('rubrica_seg', [('normal', art.get('rubrica', ''), None)]) if k != 'del')
    art['rubrica'] = rub
    art['rubrica_seg'] = [('normal', rub, None)]
    art['numkind'] = 'keep'
    art['inserted'] = False


def _srcs(art):
    out = []
    for seg in art.get('rubrica_seg') or []:
        out.append(seg[2])
    for c in art.get('commi', []):
        for seg in c.get('segments') or []:
            out.append(seg[2])
    return [s for s in out if s]


def _note_layer(art, atto, srcs, inserted):
    arts_n = []
    for s in srcs:
        m = _SRC_ART.match(s)
        if m and m.group(1) not in arts_n:
            arts_n.append(m.group(1))
    st = art.setdefault('storia', [])
    st.append({'atto': atto, 'nome': ACT_NAMES.get(atto, atto), 'art': arts_n, 'inserito': inserted})


def _touched(amendments):
    out = set()
    for am in amendments:
        t = am.get('target', {})
        if am.get('op') == 'insert_article_after':
            out.add(am['art_num'])
        elif t.get('art'):
            out.add(t['art'])
    return out


PRIMO_ATTO = 'd.l. 100/2026'      # il builder dl100 lo cambia (lì il primo strato è il d.l. 144)
ACT_DATES = {'d.l. 100/2026': '2026-06-13', 'd.lgs. 115/2026': '2026-07-16', 'd.l. 144/2026': '2026-08-08', 'd.l. 168/2026': '2026-09-30'}


def layer_files(here):
    layers = []
    for f in glob.glob(os.path.join(here, 'amendments_*.json')):
        d = json.load(open(f, encoding='utf-8'))
        ACT_NAMES.setdefault(d['_atto'], d.get('_nome', d['_atto']))
        if d.get('_data'):
            ACT_DATES.setdefault(d['_atto'], d['_data'])
        layers.append((d['_atto'], d['amendments']))
    return layers


def _storia_da_segmenti(arts):
    for a in arts:
        srcs = _srcs(a)
        acts = []
        for s in srcs:
            x = src_act(s)
            if x and x not in acts:
                acts.append(x)
        for x in acts:
            _note_layer(a, x, [s for s in srcs if src_act(s) == x], bool(a.get('inserted')))


def make_apply_amendments(g, orig, here):
    """apply_amendments a strati. Il primo strato sono le modifiche senza "src" (quelle del
    d.l. 100, che prendono la fonte di default del builder) o con la fonte dello stesso atto;
    ogni altro atto nominato in "src" (es. «…, d.lgs. 115/2026»), e ogni amendments_<atto>.json,
    è uno strato successivo, in ordine di entrata in vigore (ACT_DATES / "_data")."""
    def apply_amendments(arts, amendments, rep):
        acts = [src_act(am.get('src')) for am in amendments]
        primo_atto = PRIMO_ATTO
        primo = [am for x, am in zip(acts, amendments) if x in (None, primo_atto)]
        strati = {}
        for x, am in zip(acts, amendments):
            if x not in (None, primo_atto):
                strati.setdefault(x, []).append(am)
        for x, ams in layer_files(here):
            strati.setdefault(x, []).extend(ams)
        orig(arts, primo, rep)
        _storia_da_segmenti(arts)
        for atto in sorted(strati, key=lambda x: ACT_DATES.get(x, '9999')):
            ams = strati[atto]
            touched = _touched(ams)
            for a in arts:
                if a['label'] in touched:
                    _consolidate(g, a)
            init = g['init_segments']
            g['init_segments'] = lambda a: None       # non azzerare lo strato precedente
            try:
                n0 = len(rep.rows)
                orig(arts, ams, rep)
            finally:
                g['init_segments'] = init
            for a in arts:
                if a['label'] in touched:
                    _note_layer(a, atto, [s for s in _srcs(a) if src_act(s) == atto]
                                or [am.get('src', '') for am in ams], bool(a.get('inserted')))
            print('Strato %s: %d modifiche su %d articoli (%s)' % (
                atto, len(rep.rows) - n0, len(touched), ', '.join(sorted(touched))))
    return apply_amendments


def apply_layers(g, arts, rep, here):
    """Compatibilità: gli strati li applica già apply_amendments (v. install)."""
    return None


# ---------------------------------------------------------------- 3. storia sotto la rubrica
def storia_html(a):
    st = a.get('storia') or []
    if not st:
        return ''
    parts = []
    for i, x in enumerate(st):
        verb = ('Inserito' if x['inserito'] else 'Modificato') if i == 0 else \
               ('inserito' if x['inserito'] else 'modificato')
        rif = ' (%s)' % ', '.join('art. ' + n for n in x['art']) if x['art'] else ''
        parts.append('%s dal %s%s' % (verb, html.escape(x['nome']), rif))
    txt = parts[0] if len(parts) == 1 else '; '.join(parts[:-1]) + '; poi ' + parts[-1]
    return '<p class="amd-storia">%s</p>' % txt


_COMMA_DIV = re.compile(r'<div class="comma" id="([^"]+)"><span class="cnum">(<del class="amd-del">)?')


def _sostituiti(h):
    """Un comma soppresso che ha un successore con lo stesso numero (articolo o commi
    sostituiti) non è «soppresso»: è la versione vecchia di quel comma. Gli si dà id
    «…-vecchio» (l'id resta al comma in vigore, bersaglio dei rinvii) e la classe
    amd-sostituito, che nel testo nuovo lo nasconde del tutto."""
    ids = [(m.group(1), bool(m.group(2))) for m in _COMMA_DIV.finditer(h)]
    vivi = {i for i, d in ids if not d}
    def fix(m):
        if m.group(2) and m.group(1) in vivi:
            return m.group(0).replace('class="comma" id="%s"' % m.group(1),
                                      'class="comma amd-sostituito" id="%s-vecchio"' % m.group(1), 1)
        return m.group(0)
    return _COMMA_DIV.sub(fix, h)


def make_render_article(g, orig):
    def render_article(a, lk):
        h = _sostituiti(orig(a, lk))
        st = a.get('storia') or []
        if not st:
            return h
        h = h.replace('<div class="eli-subdivision art', '<div data-ultima="%s" class="eli-subdivision art'
                      % html.escape(st[-1]['nome'], quote=True), 1)
        i = h.find('</div>', h.find('<div class="eli-title">'))
        return h[:i + 6] + '\n' + storia_html(a) + h[i + 6:] if i >= 0 else h
    return render_article


def install(g, here):
    g['render_segments'] = make_render_segments(g)
    g['render_article'] = make_render_article(g, g['render_article'])
    g['apply_amendments'] = make_apply_amendments(g, g['apply_amendments'], here)
