#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fetcher riusabile per gli snapshot Normattiva del progetto PATTO UE.

Per ogni atto: handshake cookie -> pagina di dettaglio multivigenza in modalita'
"classica" (toggle di SESSIONE: senza, caricaArticolo risponde con l'HTML AKN-div
senza <pre>) -> scoperta dell'elenco articoli DALLA PAGINA FRESCA (mai dalla lista
di giugno: il d.l. 100/2026 ha creato articoli nuovi) -> download di ogni articolo
alla MASSIMA art.versione -> manifest con sha256 e validazione.

Uso:
  python3 fetch_normattiva.py                       # tutti gli atti
  python3 fetch_normattiva.py --act dlgs25,dl100    # subset
  python3 fetch_normattiva.py --force               # rifetch anche se gia' scaricato
  python3 fetch_normattiva.py --outdir nm_fresh_X   # default nm_fresh_YYYYMMDD (oggi)

File scaricati: <outdir>/<act>/a_{idGruppo}_{idArticolo}_{idSottoArticolo}.html
(stesso schema degli snapshot esistenti, cosi' load_articles() dei builder
funziona senza adattatori), piu' dettaglio.html e fetch_manifest.json.
"""
import argparse, datetime, hashlib, html, json, os, re, sys, time
import urllib.request, urllib.parse
from http.cookiejar import CookieJar

BASE = 'https://www.normattiva.it'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
RATE = 1.5          # secondi tra le richieste
TIMEOUT = 40

ACTS = {
    'dlgs25':  dict(codice='008G0044', gu='2008-02-16', old_dir='nm_html',
                    urn='urn:nir:stato:decreto.legislativo:2008-01-28;25',
                    expected_new=['26-bis', '26-ter', '28-bis.1', '28-bis.2']),
    'dlgs142': dict(codice='15G00158', gu='2015-09-15', old_dir='nm_html_142',
                    urn='urn:nir:stato:decreto.legislativo:2015-08-18;142',
                    expected_new=['5-ter', '5-quater', '5-quinquies', '5-sexies', '6-quater']),
    'dlgs286': dict(codice='098G0348', gu='1998-08-18', old_dir='nm_html_286',
                    urn='urn:nir:stato:decreto.legislativo:1998-07-25;286',
                    expected_new=['10-quater', '14.1']),
    'dlgs251': dict(codice='007G0259', gu='2008-01-04', old_dir='nm_html_251',
                    urn='urn:nir:stato:decreto.legislativo:2007-11-19;251',
                    expected_new=[]),
    'dl100':   dict(codice='26G00119', gu='2026-06-12', old_dir=None,
                    urn='urn:nir:stato:decreto.legge:2026-06-12;100',
                    expected_new=[]),
    # d.lgs. 115/2026 (tratta, dir. 2024/1712): novella artt. 17 d.lgs. 142, 32 d.lgs. 25, 18 d.lgs. 286
    'dlgs115': dict(codice='26G00130', gu='2026-07-01', old_dir=None,
                    urn='urn:nir:stato:decreto.legislativo:2026-06-12;115',
                    expected_new=[]),
    # d.l. 168/2026: art. 4 novella l'art. 17 d.l. 100/2026 (regime transitorio, documento del richiedente)
    'dl168':   dict(codice='26G00188', gu='2026-09-29', old_dir=None,
                    urn='urn:nir:stato:decreto.legge:2026-09-29;168',
                    expected_new=[]),
}

ROOT = os.path.dirname(os.path.abspath(__file__))

def make_opener():
    jar = CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    op.addheaders = [('User-Agent', UA), ('Accept-Language', 'it-IT,it;q=0.9'),
                     ('Accept', 'text/html,application/xhtml+xml,*/*;q=0.8')]
    return op

def get(op, url, referer=None, attempts=4):
    """GET con retry/backoff: il server Normattiva chiude connessioni a caso
    (SSL EOF / RemoteDisconnected) nei periodi di instabilita'."""
    last = None
    for i in range(attempts):
        try:
            req = urllib.request.Request(url)
            if referer:
                req.add_header('Referer', referer)
            with op.open(req, timeout=TIMEOUT) as r:
                return r.read()
        except Exception as e:
            last = e
            wait = 5 * (i + 1)
            print('  retry %d/%d fra %ds (%s)' % (i + 1, attempts - 1, wait, e))
            time.sleep(wait)
    raise last

def detail_url(a):
    return (BASE + '/atto/caricaDettaglioAtto?atto.dataPubblicazioneGazzetta=%s'
            '&atto.codiceRedazionale=%s&tipoDettaglio=multivigenza&classica=true'
            % (a['gu'], a['codice']))

def discover_articles(detail_html):
    """Estrae gli URL caricaArticolo dalla pagina di dettaglio; per ciascun
    (idGruppo,idArticolo,idSottoArticolo) tiene la MASSIMA art.versione,
    preservando l'ordine di prima apparizione."""
    txt = html.unescape(detail_html)
    seen = {}
    order = []
    for m in re.finditer(r'/atto/caricaArticolo\?[^"\'\s<>]+', txt):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(m.group(0)).query)
        try:
            g = int(q['art.idGruppo'][0]); a = int(q['art.idArticolo'][0])
            s = int(q['art.idSottoArticolo'][0]); v = int(q['art.versione'][0])
            # gli articoli DECIMALI (28-bis.1, 35-bis.2, ...) condividono
            # idArticolo/idSottoArticolo col padre e si distinguono SOLO per
            # idSottoArticolo1: 10 = normale, 20 = .1, 30 = .2, 40 = .3 ...
            s1 = int(q.get('art.idSottoArticolo1', ['10'])[0])
        except (KeyError, ValueError):
            continue
        key = (g, a, s, s1)
        if key not in seen:
            order.append(key)
            seen[key] = (v, m.group(0))
        elif v > seen[key][0]:
            seen[key] = (v, m.group(0))
    return [(k, seen[k][0], seen[k][1]) for k in order]

def pre_label(body):
    """Estrae il label 'Art. N' dal <pre> principale (validazione leggera,
    volutamente indipendente dai builder)."""
    d = re.sub(r'(?s)<(script|style)[^>]*>.*?</\1>', ' ', body)
    for p in re.findall(r'(?s)<pre[^>]*>(.*?)</pre>', d):
        t = html.unescape(re.sub(r'(?s)<[^>]+>', '', p)).lstrip()
        m = re.match(r'Art\.\s*(\d{1,3}(?:-\w+)?(?:\.\d+)?)', t)
        if m:
            return m.group(1)
    return None

def valid_article(body):
    return '<pre' in body and 'Art.' in body

def vigore_dal(body):
    """Data 'Testo in vigore dal' della versione servita (None se assente)."""
    t = re.sub(r'(?s)<[^>]+>', ' ', body)
    m = re.search(r'Testo in vigore dal:\s*(\d{1,2})-(\d{1,2})-(\d{4})', t)
    if not m:
        return None
    return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))

def fetch_walk(op, url, durl, adir, fn, today):
    """Scarica l'articolo alla versione in vigore OGGI: Normattiva pubblica anche
    versioni a decorrenza FUTURA (es. d.lgs. 115/2026, in vigore 16-7-2026) e la
    max versione puo' non essere ancora applicabile. Se la versione e' futura la
    salva come future_<fn> e scende di versione finche' vigore_dal <= oggi."""
    future_info = None
    v = int(re.search(r'art\.versione=(\d+)', url).group(1))
    for _ in range(6):
        raw = get(op, url, referer=durl)
        b = raw.decode('utf-8', 'replace')
        if not valid_article(b):
            return None, future_info
        dal = vigore_dal(b)
        if dal and dal > today and v > 1:
            if not future_info:
                open(os.path.join(adir, 'future_' + fn), 'wb').write(raw)
                future_info = dal.isoformat()
            v -= 1
            url = re.sub(r'art\.versione=\d+', 'art.versione=%d' % v, url)
            time.sleep(RATE)
            continue
        return dict(raw=raw, body=b, versione=v,
                    vigore_dal=dal.isoformat() if dal else None), future_info
    return None, future_info

def sha256(b):
    return hashlib.sha256(b).hexdigest()

def fetch_act(op, act, cfg, outdir, force):
    adir = os.path.join(outdir, act)
    os.makedirs(adir, exist_ok=True)
    durl = detail_url(cfg)
    print('[%s] dettaglio: %s' % (act, durl))
    raw = get(op, durl)
    body = raw.decode('utf-8', 'replace')
    open(os.path.join(adir, 'dettaglio.html'), 'wb').write(raw)
    arts = discover_articles(body)
    if not arts:
        # fallback: risolvi via URN e riprova la detail classica
        print('[%s] nessun articolo nella detail: fallback URN' % act)
        get(op, BASE + '/uri-res/N2Ls?%s!multivigente' % cfg['urn'], referer=BASE + '/')
        time.sleep(RATE)
        raw = get(op, durl)
        body = raw.decode('utf-8', 'replace')
        open(os.path.join(adir, 'dettaglio.html'), 'wb').write(raw)
        arts = discover_articles(body)
    print('[%s] articoli scoperti: %d' % (act, len(arts)))

    # precheck vs snapshot vecchio: nessun articolo scomparso
    warn = []
    if cfg['old_dir']:
        old = set()
        for f in os.listdir(os.path.join(ROOT, cfg['old_dir'])):
            m = re.match(r'a_(\d+)_(\d+)_(\d+)\.html$', f)
            if m:
                old.add((int(m.group(2)), int(m.group(3))))   # (idArticolo, idSottoArticolo)
        new = {(a, s) for (g, a, s, s1), _, _ in arts if s1 == 10}
        gone = old - new
        if gone:
            warn.append('articoli del vecchio snapshot assenti dal fresh: %s' % sorted(gone))
        print('[%s] vecchio snapshot: %d articoli; fresh: %d; scomparsi: %d'
              % (act, len(old), len(new), len(gone)))

    manifest = dict(act=act, detail_url=durl, fetched=datetime.datetime.now().isoformat(),
                    n_discovered=len(arts), warnings=warn, files=[])
    labels = []
    today = datetime.date.today()
    for (g, a, s, s1), v, path in arts:
        # s1==10: schema classico compatibile con gli snapshot esistenti;
        # articoli decimali: suffisso extra (fkey dei builder legge i primi 3 interi,
        # il label giuridico viene comunque dal testo)
        fn = 'a_%d_%d_%d.html' % (g, a, s) if s1 == 10 else 'a_%d_%d_%d_%d.html' % (g, a, s, s1)
        dest = os.path.join(adir, fn)
        url = BASE + path
        entry = dict(filename=fn, url=url, versione=v, ok=False, label=None)
        if os.path.exists(dest) and not force:
            b = open(dest, encoding='utf-8', errors='replace').read()
            dal = vigore_dal(b)
            if valid_article(b) and not (dal and dal > today):
                entry.update(ok=True, skipped=True, label=pre_label(b),
                             vigore_dal=dal.isoformat() if dal else None,
                             sha256=sha256(b.encode()))
                manifest['files'].append(entry)
                if entry['label']:
                    labels.append(entry['label'])
                continue
            if dal and dal > today:
                print('  [%s] %s: versione salvata con decorrenza futura (%s), rifetch'
                      % (act, fn, dal))
        for attempt in (1, 2, 3):
            try:
                time.sleep(RATE)
                got, future_info = fetch_walk(op, url, durl, adir, fn, today)
                if got:
                    open(dest, 'wb').write(got['raw'])
                    entry.update(ok=True, label=pre_label(got['body']),
                                 sha256=sha256(got['raw']), versione=got['versione'],
                                 vigore_dal=got['vigore_dal'])
                    if future_info:
                        entry['versione_futura_dal'] = future_info
                        print('  [%s] %s: esiste versione FUTURA (dal %s) -> future_%s'
                              % (act, fn, future_info, fn))
                    break
                print('  [%s] %s: risposta senza <pre> (tentativo %d)' % (act, fn, attempt))
                time.sleep(10)
            except Exception as e:
                print('  [%s] %s: %s (tentativo %d)' % (act, fn, e, attempt))
                time.sleep(15)
        manifest['files'].append(entry)
        if entry['label']:
            labels.append(entry['label'])
        if not entry['ok']:
            print('  [%s] FALLITO: %s' % (act, fn))

    n_ok = sum(1 for f in manifest['files'] if f['ok'])
    manifest['versioni_future'] = [dict(file=f['filename'], dal=f['versione_futura_dal'])
                                   for f in manifest['files'] if f.get('versione_futura_dal')]
    missing_new = [l for l in cfg['expected_new'] if l not in labels]
    manifest['n_ok'] = n_ok
    manifest['labels'] = labels
    manifest['expected_new'] = cfg['expected_new']
    manifest['missing_expected_new'] = missing_new
    manifest['consolidato_dl100'] = (not missing_new) if cfg['expected_new'] else None
    json.dump(manifest, open(os.path.join(adir, 'fetch_manifest.json'), 'w'),
              ensure_ascii=False, indent=1)
    print('[%s] scaricati %d/%d; expected_new mancanti: %s' %
          (act, n_ok, len(arts), missing_new or 'nessuno'))
    return manifest

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--act', default=','.join(ACTS))
    ap.add_argument('--outdir', default='nm_fresh_' + datetime.date.today().strftime('%Y%m%d'))
    ap.add_argument('--force', action='store_true')
    args = ap.parse_args()
    outdir = os.path.join(ROOT, args.outdir)
    os.makedirs(outdir, exist_ok=True)
    wanted = [a.strip() for a in args.act.split(',') if a.strip()]
    bad = [a for a in wanted if a not in ACTS]
    if bad:
        sys.exit('atti sconosciuti: %s (validi: %s)' % (bad, ', '.join(ACTS)))
    op = make_opener()
    print('handshake…')
    get(op, BASE + '/')
    time.sleep(RATE)
    results = {}
    for act in wanted:
        results[act] = fetch_act(op, act, ACTS[act], outdir, args.force)
    print('\n=== RIEPILOGO ===')
    for act, m in results.items():
        print('%-8s %3d/%3d ok  consolidato_dl100=%s  warn=%s'
              % (act, m['n_ok'], m['n_discovered'], m['consolidato_dl100'], m['warnings'] or '-'))

if __name__ == '__main__':
    main()
