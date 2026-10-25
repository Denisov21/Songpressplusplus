# Installer Songpress++ — note sulle modifiche

File interessati: `songpress__x64.nsi` e `songpress__x86.nsi`.

## Problema

Durante `uv tool install` la schermata di installazione sembrava bloccata:
la barra di avanzamento non si muoveva e il log restava fermo.

## Cosa è stato modificato

1. **Barra di avanzamento scorrevole** (`BusyBarStart` / `BusyBarStop`)
   Durante `uv` la barra passa in modalità "marquee" (`PBS_MARQUEE`, `PBM_SETMARQUEE`)
   e scorre in continuazione. Alla fine torna normale.

2. **Rotella di testo** (`RunUvSpinner`)
   `uv` viene lanciato in modo asincrono con `ExecDos`. Finché è in esecuzione,
   il sottotitolo della finestra mostra `Installazione in corso, attendere... |/-\`
   aggiornato ogni 120 ms. A fine installazione il sottotitolo originale viene ripristinato.
   Se `ExecDos` non parte, si usa `nsExec` (senza rotella).

3. **Elenco pacchetti nel log** (`UvLogPump`)
   `uv` scrive l'output su un file (`cmd.exe /c ... > log 2>&1`).
   Ogni giro del ciclo si copia il file con `CopyFile` (perché `uv` lo tiene aperto
   in scrittura e `FileOpen` non riuscirebbe ad aprirlo) e si mostrano con `DetailPrint`
   le righe complete nuove.

4. **Codifica dei file**
   Aggiunto il BOM UTF-8 in testa ai due `.nsi`. Senza BOM, NSIS legge il file come ANSI
   e gli accenti e il simbolo ⚠ compaiono rovinati (`installerÃ`, `âš`).
   Salvare sempre i file come "UTF-8 con BOM".

## Plugin NSIS necessari

Gli script usano `Unicode true`, quindi NSIS carica solo le cartelle `*-unicode`.

| Installer | Cartella plugin   |
|-----------|-------------------|
| x64       | `amd64-unicode`   |
| x86       | `x86-unicode`     |

Plugin usati dagli script: `ExecDos`, `nsExec`, `NScurl`, `nsDialogs`, `System`, `StartMenu`.
La cartella `x86-ansi` non viene usata.

## Da verificare alla prossima compilazione

- La rotella gira per tutta la durata di `uv`.
- Le righe di `uv` (`Resolved N packages...`, pacchetti scaricati) compaiono nel log.
- Gli accenti nelle pagine dell'installer sono corretti.
- Il codice di uscita di `uv` viene letto correttamente (controllo finale su `SongPressPlusPlus.exe`).
