# Guida rapida — Songpress++

Questa guida descrive tutti i comandi ChordPro supportati da Songpress++ e le principali funzioni dell'editor.

> **Legenda** — La colonna **Std** indica se la direttiva fa parte dello standard ChordPro ufficiale (✅) oppure è specifica di Songpress++ (🔧). La colonna **Menu** indica se la direttiva è inseribile tramite un menu dell'applicazione (⌨️) oppure va digitata manualmente nell'editor (🖊).

---

## Formato ChordPro — Concetti base

Un file ChordPro è un file di testo in cui gli **accordi** sono inseriti direttamente nel testo della canzone, racchiusi tra parentesi quadre `[accordo]`. Le **direttive** di metadati e struttura sono racchiuse tra parentesi graffe `{direttiva:valore}`.

```chordpro
{title: Amazing Grace}
{artist: Traditional}
{key: G}

[G]Amazing [G7]grace, how [C]sweet the [G]sound
```

---

## Metadati della canzone

| Direttiva | Alias | Std | Menu | Descrizione |
| --- | --- | --- | --- | --- |
| `{title:Titolo}` | `{t:Titolo}` | ✅ | ⌨️ | Titolo della canzone |
| `{subtitle:Testo}` | `{st:...}` | ✅ | ⌨️ | Sottotitolo o artista secondario |
| `{artist:Nome}` | | ✅ | 🖊 | Artista / esecutore (reso come sottotitolo) |
| `{composer:Nome}` | | ✅ | 🖊 | Compositore (reso come sottotitolo) |
| `{album:Titolo}` | | ✅ | 🖊 | Titolo dell'album (reso come «Album: …») |
| `{year:Anno}` | | ✅ | 🖊 | Anno di pubblicazione (reso come sottotitolo) |
| `{copyright:Testo}` | | ✅ | 🖊 | Nota di copyright (resa come «© …») |
| `{key:Tonalità}` | | ✅ | ⌨️ | Tonalità (es. `Am`, `C`, `G`, `F#m`); resa come «Key: …» se la visualizzazione è attiva |
| `{capo:N}` | | ✅ | 🖊 | Capotasto al tasto N (es. `{capo:2}`); reso come «Capo: N» |
| `{tempo:BPM}` | | ✅ | ⌨️ | Tempo in BPM con icona **semiminima** (es. `{tempo:120}`) |
| `{tempo_m:BPM}` | | 🔧 | 🖊 | Tempo con icona **minima** (nota da mezzo) |
| `{tempo_s:BPM}` | | 🔧 | 🖊 | Tempo con icona **semiminima** (nota da un quarto) |
| `{tempo_sp:BPM}` | | 🔧 | 🖊 | Tempo con icona **semiminima puntata** |
| `{tempo_c:BPM}` | | 🔧 | 🖊 | Tempo con icona **croma** (nota da un ottavo) |
| `{tempo_cp:BPM}` | | 🔧 | 🖊 | Tempo con icona **croma puntata** |
| `{time:N/M}` | | ✅ | ⌨️ | Metrica (es. `{time:4/4}`, `{time:3/4}`); resa con simbolo grafico della metrica |

> **Nota sul tempo** — Le direttive `{tempo*}` hanno tre modalità di visualizzazione, configurabili nelle preferenze: icona nota + valore (es. `♩ = 120`), testo `BPM: 120`, oppure solo testo `Tempo: 120`. Impostando la modalità su *nascosto* (`-1`) il valore viene trattato come puro metadato e non compare nell'anteprima né in stampa.

---

## Struttura della canzone

### Blocchi di testo

| Direttiva | Std | Menu | Descrizione |
| --- | --- | --- | --- |
| `{start_of_verse}` / `{end_of_verse}` | ✅ | ⌨️ | Strofa non numerata, senza etichetta |
| `{start_verse:Etichetta}` / `{end_verse}` | 🔧 | ⌨️ | Strofa non numerata con etichetta opzionale |
| `{start_verse_num}` / `{end_verse_num}` | 🔧 | ⌨️ | Strofa numerata automaticamente |
| `{verse:Etichetta}` | ✅ | ⌨️ | Apre una strofa con etichetta personalizzata (es. `{verse:1}`) |
| `{start_of_chorus}` / `{end_of_chorus}` | ✅ | ⌨️ | Ritornello |
| `{soc}` / `{eoc}` | ✅ | ⌨️ | Abbreviazione di `start_of_chorus` / `end_of_chorus` |
| `{soc:Etichetta}` | ✅ | ⌨️ | Ritornello con etichetta personalizzata |
| `{start_chorus:Etichetta}` / `{end_chorus}` | 🔧 | ⌨️ | Forma alternativa del ritornello (con etichetta opzionale) |
| `{start_bridge:Etichetta}` / `{end_bridge}` | 🔧 | ⌨️ | Bridge / inciso con etichetta opzionale; se omessa usa «Bridge» |
| `{start_chord:Etichetta}` / `{end_chord}` | 🔧 | ⌨️ | Blocco intro/accordi; se l'etichetta è omessa usa «Intro» |
| `{new_song}` | 🔧 | 🖊 | Inizia un nuovo brano nello stesso documento: azzera i contatori di strofe e ritornelli così la numerazione riparte da 1 |

> **Nota su `{start_of_bridge}`** — Questa forma (con `of_`) non è gestita dal renderer; usare `{start_bridge}` / `{end_bridge}`.

### Interruzioni di pagina e colonna

| Direttiva | Alias | Std | Menu | Descrizione |
| --- | --- | --- | --- | --- |
| `{new_page}` | `{np}` | ✅ | ⌨️ | Interruzione di pagina esplicita per la stampa |
| `{column_break}` | `{colb}` | ✅ | ⌨️ | Interruzione di colonna (layout a 2 colonne) |

---

## Accordi e formattazione inline

### Accordi

Gli accordi si inseriscono nel testo con le parentesi quadre, immediatamente prima della sillaba a cui appartengono:

```chordpro
[Am]Nel [F]blu [C]dipinto di [G]blu
```

### Font e colori locali

Queste direttive cambiano il font per la sezione seguente; usate senza argomento ripristinano il valore predefinito.

| Direttiva apertura | Direttiva chiusura | Std | Menu | Descrizione |
| --- | --- | --- | --- | --- |
| `{textfont:Nome}` | `{textfont}` | ✅ | ⌨️ | Famiglia di font del testo |
| `{textsize:Pt}` | `{textsize}` | ✅ | ⌨️ | Dimensione del testo in pt (accetta anche percentuale, es. `{textsize:80%}`) |
| `{textcolour:#HEX}` | `{textcolour}` | ✅ | ⌨️ | Colore del testo in formato `#RRGGBB` |
| `{chordfont:Nome}` | `{chordfont}` | ✅ | ⌨️ | Famiglia di font degli accordi |
| `{chordsize:Pt}` | `{chordsize}` | ✅ | ⌨️ | Dimensione degli accordi in pt (accetta anche percentuale) |
| `{chordcolour:#HEX}` | `{chordcolour}` | ✅ | ⌨️ | Colore degli accordi in formato `#RRGGBB` |

### Spaziatura

| Direttiva | Std | Menu | Descrizione |
| --- | --- | --- | --- |
| `{linespacing:N}` | 🔧 | ⌨️ | Interlinea in punti (es. `{linespacing:1}`); senza argomento ripristina il valore predefinito |
| `{chordtopspacing:N}` | 🔧 | ⌨️ | Spazio sopra gli accordi in punti (es. `{chordtopspacing:0}` per eliminarlo); senza argomento ripristina il valore predefinito |
| `{row}` o `{r}` | 🔧 | 🖊 | Inserisce mezzo spazio bianco verticale (spacer) — non presente nel menu, va digitato manualmente |
---

# Direttive di spaziatura in Songpress++

---

## `{linespacing: <valore>}`

**Voce di menu:** *Interlinea*

### Descrizione linespacing

Imposta l'**interlinea** tra le righe del testo del brano a partire dal punto in cui la direttiva viene inserita. Agisce sulla spaziatura verticale complessiva tra una riga di testo (con i suoi accordi) e la riga successiva.

### Sintassi linespacing

```chordpro
{linespacing: 13}
```

### Parametro linespacing

| Valore           | Effetto                                                                       |
| ---------------- | ----------------------------------------------------------------------------- |
| `0`              | Rimuove lo spazio extra tra le righe (valore di default nel dialogo di inserimento) |
| numero positivo  | Aggiunge spazio verticale tra le righe (in punti tipografici)                 |

### Note d'uso — linespacing

- La direttiva può essere inserita in qualsiasi punto del brano; ha effetto sulle righe successive.
- Valori tipici si aggirano tra `10` e `20` a seconda del font e della dimensione usati.
- Utile per aggiustare la densità di testo nella stampa, specialmente quando si usa il layout a due colonne o il formato due pagine per foglio.

---

## `{chordtopspacing: <valore>}`

**Voce di menu:** *Spazio sopra accordi*

### Descrizione chordtopspacing

Imposta lo **spazio verticale sopra gli accordi**, cioè la distanza tra il bordo superiore della riga di accordi e il contenuto che la precede (ad es. la riga di testo della strofa precedente). Permette di allentare o comprimere il margine che separa visivamente gli accordi dal verso che li sovrasta.

### Sintassi chordtopspacing

```chordpro
{chordtopspacing: 4}
```

### Parametro chordtopspacing

| Valore           | Effetto                                                                           |
| ---------------- | --------------------------------------------------------------------------------- |
| `0`              | Azzera lo spazio extra sopra gli accordi (valore di default nel dialogo di inserimento) |
| numero positivo  | Aumenta il respiro visivo sopra la riga degli accordi                             |

### Note d'uso — chordtopspacing

- Agisce indipendentemente da `linespacing`: i due parametri si sommano nella spaziatura complessiva.
- Utile quando gli accordi risultano visivamente "schiacciati" contro il testo della riga precedente.
- Come `linespacing`, può essere usato più volte nello stesso brano in punti diversi per variare la spaziatura sezione per sezione.

## Differenza tra le due direttive chordtopspacing e linespacing

```text
[riga di testo precedente]
                         ↕  chordtopspacing  (spazio sopra gli accordi)
[riga accordi:  Sol   Re   La]
[riga testo:    Quan-do il sol...]
                         ↕  linespacing      (interlinea tra righe complete)
[riga accordi:  Mi    Si...]
[riga testo:    ...sorge e...]
```

In sintesi: `chordtopspacing` controlla il margine **sopra** la coppia accordo+testo, mentre `linespacing` controlla lo spazio **tra** coppie successive.

## `{row}` / `{r}` 🖊

**Voce di menu:** *nessuna — va digitata manualmente*

### Descrizione row

Inserisce un **mezzo spazio verticale** (spacer) tra le righe del brano. Utile per aggiungere un piccolo respiro visivo tra un verso e l'altro senza ricorrere a `{linespacing}`.

### Sintassi row

```chordpro
{row}
```

oppure nella forma abbreviata:

```chordpro
{r}
```

### Note d'uso — row

- Inserisce uno spazio pari a circa **metà riga** rispetto all'interlinea corrente.
- Non ha parametri: `{row}` e `{r}` sono equivalenti e non accettano valori.
- Non è accessibile dal menu **Inserisci**: va digitato direttamente nell'editor.

---

## Commenti e note redazionali

| Forma | Alias | Std | Menu | Descrizione |
| --- | --- | --- | --- | --- |
| `{comment:Testo}` | `{c:Testo}` | ✅ | ⌨️ | Commento visibile nell'anteprima, racchiuso automaticamente tra parentesi |
| `{comment_italic:Testo}` | `{ci:Testo}` | ✅ | 🖊 | Come `{comment}`, ma con testo in corsivo |
| `{comment_box:Testo}` | `{cb:Testo}` | ✅ | 🖊 | Commento in riquadro |
| `# Testo` | | ✅ | 🖊 | Riga di commento (preceduta da `#`): ignorata come riga vuota, non appare in anteprima né in stampa |

---

## Diagrammi di accordi, tastiera e immagini

| Direttiva | Std | Menu | Descrizione |
| --- | --- | --- | --- |
| `{define: C base-fret 1 frets X 3 2 0 1 0}` | ✅ | ⌨️ | Definisce un diagramma di accordo per chitarra |
| `{taste:Accordo}` | 🔧 | ⌨️ | Mostra i tasti evidenziati sulla tastiera (klavier) — es. `{taste:Am}` |
| `{image: nomefile}` | ✅ | ⌨️ | Inserisce un'immagine (PNG, JPG, GIF, BMP, TIFF) nella canzone |

La tastiera (klavier) visualizza i tasti corrispondenti all'accordo specificato, evidenziati con il colore impostato nelle preferenze.

### Direttiva immagine

La direttiva `{image:}` incorpora un'immagine raster nel punto in cui compare nella canzone. Il percorso del file può essere relativo alla posizione del file canzone oppure assoluto.

| Opzione | Std | Descrizione |
| --- | --- | --- |
| `width=N` | ✅ | Larghezza in punti tipografici (1/72 di pollice), oppure percentuale es. `width=50%` |
| `height=N` | ✅ | Altezza in punti tipografici, oppure percentuale |
| `scale=N%` | ✅ | Fattore di scala, es. `scale=50%` (non combinabile con width/height) |
| `align=left` | ✅ | Allineamento a sinistra |
| `align=center` | ✅ | Allineamento centrato (predefinito) |
| `align=right` | ✅ | Allineamento a destra |
| `border` | ✅ | Disegna un bordo di 1pt attorno all'immagine |
| `border=N` | ✅ | Disegna un bordo di N punti tipografici |

**Formati supportati:**

| Formato | Estensioni |
| --- | --- |
| PNG | `.png` |
| JPEG | `.jpg`, `.jpeg` |
| GIF | `.gif` |
| BMP | `.bmp` |
| TIFF | `.tiff`, `.tif` |

**Esempi:**

```chordpro
{image: logo.png}
{image: logo.png width=200 align=left}
{image: logo.png scale=50% border}
{image: "C:\Users\Utente\Immagini\foto.jpg" align=center}
```

Se il file immagine si trova nella stessa cartella del file canzone è sufficiente indicare solo il nome. I percorsi contenenti spazi o backslash devono essere racchiusi tra virgolette doppie.

L'immagine può essere inserita tramite **Inserisci → Altro → Immagine {image:}**, che apre una dialog per selezionare il file e impostare tutte le opzioni, con anteprima in tempo reale della direttiva generata.

I campi numerici della dialog usano controlli con frecce incrementali:

| Campo      | Valore iniziale | Range  | Step | Note                              |
| ---------- | --------------- | ------ | ---- | --------------------------------- |
| Larghezza  | 0               | 0–9999 | 1    | 0 = non incluso nella direttiva   |
| Altezza    | 0               | 0–9999 | 1    | 0 = non incluso nella direttiva   |
| Scala      | 100             | 1–500  | 1    | 100 = non incluso (è il default)  |
| Bordo      | 1               | 0–50   | 0.5  | attivo solo se checkbox spuntato  |

---

## Struttura del file — Esempio completo

```chordpro
{title: O Sole Mio}
{artist: Eduardo di Capua}
{key: C}
{time: 4/4}
{tempo: 80}
{capo: 0}

{start_verse_num}
[C]Che bella [G7]cosa na jurnata 'e [C]sole
[C]N'aria serena [G7]doppo na tempesta!
{end_verse_num}

{soc:Ritornello}
[C]O sole [C7]mio sta [F]'nfronte a [C]te
[G7]O sole, o sole [C]mio
{eoc}

{new_page}

{start_verse_num}
[C]Ma n'atu sole [G7]cchiu bello, oje [C]ne'
{end_verse_num}
```

---

## Funzioni dell'editor

### Inserimento guidato (menu Inserisci)

Tutte le direttive principali sono accessibili tramite il menu **Inserisci**, che apre dialog di supporto per compilare i valori. Il cursore `|` nell'InsertWithCaret indica la posizione in cui il cursore sarà posizionato dopo l'inserimento.

### Gestione accordi

- **Inserisci accordo** — inserisce `[|]` con il cursore dentro le parentesi
- **Sposta accordo a destra / sinistra** — sposta l'accordo sotto il cursore di un carattere
- **Rimuovi accordi** — elimina tutti gli accordi dalla selezione
- **Incolla accordi** — incolla solo gli accordi (senza testo) dalla selezione copiata
- **Propaga accordi alle strofe** — copia gli accordi della prima strofa su tutte le strofe con lo stesso numero di righe
- **Propaga accordi ai ritornelli** — idem per i ritornelli
- **Integra accordi** — converte due righe separate (accordi sopra / testo sotto) in formato ChordPro inline

### Trasposizione e notazione

- **Trasponi** — apre il dialog per trasportare tutti gli accordi
- **Semplifica accordi** — trova la tonalità più semplice da suonare
- **Cambia notazione** — converte tra notazione anglofona (C D E…) e latina (Do Re Mi…)
- **Normalizza accordi** — uniforma la grafia degli accordi (es. `Hm` → `Bm`)
- **Converti Tab → ChordPro** — converte automaticamente il formato tab (accordi sopra il testo) in ChordPro inline

### Formato e struttura

- **Font canzone** — apre il dialog per impostare il font globale
- **Font testo** — inserisce direttive `{textfont}` / `{textsize}` / `{textcolour}` per il tratto corrente
- **Font accordi** — inserisce direttive `{chordfont}` / `{chordsize}` / `{chordcolour}`
- **Etichetta strofe** — mostra/nasconde le etichette delle strofe nell'anteprima
- **Accordi sopra / sotto** — posiziona gli accordi sopra o sotto il testo
- **Mostra accordi** — tre modalità: nessuno / prima strofa sola / brano intero
- **Linee interruzione pagina / colonna** — mostra/nasconde le linee guida nell'anteprima

### Pulizia testo

- **Rimuovi righe vuote superflue** — elimina le righe vuote doppie
- **Normalizza spazi multipli** — riduce gli spazi multipli a uno solo

### Verifica sintattica

- **Controlla sintassi** — analizza il testo e segnala direttive non riconosciute o malformate, con possibilità di navigare direttamente all'errore

---

## Preferenze di visualizzazione

I seguenti controlli si trovano nella scheda **Formattazione** delle preferenze e influenzano l'anteprima e la stampa.

| Campo | Valore predefinito | Range | Step |
| --- | --- | --- | --- |
| Spessore sottolineatura titolo | 2 | 1–5 | 1 |
| Spessore bordo numero strofa | 1 | 1–5 | 1 |

---

## Stampa e anteprima

- **Anteprima di stampa** — mostra l'anteprima con pulsante "Opzioni di stampa" e "Imposta pagina"
- **Stampa** — stampa direttamente (senza anteprima se l'opzione è disattivata nelle preferenze)
- **Imposta pagina** — carta, orientamento e margini (in mm)

### Opzioni di stampa

| Opzione | Descrizione |
| --- | --- |
| Stampa 2 pagine per foglio | Stampa due pagine logiche affiancate su un foglio fisico |
| Colonne per pagina (1 / 2) | Distribuisce il testo su una o due colonne |
| Riduci e adatta alla pagina | Riduce il contenuto per farlo stare in una sola pagina |
| Riduci per adattare alla pagina corrente | Riduce ulteriormente evitando il taglio del contenuto in fondo |
| Non replicare (lascia bianca la metà destra) | Con 2 pag/foglio: lascia vuota la seconda metà invece di replicare |
| Rimuovi pagine bianche | Elimina le pagine vuote dal risultato di stampa |

La direttiva `{new_page}` nel testo forza una nuova pagina logica durante la stampa. Con il layout a 2 colonne, `{column_break}` forza il passaggio alla colonna successiva.

---

## Esportazione

| Formato | Note |
| --- | --- |
| SVG | Vettoriale, scalabile |
| EMF | Vettoriale Windows |
| PNG | Immagine raster |
| HTML | Pagina web con accordi colorati |
| Tab | Formato testo con accordi sopra |
| PDF | Documento PDF |
| PowerPoint (.pptx) | Presentazione |
| Songbook | Raccolta di canzoni |
| Copia come immagine | Copia negli appunti come vettoriale |
| Copia solo testo | Copia il testo senza accordi |

---

## Formati di file supportati in importazione

| Estensione | Descrizione |
| --- | --- |
| `.crd` | ChordPro (estensione principale) |
| `.cho` | ChordPro |
| `.chordpro` | ChordPro |
| `.chopro` | ChordPro |
| `.pro` | ChordPro |
| `.tab` | Tab format (accordi sopra il testo) |

---

## Licenza e crediti

**Songpress++** è un'opera derivata di **Songpress**, sviluppato originariamente da Luca Allulli / [Skeed](https://www.skeed.it/songpress) — copyright © 2009–2026 Luca Allulli (Skeed).

Le modifiche presenti in Songpress++ sono copyright © Denisov21.

Songpress++ è distribuito sotto i termini della **GNU General Public License versione 2** (GPL v2), la stessa licenza del progetto originale. Il programma è software libero: è possibile ridistribuirlo e/o modificarlo rispettando i termini della GPL v2 pubblicata dalla Free Software Foundation. Il programma viene distribuito nella speranza che sia utile, ma **senza alcuna garanzia**, nemmeno implicita di commerciabilità o idoneità a uno scopo specifico.

Il testo completo della licenza è disponibile all'indirizzo: <https://www.gnu.org/licenses/old-licenses/gpl-2.0.html>

### Componenti di terze parti

Songpress (e di conseguenza Songpress++) fa uso dei seguenti componenti software di terze parti:

| Componente | Licenza | Riferimento |
| --- | --- | --- |
| Python e libreria standard Python | Python Software Foundation License | <https://www.python.org> |
| wxPython | wxWindows Library Licence | <https://wxpython.org> |
| Editra (dialog di segnalazione errori) | wxWindows Library Licence v3.1 | <https://github.com/cjprecord/editra> |
| uv (solo installer Windows) | MIT License — copyright © 2025 Astral Software Inc. | <https://github.com/astral-sh/uv> |
