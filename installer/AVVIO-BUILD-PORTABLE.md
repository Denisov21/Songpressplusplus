# Come avviare la creazione della versione portabile di Songpress++

Lo script `installer\Build-Portable.ps1` crea uno ZIP portabile di Songpress++ usando cx_Freeze in un venv dedicato (`.venv-build`).

## Requisiti

- Windows con **PowerShell**
- **Python** installato e raggiungibile dal comando `python` (verifica con `python --version`)
- Connessione internet (alla prima esecuzione scarica le dipendenze: wxPython, cx_Freeze, ecc.)
- `pyproject.toml` nella radice del progetto, con la riga `version = "x.y.z"` e la sezione `[tool.cxfreeze.build_exe]`

## Avvio

1. Apri **PowerShell** (non serve l'amministratore).
2. Vai nella cartella del progetto (la **radice**, quella che contiene `pyproject.toml` e le cartelle `src` e `installer`).

   > ⚠️ **Nota:** il percorso qui sotto è solo un **esempio** ed è **da verificare**. Sostituiscilo con il percorso effettivo in cui hai clonato o estratto il progetto sul tuo sistema.

   ```powershell
   cd "E:\Users\Utente\Documents\GitHub\songpressplusplus"
   ```

   Verifica di essere nella cartella giusta:

   ```powershell
   Get-Location
   Test-Path .\pyproject.toml
   Test-Path .\installer\Build-Portable.ps1
   ```

   - `Get-Location` mostra il percorso corrente.
   - I due `Test-Path` devono rispondere entrambi `True`. Se uno risponde `False`, sei nella cartella sbagliata.
   - Suggerimento: in Esplora file, apri la cartella del progetto, clicca sulla barra degli indirizzi, copia il percorso e incollalo dopo `cd` tra virgolette.

3. Lancia lo script **con il bypass della policy di esecuzione** (su Windows PowerShell 5.1 gli script sono disabilitati di default, quindi il semplice `.\installer\Build-Portable.ps1` dà l'errore "L'esecuzione di script è disabilitata nel sistema in uso"):

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\installer\Build-Portable.ps1
   ```

   Il bypass vale solo per questo comando: le impostazioni di sistema non vengono modificate.

> Lo script usa `$PSScriptRoot`, quindi funziona anche se lo lanci dalla cartella `installer` con `-File .\Build-Portable.ps1`: la radice del progetto viene calcolata da sola come cartella padre.

### Alternative per l'errore "esecuzione di script disabilitata"

Solo per la sessione corrente (alla chiusura della finestra torna tutto come prima):

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\installer\Build-Portable.ps1
```

Se compare una richiesta di conferma, rispondi `S`.

In modo permanente, solo per il tuo utente:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

## Cosa fa lo script

| Passo | Operazione |
|-------|------------|
| 1 | Crea il venv `.venv-build` (o lo riutilizza se esiste) |
| 2 | Installa le dipendenze con pip |
| 3 | Esegue `cx_Freeze build_exe` (con `src` aggiunto a `PYTHONPATH`) |
| 4 | Individua la cartella prodotta in `build\` |
| 5 | Copia i font in `templates\fonts` |
| 6 | Crea lo ZIP in `dist\` |

La prima esecuzione richiede alcuni minuti (soprattutto per l'installazione delle dipendenze); le successive sono più veloci perché il venv viene riutilizzato.

## Risultato

Lo ZIP viene creato in:

```
dist\Songpress++-<versione>-portable.zip
```

La versione è letta da `pyproject.toml`. Per usare il programma: estrai lo ZIP in una cartella qualsiasi (anche su chiavetta) e avvia:

```
.\Songpress++.exe
```

## Avviare Songpress++ dallo ZIP

1. **Sblocca lo ZIP (consigliato)**: se lo hai scaricato o copiato da un altro computer, clic destro sul file `.zip` → **Proprietà** → spunta **Sblocca** → **OK**. Così Windows non blocca i file estratti.
2. **Estrai tutto**: clic destro sul file `.zip` → **Estrai tutto...** → scegli una cartella (anche su chiavetta USB). Non avviare il programma dall'interno dello ZIP: va prima estratto.
3. Apri la cartella estratta (lo ZIP contiene una cartella con i file del programma) e fai doppio clic su **`Songpress++.exe`**.

In alternativa, da PowerShell (sostituisci il percorso con quello reale della cartella estratta):

```powershell
cd "C:\Percorso\della\cartella\estratta"
.\Songpress++.exe
```

Note:

- Non spostare né eliminare i file e le cartelle accanto a `Songpress++.exe` (per esempio `templates\fonts`): il programma ne ha bisogno.
- Se Windows mostra "Windows ha protetto il PC" (SmartScreen), clicca su **Ulteriori informazioni** → **Esegui comunque**. Succede perché l'eseguibile non è firmato digitalmente.
- Se l'antivirus blocca o mette in quarantena l'eseguibile, aggiungi la cartella alle eccezioni e riestrai lo ZIP.
- Per una pulizia o un aggiornamento basta eliminare la cartella estratta ed estrarre il nuovo ZIP.

## Problemi comuni

- **`python` non riconosciuto**: Python non è nel PATH. Reinstallalo spuntando "Add Python to PATH" oppure usa il launcher `py`.
- **`Impossibile leggere la versione da pyproject.toml`**: manca la riga `version = "..."` all'inizio di una riga del file.
- **`No module named songpressPlusPlus`**: controlla che esista la cartella `src` con il package; lo script la aggiunge già a `PYTHONPATH`.
- **Errori su una dipendenza (es. wxPython, pyenchant)**: verifica che la versione di Python sia compatibile con quelle versioni di pacchetti.
- **Errori strani dopo aver modificato lo script a mano** (per esempio `Impossibile recuperare la variabile $Pip perché non è stata impostata`): è un problema di codifica. Windows PowerShell 5.1 legge come ANSI i file senza BOM e i caratteri speciali dello script (`—`, `─`) rompono le stringhe. Se vuoi evitare che il problema si ripresenti quando modifichi lo script a mano, salvalo sempre come “UTF-8 con BOM” (in VS Code: barra in basso → Salva con codifica → UTF-8 with BOM).
- **Build da zero**: se qualcosa resta incoerente, elimina le cartelle `.venv-build`, `build` e `dist` e rilancia lo script.
