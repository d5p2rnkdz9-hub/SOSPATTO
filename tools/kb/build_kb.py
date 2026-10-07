#!/usr/bin/env python3
"""Costruisce la KB testuale di SOS Patto (www.sospatto.it) dal repo del sito.

Sorgente unica: il repo del sito (questa cartella è tools/kb/; working tree). Tutto ciò che è pubblicato:
  - public/patto-interattivo/<num>.html          → 1-norme-ue/
  - public/patto-interattivo/<slug>/index.html   → 2-norme-italiane/
  - public/patto-interattivo/ext-*.html          → 6-atti-collegati/
  - content/giurisprudenza/*.md (+ PDF allegati) → 3-giurisprudenza/
  - content/circolari/*.md (+ PDF allegati)      → 4-circolari-prassi/
  - content/normativa/*.md (+ PDF allegati)      → 2-normativa-schede/ (atti senza testo interattivo, es. D.M.)
  - content/dottrina/*.md (+ PDF locali) + audizione-perilli → 5-dottrina/
Esclusi: .md.bozza, schede `esempio: true`.
Schede `prePatto: true`: tolte dal sito (regime previgente) ma tenute qui, marcate
«pre-Patto», senza URL della scheda; il PDF sta in allegati-pre-patto/ del repo.

Ogni riga di testo normativo porta un TAG di citazione, es.
  [1348 art.13 par.8] ...        [dlgs25 art.35-bis c.3 lett.a] ...
così un grep restituisce già la citazione esatta (niente numerazioni dedotte).

Uso:  npm run kb   (= python3 tools/kb/build_kb.py; output in kb/, OCR in cache in tools/kb/ocr_cache/<md5>.json)
"""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import fitz  # PyMuPDF
import yaml
from bs4 import BeautifulSoup, NavigableString, Tag

HERE = Path(__file__).resolve().parent                      # tools/kb/
SITE = Path(os.environ.get('SOSPATTO_REPO', HERE.parent.parent))   # il repo del sito
KB = Path(os.environ.get('SOSPATTO_KB', SITE / 'kb'))       # output (in .gitignore: si rigenera)
OCR_CACHE = HERE / 'ocr_cache'                              # cache OCR per md5 del PDF (in .gitignore)
BUNDLE = SITE / 'public/patto-interattivo'
BASEURL = 'https://www.sospatto.it'

EU = {
    '1346': ('Direttiva (UE) 2024/1346', 'accoglienza', 'Direttiva accoglienza'),
    '1347': ('Regolamento (UE) 2024/1347', 'qualifiche', 'Regolamento qualifiche'),
    '1348': ('Regolamento (UE) 2024/1348', 'procedure', 'Regolamento procedure (APR)'),
    '1349': ('Regolamento (UE) 2024/1349', 'rimpatrio-frontiera', 'Regolamento rimpatrio alla frontiera'),
    '1350': ('Regolamento (UE) 2024/1350', 'reinsediamento', 'Regolamento reinsediamento'),
    '1351': ('Regolamento (UE) 2024/1351', 'ramm', 'Regolamento RAMM (gestione asilo e migrazione, ex Dublino)'),
    '1352': ('Regolamento (UE) 2024/1352', 'ecris-tcn', 'Modifiche ECRIS-TCN'),
    '1356': ('Regolamento (UE) 2024/1356', 'screening', 'Regolamento screening (accertamenti)'),
    '1358': ('Regolamento (UE) 2024/1358', 'eurodac', 'Regolamento Eurodac'),
    '1359': ('Regolamento (UE) 2024/1359', 'crisi', 'Regolamento crisi e forza maggiore'),
}
IT = {
    'dl-100-2026': ('dl100', 'D.L. 12 giugno 2026, n. 100 (conv. senza modif. l. 7 agosto 2026, n. 145)',
                    'Prima attuazione italiana del Patto — atto di novella'),
    'dlgs-25-2008': ('dlgs25', 'D.Lgs. 28 gennaio 2008, n. 25', 'Procedure (testo coordinato con art. 11 d.l. 100/2026)'),
    'dlgs-142-2015': ('dlgs142', 'D.Lgs. 18 agosto 2015, n. 142', 'Accoglienza (testo coordinato con art. 10 d.l. 100/2026)'),
    'dlgs-286-1998': ('dlgs286', 'D.Lgs. 25 luglio 1998, n. 286', 'T.U. immigrazione (coordinato con art. 12 d.l. 100/2026)'),
    'dlgs-251-2007': ('dlgs251', 'D.Lgs. 19 novembre 2007, n. 251', 'Qualifiche (testo vigente, non novellato dal d.l. 100)'),
}

WS = re.compile(r'\s+')


def clean(s):
    return WS.sub(' ', (s or '').replace('\xa0', ' ')).strip()


def text_of(el):
    return clean(el.get_text())


def soup(path):
    return BeautifulSoup(Path(path).read_text(encoding='utf-8'), 'html.parser')


# ---------------------------------------------------------------- citazioni
def tag_str(prefix, ctx):
    parts = [prefix]
    for k, v in ctx:
        parts.append(f'{k}.{v}')
    return '[' + ' '.join(parts) + ']'


def add_label(ctx, label):
    lab = clean(label).strip('()').rstrip(')').strip()
    keys = [k for k, _ in ctx]
    if not lab or not re.match(r'^[\w\-]+$', lab):
        kind = 'tratt'
        lab = str(sum(1 for k in keys if k == 'tratt') + 1)
    elif re.fullmatch(r'\d+', lab) and 'lett' not in keys and 'n' not in keys:
        kind = 'n'
    elif re.fullmatch(r'[a-z]{1,2}', lab) and 'lett' not in keys and not re.fullmatch(r'[ivx]{2,}', lab):
        kind = 'lett'
    else:
        kind = 'pt'
    return ctx + [(kind, lab)]


# --------------------------------------------------------- atti UE (OJ html)
def walk_oj(el, ctx, out):
    for ch in el.children:
        if not isinstance(ch, Tag):
            continue
        cls = ch.get('class') or []
        if ch.name == 'div' and 'eli-title' in cls:
            continue
        if ch.name == 'p' and ('oj-ti-art' in cls or 'oj-sti-art' in cls):
            continue
        cid = ch.get('id') or ''
        m = re.fullmatch(r'\d{3}\.(\d{3})', cid)
        if ch.name == 'div' and m:
            walk_oj(ch, [c for c in ctx if c[0] == 'art'] + [('par', str(int(m.group(1))))], out)
        elif ch.name == 'p':
            t = text_of(ch)
            if t:
                out.append((ctx, t))
        elif ch.name == 'table' and 'oj-table' in cls:
            for tr in ch.find_all('tr'):
                cells = [text_of(td) for td in tr.find_all('td', recursive=False)]
                if any(cells):
                    out.append((ctx, ' | '.join(cells)))
        elif ch.name == 'table':
            body = ch.find('tbody') or ch
            for tr in body.find_all('tr', recursive=False):
                tds = tr.find_all('td', recursive=False)
                if len(tds) == 2:
                    walk_oj(tds[1], add_label(ctx, text_of(tds[0])), out)
                else:
                    t = text_of(tr)
                    if t:
                        out.append((ctx, t))
        else:
            walk_oj(ch, ctx, out)


# ------------------------------------------ atti collegati (EUR-Lex consolidati)
BLOCK = {'div', 'p', 'table', 'ul', 'ol', 'li'}


def walk_cons(el, ctx, out):
    for ch in list(el.children):
        if isinstance(ch, NavigableString):
            continue
        if not isinstance(ch, Tag):
            continue
        cls = ch.get('class') or []
        if 'title-article-norm' in cls or 'stitle-article-norm' in cls or 'eli-title' in cls or 'modref' in cls:
            continue
        if ch.name == 'table':
            rows = [tr for tr in ch.find_all('tr') if tr.find_parent('table') is ch]
            for tr in rows:
                tds = tr.find_all('td', recursive=False)
                if len(tds) == 2 and len(text_of(tds[0])) <= 8:
                    walk_cons(tds[1], add_label(ctx, text_of(tds[0])), out)
                else:
                    t = ' | '.join(text_of(td) for td in tds)
                    if t.strip(' |'):
                        out.append((ctx, t))
            continue
        if 'grid-container' in cls:
            c1 = ch.find(class_='grid-list-column-1')
            c2 = ch.find(class_='grid-list-column-2')
            if c1 and c2:
                walk_cons(c2, add_label(ctx, text_of(c1)), out)
                continue
        np_ = ch.find('span', class_='no-parag', recursive=False)
        if np_ is not None:
            lab = text_of(np_).rstrip('.').strip()
            np_.extract()
            ctx = [c for c in ctx if c[0] == 'art'] + [('par', lab)]  # vale anche per i commi successivi
            walk_cons(ch, ctx, out)
            continue
        if not any(isinstance(d, Tag) and d.name in BLOCK for d in ch.descendants):
            t = text_of(ch)
            if t and t not in ('▼B',) and not re.fullmatch(r'▼\w+', t):
                out.append((ctx, t))
        else:
            walk_cons(ch, ctx, out)


def parse_eu(path, prefix, cited, url_page):
    s = soup(path)
    doc = s.find(class_='doc') or s.body
    lines = []
    oj = bool(doc.find(class_='oj-ti-art'))
    title_bits = [text_of(p) for p in doc.find_all(class_=re.compile(r'^(oj-doc-ti|title-doc-first|title-doc-last)$'))[:4]]
    lines.append('> ' + ' — '.join(t for t in title_bits if t))
    lines.append('')
    seen_arts = 0
    for el in doc.find_all(True):
        cls = el.get('class') or []
        eid = el.get('id') or ''
        if el.name == 'p' and any(c in cls for c in ('oj-ti-section-1', 'oj-ti-section-2', 'title-division-1', 'title-division-2')) \
                and not el.find_parent(id=re.compile(r'^art_')):
            t = text_of(el)
            if t:
                lines.append(f'\n### {t}\n')
            continue
        m_rct = re.fullmatch(r'rct_(\d+)', eid)
        if m_rct:
            out = []
            walk_oj(el, [], out) if oj else walk_cons(el, [], out)
            txt = ' '.join(t for _, t in out)
            txt = re.sub(r'^\(\d+\)\s*', '', txt)
            lines.append(f'[{prefix} cons.{m_rct.group(1)}] {txt}')
            continue
        m_art = re.fullmatch(r'art_(\d+[a-z]?(?:-\w+)?)', eid)
        if m_art and el.name == 'p' and 'title-article-norm' in cls:
            # formato piatto: l'articolo è il <p> titolo + i fratelli fino al titolo successivo
            box = s.new_tag('div')
            box['id'] = eid
            rub = el.find_next_sibling()
            sib = el.next_sibling
            sibs = []
            while sib is not None:
                nxt = sib.next_sibling
                if isinstance(sib, Tag):
                    c2 = sib.get('class') or []
                    if any(x in c2 for x in ('title-article-norm', 'title-division-1', 'title-division-2',
                                             'title-annex-1', 'separator-annex')) or \
                            (sib.find(class_='title-article-norm') is not None):
                        break
                sibs.append(sib)
                sib = nxt
            el.extract()
            box.append(el)
            for x in sibs:
                box.append(x.extract())
            m_art_box = box
        else:
            m_art_box = None
        if m_art_box is not None:
            el = m_art_box
        if m_art and el.name == 'div':
            n = m_art.group(1)
            head = el.find(class_=re.compile(r'^(oj-ti-art|title-article-norm)$'))
            rub = el.find(class_=re.compile(r'^(oj-sti-art|stitle-article-norm)$'))
            h = text_of(head) if head else f'Articolo {n}'
            if rub:
                h += ' — ' + text_of(rub)
            seen_arts += 1
            lines.append(f'\n## {h}')
            lines.append(f'<{url_page}#art_{n}>')
            if cited.get(n):
                lines.append('Citato in SOS Patto da: ' + '; '.join(cited[n]))
            lines.append('')
            out = []
            (walk_oj if oj else walk_cons)(el, [('art', n)], out)
            for ctx, t in out:
                lines.append(f'{tag_str(prefix, ctx)} {t}')
            continue
        m_anx = re.fullmatch(r'anx_(\w+)', eid)
        if m_anx and 'eli-container' in cls:
            heads = [text_of(p) for p in el.find_all('p', class_='oj-doc-ti')]
            lines.append(f'\n## {" — ".join(heads) or "ALLEGATO " + m_anx.group(1)}')
            lines.append(f'<{url_page}#{eid}>\n')
            out = []
            walk_oj(el, [('all', m_anx.group(1))], out) if oj else walk_cons(el, [('all', m_anx.group(1))], out)
            for ctx, t in out:
                if t in heads:
                    continue
                lines.append(f'{tag_str(prefix, ctx)} {t}')
    return '\n'.join(lines), seen_arts


# ---------------------------------------------- norme italiane (tracked changes)
def comma_lines(div):
    """Restituisce (vigente_lines, previgente_lines, amd_sources)."""
    amd = sorted({e.get('data-amd') for e in div.find_all(['ins', 'del']) if e.get('data-amd')})

    def render(keep):  # keep = 'vig' | 'prev'
        d = BeautifulSoup(str(div), 'html.parser').div
        for e in d.find_all('del' if keep == 'vig' else 'ins'):
            e.decompose()
        cn = d.find(class_='cnum')
        if cn:
            cn.decompose()
        for br in d.find_all('br'):
            br.replace_with('\n@@BR@@')
        for ln in d.find_all(class_='lett-n'):
            ln.insert_before('@@L@@')
        raw = d.get_text()
        res = []
        for seg in raw.split('\n@@BR@@'):
            seg = seg.replace('\xa0', ' ')
            lab = None
            m = re.match(r'\s*@@L@@\s*([\w\-]+)\)', seg)
            if m:
                lab = m.group(1)
            seg = clean(seg.replace('@@L@@', ''))
            if seg:
                res.append((lab, seg))
        return res
    has_changes = bool(div.find(['ins', 'del']))
    vig = render('vig')
    prev = render('prev') if has_changes else []
    return vig, prev, amd


def parse_it(path, prefix, cited, url_page):
    s = soup(path)
    doc = s.find(class_='doc') or s.body
    lines = []
    for p in doc.find_all(class_='oj-doc-ti'):
        lines.append('> ' + text_of(p))
    ban = doc.find(class_='amd-banner')
    if ban:
        lines.append('> ' + text_of(ban))
    lines.append('> Legenda: righe senza marcatore = testo vigente; ⟨novella: …⟩ = comma modificato; '
                 'righe PREVIGENTE = testo prima della novella (utile per il regime transitorio, art. 17 d.l. 100/2026 e art. 79 reg. 1348).')
    pre = doc.find(class_='preambolo')
    if pre:
        lines.append('\n## Preambolo\n')
        lines.append(f'[{prefix} preambolo] ' + text_of(pre))
    n_art = 0
    for el in doc.find_all(['h2', 'div']):
        cls = el.get('class') or []
        if el.name == 'h2' and 'capo' in cls:
            lines.append(f'\n### {text_of(el)}\n')
            continue
        if el.name != 'div' or 'art' not in cls or 'eli-subdivision' not in cls:
            continue
        eid = el.get('id') or ''
        n = eid.removeprefix('art_')
        head = el.find(class_='oj-ti-art')
        rub = el.find(class_='oj-sti-art')
        h = text_of(head) if head else f'Art. {n}'
        if rub:
            h += ' — ' + text_of(rub)
        n_art += 1
        lines.append(f'\n## {h}')
        lines.append(f'<{url_page}#{eid}>')
        if 'art-new' in cls:
            lines.append('(Articolo inserito dal d.l. 100/2026)')
        if cited.get(n):
            lines.append('Citato in SOS Patto da: ' + '; '.join(cited[n]))
        lines.append('')
        commi = el.find_all('div', class_='comma', recursive=False)
        if not commi:
            for ch in el.children:
                if isinstance(ch, Tag) and ch.name in ('div', 'p') and 'eli-title' not in (ch.get('class') or []) \
                        and 'oj-ti-art' not in (ch.get('class') or []):
                    t = text_of(ch)
                    if t:
                        lines.append(f'[{prefix} art.{n}] {t}')
        for c in commi:
            cn = c.find(class_='cnum')
            cnum = clean(cn.get_text()).rstrip('.') if cn else ''
            abrog = 'abrog' in (c.get('class') or [])
            base = [('art', n)] + ([('c', cnum)] if cnum else [])
            vig, prev, amd = comma_lines(c)
            note = f' ⟨novella: {"; ".join(amd)}⟩' if amd else ''
            if not vig and prev:
                lines.append(f'{tag_str(prefix, base)} (comma soppresso{": " + "; ".join(amd) if amd else ""})')
            first = True
            for lab, t in vig:
                ctx = base + ([('lett', lab)] if lab else [])
                suffix = (note if first else '') + (' (abrogato)' if abrog and first else '')
                lines.append(f'{tag_str(prefix, ctx)} {t}{suffix}')
                first = False
            for lab, t in prev:
                ctx = base + ([('lett', lab)] if lab else [])
                lines.append(f'{tag_str(prefix, ctx)[:-1]} PREVIGENTE] {t}')
    return '\n'.join(lines), n_art


# ------------------------------------------------------------------- PDF/OCR
def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def ocr_page(pdf, pno):
    with tempfile.TemporaryDirectory() as td:
        base = Path(td) / 'p'
        subprocess.run(['pdftoppm', '-r', '300', '-gray', '-png', '-f', str(pno), '-l', str(pno),
                        '-singlefile', str(pdf), str(base)], check=True, capture_output=True)
        r = subprocess.run(['tesseract', str(base) + '.png', '-', '-l', 'ita', '--psm', '6'],
                           capture_output=True, text=True)
        return r.stdout


def pdf_text(pdf):
    """Testo per pagina con marcatori [p. N]; OCR (tesseract ita) sulle pagine senza testo."""
    h = md5(pdf)
    cache = OCR_CACHE / f'{h}.json'
    if cache.exists():
        return json.loads(cache.read_text())
    d = fitz.open(pdf)
    pages, ocr_used = [], []
    for i, pg in enumerate(d, 1):
        t = pg.get_text()
        if len(t.split()) < 40:
            try:
                t2 = ocr_page(pdf, i)
            except Exception as e:  # noqa
                t2 = ''
            if len(t2.split()) > len(t.split()):
                t = t2
                ocr_used.append(i)
        pages.append(t)
    res = {'pages': pages, 'ocr': ocr_used, 'n': len(pages)}
    OCR_CACHE.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(res, ensure_ascii=False))
    return res


SENT = re.compile(r'(?<=[.;:!?»”)])\s+(?=[A-ZÀ-Ý0-9«“(])')


def reflow_text(t, maxlen=700):
    """Unisce le righe (incluse le sillabazioni) e ridivide per frasi: le frasi non restano spezzate."""
    t = re.sub(r'(\w)-\n(?=[a-zà-ù])', r'\1', t)
    t = clean(t)
    out, cur = [], ''
    for sent in SENT.split(t):
        if cur and len(cur) + len(sent) > maxlen:
            out.append(cur)
            cur = sent
        else:
            cur = f'{cur} {sent}'.strip()
    if cur:
        out.append(cur)
    return '\n'.join(out)


def fmt_pdf(res):
    out = []
    for i, t in enumerate(res['pages'], 1):
        out.append(f'[p. {i}]{" (OCR)" if i in res["ocr"] else ""}\n{reflow_text(t)}\n')
    return '\n'.join(out)


def reflow_md(md):
    """Unisce le righe a capo fisso dei paragrafi markdown (non tocca titoli, elenchi, citazioni)."""
    out = []
    for ln in md.split('\n'):
        st = ln.strip()
        starts = not st or re.match(r'^(#|[-*+] |\d+[.)] |\||```)', st)
        if out and out[-1].strip() and not starts and not re.match(r'^(#|\||```)', out[-1].strip()):
            if st.startswith('>') and out[-1].lstrip().startswith('>'):
                out[-1] += ' ' + st.lstrip('> ').strip()
                continue
            if not st.startswith('>') and not out[-1].lstrip().startswith('>'):
                out[-1] += ' ' + st
                continue
        out.append(ln)
    return '\n'.join(out)


# -------------------------------------------------------------------- schede
def read_scheda(path):
    raw = path.read_text(encoding='utf-8')
    m = re.match(r'^---\n(.*?)\n---\n?(.*)$', raw, re.S)
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, m.group(2).strip()


def abs_links(md):
    return re.sub(r'\]\((/[^)]+)\)', lambda m: f']({BASEURL}{m.group(1)})', md)


def href_to_ref(href):
    """/patto-interattivo/1348.html#art_79 → ('1348','79'); dlgs → ('dlgs25','26')."""
    if not href:
        return None
    m = re.search(r'patto-interattivo/(\d{4})\.html(?:#art_([\w\-]+))?', href)
    if m:
        return (m.group(1), m.group(2))
    m = re.search(r'patto-interattivo/([\w\-]+)/index\.html(?:#art_([\w\-]+))?', href)
    if m and m.group(1) in IT:
        return (IT[m.group(1)][0], m.group(2))
    m = re.search(r'patto-interattivo/ext-([\w\-]+)\.html(?:#art_([\w\-]+))?', href)
    if m:
        return (m.group(1), m.group(2))
    return None


def fmt_date(d):
    if isinstance(d, (datetime.date, datetime.datetime)):
        mesi = ['gennaio', 'febbraio', 'marzo', 'aprile', 'maggio', 'giugno', 'luglio', 'agosto',
                'settembre', 'ottobre', 'novembre', 'dicembre']
        return f'{d.day} {mesi[d.month - 1]} {d.year}', d.isoformat()
    return str(d), str(d)


def collect_schede():
    items = []
    for kind in ('giurisprudenza', 'circolari', 'normativa', 'dottrina'):
        for p in sorted((SITE / 'content' / kind).glob('*.md')):
            fm, body = read_scheda(p)
            if fm.get('esempio'):
                continue
            items.append((kind, p.stem, fm, body))
    return items


def scheda_title(kind, fm):
    d, _ = fmt_date(fm.get('date'))
    if kind == 'giurisprudenza':
        pre = ' [pre-Patto]' if fm.get('prePatto') else ''
        return f"{fm.get('corte', '')}, {fm.get('tipo', '')}, {fm.get('numero', '')}, {d}{pre}"
    if kind in ('circolari', 'normativa'):
        return f"{fm.get('ente', '')}, {fm.get('tipo', '')}, {fm.get('numero', '')}, {d}"
    return f"{fm.get('autori', '')}, «{fm.get('titolo', '')}», {fm.get('fonte', '')}"


def short_cite(kind, slug, fm):
    d, _ = fmt_date(fm.get('date'))
    if kind == 'giurisprudenza':
        pre = ' [pre-Patto]' if fm.get('prePatto') else ''
        return f"{fm.get('corte', '')} {fm.get('numero', '')} ({d}){pre} [3-giurisprudenza/{slug}.md]"
    if kind in ('circolari', 'normativa'):
        return f"{fm.get('ente', '')}, {fm.get('numero', '')} ({d}) [{DIRS[kind]}/{slug}.md]"
    return f"{fm.get('autori', '')}, {fm.get('fonte', '')} [5-dottrina/{slug}.md]"


def local_pdfs(fm, body):
    hrefs = []
    if fm.get('pdf'):
        hrefs.append(('Provvedimento' if fm.get('corte') else (fm.get('pdfLabel') or 'Documento'), fm['pdf']))
    for a in fm.get('allegati') or []:
        hrefs.append((a.get('label', 'Allegato'), a.get('href')))
    for l in fm.get('links') or []:
        if str(l.get('href', '')).startswith('/allegati/'):
            hrefs.append((l.get('label', 'Documento'), l['href']))
    for m in re.finditer(r'\]\((/allegati/[^)]+\.pdf)\)', body):
        hrefs.append(('PDF citato nel testo', m.group(1)))
    seen, res = set(), []
    for lab, h in hrefs:
        if not h or h in seen or not h.startswith('/allegati/'):
            continue
        seen.add(h)
        f = SITE / 'public' / h.lstrip('/')
        if not f.exists():  # schede prePatto: PDF tolto da public/
            f = SITE / 'allegati-pre-patto' / Path(h).name
        if f.exists():
            res.append((lab, h, f))
    return res


DIRS = {'giurisprudenza': '3-giurisprudenza', 'circolari': '4-circolari-prassi', 'dottrina': '5-dottrina',
        'normativa': '2-normativa-schede'}   # atti normativi italiani senza testo interattivo (D.M., …): schede, non circolari


def write_scheda(kind, slug, fm, body, pdf_cache):
    title = scheda_title(kind, fm)
    d_h, d_iso = fmt_date(fm.get('date'))
    L = [f'# {title}', '']
    L.append(f'- Tipo fonte: {kind}')
    L.append(f'- Data: {d_iso}')
    for k in ('corte', 'ente', 'tipo', 'numero', 'autori', 'titolo', 'fonte'):
        if fm.get(k):
            L.append(f'- {k.capitalize()}: {fm[k]}')
    if fm.get('prePatto'):
        L.append('- Regime: pre-Patto (disciplina previgente al 12 giugno 2026) — scheda NON pubblicata sul sito')
    else:
        L.append(f'- Scheda SOS Patto: {BASEURL}/{kind}/{slug}.html')
    if fm.get('temi'):
        L.append('- Temi: ' + '; '.join(fm['temi']))
    if fm.get('norme'):
        L.append('- Norme richiamate nella scheda:')
        for n in fm['norme']:
            ref = href_to_ref(n.get('href'))
            tag = f' → [{ref[0]} art.{ref[1]}]' if ref and ref[1] else (f' → [{ref[0]}]' if ref else '')
            L.append(f"  - {n.get('label')}{tag}")
    for l in fm.get('links') or []:
        if not str(l.get('href', '')).startswith('/allegati/'):
            L.append(f"- Link: {l.get('label')} <{l.get('href')}>")
    L.append('')
    for key, lab in (('massima', 'Massima (redazione SOS Patto — NON è testo del provvedimento)'),
                     ('oggetto', 'Oggetto (redazione SOS Patto)'),
                     ('sommario', 'Sommario (redazione SOS Patto)')):
        if fm.get(key):
            L += [f'## {lab}', '', clean(fm[key]), '']
    if body:
        L += ['## Commento della scheda (redazione SOS Patto)', '', reflow_md(abs_links(body)), '']
    for lab, h, f in local_pdfs(fm, body):
        res = pdf_cache[str(f)]
        ocr = f" — OCR su pp. {', '.join(map(str, res['ocr']))}: verificare le citazioni testuali sul PDF" if res['ocr'] else ''
        pdf_rif = f'allegati-pre-patto/{f.name} nel repo del sito, non pubblicato' if fm.get('prePatto') else f'{BASEURL}{h}'
        L += [f'## Testo integrale — {lab}', f'PDF: {pdf_rif} ({res["n"]} pp.{ocr})', '',
              '(Documento pubblicato in forma oscurata: i dati personali sono omessi.)' if kind == 'giurisprudenza' else '',
              '', fmt_pdf(res), '']
    out = KB / DIRS[kind] / f'{slug}.md'
    out.write_text('\n'.join(L), encoding='utf-8')
    return out


def page_text(html_path):
    s = soup(html_path)
    main = s.find('main') or s.body
    for x in main.find_all(['script', 'style', 'nav']):
        x.decompose()
    return '\n'.join(clean(t) for t in main.get_text('\n').split('\n') if clean(t))


# ---------------------------------------------------------------------- main
def main():
    if not BUNDLE.exists():
        sys.exit(f'Repo SOS Patto non trovato: {SITE}')
    for d in ('1-norme-ue', '2-norme-italiane', '2-normativa-schede', '3-giurisprudenza', '4-circolari-prassi', '5-dottrina', '6-atti-collegati'):
        (KB / d).mkdir(parents=True, exist_ok=True)
        for f in (KB / d).glob('*.md'):
            f.unlink()

    schede = collect_schede()
    # indice inverso norma → schede
    cited = defaultdict(lambda: defaultdict(list))
    for kind, slug, fm, body in schede:
        for n in fm.get('norme') or []:
            ref = href_to_ref(n.get('href'))
            if ref and ref[1]:
                c = short_cite(kind, slug, fm)
                if c not in cited[ref[0]][ref[1]]:
                    cited[ref[0]][ref[1]].append(c)

    # PDF (OCR in parallelo, cache per md5)
    pdfs = sorted({str(f) for kind, slug, fm, body in schede for _, _, f in local_pdfs(fm, body)})
    print(f'PDF: {len(pdfs)} (OCR solo se non in cache)…', flush=True)
    with ThreadPoolExecutor(max_workers=6) as ex:
        pdf_cache = dict(zip(pdfs, ex.map(pdf_text, pdfs)))

    catalog = []
    # 1. norme UE
    for num, (nome, slugname, desc) in EU.items():
        txt, n = parse_eu(BUNDLE / f'{num}.html', num, cited.get(num, {}), f'{BASEURL}/patto-interattivo/{num}.html')
        fn = f'1-norme-ue/{num}-{slugname}.md'
        (KB / fn).write_text(f'# {nome} — {desc}\n\nTag di citazione: [{num} art.N par.N lett.x] · considerando: [{num} cons.N]\n'
                             f'Fonte: {BASEURL}/patto-interattivo/{num}.html (testo EUR-Lex)\n\n{txt}\n', encoding='utf-8')
        catalog.append(('Norme UE (Patto)', fn, f'{nome} — {desc}', f'{n} artt.', num))
    # 2. norme italiane
    for slug, (pref, nome, desc) in IT.items():
        txt, n = parse_it(BUNDLE / slug / 'index.html', pref, cited.get(pref, {}), f'{BASEURL}/patto-interattivo/{slug}/index.html')
        fn = f'2-norme-italiane/{slug}.md'
        (KB / fn).write_text(f'# {nome} — {desc}\n\nTag di citazione: [{pref} art.N c.N lett.x] · previgente: [{pref} art.N c.N PREVIGENTE]\n'
                             f'Fonte: {BASEURL}/patto-interattivo/{slug}/index.html (testo Normattiva, novelle d.l. 100/2026 evidenziate)\n\n{txt}\n',
                             encoding='utf-8')
        catalog.append(('Norme italiane', fn, f'{nome} — {desc}', f'{n} artt.', pref))
    # 6. atti collegati
    manifest = {}
    mf = SITE.parent / 'x'  # placeholder, titoli presi dal file
    for p in sorted(BUNDLE.glob('ext-*.html')):
        code = p.stem.removeprefix('ext-')
        txt, n = parse_eu(p, code, cited.get(code, {}), f'{BASEURL}/patto-interattivo/{p.name}')
        first = txt.split('\n', 1)[0].lstrip('> ')[:200]
        fn = f'6-atti-collegati/{code}.md'
        (KB / fn).write_text(f'# {code} — {first}\n\nTag di citazione: [{code} art.N par.N lett.x]\n'
                             f'Fonte: {BASEURL}/patto-interattivo/{p.name} (atto richiamato dal Patto, testo EUR-Lex)\n\n{txt}\n', encoding='utf-8')
        catalog.append(('Atti collegati (richiamati dal Patto)', fn, first, f'{n} artt.', code))
    # 3-5. schede
    for kind, slug, fm, body in schede:
        out = write_scheda(kind, slug, fm, body, pdf_cache)
        catalog.append(({'giurisprudenza': 'Giurisprudenza', 'circolari': 'Circolari e prassi', 'dottrina': 'Dottrina',
                         'normativa': 'Normativa italiana (schede)'}[kind],
                        str(out.relative_to(KB)), scheda_title(kind, fm), '; '.join(fm.get('temi') or []), fmt_date(fm.get('date'))[1]))
    # pagina audizione Perilli (trascrizione pubblicata)
    ap = SITE / '_site/audizione-perilli.html'
    if ap.exists():
        (KB / '5-dottrina/audizione-perilli-trascrizione.md').write_text(
            f'# Audizione Perilli — trascrizione non ufficiale pubblicata su SOS Patto\n\nFonte: {BASEURL}/audizione-perilli.html\n\n{page_text(ap)}\n', encoding='utf-8')
        catalog.append(('Dottrina', '5-dottrina/audizione-perilli-trascrizione.md', 'Audizione Perilli (trascrizione)', '', ''))

    # indice norme citate
    L = ['# Indice inverso: norma → schede SOS Patto che la richiamano', '',
         'Generato dal campo `norme` delle schede (giurisprudenza, circolari, dottrina). '
         'Non copre i richiami presenti solo nel testo integrale dei provvedimenti: per quelli fare grep in 3-giurisprudenza/.', '']
    order = list(EU) + [v[0] for v in IT.values()]
    for act in sorted(cited, key=lambda a: (order.index(a) if a in order else 99, a)):
        L.append(f'\n## {act}')
        for art in sorted(cited[act], key=lambda x: [int(t) if t.isdigit() else t for t in re.split(r'(\d+)', x)]):
            L.append(f'- art. {art}: ' + '; '.join(cited[act][art]))
    (KB / 'INDICE-norme-citate.md').write_text('\n'.join(L) + '\n', encoding='utf-8')

    # catalogo
    try:
        commit = subprocess.run(['git', '-C', str(SITE), 'log', '-1', '--format=%h %cs %s'], capture_output=True, text=True).stdout.strip()
    except Exception:
        commit = '?'
    C = ['# Catalogo KB SOS Patto', '',
         f'Costruita il {datetime.date.today().isoformat()} da `{SITE}` (commit {commit}). '
         'Rigenerare con `python3 _build/build_kb.py`.', '']
    sect = None
    for row in catalog:
        if row[0] != sect:
            sect = row[0]
            C.append(f'\n## {sect}\n')
        if sect in ('Giurisprudenza', 'Circolari e prassi', 'Dottrina'):
            C.append(f'- {row[4]} · [{row[1]}]({row[1]}) — {row[2]}' + (f' — temi: {row[3]}' if row[3] else ''))
        else:
            C.append(f'- `[{row[4]} …]` [{row[1]}]({row[1]}) — {row[2]} ({row[3]})')
    (KB / 'CATALOGO.md').write_text('\n'.join(C) + '\n', encoding='utf-8')
    counts = defaultdict(int)
    for r in catalog:
        counts[r[0]] += 1
    print(dict(counts))
    print(f'OCR usato su {sum(1 for r in pdf_cache.values() if r["ocr"])} PDF')


if __name__ == '__main__':
    main()
