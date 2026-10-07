#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build the interactive, tracked-changes version of d.lgs. 18/8/2015 n. 142
(accoglienza dei richiedenti protezione internazionale) as modified by
art. 10 d.l. 12/6/2026 n. 100 (recepimento della direttiva (UE) 2024/1346).

SOURCE: Normattiva caricaArticolo HTML (complete, merged display text) in ../nm_html_142/.
  (The AKN export is NOT used as text source: it stores some amendments only in
   <meta><textualMod> and drops them from <body>.)

Pipeline: parse articles -> apply amendments.json (tracked changes) -> link
cross-references -> render index.html + assets/data.js + ext pages + REPORT_MODIFICHE.md.

Cross-references to d.lgs. 25/2008 deep-link to the sibling "Dlgs25 interattivo"
site; the 10 EU Pact acts deep-link to the "Patto interattivo" site; d.lgs. 286/1998
and 251/2007 are hoverable from their consolidated .txt. Adapted from build_dlgs25.py.
"""
import re, html, json, glob, os, difflib

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, "..", "nm_html_142")
ORD  = "bis|ter|quater|quinquies|sexies|septies|octies|novies|nonies|decies|undecies|duodecies|terdecies"
NUM  = r"\d{1,3}(?:-(?:%s))?" % ORD
COMMA_LINE = re.compile(r'^\s*\(*\s*(%s)\.(?!\d)' % NUM)
LABEL = re.compile(r'^\s*Art\.\s*(%s(?:\.\d+)?)' % NUM)

def base(n): return int(re.match(r'\d+', n).group())

def _unwrap_outer_parens(s):
    """d.lgs. 142/2015 wraps the rubric of amended articles in a single outer paren pair
    ('(Iscrizione anagrafica)'). Strip ONE balanced outer pair when it spans the whole
    string, preserving inner parens ('(... regolamento (UE) n. 604/2013)' -> '... (UE) ...')."""
    s = s.strip()
    if not (s.startswith('(') and s.endswith(')')):
        return s
    depth = 0
    for i, ch in enumerate(s):
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
            if depth == 0:
                return (s[1:-1].strip() if i == len(s) - 1 else s)
    return s

def normalize_ocr(t):
    """Fix obvious Normattiva rendering artifacts (the true legal text is unambiguous):
      '604//2013' -> '604/2013' ; '1'ufficio' (digit-1 for letter-l) -> 'l'ufficio'."""
    t = t.replace('//', '/')
    t = re.sub(r"(?<!\d)1'(?=[A-Za-zÀ-ÿ])", "l'", t)
    t = t.replace('protezionen', 'protezione')     # OCR typo in the art. 4 rubric
    return t

# ---------------------------------------------------------------- parse
def body_lines(raw):
    d = re.sub(r'(?s)<!--.*?-->', ' ', raw)
    d = re.sub(r'(?s)<(script|style)[^>]*>.*?</\1>', ' ', d)
    pres = re.findall(r'(?s)<pre[^>]*>(.*?)</pre>', d)
    best = ''
    for p in pres:
        t = html.unescape(re.sub(r'(?s)<[^>]+>', '', p))
        if t.lstrip().startswith('Art.') and len(t) > len(best):
            best = t
    if not best:
        for p in pres:
            t = html.unescape(re.sub(r'(?s)<[^>]+>', '', p))
            if re.search(r'\bArt\.\s*\d', t) and len(t) > len(best):
                best = t
    lines = [normalize_ocr(re.sub(r'[ \t\xa0]+', ' ', l)).rstrip() for l in best.split('\n')]
    out = []
    for l in lines:
        if re.match(r'\s*\(*\s*AGGIORNAMENTO', l):
            break
        out.append(l)
    return [l for l in out if l.strip()]

RE_WRAP_TAIL = re.compile(r"(?:comm[ai]|articol[oi]|lettera|lettere|numero|numeri|paragraf[oi]|n\.)\s*$", re.I)

def comma_marker(lines, i):
    """COMMA_LINE.match con guardia: se la riga precedente finisce con un rinvio
    troncato dall'a-capo, il «N.» a inizio riga e' la continuazione della citazione
    («... dall'articolo 3, comma / 3. ...»), non un nuovo comma."""
    cm = COMMA_LINE.match(lines[i])
    if cm and i > 0 and RE_WRAP_TAIL.search(lines[i - 1]):
        return None
    return cm

def parse_article(raw, known_label=None):
    lines = body_lines(raw)
    if not lines:
        return None
    # locate the "Art. N" heading line (skip any preamble before it)
    art_i = next((i for i, l in enumerate(lines) if LABEL.match(l)), 0)
    preamble = ' '.join(lines[:art_i]).strip() if art_i else ''
    lines = lines[art_i:]
    m = LABEL.match(lines[0])
    label = m.group(1) if m else (known_label or '??')
    first_c = next((i for i, l in enumerate(lines) if COMMA_LINE.match(l)), len(lines))
    htext = ' '.join(lines[:first_c]).strip()
    htext = re.sub(r'^\s*Art\.\s*%s(?:\.\d+)?\s*\.?\s*' % NUM, '', htext, count=1)
    rubrica = htext.replace('((', '').replace('))', '').strip()
    if rubrica.count('(') != rubrica.count(')'):
        rubrica = rubrica.strip('()')
    rubrica = _unwrap_outer_parens(rubrica.strip(' .')).strip(' .')
    commi = []
    cur_base = 0
    i = first_c
    while i < len(lines):
        cm = comma_marker(lines, i)
        if not cm or not (cur_base <= base(cm.group(1)) <= cur_base + 1):
            if commi:
                commi[-1]['text'] += ' ' + lines[i].strip()
            i += 1
            continue
        num = cm.group(1); cur_base = base(num)
        buf = [lines[i]]; i += 1
        while i < len(lines):
            nm = comma_marker(lines, i)
            if nm and (cur_base <= base(nm.group(1)) <= cur_base + 1):
                break
            buf.append(lines[i]); i += 1
        text = re.sub(r'^\(*\s*%s\.\s*' % re.escape(num), '', ' '.join(buf).strip(), count=1)
        if commi and commi[-1]['num'] == num:          # dedup wrap-induced repeats
            commi[-1]['text'] += ' ' + text
        else:
            commi.append({'num': num, 'text': text})
    abrogated = bool(re.match(r'(?i)articolo abrogato', rubrica))
    return dict(label=label, rubrica=rubrica, commi=commi, preamble=preamble, abrogated=abrogated)

def fkey(path):
    # 4o intero = idSottoArticolo1 di Normattiva (10 = articolo normale, 20/30/40 =
    # articoli DECIMALI 39-bis.1 ecc., file a_G_A_S_S1.html): ordina 39-bis < 39-bis.1 < 39-ter
    nums = [int(x) for x in re.findall(r'\d+', os.path.basename(path))]
    g, a, s = nums[:3]
    return (g, a, s, nums[3] if len(nums) > 3 else 10)

def load_articles():
    arts = []
    for f in sorted(glob.glob(os.path.join(SRC, 'a_*.html')), key=fkey):
        a = parse_article(open(f, encoding='utf-8').read())
        if a:
            a['file'] = os.path.basename(f)
            arts.append(a)
    return arts

# ---------------------------------------------------------------- amendment engine
class Report:
    def __init__(self): self.rows = []
    def add(self, amid, letter, status, detail=''):
        self.rows.append((amid, letter, status, detail))

def norm_ws(s): return re.sub(r'\s+', ' ', s).strip()

def find_article(arts, num):
    for a in arts:
        if a['label'] == num:
            return a
    return None

def find_comma(art, num):
    for c in art['commi']:
        if c['num'] == num:
            return c
    return None

def seg_text(c):
    """Concatenate current visible text of a comma's segments (normal+ins, not del)."""
    return ''.join(s[1] for s in c['segments'] if s[0] != 'del')

def init_segments(art):
    for c in art['commi']:
        c['segments'] = [('normal', c['text'], None)]
        c.setdefault('numkind', 'keep')
    art.setdefault('rubrica_seg', [('normal', art['rubrica'], None)])
    art.setdefault('numkind', 'keep')

_DIFF_TOK = re.compile(r'[^\s,;:.]+|[,;:.]|\s+')   # words (with trailing ')'), punctuation, whitespace

def diff_segments(old, new, src):
    """Word-level diff of an in-place substitution: tokens that are UNCHANGED stay
    'normal' (not struck), only the genuinely removed/added tokens become del/ins — so
    e.g. «articoli 23, 29 e 29-bis» -> «articoli 23, 23-bis, 29 e 29-bis» shows only
    «23-bis,» as inserted, leaving 23/29/29-bis untouched (and still linkable)."""
    a, b = _DIFF_TOK.findall(old), _DIFF_TOK.findall(new)
    segs = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == 'equal':
            segs.append(('normal', ''.join(a[i1:i2]), None))
        elif op == 'delete':
            segs.append(('del', ''.join(a[i1:i2]), src))
        elif op == 'insert':
            segs.append(('ins', ''.join(b[j1:j2]), src))
        else:                                          # replace
            segs.append(('del', ''.join(a[i1:i2]), src))
            segs.append(('ins', ''.join(b[j1:j2]), src))
    return [s for s in segs if s[1]]


def apply_substitute(art, comma_num, pairs, src, rep, amid, letter, on_rubrica=False):
    ok_all = True
    for old, new in pairs:
        target_segs = art['rubrica_seg'] if on_rubrica else (find_comma(art, comma_num)['segments'] if find_comma(art, comma_num) else None)
        where = 'rubrica' if on_rubrica else ('comma %s' % comma_num)
        if target_segs is None:
            rep.add(amid, letter, 'NON APPLICATA', 'comma %s non trovato in art. %s' % (comma_num, art['label']))
            ok_all = False; continue
        # find old in a 'normal' segment (whitespace-insensitive)
        hit = False
        for idx, (k, txt, s) in enumerate(target_segs):
            if k != 'normal':
                continue
            pos = find_flexible(txt, old)
            if pos is None:
                continue
            a, b = pos
            before, mid, after = txt[:a], txt[a:b], txt[b:]
            newsegs = []
            if before: newsegs.append(('normal', before, None))
            newsegs.extend(diff_segments(mid, new, src))   # minimal word-level diff, not blanket del+ins
            if after:  newsegs.append(('normal', after, None))
            target_segs[idx:idx+1] = newsegs
            hit = True
            break
        if not hit:
            rep.add(amid, letter, 'NON APPLICATA', 'testo da sostituire non trovato in %s di art. %s: «%s…»'
                    % (where, art['label'], old[:45]))
            ok_all = False
    if ok_all:
        rep.add(amid, letter, 'applicata', 'sostituzione/i in %s art. %s'
                % ('rubrica' if on_rubrica else 'comma %s' % comma_num, art['label']))
    return ok_all

def find_flexible(haystack, needle):
    """Find needle in haystack tolerant of whitespace differences; return (start,end) in haystack or None."""
    pat = re.escape(needle)
    pat = re.sub(r'\\\s+|\s+', r'\\s+', pat)  # any run of ws in needle -> \s+
    m = re.search(pat, haystack)
    return (m.start(), m.end()) if m else None

# expose with the spelling used above
find_flexible = find_flexible
find_flexible_ = find_flexible

def apply_amendments(arts, amendments, rep):
    for a in arts:
        init_segments(a)
    idx_by_label = {a['label']: i for i, a in enumerate(arts)}
    for am in amendments:
        amid, letter, op = am['id'], am['letter'], am['op']
        tgt = am['target']; src = am.get('src') or 'art. 10, %s, d.l. 100/2026' % letter
        art_label = tgt.get('art')
        art = find_article(arts, art_label) if art_label else None

        if op == 'substitute':
            if art is None:
                rep.add(amid, letter, 'NON APPLICATA', 'art. %s non trovato' % art_label); continue
            apply_substitute(art, tgt.get('comma'), am['pairs'], src, rep, amid, letter,
                             on_rubrica=bool(tgt.get('rubrica')))

        elif op == 'replace_rubrica':
            if art is None:
                rep.add(amid, letter, 'NON APPLICATA', 'art. %s non trovato' % art_label); continue
            art['rubrica_seg'] = [('del', art['rubrica'], src), ('ins', am['text'], src)]
            rep.add(amid, letter, 'applicata', 'rubrica art. %s sostituita' % art_label)

        elif op == 'replace_comma':
            c = find_comma(art, tgt['comma']) if art else None
            if not c:
                rep.add(amid, letter, 'NON APPLICATA', 'comma %s non trovato in art. %s' % (tgt.get('comma'), art_label)); continue
            old = seg_text(c)
            c['segments'] = [('del', old, src), ('ins', am['text'], src)]
            rep.add(amid, letter, 'applicata', 'comma %s art. %s sostituito' % (tgt['comma'], art_label))

        elif op == 'repeal_comma':
            done = []
            for cn in am['commi']:
                c = find_comma(art, cn) if art else None
                if c:
                    c['segments'] = [('del', seg_text(c), src)]
                    c['abrogato'] = True; done.append(cn)
            miss = [cn for cn in am['commi'] if cn not in done]
            rep.add(amid, letter, 'applicata' if not miss else 'PARZIALE',
                    'abrogati commi %s di art. %s%s' % (','.join(done), art_label,
                    '' if not miss else ' — non trovati: ' + ','.join(miss)))

        elif op == 'insert_comma_after':
            if art is None:
                rep.add(amid, letter, 'NON APPLICATA', 'art. %s non trovato' % art_label); continue
            after = tgt['after_comma']; pos = next((i for i, c in enumerate(art['commi']) if c['num'] == after), None)
            nc = {'num': am['comma']['num'], 'text': am['comma']['text'],
                  'segments': [('ins', am['comma']['text'], src)], 'numkind': 'ins'}
            if pos is None:
                art['commi'].append(nc)
                rep.add(amid, letter, 'PARZIALE', 'comma %s dopo %s: ancora %s non trovato, aggiunto in coda'
                        % (am['comma']['num'], after, after))
            else:
                art['commi'].insert(pos + 1, nc)
                rep.add(amid, letter, 'applicata', 'inserito comma %s dopo comma %s in art. %s'
                        % (am['comma']['num'], after, art_label))

        elif op == 'replace_commas':
            if art is None:
                rep.add(amid, letter, 'NON APPLICATA', 'art. %s non trovato' % art_label); continue
            old_nums = am['commi_old']
            positions = [i for i, c in enumerate(art['commi']) if c['num'] in old_nums]
            if not positions:
                rep.add(amid, letter, 'NON APPLICATA', 'commi %s non trovati in art. %s' % (','.join(old_nums), art_label)); continue
            ins_at = positions[0]
            for i in positions:                              # mark old as deleted
                c = art['commi'][i]
                c['segments'] = [('del', seg_text(c), src)]; c['abrogato'] = True
            newcommi = [{'num': cc['num'], 'text': cc['text'],
                         'segments': [('ins', cc['text'], src)], 'numkind': 'ins'} for cc in am['commi_new']]
            # insert the new commi right after the first replaced one
            for off, nc in enumerate(newcommi):
                art['commi'].insert(positions[0] + 1 + off, nc)
            rep.add(amid, letter, 'applicata', 'commi %s di art. %s sostituiti con %s'
                    % (','.join(old_nums), art_label, ','.join(c['num'] for c in newcommi)))

        elif op == 'replace_article':
            if art is None:
                rep.add(amid, letter, 'NON APPLICATA', 'art. %s non trovato' % art_label); continue
            for c in art['commi']:
                c['segments'] = [('del', seg_text(c), src)]; c['abrogato'] = True
            if norm_ws(art['rubrica']) != norm_ws(am['rubrica']):   # only mark if rubric actually changed
                art['rubrica_seg'] = [('del', art['rubrica'], src), ('ins', am['rubrica'], src)]
            newcommi = [{'num': cc['num'], 'text': cc['text'],
                         'segments': [('ins', cc['text'], src)], 'numkind': 'ins'} for cc in am['commi']]
            art['commi'].extend(newcommi)
            rep.add(amid, letter, 'applicata', 'art. %s integralmente sostituito (%d commi nuovi)'
                    % (art_label, len(newcommi)))

        elif op == 'insert_article_after':
            after = tgt['after_art']; pos = idx_by_label.get(after)
            newart = dict(label=am['art_num'],
                          rubrica=am['rubrica'], rubrica_seg=[('ins', am['rubrica'], src)],
                          commi=[{'num': cc['num'], 'text': cc['text'],
                                  'segments': [('ins', cc['text'], src)], 'numkind': 'ins'} for cc in am['commi']],
                          preamble='', abrogated=False, numkind='ins', inserted=True)
            if pos is None:
                arts.append(newart)
                rep.add(amid, letter, 'PARZIALE', 'art. %s inserito in coda (ancora %s non trovato)' % (am['art_num'], after))
            else:
                arts.insert(pos + 1, newart)
                idx_by_label = {a['label']: i for i, a in enumerate(arts)}
                rep.add(amid, letter, 'applicata', 'inserito nuovo art. %s dopo art. %s' % (am['art_num'], after))
        else:
            rep.add(amid, letter, 'NON APPLICATA', 'op sconosciuta: %s' % op)

# ---------------------------------------------------------------- cross-reference linker
MONTHS = {'gennaio':'01','febbraio':'02','marzo':'03','aprile':'04','maggio':'05','giugno':'06',
          'luglio':'07','agosto':'08','settembre':'09','ottobre':'10','novembre':'11','dicembre':'12'}
IT_TYPE = {'decreto legislativo':'decreto.legislativo', 'decreto-legge':'decreto.legge',
           'decreto del presidente della repubblica':'decreto.del.presidente.della.repubblica',
           'legge':'legge', 'regio decreto':'regio.decreto'}
KNOWN_DATE = {('decreto.legislativo','25'):'2008-01-28', ('decreto.legislativo','286'):'1998-07-25',
              ('decreto.legislativo','251'):'2007-11-19', ('decreto.legislativo','142'):'2015-08-18'}

def eli_url(kind, year, num):
    t = {'regolament':'reg','direttiv':'dir','decision':'dec'}[
        next(k for k in ('regolament','direttiv','decision') if kind.lower().startswith(k))]
    return 'https://eur-lex.europa.eu/eli/%s/%d/%d/oj/ita' % (t, int(year), int(num))

def normattiva_url(urntype, num, date):
    return 'https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:%s:%s;%s' % (urntype, date, num)

# ---------------------------------------------------------------------------
# The cross-reference resolver is a faithful port of the act-context grammar in
# build_patto_interattivo.py (Fable), EXTENDED to Italian national acts (which
# the Pact corpus never cites). A single left-to-right scan threads a per-article
# context so each "articolo N" resolves to the act named in its TAIL
# ("del regolamento (UE) 2024/1348", "del decreto legislativo ... n. 251"), to an
# anaphoric antecedent ("del medesimo regolamento" -> last act mentioned), to the
# host decree ("del presente decreto" / a bare reference that exists here), or to
# a plain external link. The previous build linked EVERY "articolo N" matching a
# d.lgs.25 article number to d.lgs.25 — wrong for 30% of refs (its RE_EXT_AHEAD
# guard never fired: `^` in re.match(text,pos) anchors to string start, not pos).
#
# Routing of a resolved reference:
#   self      -> d.lgs. 142 itself           -> internal <a class="xref"> (hover+panel)
#   extlocal  -> a "core act" (d.lgs.25, 286, 251, 10 Pact acts) -> hoverable <a class="xref">
#   ext       -> any other act               -> plain <a class="lawlink ext"> link
# d.lgs.25 and the Pact acts are 'deep' core acts: their xref deep-links to a sibling site.
# ---------------------------------------------------------------------------

# Shared registry of every interactive site (act-key -> slug/src/href) — see ../sites.json.
# Cross-links are RELATIVE to the deploy tree (/patto-interattivo/): the hub/home is one
# level up (../), each sibling law is ../<slug>/, each Pact act page is ../<num>.html. The
# SAME bundle therefore resolves on file://, on localhost and live, with no absolute URLs.
SITES = json.load(open(os.path.join(HERE, '..', 'sites.json'), encoding='utf-8'))
SELF_KEY = 'dlgs-2015-142'
SELF_IT  = tuple(SITES['acts'][SELF_KEY]['it'])   # named self-reference -> internal xref

def _sibling_href(key):
    return '../%s/index.html' % SITES['acts'][key]['slug']
# non-core codici cited by d.lgs. 142 -> plain Normattiva links
CODICI = {
    'di procedura civile': ('regio.decreto', '1443', '1940-10-28'),
    'di procedura penale': ('decreto.del.presidente.della.repubblica', '447', '1988-09-22'),
    'civile':              ('regio.decreto', '262', '1942-03-16'),
    'penale':              ('regio.decreto', '1398', '1930-10-19'),
}

def _strip_anchors(h):
    """Lifted Patto frags carry <a> links to Patto pages; keep the text only."""
    return re.sub(r'</?a\b[^>]*>', '', h)

def _load_patto_acts():
    p = os.path.join(HERE, '..', SITES['pact_src'], 'assets', 'data.js')
    js = open(p, encoding='utf-8').read()
    i = js.index('window.PACTO=') + len('window.PACTO=')
    j = js.index(';window.PACTO_V', i)
    return json.loads(js[i:j])['acts']

def _load_sibling_act(folder, actkey):
    """A sibling interactive site's data.js holds its coordinated act
    (window.PACTO={'acts': {<actkey>: {...}, ...}};). Return that act dict."""
    p = os.path.join(HERE, '..', folder, 'assets', 'data.js')
    js = open(p, encoding='utf-8').read().strip()
    js = js[js.index('=') + 1:]
    if js.endswith(';'):
        js = js[:-1]
    return json.loads(js)['acts'][actkey]

def _clean_sibling_frag(h):
    """Turn a sibling tracked-changes frag into clean current text for a hover tooltip:
    drop struck (<del>) text, unwrap <ins>/<a> keeping their text."""
    h = re.sub(r'(?s)<del\b[^>]*>.*?</del>', '', h)     # remove soppresso text
    h = re.sub(r'</?(?:ins|a)\b[^>]*>', '', h)            # unwrap ins + links
    return re.sub(r'\s{2,}', ' ', h)

def _parse_it_txt(path):
    """Parse a consolidated .txt (same 'Art. N.' / comma-line grammar as d.lgs. 25)
    into {art_label: {label, heading, anchor, frags:[[comma_num, html], ...]}}."""
    arts = {}
    cur = None
    for raw in open(path, encoding='utf-8'):
        line = normalize_ocr(re.sub(r'[ \t\xa0]+', ' ', raw)).rstrip()
        if not line.strip():
            continue
        ml = LABEL.match(line)
        if ml:
            lab = ml.group(1)
            heading = re.sub(r'^\s*Art\.\s*%s(?:\.\d+)?\s*\.?\s*' % NUM, '', line, count=1).strip(' .')
            cur = lab
            arts[lab] = dict(label='Art. %s' % lab, heading=heading, anchor='art_%s' % lab, frags=[])
            continue
        if cur is None:
            continue
        if re.match(r'\s*\(*\s*(?:AGGIORNAMENTO|CAPO|TITOLO|Capo|Titolo)\b', line):
            continue
        cm = COMMA_LINE.match(line)
        if cm:
            num = cm.group(1)
            body = re.sub(r'^\(*\s*%s\.\s*' % re.escape(num), '', line, count=1)
            arts[cur]['frags'].append([base(num), '<div class="comma"><span class="cnum">%s.</span> %s</div>'
                                       % (html.escape(num), html.escape(body))])
        elif arts[cur]['frags']:                       # continuation of the previous comma
            f = arts[cur]['frags'][-1]
            f[1] = f[1][:-6] + ' ' + html.escape(line) + '</div>'
    return arts

def load_core_acts():
    """Build the registry of hoverable acts + the (eu)/(it) -> key resolver maps, from the
    shared ../sites.json. The EU Pact acts deep-link to ../<num>.html (pages at the deploy
    root); every OTHER national interactive site deep-links to ../<slug>/index.html#art_N.
    All four national texts (25, 142, 286, 251) thus interlink hoverably."""
    core = {}
    try:
        patto = _load_patto_acts()
    except Exception as e:
        print('  ATTENZIONE: data.js del Patto non leggibile (%s) — gli atti del Patto resteranno link EUR-Lex.' % e)
        patto = {}
    for num, src in patto.items():
        lab = src.get('label', '')
        pfx = 'dir' if lab.lower().startswith('direttiv') else 'reg'
        key = '%s-2024-%s' % (pfx, num)
        arts = {an: dict(label=info['label'], heading=info['heading'], anchor=info['anchor'],
                         frags=[[f[0], _strip_anchors(f[1])] for f in info['frags']])
                for an, info in src['articles'].items()}
        core[key] = dict(kind='pact', eu=(2024, int(num)), label=lab, short=src.get('short'),
                         version='Patto UE — interattivo', deep=True,
                         url='../' + (src.get('file') or (num + '.html')),
                         articles=arts, artset=set(arts))
    for key, meta in SITES['acts'].items():
        if key == SELF_KEY:
            continue
        try:
            sib = _load_sibling_act(meta['src'], key)
        except Exception as e:
            print('  ATTENZIONE: data.js di "%s" non leggibile (%s) — %s resterà link semplice.' % (meta['src'], e, meta['label']))
            continue
        sarts = {an: dict(label=info['label'], heading=info['heading'], anchor=info['anchor'],
                          frags=[[f[0], _clean_sibling_frag(f[1])] for f in info['frags']])
                 for an, info in sib['articles'].items()}
        ver = ('Coordinato con %s — interattivo' % meta['coord']) if meta.get('coord') else 'Testo vigente — interattivo'
        core[key] = dict(kind='sibling', it=tuple(meta['it']), date=meta['date'],
                         label=meta['label'], short=meta['short'] + ' — interattivo',
                         version=ver, deep=True, url=_sibling_href(key),
                         articles=sarts, artset=set(sarts))
    _merge_extra_acts(core)
    eu_map = {c['eu']: k for k, c in core.items() if c.get('eu')}
    it_map = {c['it']: k for k, c in core.items() if c.get('it')}
    return core, eu_map, it_map

def _merge_extra_acts(core):
    """Merge manually-supplied articles (extra_acts.json) into the core acts — for provisions
    cited by the coordinated text but not yet in the source consolidato (e.g. art. 14.1 d.lgs.
    286, introduced by the same d.l. 100/2026). Makes those refs hoverable with the given text."""
    fp = os.path.join(HERE, 'extra_acts.json')
    if not os.path.exists(fp):
        return
    try:
        extra = json.load(open(fp, encoding='utf-8'))
    except Exception as e:
        print('  ATTENZIONE: extra_acts.json non valido (%s) — ignorato.' % e); return
    for akey, arts in extra.items():
        if akey.startswith('_') or akey not in core:
            continue
        c = core[akey]
        for lab, info in arts.items():
            frags = [[base(num), '<div class="comma"><span class="cnum">%s.</span> %s</div>'
                      % (html.escape(num), html.escape(txt))] for num, txt in info.get('commi', [])]
            heading = info.get('heading', '')
            if info.get('source'):
                frags.insert(0, [None, '<div class="comma" style="color:var(--amd-ins)">[%s]</div>' % html.escape(info['source'])])
            c['articles'][lab] = dict(label='Art. %s' % lab, heading=heading, anchor='art_%s' % lab, frags=frags)
            c['artset'].add(lab)

# --- grammar regexes (NUM/ORD are defined at module top) -----------------------
RE_ART_HEAD = re.compile(r'articol([oi])\s+(?=\d|da\s)', re.I)
# article number, with optional ordinal AND optional decimal (the inserted arts use
# both, e.g. "28-bis.1" / "28-bis.2", sitting between 28-bis and 28-ter)
RE_ANUM     = re.compile(r'(\d{1,3})((?:[-\s](?:%s))?(?:\.\d+)?)\b' % ORD, re.I)
RE_LIST_SEP = re.compile(r'(?:\s*,\s*|\s+(?:e|ed|o|od)\s+)(?=\d)', re.I)
# list separator incl. the "comma + e/ed" combo «13, e 14» (Oxford-ish), used to rejoin an
# article list after a per-item qualifier («articoli 13, comma 5.2, e 14»)
RE_LIST_SEP_E = re.compile(r'(?:\s*,\s*(?:e|ed|o|od|nonch[ée])\s+|\s*,\s*|\s+(?:e|ed|o|od|nonch[ée])\s+)(?=\d)', re.I)
RE_RANGE    = re.compile(r'da\s+(\d{1,3})\s+a\s+(\d{1,3})\b', re.I)
RE_CHAIN    = re.compile(
    r'\s*[,;]?\s*(?:e|ed|o|od|nonch[ée])?\s*(?:di\s+cui\s+)?'
    r'(?:l[\'’]|all[\'’]|dell[\'’]|dall[\'’]|sull[\'’]|nell[\'’]|agli|degli|negli|gli)?\s*(?=articol[oi]\s)', re.I)
RE_PAR_CAP   = re.compile(r'\s*,?\s*paragraf[oi]\s+(\d{1,3})', re.I)
RE_COMMA_CAP = re.compile(r'\s*,?\s*comm[ai]\s+(\d{1,3}(?:\.\d+)?(?:-(?:%s))?)' % ORD, re.I)
RE_PAR_Q     = re.compile(r'\s*,?\s*paragraf[oi]\s+\d{1,3}(?:\s*(?:,|e|ed|o|od)\s*\d{1,3})*', re.I)
# il comma italiano può avere numerazione decimale ("comma 1.1") e suffissi ("1-bis")
RE_COMMA_Q   = re.compile(r'\s*,?\s*comm[ai]\s+\d{1,3}(?:\.\d+)?(?:-(?:%s))?'
                          r'(?:\s*(?:,|e|ed|o|od)\s*\d{1,3}(?:\.\d+)?(?:-(?:%s))?)*' % (ORD, ORD), re.I)
LETT_STOP = r'(?:e|ed|o|od|a|ai|al|di|da|de|del|in|su|si|se|la|le|lo|il|un|ne|tra|fra|per|che|chi|cui|non)'
LETT = r'(?:[a-z]{1,2}(?:[\s-](?:%s))?\)|(?!%s\b)[a-z]{1,2}\b)' % (ORD, LETT_STOP)  # (?:%s) raggruppato: senza, «[\s-]» legava solo a 'bis' e «lettera c-quater)» consumava solo «c»
RE_LETT_Q = re.compile(
    r'\s*,?\s*letter[ae]\s+(?:da\s+)?%s(?:\s+a\s+%s)?'
    r'(?:(?:\s*,\s*|\s+(?:e|ed|o|od)\s+)(?:da\s+)?%s(?:\s+a\s+%s)?)*' % (LETT, LETT, LETT, LETT), re.I)
# continuazione di paragrafo/comma dopo gli altri qualificatori: «…, lettere a)…j), e paragrafo 3, …»
RE_CONT_PARCOMMA = re.compile(
    r'\s*,?\s*(?:e|ed|o|od|nonch[ée])\s+(?:il\s+|al\s+|nel\s+|all[\'’]\s*)?'
    r'(?:paragraf[oi]|comm[ai])\s+\d{1,3}(?:-(?:%s))?' % ORD, re.I)

ITKIND = r'(decreto\s+legislativo|decreto-legge|decreto\s+del\s+Presidente\s+della\s+Repubblica|legge|regio\s+decreto)'
RE_EU = re.compile(
    r'(regolament[oi]|direttiv[ae]|decision[ei])((?:\s+(?:di\s+esecuzione|delegat[oa]|quadro))?)'
    r'(?:\s*\(?(UE,?\s*Euratom|UE|CE|CEE|EU)\)?)?(?:\s*|\s+)((?:n\.\s*)?)(\d{1,4})/(\d{1,4})'
    r'((?:/(?:CE|CEE|UE|GAI|PESC|Euratom))?)', re.I)
RE_IT_FULL  = re.compile(ITKIND + r'\s+(\d{1,2})°?\s+(%s)\s+(\d{4}),?\s*n\.?\s*(\d+)' % '|'.join(MONTHS), re.I)
RE_IT_SHORT = re.compile(ITKIND + r'\s+n\.?\s*(\d+)\s+del\s+(\d{4})', re.I)
RE_IT_NNUM  = re.compile(ITKIND + r'\s+n\.?\s*(\d+)\b', re.I)
RE_DPR_ABBR = re.compile(r'd\.?\s*[Pp]\.?\s*R\.?\s*(\d{1,2})°?\s+(%s)\s+(\d{4}),?\s*n\.?\s*(\d+)' % '|'.join(MONTHS), re.I)
# An "amending article" (rubric "Modifiche a…"/"Disposizioni di aggiornamento") novellates
# ANOTHER act; its bare "articolo N" refs belong to that act, not to the host (d.lgs. 142).
RE_AMEND_RUBRICA = re.compile(r'\s*(?:Modific|Disposizioni\s+di\s+aggiornament)', re.I)

RE_TAIL_ACT = re.compile(
    r'\s*,?\s*(?:del|dello|della|dell[\'’]|dei|degli|delle|di\s+cui\s+al(?:la)?)\s+'
    # filler opzionale: «del TESTO UNICO di cui al decreto…», «del CAPO III della legge…»
    r'(?:(?:medesim[oa]|stess[oa]|citat[oa]|predett[oa]|suddett[oa])\s+(?=testo\s+unico))?(?:testo\s+unico\s+(?:d[ei]lle\s+disposizioni\s+[^,;.)]{0,150}?(?:,\s*|\s+))?di\s+cui\s+al(?:la)?\s+|cap[oi]\s+[IVXLC]+\s+del(?:la)?\s+|part[ei]\s+[IVXLC]+\s+del(?:la)?\s+)?'
    r'(?=(?:regolament|direttiv|decision|decreto|legge|regio\s+decreto|d\.?\s*[Pp]\.?\s*R))', re.I)
RE_TAIL_SELF  = re.compile(r'\s*,?\s*(?:del|dello|della|dell[\'’])\s+presente\s+(decreto|regolamento|articolo)\b', re.I)
RE_TAIL_ANAPH = re.compile(
    r'\s*,?\s*(?:del(?:la)?|dell[\'’]|dello|dei|degli|delle|di\s+tal[ei]|di\s+dett[oa])\s+'
    r'(?:medesim[oa]|stess[oa]|citat[oa]|predett[oa]|suddett[oa]|dett[oa]|tal[ei])\s+'
    r'(regolament|direttiv|decision|decreto|legge)\w*', re.I)
RE_TAIL_CODICE = re.compile(r'\s*,?\s*del\s+codice\s+(di\s+procedura\s+penale|di\s+procedura\s+civile|penale|civile)', re.I)
RE_TAIL_SKIP   = re.compile(
    r'\s*,?\s*(?:del|della|dell[\'’]|dello|della\s+predett[ao]|del\s+predett[ao]|di\s+tal[ei]|di\s+dett[oa])\s+'
    r'(?:protocoll|convenzion|accord|statut|trattato\s+di|Carta\b)', re.I)

MASTER = re.compile(
    r'articol[oi]\s+(?=\d|da\s)|regolament[oi]\b|direttiv[ae]\b|decision[ei]\b|'
    r'decreto\s+legislativo\b|decreto-legge\b|decreto\s+del\s+Presidente\b|'
    r'\blegge\s+(?=\d|n\.)|regio\s+decreto\b|d\.?\s*[Pp]\.?\s*R', re.I)


def _itkind_urn(word):
    return IT_TYPE.get(re.sub(r'\s+', ' ', word.strip().lower()))


class Linker:
    """Stateful, per-article cross-reference resolver (see header above)."""

    def __init__(self, self_labels, core, eu_map, it_map, overrides):
        self.self_labels = self_labels
        self.core = core
        self.eu_map = eu_map
        self.it_map = it_map
        self.overrides = overrides or []
        self.ov_hits = set()                  # indices of override rules that fired (≥1×)
        self.cited = {}                       # extlocal key -> set(article) actually linked
        self.unresolved = []                  # (art, text-window) left plain on purpose
        self.begin_article('?')

    # -- context lifecycle --
    def begin_article(self, label, art=None):
        self.cur_art = label
        self.last_act = None                  # (kind, key_or_url, label); kind in self/extlocal/ext
        self.last_art = None
        self.amend_act = self._detect_amend_act(art) if art else None  # target of an "amending article"
        self.scope('?')

    def _detect_amend_act(self, art):
        """For an amending article (rubric 'Modifiche a…' / 'Disposizioni di aggiornamento'),
        return the target act of its bare article refs: ('extlocal', key) | ('ext', url) | ('self',)."""
        if not RE_AMEND_RUBRICA.match(art.get('rubrica', '')):
            return None
        head = next((''.join(t for k, t, _ in c.get('segments', []) if k != 'del') or c.get('text', '')
                     for c in art.get('commi', [])), '')
        for src in (art.get('rubrica', ''), head[:220]):       # first act named in rubric / comma-1 opening
            for m in MASTER.finditer(src):
                if m.group(0).lower().startswith('articol'):
                    continue
                _, info = self._parse_act(src, m.start())
                if info:
                    return self._act_target(info)
        return None

    def scope(self, scope_id):
        self.cur_scope = scope_id
        self._occ = {}

    # -- public entry --
    def link_spans(self, text):
        """Resolve cross-references in `text`; return chosen non-overlapping (start,end,html)."""
        emits = []
        pos = 0
        while True:
            m = MASTER.search(text, pos)
            if not m:
                break
            s = m.start()
            if m.group(0).lower().startswith('articol'):
                end, es = self._chain(text, s)
            else:
                end, es = self._standalone(text, s)
            for e in es:
                if e:
                    emits.append(e)
            pos = max(end, m.end())
        emits.sort(key=lambda e: (e[0], -(e[1] - e[0])))
        chosen, last = [], -1               # drop overlaps: keep earliest, then longest
        for e in emits:
            if e[0] >= last:
                chosen.append(e); last = e[1]
        return chosen

    def link(self, text):
        out, p = [], 0
        for s, e, h in self.link_spans(text):
            out.append(html.escape(text[p:s])); out.append(h); p = e
        out.append(html.escape(text[p:]))
        return ''.join(out)

    # -- article number + qualifier groups --
    def _group(self, text, start):
        m = RE_ART_HEAD.match(text, start)
        if not m:
            return None
        plural = m.group(1).lower() == 'i'
        i = m.end()
        items = []                            # (num, suffix, numstart, numend)
        while True:
            mr = RE_RANGE.match(text, i)
            if mr and plural:
                items.append((int(mr.group(1)), None, mr.start(1), mr.start(1) + len(mr.group(1))))
                items.append((int(mr.group(2)), None, mr.start(2), mr.start(2) + len(mr.group(2))))
                i = mr.end()
            else:
                mn = RE_ANUM.match(text, i)
                if not mn:
                    break
                suff = mn.group(2)
                items.append((int(mn.group(1)), re.sub(r'^[\s-]+', '', suff) if suff else None,
                              mn.start(1), mn.end()))
                i = mn.end()
            if not plural:
                break
            nxt = self._next_in_list(text, i)
            if nxt is None:
                break
            i = nxt
        if not items:
            return None
        single = (not plural) and len(items) == 1
        par = None
        if single:
            mp = RE_PAR_CAP.match(text, i) or RE_COMMA_CAP.match(text, i)
            if mp:
                par = mp.group(1)
        i = self._consume_quals(text, i)
        return dict(start=start, end=i, items=items, plural=plural, single=single, par=par)

    def _next_in_list(self, text, i):
        """Position of the next article number in a plural list, or None. Accepts a plain
        separator («13, 14» / «13 e 14») OR a per-item comma/paragrafo qualifier followed by a
        separator («articoli 13, comma 5.2, e 14» / «articoli 5, paragrafo 3, e 7»). The greedy
        comma-qualifier correctly keeps a real comma list with the article («art. 13 commi 2-ter,
        5, 13 e 14») — only a following number reached via a separator becomes a new article."""
        m = RE_LIST_SEP_E.match(text, i)
        if m:
            return m.end()
        mq = RE_COMMA_Q.match(text, i) or RE_PAR_Q.match(text, i)
        if mq:
            m2 = RE_LIST_SEP_E.match(text, mq.end())
            if m2:
                return m2.end()
        return None

    def _consume_quals(self, text, i):
        while True:
            for rx in (RE_PAR_Q, RE_COMMA_Q, RE_LETT_Q, RE_CONT_PARCOMMA):
                m = rx.match(text, i)
                if m and m.end() > i:
                    i = m.end()
                    break
            else:
                return i

    # -- tail: which act do the cited articles belong to? --
    def _tail(self, text, j):
        m = RE_TAIL_SELF.match(text, j)
        if m:
            return dict(kind='self', end=m.end(), act_emits=[])
        m = RE_TAIL_SKIP.match(text, j)
        if m:
            return dict(kind='skip', end=j, act_emits=[])
        m = RE_TAIL_CODICE.match(text, j)
        if m:
            urn = CODICI.get(m.group(1).lower())
            url = normattiva_url(*urn) if urn else None
            return dict(kind='ext', url=url, end=m.end(), act_emits=[])
        m = RE_TAIL_ACT.match(text, j)
        if m:
            a_end, info = self._parse_act(text, m.end())
            if info:
                tgt = self._act_target(info)
                self._set_last_act(tgt)
                ae = self._act_name_link(text, info, tgt)
                if tgt[0] == 'extlocal':
                    return dict(kind='extlocal', key=tgt[1], end=a_end, act_emits=[ae] if ae else [])
                if tgt[0] == 'ext':
                    return dict(kind='ext', url=tgt[1], end=a_end, act_emits=[ae] if ae else [])
                return dict(kind='self', end=a_end, act_emits=[])     # "del presente ..." spelt out
            return dict(kind='none', end=j, act_emits=[])
        m = RE_TAIL_ANAPH.match(text, j)
        if m:
            return dict(kind='anaphora', end=m.end(), act_emits=[])
        return dict(kind='none', end=j, act_emits=[])

    def _chain(self, text, start):
        groups, p = [], start
        while True:
            g = self._group(text, p)
            if not g:
                break
            groups.append(g)
            mc = RE_CHAIN.match(text, g['end'])
            if not mc:
                break
            p = mc.end()
        if not groups:
            return start, []
        j = groups[-1]['end']
        tail = self._tail(text, j)
        end = max(j, tail['end'])
        emits = list(tail.get('act_emits', []))
        kind = tail['kind']

        if kind == 'skip':
            return end, emits
        if kind == 'extlocal':
            for g in groups:
                self._emit_group(g, ('extlocal', tail['key']), emits, text)
            return end, emits
        if kind == 'ext':
            for g in groups:
                self._emit_group(g, ('ext', tail['url']), emits, text)
            self.last_art = None
            return end, emits
        if kind == 'anaphora':
            la = self.last_act
            if not la:
                self.unresolved.append((self.cur_art, text[max(0, start - 30):end + 20]))
                return end, emits
            base_t = ('self',) if la[0] == 'self' else (la[0], la[1])
            for g in groups:
                self._emit_group(g, base_t, emits, text)
            return end, emits

        # kind in ('self', 'none') -> the host decree (d.lgs. 142), unless inside an amending article
        if kind == 'none':
            if self.amend_act is not None:        # amending article: bare refs -> the modified act
                at = self.amend_act
                if at[0] == 'extlocal':
                    for g in groups:
                        self._emit_group(g, ('extlocal', at[1]), emits, text)
                    return end, emits
                if at[0] == 'ext':                # non-core target -> don't mislink to self; leave plain
                    self.unresolved.append((self.cur_art, text[max(0, groups[0]['start'] - 30):end + 30]))
                    return end, emits
                # at[0] == 'self' -> fall through to self emit below
            else:
                missing = [self._lab(n, suff) for g in groups for (n, suff, s0, e0) in g['items']
                           if self._lab(n, suff) not in self.self_labels]
                if missing:                   # bare chain, numbers foreign to d.lgs. 142 -> don't guess
                    self.unresolved.append((self.cur_art, text[max(0, groups[0]['start'] - 30):end + 30]))
                    return end, emits
        for g in groups:
            self._emit_group(g, ('self',), emits, text)
        return end, emits

    # -- standalone act mention (sets context; also links the act name) --
    def _standalone(self, text, s):
        a_end, info = self._parse_act(text, s)
        if not info:
            return s, []
        tgt = self._act_target(info)
        self._set_last_act(tgt)
        ae = self._act_name_link(text, info, tgt)
        return a_end, [ae] if ae else []

    # -- act recognition: EU reg/dir/dec, IT decreto/legge, DPR --
    def _parse_act(self, text, pos):
        m = RE_EU.match(text, pos)
        if m:
            word, _var, paren, nmark, n1, n2, suffix = m.groups()
            if paren or suffix or nmark.strip():        # a bare "decisione 2/3" is too ambiguous
                a, b = int(n1), int(n2)
                year, num = (a, b) if 1950 <= a <= 2099 else (b, a)
                return m.end(), dict(scheme='eu', word=word, year=year, num=num, span=(m.start(), m.end()))
        m = RE_IT_FULL.match(text, pos)
        if m:
            urn = _itkind_urn(m.group(1))
            date = '%s-%s-%02d' % (m.group(4), MONTHS[m.group(3).lower()], int(m.group(2)))
            return m.end(), dict(scheme='it', urn=urn, num=m.group(5), date=date, span=(m.start(), m.end()))
        m = RE_DPR_ABBR.match(text, pos)
        if m:
            date = '%s-%s-%02d' % (m.group(3), MONTHS[m.group(2).lower()], int(m.group(1)))
            return m.end(), dict(scheme='it', urn='decreto.del.presidente.della.repubblica',
                                 num=m.group(4), date=date, span=(m.start(), m.end()))
        m = RE_IT_SHORT.match(text, pos)
        if m:
            urn = _itkind_urn(m.group(1)); num = m.group(2)
            date = KNOWN_DATE.get((urn, num))
            return m.end(), dict(scheme='it', urn=urn, num=num, date=date, span=(m.start(), m.end()))
        m = RE_IT_NNUM.match(text, pos)
        if m:
            urn = _itkind_urn(m.group(1)); num = m.group(2)
            date = KNOWN_DATE.get((urn, num))
            return m.end(), dict(scheme='it', urn=urn, num=num, date=date, span=(m.start(), m.end()))
        return pos, None

    def _act_target(self, info):
        if info['scheme'] == 'eu':
            key = self.eu_map.get((info['year'], info['num']))
            if key:
                return ('extlocal', key)
            return ('ext', eli_url('regolamento' if info['word'].lower().startswith('reg')
                                   else 'direttiva' if info['word'].lower().startswith('dir')
                                   else 'decision', info['year'], info['num']))
        if (info.get('urn'), info.get('num')) == SELF_IT:    # "del decreto legislativo 18 agosto 2015, n. 142" -> self
            return ('self',)
        key = self.it_map.get((info['urn'], info['num']))
        if key and info.get('date') and self.core[key].get('date') and info['date'] != self.core[key]['date']:
            key = None                      # stesso tipo e numero, altro anno (es. d.lgs. n. 115 non del 2026)
        if key:
            return ('extlocal', key)
        if info.get('date'):
            return ('ext', normattiva_url(info['urn'], info['num'], info['date']))
        return ('ext', 'https://www.normattiva.it/ricerca/semplice?numeroProvvedimento=%s' % info['num'])

    def _set_last_act(self, tgt):
        if tgt[0] == 'extlocal':
            self.last_act = ('extlocal', tgt[1], self.core[tgt[1]]['label'])
        elif tgt[0] == 'ext':
            self.last_act = ('ext', tgt[1], None)
        else:
            self.last_act = ('self', SELF_KEY, None)

    def _act_name_link(self, text, info, tgt):
        s, e = info['span']
        url = self.core[tgt[1]]['url'] if tgt[0] == 'extlocal' else (tgt[1] if tgt[0] == 'ext' else None)
        if not url:
            return None
        return (s, e, '<a class="lawlink ext" href="%s" target="_blank" rel="noopener">%s</a>'
                % (url, html.escape(text[s:e])))

    # -- emit one article group toward a target --
    def _emit_group(self, g, base_target, emits, text):
        for (n, suff, s0, e0) in g['items']:
            art = self._lab(n, suff)
            span_s = g['start'] if g['single'] else s0
            par = g['par'] if g['single'] else None
            kind = base_target[0]
            if kind == 'self':
                if art in self.self_labels:
                    emits.append(self._emit(span_s, e0, text, ('self', art, par)))
                    self.last_art = ('self', SELF_KEY, art)
            elif kind == 'extlocal':
                key = base_target[1]
                if art in self.core[key]['artset']:
                    emits.append(self._emit(span_s, e0, text, ('extlocal', key, art, par)))
                    self.cited.setdefault(key, set()).add(art)
                    self.last_art = ('extlocal', key, art)
                else:                          # article absent from local data -> link to act page
                    emits.append(self._emit(span_s, e0, text, ('ext', self.core[key]['url'])))
            else:                              # ext
                emits.append(self._emit(span_s, e0, text, ('ext', base_target[1])))

    # -- override hook + final link rendering --
    def _emit(self, s, e, text, target):
        label = re.sub(r'\s+', ' ', text[s:e]).strip()
        self._occ[label] = self._occ.get(label, 0) + 1
        ov = self._match_override(label, self._occ[label])
        if ov is not None:
            if ov.get('unlink'):
                return None
            target = self._override_target(ov['target'])
            if target is None:
                return None
        return self._render(s, e, text, target)

    def _match_override(self, label, nth):
        for idx, r in enumerate(self.overrides):
            if r.get('art') != self.cur_art:
                continue
            if 'where' in r and r['where'] != self.cur_scope:
                continue
            if re.sub(r'\s+', ' ', r['text']).strip() != label:
                continue
            if r.get('nth', 1) != nth:
                continue
            self.ov_hits.add(idx)
            return r
        return None

    def _override_target(self, t):
        akey = t.get('act')
        if akey == SELF_KEY:
            return ('self', str(t['art']), str(t['par']) if t.get('par') else None)
        if akey in self.core:
            return ('extlocal', akey, str(t['art']), str(t['par']) if t.get('par') else None)
        if t.get('href'):
            return ('ext', t['href'])
        return None

    def _render(self, s, e, text, target):
        disp = html.escape(text[s:e])
        kind = target[0]
        if kind == 'self':
            art = target[1]; par = target[2] if len(target) > 2 else None
            pa = ' data-par="%s"' % par if par else ''
            return (s, e, '<a class="xref" data-act="%s" data-art="%s"%s href="#art_%s">%s</a>'
                    % (SELF_KEY, art, pa, art, disp))
        if kind == 'extlocal':
            key, art = target[1], target[2]; par = target[3] if len(target) > 3 else None
            self.cited.setdefault(key, set()).add(art)
            core = self.core[key]
            href = core['url']
            if core.get('deep') and art in core['articles']:        # Pact act -> deep-link to its page
                href = '%s#%s' % (core['url'], core['articles'][art]['anchor'])
            pa = ' data-par="%s"' % par if par else ''
            return (s, e, '<a class="xref" data-act="%s" data-art="%s"%s href="%s" target="_blank" rel="noopener">%s</a>'
                    % (key, art, pa, href, disp))
        return (s, e, '<a class="lawlink ext" href="%s" target="_blank" rel="noopener">%s</a>'
                % (target[1], disp))

    @staticmethod
    def _lab(n, suff):
        if not suff:
            return str(n)
        return ('%d%s' if suff.startswith('.') else '%d-%s') % (n, suff)  # 28+bis.1 -> 28-bis.1; 28+.1 -> 28.1


# Normattiva update-note reference markers — '(8)', '((22))' — point to the
# "AGGIORNAMENTO (N)" history notes, NOT part of the legal text. Stripped at display
# time only (the parse/amendment model keeps them, so amendment matching is untouched).
# NB: distinct from the ((…)) brackets that wrap actual amended TEXT, which are kept.
# A lettered enumeration item ("…per: a) …; b) …") gets its own line. Triggers on a
# ':'/';'/'.' immediately followed by a letter-marker (items can end with any of the
# three), so citations ('lettera a)', list ', b)') stay inline. Operates on rendered
# HTML; markers are always plain top-level text. (Verified: no abbreviation false-positives.)
# Group 2 tolerates intervening tags (e.g. the «.» can be in a normal segment and the
# «b-quater)» marker inside the following <ins>): break right before the marker.
# «»» (virgoletta di chiusura) è innesco a sua volta: negli articoli di novella l'item può
# finire con la citazione chiusa senza punto/punto e virgola («…completamente.» l) all'art. 12…»,
# d.lgs. 142/2015 art. 25 co. 2 e 3-bis) e senza questo la lettera restava in linea.
LETT_BREAK = re.compile(r'([:;.»])(\s*(?:<[^>]+>\s*)*)((?:[a-z]{1,2})(?:-(?:%s))?\))(\s|(?=<))' % ORD)

def strip_notes(h):
    """Drop Normattiva display artifacts: update-note markers '(8)'/'((22))' (refs to the
    AGGIORNAMENTO notes, not legal text) AND the '((…))' brackets that mark prior-amendment
    spans — the bracketed TEXT is kept, only the doubled parentheses are removed."""
    # Il marcatore può avere un suffisso letterale: «(2A)» in art. 19, co. 2, T.U. 286/98
    # rimanda ad «AGGIORNAMENTO (2A)» (C. cost. 376/2000). Se non lo si toglie resta
    # in mezzo al testo E, stando fra il «.» e «d-bis)», impedisce a LETT_BREAK di
    # mandare la lettera a capo.
    h = re.sub(r'\s?\(\(\s*\d{1,3}[A-Z]?\s*\)\)', '', h)   # ((22)) / ((2A))  note-in-brackets
    h = re.sub(r'\s?\((\d{1,3}[A-Z]?)\)', '', h)            # (8) / (2A)      note marker
    return h.replace('((', '').replace('))', '')      # unwrap the amendment brackets

# Refuso Normattiva: marcatore incollato alla parola («e)godono» art. 19 co. 2, «d)assunzione»
# art. 27-bis T.U. 286/98). Senza lo spazio il gruppo 4 di LETT_BREAK non aggancia e la
# lettera resta in linea: si reinserisce lo spazio prima di applicare LETT_BREAK.
LETT_GLUED = re.compile(r'([:;.»]\s*(?:<[^>]+>\s*)*(?:[a-z]{1,2})(?:-(?:%s))?\))(?=[a-zàèéìòù])' % ORD)

def break_letters(body):
    body = LETT_GLUED.sub(r'\1 ', body)
    return LETT_BREAK.sub(r'\1\2<br><span class="lett-n">\3</span>\4', body)

def link_text(text, lk):
    return strip_notes(lk.link(text))

# ---------------------------------------------------------------- render
def _ins_open(src):
    return '<ins class="amd-ins" data-amd="%s" title="%s">' % (
        html.escape(src or ''), html.escape('Inserito/sostituito da ' + src) if src else '')

_A_ONE = re.compile(r'^(<a\s[^>]*>)([^<]*)</a>$')   # a single link with plain text

def render_segments(segs, lk, plain=False):
    """Render tracked-changes segments. Cross-references are resolved on the FULL new
    (normal+ins) text of the unit — so a reference whose pieces straddle a deletion still
    links correctly (e.g. «28-bis» kept + «.1» inserted with «, comma 2-bis» struck between
    → links to art. 28-bis.1). Deleted text is then interleaved at its position, struck.
    A link that straddles kinds (part kept, part inserted) or has a deletion inside is
    split into same-href pieces, each wrapped by its own kind, with the deletion at its
    real position: so kept+del reads as the previous text and kept+ins as the new one
    (needed by the Vigente/Previgente views of the site)."""
    parts, ranges, dels, pos = [], [], [], 0    # ranges: (start,end,kind,src) over `full`
    for k, t, s in segs:
        if k == 'del':
            if not plain:
                dels.append([pos, t, s])         # offset in `full` where the struck text sat
            continue
        parts.append(t); ranges.append((pos, pos + len(t), k, s)); pos += len(t)
    full = ''.join(parts)
    spans = {sp[0]: sp for sp in lk.link_spans(full)}
    span_starts = sorted(spans)
    del_offs = sorted({d[0] for d in dels})
    def at(p):
        for a, b, k, s in ranges:
            if a <= p < b:
                return k, s
        return 'normal', None
    res, cur = [], [None, None]                  # cur = [kind, src] of the open wrapper
    def set_kind(k, s):
        if k != cur[0] or (k == 'ins' and s != cur[1]):
            if cur[0] == 'ins':
                res.append('</ins>')
            if k == 'ins':
                res.append(_ins_open(s))
            cur[0], cur[1] = k, s
    def flush_dels(upto):
        while dels and dels[0][0] <= upto:
            _, dt, ds = dels.pop(0)
            if cur[0] == 'ins':                  # a <del> must not sit inside <ins>
                res.append('</ins>'); cur[0] = cur[1] = None
            t = html.escape('Soppresso/sostituito da ' + ds) if ds else ''
            res.append('<del class="amd-del" data-amd="%s" title="%s">%s</del>'
                       % (html.escape(ds or ''), t, lk.link(dt)))
    p, L = 0, len(full)
    while p < L:
        flush_dels(p)
        if p in spans:
            s_, e_, h_ = spans[p]
            cuts = sorted({b for a, b, _, _ in ranges if s_ < b < e_ and at(b) != at(b - 1)}
                          | {o for o in del_offs if s_ < o < e_})
            m_ = _A_ONE.match(h_) if cuts else None
            if m_ and html.unescape(m_.group(2)) == full[s_:e_]:
                pts = [s_] + cuts + [e_]
                for x, y in zip(pts, pts[1:]):
                    flush_dels(x)
                    k, s = at(x); set_kind(k, s)
                    res.append(m_.group(1) + html.escape(full[x:y]) + '</a>')
            else:
                if cuts:
                    print('  ATTENZIONE: rinvio a cavallo di una novella non divisibile:', full[s_:e_])
                k, s = at(p); set_kind(k, s); res.append(h_)
            p = e_
        else:
            nb = min([L] + [x for x in span_starts if x > p]
                     + [b for a, b, _, _ in ranges if b > p]
                     + [o for o in del_offs if o > p])
            k, s = at(p); set_kind(k, s); res.append(html.escape(full[p:nb])); p = nb
    flush_dels(L)
    if cur[0] == 'ins':
        res.append('</ins>')
    return strip_notes(''.join(res))

def render_comma(art_label, c, lk, plain=False):
    num = c['num']; nk = c.get('numkind', 'keep')
    if c.get('abrogato'):
        numh = '<del class="amd-del">%s.</del>' % num
    elif nk == 'ins':
        numh = '<ins class="amd-ins">%s.</ins>' % num
    else:
        numh = '%s.' % num
    lk.scope('com%s' % num)
    body = break_letters(render_segments(c['segments'], lk, plain=plain))
    return '<div class="comma" id="art_%s-com%s"><span class="cnum">%s</span> %s</div>' % (
        art_label, num, numh, body)

def render_article(a, lk):
    lk.begin_article(a['label'], a)
    cls = 'eli-subdivision art' + (' art-new' if a.get('inserted') else '')
    head_num = ('<ins class="amd-ins">Art. %s</ins>' % a['label']) if a.get('inserted') else ('Art. %s' % a['label'])
    lk.scope('rubrica')
    rub = render_segments(a.get('rubrica_seg', [('normal', a.get('rubrica', ''), None)]), lk)
    parts = ['<div class="%s" id="art_%s">' % (cls, a['label']),
             '<p class="oj-ti-art">%s</p>' % head_num,
             '<div class="eli-title"><p class="oj-sti-art">%s</p></div>' % rub]
    if a.get('preamble'):
        lk.scope('preamble')
        parts.append('<div class="preambolo">%s</div>' % link_text(a['preamble'], lk))
    for c in a['commi']:
        parts.append(render_comma(a['label'], c, lk))
    if not a['commi'] and a.get('abrogated'):
        parts.append('<div class="comma abrog">%s</div>' % html.escape(a['rubrica']))
    parts.append('</div>')
    return '\n'.join(parts)

def get_chapters():
    import xml.etree.ElementTree as ET
    p = os.path.join(HERE, '..', 'D.Lgs_142-2015_consolidato_vigente_2025-05-24.akn.xml')
    NS = '{http://docs.oasis-open.org/legaldocml/ns/akn/3.0}'
    root = ET.parse(p).getroot()
    label2capo = {}
    capi = []
    for ch in root.iter(NS + 'chapter'):
        nn = ch.find(NS + 'num'); hh = ch.find(NS + 'heading')
        num = norm_ws(''.join(nn.itertext())) if nn is not None else ''
        head = norm_ws(''.join(hh.itertext())) if hh is not None else ''
        labs = []
        for a in ch.iter(NS + 'article'):
            n = a.find(NS + 'num')
            lab = re.search(r'(%s(?:\.\d+)?)' % NUM, ''.join(n.itertext())).group(1) if n is not None and re.search(r'\d', ''.join(n.itertext())) else a.get('eId', '').replace('art_', '')
            labs.append(lab); label2capo[lab] = len(capi)
        capi.append((num, head, labs))
    return capi, label2capo

PAGE_TMPL = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>D.Lgs. 142/2015 — testo coordinato con l'art. 10 d.l. 100/2026</title>
<link rel="stylesheet" href="assets/style.css">
<link rel="stylesheet" href="assets/amend.css">
</head>
<body data-act="dlgs-2015-142">
<header class="topbar">
  <a class="home" href="../index.html">&#8962; Patto UE</a> <a class="home-here" href="#top">D.Lgs. 142/2015</a>
  <button id="toc-toggle">Sommario</button>
  <span class="topttl">Accoglienza dei richiedenti protezione internazionale — <b>testo coordinato</b> con le modifiche dell'art. 10 d.l. 12 giugno 2026, n. 100</span>
</header>
<div class="amd-banner">Testo vigente al 24 maggio 2025 <b>coordinato</b> con le modificazioni introdotte dall'<b>art. 10 del d.l. 12 giugno 2026, n. 100</b> (convertito senza modificazioni dalla l. 7 agosto 2026, n. 145), di recepimento della direttiva (UE) 2024/1346. <span class="amd-legenda">Le parti <ins class="amd-ins">inserite o sostituite</ins> e <del class="amd-del">soppresse</del> dall'art. 10 sono evidenziate; passa il mouse per la fonte.</span> I rinvii al d.lgs. 25/2008 aprono il relativo testo coordinato interattivo. È inoltre coordinata, con la stessa evidenziazione, la sostituzione dell'art. 17, comma 2, disposta dall'art. 11, comma 1, del <b>d.lgs. 12 giugno 2026, n. 115</b> (GU n. 150 del 1/7/2026, in vigore dal 16/7/2026, attuazione della direttiva (UE) 2024/1712 sulla tratta di esseri umani).</div>
<div class="layout">
<nav class="toc" id="toc"><div class="toc-title">D.Lgs. 18 agosto 2015, n. 142</div>
{toc}
</nav>
<main class="doc" id="top">
<div class="eli-main-title"><p class="oj-doc-ti">DECRETO LEGISLATIVO 18 agosto 2015, n. 142</p>
<p class="oj-doc-ti sub">Attuazione delle direttive 2013/33/UE e 2013/32/UE — accoglienza dei richiedenti e procedure di protezione internazionale</p>
<p class="oj-doc-ti note">Testo coordinato (non ufficiale) con le modifiche dell'art. 10 d.l. 12 giugno 2026, n. 100</p></div>
{body}
<p class="disclaimer">Testo coordinato non ufficiale a fini di studio. Fonte del testo vigente: Normattiva (consolidato al 24/5/2025). Modifiche: art. 10 d.l. 12/6/2026 n. 100 (G.U. 26G00119), convertito senza modificazioni dalla l. 7/8/2026 n. 145; art. 11 d.lgs. 12/6/2026 n. 115 (G.U. 26G00130). Fa fede unicamente il testo pubblicato nella Gazzetta Ufficiale.</p>
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

def load_overrides():
    fp = os.path.join(HERE, 'overrides.json')
    if not os.path.exists(fp):
        return []
    try:
        return json.load(open(fp, encoding='utf-8'))
    except Exception as e:
        print('  ATTENZIONE: overrides.json non valido (%s) — ignorato.' % e)
        return []

def plain_heading(a):
    """Article rubric as plain text (new text where the rubric was novellato), no links."""
    txt = ''.join(t for k, t, _ in a.get('rubrica_seg', [('normal', a.get('rubrica', ''), None)]) if k != 'del')
    return html.escape(re.sub(r'\s+', ' ', txt).strip())

def build_site(arts, rep):
    self_labels = {a['label'] for a in arts}
    core, eu_map, it_map = load_core_acts()
    lk = Linker(self_labels, core, eu_map, it_map, load_overrides())
    capi, label2capo = get_chapters()
    for a in arts:                                  # inserted arts inherit predecessor's capo
        if a['label'] not in label2capo:
            label2capo[a['label']] = None
    # TOC + body grouped by capo
    toc, body = [], []
    cur_capo = None
    for i, a in enumerate(arts):
        cp = label2capo.get(a['label'])
        if cp is None:                              # inherit from previous article
            cp = cur_capo
        if cp != cur_capo:
            cur_capo = cp
            if cp is not None and cp < len(capi):
                num, head, _ = capi[cp]
                toc.append('<div class="toc-capo">%s — %s</div>' % (html.escape(num), html.escape(head)))
                body.append('<h2 class="capo" id="capo_%d">%s — %s</h2>' % (cp, html.escape(num), html.escape(head)))
        _chg = (a.get('inserted')
                or any(s[0] in ('ins', 'del') for s in (a.get('rubrica_seg') or []))
                or any(c.get('numkind') == 'ins' or c.get('abrogato')
                       or any(s[0] in ('ins', 'del') for s in (c.get('segments') or []))
                       for c in a.get('commi', [])))
        flag = (' new' if a.get('inserted') else ' changed') if _chg else ''
        toc.append('<a class="toc-art%s" href="#art_%s"><span class="toc-n">%s</span><span class="toc-art-h">%s</span></a>'
                   % (flag, a['label'], html.escape(a['label']), plain_heading(a)))
        body.append(render_article(a, lk))
    page = PAGE_TMPL.replace('{toc}', '\n'.join(toc)).replace('{body}', '\n'.join(body))
    open(os.path.join(HERE, 'index.html'), 'w', encoding='utf-8').write(page)

    # data.js — d.lgs. 142 itself + the cited articles of the hoverable "core acts"
    acts = {SELF_KEY: {'label': 'D.Lgs. 18 agosto 2015, n. 142',
                       'short': 'D.Lgs. 142/2015', 'file': 'index.html', 'articles': {}}}
    for a in arts:
        lk.begin_article(a['label'], a)
        frags = [[base(c['num']), render_comma(a['label'], c, lk, plain=True)] for c in a['commi']]
        if not frags:                              # articolo abrogato / senza commi: niente hover vuoto
            note = plain_heading(a) or 'Articolo'
            frags = [[None, '<div class="comma abrog">%s</div>' % note]]
        acts[SELF_KEY]['articles'][a['label']] = {
            'label': 'Art. %s' % a['label'], 'heading': plain_heading(a),
            'anchor': 'art_%s' % a['label'], 'frags': frags}
    for key, used in sorted(lk.cited.items()):
        c = core[key]
        acts[key] = {'label': c['label'], 'short': c['short'], 'external': True,
                     'version': c['version'], 'eurlex': c['url'], 'file': c['url'],
                     'articles': {an: c['articles'][an] for an in sorted(used) if an in c['articles']}}
    with open(os.path.join(HERE, 'assets', 'data.js'), 'w', encoding='utf-8') as f:
        f.write('window.PACTO=' + json.dumps({'acts': acts}, ensure_ascii=False) + ';\n')

    open(os.path.join(HERE, 'assets', 'amend.css'), 'w', encoding='utf-8').write(AMEND_CSS)
    write_report(rep)
    return lk

AMEND_CSS = """/* tracked-changes + Italian-decree styling for d.lgs. 142/2015 */
:root{ --amd-ins:#c1121f; --amd-del:#8a8f98; }
.amd-banner{ background:#fff4f4; border:1px solid #f3c9c9; border-left:4px solid var(--amd-ins);
  color:#5b1416; font-family:var(--sans); font-size:12.5px; line-height:1.5; padding:10px 16px; margin:0; }
.amd-banner ins,.amd-banner del{ font-weight:600; }
ins.amd-ins{ color:var(--amd-ins); text-decoration:none; background:rgba(193,18,31,.07); border-radius:3px; padding:0 1px; }
ins.amd-ins:hover{ background:rgba(193,18,31,.15); cursor:help; }
del.amd-del{ color:var(--amd-del); text-decoration:line-through; }
del.amd-del:hover{ cursor:help; }
.art{ margin:1.4em 0; }
.preambolo{ font-style:italic; color:#444; margin:.4em 0; }
.comma{ margin:.45em 0; text-align:left; }
.comma .cnum{ font-weight:600; color:#1452a3; }
.comma.abrog{ color:var(--amd-del); }
h2.capo{ font-family:var(--sans); font-size:14px; letter-spacing:.04em; color:#0d3a76;
  border-bottom:1px solid var(--line); padding:.6em 0 .3em; margin:1.8em 0 .6em; }
.toc-capo{ font-family:var(--sans); font-size:10.5px; font-weight:700; color:#0d3a76;
  text-transform:uppercase; letter-spacing:.03em; margin:10px 6px 3px; }
.toc-art{ display:flex !important; gap:6px; align-items:baseline; }
.toc-art .toc-n{ flex:0 0 auto; min-width:2.6em; }
.toc-art-h{ font-size:11px; line-height:1.3; color:var(--muted);
  overflow:hidden; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; }
.toc-art:hover .toc-art-h,.toc-art.active .toc-art-h{ color:#3a3a3c; }
.toc-art.new{ border-left:2px solid var(--amd-ins); }
.toc-art.changed{ border-left:2px solid var(--amd-ins); }
.toc-art.changed .toc-n{ color:var(--amd-ins); }
.toc-art.new .toc-n{ color:var(--amd-ins); }
.comma .lett-n{ display:inline-block; margin-left:1.6em; color:#1452a3; font-weight:600; }
a.lawlink{ color:#1452a3; text-decoration:none; border-bottom:1px dashed rgba(20,82,163,.5); cursor:pointer; }
a.lawlink:hover{ background:#eef4ff; }
a.lawlink.ext::after{ content:"\\2197"; font-size:.7em; vertical-align:super; color:var(--muted); margin-left:1px; }
.topttl{ font-family:var(--sans); font-size:12px; color:#3a3a3c; margin-left:10px; }
.home-here{ font-family:var(--sans); font-size:13px; font-weight:600; color:#0d3a76; text-decoration:none; }
.panel-foot{ display:flex; align-items:center; justify-content:space-between; gap:12px; }
.panel-foot a{ margin-right:0; }
.panel-home{ font-size:13px; white-space:nowrap; }
.home-here::before{ content:"\\203A"; color:#8a8f98; font-weight:400; margin:0 6px; }
.oj-doc-ti.sub{ font-size:13px; font-weight:400; color:#444; }
.oj-doc-ti.note{ font-size:11.5px; color:var(--amd-ins); font-weight:600; }
"""

def write_report(rep):
    applied = sum(1 for r in rep.rows if r[2] == 'applicata')
    partial = sum(1 for r in rep.rows if r[2] == 'PARZIALE')
    failed  = sum(1 for r in rep.rows if r[2] == 'NON APPLICATA')
    lines = ['# Report applicazione modifiche — art. 10 d.l. 100/2026 su d.lgs. 142/2015', '',
             'Testo base: Normattiva, consolidato vigente al 24 maggio 2025 (fonte HTML completa '
             'da `caricaArticolo`, comprensiva delle modifiche che l\'export Akoma Ntoso poteva omettere).', '',
             'Art. 10 d.l. 12 giugno 2026, n. 100 recepisce gli articoli 6, 9, 10, 11, 17 e 29 della '
             'direttiva (UE) 2024/1346 (accoglienza).', '',
             '**Copertura: %d applicate, %d parziali, %d non applicate (su %d).**' % (applied, partial, failed, len(rep.rows)),
             '', '| ID | Lettera art. 10 | Esito | Dettaglio |', '|----|----|----|----|']
    for amid, letter, status, detail in rep.rows:
        lines.append('| %s | %s | %s | %s |' % (amid, letter, status, detail.replace('|', '\\|')))
    lines += ['', '## Note di interpretazione', '',
              '- **art. 4**: integralmente sostituito (rubrica «Documentazione» → «Documenti forniti al richiedente»).',
              '- **artt. 5-ter, 5-quater, 5-quinquies, 5-sexies** inseriti dopo l\'art. 5-bis (lett. c); '
              '**art. 6-quater** inserito dopo l\'art. 6-ter (lett. f).',
              '- **art. 6-bis, rubrica** (lett. e n. 8): «cosi\' modificata» — resa come sostituzione integrale '
              'della rubrica con il nuovo testo.',
              '- Le aggiunte «in fine» / «dopo le parole X» sono rese come sostituzione minimale (diff per parole) '
              'ancorata a una frase di coda univoca del comma, così da non barrare il testo che permane.',
              '- I rinvii al d.lgs. 25/2008 puntano al testo coordinato interattivo (sito «Dlgs25 interattivo»).']
    open(os.path.join(HERE, 'REPORT_MODIFICHE.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')

# ---------------------------------------------------------------- main
# ---------------------------------------------------------------- versioni (motore condiviso)
# rinvii per versione (nuovo/vecchio), strati amendments_<atto>.json, storia sotto la rubrica:
# v. ../versioni.py
import sys as _sys
_sys.path.insert(0, os.path.join(HERE, '..'))
import versioni as V
V.install(globals(), HERE)

def main():
    arts = load_articles()
    amendments = json.load(open(os.path.join(HERE, 'amendments.json')))['amendments']
    rep = Report()
    apply_amendments(arts, amendments, rep)
    V.apply_layers(globals(), arts, rep, HERE)
    lk = build_site(arts, rep)
    applied = sum(1 for r in rep.rows if r[2] == 'applicata')
    failed  = sum(1 for r in rep.rows if r[2] != 'applicata')
    print("Modifiche: %d applicate, %d da rivedere (su %d)" % (applied, failed, len(rep.rows)))
    print("Articoli (incl. inseriti):", len(arts), "| nuovi:", [a['label'] for a in arts if a.get('inserted')])
    cited = {k: len(v) for k, v in sorted(lk.cited.items())}
    print("Atti-fonte resi navigabili (articoli citati):", cited or "nessuno")
    if lk.unresolved:
        print("Rinvii lasciati non collegati (da rivedere a mano):", len(lk.unresolved))
    if lk.overrides:
        unused = [r for i, r in enumerate(lk.overrides) if i not in lk.ov_hits]
        print("Override applicati: %d/%d" % (len(lk.ov_hits), len(lk.overrides)))
        for r in unused:
            print("  ⚠️ OVERRIDE NON APPLICATO (nessun match):", r.get('art'), r.get('where'), repr(r.get('text')), 'nth', r.get('nth', 1))
    print("Scritti: index.html, assets/data.js, assets/amend.css, REPORT_MODIFICHE.md")

if __name__ == '__main__':
    main()
