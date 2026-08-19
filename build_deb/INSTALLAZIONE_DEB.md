# Songpress++ — Creazione e installazione del pacchetto `.deb`

Questa guida copre **solo** la creazione del pacchetto Debian (`.deb`) di
Songpress++ e la sua installazione su Linux (Debian/Ubuntu e derivate).

---

## Prerequisiti

Assicurati di avere installati i seguenti pacchetti:

```bash
sudo apt install python3 python3-pip python3-venv fakeroot dpkg imagemagick
```

> **Utenti Wayland:** per copiare il brano negli appunti **come immagine** è
> necessario il pacchetto `wl-clipboard` (che fornisce `wl-copy`). Il pacchetto
> `.deb` lo indica tra i `Recommends`, quindi `apt` lo installa automaticamente.
> Se esegui da sorgente su una sessione Wayland, installalo manualmente:
> ```bash
> sudo apt install wl-clipboard
> ```
> Su sessioni X11 non serve. Per sapere su quale sessione sei:
> ```bash
> # rapido
> echo "$XDG_SESSION_TYPE"      # stampa  wayland  oppure  x11
> # autorevole (systemd-logind, consigliato sulle distro recenti)
> loginctl show-session "$(loginctl --no-legend list-sessions | awk -v u="$USER" '$3==u {print $1; exit}')" -p Type --value
> ```

---

## Creazione del pacchetto `.deb`

Lo script `build_deb.sh` si trova nella root del progetto, accanto a `pyproject.toml`.

### 1. Entra nella cartella del progetto

> **⚠️ Nota:** il percorso qui sotto è solo un **esempio** ed è **da verificare**. Sostituiscilo con il percorso effettivo in cui si trova il progetto sul tuo sistema.

```bash
cd /home/denis/Songpress_DEFINitiVO3/SongpressPlusPlus
```

### 2. Rendi eseguibile lo script (solo la prima volta)

```bash
chmod +x build_deb.sh
```

### 3. Esegui lo script

```bash
./build_deb.sh
```

Lo script esegue automaticamente:

- Lettura di nome e versione da `pyproject.toml`
- Costruzione della wheel Python con `pip` e `hatchling`
- Installazione della wheel nell'albero del pacchetto
- Normalizzazione del layout secondo la Debian Policy (i file vengono spostati
  da `usr/local/` a `usr/`, i moduli in `usr/lib/python3/dist-packages`)
- Creazione del wrapper `GDK_BACKEND=x11` per la compatibilità con Wayland
- Creazione del symlink minuscolo `songpressplusplus` → `SongpressPlusPlus`
- Generazione della voce nel menu applicazioni (file `.desktop`), del tipo MIME
  `text/x-chordpro` e delle icone `hicolor`
- Scrittura degli script `postinst`/`postrm` (aggiornamento delle cache di
  sistema e installazione delle dipendenze solo-PyPI)
- Produzione del file `.deb` finale nella cartella `build_deb/`

Al termine vedrai (il numero di versione mostrato è solo un **esempio**, dipende da quello in `pyproject.toml`):

```
✅  Pacchetto creato: build_deb/songpressplusplus_8.0.2_all.deb
```

### Struttura della cartella `build_deb/`

Al termine della build, la cartella `build_deb/` contiene i due file di
documentazione (questa guida e la sua versione inglese) più tre elementi
generati (il numero di versione — qui `8.0.2` — dipende da `pyproject.toml`):

```
build_deb/
├── INSTALLAZIONE_DEB.md              ← questa guida (italiano)
├── DEB_INSTALLATION.md               ← guida inglese
├── songpressplusplus_8.0.2/          ← albero di staging del pacchetto
│   ├── DEBIAN/                        ← metadati e script di manutenzione
│   │   ├── control                    ← nome, versione, Depends, Maintainer…
│   │   ├── preinst                    ← rimozione dei residui in /usr/local
│   │   ├── postinst                   ← dipendenze PyPI + refresh delle cache
│   │   └── postrm                     ← pulizia alla rimozione
│   └── usr/                           ← ciò che verrà copiato nel filesystem
│       ├── bin/SongpressPlusPlus      ← wrapper eseguibile (GDK_BACKEND=x11)
│       ├── lib/python3/dist-packages/songpressplusplus/   ← codice del programma
│       └── share/                     ← .desktop, MIME, icone hicolor, metainfo
├── wheel/                            ← wheel Python intermedia (.whl)
│   └── songpressplusplus-8.0.2-py3-none-any.whl
└── songpressplusplus_8.0.2_all.deb   ← pacchetto finale da installare
```

Cosa sono e a cosa servono:

- **`songpressplusplus_<versione>/`** — è l'**albero di staging**: la copia
  esatta di ciò che il pacchetto installerà nel sistema, con in più la cartella
  `DEBIAN/` (metadati e script). Da questa cartella `dpkg-deb --build` produce il
  `.deb`. È un artefatto intermedio: puoi ispezionarlo per verificare cosa
  finirà nel sistema, ma per installare serve solo il `.deb`.
- **`wheel/`** — contiene la **wheel Python** (`.whl`) costruita con `hatchling`,
  passaggio intermedio da cui i moduli vengono estratti e installati
  nell'albero di staging. Anch'essa è un artefatto della build.
- **`songpressplusplus_<versione>_all.deb`** — è il **pacchetto finale**, l'unico
  file che ti serve per installare (o distribuire) il programma. Il suffisso
  `_all` indica che il pacchetto è indipendente dall'architettura (Python puro),
  quindi lo stesso `.deb` funziona su amd64, arm64, ecc.

> **Nota:** le due cartelle (`songpressplusplus_<versione>/` e `wheel/`) possono
> essere cancellate senza problemi dopo la build — vengono rigenerate a ogni
> esecuzione di `build_deb.sh`. Conserva solo il file `.deb` se vuoi archiviare
> o distribuire quella versione. All'inizio di ogni esecuzione `build_deb.sh`
> rimuove **soltanto** questi artefatti generati (albero di staging, `wheel/` e
> gli eventuali `.deb` precedenti): i file di documentazione presenti in
> `build_deb/` restano intatti.

---

## Installazione del pacchetto `.deb`

> **⚠️ Nota:** il numero di versione (`8.0.2`) è solo un **esempio** ed è **da verificare**: usa quello effettivamente prodotto dallo script, mostrato a schermo al termine della build.

```bash
sudo dpkg -i "build_deb/songpressplusplus_8.0.2_all.deb"
```

In caso di dipendenze mancanti:

```bash
sudo apt-get install -f
```

> **✅ Oppure, con barra di avanzamento.** Installando con `apt` invece di
> `dpkg` viene mostrata una barra di avanzamento durante l'installazione e le
> dipendenze vengono risolte in automatico (così il passo separato
> `apt-get install -f` non serve):
>
> ```bash
> sudo apt install "build_deb/songpressplusplus_8.0.2_all.deb"
> ```
>
> Il percorso contiene una `/`, quindi `apt` lo riconosce come file locale e non
> come nome di pacchetto da cercare nei repository. Se non sei nella cartella del
> `.deb`, passa il percorso completo.

> **🔎 Quale dei due metodi scegliere?** I due comandi lavorano a livelli
> diversi: `dpkg` è lo strumento di **basso livello** (installa il singolo `.deb`
> e basta, **senza** risolvere le dipendenze), mentre `apt` è quello di **alto
> livello** (installa il `.deb` **e** scarica dai repository le dipendenze
> mancanti).
>
> **`dpkg -i` + `apt-get install -f`**
> - ✔ Massimo controllo e trasparenza: `dpkg` installa in modo deterministico
>   proprio quel file, e la fase di scompattamento funziona anche offline.
> - ✘ Sono **due passaggi**: se dimentichi `apt-get install -f` il pacchetto
>   resta in stato incoerente (fra un comando e l'altro `dpkg` segnala errore, ed
>   è normale). Nessuna barra di avanzamento.
>
> **`apt install "…deb"`**
> - ✔ **Un solo comando**, dipendenze risolte in automatico (il passo
>   `apt-get install -f` non serve) e barra di avanzamento; non lascia mai il
>   sistema in stato incoerente.
> - ✘ Richiede l'accesso ai repository e il percorso deve contenere una `/`
>   (`./` o percorso completo), altrimenti `apt` cerca un pacchetto con quel nome.
>
> **Nota:** la scelta riguarda **solo** le dipendenze Debian dei repository. Le
> due dipendenze solo-PyPI (`python-pptx`, `pyshortcuts`) sono gestite in
> entrambi i casi dal `postinst`, che le scarica da PyPI: la connessione a
> Internet serve comunque. Il risultato finale installato è identico.

> **🌐 Serve una connessione a Internet.** Due dipendenze Python
> (`python-pptx` e `pyshortcuts`) non esistono nei repository Debian e vengono
> scaricate da PyPI durante l'installazione. Il `postinst` te lo segnala e
> chiede conferma.
>
> **Lingua dell'installazione.** I messaggi seguono il locale di sistema:
> **italiano** su un sistema in italiano, **inglese** su qualsiasi altro locale
> (l'inglese è la lingua predefinita, quindi copre ogni sistema non italiano).
> Su un sistema italiano la domanda è:
>
> ```
> 🌐  Continuare e scaricare le dipendenze ora? [S/n]
> ```
>
> Rispondendo `n` il pacchetto viene installato lo stesso, ma dovrai poi
> completare a mano:
>
> ```bash
> sudo pip3 install --break-system-packages python-pptx pyshortcuts
> ```
>
> La domanda compare solo da terminale: installando da Discover o GDebi, o con
> `DEBIAN_FRONTEND=noninteractive`, il download parte senza chiedere nulla.

> **Marcatori di stato durante l'installazione.** Mentre gestisce le dipendenze
> il `postinst` stampa gli stessi marcatori colorati usati dallo script di build:
> `🌐` indica un'operazione di rete (download da PyPI), `✔` un passo completato
> (dipendenza già presente o appena installata), `⚠` un problema non fatale (il
> download saltato su tua richiesta) e `✘` un errore (una dipendenza non è stata
> installata — il messaggio spiega come completare a mano). I colori compaiono
> solo da terminale; da Discover/GDebi, o quando l'output è rediretto su file,
> vengono usati i simboli semplici. Un'esecuzione riuscita ha più o meno questo
> aspetto:
>
> ```
> 🌐 Songpress++: controllo dipendenze PyPI (richiede una connessione a Internet)...
> ✔ Songpress++: dipendenza 'python-pptx' già presente.
> 🌐 Songpress++: installo 'pyshortcuts' via pip...
> ✔ Songpress++: 'pyshortcuts' installato.
> ```

**Cartella di installazione.** Il pacchetto copia i file del programma
nell'albero di sistema `dist-packages`:

```
/usr/lib/python3/dist-packages/songpressplusplus/
```

e l'eseguibile in `/usr/bin/SongpressPlusPlus`.

> **⚠️ Nota:** il percorso **non** contiene il numero di versione di Python
> (`python3` e non `python3.13`): è l'unica directory di sistema realmente
> presente in `sys.path` su Debian, e in questo modo il pacchetto continua a
> funzionare anche dopo un aggiornamento di Python. La cartella appartiene a
> `root` ed è quindi in sola lettura per l'utente: i template e i temi personali
> vengono salvati nella cartella dati utente.

> **⚠️ Aggiornamento da versioni precedenti.** Fino alla 7.0.1 l'installazione
> avveniva sotto `/usr/local/`, percorso che la Debian Policy riserva
> all'amministratore locale. La migrazione è **automatica**: lo script
> `preinst` del pacchetto rimuove i residui prima dello scompattamento e lo
> segnala a schermo. Rimuove soltanto i file della vecchia installazione, e solo
> dopo aver verificato con `dpkg-query` che nessun pacchetto li rivendichi;
> qualsiasi altro contenuto di `/usr/local` resta intatto. Per verificare quale
> copia è effettivamente in uso:
>
> ```bash
> python3 -c "import songpressplusplus, os; print(os.path.dirname(songpressplusplus.__file__))"
> ```

---

## Installazione grafica (doppio click)

Facendo doppio click su un file `.deb` in un ambiente desktop (es. KDE Plasma) di norma si apre **Discover**. Il backend PackageKit di Discover, però, gestisce male i `.deb` **locali** con dipendenze esterne e con un `postinst` che scarica pacchetti da PyPI/apt (come questo): spesso non risolve le `Depends:` del pacchetto e l'installazione fallisce a metà o non parte affatto.

Per un'installazione grafica affidabile conviene un **installer dedicato**, che risolve correttamente le dipendenze. Su Debian 13 (trixie) il pacchetto è **`gdebi`** (la GUI; `gdebi-core` è solo la riga di comando):

```bash
sudo apt install gdebi
```

> **Nota:** su versioni Debian più vecchie esisteva anche `qapt-deb-installer` (QApt, installer nativo Qt/KDE), ma è stato **rimosso** dai repository a partire da trixie; allo stesso modo `gdebi-kde` non ha più un pacchetto installabile. Usa `gdebi`.

Dopodiché, in Dolphin: tasto destro sul `.deb` → _Apri con…_ → scegli "Programma d'installazione pacchetti GDebi", spuntando l'opzione per usarlo sempre con questo tipo di file. Al doppio click successivo il `.deb` verrà installato tramite un dialogo grafico che gestisce le dipendenze in autonomia.

> **Nota:** la GUI di GDebi è basata su GTK, quindi su KDE si porta dietro qualche piccola dipendenza GTK e ha un aspetto un po' meno nativo, ma funziona correttamente. Se dovesse dare problemi, usa il metodo `apt` da terminale descritto qui sotto, che è il più affidabile.

> **✅ In alternativa (più robusto): `apt` da terminale.** Usa `apt` invece di `dpkg`, così risolve automaticamente le dipendenze dai repository:
>
> ```bash
> sudo apt install ./songpressplusplus_8.0.2_all.deb
> ```
>
> Il prefisso `./` (o un percorso completo) è **obbligatorio**: senza almeno una `/` nel nome, `apt` interpreta l'argomento come il nome di un pacchetto da cercare nei repository e restituisce "impossibile trovare il pacchetto". Se non sei nella cartella del `.deb`, passa il percorso completo, ad esempio `sudo apt install ~/…/build_deb/songpressplusplus_8.0.2_all.deb`.

---

## Aggiornamento a una nuova versione

### 1. Aggiorna la versione in `pyproject.toml`

```toml
[project]
version = "8.0.2"   # ← modifica questo numero
```

### 2. Rimuovi la versione installata, ricostruisci e reinstalla

```bash
sudo dpkg -r songpressplusplus
./build_deb.sh
```

Al termine dello script, `build_deb/` conterrà il nuovo `.deb` con il numero
di versione aggiornato. Installalo con il comando suggerito a schermo, ad esempio:

```bash
sudo dpkg -i "build_deb/songpressplusplus_8.0.2_all.deb"
```

> **Suggerimento:** non è necessario ricordare il numero di versione esatto —
> puoi usare il completamento automatico della shell con `Tab` dopo aver digitato
> `sudo dpkg -i "build_deb/songpressplusplus_`, oppure copiare il comando
> che lo script stampa al termine della build.

---

## Disinstallazione

```bash
sudo dpkg -r songpressplusplus
```

---

## Avvio del programma

Dopo l'installazione il programma si avvia in tre modi:

**Da terminale:**
```bash
SongpressPlusPlus
# oppure (minuscolo)
songpressplusplus
```

**Dal menu applicazioni** (KDE/GNOME): cerca "Songpress" nel launcher.

> Il wrapper installato imposta automaticamente `GDK_BACKEND=x11` per garantire
> la compatibilità con wxPython su sistemi Wayland. Non è necessario impostare
> la variabile manualmente. Per vedere l'output grezzo (utile in debug):
>
> ```bash
> SONGPRESS_VERBOSE=1 SongpressPlusPlus
> ```

---
*Questo file è codificato UTF-8 senza BOM.*
