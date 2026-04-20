# Songpress++

Songpress++ è un programma gratuito e facile da usare per la composizione tipografica di canzoni su Windows (e Linux), che genera canzonieri di alta qualità.

Songpress++ è incentrato sulla formattazione delle canzoni. Una volta che la canzone è pronta, puoi copiarla/incollarla nella tua applicazione preferita per dare al tuo canzoniere l'aspetto che desideri. In alternativa puoi stamparla o creare un "Libro di canzoni"

## Installazione su Windows

### Utenti finali

1. Scarica ed esegui il file `songpress++-setup.exe`
2. L'installer guida l'utente attraverso l'installazione passo passo
3. **Nessuna configurazione manuale richiesta**: l'installer scarica automaticamente Python (se non già presente nel sistema) e tutti i pacchetti necessari direttamente da internet
4. Disponibile in versione portabile o installabile

> **Nota:** È necessaria una connessione internet durante la prima installazione.

> **Nota — `uv.exe` non è un virus:** L'installer include il file `uv.exe`, uno strumento open source per la gestione dei pacchetti Python ([astral-sh/uv](https://github.com/astral-sh/uv)). Alcuni antivirus potrebbero segnalarlo come sospetto a causa dell'euristica sui file eseguibili di nuova generazione. Si tratta di un **falso positivo**: `uv.exe` è un programma legittimo, sicuro e ampiamente diffuso nella comunità Python. Se il tuo antivirus lo blocca, aggiungi un'eccezione per la cartella di installazione di Songpress++.

Tutti i file vengono installati in un'unica cartella all'interno della directory _User_ dell'utente corrente, consentendo una disinstallazione pulita tramite il proprio programma di disinstallazione.

### Sviluppo

#### Prerequisiti

- **Python >= 3.12** installato e aggiunto al PATH
- Installare i pacchetti necessari:

```
pip install -r requirements.txt
```

Poi avviare `src/Avvio SONGPRESS.vbs` oppure `src/Avvio SONGPRESS2.vbs`.

In alternativa, è possibile avviare l'applicazione direttamente con Python dalla root del progetto:

```
cd E:\Users\Utente\Downloads\SongpressV33_OK\Songpressplusplus
python main.py
```

> **Nota:** Il percorso indicato (`E:\Users\Utente\Downloads\SongpressV33_OK\Songpressplusplus`) è un esempio. Sostituiscilo con il percorso effettivo in cui hai clonato o estratto il progetto sul tuo sistema.

> **Nota:** `main.py` va eseguito dalla directory radice del progetto (`Songpressplusplus\`), dove si trova, affinché il pacchetto `songpressPlusPlus` venga trovato correttamente nel Python path.

Le differenze tra i due launcher sono due, entrambe significative:

1. Ricerca di Python

`Avvio SONGPRESS2.vbs`: usa un array statico di versioni hardcoded (3.4 → 3.14) e le prova una per una con RegRead. Semplice ma fragile — se esce Python 3.15 non lo trova.
`Avvio SONGPRESS.vbs`: usa reg query per interrogare dinamicamente il registro, trovando qualsiasi versione 3.x installata senza lista hardcoded. Più robusto. Usa **"Add Python to PATH"** per la ricerca della versione in uso.

1. Messaggi di errore

`Avvio SONGPRESS2.vbs`: messaggi brevi e tecnici (mostra il path grezzo), senza titolo nella finestra.
`Avvio SONGPRESS.vbs`: messaggi più user-friendly, con titolo "Songpress - Errore avvio" e, in caso di Python mancante, suggerisce dove scaricarlo (python.org) e cosa fare durante l'installazione.

In sintesi: `Avvio SONGPRESS2.vbs` è la versione di sviluppo/debug, `Avvio SONGPRESS.vbs` è la versione rifinita per l'utente finale.

## Installazione su Linux

(Mai testata)

## Installazione su MAC

(Mai testata)

## Lingua interfaccia

- Inglese
- Italiano

## Funzionalità principali

### Editing
- Produzione di **spartiti per chitarra di alta qualità** (testo e accordi)
- **Facile** da imparare, veloce da usare
- **Autocomplete ChordPro (IntelliSense)**: le direttive vengono suggerite e completate automaticamente durante la digitazione, con inserimento intelligente delle parentesi e dei due punti
- **Supporto per multicursore**: possibilità di creare e lavorare con più cursori simultaneamente
- **Trova e Sostituisci**: dialogo unificato con due tab (Trova / Sostituisci), ricerca per parola intera, distinzione maiuscole/minuscole e **espressioni regolari**, con colore di evidenziazione configurabile e cronologia delle ricerche
### Strumenti
- **Verifica sintattica**: controlla la sintassi ChordPro e salta direttamente a ogni errore trovato nel documento
- **Statistiche brano** (`F8`): analizza il brano aperto e mostra un dialogo riepilogativo con valutazione della difficoltà (1–5 stelle), struttura (strofe, ritornelli, bridge, pagine stimate), conteggio parole, complessità degli accordi e durata — dichiarata tramite `{duration:MM:SS}` o stimata automaticamente da `{tempo:}` e `{time:}`
- **Nuovo da template**: crea un nuovo brano a partire da un template ChordPro preconfezionato

### Accordi
- **Trasposizione degli accordi** con rilevamento automatico della tonalità
- **Semplificazione degli accordi** per chitarristi principianti: individua la tonalità più facile da suonare e traspone la canzone automaticamente
- **Propagazione degli accordi**: copia gli accordi dalla prima strofa (o dal primo ritornello) a tutte le strofe (o ritornelli) successivi con lo stesso numero di righe, con un solo clic
- **Integrazione degli accordi**: unisce gli accordi copiati negli appunti nella selezione corrente (*Incolla accordi*)
- **Sposta accordo a destra / sinistra**: posiziona con precisione i singoli accordi lungo la riga del testo
- **Rimuovi accordi**: elimina tutti gli accordi dal testo, conservando solo il testo
- Supporto per diverse **notazioni degli accordi**: americana (C, D, E), italiana (Do, Re, Mi), francese, tedesca e portoghese; con conversione tra notazioni
- Supporto per i formati di accordi **ChordPro e Tab** (su due righe); rilevamento automatico e conversione da Tab a ChordPro

> **Perché preferire il formato ChordPro al Tab?**
>
> Il formato **Tab** (o "a due righe") affianca gli accordi al testo su righe separate, allineandoli spazialmente carattere per carattere. Sebbene sia semplice da digitare, presenta limiti importanti: è fragile rispetto ai cambi di font o dimensione del testo, difficile da modificare senza rompere l'allineamento, e non portabile tra applicazioni diverse.
>
> Il formato **ChordPro** incorpora invece gli accordi direttamente nel testo tra parentesi quadre (es. `Amaz[G]ing grace`), rendendoli indipendenti dalla formattazione visiva. I vantaggi sono significativi:
> - **Robustezza**: l'accordo è legato alla parola, non alla colonna; cambiare font o dimensione non rompe mai il layout
> - **Modificabilità**: aggiungere o rimuovere parole non richiede di riallineare manualmente tutti gli accordi
> - **Trasposizione affidabile**: la trasposizione automatica funziona in modo preciso perché gli accordi sono strutturalmente distinti dal testo
> - **Portabilità**: il formato ChordPro è uno standard aperto, riconosciuto da decine di applicazioni su tutte le piattaforme
>
> Per questi motivi, Songpress++ supporta la **conversione automatica da Tab a ChordPro** ed è consigliabile convertire i brani nel formato ChordPro prima di lavorarci.

### Formattazione e impaginazione
- **Posizionamento accordi**: visualizza gli accordi sopra o sotto il testo
- **Mostra/nascondi accordi**: cursore per mostrare l'intero brano, solo un pattern di accordi per strofa, o nessun accordo
- **Etichette strofe e ritornelli**: attiva/disattiva le etichette, con testo del ritornello personalizzabile
- **Etichette strofa personalizzate**: inserisce strofe con etichetta custom o senza etichetta
- **Inserimento blocchi strutturati**: inserisce rapidamente dal menu strofa, strofa numerata, ritornello, bridge, blocco accordi e blocco griglia
- **Metadati**: inserisce dal menu titolo, sottotitolo, artista, compositore, album, anno, copyright, tonalità, capotasto, tempo, metro e durata
- **Inserimento simboli musicali**: dialogo dedicato per inserire simboli musicali speciali nel testo
- **Inserimento diagrammi di accordi** (*klavier*): inserisce diagrammi di diteggiatura, con colore di evidenziazione e numerazione delle dita configurabili
- **Spaziatura righe e pagine**: inserisce spaziatura riga personalizzata, spaziatura sopra gli accordi, interruzioni di pagina manuali (`{new_page}`) e interruzioni di colonna
- **Linee di interruzione pagina e colonna**: guide visive mostrate nel pannello di anteprima
- **Visualizzazione battiti di durata**: mostra indicatori ritmici nell'anteprima

### Anteprima e stampa
- **Pannello di anteprima in tempo reale**: il brano formattato si aggiorna mentre si digita; il pannello è agganciabile e ridimensionabile
- **Visualizzazione di tempo, metro e tonalità** nell'intestazione dell'anteprima, con dimensione icona configurabile
- **Visualizzazione griglia accordi**: modalità di rendering della griglia configurabile (stile barra), etichetta predefinita e direzione del ridimensionamento
- **Formato pagina e margini**: formato carta e margini top/bottom/left/right configurabili, salvati tra le sessioni
- **Layout multi-colonna**: stampa o anteprima del brano su una o due colonne per pagina
- **Due pagine per foglio**: stampa due pagine logiche affiancate su un singolo foglio fisico
- **Adatta alla pagina / riduci automaticamente**: ridimensiona il brano per evitare il ritaglio del contenuto in fondo alla pagina
- **Anteprima di stampa**: anteprima completa prima di stampare
- **Stampa**: stampa il brano o esporta in PDF, con supporto per interruzioni di pagina esplicite tramite i comandi `{new_page}` / `{np}`
- **Crea canzoniere**: genera una raccolta PDF completa da tutti i brani presenti in una cartella selezionata

### Esportazione e appunti
- Possibilità di **incollare le canzoni formattate** come immagine vettoriale in qualsiasi applicazione Windows o Linux (Affinity, Microsoft Word, LibreOffice, Microsoft Publisher, Inkscape, ecc.)
- **Copia come immagine**: copia il brano formattato (o le strofe selezionate) negli appunti come Windows Metafile (WMF) su Windows, o come SVG + PNG su Linux
- **Esportazione in EMF** (Windows Metafile, solo Windows) e in formato **vettoriale SVG**
- **Esportazione in PNG** e **HTML** (pagine web complete o frammenti)
- **Copia solo testo**: copia il testo del brano senza accordi negli appunti

### Pulizia e importazione
- **Pulizia di righe vuote spurie**: rileva e rimuove automaticamente le righe vuote in eccesso (tipiche nei brani copiati da pagine web)
- **Normalizza notazione accordi**: uniforma le notazioni degli accordi non omogenee nel documento
- **Normalizza spazi multipli**: rimuove gli spazi in eccesso nel testo
- **Importa da PDF**: estrae il testo di un brano da un file PDF e lo apre per la modifica

### Interfaccia e preferenze
- **Interfaccia bilingue**: italiano e inglese
- **Editor personalizzabile**: tipo e dimensione del carattere, colore di sfondo, colore di selezione e colorazione sintattica per elemento (testo normale, ritornello, accordi, comandi, attributi, commenti, griglia tab)
- **Guida integrata**: visualizzatore di aiuto con rendering Markdown, controllo zoom (50 %–200 %), tema chiaro/scuro, modalità a schermo intero e ricerca nel documento
- **Posizione e dimensioni finestra**: salva e ripristina l'ultima posizione e il layout della finestra (prospettiva AUI)

## Immagini programma

![Songpress++ cambio nome e versione](src/songpressPlusPlus/img/GUIDE/Schermata_principale_it.png)

![Songpress++ cambio nome e versione](src/songpressPlusPlus/img/GUIDE/Menu_contestuale_it.png)

## Aggiungere una nuova direttiva ChordPro (guida per sviluppatori)

Per aggiungere una nuova direttiva (es. `{miocomando: valore}`) è necessario modificare fino a **sei file**, a seconda che la direttiva sia un puro metadato, produca un output visivo nell'anteprima, o abbia un'azione UI dedicata.

### 1. `Renderer.py` — parsing ed esecuzione *(sempre richiesto)*

È il file centrale. All'interno del metodo `Render()`, trovare la catena `elif cmd == ...` e aggiungere un nuovo ramo:

```python
elif cmd == 'miocomando':
    a = self.GetAttribute()
    if a is not None and a.strip():
        # usare a.strip()
```

Le **direttive solo-metadato** (non visualizzate nell'anteprima) vanno invece aggiunte alla tupla di consumo silenzioso già esistente:

```python
elif cmd in ('sorttitle', 'keywords', ..., 'duration', 'miocomando'):
    self.GetAttribute()   # consuma il token `:valore` senza usarlo
```

### 2. `SyntaxChecker.py` — validazione *(sempre richiesto)*

Aggiungere `"miocomando"` a **due** insiemi dentro `_validate_command()`:

- **`_KNOWN_COMMANDS`** — marca la direttiva come riconosciuta (evita errori "comando sconosciuto").
- **`_REQUIRES_VALUE`** — se la direttiva richiede un valore non vuoto; oppure **`_OPTIONAL_VALUE`** — se può essere usata senza valore per ripristinare un default.

Facoltativamente, aggiungere una funzione dedicata `_validate_miocomando()` per validazioni di formato (vedere `_validate_beats_time()` come riferimento) e chiamarla in fondo a `_validate_command()`.

### 3. `SongpressFrame.py` — IntelliSense e azione UI opzionale *(sempre richiesto)*

- Aggiungere `'miocomando'` a `_CHORDPRO_DIRECTIVES` — fa apparire la direttiva nel popup di completamento automatico **Ctrl+Spazio**.
- Se la direttiva non accetta valore (si chiude subito con `}`), aggiungerla a `_DIRECTIVES_NO_VALUE`.
- Se si vuole una **voce di menu** per inserire la direttiva, aggiungere un metodo handler `OnInsertMiocomando()` e collegarlo con `Bind(self.OnInsertMiocomando, 'insertMiocomando')`.

### 4. `songpress.xrc` + `songpress_it.xrc` — voci di menu *(solo se si aggiunge una voce di menu)*

Aggiungere un blocco `wxMenuItem` nella sezione `<object class="wxMenu">` appropriata:

```xml
<object class="wxMenuItem" name="insertMiocomando">
  <label>_Mio comando {miocomando:}...</label>
  <accel></accel>
  <help>Inserisci la direttiva ChordPro per ...</help>
</object>
```

Aggiungere lo stesso blocco con l'etichetta inglese in `songpress.xrc`.

### 5. `gui.fbp` — sorgente wxFormBuilder *(solo se si aggiunge una voce di menu)*

Aggiungere il corrispondente oggetto `wxMenuItem` nel file di progetto wxFormBuilder, specchiando la voce XRC. Questo mantiene il designer visuale sincronizzato con i file XRC.

### 6. `PreferencesDialog.po` + file di traduzione *(solo se si aggiungono stringhe UI)*

Se la nuova direttiva introduce nuove stringhe traducibili (etichette, tooltip, messaggi di errore), aggiungere le corrispondenti coppie `msgid` / `msgstr` nel file `.po`.

---

### Riferimento rapido — checklist dei file

| File | Quando modificare |
|---|---|
| `Renderer.py` | Sempre — aggiungere il ramo `elif cmd == 'miocomando':` |
| `SyntaxChecker.py` | Sempre — aggiungere a `_KNOWN_COMMANDS` e `_REQUIRES_VALUE` / `_OPTIONAL_VALUE` |
| `SongpressFrame.py` | Sempre — aggiungere a `_CHORDPRO_DIRECTIVES`; opzionalmente aggiungere handler di menu |
| `songpress.xrc` | Solo se si aggiunge una voce di menu (UI inglese) |
| `songpress_it.xrc` | Solo se si aggiunge una voce di menu (UI italiana) |
| `gui.fbp` | Solo se si aggiunge una voce di menu (sorgente wxFormBuilder) |
| `PreferencesDialog.po` | Solo se si aggiungono nuove stringhe traducibili |



### Linux: esportazione SVG e scaling del display

Quando il fattore di scala del display di sistema non è impostato su 1, l'output SVG prodotto dalla funzione Copia come immagine potrebbe essere formattato in modo errato. Si tratta di un problema noto nella versione attuale di wxPython. Il problema sottostante [è già stato risolto a monte in wxWidgets](https://github.com/wxWidgets/wxWidgets/issues/25707) e verrà corretto automaticamente non appena sarà disponibile la prossima versione di wxPython.

## Crediti

**Songpress++** è un fork di *Songpress* di Luca Allulli - Skeed, mantenuto ed esteso da Denisov21.

- Sito web versione originale: <http://www.skeed.it/songpress>
- Repository fork: <https://github.com/Denisov21/Songpressplusplus>

---
*Questo file è codificato UTF-8 senza BOM.*
