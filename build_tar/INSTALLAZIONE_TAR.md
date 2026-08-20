# Songpress++ — Installazione da pacchetto `.tar`

Guida all'**installazione**, all'**avvio** e alla **disinstallazione** del pacchetto
Songpress++ distribuito come tarball (`.tar.gz` o `.tar.xz`).

Il tarball contiene:

```
songpressplusplus-<versione>/
├── usr/            # i file dell'applicazione (stesso albero del pacchetto .deb)
├── install.sh      # installa: dipendenze + file + cache di sistema
├── uninstall.sh    # disinstalla: rimuove i file e ripristina le cache
└── README.txt      # riepilogo rapido bilingue
```

> **Nota.** A differenza del `.deb`, un tarball non ha un package manager alle
> spalle: è `install.sh` a occuparsi delle dipendenze di sistema (via `apt`),
> delle dipendenze solo-PyPI e dell'aggiornamento delle cache desktop/MIME/icone.

> **Devi ancora creare il tarball?** Se non hai il file
> `songpressplusplus-<versione>.tar.gz` ma i sorgenti del progetto, vai
> direttamente all'[Appendice — Creare il pacchetto con `build_tar.sh`](#appendice--creare-il-pacchetto-tar-con-build_tarsh).

---

## 1. Requisiti

- Una distribuzione **Debian/Ubuntu** (o derivata) con `apt`.
  Su altre distribuzioni l'installazione dei file funziona lo stesso, ma le
  dipendenze di sistema vanno installate a mano (vedi §7).
- **Permessi di root** (`sudo`): l'installazione scrive sotto `/usr`.
  Gli script si rilanciano da soli con `sudo` se lanciati da utente normale.
- Una **connessione a Internet**, usata per scaricare le dipendenze.
  Con `--no-deps` si copiano solo i file, senza toccare la rete (vedi §4).

---

## 2. Installazione

Dal file `songpressplusplus-<versione>.tar.gz` (o `.tar.xz`):

```bash
# 1. Estrai l'archivio
tar xf songpressplusplus-<versione>.tar.gz

# 2. Entra nella cartella estratta
cd songpressplusplus-<versione>

# 3. Installa
sudo ./install.sh
```

`tar xf` riconosce da solo la compressione, quindi lo stesso comando vale sia per
`.tar.gz` sia per `.tar.xz`.

Durante l'installazione lo script:

1. rimuove eventuali residui di vecchie installazioni sotto `/usr/local`
   (solo se non appartengono ad altri pacchetti);
2. installa le **dipendenze di sistema** con `apt` (chiede conferma);
3. copia i file sotto `/usr` e scrive un **manifest** per la disinstallazione;
4. aggiorna le cache di desktop, MIME, icone e AppStream;
5. installa le **dipendenze solo-PyPI** (`python-pptx`, `pyshortcuts`) con `pip`
   (chiede conferma).

Al termine vedrai un messaggio `✔ Installazione completata`.

---

## 3. Avvio

Dopo l'installazione l'applicazione è disponibile in tre modi:

- **Dal menu applicazioni** del desktop, come voce **Songpress++**
  (categorie Ufficio / Editoria).
- **Da terminale**, con uno di questi comandi (equivalenti):

  ```bash
  SongpressPlusPlus
  songpressplusplus      # alias tutto minuscolo
  ```

- **Aprendo un file canzone** (`.crd`, `.cho`, `.chordpro`, `.chopro`, `.pro`,
  `.sng`): sono associati automaticamente a Songpress++.

> **Perché il comando forza X11.** L'avvio passa da un wrapper che imposta
> `GDK_BACKEND=x11` per compatibilità con wxPython su Wayland. Per vedere l'output
> di debug completo (senza il filtro dei messaggi GTK innocui):
>
> ```bash
> SONGPRESS_VERBOSE=1 SongpressPlusPlus
> ```

---

## 4. Opzioni di installazione

`install.sh` accetta alcune opzioni:

| Opzione        | Effetto |
|----------------|---------|
| `--prefix DIR` | Installa sotto `DIR` invece di `/usr` (vedi §5). |
| `--no-deps`    | Copia **solo i file**: niente `apt`, niente `pip`, niente rete. |
| `-y`, `--yes`  | Risponde "sì" a tutte le domande (utile in script non interattivi). |
| `-h`, `--help` | Mostra l'aiuto. |

Esempi:

```bash
# Installazione senza toccare le dipendenze (le gestisci tu)
sudo ./install.sh --no-deps

# Installazione non interattiva, tutto automatico
sudo ./install.sh -y
```

---

## 5. Installare in un prefisso diverso da `/usr`

Di default tutto va sotto `/usr`, come farebbe il `.deb`. Puoi però scegliere un
altro prefisso, ad esempio per un'installazione locale:

```bash
sudo ./install.sh --prefix /usr/local
```

Quando il prefisso **non** è `/usr`, `install.sh` adatta automaticamente i
percorsi assoluti:

- riscrive il percorso del binario nel **wrapper** e nel file **`.desktop`**;
- imposta `PYTHONPATH` nel wrapper, così i moduli Python restano importabili
  anche fuori dai percorsi di sistema standard.

> Ricorda il prefisso usato: ti servirà con lo stesso valore per la
> disinstallazione (`uninstall.sh --prefix ...`).

---

## 6. Disinstallazione

Dalla stessa cartella estratta (quella che contiene `uninstall.sh`):

```bash
sudo ./uninstall.sh
```

Se avevi installato con un prefisso diverso, passalo di nuovo:

```bash
sudo ./uninstall.sh --prefix /usr/local
```

Lo script legge il **manifest** creato durante l'installazione e rimuove
esattamente i file che aveva copiato, poi ripristina le cache di sistema. Se il
manifest non c'è più (cartella spostata o cancellata), ricade sull'albero `usr/`
presente accanto allo script.

Opzioni di `uninstall.sh`:

| Opzione        | Effetto |
|----------------|---------|
| `--prefix DIR` | Prefisso da cui disinstallare (default `/usr`). |
| `--purge`      | Rimuove **anche i dati utente** in `~/.Songpress++`. |
| `-h`, `--help` | Mostra l'aiuto. |

```bash
# Rimozione completa, dati utente inclusi
sudo ./uninstall.sh --purge
```

> **Cosa NON viene rimosso.** Le dipendenze installate da `apt` e da `pip`
> restano nel sistema, esattamente come farebbe `dpkg -r`. Senza `--purge`
> vengono conservati anche i dati utente in `~/.Songpress++`.

---

## 7. Dipendenze (per riferimento)

Se installi con `--no-deps`, o su una distribuzione senza `apt`, dovrai
installare a mano queste dipendenze.

**Di sistema** (nei repository Debian/Ubuntu):

```
python3 (>= 3.12), python3-pip, python3-wxgtk4.0 | python3-wxpython4,
python3-requests, python3-reportlab, python3-markdown, python3-mistune,
python3-pypdf, python3-enchant, xdg-utils
```

**Consigliate** (migliorano l'esperienza ma non obbligatorie):

```
wl-clipboard, hunspell-it, hunspell-en-us
```

**Solo-PyPI** (non presenti nei repository Debian, si installano con `pip`):

```bash
sudo pip3 install --break-system-packages python-pptx pyshortcuts
```

---

## 8. Risoluzione problemi

**«L'installazione chiede la password»**
`install.sh` e `uninstall.sh` hanno bisogno dei permessi di root e si rilanciano
con `sudo`: inserisci la tua password quando richiesto, oppure lanciali già con
`sudo ./install.sh`.

**«Serve una connessione a Internet»**
La copia dei file è locale, ma l'installazione delle dipendenze scarica pacchetti
da `apt` e da PyPI. Se sei offline usa `--no-deps` e installa le dipendenze più
tardi (§7).

**«L'app non parte o dà errori grafici su Wayland»**
L'avvio forza già `GDK_BACKEND=x11`. Per vedere i messaggi completi:

```bash
SONGPRESS_VERBOSE=1 SongpressPlusPlus
```

**«Ho installato con un prefisso ma l'app non trova i moduli Python»**
Assicurati di aver usato `install.sh --prefix ...` (che imposta `PYTHONPATH` nel
wrapper), non una copia manuale dei file.

**«La voce di menu o l'icona non compaiono subito»**
Le cache vengono aggiornate a fine installazione. Se necessario, esci e rientra
nella sessione desktop, oppure aggiorna a mano:

```bash
sudo update-desktop-database -q /usr/share/applications
sudo gtk-update-icon-cache -qf /usr/share/icons/hicolor
```

---

## 9. Riepilogo comandi

```bash
# Installazione
tar xf songpressplusplus-<versione>.tar.gz
cd songpressplusplus-<versione>
sudo ./install.sh

# Avvio
SongpressPlusPlus

# Disinstallazione
sudo ./uninstall.sh            # aggiungi --purge per rimuovere ~/.Songpress++
```

---

## Appendice — Creare il pacchetto `.tar` con `build_tar.sh`

Questa sezione riguarda **chi costruisce e distribuisce** il pacchetto, non
l'utente finale. Serve per generare il file
`songpressplusplus-<versione>.tar.gz` a partire dai sorgenti del progetto.

### A.1 Requisiti di build

- Gli stessi di `build_deb.sh`: **Python ≥ 3.12**, `pip`, e una connessione a
  Internet (la wheel viene costruita scaricando `hatchling` e le dipendenze di
  build da PyPI).
- `tar` e il compressore del formato scelto: `gzip` per `.tar.gz`,
  `xz-utils` per `.tar.xz`.
- I file del progetto nella stessa cartella dello script: `pyproject.toml`
  (da cui si leggono nome e versione) e `build_deb.sh`.

### A.2 Come funziona

`build_tar.sh` **riusa il payload** che `build_deb.sh` produce
(`build_deb/<nome>_<versione>/usr`), così le patch ai sorgenti e la build della
wheel non vengono duplicate. Se quel payload non esiste — o se passi
`--rebuild` — lo script lancia da solo `build_deb.sh` per costruirlo. Poi vi
affianca `install.sh`, `uninstall.sh` e `README.txt` e crea l'archivio.

### A.3 Avvio

```bash
# 1. Rendi eseguibile lo script (una volta sola)
chmod +x build_tar.sh

# 2. Crea il pacchetto (default: .tar.gz)
./build_tar.sh
```

Al termine lo script stampa il percorso dell'archivio, che finisce in:

```
build_tar/songpressplusplus-<versione>.tar.gz
```

> **Non serve `sudo`.** La build gira da utente normale; i file dentro
> l'archivio risultano comunque di proprietà di `root` (come nel `.deb`).

### A.4 Opzioni

| Opzione            | Effetto |
|--------------------|---------|
| `--format gz`      | Archivio `.tar.gz` (default). |
| `--format xz`      | Archivio `.tar.xz` (compressione migliore, più lento). |
| `--format tar`     | `.tar` non compresso. |
| `-z` / `-J`        | Scorciatoie per `--format gz` / `--format xz`. |
| `--rebuild`        | Ricostruisce il payload anche se già presente. |
| `-y`, `--yes`      | Non fa domande (utile in CI). |
| `-h`, `--help`     | Mostra l'aiuto. |

Esempi:

```bash
# Archivio .tar.xz
./build_tar.sh --format xz

# Ricostruzione pulita del payload, senza domande
./build_tar.sh --rebuild -y
```

### A.5 Variabili d'ambiente

| Variabile         | Effetto |
|-------------------|---------|
| `SPP_TAR_FORMAT`  | Formato predefinito (`gz` \| `xz` \| `tar`). |
| `SPP_ASSUME_YES=1`| Equivale a `-y`. |
| `SPP_DEB_SCRIPT`  | Percorso di `build_deb.sh`, se non è accanto a `build_tar.sh`. |
| `SPP_BUILD_LANG`  | Lingua dei messaggi di build (`it` \| `en`). |

### A.6 Verifica veloce

Dopo la build puoi controllare il contenuto dell'archivio senza estrarlo:

```bash
tar tf build_tar/songpressplusplus-<versione>.tar.gz | head
```

Devi vedere la cartella `songpressplusplus-<versione>/` con dentro `usr/`,
`install.sh`, `uninstall.sh` e `README.txt`. A quel punto il pacchetto è pronto
per essere distribuito e installato come descritto nelle sezioni §2–§6.
