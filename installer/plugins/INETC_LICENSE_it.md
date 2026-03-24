# INetC NSIS Plugin — Licenza e istruzioni

## Informazioni

| Campo       | Valore |
|-------------|--------|
| Nome        | Inetc plug-in |
| Autore      | Takhir |
| Versioni successive | v1.0.4.4 Stuart "Afrow UK" Welch · v1.0.5.0–1.0.5.3 Anders |
| Licenza     | zlib/libpng |
| Download ufficiale | https://nsis.sourceforge.io/mediawiki/images/c/c9/Inetc.zip (81 KB) |
| Pagina wiki | https://nsis.sourceforge.io/Inetc_plug-in |
| Fork con colori personalizzati | https://github.com/DigitalMediaServer/NSIS-INetC-plugin/releases |

---

## Licenza (zlib/libpng)

```
INetC NSIS plug-in
Copyright (c) Takhir, Stuart "Afrow UK" Welch, Anders

This software is provided 'as-is', without any express or implied
warranty. In no event will the authors be held liable for any damages
arising from the use of this software.

Permission is granted to anyone to use this software for any purpose,
including commercial applications, and to alter it and redistribute it
freely, subject to the following restrictions:

1. The origin of this software must not be misrepresented; you must not
   claim that you wrote the original software. If you use this software
   in a product, an acknowledgment in the product documentation would be
   appreciated but is not required.

2. Altered source versions must be plainly marked as such, and must not
   be misrepresented as being the original software.

3. This notice may not be removed or altered from any source distribution.
```

> La licenza zlib è compatibile con GNU GPL v2 (la licenza di Songpress++).
> INetC viene usato **solo dall'installer** e non viene distribuito con
> l'applicazione: NSIS lo include temporaneamente in `$PLUGINSDIR` durante
> l'installazione, dopodiché viene rimosso automaticamente.

---

## Installazione del plugin nel progetto

Estrarre dallo zip il file `INetC.dll` dalla cartella `Plugins\x86-unicode\`
e copiarlo in:

```
installer/
└── plugins/
    └── INetC.dll    ← versione x86-unicode
```

Aggiungere nel file `.nsi`, **prima** di `!include "MUI2.nsh"`:

```nsi
!addplugindir /x86-unicode "plugins"
```

Già presente nel file `songpress++.nsi` del progetto.

---

## Comandi disponibili

### `inetc::get` — Download di file

```nsi
inetc::get [opzioni] URL file_locale [URL2 file2 ...] [/END]
Pop $0  ; "OK" oppure stringa di errore
```

**Opzioni principali:**

| Opzione | Descrizione |
|---------|-------------|
| `/SILENT` | Nasconde la barra di avanzamento |
| `/CONNECTTIMEOUT secondi` | Timeout di connessione (default: valore IE) |
| `/RECEIVETIMEOUT secondi` | Timeout di ricezione |
| `/NOPROXY` | Disabilita il proxy |
| `/PROXY IP:PORTA` | Proxy esplicito |
| `/USERNAME login /PASSWORD pwd` | Credenziali proxy |
| `/NOCANCEL` | Impedisce all'utente di annullare |
| `/WEAKSECURITY` | Ignora certificati sconosciuti o revocati |
| `/POPUP testo` | Mostra un dialogo popup dettagliato |
| `/BANNER testo` | Mostra un banner semplice (stile MSI) |
| `/USERAGENT testo` | Imposta lo User-Agent HTTP |
| `/HEADER testo` | Aggiunge o sostituisce un header HTTP |
| `/TOSTACK` | Scrive la risposta sullo stack NSIS invece che su file |
| `/TOSTACKCONV` | Come `/TOSTACK` ma con conversione encoding |
| `/RESUME domanda` | In caso di errore mostra un dialogo "Riprova" |

---

### `inetc::head` — Solo header HTTP (usato in Songpress++)

```nsi
inetc::head [opzioni] URL file_locale
Pop $0  ; "OK" oppure stringa di errore
```

Identico a `get` ma scarica **solo gli header HTTP**, senza il body.
Molto più veloce: ideale per testare la connessione.
Supporta le stesse opzioni di `get`.

**Uso in Songpress++:**

```nsi
inetc::head /SILENT /CONNECTTIMEOUT 5000 "https://pypi.org/"
Pop $0
${If} $0 == "OK"
    ; connessione OK
${Else}
    ; $0 contiene la descrizione dell'errore
${EndIf}
```

---

### `inetc::post` — Upload HTTP POST

```nsi
inetc::post testo_da_inviare [opzioni] URL file_risposta
Pop $0
```

Imposta la modalità POST. L'opzione `/FILE` permette di inviare il contenuto
di un file invece di una stringa.

---

### `inetc::put` — Upload HTTP PUT

```nsi
inetc::put [opzioni] URL file_locale [URL2 file2 ...] [/END]
Pop $0
```

---

## Valori di ritorno

Tutte le funzioni restituiscono sullo stack:

| Valore | Significato |
|--------|-------------|
| `"OK"` | Operazione riuscita |
| altra stringa | Descrizione dell'errore (es. `"Host not found"`, `"Connection refused"`, `"SSL error"`) |
