# Come compilare il programma di installazione Windows

Per compilare il programma di installazione Windows è necessario scaricare:

- I binari Windows x64 di `uv`, ad esempio [Releases · astral-sh/uv](https://github.com/astral-sh/uv/releases/)
- Il [compilatore NSIS](https://nsis.sourceforge.io/Download)

Estrarre `uv.exe` dallo zip in questa cartella.
Avviare poi il compilatore NSIS e compilare lo script `.nsi` appropriato:

- **Installer a 64 bit**: compilare `songpressx++64bit.nsi`
- **Installer a 32 bit**: compilare `songpressx++x86.nsi`

## Compilazione passo per passo

1. Apri il programma NSIS
2. Clicca su **Compile NSI scripts**
3. Premi **File → Load Script**
4. Seleziona `songpress++64bit.nsi` (64 bit) oppure `songpress++x86.nsi` (32 bit)
5. Clicca **Compile**

## File NSI

Codifica del file NSI: **UTF-16 LE con BOM** (obbligatoria per la modalità Unicode di NSIS).

Lo script contiene:

```nsi
Unicode true
!include "MUI2.nsh"
```

Non sono necessarie DLL esterne né direttive `!addplugindir`: entrambi gli installer
usano **NScurl**, già incluso in NSIS.

La versione viene letta automaticamente da `pyproject.toml` tramite `!searchparse`,
quindi non è necessario aggiornarla manualmente nello script NSI.

## Plugin per la verifica della connessione Internet

Entrambi gli installer usano **NScurl** (built-in NSIS) — nessuna DLL esterna richiesta.

```nsi
NScurl::http GET "http://1.1.1.1/" "$INSTDIR\nettest.tmp" /TIMEOUT 10000 /END
Pop $0   ; "OK" oppure stringa di errore
Delete "$INSTDIR\nettest.tmp"
```

URL di test: `http://1.1.1.1/` — IP di Cloudflare, risponde sempre in pochi millisecondi
senza SSL, evitando possibili blocchi TLS.

## Struttura delle cartelle

```
installer/
├── songpress++64bit.nsi
├── songpress++x86.nsi
├── songpressplusplus.ico
├── uv.exe
└── license.txt
```

> La cartella `plugins/` non è più necessaria: entrambi gli installer usano NScurl
> (built-in NSIS) e non richiedono DLL esterne.

La cartella `installer\` deve trovarsi direttamente dentro la radice del progetto
(quella che contiene `pyproject.toml`), perché lo script usa `SRCDIR = ".."`.

## Percorsi di installazione

| Cosa | Percorso |
|------|----------|
| Applicazione (standard) | `%LOCALAPPDATA%\Songpress++\bin\songpress.exe` |
| Applicazione (portabile) | `%DESKTOP%\Songpress++\bin\songpress.exe` |
| Template canzoni (standard) | `%APPDATA%\Songpress++\templates\songs\` |
| Template slide (standard) | `%APPDATA%\Songpress++\templates\slides\` |
| Font (standard) | `%APPDATA%\Songpress++\templates\fonts\` |
| Template canzoni (portabile) | `%DESKTOP%\Songpress++\templates\songs\` |
| Template slide (portabile) | `%DESKTOP%\Songpress++\templates\slides\` |
| Font (portabile) | `%DESKTOP%\Songpress++\templates\fonts\` |

L'intera cartella `templates\` (incluse tutte le sottocartelle: `songs`, `slides`, `fonts`
e qualsiasi aggiunta futura) viene copiata ricorsivamente dall'albero del pacchetto uv
nella destinazione corretta durante l'installazione.

- **Installazione standard**: `%APPDATA%\Songpress++\templates\`
- **Installazione portabile**: `<cartella portabile>\templates\` (accanto all'exe)

In fase di disinstallazione viene chiesto se eliminare la cartella dati (default: No).

## Opzioni della pagina di installazione

| Opzione | Default | Descrizione |
|---------|---------|-------------|
| **Installazione standard** | ✔ | Installa in `%LOCALAPPDATA%\Songpress++`, crea scorciatoie nel menu Start |
| **Installazione portabile** | — | Installa in `%DESKTOP%\Songpress++`, nessuna voce nel registro né scorciatoie |
| **Associa estensioni** | — | Associa `.crd .pro .chopro .chordpro .cho` a Songpress++ |
| **Verifica connessione** | ✔ | Testa la connessione Internet prima di scaricare i pacchetti |
| **Collegamento sul Desktop** | ✔ | Crea un collegamento `.lnk` sul Desktop (solo installazione standard) |

La lingua dell'installer (italiano/inglese) viene selezionata all'avvio.

## Modifica nome e versione programma

![Songpress++ cambio nome e versione](../src/songpress/img/GUIDE/Versione_it.png)

## Risultato finale

Se la compilazione va a buon fine, nella cartella `installer/` appariranno i file:

```
songpress++64bit-setup.exe         ← installer a 64 bit
songpress++x86-setup.exe           ← installer a 32 bit
```

---
*Questo file è codificato UTF-8 senza BOM.*
