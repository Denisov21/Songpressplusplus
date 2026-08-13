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
│   └── songpressplusplus/
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

Il «percorso del progetto» è la cartella che contiene `pyproject.toml` e la
sottocartella `installer\` (cioè la radice del repo, non `installer\` né `src\`).

Portati in quella cartella con `cd`, racchiudendo il percorso tra virgolette
perché può contenere spazi. Esempio con un progetto sul Desktop:

```powershell
cd "<percorso-progetto>"
```

> **Nota:** Il percorso indicato è solo un esempio. Sostituiscilo con quello
> effettivo in cui hai clonato o estratto il progetto sul tuo sistema.

**Come ricavare il percorso esatto:** apri la cartella del progetto in Esplora
File, clicca sulla barra degli indirizzi in alto (il percorso diventa
selezionabile), copialo con `Ctrl+C` e incollalo dopo `cd ` tra virgolette.
In alternativa, tieni premuto `Shift`, clicca con il tasto destro sulla cartella
e scegli **«Copia come percorso»**: copia già il percorso completo con le
virgolette incluse.

> **Suggerimento:** una scorciatoia è aprire la cartella in Esplora File,
> digitare `powershell` nella barra degli indirizzi e premere `Invio`:
> PowerShell si apre già posizionato in quella cartella, saltando il `cd`.

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
| 1 | Crea `.venv-build\` nella radice del progetto (solo al primo avvio; poi riutilizzato) |
| 2 | Aggiorna pip e installa cx_Freeze + tutte le dipendenze pinnate (a ogni esecuzione) |
| 3 | Aggiunge temporaneamente `src\` a `PYTHONPATH` (così il package `songpressPlusPlus` è importabile) ed esegue `cx_Freeze build_exe` usando la configurazione in `pyproject.toml` |
| 4 | Individua la cartella build prodotta scegliendo la sottocartella di `build\` modificata più di recente (`build\exe.*` o `build\<nome>`). **Nota:** lo script *non* elimina la cartella `build\` prima della compilazione |
| 5 | Copia `templates\fonts\` nella cartella build se non già inclusa |
| 6 | Comprime la **cartella build** in `dist\Songpress++-<versione>-portable.zip` (la cartella viene inclusa come livello superiore dell'archivio) |

> **Nota su pip:** l'aggiornamento di pip e l'installazione delle dipendenze
> vengono eseguiti a **ogni** avvio, non solo al primo. Se i pacchetti sono già
> presenti, pip li segnala come soddisfatti e non scarica nulla.

### Dipendenze installate (pinnate)

Lo script installa cx_Freeze più i seguenti pacchetti nel venv isolato:

| Pacchetto | Vincolo di versione |
|-----------|---------------------|
| wxPython | `>=4.2.4,<5.0.0` |
| requests | `>=2.32.4,<3.0.0` |
| python-pptx | `>=1.0.2,<2.0.0` |
| pyshortcuts | `>=1.9.5,<2.0.0` |
| reportlab | `>=4.0.0,<5.0.0` |
| pypdf | `>=6.0.0,<7.0.0` |
| markdown | `>=3.4,<4.0.0` |
| mistune | `>=3.0.0,<4.0.0` |
| pywin32 | `>=308` (solo Windows, `sys_platform == 'win32'`) |

---

## Output

L'archivio include la cartella build come livello superiore, quindi dopo
l'estrazione `Songpress++.exe` si trova dentro una sottocartella
`exe.win-amd64-3.12\` (il nome dipende da piattaforma e versione di Python):

```
dist/
└── Songpress++-8.0.0-portable.zip   ← estrai e distribuisci
    └── exe.win-amd64-3.12/          ← livello intermedio creato da Compress-Archive
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

Dopo l'estrazione i file si trovano nella sottocartella `exe.win-amd64-3.12\`
(indicata qui sotto come `<cartella exe>`):

| Cosa | Percorso |
|------|----------|
| Eseguibile | `<cartella exe>\Songpress++.exe` |
| Template canzoni | `<cartella exe>\templates\songs\` |
| Template slide | `<cartella exe>\templates\slides\` |
| Temi colori | `<cartella exe>\templates\themes\` |
| Font | `<cartella exe>\templates\fonts\` |

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
version = "8.0.0"   ← aggiorna qui, il resto è automatico
```

---

## Build automatica con GitHub Actions (CI)

Oltre alla build locale descritta sopra, il repository include un workflow di
GitHub Actions — `.github/workflows/build-portable.yml` — che esegue **lo stesso**
`Build-Portable.ps1` sui runner Windows di GitHub. In questo modo puoi generare lo
ZIP portabile senza avere un PC Windows a disposizione: la compilazione avviene sul
cloud e produce esattamente lo stesso pacchetto della build locale.

Il workflow gira su `windows-latest` con **Python 3.13** e si può avviare in due modi.

### Avvio manuale (`workflow_dispatch`)

Utile per generare uno ZIP al volo, ad esempio per provare una modifica.

| Passo | Operazione |
|-------|-----------|
| 1 | Apri la tab **Actions** del repository su GitHub |
| 2 | Nella barra laterale seleziona il workflow **«Build portable (Windows)»** |
| 3 | Premi **Run workflow**, scegli il branch (di norma `main`) e conferma |
| 4 | Al termine apri l'esecuzione e scarica lo ZIP dalla sezione **Artifacts** in fondo alla pagina di riepilogo |

> **Nota:** l'avvio manuale produce **solo** l'artifact scaricabile. La
> pubblicazione sulla Release avviene esclusivamente con i tag di versione (vedi
> sotto), perché lo step finale è condizionato a
> `if: startsWith(github.ref, 'refs/tags/')`.

### Avvio automatico su tag di versione (`v*`)

Quando pubblichi un tag che inizia con `v` (es. `v8.0.0`), il workflow parte da
solo, costruisce lo ZIP e **lo allega automaticamente alla Release** di GitHub
corrispondente:

```bash
git tag v8.0.0
git push origin v8.0.0
```

> **⚠️ Nota:** il numero di versione del tag dovrebbe coincidere con quello in
> `pyproject.toml`, per mantenere coerenti Release e pacchetto.

> **Permessi.** Lo step che allega il file alla Release richiede il permesso
> `contents: write`, già dichiarato nel workflow:
>
> ```yaml
> permissions:
>   contents: write
> ```
>
> Se lo step di release fallisse con un errore di permessi, controlla in
> **Settings → Actions → General → Workflow permissions** che le action del
> repository non siano limitate alla sola lettura.

Poiché il workflow riusa lo stesso `Build-Portable.ps1`, lo ZIP prodotto dalla CI
è identico a quello che otterresti in locale (stessa struttura di cartelle e stessi
percorsi a runtime descritti sopra).

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
& "<percorso-progetto>\.venv-build\Scripts\python.exe" -m pip install --upgrade pip
```

> **Nota:** Sostituisci `<percorso-progetto>` con il percorso effettivo del tuo progetto.

In alternativa, attiva prima il venv e poi usa la forma breve:

```powershell
& "<percorso-progetto>\.venv-build\Scripts\Activate.ps1"
python -m pip install --upgrade pip
```

> **Nota:** Come sopra — sostituisci il percorso con quello effettivo del tuo progetto.

Questo avviso non blocca la build; l'aggiornamento è facoltativo.

---

### Ripartire da zero (venv + build)

Lo script **non** elimina la cartella `build\`: riutilizza la sottocartella più
recente. Per una ricompilazione davvero pulita elimina sia il venv sia `build\`
prima di rilanciare lo script:

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
