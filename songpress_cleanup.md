# songpress_cleanup.py

Script Python con GUI (tkinter) che scansiona e rimuove tutti i file, cartelle e chiavi di registro
lasciate da installazioni attuali o precedenti di Songpress++.

## Avvio

```
python songpress_cleanup.py
```

Nessuna dipendenza esterna — usa solo librerie standard Windows. Richiede Python su Windows.

## Cosa fa

- Scansiona automaticamente all'avvio tutti i percorsi e le chiavi di registro
- Mostra una tabella con colori: **verde** = selezionato, **giallo** = trovato (non selezionato), **grigio** = assente
- Gli elementi trovati sono pre-selezionati con ☑, cliccabili per togliere/rimettere la spunta
- Bottoni **Seleziona tutto** / **Deseleziona tutto** / **📂 Aggiungi cartella...**
- Prima di eliminare mostra un riepilogo con richiesta di conferma
- Cartelle → mandate nel cestino via `SHFileOperation` (recuperabili)
- Chiavi registro → eliminate definitivamente con `RegDeleteTree` (non vanno nel cestino)
- Dopo l'eliminazione la lista si aggiorna automaticamente

## Strategia di ricerca cartelle

Lo script usa una ricerca a più livelli per trovare installazioni su qualsiasi unità:

1. **Dal registro** — legge `UninstallString` da `HKCU\Software\Microsoft\Windows\CurrentVersion\Uninstall\Songpress++`
2. **Shell Folders reali** — legge i percorsi effettivi da `HKCU\...\Explorer\Shell Folders` (funziona anche su unità non-C:)
3. **Variabili ambiente** — fallback su `%LOCALAPPDATA%`, `%APPDATA%`, `%USERPROFILE%\Desktop`
4. **Scansione pattern su tutte le unità** — controlla i pattern tipici su ogni lettera di unità disponibile (A:–Z:)
5. **Scansione profonda su tutte le unità** — ricerca ricorsiva reale fino a 4 livelli di profondità su ogni unità, trova `Songpress++` in qualsiasi percorso non coperto dai pattern fissi
6. **Aggiunta manuale** — il pulsante **📂 Aggiungi cartella...** permette di aggiungere un percorso personalizzato (ad es. un'unità esterna o un percorso non standard)

I duplicati vengono rimossi automaticamente.

## Scansione in due fasi

La GUI mostra i risultati progressivamente:

- **Fase 1 — Scansione rapida** (sincrona, immediata): registro + Shell Folders + variabili ambiente + pattern fissi. I risultati compaiono subito all'avvio.
- **Fase 2 — Scansione profonda** (asincrona, in background): ricerca ricorsiva su tutte le unità. Le cartelle trovate vengono aggiunte alla lista in tempo reale; la barra di stato mostra l'avanzamento. Il pulsante **Elimina** è bloccato finché la scansione non è completata.

## Aggiunta manuale di una cartella

Il pulsante **📂 Aggiungi cartella...** apre un dialogo di selezione cartella e aggiunge il percorso scelto alla lista, utile per installazioni in unità personalizzate o percorsi non coperti dalla scansione automatica.

Comportamento:

- Se la cartella è già in lista viene mostrato un avviso e non viene aggiunta di nuovo
- Se la cartella esiste, viene pre-selezionata con ☑ e vengono aggiunte automaticamente anche le sue sottocartelle interne (`bin`, `tools`, `python`, `cache`) non ancora presenti in lista
- Se la cartella non esiste viene aggiunta comunque come **Assente** (utile per rimuovere voci di registro orfane senza cartella corrispondente)

## Percorsi cartelle controllati (pattern fissi)

Per ogni unità disponibile vengono controllati i seguenti pattern:

| Pattern | Etichetta |
|---------|-----------|
| `{drive}\Users\*\AppData\Local\Songpress++` | Installazione standard |
| `{drive}\Users\*\AppData\Roaming\Songpress++` | Dati utente |
| `{drive}\Users\*\Desktop\Songpress++` | Installazione portabile – Desktop |
| `{drive}\Users\*\OneDrive\Desktop\Songpress++` | Installazione portabile – OneDrive Desktop |
| `{drive}\Songpress++` | Cartella radice unità |
| `{drive}\Program Files\Songpress++` | Program Files |
| `{drive}\Program Files (x86)\Songpress++` | Program Files (x86) |
| `{drive}\Apps\Songpress++` | Cartella Apps |
| `{drive}\Programmi\Songpress++` | Programmi (IT) |

In aggiunta, la scansione profonda trova `Songpress++` in qualsiasi percorso arbitrario
(es. `D:\Lavoro\Tools\Songpress++`), saltando automaticamente cartelle di sistema
(`Windows`, `System32`, `$Recycle.Bin`, ecc.) per contenere i tempi.

## Chiavi di registro controllate (HKCU)

| Chiave | Descrizione |
|--------|-------------|
| `Software\Microsoft\Windows\CurrentVersion\Uninstall\Songpress++` | Disinstallatore |
| `Software\Microsoft\Windows\CurrentVersion\App Paths\SongPressPlusPlus.exe` | App Paths |
| `Software\Classes\SongpressPlusPlus.ChordPro` | ProgID attuale |
| `Software\Classes\Songpress.ChordPro` | ProgID legacy |
| `Software\Classes\Songpress.crd` | ProgID legacy |
| `Software\Classes\.crd` | Associazione `.crd` |
| `Software\Classes\.pro` | Associazione `.pro` |
| `Software\Classes\.chopro` | Associazione `.chopro` |
| `Software\Classes\.chordpro` | Associazione `.chordpro` |
| `Software\Classes\.cho` | Associazione `.cho` |
| `Software\Classes\.tab` | Associazione `.tab` |

Dopo l'eliminazione viene notificata la shell (`SHChangeNotify`) per aggiornare le associazioni file.

---
*Questo file è codificato UTF-8 senza BOM.*
