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

---

## Utilizzo attuale in Songpress++

**INetC non è più utilizzato.** Entrambi gli installer usano ora **NScurl**, incluso
di default in NSIS (sia amd64-unicode che x86-unicode). Non è richiesta nessuna DLL esterna.

| Installer | Plugin | DLL esterna |
|-----------|--------|-------------|
| **64 bit** (`songpress++64bit.nsi`) | NScurl (built-in NSIS) | nessuna |
| **32 bit** (`songpress++x86.nsi`) | NScurl (built-in NSIS) | nessuna |

INetC veniva usato in precedenza per il controllo della connessione Internet, ma è stato
sostituito da NScurl perché già incluso in NSIS, funziona in modo identico sia a 32 che
a 64 bit, e non richiede file aggiuntivi nel progetto.

La cartella `plugins/` e le direttive `!addplugindir` sono state rimosse da entrambi gli script.

---

## NScurl — sintassi sostitutiva

```nsi
NScurl::http GET "http://1.1.1.1/" "$INSTDIR\nettest.tmp" /TIMEOUT 10000 /END
Pop $0   ; "OK" oppure stringa di errore
Delete "$INSTDIR\nettest.tmp"

${If} $0 == "OK"
    ; connessione OK
${Else}
    ; $0 contiene la descrizione dell'errore
${EndIf}
```

---

## Riferimento comandi INetC (mantenuto per documentazione storica)

### `inetc::get` — Download di file

```nsi
inetc::get [opzioni] URL file_locale [URL2 file2 ...] [/END]
Pop $0  ; "OK" oppure stringa di errore
```

| Opzione | Descrizione |
|---------|-------------|
| `/SILENT` | Nasconde la barra di avanzamento |
| `/CONNECTTIMEOUT secondi` | Timeout di connessione |
| `/RECEIVETIMEOUT secondi` | Timeout di ricezione |
| `/NOPROXY` | Disabilita il proxy |
| `/PROXY IP:PORTA` | Proxy esplicito |
| `/NOCANCEL` | Impedisce l'annullamento |
| `/WEAKSECURITY` | Ignora certificati sconosciuti o revocati |
| `/TOSTACK` | Scrive la risposta sullo stack NSIS |
| `/RESUME domanda` | Dialogo "Riprova" in caso di errore |

### `inetc::head` — Solo header HTTP

Identico a `get` ma scarica solo gli header. Inaffidabile su Windows 10/11 —
usare `inetc::get` o NScurl al suo posto.

---

## Valori di ritorno (sia INetC che NScurl)

| Valore | Significato |
|--------|-------------|
| `"OK"` | Operazione riuscita |
| altra stringa | Descrizione dell'errore (es. `"Host not found"`, `"Connection refused"`) |
