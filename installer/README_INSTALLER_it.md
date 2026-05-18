# Come compilare il programma di installazione Windows

Per compilare il programma di installazione Windows è necessario scaricare:

- I binari Windows x64 di `uv`, ad esempio [Releases · astral-sh/uv](https://github.com/astral-sh/uv/releases/)
- Il [compilatore NSIS](https://nsis.sourceforge.io/Download) — scaricare la versione **64 bit** (`amd64` / `x64`), che compila sia installer a 64 bit sia a 32 bit. La versione a 32 bit (`x86`) non supporta la compilazione per `amd64`.
  Per uso in CI/CD: [Install NSIS compiler 64bit · GitHub Actions Marketplace](https://github.com/marketplace/actions/install-nsis-compiler)

Estrarre `uv.exe` dallo zip nella sottocartella corrispondente all'architettura:

- `uv-x86_64\uv.exe` — per l'installer a **64 bit** (architettura x86_64 / AMD64, la più comune sui PC moderni)
- `uv-i686\uv.exe` — per l'installer a **32 bit** (architettura i686 / x86, per sistemi a 32 bit o per distribuire un installer universale)

Gli script `.nsi` puntano direttamente a queste sottocartelle — non è necessario copiare `uv.exe` nella cartella `installer\` principale.

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
├── uv-x86_64/               ← uv per installer 64 bit (x86_64 / AMD64)
│   └── uv.exe
├── uv-i686/                 ← uv per installer 32 bit (i686 / x86)
│   └── uv.exe
└── tools/
    ├── rcedit-x64.exe
    ├── rcedit-i686.exe
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
| `rcedit-i686.exe` | Tool da riga di comando per incorporare un'icona in un `.exe` Windows (sistemi 32 bit) |
| `set_iconx64.bat` | Script di supporto per sistemi **64 bit** — usa `rcedit-x64.exe` |
| `set_iconx86.bat` | Script di supporto per sistemi **32 bit** — usa `rcedit-i686.exe` |

### Come usare i bat

Eseguire il bat appropriato **dopo** aver compilato l'applicazione con cx_Freeze e **prima**
di compilare l'installer NSIS, in modo che il `.exe` finale abbia già l'icona corretta.

- Su sistemi **64 bit**: usare `set_iconx64.bat`
- Su sistemi **32 bit**: usare `set_iconx86.bat`

1. Fare doppio clic sul bat corretto (richiederà i privilegi di amministratore automaticamente)
2. Quando richiesto, trascinare `SongPressPlusPlus.exe` nella finestra (oppure incollare il percorso)
3. Quando richiesto, trascinare `songpressplusplus.ico` nella finestra (oppure incollare il percorso)
4. Lo script applicherà l'icona, confermerà il successo e **riavvierà automaticamente Explorer** per aggiornare la cache delle icone

> **Download rcedit**: https://github.com/electron/rcedit/releases — scaricare entrambi
> `rcedit-x64.exe` e `rcedit-i686.exe` e posizionarli nella cartella `tools/`.

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



## Icona mancante sull'exe e nel menu "Apri con" — risolto nel file .nsi

![Songpress++ problema con Apri con](../src/songpressplusplus/img/GUIDE/Powershell_it.png)

**Sintomo:** Dopo l'installazione, `SongPressPlusPlus.exe` non mostra l'icona in
Esplora file, nel menu contestuale "Apri con" e nella barra delle applicazioni.

**Causa:** `uv tool install` genera l'exe senza icona incorporata.

**Fix applicato negli script `.nsi`:** Durante l'installazione, `rcedit` viene estratto
in `$PLUGINSDIR` e incorpora automaticamente l'icona nell'exe subito dopo che `uv`
lo ha creato:

```nsi
; 6b. Incorpora icona nell'exe tramite rcedit
!if /FileExists "${SRCDIR}\installer\tools\rcedit-x64.exe"
  File "/oname=$PLUGINSDIR\rcedit.exe" "${SRCDIR}\installer\tools\rcedit-x64.exe"
!endif
${If} ${FileExists} "$PLUGINSDIR\rcedit.exe"
  nsExec::ExecToLog '"$PLUGINSDIR\rcedit.exe" "$SongpressExe" --set-icon "$INSTDIR\songpressplusplus.ico"'
  Pop $0
${EndIf}
```

`rcedit` viene estratto in `$PLUGINSDIR` (cartella temporanea di NSIS, eliminata al
termine) e non viene incluso nell'installazione finale.

**Workaround manuale (con installer precedenti):** Usare il bat `tools\set_iconx64.bat`
(o `set_iconx86.bat` su 32 bit) — trascinare l'exe e l'ico quando richiesto. Il bat
aggiorna automaticamente la cache icone di Windows e riavvia Explorer.

> **Nota:** Se si reinstalla Songpress++ tramite `uv tool install` senza ricompilare
> l'installer, l'exe viene sovrascritto e l'icona va persa. Ricompilare l'installer
> con il file `.nsi` aggiornato per incorporare l'icona automaticamente a ogni installazione.

## Collegamento nel menu Start mancante — risolto nel file .nsi

**Sintomo:** Dopo un'installazione standard, Songpress++ non appare nella griglia delle
app del menu Start di Windows 11.

**Causa:** Se `DoInstallLocal` chiama `Abort` (ad esempio perché `uv` fallisce o l'exe
non viene trovato), l'esecuzione esce dalla `Section` principale prima che il
collegamento nel menu Start venga creato.

**Fix applicato negli script `.nsi`:** Nella `Section -Post` (eseguita sempre,
anche in caso di `Abort`) è stato aggiunto un blocco di fallback che ricrea il
collegamento se mancante, e forza l'aggiornamento della cache di Windows tramite
`SHChangeNotify`. Inoltre, nella pagina finale del wizard viene mostrato il messaggio:

- 🇮🇹 *Per completare l'installazione e visualizzare Songpress++ nel menu Start, è consigliato riavviare il computer.*
- 🇬🇧 *To complete the installation and make Songpress++ appear in the Start menu, it is recommended to restart your computer.*

```nsi
; Section -Post — fallback collegamento + notifica Windows
${If} $SongpressExe == ""
  StrCpy $SongpressExe "$INSTDIR\bin\SongPressPlusPlus.exe"
${EndIf}
!insertmacro MUI_STARTMENU_GETFOLDER Application $ICONS_GROUP
${Unless} ${FileExists} "$SMPROGRAMS\$ICONS_GROUP\Songpress++.lnk"
  CreateDirectory "$SMPROGRAMS\$ICONS_GROUP"
  CreateShortCut "$SMPROGRAMS\$ICONS_GROUP\Songpress++.lnk" \
    "$SongpressExe" "" "$INSTDIR\songpressplusplus.ico" 0
${EndUnless}
System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, i 0, i 0)'
```

**Workaround manuale (con installer precedenti):** Creare manualmente il collegamento:

1. Aprire `%APPDATA%\Microsoft\Windows\Start Menu\Programs\` in Esplora file
2. Creare una nuova cartella chiamata `Songpress++`
3. Navigare in `%LOCALAPPDATA%\Songpress++\bin\`, clic destro su `SongPressPlusPlus.exe` → *Crea collegamento*
4. Spostare il collegamento nella cartella creata al passo 2

> **Nota sul BOM:** NSIS richiede che i file `.nsi` siano in UTF-16 LE con BOM di 2 byte
> (`FF FE`). Un doppio BOM causa l'errore `Invalid command: "﻿;"` alla riga 1.
> Verificare che il file inizi con esattamente `FF FE` seguito dal primo carattere `;`.

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
