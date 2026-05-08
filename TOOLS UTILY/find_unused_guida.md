# Guida — `find_unused.py`

Script Python per trovare i file `.py` non referenziati in un progetto, così da identificare quelli potenzialmente eliminabili.

---

## Requisiti

- Python 3.9 o superiore installato
- PowerShell (incluso in Windows 10/11)

---

## Installazione

1. Scarica `find_unused.py`
2. Copialo nella cartella del progetto da analizzare (stessa cartella dei file `.py`)

---

## Utilizzo

### Passo 1 — Apri PowerShell

Premi <kbd>Win</kbd> + <kbd>R</kbd>, digita `powershell`, premi <kbd>Invio</kbd>.

### Passo 2 — Entra nella cartella del progetto

```powershell
cd "E:\Users\Utente\Downloads\SongpressV56 OK - BUGFIX\SongpressPlusPlus\src\songpressPlusPlus"
```

> Sostituisci il percorso con quello reale del tuo progetto.

### Passo 3 — Esegui lo script

```powershell
python find_unused.py .
```

Il punto `.` significa *"analizza la cartella corrente"*. Puoi anche specificare un percorso assoluto:

```powershell
python find_unused.py "E:\percorso\al\progetto"
```

### Passo 4 — Salva l'output su file (opzionale)

```powershell
python find_unused.py . > risultato.txt
```

Apri poi `risultato.txt` con il Blocco Note o VS Code per leggere comodamente l'elenco.

---

## Interpretare i risultati

### 🗑️ FILE POTENZIALMENTE ELIMINABILI

Nessun altro file `.py` del progetto li importa o li referenzia testualmente. Esempio di output:

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

## Controllare un file specifico con PowerShell

Se vuoi verificare manualmente se un singolo file è usato, esegui:

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

> ⚠️ Non eliminare mai i file direttamente. Segui questi passi:

1. Crea una sottocartella `_da_eliminare` nella cartella del progetto
2. **Sposta** (non copiare) i file candidati in `_da_eliminare`
3. Avvia il programma e verifica che funzioni correttamente
4. Se tutto funziona, svuota `_da_eliminare` e cancella la cartella
5. Se qualcosa si rompe, sposta i file di ritorno nella posizione originale

---

## Limitazioni

Lo script usa l'**analisi testuale** degli import: legge i file `.py` e cerca pattern come `import NomeFile` e `from .NomeFile import`. Questo significa che:

- Funziona correttamente per import standard Python
- Potrebbe non rilevare referenze tramite XRC, `__import__()`, o `importlib`
- Potrebbe segnalare come "non usato" un file che viene caricato solo a runtime

In caso di dubbio, usa sempre la procedura sicura descritta sopra.
