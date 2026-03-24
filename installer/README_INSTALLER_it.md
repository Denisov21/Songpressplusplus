# Come compilare il programma di installazione Windows

Per compilare il programma di installazione Windows è necessario scaricare:

- I binari Windows x64 di `uv`, ad esempio [uv-x86\_64-pc-windows-msvc.zip](https://github.com/astral-sh/uv/releases/download/0.9.21/uv-x86_64-pc-windows-msvc.zip)
- Il [compilatore NSIS](https://nsis.sourceforge.io/Download)

Estrarre il contenuto dello zip di `uv` in questa cartella (è sufficiente `uv.exe`).
Avviare poi il compilatore NSIS e compilare lo script `songpress++-setup.nsi`.

## File NSI

Codifica del file NSI: UTF-8 con BOM.

```nsi
!addplugindir /x86-unicode "plugins"
!include "MUI2.nsh"
```

## Note

URL modificato: il controllo della connessione Internet usa `http://1.1.1.1/` — l'IP di Cloudflare,
che risponde sempre in pochi millisecondi senza SSL, evitando possibili blocchi TLS.

`inetc::head` → `inetc::get`: le richieste HEAD tramite INetC sono notoriamente inaffidabili su
Windows 10/11. L'uso di `get` scarica un body minimo e funziona in modo molto più stabile.
Il file temporaneo viene eliminato immediatamente dopo.

## Struttura delle cartelle

```
installer/
├── songpress++.nsi
├── songpressplusplus.ico
├── uv.exe
├── license.txt
└── plugins/
    └── INetC.dll      ← dallo zip di INetC, cartella Plugins\x86-unicode\
```

Percorso di installazione: `%LOCALAPPDATA%\Songpress-local\bin\songpress.exe`
