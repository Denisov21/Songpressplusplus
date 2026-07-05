# Fix icona associazioni file (.crd, .pro, .chopro, .chordpro, .cho, .tab, .sng)

## Sintomo

Dopo l'installazione (o un aggiornamento) di Songpress++, i file con estensioni
associate all'app (es. `Santa Maria del cammino.crd`) mostrano l'icona
generica di Windows invece dell'icona di Songpress++, anche se l'app si apre
correttamente con doppio click.

## Causa

Windows gestisce le associazioni file/icona su **due livelli separati**:

1. **`HKCU\Software\Classes\.crd`** → scritto dall'installer, punta al ProgID
   (es. `SongpressPlusPlus.ChordPro`), che a sua volta definisce
   `DefaultIcon`. Questo è il livello che l'installer NSI gestisce con la
   macro `APP_ASSOCIATE`.

2. **`HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.crd\UserChoice`**
   → scritto da **Explorer stesso**, non dall'installer, la prima volta che
   l'utente apre un file con una certa app (o sceglie "Apri con → Usa
   sempre"). Questa chiave è protetta da un hash e ha **priorità** su
   `Software\Classes\.crd` per decidere sia l'app di apertura sia l'icona
   mostrata.

Il problema: l'installer, nelle versioni precedenti, usava ProgID diversi nel
tempo (`Songpress.crd`, poi `Songpress.ChordPro`, poi
`SongpressPlusPlus.ChordPro`). Ogni volta che un ProgID veniva sostituito, lo
script di installazione cancellava correttamente il vecchio ProgID legacy
(`DeleteRegKey HKCU "Software\Classes\Songpress.crd"` ecc.), **ma non
cancellava mai `FileExts\.crd\UserChoice`**.

Risultato: se `UserChoice` era rimasto puntato a un ProgID nel frattempo
cancellato, Explorer si ritrova a dover risolvere l'icona per un ProgID che
non esiste più nel registro → non trova nulla → mostra l'icona generica,
anche se l'associazione "vera" (`Software\Classes\.crd`) è scritta
correttamente e punta a un file `.ico` esistente.

## Fix nello script NSI

Aggiunta la macro `APP_CLEAR_USERCHOICE`, che cancella l'intera chiave
`FileExts\.ext` per ogni estensione gestita:

```nsis
!macro APP_CLEAR_USERCHOICE EXT
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.${EXT}"
!macroend
```

Richiamata per **tutte e 7 le estensioni gestite da Songpress++**: `crd`,
`pro`, `chopro`, `chordpro`, `cho`, `tab`, `sng`.

- **In installazione**, subito prima di ricreare le associazioni con
  `APP_ASSOCIATE`, così ogni installazione/aggiornamento riparte pulita e
  Explorer è costretto a ririsolvere icona/app dal registro corrente.
- **In disinstallazione**, insieme alla rimozione delle associazioni, per non
  lasciare residui.

Questo non richiede il consenso dell'utente né tocca chiavi protette: si
limita a **cancellare** la chiave, che Explorer poi ricrea da sé al prossimo
utilizzo, basandosi sui dati aggiornati.

**Copertura completa verificata:** ogni blocco dello script — pulizia ProgID
legacy (`OpenWithProgids`), `APP_CLEAR_USERCHOICE`, `APP_ASSOCIATE` e
`APP_UNASSOCIATE` — gestisce tutte e 7 le estensioni in modo identico, sia
nella versione x64 che x86 dell'installer. Non esistono estensioni "parziali"
o gestite solo in alcuni punti: se un'estensione è associata a Songpress++,
è coperta ovunque nello script.

## Fix per installazioni già esistenti

Per chi ha già installato una versione senza questa patch, non serve
reinstallare: basta ripulire le stesse chiavi `FileExts` a mano (o con lo
script `fix_icona_songpress.bat`, che lo fa già in automatico) e forzare il
refresh della cache icone di Explorer.

Lo script `fix_icona_songpress.bat` cicla su **tutte e 7 le estensioni** in
un unico passaggio:

```bat
for %%E in (crd pro chopro chordpro cho tab sng) do (
    reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.%%E" /f
)
rundll32.exe shell32.dll,SHChangeNotify 0x08000000 0 0 0
ie4uinit.exe -show
taskkill /f /im explorer.exe
start explorer.exe
```

Non serve eseguirlo più volte per estensioni diverse: una sola esecuzione
copre `crd`, `pro`, `chopro`, `chordpro`, `cho`, `tab` e `sng`
contemporaneamente.

## Se il problema persiste dopo il fix

Se dopo aver pulito le chiavi l'icona resta comunque generica, molto
probabilmente l'associazione stessa non è mai stata creata (es. checkbox
"Associa estensioni" non spuntata durante l'installazione). In tal caso:
tasto destro sul file → **Apri con** → **Songpress++** → **Usa sempre questa
app** — Windows scriverà una `UserChoice` nuova e corretta.

## File coinvolti

- `installer/songpress__x64.nsi`
- `installer/songpress__x86.nsi`
- `fix_icona_songpress.bat` (fix esterno one-shot per installazioni esistenti)
