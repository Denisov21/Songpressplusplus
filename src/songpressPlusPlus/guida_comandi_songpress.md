# Guida ai comandi di Songpress++

Songpress++ utilizza il formato **ChordPro** esteso. I comandi sono racchiusi tra parentesi graffe `{...}` e possono accettare un valore separato dai due punti `{comando: valore}`. Gli accordi si inseriscono tra parentesi quadre `[Accordo]` nel mezzo del testo. Le righe che iniziano con `#` sono commenti e vengono ignorate.

---

## Indice

1. [Struttura della canzone](#1-struttura-della-canzone)
   - [title / t](#title--t)
   - [subtitle / st](#subtitle--st)
   - [start_of_verse / end_of_verse](#start_of_verse--end_of_verse)
   - [start_verse / end_verse](#start_verse--end_verse)
   - [start_verse_num / end_verse_num](#start_verse_num--end_verse_num)
   - [start_of_chorus / end_of_chorus](#start_of_chorus--end_of_chorus)
   - [start_chorus / end_chorus](#start_chorus--end_chorus)
   - [start_of_bridge / end_of_bridge](#start_of_bridge--end_of_bridge)
   - [start_bridge / end_bridge](#start_bridge--end_bridge)
   - [start_chord / end_chord](#start_chord--end_chord)
   - [start_of_part / end_of_part](#start_of_part--end_of_part)
   - [verse](#verse)
   - [row / r](#row--r)
   - [new_song](#new_song)
2. [Tab e griglia accordi](#2-tab-e-griglia-accordi)
   - [start_of_tab / end_of_tab](#start_of_tab--end_of_tab)
   - [start_of_grid / end_of_grid](#start_of_grid--end_of_grid)
3. [Commenti e annotazioni](#3-commenti-e-annotazioni)
   - [comment / c](#comment--c)
   - [comment_italic / ci](#comment_italic--ci)
   - [comment_box / cb](#comment_box--cb)
4. [Metadati](#4-metadati)
   - [artist](#artist)
   - [composer](#composer)
   - [lyricist](#lyricist)
   - [arranger](#arranger)
   - [album](#album)
   - [year](#year)
   - [duration](#duration)
   - [ccli](#ccli)
   - [copyright](#copyright)
   - [key](#key)
   - [capo](#capo)
5. [Impaginazione](#5-impaginazione)
   - [new_page / np](#new_page--np)
   - [column_break / colb](#column_break--colb)
6. [Indicazioni musicali](#6-indicazioni-musicali)
   - [tempo](#tempo)
   - [tempo_m](#tempo_m)
   - [tempo_s](#tempo_s)
   - [tempo_c](#tempo_c)
   - [tempo_sp](#tempo_sp)
   - [tempo_cp](#tempo_cp)
   - [time](#time)
   - [beats_time](#beats_time)
7. [Formattazione del testo](#7-formattazione-del-testo)
   - [textsize](#textsize)
   - [textfont](#textfont)
   - [textcolour / textcolor](#textcolour--textcolor)
   - [linespacing](#linespacing)
8. [Formattazione degli accordi](#8-formattazione-degli-accordi)
   - [chordsize](#chordsize)
   - [chordfont](#chordfont)
   - [chordcolour / chordcolor](#chordcolour--chordcolor)
   - [chordtopspacing](#chordtopspacing)
9. [Diagrammi e immagini](#9-diagrammi-e-immagini)
   - [define](#define)
   - [taste](#taste)
   - [fingering](#fingering)
   - [image](#image)
10. [Accordi inline](#10-accordi-inline)
11. [Commenti di riga](#11-commenti-di-riga)
12. [Preferenze dell'applicazione](#12-preferenze-dellapplicazione)
    - [Scheda Generale](#scheda-generale)
    - [Scheda Correz. automatiche (AutoAdjust)](#scheda-correz-automatiche-autoadjust)
    - [Scheda Formato (Format)](#scheda-formato-format)
    - [Scheda Anteprima (Songpress++ Preview)](#scheda-anteprima-songpress-preview)
    - [Scheda Guida rapida (Quick guide)](#scheda-guida-rapida-quick-guide)
    - [Scheda Menu contestuale (Context menu)](#scheda-menu-contestuale-context-menu)
    - [Scheda Associazioni file (File associations)](#scheda-associazioni-file-file-associations)
    - [Impostazioni dal menu Formato](#impostazioni-dal-menu-formato)
13. [Sommario finale](#13-sommario-finale)

---

## 1. Struttura della canzone

### `title` / `t`

**Sintassi:** `{title: Titolo della canzone}` oppure `{t: Titolo}`

Imposta il titolo della canzone. Viene visualizzato in testa alla pagina con lo stile tipografico del titolo (font più grande, eventuale linea decorativa). È obbligatorio fornire un valore.

```chordpro
{title: Amazing Grace}
```

---

### `subtitle` / `st`

**Sintassi:** `{subtitle: Sottotitolo}` oppure `{st: Sottotitolo}`

Imposta il sottotitolo della canzone, visualizzato sotto il titolo con uno stile ridotto. Utile per indicare artista, tonalità originale o altre informazioni secondarie.

```chordpro
{subtitle: Traditional}
```

---

### `start_of_verse` / `end_of_verse`

**Sintassi:**
```chordpro
{start_of_verse: Etichetta}
...testo...
{end_of_verse}
```

Delimita una strofa. L'etichetta è opzionale: se omessa, la strofa riceve automaticamente un numero progressivo (1., 2., ecc.) in base all'impostazione "mostra etichette" di Songpress++. Le abbreviazioni sono `{sov}` e `{eov}`.

```chordpro
{sov: Strofa 1}
[C]Testo della [G]prima strofa
[Am]ancora testo [F]qui
{eov}
```

---

### `start_verse` / `end_verse`

**Sintassi:**
```chordpro
{start_verse: Etichetta opzionale}
...testo...
{end_verse}
```

Variante alternativa di `start_of_verse` / `end_of_verse`, introdotta come estensione Songpress++. Il comportamento è identico. Utile se si preferisce una sintassi più compatta.

---

### `start_verse_num` / `end_verse_num`

**Sintassi:**
```chordpro
{start_verse_num: Etichetta}
...testo...
{end_verse_num}
```

Come `start_verse`, ma **forza** la numerazione automatica anche se viene specificata un'etichetta. Se l'etichetta è vuota o assente, viene assegnato comunque il numero progressivo. Utilizzare quando si vuole garantire la numerazione indipendentemente dall'etichetta.

---

### `start_of_chorus` / `end_of_chorus`

**Sintassi:**
```chordpro
{start_of_chorus: Etichetta opzionale}
...testo del ritornello...
{end_of_chorus}
```

Delimita un ritornello. Il ritornello viene visualizzato con uno stile visivo distinto (riquadro, sfondo, etichetta configurabile tramite le preferenze di Songpress++). Le abbreviazioni sono `{soc}` e `{eoc}`.

```chordpro
{soc}
[G]Rit: testo del [D]ritornello
{eoc}
```

---

### `start_chorus` / `end_chorus`

**Sintassi:**
```chordpro
{start_chorus}
...testo...
{end_chorus}
```

Variante alternativa di `start_of_chorus` / `end_of_chorus`. Comportamento identico.

---

### `start_of_bridge` / `end_of_bridge`

**Sintassi:**
```chordpro
{start_of_bridge: Etichetta opzionale}
...testo del bridge...
{end_of_bridge}
```

Delimita un bridge. Viene trattato come una strofa speciale, con numerazione autonoma separata dalle strofe ordinarie. Le abbreviazioni sono `{sob}` e `{eob}`.

---

### `start_bridge` / `end_bridge`

**Sintassi:**
```chordpro
{start_bridge: Etichetta opzionale}
...testo...
{end_bridge}
```

Variante alternativa di `start_of_bridge` / `end_of_bridge`. Comportamento identico.

---

### `start_chord` / `end_chord`

**Sintassi:**
```chordpro
{start_chord: Etichetta opzionale}
...blocco...
{end_chord}
```

Crea un blocco generico di tipo strofa, con etichetta personalizzata. Utile per sezioni che non rientrano nelle categorie standard (es. intro, coda, assolo).

```chordpro
{start_chord: Intro}
[C] / / / | [G] / / /
{end_chord}
```

---

### `start_of_part` / `end_of_part`

**Sintassi:**
```chordpro
{start_of_part: Etichetta opzionale}
...testo...
{end_of_part}
```

Sezione generica conforme a **ChordPro 6**. Trattata esattamente come `start_chord` / `end_chord`: crea un blocco strofa con l'etichetta indicata, non numerato automaticamente. Se l'etichetta è omessa, viene usata l'etichetta predefinita `Part`. Le abbreviazioni sono `{sop}` e `{eop}`.

```chordpro
{sop: Outro}
[Em]Testo della sezione finale
{eop}
```

---

### `verse`

**Sintassi:** `{verse: Etichetta}`

Aggiunge un riferimento a una strofa già definita. In Songpress++ viene trattato come l'apertura di un nuovo blocco strofa con l'etichetta indicata. Usato raramente: preferire `start_of_verse`.

---

### `row` / `r`

**Sintassi:** `{row}` oppure `{r}`

Inserisce una **riga separatrice vuota** tra sezioni, senza creare un nuovo blocco. Aggiunge spazio visivo verticale di mezza riga. Può essere usato anche **all'interno di un blocco `{start_of_grid}`** per separare gruppi di righe della griglia.

```chordpro
{sov}
Testo prima parte
{row}
Testo seconda parte
{eov}
```

---

### `new_song`

**Sintassi:** `{new_song}`

Reimposta completamente lo stato del renderer: azzera i contatori di strofe, ritornelli e etichette, e ripristina i font e i colori ai valori predefiniti. Utile quando si concatenano più canzoni in un unico file ChordPro o si usa `{start_of_grid}` su documenti multi-canzone.

---

## 2. Tab e griglia accordi

### `start_of_tab` / `end_of_tab`

**Sintassi:**
```chordpro
{start_of_tab: Etichetta opzionale}
...testo ASCII...
{end_of_tab}
```

Delimita un blocco di tablatura ASCII. All'interno del blocco:
- Viene usato automaticamente un **font monospace** (es. Courier New).
- Gli accordi tra `[...]` vengono **soppressi**: il blocco è già notazione completa.
- Il testo viene visualizzato esattamente così com'è, preservando spazi e allineamento.
- Le abbreviazioni sono `{sot}` e `{eot}`.

```chordpro
{sot: Fingerpicking}
e|---0---2---3---|
B|---1---3---0---|
G|---0---2---0---|
{eot}
```

---

### `start_of_grid` / `end_of_grid`

**Sintassi:**
```chordpro
{start_of_grid: Etichetta [size=N] [chordtopspacing=N] [linespacing=N]}
...righe di accordi...
{end_of_grid}
```

Delimita un blocco **griglia accordi** (schema armonico per battute). Le abbreviazioni sono `{sog}` / `{eog}` e anche il solo `{grid}` apre il blocco.

**Parametri opzionali nella direttiva di apertura:**

| Parametro | Descrizione | Esempio |
|---|---|---|
| `size=N` | Moltiplicatore dimensione celle (default: 1). Accetta decimali. | `size=2` |
| `sizedir=horizontal\|vertical\|both` | Direzione a cui si applica `size=`: orizzontale, verticale o entrambe (default: valore dalle preferenze, solitamente `both`) | `sizedir=horizontal` |
| `chordtopspacing=N` | Spazio extra in pixel sopra ogni riga della griglia | `chordtopspacing=10` |
| `linespacing=N` | Spazio extra in pixel sotto ogni riga della griglia | `linespacing=8` |
| Etichetta libera | Testo dell'etichetta del blocco (dopo i parametri key=value) | `size=2 Ritornello` |

**Formato delle righe all'interno del blocco:**

*Formato pipe* (predefinito): le battute sono separate da `|`. Gli accordi possono essere scritti come testo semplice o tra `[...]`.

```chordpro
{sog: size=1.5 Armonia}
C | G | Am | F
C | G | F  | F
{eog}
```

*Formato plain* (solo spazi): le battute sono separate da spazio. La larghezza proporzionale è calcolata automaticamente in base alla lunghezza del testo.

```chordpro
{sog}
C  G  Am F
{eog}
```

**Modalità di visualizzazione** (configurabile nelle preferenze):
- `pipe` — tabella con separatori `|` visibili
- `plain` — celle affiancate senza bordi
- `table` — tabella con bordi grafici

**Uso di `{row}` / `{r}` dentro il blocco:** inserisce una riga vuota separatrice tra gruppi di battute.

```chordpro
{sog}
C | G | Am | F
{r}
F | C | G  | G
{eog}
```

---

## 3. Commenti e annotazioni

### `comment` / `c`

**Sintassi:** `{comment: Testo}` oppure `{c: Testo}`

Inserisce un commento visibile nell'anteprima, in stile normale. Utile per annotazioni esecutive (es. "D.C. al Coda", "con pedale", "ritardando"). Il testo viene visualizzato nel flusso della canzone, distinto dal testo cantato.

```chordpro
{c: Ripeti 2 volte}
```

---

### `comment_italic` / `ci`

**Sintassi:** `{comment_italic: Testo}` oppure `{ci: Testo}`

Come `comment`, ma il testo viene visualizzato in **corsivo**. Usato tipicamente per indicazioni dinamiche o espressive.

```chordpro
{ci: Piano, con delicatezza}
```

---

### `comment_box` / `cb`

**Sintassi:** `{comment_box: Testo}` oppure `{cb: Testo}`

Come `comment`, ma il testo viene racchiuso in un **riquadro grafico** per evidenziarlo maggiormente. Usato per sezioni importanti o avvertenze.

```chordpro
{cb: CODA}
```

---

## 4. Metadati

I metadati vengono memorizzati nella canzone ma **non appaiono visivamente nell'anteprima** come elementi separati (eccetto `title`, `subtitle`, `key`, `capo`). Sono inclusi nei formati di esportazione che li supportano.

> **Metadati ChordPro 6 ignorati silenziosamente:** i seguenti comandi sono riconosciuti e consumati dal renderer senza generare errori, ma non producono alcun output visivo né vengono esportati: `{sorttitle}`, `{keywords}`, `{topic}`, `{collection}`, `{language}`, `{pagetype}`, `{columns}`, `{meta}`, `{transpose}`. Possono essere inclusi nel file per compatibilità con altri editor ChordPro senza effetti collaterali.

### `artist`

**Sintassi:** `{artist: Nome artista}`

Nome dell'artista o del gruppo che esegue la canzone.

```chordpro
{artist: The Beatles}
```

---

### `composer`

**Sintassi:** `{composer: Nome compositore}`

Nome del compositore della musica (può differire dall'artista esecutore).

```chordpro
{composer: John Lennon}
```

---

### `lyricist`

**Sintassi:** `{lyricist: Nome paroliere}`

Nome dell'autore del testo (paroliere), quando diverso dal compositore della musica. Viene visualizzato nell'anteprima come sottotitolo con il prefisso **`Testo:`**.

```chordpro
{lyricist: Paul McCartney}
```

> Visualizzato come: *Testo: Paul McCartney*

---

### `arranger`

**Sintassi:** `{arranger: Nome arrangiatore}`

Nome dell'arrangiatore. Viene visualizzato nell'anteprima come sottotitolo con il prefisso **`Arrangiamento:`**.

```chordpro
{arranger: George Martin}
```

> Visualizzato come: *Arrangiamento: George Martin*

---

### `album`

**Sintassi:** `{album: Titolo album}`

Titolo dell'album di provenienza della canzone.

```chordpro
{album: Abbey Road}
```

---

### `year`

**Sintassi:** `{year: Anno}`

Anno di pubblicazione o composizione.

```chordpro
{year: 1969}
```

---

### `duration`

**Sintassi:** `{duration: Durata}`

Durata della canzone. Il formato consigliato è `mm:ss` (es. `3:45`), ma il campo accetta qualsiasi stringa testuale. **Metadato di sola memorizzazione**: il valore viene consumato silenziosamente dal renderer e non appare nell'anteprima né in stampa. Può essere incluso nel file per compatibilità con altri editor ChordPro o per uso esterno (esportatori, database).

```chordpro
{duration: 3:45}
{duration: 4:28}
```

> Per associare durate in battiti ai singoli accordi di una riga, usare invece `{beats_time:}` (sezione 6).

---

### `ccli`

**Sintassi:** `{ccli: Numero}`

Numero di licenza **CCLI** (Christian Copyright Licensing International), usato in ambito liturgico/corale per tracciare i brani coperti da licenza CCLI. Metadato di sola memorizzazione, non visualizzato nell'anteprima.

```chordpro
{ccli: 1234567}
```

---

### `copyright`

**Sintassi:** `{copyright: Testo copyright}`

Informazioni sul copyright. Obbligatorio fornire un valore non vuoto.

```chordpro
{copyright: © 1969 Northern Songs}
```

---

### `key`

**Sintassi:** `{key: Tonalità}`

Indica la **tonalità** della canzone. Il valore viene visualizzato nell'anteprima (se l'opzione "Mostra tonalità" è attiva nelle preferenze). Supporta la notazione italiana (Do, Re, Mi…) e inglese (C, D, E…) con alterazioni (`#`, `b`).

```chordpro
{key: La minore}
{key: Am}
{key: F#}
```

---

### `capo`

**Sintassi:** `{capo: N}`

Indica la posizione del **capotasto** (barrè). Il valore N è il numero del tasto. Viene visualizzato nell'anteprima come indicazione testuale.

```chordpro
{capo: 3}
```

---

## 5. Impaginazione

### `new_page` / `np`

**Sintassi:** `{new_page}` oppure `{np}`

Forza un **salto di pagina** nel punto in cui compare. Nella stampa e nell'anteprima la canzone viene spezzata esattamente in quel punto. Particolarmente utile per canzoni lunghe o per il canzoniere multi-pagina.

```chordpro
{sov: Strofa 1}
...
{eov}
{new_page}
{sov: Strofa 2}
...
{eov}
```

> **Nota:** Le righe commentate con `#` che contengono `{new_page}` vengono ignorate e non producono alcun salto.

---

### `column_break` / `colb`

**Sintassi:** `{column_break}` oppure `{colb}`

Forza un **salto di colonna** quando la stampa è configurata in modalità multi-colonna. Il blocco successivo viene posizionato all'inizio della colonna seguente. Se la stampa è a colonna singola, l'effetto è equivalente a un salto di pagina.

```chordpro
{sov: Strofa 1}
...
{eov}
{colb}
{sov: Strofa 2}
...
{eov}
```

---

## 6. Indicazioni musicali

Le indicazioni di tempo vengono visualizzate nell'anteprima secondo la modalità scelta nelle preferenze (*Strumenti → Preferenze → Anteprima → Visualizzazione tempo*):

| Modalità | Descrizione |
|---|---|
| `0` (testo) | Mostra il valore numerico come testo (es. "♩ = 120") |
| `1` (nota grafica) | Mostra l'icona della nota + il valore numerico |
| `2` (solo testo) | Mostra solo il numero senza simbolo |
| `3` (metronomo) | Mostra un'icona a forma di metronomo |
| `-1` (nascosto) | Il metadato è memorizzato ma non visualizzato |

---

### `tempo`

**Sintassi:** `{tempo: N}`

Indica il **tempo** in BPM riferito alla **semiminima** (♩ = N). È il comando di tempo più comune.

```chordpro
{tempo: 120}
```

---

### `tempo_m`

**Sintassi:** `{tempo_m: N}`

Tempo riferito alla **minima** (𝅗𝅥 = N). Usato per i brani in 2/2 (alla breve).

```chordpro
{tempo_m: 60}
```

---

### `tempo_s`

**Sintassi:** `{tempo_s: N}`

Sinonimo di `tempo`: tempo riferito alla **semiminima** (♩ = N). Utile per disambiguare quando si usano più indicazioni di tempo nello stesso file.

```chordpro
{tempo_s: 96}
```

---

### `tempo_c`

**Sintassi:** `{tempo_c: N}`

Tempo riferito alla **croma** (♪ = N). Usato per brani in 6/8, 9/8, 12/8.

```chordpro
{tempo_c: 176}
```

---

### `tempo_sp`

**Sintassi:** `{tempo_sp: N}`

Tempo riferito alla **semiminima puntata** (♩. = N). Comune nei brani composti in tempo ternario semplice.

```chordpro
{tempo_sp: 72}
```

---

### `tempo_cp`

**Sintassi:** `{tempo_cp: N}`

Tempo riferito alla **croma puntata** (♪. = N).

```chordpro
{tempo_cp: 116}
```

---

### `time`

**Sintassi:** `{time: N/D}`

Indica il **metro** della canzone (indicazione di misura). N è il numero di tempi per battuta, D il valore della figura di riferimento. Viene visualizzato nell'anteprima (se l'opzione "Mostra metro" è attiva).

```chordpro
{time: 4/4}
{time: 3/4}
{time: 6/8}
```

---

### `beats_time`

**Sintassi:** `{beats_time: ACCORDO=battiti ACCORDO=battiti ...}`

Associa un numero di **battiti** a ciascun accordo della riga immediatamente successiva. I token hanno forma `ACCORDO=N`, dove `N` è un intero positivo. Gli accordi si indicano in maiuscolo; il bemolle si scrive con il trattino (`La-` = La♭).

L'associazione è **posizionale**: il primo token si riferisce al primo accordo `[...]` della riga, il secondo al secondo, e così via. Se il numero di token è inferiore al numero di accordi, i restanti accordi non ricevono durata.

```chordpro
{beats_time: Do=4 Sol=2 La-=2}
[Do]Prima par[Sol]te bre[La-]ve
```

I valori di durata vengono mostrati nell'anteprima accanto agli accordi (se l'opzione **Mostra durate battiti** è attiva nel menu Visualizza). Colore, dimensione e modalità di visualizzazione sono configurabili in *Preferenze → Formato → Durate battiti*.

> La direttiva agisce solo sulla riga successiva; non ha effetto su righe più distanti. Per la durata complessiva della canzone usare `{duration:}` (sezione 4).

---

## 7. Formattazione del testo

Questi comandi modificano l'aspetto del testo cantato a partire dal punto in cui compaiono. I valori si applicano per il resto della canzone o fino a un nuovo comando dello stesso tipo. Usati senza valore, **ripristinano il valore predefinito**.

### `textsize`

**Sintassi:** `{textsize: N}` oppure `{textsize}` per reset

Imposta la **dimensione del font** del testo in punti tipografici. Il valore deve essere un numero intero positivo.

```chordpro
{textsize: 14}
Testo più grande
{textsize}
Testo di dimensione normale
```

---

### `textfont`

**Sintassi:** `{textfont: NomeFont}` oppure `{textfont}` per reset

Imposta il **font** del testo cantato. Il nome deve corrispondere esattamente a un font installato nel sistema.

```chordpro
{textfont: Georgia}
Testo con font serif
{textfont}
```

---

### `textcolour` / `textcolor`

**Sintassi:** `{textcolour: #RRGGBB}` oppure `{textcolour: nome_colore}`

Imposta il **colore** del testo cantato. Accetta valori esadecimali CSS (`#FF0000`) o nomi colore inglesi (`red`, `blue`, ecc.).

```chordpro
{textcolour: #CC0000}
Testo in rosso
{textcolour: black}
```

---

### `linespacing`

**Sintassi:** `{linespacing: N}` oppure come attributo in `{start_of_grid}`

Imposta la **spaziatura extra** in pixel tra le righe di testo. Quando usato come attributo di `{start_of_grid}`, si applica solo a quel blocco griglia.

```chordpro
{linespacing: 6}
```

---

## 8. Formattazione degli accordi

### `chordsize`

**Sintassi:** `{chordsize: N}` oppure `{chordsize}` per reset

Imposta la **dimensione del font** degli accordi in punti tipografici. Analogamente a `textsize`, si applica da quel punto in avanti.

```chordpro
{chordsize: 11}
[C]Accordo più [G]piccolo
{chordsize}
```

---

### `chordfont`

**Sintassi:** `{chordfont: NomeFont}` oppure `{chordfont}` per reset

Imposta il **font** degli accordi. Utile per distinguere visivamente accordi e testo con famiglie tipografiche diverse.

```chordpro
{chordfont: Arial Bold}
```

---

### `chordcolour` / `chordcolor`

**Sintassi:** `{chordcolour: #RRGGBB}` oppure `{chordcolour: nome_colore}`

Imposta il **colore** degli accordi. Stesso formato di `textcolour`.

```chordpro
{chordcolour: #0055AA}
[C]Accordo [G]blu
{chordcolour: black}
```

---

### `chordtopspacing`

**Sintassi:** `{chordtopspacing: N}` oppure come attributo in `{start_of_grid}`

Imposta lo **spazio extra in pixel tra la riga degli accordi e il testo** sottostante. Aumentandolo si crea più respiro visivo. Quando usato come attributo di `{start_of_grid}`, si applica solo a quel blocco griglia.

```chordpro
{chordtopspacing: 8}
```

---

## 9. Diagrammi e immagini

### `define`

**Sintassi:** `{define: NomeAccordo base-fret N frets X N N N N N}`

Definisce un **diagramma di chitarra** personalizzato per un accordo. Il formato segue lo standard ChordPro:
- `base-fret N` indica il tasto di partenza del diagramma
- `frets` elenca la posizione del dito su ciascuna corda (da bassa ad alta): `X` = corda non suonata, `0` = corda a vuoto, numero = tasto

```chordpro
{define: C base-fret 1 frets X 3 2 0 1 0}
{define: Barre7 base-fret 7 frets 1 1 1 1 1 1}
```

Il diagramma viene visualizzato nell'anteprima (se l'opzione "Mostra diagrammi chitarra" è attiva) sopra la prima occorrenza dell'accordo nella canzone.

---

### `taste`

**Sintassi:** `{taste: NomeAccordo}`

Mostra la **tastiera di pianoforte** con le note dell'accordo evidenziate (funzione Klavier). È l'equivalente pianistico di `define`. La tastiera viene renderizzata graficamente con i tasti premuti colorati.

```chordpro
{taste: Cmaj7}
{taste: Am}
```

> Il colore dei tasti evidenziati è configurabile in *Preferenze → Formato → Colore tasti Klavier*.

---

### `fingering`

**Sintassi:** `{fingering: NomeAccordo N=Nota [N=Nota ...]}`

Mostra la **tastiera di pianoforte** di un accordo con la **diteggiatura numerata**: sopra ogni tasto premuto viene visualizzato il numero del dito corrispondente. Estende `{taste}` aggiungendo una mappa dito→nota.

Il formato è: nome dell'accordo, seguito da coppie `numero_dito=nota_italiana` (es. `1=Do`, `2=Mi`, `3=Sol`). Il KlavierRenderer interpreta la mappa e disegna i numeri sui tasti. Il colore dei numeri è configurabile nelle preferenze.

```chordpro
{fingering: Am 1=Do 2=Mi 3=La}
{fingering: C 1=Mi 2=Sol 3=Do}
```

> I comandi `{taste}` e `{fingering}` utilizzano la stessa lista interna (`klavier_list`): possono coesistere liberamente nello stesso file.

---

**Sintassi:**
```
{image: percorso/file.png [width=N] [height=N] [scale=N] [align=left|center|right] [border[=N]]}
```

Inserisce un'**immagine** nel corpo della canzone. Il percorso può essere assoluto o relativo alla posizione del file `.crd`. Parametri opzionali:

| Parametro | Descrizione | Default |
|---|---|---|
| `width=N` | Larghezza in punti logici (0 = automatica) | `0` |
| `height=N` | Altezza in punti logici (0 = automatica) | `0` |
| `scale=N` | Fattore di scala (es. `0.5` = 50%, `2` = 200%) | `1.0` |
| `align=left\|center\|right` | Allineamento orizzontale | `center` |
| `border` / `border=N` | Aggiunge un bordo; N è lo spessore (senza N default=1) | nessun bordo |

Le parole chiave `left`, `center`, `right` possono essere usate anche da sole senza il prefisso `align=`.

```chordpro
{image: img/logo.png width=200 align=center}
{image: foto.jpg scale=0.5 border=2}
{image: copertina.png left}
```

---

## 10. Accordi inline

Gli accordi non sono comandi `{...}` ma si inseriscono tra **parentesi quadre** `[...]` direttamente nel testo, nel punto esatto in cui cadono sull'ultima sillaba.

**Sintassi:** `[Accordo]testo`

```chordpro
[C]Testo della can[G]zone con ac[Am]cordi [F]inline
```

**Notazioni supportate:**
- **Inglese:** `C`, `Dm`, `G7`, `Am/E`, `F#m`, `Bb`, `Cmaj7`, `Csus4`, ecc.
- **Italiana:** `Do`, `Rem`, `Sol7`, `Lam/Mi`, `Fa#m`, `Sib`, ecc.

Gli accordi vengono visualizzati **sopra** il testo (o sotto, se configurato nelle preferenze). La posizione verticale è definita dall'opzione *Accordi sopra/sotto* nel menu Formato.

---

## 11. Commenti di riga

Le righe che iniziano con `#` sono **commenti** e vengono completamente ignorate dal renderer. Possono essere usate per note interne al file o per disattivare temporaneamente una riga.

```chordpro
# Questa riga non viene visualizzata
# {new_page} — questo salto di pagina è disabilitato
{t: La mia canzone}
```

Un `#` che appare **all'interno di una riga** (non all'inizio) viene trattato come commento inline: tutto ciò che segue il `#` (al di fuori di `[...]` e `{...}`) viene ignorato.

---

## 12. Preferenze dell'applicazione

Le preferenze si aprono dal menu **Strumenti → Preferenze** (o con la scorciatoia corrispondente). La finestra è organizzata in sette schede (tab).

---

### Scheda Generale

#### Gruppo: Font editor

| Impostazione | Tipo | Default | Descrizione |
|---|---|---|---|
| **Font editor** | ComboBox | font monospace di sistema | Font usato nell'editor di testo per la digitazione del codice ChordPro. |
| **Dimensione** | ComboBox | 12 | Dimensione in punti del font dell'editor (valori: 7, 8, 9, 10, 11, 12, 13, 14, 16, 18, 20). |
| **Colore sfondo editor** | Colore (#HEX) | `#FFFFFF` | Colore di sfondo dell'area di testo dell'editor. Il bottone **Pick…** apre il selettore colori con palette personalizzata salvata. |
| **Colore selezione** | Colore (#HEX) | `#C0C0C0` | Colore di evidenziazione del testo selezionato nell'editor. |
| **Colore barra Editor** | Colore (#HEX) | `#4682C8` | Colore base della barra del titolo del pannello **Editor**. La sfumatura attivo/inattivo viene calcolata automaticamente da questo colore. |
| **Colore barra Anteprima** | Colore (#HEX) | `#329B82` | Colore base della barra del titolo del pannello **Anteprima**. |

Un'area di anteprima live mostra in tempo reale come appare il testo con le impostazioni correnti di font, sfondo e selezione.

#### Gruppo: Canzone (Song)

| Impostazione | Tipo | Default | Descrizione |
|---|---|---|---|
| **Notazione predefinita** | Choice | inglese | Notazione musicale predefinita per gli accordi: inglese (C, D, E…) o italiana (Do, Re, Mi…). Usata per il riconoscimento automatico e la trasposizione. |
| **Estensione file predefinita** | Choice | `crd` | Estensione predefinita per il salvataggio dei file: `crd`, `cho`, `chordpro`, `chopro`, `pro`, `tab`. |
| **Lingua** | ComboBox con bandiera | sistema | Lingua dell'interfaccia di Songpress++. La modifica ha effetto al prossimo riavvio. |

#### Gruppo: Generali (General)

| Impostazione | Tipo | Default | Descrizione |
|---|---|---|---|
| **Cancella file recenti** | Bottone | — | Cancella immediatamente la lista dei file aperti di recente dal menu File. |
| **Mostra anteprima di stampa prima di stampare** | Checkbox | ✔ attivo | Se attivo, apre l'anteprima di stampa prima di inviare alla stampante. |
| **Abilita multi-cursore (Alt+Clic, Ctrl+D)** | Checkbox | ✗ disattivo | Abilita la modalità multi-cursore nell'editor: Alt+Click aggiunge un cursore, Ctrl+D seleziona la prossima occorrenza della parola selezionata. |
| **Salva dimensione e posizione finestra all'uscita** | Checkbox | ✔ attivo | Se attivo, memorizza dimensione, posizione e stato massimizzato della finestra principale alla chiusura e le ripristina alla riapertura. |

---

### Scheda Correz. automatiche (AutoAdjust)

Songpress++ può offrire correzioni automatiche quando rileva determinati pattern nel testo incollato o digitato.

| Impostazione | Tipo | Default | Descrizione |
|---|---|---|---|
| **Proponi rimozione righe vuote** | Checkbox | ✔ attivo | Se il testo incollato contiene righe vuote spurie (tipiche delle canzoni copiate da siti web), Songpress++ propone di rimuoverle automaticamente. |
| **Proponi conversione da formato tab** | Checkbox | ✔ attivo | Se rileva che il testo è in formato tab (accordi su una riga, testo sulla successiva), propone la conversione automatica in ChordPro. |
| **Proponi trasposizione per semplificare gli accordi** | Checkbox | ✗ disattivo | Se la canzone usa accordi difficili e esiste una tonalità più semplice, propone la trasposizione automatica. |

Sotto i tre checkbox è presente un pannello scorrevole con i **gruppi di accordi facili** configurabili con uno slider per ciascun gruppo (es. accordi aperti, accordi con barrè al I tasto, ecc.). Ogni slider indica quanto "peso" dare a quel gruppo nel calcolo della difficoltà.

---

### Scheda Formato (Format)

#### Gruppo: Titolo e struttura

| Impostazione | Tipo | Intervallo | Default | Descrizione |
|---|---|---|---|---|
| **Spessore linea sotto il titolo** | SpinCtrl | 1–5 | 4 | Spessore in pixel della linea decorativa sotto il titolo della canzone nell'anteprima. |
| **Spessore riquadro numero strofa** | SpinCtrl | 1–5 | 1 | Spessore in pixel del riquadro attorno al numero della strofa nell'anteprima. |

#### Gruppo: Accordi e tempo

| Impostazione | Tipo | Default | Descrizione |
|---|---|---|---|
| **Colore tasti Klavier** | Colore (#HEX) | `#D23C3C` | Colore dei tasti evidenziati nella tastiera Klavier (diagramma pianoforte resa da `{taste:}`). |
| **Dimensione icone tempo** | RadioButton | 24×24 | Dimensione delle icone grafiche del tempo (`{tempo:`, ecc.) nell'anteprima. Valori: 16×16, 24×24, 32×32 pixel. |

#### Gruppo: Griglia accordi — `{start_of_grid}`

| Impostazione | Tipo | Default | Descrizione |
|---|---|---|---|
| **Modalità di visualizzazione** | RadioButton | Tabella pipe | Modalità di visualizzazione delle griglie accordi (vedi sotto). |
| **Etichetta griglia predefinita** | TextCtrl | `Grid` | Etichetta mostrata accanto al blocco griglia quando `{start_of_grid}` non specifica un'etichetta esplicita. |
| **Barra spazio inserisce \| (modalità pipe)** | Checkbox | ✔ attivo | Quando attivo, premere Barra Spazio dentro un blocco `{start_of_grid}` inserisce il carattere `|` anziché uno spazio, facilitando la digitazione in modalità pipe. |
| **size=N agisce su** | RadioButton | Larghezza e altezza | Controlla a quali dimensioni della cella si applica il moltiplicatore `size=N` della direttiva `{start_of_grid}`: larghezza e altezza, solo larghezza, solo altezza. |

**Modalità di visualizzazione griglia:**

| Opzione | Aspetto | Descrizione |
|---|---|---|
| **Tabella con pipe** | `\| C \| G \| Am \| F \|` | Le battute sono separate da caratteri `\|`. Modalità predefinita. |
| **Spaziatura semplice** | `C   G   Am  F` | Le celle sono affiancate con spazio proporzionale, senza separatori. |
| **Tabella con bordi** | celle con bordi grafici | Ogni battuta è racchiusa in una cella con bordo grafico visibile. |

---

### Scheda Anteprima (Songpress++ Preview)

Queste impostazioni controllano il comportamento del pannello di anteprima in tempo reale.

| Impostazione | Tipo | Default | Descrizione |
|---|---|---|---|
| **Mostra indicatore pagina (es. 'Pagina 1 di 3')** | Checkbox | ✔ attivo | Mostra o nasconde il contatore di pagina in alto a destra del pannello anteprima (es. "Pagina 1 di 3"). |
| **Sfondo grigio nell'anteprima (stile pagina)** | Checkbox | ✔ attivo | Mostra l'anteprima su sfondo grigio con la pagina bianca al centro, simulando un foglio stampato. Se disattivato, lo sfondo è bianco uniforme. |
| **Ritarda aggiornamento anteprima durante la digitazione** | Checkbox | ✔ attivo | Ritarda il ridisegno dell'anteprima fino a una breve pausa nella digitazione, migliorando le prestazioni su file lunghi. Se disattivato, l'anteprima si aggiorna a ogni tasto. |
| **Doppio clic nell'anteprima salta alla riga sorgente** | Checkbox | ✔ attivo | Facendo doppio clic su una parola o un accordo nell'anteprima, il cursore dell'editor salta alla riga corrispondente nel sorgente ChordPro. |
| **Imposta dimensione minima del pannello anteprima all'avvio (370×520)** | Checkbox | ✔ attivo | Impedisce al pannello anteprima di essere ridimensionato sotto 370×520 pixel. Utile per evitare che l'anteprima diventi troppo piccola da leggere. |

---

### Scheda Guida rapida (Quick guide)

Configura il visualizzatore della guida rapida integrata di Songpress++.

#### Gruppo: Visualizzatore Markdown

| Impostazione | Tipo | Default | Descrizione |
|---|---|---|---|
| **Visualizzatore Markdown** | Choice | Automatico | Motore usato per renderizzare la guida in Markdown: **Automatico** (prova python-markdown, poi mistune, poi parser integrato), **python-markdown**, **mistune**, **Parser integrato**. |

#### Gruppo: Percorsi immagini

| Impostazione | Tipo | Default | Descrizione |
|---|---|---|---|
| **Usa percorsi assoluti per le immagini nel Markdown** | Checkbox | ✗ disattivo | Se attivo, i percorsi delle immagini nella guida vengono riscritti come percorsi assoluti completi (`../src/songpress/img/GUIDE/...`). Utile per visualizzare la guida in editor Markdown esterni. |

---

### Scheda Menu contestuale (Context menu)

Permette di personalizzare quali voci appaiono nel **menu contestuale** (tasto destro) dell'editor. Ogni voce può essere abilitata o disabilitata individualmente.

#### Gruppo: Cronologia

| Voce | Default |
|---|---|
| Annulla | ✔ |
| Ripristina | ✔ |

#### Gruppo: Modifica

| Voce | Default |
|---|---|
| Taglia | ✔ |
| Copia | ✔ |
| Incolla | ✔ |
| Elimina | ✔ |

#### Gruppo: Azioni speciali

| Voce | Default | Descrizione |
|---|---|---|
| Incolla accordi | ✔ | Incolla solo gli accordi dal testo copiato, sovrascrivendo quelli presenti. |
| Propaga accordi strofa | ✔ | Propaga lo schema accordi della strofa corrente a tutte le strofe con lo stesso schema. |
| Propaga accordi ritornello | ✔ | Come sopra, per il ritornello. |
| Copia solo testo | ✔ | Copia il testo senza accordi negli appunti. |

#### Gruppo: Selezione

| Voce | Default |
|---|---|
| Seleziona tutto | ✔ |

---

### Scheda Associazioni file (File associations)

Disponibile **solo su Windows**. Permette di associare le estensioni dei file ChordPro a Songpress++ per l'utente corrente, in modo che un doppio clic sul file apra direttamente l'applicazione.

| Estensione | Descrizione |
|---|---|
| `.crd` | Formato principale di Songpress++ |
| `.cho` | ChordPro classico |
| `.chordpro` | ChordPro esteso |
| `.chopro` | Variante ChordPro |
| `.pro` | Abbreviazione ChordPro |
| `.tab` | Formato tab |

I bottoni **Associa tutte** e **Rimuovi tutte** selezionano o deselezionano tutte le estensioni in un solo clic.

> Le modifiche alle associazioni file si applicano immediatamente e riguardano solo l'utente Windows corrente (non richiedono privilegi di amministratore).

---

### Impostazioni dal menu Formato

Alcune impostazioni non si trovano nella finestra Preferenze ma nel menu **Formato** della barra dei menu principale. Vengono salvate automaticamente alla chiusura dell'applicazione.

#### Visualizzazione accordi (slider nella toolbar)

Controlla quante strofe vengono mostrate con gli accordi nell'anteprima.

| Posizione slider | Comportamento |
|---|---|
| 0 — Nessun accordo | Nessuna strofa mostra gli accordi. Utile per la stampa solo testo. |
| 1 — Una strofa per schema | Solo la prima strofa di ogni schema accordale viene mostrata con gli accordi. Le strofe identiche vengono mostrate senza accordi per leggibilità. |
| 2 — Tutta la canzone | Tutti gli accordi di tutte le strofe sono sempre visibili. |

#### Etichette strofe (pulsante nella toolbar)

| Impostazione | Descrizione |
|---|---|
| **Mostra etichette strofe** (toggle) | Mostra o nasconde le etichette numerate delle strofe e i riquadri del ritornello nell'anteprima e in stampa. |

#### Posizione accordi

| Impostazione | Descrizione |
|---|---|
| **Accordi sopra** | Gli accordi vengono visualizzati sopra la riga di testo corrispondente (comportamento predefinito). |
| **Accordi sotto** | Gli accordi vengono visualizzati sotto la riga di testo. |

#### Indicazione di tempo `{tempo:}` — modalità visualizzazione

Accessibile da **Formato → Indicazione di tempo** (o clic sull'indicazione nell'anteprima). Controlla come viene rappresentato il valore del tempo.

| Modalità | Valore interno | Descrizione |
|---|---|---|
| Icona nota + numero | `1` | Mostra l'icona grafica della nota di riferimento seguita dal valore BPM (es. ♩ = 120). |
| Solo testo | `2` | Mostra solo il numero BPM senza simbolo grafico. |
| Icona metronomo | `3` | Mostra un'icona a forma di metronomo con il valore BPM. |
| Testo semplice | `0` | Mostra il testo in forma compatta (es. "♩=120") senza icona separata. |
| Solo metadato (nascosto) | `-1` | Il valore è memorizzato nel file ma non visualizzato nell'anteprima né in stampa. |

#### Indicazione di metro `{time:}` — visibilità

| Impostazione | Descrizione |
|---|---|
| **Mostra metro** | Se attivo, l'indicazione di metro (es. 4/4, 3/4) viene visualizzata nell'anteprima. |
| **Solo metadato** | Il metro è memorizzato nel file ma non visualizzato. |

#### Tonalità `{key:}` — visibilità

| Impostazione | Descrizione |
|---|---|
| **Mostra tonalità** | Se attivo, la tonalità viene visualizzata nell'anteprima. |
| **Solo metadato** | La tonalità è memorizzata nel file ma non visualizzata. |

---

## 13. Sommario finale

| Comando | Abbreviazione | Categoria | Descrizione sintetica |
|---|---|---|---|
| `{title: ...}` | `{t:}` | Struttura | Titolo della canzone |
| `{subtitle: ...}` | `{st:}` | Struttura | Sottotitolo |
| `{start_of_verse}` / `{end_of_verse}` | `{sov}` / `{eov}` | Struttura | Delimita una strofa con numerazione automatica |
| `{start_verse}` / `{end_verse}` | — | Struttura | Variante alternativa di start_of_verse |
| `{start_verse_num}` / `{end_verse_num}` | — | Struttura | Strofa con numerazione forzata |
| `{start_of_chorus}` / `{end_of_chorus}` | `{soc}` / `{eoc}` | Struttura | Delimita un ritornello |
| `{start_chorus}` / `{end_chorus}` | — | Struttura | Variante alternativa di start_of_chorus |
| `{start_of_bridge}` / `{end_of_bridge}` | `{sob}` / `{eob}` | Struttura | Delimita un bridge |
| `{start_bridge}` / `{end_bridge}` | — | Struttura | Variante alternativa di start_of_bridge |
| `{start_chord}` / `{end_chord}` | — | Struttura | Blocco generico con etichetta personalizzata |
| `{start_of_part}` / `{end_of_part}` | `{sop}` / `{eop}` | Struttura | Sezione generica ChordPro 6 (non numerata) |
| `{verse: ...}` | — | Struttura | Blocco strofa con etichetta specifica |
| `{row}` | `{r}` | Struttura | Riga separatrice vuota |
| `{new_song}` | — | Struttura | Reset completo del renderer |
| `{start_of_tab}` / `{end_of_tab}` | `{sot}` / `{eot}` | Tab/Griglia | Blocco tablatura ASCII con font monospace |
| `{start_of_grid}` / `{end_of_grid}` | `{sog}` / `{eog}` | Tab/Griglia | Blocco griglia accordi per battute |
| `{grid}` | — | Tab/Griglia | Apre un blocco griglia (sinonimo di `{sog}`) |
| `{comment: ...}` | `{c:}` | Annotazioni | Commento visibile in stile normale |
| `{comment_italic: ...}` | `{ci:}` | Annotazioni | Commento in corsivo |
| `{comment_box: ...}` | `{cb:}` | Annotazioni | Commento in riquadro |
| `{artist: ...}` | — | Metadati | Nome artista |
| `{composer: ...}` | — | Metadati | Nome compositore |
| `{lyricist: ...}` | — | Metadati | Nome paroliere — visualizzato con prefisso "Testo:" |
| `{arranger: ...}` | — | Metadati | Nome arrangiatore — visualizzato con prefisso "Arrangiamento:" |
| `{album: ...}` | — | Metadati | Titolo album |
| `{year: ...}` | — | Metadati | Anno di pubblicazione |
| `{duration: ...}` | — | Metadati | Durata della canzone (metadato puro, non visualizzato) |
| `{ccli: ...}` | — | Metadati | Numero licenza CCLI |
| `{copyright: ...}` | — | Metadati | Testo copyright |
| `{key: ...}` | — | Metadati | Tonalità della canzone |
| `{capo: N}` | — | Metadati | Posizione del capotasto |
| `{new_page}` | `{np}` | Impaginazione | Salto di pagina |
| `{column_break}` | `{colb}` | Impaginazione | Salto di colonna |
| `{tempo: N}` | — | Musicale | Tempo in BPM (semiminima) |
| `{tempo_m: N}` | — | Musicale | Tempo in BPM (minima) |
| `{tempo_s: N}` | — | Musicale | Tempo in BPM (semiminima, sinonimo) |
| `{tempo_c: N}` | — | Musicale | Tempo in BPM (croma) |
| `{tempo_sp: N}` | — | Musicale | Tempo in BPM (semiminima puntata) |
| `{tempo_cp: N}` | — | Musicale | Tempo in BPM (croma puntata) |
| `{time: N/D}` | — | Musicale | Metro (indicazione di misura) |
| `{beats_time: ACC=N ...}` | — | Musicale | Durata in battiti degli accordi della riga successiva |
| `{textsize: N}` | — | Testo | Dimensione font testo |
| `{textfont: ...}` | — | Testo | Font del testo |
| `{textcolour: ...}` | `{textcolor:}` | Testo | Colore del testo |
| `{linespacing: N}` | — | Testo | Spaziatura interlinea extra |
| `{chordsize: N}` | — | Accordi | Dimensione font accordi |
| `{chordfont: ...}` | — | Accordi | Font degli accordi |
| `{chordcolour: ...}` | `{chordcolor:}` | Accordi | Colore degli accordi |
| `{chordtopspacing: N}` | — | Accordi | Spazio tra accordi e testo |
| `{define: ...}` | — | Diagrammi | Diagramma chitarra personalizzato |
| `{taste: ...}` | — | Diagrammi | Tastiera pianoforte (Klavier) |
| `{fingering: ...}` | — | Diagrammi | Tastiera pianoforte con diteggiatura numerata |
| `{image: ...}` | — | Immagini | Inserisce un'immagine |
| `[Accordo]` | — | Accordi inline | Accordo posizionato nel testo |
| `# testo` | — | Commenti | Riga di commento (ignorata) |
