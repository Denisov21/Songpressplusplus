# Guida — `find_unused.py`

Strumento Python per trovare i file `.py` non referenziati in un progetto, così da identificare quelli potenzialmente eliminabili.

Da questa versione è disponibile un'**interfaccia grafica** (finestra con selezione cartella, drag & drop e spostamento nel cestino). L'uso da **riga di comando** resta comunque disponibile.

---

## Novità di questa versione

- Interfaccia grafica (tkinter) multipiattaforma: Windows, Linux, macOS
- Selezione della cartella con **Sfoglia…** o con **trascinamento** (drag & drop)
- Comando **🗑 Cestina file inutilizzati…**: sposta i candidati **nel cestino** (non li elimina definitivamente)
- Barra dei menu: **File** (Apri cartella, Cestina, Esci) e **?** (Crediti)
- Uso da riga di comando ancora funzionante, per compatibilità con l'uso precedente

---

## Requisiti

- **Python 3.9** o superiore
- **tkinter** — su Windows è già incluso; su Debian/Ubuntu si installa con:

  ```bash
  sudo apt install python3-tk
  ```

### Dipendenze opzionali

Servono solo per due funzioni specifiche; senza di esse il programma funziona comunque.

| Pacchetto | A cosa serve | Installazione |
|---|---|---|
| `tkinterdnd2` | Abilita il **drag & drop** di una cartella sulla finestra | `pip install tkinterdnd2` |
| `send2trash` | Spostamento **nel cestino** affidabile su tutti i sistemi | `pip install send2trash` |

> Nota: su molti desktop Linux (incluso **KDE**) il cestino funziona anche senza `send2trash`, tramite `gio trash` o `trash-cli`. `send2trash` è comunque il metodo consigliato per la massima compatibilità.

---

## Installazione

1. Scarica `find_unused.py`
2. Copialo in una cartella qualsiasi (non deve necessariamente stare dentro il progetto)
3. (Facoltativo) installa le dipendenze opzionali qui sopra

---

## Utilizzo con l'interfaccia grafica

### Passo 1 — Avvia il programma

```bash
python find_unused.py
```

Senza argomenti si apre la finestra grafica.

### Passo 2 — Indica la cartella del progetto

In uno di questi modi:

- premi **📂 Sfoglia…** e seleziona la cartella, oppure
- **trascina** la cartella dal file manager dentro la finestra (richiede `tkinterdnd2`), oppure
- usa il menu **File → Apri cartella…** (<kbd>Ctrl</kbd>+<kbd>O</kbd>)

### Passo 3 — Analizza

Premi **🔍 Analizza** (o <kbd>Invio</kbd> nel campo del percorso). Se trascini una cartella, l'analisi parte automaticamente.

Il riquadro **Risultato** mostra l'elenco dei file potenzialmente eliminabili e di quelli in uso.

### Passo 4 — (Opzionale) Sposta nel cestino i file inutilizzati

Vedi la sezione [Cestinare i file inutilizzati](#cestinare-i-file-inutilizzati).

---

## Cestinare i file inutilizzati

Dopo un'analisi, il pulsante **🗑 Cestina file inutilizzati…** (o **File → Cestina file inutilizzati…**) diventa attivo se ci sono candidati.

1. Premi il pulsante: compare una **richiesta di conferma** con l'elenco dei file
2. Confermando, i file vengono **spostati nel cestino** — **non** eliminati definitivamente
3. Il programma riporta quanti file sono stati spostati ed eventuali errori, poi **rianalizza** la cartella

> Il cestino fa da rete di sicurezza: se ti accorgi che un file serviva, puoi ripristinarlo. Rimane comunque valido dare un'occhiata all'elenco prima di confermare (vedi [Limitazioni](#limitazioni)).

Se non è disponibile alcun metodo per il cestino, il programma **non tocca i file** e ti invita a installare `send2trash`.

---

## Utilizzo da riga di comando (opzionale)

Passando una cartella come argomento, il programma **non** apre la GUI ma stampa il risultato nel terminale, esattamente come nelle versioni precedenti.

### Linux / macOS

```bash
python find_unused.py "/percorso/al/progetto"
python find_unused.py .        # cartella corrente
```

### Windows (PowerShell)

Premi <kbd>Win</kbd> + <kbd>R</kbd>, digita `powershell`, premi <kbd>Invio</kbd>, poi:

```powershell
cd "E:\Users\Utente\Downloads\SongpressV56 OK - BUGFIX\SongpressPlusPlus\src\songpressPlusPlus"
python find_unused.py .
```

### Salvare l'output su file

```bash
python find_unused.py . > risultato.txt
```

Apri poi `risultato.txt` con un editor di testo per leggere comodamente l'elenco.

---

## Interpretare i risultati

### 🗑️ FILE POTENZIALMENTE ELIMINABILI

Nessun altro file `.py` del progetto li importa o li referenzia testualmente. Esempio:

```
======================================================================
  🗑️  FILE POTENZIALMENTE ELIMINABILI (2)
======================================================================
  • MyUpdatePanel.py
  • UpdatePanel.py
```

Questi file sono **candidati** all'eliminazione. Prima di cancellarli verifica che non siano:

- caricati dinamicamente da un file `.xrc` (cerca il nome nel file XRC)
- usati come plugin o entry point esterni (es. `setup.py`, `pyproject.toml`)
- referenziati tramite `__import__()` o `importlib.import_module()`

### ✅ FILE IN USO

Viene mostrato il primo file che li referenzia. Esempio:

```
======================================================================
  ✅  FILE IN USO (42)
======================================================================
  • FontFaceDialog.py
      ← SongpressFrame.py (+1 altri)
  • SongTokenizer.py
      ← Renderer.py (+3 altri)
```

---

## Controllare un file specifico

Per verificare manualmente se un singolo file è usato:

### Linux / macOS

```bash
grep -rl "NomeFile" --include="*.py" .
```

### Windows (PowerShell)

```powershell
Get-ChildItem -Recurse -Filter "*.py" . | Select-String "NomeFile"
```

Esempio per `MyUpdatePanel`:

```powershell
Get-ChildItem -Recurse -Filter "*.py" . | Select-String "MyUpdatePanel"
```

Se l'unico risultato è il file stesso → nessuno lo usa → puoi eliminarlo.

---

## Procedura sicura per l'eliminazione

Il comando **Cestina** già ti protegge (i file finiscono nel cestino e sono recuperabili). Se preferisci un margine ancora maggiore, o non hai un cestino disponibile:

1. Crea una sottocartella `_da_eliminare` nella cartella del progetto
2. **Sposta** (non copiare) i file candidati in `_da_eliminare`
3. Avvia il programma e verifica che funzioni correttamente
4. Se tutto funziona, svuota `_da_eliminare` e cancella la cartella
5. Se qualcosa si rompe, riporta i file nella posizione originale

---

## Limitazioni

Lo strumento usa l'**analisi testuale** degli import: legge i file `.py` e cerca pattern come `import NomeFile` e `from .NomeFile import`. Questo significa che:

- Funziona correttamente per import standard Python
- Potrebbe non rilevare referenze tramite XRC, `__import__()`, o `importlib`
- Potrebbe segnalare come "non usato" un file caricato solo a runtime

In caso di dubbio, usa il cestino (recuperabile) o la procedura sicura descritta sopra.

---

## Licenza

Distribuito secondo i termini della **GNU General Public License, versione 2 — e solo la versione 2 (GPL-2.0-only)**, come pubblicata dalla Free Software Foundation. Il programma è fornito **senza alcuna garanzia**.

Autore: **Denisov21**
