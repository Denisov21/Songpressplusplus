# Come compilare il programma di installazione Windows

Per compilare il programma di installazione Windows è necessario scaricare:

- I binari Windows x64 di `uv`, ad esempio [Releases · astral-sh/uv](https://github.com/astral-sh/uv/releases/)
- Il [compilatore NSIS](https://nsis.sourceforge.io/Download)

Estrarre `uv.exe` dallo zip in questa cartella.

> **Nota antivirus — `uv.exe` non è un virus:** Alcuni antivirus potrebbero segnalare
> `uv.exe` come sospetto a causa dell'euristica sui file eseguibili di nuova generazione.
> Si tratta di un **falso positivo**: `uv.exe` è uno strumento open source legittimo,
> sicuro e ampiamente diffuso nella comunità Python
> ([astral-sh/uv](https://github.com/astral-sh/uv)). Se il tuo antivirus lo blocca,
> aggiungi un'eccezione per la cartella `installer/`.

Avviare poi il compilatore NSIS e compilare lo script `.nsi` appropriato:

- **Installer a 64 bit**: compilare `songpress__x64.nsi`
- **Installer a 32 bit**: compilare `songpress__x86.nsi`

## Compilazione passo per passo

1. Apri il programma NSIS
2. Clicca su **Compile NSI scripts**
3. Premi **File → Load Script**
4. Seleziona `songpress__x64.nsi` (64 bit) oppure `songpress__x86.nsi` (32 bit)
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
├── songpress__x64.nsi
├── songpress__x86.nsi
├── songpressplusplus.ico
├── license.txt
├── uv-x86_64/
│   └── uv.exe
├── uv-i686/
│   └── uv.exe
└── tools/
    ├── rcedit-x64.exe
    ├── rcedit-x86.exe
    ├── set_iconx64.bat
    └── set_iconx86.bat
```

> La cartella `plugins/` non è necessaria: entrambi gli installer usano NScurl
> (built-in NSIS) e non richiedono DLL esterne.

## Cartella tools/

La cartella `tools/` contiene utility usate **solo durante la build** — non vengono
incluse nell'installer né nell'applicazione finale.

| File | Scopo |
|------|-------|
| `rcedit-x64.exe` | Tool da riga di comando per incorporare un'icona in un `.exe` Windows (sistemi 64 bit) |
| `rcedit-x86.exe` | Tool da riga di comando per incorporare un'icona in un `.exe` Windows (sistemi 32 bit) |
| `set_iconx64.bat` | Script di supporto per sistemi **64 bit** — usa `rcedit-x64.exe` |
| `set_iconx86.bat` | Script di supporto per sistemi **32 bit** — usa `rcedit-x86.exe` |

### Come usare i bat

Eseguire il bat appropriato **dopo** aver compilato l'applicazione con cx_Freeze e **prima**
di compilare l'installer NSIS, in modo che il `.exe` finale abbia già l'icona corretta.

- Su sistemi **64 bit**: usare `set_iconx64.bat`
- Su sistemi **32 bit**: usare `set_iconx86.bat`

1. Fare doppio clic sul bat corretto (richiederà i privilegi di amministratore automaticamente)
2. Quando richiesto, trascinare `SongPressPlusPlus.exe` nella finestra (oppure incollare il percorso)
3. Quando richiesto, trascinare `songpressplusplus.ico` nella finestra (oppure incollare il percorso)
4. Lo script applicherà l'icona e confermerà il successo

> **Download rcedit**: https://github.com/electron/rcedit/releases — scaricare entrambi
> `rcedit-x64.exe` e `rcedit-x86.exe` e posizionarli nella cartella `tools/`.

> **Nota antivirus**: Windows Defender potrebbe segnalare rcedit come `Exploit.PayloadProtect`.
> Si tratta di un **falso positivo** dovuto alla natura dello strumento (modifica binari exe).
> Per sbloccarlo: Sicurezza di Windows → Protezione da virus e minacce → Cronologia protezione
> → seleziona il rilevamento → Azioni → **Consenti nel dispositivo**.

La cartella `installer\` può essere posizionata ovunque all'interno dell'albero
del progetto. Lo script usa `SRCDIR = "${__FILEDIR__}\.."`, quindi `pyproject.toml`
viene sempre risolto in modo relativo al file `.nsi` stesso, indipendentemente
dalla directory di lavoro da cui viene lanciato NSIS.

## ⚠️ Non installare in Programmi

**Non installare Songpress++ nella cartella `C:\Program Files` o `C:\Program Files (x86)`.**

Queste cartelle sono protette da UAC (User Account Control) e richiedono privilegi di
amministratore per qualsiasi scrittura. Songpress++ scarica e aggiorna i propri pacchetti
a runtime tramite `uv`: se installato in `Program Files`, queste operazioni fallirebbero
silenziosamente o causerebbero errori di accesso negato.

Usare sempre i percorsi predefiniti proposti dall'installer (`%LOCALAPPDATA%` per
l'installazione standard, `%DESKTOP%` per quella portabile), che non richiedono privilegi
elevati.

## Percorsi di installazione

| Cosa | Percorso |
|------|----------|
| Applicazione (standard) | `%LOCALAPPDATA%\Songpress++\bin\SongPressPlusPlus.exe` |
| Applicazione (portabile) | `%DESKTOP%\Songpress++\bin\SongPressPlusPlus.exe` |
| Template canzoni (standard) | `%APPDATA%\Songpress++\templates\songs\` |
| Template slide (standard) | `%APPDATA%\Songpress++\templates\slides\` |
| Font (standard) | `%APPDATA%\Songpress++\templates\fonts\` |
| Template canzoni (portabile) | `<cartella installazione>\templates\songs\` |
| Template slide (portabile) | `<cartella installazione>\templates\slides\` |
| Font (portabile) | `<cartella installazione>\templates\fonts\` |

L'intera cartella `templates\` (incluse tutte le sottocartelle: `songs`, `slides`, `fonts`
e qualsiasi aggiunta futura) viene copiata ricorsivamente dall'albero del pacchetto uv
nella destinazione corretta durante l'installazione.

- **Installazione standard**: `%APPDATA%\Songpress++\templates\`
- **Installazione portabile**: `<cartella installazione>\templates\` (accanto all'exe)

In fase di disinstallazione viene chiesto se eliminare la cartella dati (default: No).

## Opzioni della pagina di installazione

| Opzione | Default | Descrizione |
|---------|---------|-------------|
| **Installazione standard** | ✔ | Installa in `%LOCALAPPDATA%\Songpress++`, crea scorciatoie nel menu Start |
| **Installazione portabile** | — | Installa in `%DESKTOP%\Songpress++`, nessuna voce nel registro né scorciatoie |
| **Associa estensioni** | ✔ | Associa `.crd .pro .chopro .chordpro .cho .tab` a Songpress++ |
| **Verifica connessione** | ✔ | Testa la connessione Internet prima di scaricare i pacchetti |
| **Collegamento sul Desktop** | ✔ | Crea un collegamento `.lnk` sul Desktop (solo installazione standard) |

La lingua dell'installer (italiano/inglese) viene selezionata all'avvio.

## Associazione file e pulizia ProgID legacy

Gli installer registrano le estensioni di file sotto il ProgID `SongpressPlusPlus.ChordPro`
nel registro utente (`HKCU\Software\Classes`).

Versioni precedenti dell'installer usavano i ProgID `Songpress.crd` e `Songpress.ChordPro`
(errati), che potevano impedire l'apertura dei file `.crd` con doppio clic anche dopo una
reinstallazione. Gli script `.nsi` attuali includono una **pulizia automatica** di entrambi
i ProgID legacy:

- **In fase di installazione**: prima di registrare le nuove associazioni, vengono rimossi
  `HKCU\Software\Classes\Songpress.crd`, `HKCU\Software\Classes\Songpress.ChordPro` e le
  relative voci `OpenWithProgids` per tutte le estensioni gestite (`.crd`, `.pro`, `.chopro`,
  `.chordpro`, `.cho`).
- **In fase di disinstallazione**: vengono rimossi entrambi i ProgID legacy e le relative
  voci `OpenWithProgids`; successivamente vengono rimossi in modo **selettivo** anche tutti
  i riferimenti a `SongpressPlusPlus.ChordPro`: il valore `Default` e la voce
  `OpenWithProgids` per ciascuna estensione gestita, più la chiave
  `HKCU\Software\Classes\SongpressPlusPlus.ChordPro`. Le chiavi `.EXT` stesse **non vengono
  cancellate**, per non rimuovere accidentalmente le associazioni di altri programmi
  eventualmente presenti sullo stesso sistema.

## Spazio richiesto visualizzato dal wizard

Il wizard mostra sempre **100 KB** come spazio richiesto, perché NSIS conta solo i file
fisicamente inclusi nel pacchetto (in questo caso la sola icona `.ico`). Il grosso
dell'installazione — Python, i pacchetti uv, i tool — viene scaricato e installato a
runtime da `uv tool install` e NSIS non può calcolarlo in anticipo.

Per mostrare una stima realistica, lo script include la direttiva `AddSize`:

```nsi
Section "Songpress++" SongpressSection
  SectionIn RO
  AddSize 117760   ; spazio stimato: ~115 MB (uv + Python + pacchetti)
  SetOutPath "$INSTDIR"
```

Il valore `117760` corrisponde a 115 MB (115 × 1024 KB). Se l'installazione reale
cambia dimensione in futuro, aggiorna questo valore misurando le cartelle
`$INSTDIR\bin`, `$INSTDIR\tools` e `$INSTDIR\python` dopo un'installazione completa.

## Modifica nome e versione programma

![Songpress++ cambio nome e versione](../src/songpressplusplus/img/GUIDE/Versione_it.png)

## Risultato finale

Se la compilazione va a buon fine, nella cartella `installer/` appariranno i file:

```
songpress++64bit-setup.exe         ← installer a 64 bit
songpress++x86-setup.exe           ← installer a 32 bit
```

### Ordine di build consigliato

1. Compilare l'applicazione con cx_Freeze
2. Eseguire `tools\set_iconx64.bat` (o `set_iconx86.bat` su 32 bit) per incorporare l'icona in `SongPressPlusPlus.exe`
3. Compilare lo script NSIS per generare l'installer

## Note

### SongpressOpen.pyw

Dopo l'installazione potrebbe essere presente nella cartella `bin\` il file
`SongpressOpen.pyw`. Si tratta di un residuo del Songpress originale di Luca Allulli
e non è referenziato da nessuna parte del progetto (né in `pyproject.toml` né negli
script NSI). **Può essere cancellato tranquillamente.**



### Verificare la versione di uv (PowerShell)

Sostituire `<percorso-installer>` con il percorso effettivo della cartella `installer\` sul proprio sistema.

**64 bit (`uv-x86_64`):**

```powershell
& "<percorso-installer>\uv-x86_64\uv.exe" --version
```

Esempio di output:

```
uv 0.11.14 (3fdfdc7d4 2026-05-12 x86_64-pc-windows-msvc)
```

**32 bit (`uv-i686`):**

```powershell
& "<percorso-installer>\uv-i686\uv.exe" --version
```

Esempio di output:

```
uv 0.11.14 (3fdfdc7d4 2026-05-12 i686-pc-windows-msvc)
```





---
*Questo file è codificato UTF-8 senza BOM.*
