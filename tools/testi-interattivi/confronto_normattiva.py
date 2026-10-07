#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Confronto di verita' dei 4 testi interattivi contro Normattiva (fonte di verita').

Per ogni atto costruisce TRE modelli con il parser del suo stesso builder:
  base  = snapshot vecchio (giugno, pre-consolidamento d.l. 100/2026)
  sito  = base + amendments.json applicati -> testo FINALE (segmenti non-del)
  fresh = snapshot Normattiva odierno (nm_fresh_YYYYMMDD, gia' consolidato)

Doppio confronto:
  A) base vs fresh  -> isola TUTTO cio' che e' cambiato su Normattiva da giugno
  B) sito  vs fresh -> la verifica richiesta: il nostro coordinato deve coincidere
                       col vigente Normattiva. Atteso: vuoto.

Uso:
  python3 confronto_normattiva.py [--act dlgs25,...] [--freshdir nm_fresh_20260710]
Output: <freshdir>/reports/confronto_<act>.md + .json
"""
import argparse, difflib, importlib.util, json, os, re
from collections import OrderedDict

ROOT = os.path.dirname(os.path.abspath(__file__))

BUILDERS = {
    'dlgs25':  ('Dlgs25 interattivo',  'build_dlgs25',  'nm_html'),
    'dlgs142': ('142-15-interattivo',  'build_dlgs142', 'nm_html_142'),
    'dlgs286': ('286-98-interattivo',  'build_dlgs286', 'nm_html_286'),
    'dlgs251': ('251-07-interattivo',  'build_dlgs251', 'nm_html_251'),
}

# articolo mai in vigore / abrogato: placeholder Normattiva a livello di rubrica
# (\s* dopo piu': canon puo' aver compattato lo spazio dopo l'apostrofo GU)
RE_TOMBSTONE = re.compile(
    r"(?i)^\s*\(*\s*articolo\s+(abrogato|non\s+piu'?\s*previsto|soppresso)")
# comma abrogato/soppresso: placeholder Normattiva a livello di comma
RE_COMMA_ABRO = re.compile(r"(?i)^\s*\(*\s*(comma\s+)?(abrogato|soppresso)")

# vocabolario dei placeholder interni («LETTERA SOPPRESSA DAL D.L. ...» in mezzo
# a un comma): se il diff mostra SOLO inserzioni Normattiva fatte di questi token,
# la discrepanza e' un artefatto di rappresentazione, non un errore di testo
_PLACEHOLDER_WORDS = {
    'LETTERA', 'LETTERE', 'NUMERO', 'NUMERI', 'COMMA', 'COMMI', 'PERIODO',
    'SOPPRESSA', 'SOPPRESSO', 'SOPPRESSE', 'SOPPRESSI',
    'ABROGATA', 'ABROGATO', 'ABROGATE', 'ABROGATI',
    'DAL', 'DALLA', 'DALL', 'D.L.', 'L.', 'N.', 'N', 'CONVERTITO', 'CON',
    'MODIFICAZIONI', 'DECRETO', 'LEGGE', 'LEGISLATIVO',
    'GENNAIO', 'FEBBRAIO', 'MARZO', 'APRILE', 'MAGGIO', 'GIUGNO', 'LUGLIO',
    'AGOSTO', 'SETTEMBRE', 'OTTOBRE', 'NOVEMBRE', 'DICEMBRE',
}

def canon(s):
    """Normalizzazione condivisa, identica sui due lati del confronto."""
    s = s.replace('((...))', ' ')                    # omissis Normattiva (testo soppresso)
    s = re.sub(r'\s*\(\(\s*\d{1,3}\s*\)\)', '', s)   # marcatore nota ((22))
    s = re.sub(r'\s*\(\d{1,3}\)', '', s)             # marcatore nota (8)
    s = s.replace('((', ' ').replace('))', ' ')      # parentesi di novella
    # il rendering <pre> di Normattiva spazieggia apostrofi e punteggiatura
    # («dell' articolo», «445 ,») dove la GU scrive «dell'articolo», «445,»:
    # differenze SOLO tipografiche, normalizzate su entrambi i lati
    s = re.sub(r"'\s+(?=[A-Za-zÀ-ÿ0-9])", "'", s)
    s = re.sub(r'\s+([,;:.!?])', r'\1', s)
    s = re.sub(r'«\s+', '«', s)
    s = re.sub(r'\s+»', '»', s)
    # residui tipografici del rendering: righe di trattini separatori, sequenze
    # di puntini variabili fra versioni («riposo....» vs «riposo.»), spazio
    # prima dell'ordinale («2 -bis» vs «2-bis»)
    s = re.sub(r'-{4,}', ' ', s)
    s = re.sub(r'\.{2,}', '.', s)
    s = re.sub(r'(\d)\s+-\s*(?=bis|ter|quater|quinquies|sexies|septies|octies|novies|nonies|decies)',
               r'\1-', s)
    # sequenze di punteggiatura lasciate dall'omissis («2, ((...)) ,» -> «2, ,»):
    # tieni il primo segno della sequenza
    s = re.sub(r'([,;:.])(\s*[,;:.])+', r'\1', s)
    # punto spurio prima di una continuazione minuscola («nazionale. e'ammesso»:
    # residuo dei puntini-omissis delle versioni vecchie); simmetrico sui due lati
    s = re.sub(r'(?<=[a-zà-ÿ0-9])\.(\s+[a-zà-ÿ])', r'\1', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def canon_rubrica(s):
    """Le versioni riconsolidate di Normattiva racchiudono la rubrica in parentesi
    («(Diritto di rimanere...)») dove le versioni piu' vecchie no: convenzione di
    visualizzazione, non testo — spoglia UNA coppia esterna bilanciata."""
    s = s.strip()
    m = re.match(r'^\(\s*(.*?)\s*\)$', s)
    if m:
        inner = m.group(1)
        depth = 0
        for ch in inner:
            if ch == '(':
                depth += 1
            elif ch == ')':
                depth -= 1
                if depth < 0:
                    return s.strip(' .')
        s = inner
    return s.strip(' .')

def load_builder(act):
    folder, modname, old_dir = BUILDERS[act]
    p = os.path.join(ROOT, folder, modname + '.py')
    spec = importlib.util.spec_from_file_location('%s_%s' % (modname, act), p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, folder, os.path.join(ROOT, old_dir)

def model(arts, mod, final):
    """label -> {rubrica, commi{num:txt}, abrogati:set, inserted, tomb}.
    final=True legge il testo FINALE dei segmenti (non-del); i commi marcati
    'abrogato' finiscono nel set abrogati (esclusi dal testo)."""
    m = OrderedDict()
    for a in arts:
        commi, abro = OrderedDict(), set()
        for c in a['commi']:
            if final and c.get('abrogato'):
                abro.add(c['num']); continue
            commi[c['num']] = canon(mod.seg_text(c) if final else c['text'])
        rub = canon_rubrica(canon(''.join(s[1] for s in a['rubrica_seg'] if s[0] != 'del')
                                  if final else a['rubrica']))
        m[a['label']] = dict(rubrica=rub, commi=commi, abrogati=abro,
                             inserted=bool(a.get('inserted')),
                             tomb=bool(RE_TOMBSTONE.match(rub)) and not commi)
    return m

def word_diff(site, fresh, ctx=3):
    """Diff parola-per-parola compatto: {SITO- ...} testo solo nostro,
    {NORM+ ...} testo solo Normattiva."""
    sa, sb = site.split(), fresh.split()
    out, ins_tokens, del_tokens = [], [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, sa, sb, autojunk=False).get_opcodes():
        if op == 'equal':
            seg = sa[i1:i2]
            out.append(' '.join(seg) if len(seg) <= 2 * ctx
                       else ' '.join(seg[:ctx]) + ' […] ' + ' '.join(seg[-ctx:]))
        else:
            if op in ('delete', 'replace'):
                t = ' '.join(sa[i1:i2]); del_tokens += sa[i1:i2]
                out.append('{SITO- %s}' % t)
            if op in ('insert', 'replace'):
                t = ' '.join(sb[j1:j2]); ins_tokens += sb[j1:j2]
                out.append('{NORM+ %s}' % t)
    return ' '.join(out), ins_tokens, del_tokens

def is_placeholder_artifact(ins_tokens, del_tokens):
    """Solo inserzioni Normattiva in stile placeholder MAIUSCOLO («PERIODO SOPPRESSO
    DAL D.L. 12 GIUGNO 2026, N. 100.», «LETTERA ABROGATA DAL...»): il sito rende la
    soppressione come testo barrato (escluso dal finale), Normattiva con l'avviso."""
    if del_tokens or not ins_tokens:
        return False
    j = ' '.join(ins_tokens)
    if not re.search(r'(?i)(soppress|abrogat|non\s+piu)', j):
        return False
    return not re.search(r'[a-zà-ÿ]{3,}', j)   # tutto maiuscole/numeri/punteggiatura

SEG_CLASSES = {'MISMATCH', 'COMMA-ASSENTE-NORMATTIVA', 'COMMA-NUOVO-NORMATTIVA'}

def lenient_join(entry):
    """Testo INTEGRALE dell'articolo (rubrica + commi con marcatore), con
    normalizzazione lenta dei marcatori: Normattiva spezza/fonde i commi a
    seconda degli a-capo della versione servita («1-bis.» a inizio riga = comma
    separato; in mezzo alla riga = testo del comma precedente). Se il testo
    integrale coincide, la differenza era SOLO di segmentazione."""
    parts = [entry['rubrica']]
    for num, txt in entry['commi'].items():
        if RE_COMMA_ABRO.match(txt):
            continue                      # placeholder di comma abrogato (simmetrico)
        parts.append('%s. %s' % (num, txt))
    s = ' '.join(parts)
    s = re.sub(r'\.\s+(?=\d{1,3}[.\-])', ' ', s)                      # punto-frase prima del marcatore
    s = re.sub(r'\b(\d{1,3}(?:-\w+)?(?:\.\d+)?)\.(?=\s)', r'\1', s)   # punto del marcatore
    # marcatore duplicato quando l'a-capo di Normattiva crea un falso comma il cui
    # numero ripete la citazione che precede («previste al comma 2-ter 2-ter E'…»)
    s = re.sub(r'\b(\d{1,3}(?:-\w+)?(?:\.\d+)?)( \1)+\b', r'\1', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def artkey(label):
    m = re.match(r'(\d+)(?:-(\w+))?(?:\.(\d+))?', label)
    ords = ['', 'bis', 'ter', 'quater', 'quinquies', 'sexies', 'septies',
            'octies', 'novies', 'nonies', 'decies', 'undecies', 'duodecies']
    o = m.group(2) or ''
    return (int(m.group(1)), ords.index(o) if o in ords else 99, int(m.group(3) or 0))

def compare(m_a, m_b, side_a='SITO'):
    """Confronta due modelli; ritorna findings + contatori. m_b = Normattiva."""
    F = []
    n_art_ok = n_comma_ok = n_abro_ok = 0
    for lab in sorted(m_a, key=artkey):
        s = m_a[lab]; f = m_b.get(lab)
        if f is None:
            F.append(dict(art=lab, comma=None, classe='ARTICOLO-ASSENTE-NORMATTIVA',
                          sito=s['rubrica'][:120], norm=None, diff=None))
            continue
        if f['tomb'] and not s['commi']:
            n_art_ok += 1; continue
        art_clean = True
        if s['rubrica'] != f['rubrica']:
            d, ins, dele = word_diff(s['rubrica'], f['rubrica'])
            F.append(dict(art=lab, comma='rubrica', classe='RUBRICA-DIFFORME',
                          sito=s['rubrica'], norm=f['rubrica'], diff=d))
            art_clean = False
        for num, stext in s['commi'].items():
            ftext = f['commi'].get(num)
            if ftext is None:
                F.append(dict(art=lab, comma=num, classe='COMMA-ASSENTE-NORMATTIVA',
                              sito=stext[:200], norm=None, diff=None))
                art_clean = False
            elif stext != ftext:
                d, ins, dele = word_diff(stext, ftext)
                classe = ('placeholder-artifact'
                          if is_placeholder_artifact(ins, dele) else 'MISMATCH')
                F.append(dict(art=lab, comma=num, classe=classe,
                              sito=stext, norm=ftext, diff=d))
                if classe == 'MISMATCH':
                    art_clean = False
            else:
                n_comma_ok += 1
        for num in s['abrogati']:
            if num in s['commi']:
                continue   # comma SOSTITUITO (vecchio abrogato + nuovo stesso num): gia' confrontato sopra
            ftext = f['commi'].get(num)
            if ftext is None or RE_COMMA_ABRO.match(ftext):
                n_abro_ok += 1
            else:
                F.append(dict(art=lab, comma=num, classe='ABROGAZIONE-NON-SU-NORMATTIVA',
                              sito='(abrogato dal sito)', norm=ftext[:200], diff=None))
                art_clean = False
        for num, ftext in f['commi'].items():
            if num in s['commi'] or num in s['abrogati']:
                continue
            classe = ('COMMA-NUOVO-ABROGATO' if RE_COMMA_ABRO.match(ftext)
                      else 'COMMA-NUOVO-NORMATTIVA')
            F.append(dict(art=lab, comma=num, classe=classe,
                          sito=None, norm=ftext[:300], diff=None))
            if classe == 'COMMA-NUOVO-NORMATTIVA':
                art_clean = False
        if art_clean:
            n_art_ok += 1
    for lab in sorted(m_b, key=artkey):
        if lab in m_a:
            continue
        f = m_b[lab]
        if f['tomb']:
            n_art_ok += 1; continue
        F.append(dict(art=lab, comma=None, classe='ARTICOLO-NUOVO-NORMATTIVA',
                      sito=None, norm=(f['rubrica'] or '')[:200], diff=None))
    stats = dict(articoli_ok=n_art_ok, commi_ok=n_comma_ok, abrogazioni_ok=n_abro_ok,
                 findings=len(F),
                 per_classe={c: sum(1 for x in F if x['classe'] == c)
                             for c in sorted({x['classe'] for x in F})})
    return F, stats

def run_act(act, freshdir):
    mod, folder, old_dir = load_builder(act)
    fdir = os.path.join(freshdir, act)
    manifest = json.load(open(os.path.join(fdir, 'fetch_manifest.json')))
    gate = manifest.get('consolidato_dl100')
    n_failed = manifest['n_discovered'] - manifest['n_ok']
    if n_failed:
        print('[%s] ATTENZIONE: %d articoli non scaricati' % (act, n_failed))

    mod.SRC = old_dir
    base_arts = mod.load_articles()
    site_arts = mod.load_articles()
    ams = json.load(open(os.path.join(ROOT, folder, 'amendments.json'),
                         encoding='utf-8'))['amendments']
    rep = mod.Report()
    mod.apply_amendments(site_arts, ams, rep)
    not_applied = [r for r in rep.rows if r[2] != 'applicata']
    if not_applied:
        print('[%s] ATTENZIONE: %d amendments non applicati puliti: %s'
              % (act, len(not_applied), [(r[0], r[2]) for r in not_applied]))
    mod.SRC = fdir
    fresh_arts = mod.load_articles()
    # dettaglio.html non e' un articolo: load_articles lo ignora (glob a_*.html)

    m_base = model(base_arts, mod, final=False)
    # init_segments per il sito e' fatto da apply_amendments (anche a lista vuota)
    m_site = model(site_arts, mod, final=True)
    m_fresh = model(fresh_arts, mod, final=False)

    FA, sa = compare(m_base, m_fresh, 'BASE')
    FB, sb = compare(m_site, m_fresh, 'SITO')
    akeys = {(x['art'], x['comma']) for x in FA}
    for x in FB:
        x['in_confronto_A'] = (x['art'], x['comma']) in akeys

    # fallback a livello di ARTICOLO: differenze di sola segmentazione dei commi
    by_art = {}
    for x in FB:
        by_art.setdefault(x['art'], []).append(x)
    for lab, items in by_art.items():
        if lab not in m_site or lab not in m_fresh:
            continue
        if not all(x['classe'] in SEG_CLASSES and x['comma'] for x in items):
            continue
        if lenient_join(m_site[lab]) == lenient_join(m_fresh[lab]):
            for x in items:
                x['classe'] = 'ok-segmentazione-commi'

    # whitelist di equivalenze verificate a mano (confronto_whitelist.json)
    wlp = os.path.join(ROOT, 'confronto_whitelist.json')
    if os.path.exists(wlp):
        for w in json.load(open(wlp, encoding='utf-8')):
            if w['act'] != act:
                continue
            for x in FB:
                if x['art'] == w['art'] and x['comma'] == w.get('comma'):
                    x['classe'] = 'equivalente-verificato'
                    x['motivo'] = w['motivo']

    sb['per_classe'] = {c: sum(1 for x in FB if x['classe'] == c)
                        for c in sorted({x['classe'] for x in FB})}
    sb['findings'] = len(FB)
    sb['aperti'] = sum(1 for x in FB if x['classe'].isupper() or x['classe'] == 'MISMATCH')

    out = dict(act=act, gate_consolidato_dl100=gate, failed_fetch=n_failed,
               stats_A=sa, stats_B=sb, findings_B=FB,
               findings_A_sintesi=[dict(art=x['art'], comma=x['comma'],
                                        classe=x['classe']) for x in FA])
    rdir = os.path.join(freshdir, 'reports')
    os.makedirs(rdir, exist_ok=True)
    json.dump(out, open(os.path.join(rdir, 'confronto_%s.json' % act), 'w'),
              ensure_ascii=False, indent=1)

    md = ['# Confronto %s — sito vs Normattiva (%s)' % (act, os.path.basename(freshdir)),
          '', 'Gate consolidamento d.l. 100: **%s** — fetch falliti: %d' % (gate, n_failed),
          '', '## B) SITO (finale) vs NORMATTIVA vigente — la verifica di verita\'', '',
          'Articoli ok: %(articoli_ok)d — commi identici: %(commi_ok)d — '
          'abrogazioni riscontrate: %(abrogazioni_ok)d — findings: %(findings)d' % sb,
          '', 'Per classe: `%s`' % json.dumps(sb['per_classe'], ensure_ascii=False), '']
    for x in FB:
        md.append('### art. %s%s — %s%s' % (
            x['art'], (' comma ' + x['comma']) if x['comma'] else '',
            x['classe'], ' *(anche nel confronto A)*' if x['in_confronto_A'] else ''))
        if x['diff']:
            md.append('\n> ' + x['diff'] + '\n')
        else:
            if x['sito'] is not None: md.append('- SITO: %s' % x['sito'])
            if x['norm'] is not None: md.append('- NORMATTIVA: %s' % x['norm'])
        md.append('')
    md += ['## A) BASE (giugno) vs NORMATTIVA vigente — cosa e\' cambiato su Normattiva', '',
           'Findings: %d — per classe: `%s`' % (sa['findings'],
           json.dumps(sa['per_classe'], ensure_ascii=False)), '']
    for x in FA:
        md.append('- art. %s%s — %s' % (x['art'],
                  (' comma ' + x['comma']) if x['comma'] else '', x['classe']))
    open(os.path.join(rdir, 'confronto_%s.md' % act), 'w').write('\n'.join(md))
    print('[%s] B: %d findings %s | A: %d findings | report scritti' %
          (act, sb['findings'], json.dumps(sb['per_classe'], ensure_ascii=False),
           sa['findings']))
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--act', default=','.join(BUILDERS))
    ap.add_argument('--freshdir', default='nm_fresh_20260710')
    args = ap.parse_args()
    freshdir = os.path.join(ROOT, args.freshdir)
    for act in [a.strip() for a in args.act.split(',') if a.strip()]:
        run_act(act, freshdir)

if __name__ == '__main__':
    main()
