# Build portabile Songpress++ — ZIP con cx_Freeze

Alternativa all'installer NSIS: produce un archivio ZIP autonomo che non richiede
installazione. L'utente estrae e avvia `Songpress++.exe` direttamente.
Questa procedura è specifica per Windows; la build portabile produce un eseguibile
`.exe` e non è compatibile con macOS o Linux.

---

## Prerequisiti

| Requisito | Note |
|-----------|------|
| Python 3.12+ | Installato e nel `PATH` di sistema |
| Connessione internet | Per scaricare le dipendenze nel venv al primo avvio |

Non servono NSIS, uv, né alcun altro strumento esterno.

---

## Struttura cartelle richiesta

```
Songpressplusplus/
├── installer/
│   └── Build-Portable.ps1   ← script da eseguire
├── src/
│   └── songpress/
│       ├── img/
│       ├── locale/
│       ├── templates/
│       │   ├── songs/
│       │   ├── slides/
│       │   ├── themes/      ← temi colori sintassi (.ini)
│       │   └── fonts/       ← font .ttf opzionali
│       └── xrc/
├── pyproject.toml
└── ...
```

---

## Procedura

### 1. Apri PowerShell nella cartella del progetto

Sostituisci il percorso seguente con quello completo del tuo progetto Songpress++:

```powershell
cd "E:\Users\Utente\Downloads\SongpressV30\Songpressplusplus"
```

> **Nota:** Il percorso indicato è un esempio. Sostituiscilo con il percorso effettivo in cui hai clonato o estratto il progetto sul tuo sistema.

### 2. Consenti l'esecuzione di script (solo al primo utilizzo, una tantum per il sistema)

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

### 3. Sblocca lo script (solo al primo avvio)

Windows contrassegna i file scaricati da internet con una zona di sicurezza (NTFS
Alternate Data Stream "Zone.Identifier") che impedisce l'esecuzione degli script
PowerShell. Una volta rimosso il contrassegno, il comando non va ripetuto.

```powershell
Unblock-File .\installer\Build-Portable.ps1
```

### 4. Esegui lo script

```powershell
.\installer\Build-Portable.ps1
```

Lo script esegue automaticamente questi passi:

| Passo | Operazione |
|-------|-----------|
| 1 | Crea `.venv-build\` nella radice del progetto (solo al primo avvio) |
| 1b | Aggiorna pip nel venv (solo al primo avvio) |
| 2 | Installa cx_Freeze + tutte le dipendenze nel venv isolato |
| 3 | Esegue `cx_Freeze build_exe` usando la configurazione in `pyproject.toml` |
| 4 | Copia `templates\fonts\` nella cartella build se non già inclusa |
| 5 | Comprime in `dist\Songpress++-<versione>-portable.zip` |

---

## Output

```
dist/
└── Songpress++-3.0.1-portable.zip
    └── exe.win-amd64-3.12\      ← cartella da estrarre e distribuire
        ├── Songpress++.exe
        ├── python3xx.dll
        ├── wx/
        ├── img/
        ├── locale/
        ├── templates/
        │   ├── songs/
        │   ├── slides/
        │   ├── themes/
        │   └── fonts/
        ├── xrc/
        └── pyproject.toml
```

---

## Percorsi a runtime (modalità portabile)

| Cosa | Percorso |
|------|----------|
| Eseguibile | `<cartella estratta>\Songpress++.exe` |
| Template canzoni | `<cartella estratta>\templates\songs\` |
| Template slide | `<cartella estratta>\templates\slides\` |
| Temi colori | `<cartella estratta>\templates\themes\` |
| Font | `<cartella estratta>\templates\fonts\` |

Poiché `templates\` è accanto all'exe, Songpress++ lo rileva automaticamente
come installazione portabile (logica in `MyPreferencesDialog.OnOpenTemplatesFolder`).

---

## Tempi indicativi

| Operazione | Prima esecuzione | Esecuzioni successive |
|------------|-----------------|----------------------|
| Creazione venv + download dipendenze | 5–15 min | — (venv riutilizzato) |
| cx_Freeze build | 2–5 min | 2–5 min |
| Compressione ZIP | 1–2 min | 1–2 min |
| **Totale** | **~20 min** | **~7 min** |

---

## Dimensioni attese

| Cosa | Dimensione |
|------|-----------|
| Cartella build (non compressa) | ~150–250 MB |
| ZIP finale | ~80–130 MB |

La dimensione dipende principalmente da wxPython (~80 MB) e dalle DLL Python.

---

## Aggiornamento versione

La versione nel nome del ZIP viene letta automaticamente da `pyproject.toml`:

```toml
[project]
version = "3.0.1"   ← aggiorna qui, il resto è automatico
```

---

## Pulizia e risoluzione problemi

### Avviso aggiornamento pip durante la build

Se compare un messaggio come:

```
NOTICE: A new release of pip is available: 25.x → 26.x
```

pip è funzionante ma non aggiornato nel `.venv-build`. Per aggiornarlo, usa `&` e
le virgolette perché il percorso del progetto può contenere spazi:

```powershell
& "E:\Users\Utente\Downloads\SongpressV30_OK\Songpressplusplus\.venv-build\Scripts\python.exe" -m pip install --upgrade pip
```

> **Nota:** Sostituisci `E:\Users\Utente\Downloads\SongpressV30_OK\Songpressplusplus` con il percorso effettivo del tuo progetto.

In alternativa, attiva prima il venv e poi usa la forma breve:

```powershell
& "E:\Users\Utente\Downloads\SongpressV30_OK\Songpressplusplus\.venv-build\Scripts\Activate.ps1"
python -m pip install --upgrade pip
```

> **Nota:** Come sopra — sostituisci il percorso con quello effettivo del tuo progetto.

Questo avviso non blocca la build; l'aggiornamento è facoltativo.

---

### Ripartire da zero (venv + build)

```powershell
Remove-Item -Recurse -Force .venv-build, build
.\installer\Build-Portable.ps1
```

### Errore "Unable to create process" o "Impossibile trovare il file specificato"

Questo errore si verifica quando il `.venv-build` è stato creato in una cartella
precedente del progetto (ad esempio `SongpressV26`) e poi il progetto è stato
spostato o copiato in una nuova cartella (ad esempio `SongpressV28`).

I venv Python contengono path assoluti interni e **non sono spostabili**. Lo script
rileva il venv esistente e lo riutilizza, ma i path puntano alla vecchia posizione.

**Soluzione:** eliminare il venv e ricreare tutto da zero:

```powershell
Remove-Item -Recurse -Force .\.venv-build
.\installer\Build-Portable.ps1
```

Lo script creerà un venv nuovo con i path corretti della cartella attuale.

---

*Codifica file: UTF-8*
