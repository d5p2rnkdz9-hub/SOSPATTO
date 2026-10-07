#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the interactive version of d.l. 12 giugno 2026, n. 100 (misure urgenti in materia di
giustizia e per l'attuazione del Patto UE sulla migrazione e l'asilo), converted WITHOUT
amendments by l. 7 agosto 2026, n. 145; artt. 1, 2 and 16 were then amended by art. 7 d.l. 7 agosto
2026, n. 144 — applied as a later layer (amendments_dl144.json, see genera_strato_dl144.py; likewise art. 17
by d.l. 168/2026, amendments_dl168.json / genera_strato_dl168.py — and
../versioni.py), so those articles show the previous version and the changes.

Unlike the four consolidated laws, this is the NOVELLATING act itself: Capo II (artt. 10-17)
rewrites d.lgs. 142/2015, 25/2008 and 286/1998, whose coordinated (tracked-changes) versions are
the sibling sites. So this site is a PLAIN interactive text (no tracked changes) whose every
cross-reference is navigable — into the Pact acts, into the three coordinated laws, and into
the decree itself.

SOURCE: Normattiva caricaArticolo HTML in ../nm_fresh_20260710/dl100/ (19 articles, snapshot of
10 July 2026; the conversion law changed nothing, so it is still the text in force).

ENGINE: the parser primitives, the cross-reference Linker and the tracked-changes renderer are
IMPORTED from ../251-07-interattivo/build_dlgs251.py (the plain-text sibling) rather than copied,
so fixes to the shared grammar land here automatically. Only what is specific to a decree of
novellazione lives in this file:

  * PARSER — the GU typography, not the "N." markers, decides the structure. In the Normattiva
    <pre> every paragraph that starts a new GU paragraph has a LEADING SPACE, wrapped lines do
    not. A "N." paragraph is a comma OF THE DECREE only at quote depth 0 («…» balanced) and in
    sequence; at depth > 0 it is a comma of the quoted (inserted/replaced) article and stays
    inside the decree's comma as a paragraph. The GU itself omits the opening « once (art. 10,
    lett. c: «Art. 5-ter … 5-sexies» closes at «5-quater, comma 3.»), so an introducer line
    ending in «…i seguenti:» / «…dal seguente:» followed by a paragraph without « opens a
    virtual quote.
  * AMEND TARGETS — a bare «articolo N» inside a comma that novellates another act («al decreto
    legislativo …, n. 142, sono apportate le seguenti modificazioni: a) l'articolo 4 è
    sostituito…») refers to THAT act, not to the decree. Per comma, the act named right before
    the novella verb (skipping the conversion law after «convertito … dalla legge») becomes the
    target for the comma's bare references; commi without a novella verb resolve bare refs to
    the decree itself (art. 17, comma 4: «articolo 16, comma 1»).
  * RENDER — paragraphs inside a comma become line breaks; quoted comma numbers, lettere,
    numeri («2.1)») and quoted article heads («Art. 4 (Documenti forniti al richiedente).») get
    their markers styled.

Pipeline: parse -> link -> render index.html + assets/data.js + assets/amend.css +
REPORT_MODIFICHE.md. Registered in ../sites.json as 'dl-2026-100' (slug dl-100-2026), so the
sibling builders link «decreto-legge 12 giugno 2026, n. 100» here hoverably.
"""
import re, html, json, glob, os, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..')
SRC  = os.path.join(ROOT, 'nm_fresh_20260710', 'dl100')

# ---------------------------------------------------------------- shared engine
_spec = importlib.util.spec_from_file_location('engine', os.path.join(ROOT, '251-07-interattivo', 'build_dlgs251.py'))
E = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(E)
E.SELF_KEY = 'dl-2026-100'
E.SELF_IT  = tuple(E.SITES['acts'][E.SELF_KEY]['it'])      # ('decreto.legge', '100')
E.KNOWN_DATE[('decreto.legge', '100')] = '2026-06-12'
ORD, NUM, LABEL, COMMA_LINE, base = E.ORD, E.NUM, E.LABEL, E.COMMA_LINE, E.base

SELF_LABEL = 'D.L. 12 giugno 2026, n. 100'
SELF_SHORT = 'D.L. 100/2026'
CAPI = [('Capo I',   'Disposizioni urgenti in materia di giustizia'),
        ('Capo II',  "Disposizioni urgenti per l'attuazione del Patto dell'Unione europea sulla migrazione e l'asilo"),
        ('Capo III', 'Disposizioni finali')]

# ---------------------------------------------------------------- parse
# Nei decreti legislativi Normattiva mette nella stessa pagina anche le NOTE (premesse e
# articolo), in un altro <pre> che cita a sua volta «Art. N» ed è più lungo: la scelta del
# motore («il <pre> più lungo che contiene Art. N») prenderebbe le note. Qui vince il <pre>
# con la riga d'intestazione «Art. N» da sola (quella del testo); se manca, si torna al motore.
_body_lines_engine = E.body_lines
_ART_HEAD_LINE = re.compile(r'^\s*Art\.\s*\d+(?:-\w+)?\s*$', re.M)
def body_lines(raw):
    d = re.sub(r'(?s)<!--.*?-->', ' ', raw)
    pres = [html.unescape(re.sub(r'(?s)<[^>]+>', '', p)) for p in re.findall(r'(?s)<pre[^>]*>(.*?)</pre>', d)]
    testo = [p for p in pres if _ART_HEAD_LINE.search(p) and not re.match(r'\s*NOTE\b', p)]
    if len(testo) == 1 and not testo[0].lstrip().startswith('Art.'):
        return _body_lines_engine('<pre>' + html.escape(testo[0]) + '</pre>')   # premesse comprese
    return _body_lines_engine(raw)
E.body_lines = body_lines
# a GU paragraph opener: leading space + marker (comma «N.», lettera «a)», numero «1)»/«2.1)»,
# quoted article «Art. N (…)», quoted comma «2-bis.», or the closing formula/signatures)
INTRO_OPEN = re.compile(r"(?:seguent[ei]|modificat[ao]|periodo|periodi):\s*$")

RE_LETT_PAR = re.compile(r'^\s[a-z]{1,2}(?:-(?:%s))?\)\s' % ORD)

def parse_decree_article(raw):
    """Same label/rubric extraction as the engine; commi split with quote-depth awareness.
    A comma's text keeps its inner paragraphs separated by '\\n'."""
    a = E.parse_article(raw)
    if not a:
        return None
    lines = E.body_lines(raw)
    art_i = next((i for i, l in enumerate(lines) if LABEL.match(l)), 0)
    lines = lines[art_i:]
    first_c = next((i for i, l in enumerate(lines) if COMMA_LINE.match(l)), len(lines))
    commi, cur, cur_base, depth, virtual_pending = [], None, 0, 0, False
    punto, prev_par_lett_intro, par_lett = 0, False, False
    for i in range(first_c, len(lines)):
        l = lines[i]
        is_par = l.startswith(' ')                     # new GU paragraph
        if is_par:
            # il paragrafo appena chiuso era una lettera che introduce un elenco («…modificazioni:»)?
            prev_par_lett_intro = par_lett and bool(cur) and cur['text'].rstrip().endswith(':')
            par_lett = bool(RE_LETT_PAR.match(l))
            if par_lett:
                punto = 0
        if virtual_pending:
            if is_par and not l.lstrip().startswith('«'):
                depth += 1                             # GU forgot the opening «
            virtual_pending = False
        cm = E.comma_marker(lines, i) if is_par else None
        # numeri «1.» «2.» dentro una lettera (d.lgs. 115/2026: «b) al comma 2-quater sono
        # apportate le seguenti modificazioni: 1. al primo periodo …; 2. il secondo periodo …»):
        # un «N.» che apre la lista dopo una lettera che finisce con «:», o la continua, non è un comma
        if cm and depth <= 0 and (
                (base(cm.group(1)) == 1 and prev_par_lett_intro) or
                (punto and base(cm.group(1)) == punto + 1 and not RE_LETT_PAR.match(l))):
            punto = base(cm.group(1)); cm = None; is_punto = True
        else:
            is_punto = False
        if cm and depth <= 0 and (cur_base + 1 == base(cm.group(1)) or
                                  (base(cm.group(1)) == cur_base and cur is not None and cm.group(1) != cur['num'])):
            num = cm.group(1); cur_base = base(num)
            cur = {'num': num, 'text': re.sub(r'^\(*\s*%s\.\s*' % re.escape(num), '', l.strip(), count=1)}
            commi.append(cur)
        elif cur is not None:
            cur['text'] += ('\n' if is_par else ' ') + l.strip()
        depth += l.count('«') - l.count('»')
        if depth <= 0 and INTRO_OPEN.search(l):
            virtual_pending = True
    a['commi'] = commi
    a['depth_end'] = depth
    return a

def load_articles():
    arts, preamble = [], ''
    for f in sorted(glob.glob(os.path.join(SRC, 'a_*.html')), key=E.fkey):
        a = parse_decree_article(open(f, encoding='utf-8').read())
        if not a:
            continue
        a['file'] = os.path.basename(f)
        a['capo'] = int(re.match(r'a_(\d+)_', a['file']).group(1)) - 1   # idGruppo = capo
        if a.get('preamble') and not preamble:                           # premesse del decreto (nel file dell'art. 1)
            preamble = a['preamble']
        a['preamble'] = ''
        arts.append(a)
    return arts, preamble

def preamble_paragraphs(raw_first):
    """The decree's premesse («IL PRESIDENTE DELLA REPUBBLICA / Visti … / EMANA …») sit before
    «Art. 1» in the first Normattiva file: same leading-space paragraph rule."""
    lines = E.body_lines(raw_first)
    art_i = next((i for i, l in enumerate(lines) if LABEL.match(l)), 0)
    paras = []
    for l in lines[:art_i]:
        if l.startswith(' ') or not paras:
            paras.append(l.strip())
        else:
            paras[-1] += ' ' + l.strip()
    return paras

# ---------------------------------------------------------------- amend targets (per comma)
NOVELLA_VERB = re.compile(
    r"sono apportate le seguenti modificazioni|(?:e'|è|sono) (?:sostituit|inserit|abrogat|aggiunt|soppress|premess|cos[iì]' modificat)"
    r"|le parole", re.I)
RE_CONVERTED = re.compile(r"convertit[oa],?\s*(?:(?:con|senza)\s+modificazioni,?\s*)?dall[a']\s*$", re.I)

def comma_amend_target(lk, art, c):
    """Act novellated by this comma, from its head (first paragraph, up to the first «):
    the LAST act named before the novella verb, skipping the conversion law."""
    head = c['text'].split('\n', 1)[0].split('«', 1)[0]
    mv = NOVELLA_VERB.search(head)
    if not mv:
        return None
    last = None
    for m in E.MASTER.finditer(head[:mv.start()]):
        if m.group(0).lower().startswith('articol'):
            continue
        if RE_CONVERTED.search(head[max(0, m.start() - 45):m.start()]):
            continue
        _, info = lk._parse_act(head, m.start())
        if info:
            last = lk._act_target(info)
    return last

# «del menzionato/richiamato regolamento» is an anaphora too (the engine knows medesimo,
# stesso, citato, predetto, suddetto, detto, tale). Process-local patch of the shared regex.
E.RE_TAIL_ANAPH = re.compile(E.RE_TAIL_ANAPH.pattern.replace('dett[oa]|tal[ei])', 'dett[oa]|tal[ei]|menzionat[oa]|richiamat[oa])'), re.I)
# qualifiers the engine's grammar does not consume: a reference that goes on with one of these
# («articolo 18, comma 1, lettera a), punto 2, capoverso 1-quinquies, del decreto-legge…») has
# NOT reached its act tail yet — never resolve it to the decree.
_QITEM = r"(?:\d+(?:[-.][\w]+)*\)?|[a-z]{1,2}(?:-\w+)?\))"
RE_MORE_QUALS = re.compile(
    r"\s*,?\s*(?:(?:punt[oi]|capovers[oi]|numer[oi]|n\.|alinea)\s+%s(?:\s*(?:,|e|ed|o)\s*%s)*"
    r"|(?:prim|second|terz|quart|quint|ultim)[oa]\s+(?:periodo|comma|alinea))" % (_QITEM, _QITEM), re.I)

RE_PREF_ANAPH = re.compile(r"\b(?:stess|medesim|predett|suddett)[oa]\s+$", re.I)
RE_ART_NUM = re.compile(r"articolo\s+(\d{1,3}(?:-[a-z]+)?)\b", re.I)

class DecreeLinker(E.Linker):
    """Engine Linker + per-comma amend target (the engine's is per article, from the rubric).
    A bare «articolo N» resolves to the decree only where that is plausible: never in the
    premesse («Vista la legge 400/1988 … e, in particolare, l'articolo 15»), never when an act
    phrase follows that the grammar cannot parse («del regolamento di cui al decreto del
    Ministro…», «del decreto legislativo del Capo provvisorio dello Stato…»)."""
    def begin_article(self, label, art=None):
        super().begin_article(label, art)
        self._art_amend = ('ext', None) if label == 'preambolo' else self.amend_act
        self._comma_amend = (art or {}).get('amend', {})
        self.amend_act = self._art_amend
    def _tail(self, text, j):
        j0 = j
        while True:                # step over the qualifiers the grammar ignores, then the ones it knows
            m = RE_MORE_QUALS.match(text, j)
            j2 = self._consume_quals(text, m.end() if m else j)
            if j2 == j:
                break
            j = j2
        t = super()._tail(text, j)
        pa = getattr(self, '_pref_anaph', None)
        if t['kind'] == 'none' and pa and j == j0 and not E.RE_TAIL_ACT.match(text, j):
            # «comma 4 dello stesso articolo 4»: anafora PRIMA del rinvio -> l'atto in cui
            # quell'articolo è stato citato per ultimo (non l'ultimo atto nominato: nei testi
            # di novella in mezzo può comparire un regolamento)
            for kind, key, art in reversed(getattr(self, '_art_hist', [])):
                if art == pa:
                    if kind == 'extlocal':
                        return dict(kind='extlocal', key=key, end=j, act_emits=[])
                    return dict(kind='self', end=j, act_emits=[])
            if self.last_act:          # articolo mai citato prima: l'ultimo atto nominato
                return dict(kind='anaphora', end=j, act_emits=[])
        if t['kind'] == 'none' and (j != j0 or E.RE_TAIL_ACT.match(text, j)):
            # qualifiers stepped over but no readable act tail, or an act phrase the grammar
            # cannot parse («del regolamento di cui al decreto del Ministro…»): never guess
            return dict(kind='skip', end=j0, act_emits=[])
        return t
    def _chain(self, text, start):
        m = RE_ART_NUM.match(text, start)
        self._pref_anaph = (m.group(1) if m and RE_PREF_ANAPH.search(text[max(0, start - 30):start])
                            else None)
        try:
            return super()._chain(text, start)
        finally:
            self._pref_anaph = None
            if self.last_art:
                h = self.__dict__.setdefault('_art_hist', [])
                if not h or h[-1] != self.last_art:
                    h.append(self.last_art)
    def scope(self, scope_id):
        super().scope(scope_id)
        ca = getattr(self, '_comma_amend', None)
        if ca is not None:
            self.amend_act = ca.get(scope_id, getattr(self, '_art_amend', None))

# ---------------------------------------------------------------- render
RE_Q_HEAD  = re.compile(r'(^|<br>)(\s*«?Art\.\s(?:\d{1,3}(?:-(?:%s))?(?:\.\d+)?)\s\((?:[^()<]|<[^>]+>)*\)\.?)' % ORD)
RE_Q_COMMA = re.compile(r'(<br>)(\s*«?\d{1,3}(?:-(?:%s))?(?:\.\d+)?\.)(\s)' % ORD)
RE_LETT    = re.compile(r'(<br>)(\s*«?[a-z]{1,2}(?:-(?:%s))?\))(\s)' % ORD)
RE_NUMERO  = re.compile(r'(<br>)(\s*\d{1,2}(?:\.\d+)?\))(\s)')

def format_paragraphs(h):
    """'\\n' (GU paragraph inside a comma) -> <br>, then style the paragraph markers."""
    h = h.replace('\n', '<br>')
    h = RE_Q_HEAD.sub(r'\1<b class="q-head">\2</b>', h)
    h = RE_Q_COMMA.sub(r'\1<span class="cnum q">\2</span>\3', h)
    h = RE_LETT.sub(r'\1<span class="lett-n">\2</span>\3', h)
    h = RE_NUMERO.sub(r'\1<span class="lett-n">\2</span>\3', h)
    return h

def render_comma(art_label, c, lk, plain=False):
    lk.scope('com%s' % c['num'])
    body = format_paragraphs(E.render_segments(c['segments'], lk, plain=plain))
    num = '%s.' % c['num']
    if c.get('abrogato'):                          # comma soppresso / sostituito da uno strato
        num = '<del class="amd-del">%s</del>' % num
    elif c.get('numkind') == 'ins':
        num = '<ins class="amd-ins">%s</ins>' % num
    return '<div class="comma" id="art_%s-com%s"><span class="cnum">%s</span> %s</div>' % (
        art_label, c['num'], num, body)

def render_article(a, lk):
    lk.begin_article(a['label'], a)
    lk.scope('rubrica')
    rub = E.render_segments(a['rubrica_seg'], lk)
    parts = ['<div class="eli-subdivision art" id="art_%s">' % a['label'],
             '<p class="oj-ti-art">Art. %s</p>' % a['label'],
             '<div class="eli-title"><p class="oj-sti-art">%s</p></div>' % rub]
    for c in a['commi']:
        parts.append(render_comma(a['label'], c, lk))
    parts.append('</div>')
    return '\n'.join(parts)

import versioni as V                            # già sul path: l'ha importato il motore (251)
render_article = V.make_render_article(globals(), render_article)   # riga «Modificato dal …»

PAGE_TMPL = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>D.L. 100/2026 (attuazione del Patto) — testo vigente interattivo</title>
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/amend.css">
</head>
<body data-act="dl-2026-100">
<header class="topbar">
  <a class="home" href="../index.html">&#8962; Patto UE</a> <a class="home-here" href="#top">D.L. 100/2026</a>
  <button id="toc-toggle">Sommario</button>
  <span class="topttl">Prima attuazione italiana del Patto UE — <b>testo vigente</b>, rinvii normativi navigabili</span>
</header>
<div class="amd-banner">Testo del <b>decreto-legge 12 giugno 2026, n. 100</b> (G.U. Serie generale n. 134 del 12 giugno 2026), <b>convertito senza modificazioni</b> dalla legge 7 agosto 2026, n. 145 (G.U. n. 183 dell'8 agosto 2026). Gli artt. 1, 2 e 16 sono stati poi modificati dall'art. 7 del <b>d.l. 7 agosto 2026, n. 144</b> (G.U. n. 182 del 7 agosto 2026, in vigore dall'8 agosto) e l'art. 17 dall'art. 4 del <b>d.l. 29 settembre 2026, n. 168</b> (G.U. n. 226 del 29 settembre 2026, in vigore dal 30 settembre): il testo è quello vigente e, sotto la rubrica degli articoli modificati, se ne leggono la versione precedente e le modifiche. Il Capo II (artt. 10-17) attua il Patto per novella: le modifiche al <a href="../dlgs-142-2015/index.html">d.lgs. 142/2015</a> (art. 10), al <a href="../dlgs-25-2008/index.html">d.lgs. 25/2008</a> (art. 11) e al <a href="../dlgs-286-1998/index.html">d.lgs. 286/1998</a> (art. 12) si leggono evidenziate nei rispettivi testi coordinati. Ogni rinvio normativo è navigabile; i rinvii agli atti del Patto e alle leggi coordinate aprono i relativi testi interattivi.</div>
<div class="layout">
<nav class="toc" id="toc"><div class="toc-title">D.L. 12 giugno 2026, n. 100</div>
{toc}
</nav>
<main class="doc" id="top">
<div class="eli-main-title"><p class="oj-doc-ti">DECRETO-LEGGE 12 giugno 2026, n. 100</p>
<p class="oj-doc-ti sub">Misure urgenti in materia di giustizia e per l'attuazione del Patto dell'Unione europea sulla migrazione e l'asilo del 14 maggio 2024</p>
<p class="oj-doc-ti note">Testo vigente (convertito senza modificazioni dalla l. 7 agosto 2026, n. 145) — rinvii normativi navigabili</p></div>
{body}
<p class="disclaimer">Testo non ufficiale a fini di studio. Fonte: Normattiva / Gazzetta Ufficiale Serie generale n. 134 del 12 giugno 2026. Decreto convertito senza modificazioni dalla legge 7 agosto 2026, n. 145. Fa fede unicamente il testo pubblicato nella Gazzetta Ufficiale.</p>
</main>
</div>
<div id="tip" class="tip" hidden></div>
<aside id="panel" class="panel" hidden>
  <div class="panel-bar"><button id="panel-back" class="pbtn" hidden>&#8592;</button><div id="panel-crumb" class="crumb"></div><button id="panel-close" class="pbtn">&#10005;</button></div>
  <div id="panel-body" class="panel-body"></div>
  <div class="panel-foot"><a class="panel-home" href="../index.html">&#8962; Patto UE</a><a id="panel-go" href="#">Vai all'articolo &#8594;</a></div>
</aside>
<button id="return-chip" hidden>&#8617; Torna al punto precedente</button>
<script src="assets/data.js"></script>
<script src="assets/app.js"></script>
</body>
</html>"""

EXTRA_CSS = """
/* --- d.l. 100/2026: capoversi interni ai commi (testi novellati fra «») --- */
.comma .cnum.q{ color:#555; font-weight:600; }
.comma .q-head{ font-weight:600; color:#0d3a76; }
.comma br + .cnum.q, .comma br + .q-head{ margin-left:1.2em; }
.preambolo{ font-style:normal; color:#333; }
.preambolo p{ margin:.35em 0; }
.preambolo p.emana{ font-weight:600; text-align:center; letter-spacing:.06em; }
"""

def load_overrides():
    fp = os.path.join(HERE, 'overrides.json')
    if not os.path.exists(fp):
        return []
    return json.load(open(fp, encoding='utf-8'))

def plain_heading(a):
    rub = ''.join(t for k, t, _ in a.get('rubrica_seg') or [('normal', a['rubrica'], None)] if k != 'del')
    return html.escape(re.sub(r'\s+', ' ', rub).strip())

def strati():
    """Modifiche successive al d.l. (amendments_<atto>.json, es. lo strato del d.l. 144/2026):
    le applica il motore a strati di ../versioni.py, via E.apply_amendments."""
    ams = []
    for f in sorted(glob.glob(os.path.join(HERE, 'amendments_*.json'))):
        d = json.load(open(f, encoding='utf-8'))
        V.ACT_NAMES.setdefault(d['_atto'], d.get('_nome', d['_atto']))
        V.ACT_DATES.setdefault(d['_atto'], d.get('_data', ''))
        ams += d['amendments']
    return ams

def build_site(arts, preamble_paras):
    rep = E.Report()
    E.apply_amendments(arts, strati(), rep)      # init dei segmenti + strati (versioni.py)
    for amid, letter, status, detail in rep.rows:
        if status != 'applicata':
            print('ATTENZIONE modifica %s (%s): %s — %s' % (amid, letter, status, detail))
    self_labels = {a['label'] for a in arts}
    core, eu_map, it_map = E.load_core_acts()
    lk = DecreeLinker(self_labels, core, eu_map, it_map, load_overrides())
    # per-comma amend targets
    amend_table = []
    for a in arts:
        a['amend'] = {}
        for c in a['commi']:
            t = comma_amend_target(lk, a, c)
            a['amend']['com%s' % c['num']] = t
            if t:
                amend_table.append((a['label'], c['num'], t[0], t[1] if t[0] != 'self' else '—'))
    toc, body = [], []
    # premesse
    if preamble_paras:
        lk.begin_article('preambolo', None); lk.scope('preambolo')
        toc.append('<a class="toc-art" href="#preambolo"><span class="toc-n">§</span><span class="toc-art-h">Premesse</span></a>')
        ps = []
        for p in preamble_paras:
            cls = ' class="emana"' if re.match(r'^(IL PRESIDENTE|EMANA|Emana)', p) else ''
            ps.append('<p%s>%s</p>' % (cls, E.link_text(p, lk)))
        body.append('<div class="preambolo" id="preambolo">%s</div>' % '\n'.join(ps))
    cur_capo = None
    for a in arts:
        if CAPI and a['capo'] != cur_capo:          # (il d.lgs. 115/2026, che riusa questo builder, non ha capi)
            cur_capo = a['capo']
            num, head = CAPI[cur_capo]
            toc.append('<div class="toc-capo">%s — %s</div>' % (html.escape(num), html.escape(head)))
            body.append('<h2 class="capo" id="capo_%d">%s — %s</h2>' % (cur_capo, html.escape(num), html.escape(head)))
        toc.append('<a class="toc-art%s" href="#art_%s"><span class="toc-n">%s</span><span class="toc-art-h">%s</span></a>'
                   % (' changed' if a.get('storia') else '', a['label'], html.escape(a['label']), plain_heading(a)))
        body.append(render_article(a, lk))
    page = PAGE_TMPL.replace('{toc}', '\n'.join(toc)).replace('{body}', '\n'.join(body))
    open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(page)

    # data.js — the decree + the cited articles of the hoverable core acts
    acts = {E.SELF_KEY: {'label': SELF_LABEL, 'short': SELF_SHORT, 'file': 'index.html', 'articles': {}}}
    for a in arts:
        lk.begin_article(a['label'], a)
        frags = [[base(c['num']), render_comma(a['label'], c, lk, plain=True)] for c in a['commi']]
        acts[E.SELF_KEY]['articles'][a['label']] = {
            'label': 'Art. %s' % a['label'], 'heading': plain_heading(a),
            'anchor': 'art_%s' % a['label'], 'frags': frags}
    for key, used in sorted(lk.cited.items()):
        c = core[key]
        acts[key] = {'label': c['label'], 'short': c['short'], 'external': True,
                     'version': c['version'], 'eurlex': c['url'], 'file': c['url'],
                     'articles': {an: c['articles'][an] for an in sorted(used) if an in c['articles']}}
    with open(os.path.join(HERE, 'assets', 'data.js'), 'w', encoding='utf-8') as f:
        f.write('window.PACTO=' + json.dumps({'acts': acts}, ensure_ascii=False) + ';\n')
    open(os.path.join(HERE, 'assets', 'amend.css'), 'w', encoding='utf-8').write(E.AMEND_CSS + EXTRA_CSS)

    # report
    lines = ['# Report — d.l. 100/2026, testo vigente interattivo', '',
             'Fonte: Normattiva (snapshot `nm_fresh_20260710/dl100/`, 19 articoli). Il decreto è stato '
             '**convertito senza modificazioni** dalla l. 7 agosto 2026, n. 145: il testo è quello vigente.', '',
             'Atto di novella (non consolidato): nessuna modifica evidenziata. Bersaglio dei rinvii «nudi» '
             '(«articolo N» senza atto) per comma, ricavato dall\'atto nominato prima del verbo di novella:', '',
             '| Art. | Comma | Bersaglio |', '|---|---|---|']
    for al, cn, kind, key in amend_table:
        lines.append('| %s | %s | %s %s |' % (al, cn, kind, key))
    lk.unresolved = list(dict.fromkeys(lk.unresolved))      # page + hover frags: linked twice
    lines += ['', 'Rinvii lasciati non collegati (da rivedere a mano): %d' % len(lk.unresolved), '']
    for art, ctx in lk.unresolved:
        lines.append('- art. %s: …%s…' % (art, re.sub(r'\s+', ' ', ctx)))
    open(os.path.join(HERE, 'REPORT_MODIFICHE.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    return lk, amend_table

def main():
    arts, _ = load_articles()
    first = sorted(glob.glob(os.path.join(SRC, 'a_*.html')), key=E.fkey)[0]
    paras = preamble_paragraphs(open(first, encoding='utf-8').read())
    bad_depth = [(a['label'], a['depth_end']) for a in arts if a['depth_end'] != 0]
    lk, amend_table = build_site(arts, paras)
    print('Articoli:', len(arts), '| commi:', {a['label']: [c['num'] for c in a['commi']] for a in arts})
    print('Premesse: %d capoversi' % len(paras))
    if bad_depth:
        print('ATTENZIONE virgolette non bilanciate a fine articolo:', bad_depth)
    print('Bersagli di novella per comma:')
    for row in amend_table:
        print('  art. %s c. %s -> %s %s' % row)
    cited = {k: len(v) for k, v in sorted(lk.cited.items())}
    print('Atti-fonte resi navigabili (articoli citati):', cited or 'nessuno')
    print('Rinvii lasciati non collegati:', len(lk.unresolved))
    for art, ctx in lk.unresolved:
        print('   - art. %s: …%s…' % (art, re.sub(r'\s+', ' ', ctx)))
    if lk.overrides:
        unused = [r for i, r in enumerate(lk.overrides) if i not in lk.ov_hits]
        print('Override applicati: %d/%d' % (len(lk.ov_hits), len(lk.overrides)))
        for r in unused:
            print('  ⚠️ OVERRIDE NON APPLICATO:', r)
    print('Scritti: index.html, assets/data.js, assets/amend.css, REPORT_MODIFICHE.md')

if __name__ == '__main__':
    main()
