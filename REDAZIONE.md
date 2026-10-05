# Redazione delle schede e del nastro

Regole vincolanti per chi scrive o corregge una scheda di `content/giurisprudenza/` o
`content/circolari/` e il nastro `_data/updates.js`, a mano o dalla routine settimanale.
La struttura dei file è nel `README.md`, le traduzioni in `TRADUZIONI.md`.

## 1. Registro

Le schede sono documenti giuridici, non post: le legge un avvocato che deve decidere se e come
spendere quel precedente. Niente colloquialismi, niente tono da newsletter.

| no | sì |
|---|---|
| `## Il pezzo immediatamente utile: come si prova…` | `## La prova della data della manifestazione di volontà` |
| «Tradotto per chi deposita: la comunicazione prefettizia…» | «Sul piano probatorio: la comunicazione prefettizia…» |
| «è quella su cui i ricorsi del filone si giocano» | «è il punto su cui si decide l'applicazione del regime transitorio» |
| «il decreto spiega perché basta» | «il decreto motiva perché è sufficiente» |

- **Mai «chi deposita» o «chi difende»**: si scrive «la difesa» o «il difensore».
- «vale la pena», «conviene», «da non perdere»: con parsimonia. Un'osservazione utile si scrive
  come rilievo, non come consiglio.
- I titoli `##` descrivono il contenuto giuridico («La prova della data», «La disciplina
  applicabile», «L'esito processuale»), non sono ganci («Il fatto che regge tutto»).

## 2. Il sito è autonomo: niente fonte, sì avvertenze

- **Non nominare mai ASGI né le liste** e non presentare il materiale come «diffuso in lista».
- **Mai la provenienza del provvedimento**: né lista, né Osservatorio, né «reso disponibile dalla
  difesa», né lo stato dell'anonimizzazione. Niente «Nota sulla fonte», niente blockquote in coda.
  Fonte e anonimizzazione vanno nel report di revisione.
- **Obbligatorio invece segnalare i dati che non vengono dal provvedimento** (nazionalità, date,
  fatti presi dalla comunicazione di accompagnamento): «dati riferiti dalla difesa e non desumibili
  dal testo del decreto». È un'avvertenza sull'attendibilità, non un'indicazione di provenienza.
- ASGI come **parte processuale** o autore di un documento è un fatto della causa: si può scrivere,
  ma solo dopo conferma di Alberto.

## 3. Misura: massima più analisi breve

La scheda non è l'esegesi del provvedimento: massima nel frontmatter e commento che dica che cosa
ha deciso, su quale argomento, che cosa se ne ricava e come si colloca rispetto alle decisioni già
pubblicate. Il resto è nel PDF linkato.

**Corpo: 300-450 parole**, salvo decisioni davvero eccezionali (le schede fino a settembre 2026
hanno mediana 929 parole: sono il metro di ciò che non va rifatto). Si taglia così:

- una citazione testuale per punto, la più densa;
- niente parafrasi di un passaggio appena citato;
- i richiami ad altre schede come rinvio secco, non come riassunto;
- le questioni che il provvedimento non affronta, in una riga.

## 4. Frontmatter

- **`corte:` solo l'autorità**: `"Tribunale di Bologna"`, `"Corte di cassazione"`,
  `"T.A.R. Lombardia — Milano"`, `"Corte d'Appello di Palermo"`. Niente sezione. Se la sezione dice
  qualcosa di sostanziale (tipicamente la **feriale**, che spiega un giudice non tabellare), va
  nel corpo.
- **`temi:` solo le label di `_data/vocabolarioTemi.js`** (le verifica `npm run temi-check`, che
  gira dentro `npm run build`); almeno un tema per scheda. Non inventare label: scegli la più
  prossima e, se è stretta, segnalalo nel report.
- ⚠️ **«Attuazione italiana» solo per la dottrina, mai per la giurisprudenza**: ogni decisione
  applica l'attuazione italiana, quindi il tema non distinguerebbe nulla. Per la giurisprudenza il
  tema sostanziale (`Procedura di frontiera`, `Trattenimento`, `Garanzie procedurali`,
  `Screening`…) o `Regime transitorio` se il punto è la successione delle discipline.
- `date`, `numero` (R.G.) e nome file si prendono **dal PDF**, mai dalla mail o dall'elenco
  dell'Osservatorio (che spesso indica la data di deposito).

## 5. Citazioni normative nel corpo

Le citazioni nel corpo e nella massima diventano in build link al testo interattivo con anteprima
(`scripts/norme-linker.js`). **Non scrivere link Markdown alle norme**: basta la forma canonica.
Il box «Norme collegate» (`norme:` nel frontmatter) resta a mano.

- **UE**: `art. 42, par. 1, lett. j) Reg. (UE) 2024/1348`; atti del Patto `Reg. (UE) 2024/1346`…`1359`
  e `Dir. (UE) 2024/1346`; atti esterni nel bundle (`direttiva 2013/32/UE`, `Reg. (UE) 2016/399`,
  `direttiva 2008/115`); `considerando 17 Reg. (UE) 2024/1348`. Le varianti brevi (`Reg. 1348`,
  «Regolamento procedure»…) sono tollerate, ma nelle schede nuove si usa la forma piena.
- **Italiane**: `art. 35-bis, comma 3, d.lgs. 25/2008`; `d.lgs. 142/2015`, `d.lgs. 286/1998`
  (anche «t.u. immigrazione»/«TUI»), `d.lgs. 251/2007`. Suffissi col trattino (`28-bis`, anche
  `28-*bis*`), `comma 2-bis`, `lett. b-bis)`.
- **Elenchi**: `artt. 5-ter, 5-quater e 5-quinquies d.lgs. 142/2015` → un link per articolo.
  Niente intervalli («artt. 20-21»): `artt. 20, 21 e 53`.
- `d.l. 100/2026` non ha testo interattivo: rimanda a `/circolari/dl-100-2026.html`, senza
  anteprima; nel frontmatter `norme:` usa quell'href.
- Restano testo, ed è corretto: `c.p.c.`, `Cost.`, `CEDU`, `d.l. 13/2017`, `Reg. (UE) 2026/464`
  e ogni atto senza testo nel bundle.

**Citazioni senza atto** («l'art. 43, par. 1, richiama…») si risolvono sul contesto: candidati
sono gli atti citati nel testo (anche quelli senza testo interattivo: se vince uno di questi, resta
testo), filtrati per tipo («par.» ⇒ UE, «comma» o `-bis` ⇒ italiana) e per esistenza
dell'articolo; poi, nell'ordine: l'articolo è fra le `norme:` del frontmatter; l'atto è citato nello
stesso paragrafo; è il più vicino (prima chi precede). Se resta ambiguo, testo.

Regola pratica: **cita l'atto la prima volta in ogni paragrafo** e metti in `norme:` gli articoli
che poi abbrevi. Se una citazione resta ambigua, non aggiungere un link a mano: rendi esplicito
l'atto. «art. N non trovato in …» è quasi sempre un refuso o un articolo abrogato: verifica sul
PDF. Per una scheda il cui oggetto è un atto senza testo interattivo, `norme_impliciti: false`
spegne la risoluzione dal contesto.

Controllo: `npm run norme-check` (0 non risolte, 0 href rotti); per le schede nuove
`NORME_VERBOSE=1 npm run norme-check <file>` e rileggi le righe «dal contesto» una per una.

## 6. Il nastro «Ultimi aggiornamenti» — `_data/updates.js`

Il commento in testa a `updates.js` è la fonte di verità sulla meccanica. In sintesi:

- **5 voci**, ordine di data del provvedimento decrescente, **una sola voce per filone**; entra
  una novità, esce l'ultima. Circolari e D.M. concorrono per lo stesso posto. Una decisione più
  vecchia di tutte le voci in vetrina, o di un filone già presente, non entra (dillo nel report).
- **`text`: 120-125 caratteri, soffitto 130.** È voluto che la voce non stia tutta nella finestra:
  non comprimere a ~95.
- `en` e `fr` rispecchiano `it` voce per voce, con `href` prefissati `/en` e `/fr`.

**Registro** — italiano giuridico formale, forma `Corte: premessa, conseguenza`; per gli atti
`Nuovo D.M. X: inclusi A e B, istituite N sezioni di C`.

- Nomina l'attore concreto: «per inerzia della **Questura**», non «per colpa dell'Amministrazione».
- Forma nominalizzata: «non ha **effetto sanante**», non «non sana».
- Termine tecnico: procedure «**instaurate**», «il **provvedimento**», «la **disciplina
  pre-Patto**», «il **rito previgente**».
- Afferma la regola, non limitarti a negarla: «valgono le norme vigenti al momento della
  manifestazione di volontà».
- Niente ellissi: «prima della **pubblicazione in G.U.**», «sezioni **delle Commissioni
  territoriali**».
- Di' con precisione il vizio: «richiama un articolo del Regolamento **senza indicarne il numero**».
- Principi in forma condizionale: «**se** la Commissione ha applicato la disciplina pre-Patto, il
  ricorso segue il rito previgente **ed è tempestivo**».

Campione di calibrazione — rileggilo prima di scrivere una voce:

```
[121] date: '4 settembre 2026'
      Trib. Bologna: C3 tardivo per inerzia della Questura, valgono le norme vigenti
      al momento della manifestazione di volontà

[124] date: '20 agosto 2026'
      Trib. Trieste: il D.M. zone di frontiera non ha effetto sanante sulle procedure
      instaurate prima della pubblicazione in G.U.

[125] date: '19 agosto 2026'
      Trib. Roma: sospeso il trasferimento Dublino, il provvedimento richiama un
      articolo del Regolamento senza indicarne il numero

[122] date: '17 agosto 2026'
      Trib. Perugia: se la Commissione ha applicato la disciplina pre-Patto, il ricorso
      segue il rito previgente ed è tempestivo

[121] date: 'in G.U. il 10 agosto 2026'
      Nuovo D.M. zone di frontiera: inclusi valichi Schengen e porti, istituite 19
      nuove sezioni delle Commissioni territoriali
```

Il contenuto della voce si legge dal provvedimento: la sintesi breve è il punto in cui è più
facile far dire a una decisione ciò che non dice.
