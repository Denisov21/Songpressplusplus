# Songpress++ — Guida AppImage (installazione, uso, disinstallazione)

Questa guida riguarda il file `SongpressPlusPlus-<versione>-<arch>.AppImage`
prodotto da `build_appimage.sh`. È indipendente dalla versione `.deb`: le due
possono coesistere sulla stessa macchina senza conflitti, perché l'AppImage
non tocca `/usr` né il gestore pacchetti di sistema.

> 🌐 **Nota:** costruire l'AppImage richiede una connessione a Internet (vedi
> `build_appimage.sh`). Una volta creato, il file `.AppImage` **funziona
> offline**: contiene già Python, wxPython e le librerie necessarie.

---

## 0. Cos'è: un'installazione portabile

L'AppImage **non è un'installazione nel senso tradizionale**: è un
pacchetto *portabile*. Tutto ciò che serve all'applicazione (Python,
wxPython, le librerie) sta dentro un unico file eseguibile, che puoi tenere
dove vuoi — nella home, su una chiavetta USB, in una cartella condivisa di
rete — e spostare da una macchina Linux compatibile a un'altra senza
reinstallare nulla: basta copiare il file.

Non modifica il sistema (nessun file sotto `/usr`, nessuna voce nel
database del gestore pacchetti), non richiede privilegi di root, e può
essere rimosso cancellando semplicemente il file. Per questo motivo alcuni
passi di questa guida (icona nel menu, associazione file) sono **opzionali
**: l'app funziona comunque senza.

### Pro e contro rispetto al pacchetto `.deb`

**Pro:**
- **Portabilità reale**: un solo file, nessuna installazione di sistema,
  funziona su qualunque distribuzione Linux abbastanza recente (Debian,
  Fedora, openSUSE, Arch, ecc.), non solo su derivate Debian/Ubuntu.
- **Nessun privilegio di root richiesto**, né per l'uso né per la rimozione.
- **Nessuna dipendenza da risolvere**: Python, wxPython e le librerie
  Python (pptx, reportlab, ecc.) sono già dentro il file.
- **Funziona offline** una volta creato: a differenza del `.deb`, il cui
  `postinst` scarica dipendenze da PyPI durante l'installazione, l'AppImage
  non contatta la rete per essere eseguito.
- **Convivenza pacifica**: può stare installato insieme al `.deb` sulla
  stessa macchina senza conflitti di file.
- **Multiple versioni in parallelo**: puoi tenere più file `.AppImage` di
  versioni diverse nella stessa cartella e lanciare quella che vuoi.

**Contro:**
- **File più grande**: include Python, wxPython, GTK e le librerie native,
  quindi pesa molto di più del `.deb` (che si appoggia alle librerie di
  sistema già presenti).
- **Nessuna integrazione automatica**: di serie non compare nel menu
  applicazioni né associa i tipi di file; va integrato a mano o con
  AppImageLauncher (§2a).
- **Nessun aggiornamento automatico**: niente `apt upgrade`. Aggiornare
  significa scaricare/costruire il nuovo file e sostituire il vecchio (§3);
  esistono strumenti di terze parti come AppImageUpdate per gli
  aggiornamenti incrementali, ma non sono coperti da questa guida.
- **Richiede FUSE** per il montaggio automatico (aggirabile, vedi §8).
- **Legato alla ABI della macchina di build**: essendo compilato contro le
  librerie native di sistema (glibc, GTK) della macchina che lo ha creato,
  potrebbe non partire su distribuzioni molto più vecchie di quella di
  build. Il `.deb`, risolvendo le dipendenze tramite apt, è in genere più
  affidabile a lungo termine sulla stessa famiglia di distribuzioni.
- **Nessun file di copyright/changelog standardizzato** come nel formato
  Debian: la tracciabilità della licenza è meno "di sistema".

In breve: scegli l'AppImage se vuoi **provare l'app senza installarla**,
usarla su una **distribuzione non Debian-based**, o portarla con te su più
macchine; scegli il `.deb` se vuoi un'**integrazione di sistema completa**
con aggiornamenti gestiti da apt.

---

## 1. Requisiti del sistema di destinazione

L'AppImage è pensato per essere eseguito così com'è, senza installare nulla.
Servono solo:

- Un desktop Linux **x86_64** o **aarch64** (l'architettura è nel nome del file).
- **FUSE** disponibile, per il montaggio automatico dell'immagine:
  - Debian/Ubuntu recenti: `sudo apt install libfuse2t64` (o `libfuse2` sulle
    versioni più vecchie).
  - Fedora: `sudo dnf install fuse-libs`.
  - openSUSE: `sudo zypper install libfuse2`.
  - Se non puoi installare FUSE, vedi la sezione [8. Eseguire senza
    FUSE](#8-eseguire-senza-fuse).

Non serve Python, non serve wxPython, non serve alcuna libreria applicativa:
sono tutte dentro l'immagine.

---

## 2. Installazione

Un AppImage **non si "installa"** nel senso classico: è un unico file
eseguibile. "Installarlo" significa semplicemente:

```bash
# 1. Rendilo eseguibile
chmod +x SongpressPlusPlus-*.AppImage

# 2. (Facoltativo ma consigliato) spostalo in un posto stabile
mkdir -p ~/Applicazioni
mv SongpressPlusPlus-*.AppImage ~/Applicazioni/
```

Da qui puoi già lanciarlo con doppio clic dal file manager, oppure da
terminale:

```bash
~/Applicazioni/SongpressPlusPlus-*.AppImage
```

### 2a. Integrazione nel menu applicazioni (icona, voce di menu, tipo file)

Di serie l'AppImage **non compare nel menu** del desktop finché non lo
integri. Il modo più semplice è usare
**[AppImageLauncher](https://github.com/TheAssassin/AppImageLauncher)**, che
intercetta il primo avvio e chiede se vuoi integrarlo automaticamente
(icona, voce di menu, associazione file):

```bash
# Debian/Ubuntu — PPA ufficiale del progetto:
# https://launchpad.net/~appimagelauncher-team/+archive/ubuntu/stable
sudo add-apt-repository ppa:appimagelauncher-team/stable
sudo apt update
sudo apt install appimagelauncher
```

Per Fedora/openSUSE/Arch e altre distribuzioni, il progetto pubblica
pacchetti pronti nella pagina
**[release di AppImageLauncher](https://github.com/TheAssassin/AppImageLauncher/releases)**.

In alternativa, integrazione manuale (funziona ovunque, nessun pacchetto
esterno):

```bash
APPIMG=~/Applicazioni/SongpressPlusPlus-*.AppImage

# Icona
mkdir -p ~/.local/share/icons/hicolor/256x256/apps
"$APPIMG" --appimage-extract 'usr/share/icons/hicolor/256x256/apps/*.png'
cp squashfs-root/usr/share/icons/hicolor/256x256/apps/*.png \
   ~/.local/share/icons/hicolor/256x256/apps/songpressplusplus.png
rm -rf squashfs-root

# Voce di menu
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/songpressplusplus.desktop <<DESKTOP
[Desktop Entry]
Type=Application
Name=Songpress++
Comment=Genera canzonieri di alta qualità in PDF e PPTX
Exec=$APPIMG %f
Icon=songpressplusplus
Terminal=false
Categories=Office;Publishing;Education;
MimeType=text/x-chordpro;
DESKTOP

update-desktop-database ~/.local/share/applications 2>/dev/null || true
gtk-update-icon-cache -qf ~/.local/share/icons/hicolor 2>/dev/null || true
```

Dopo questo passo Songpress++ compare nel menu applicazioni con la sua icona,
e i file `.crd`/`.cho`/`.chordpro`/`.chopro`/`.pro`/`.sng` possono essere
associati ad esso dal file manager (tasto destro → Apri con).

> ℹ️ Il file `.desktop` sopra segue la
> **[Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/latest/)**
> di freedesktop.org: lo stesso standard usato dal `.deb`. Se vuoi
> personalizzare ulteriormente la voce di menu (lingue, azioni aggiuntive,
> ecc.), è il riferimento da consultare.

---

## 3. Aggiornamento

Un AppImage nuovo **sostituisce** semplicemente il vecchio file:

```bash
mv SongpressPlusPlus-<nuova_versione>-x86_64.AppImage \
   ~/Applicazioni/SongpressPlusPlus-*.AppImage
chmod +x ~/Applicazioni/SongpressPlusPlus-*.AppImage
```

Se avevi integrato l'icona/voce di menu con il metodo manuale (§2a) e il
percorso del file **non cambia nome**, non serve rifare nulla: la voce
`.desktop` punta già al file corretto. Se invece cambi nome/percorso,
aggiorna la riga `Exec=` nel file `.desktop`.

I dati utente (canzoni, template personalizzati, preferenze) vivono in
`~/.Songpress++` **fuori** dall'AppImage: sopravvivono a qualunque
aggiornamento o rimozione del file `.AppImage`.

---

## 4. Disinstallazione

Poiché l'AppImage non tocca il sistema, disinstallarlo è semplice:

```bash
# 1. Rimuovi il file eseguibile
rm ~/Applicazioni/SongpressPlusPlus-*.AppImage

# 2. Se avevi integrato icona/voce di menu manualmente (§2a), rimuovile
rm -f ~/.local/share/applications/songpressplusplus.desktop
rm -f ~/.local/share/icons/hicolor/256x256/apps/songpressplusplus.png
update-desktop-database ~/.local/share/applications 2>/dev/null || true
```

Se avevi usato **AppImageLauncher**, disintegra prima l'app dal suo menu
contestuale (tasto destro sull'icona → *Rimuovi integrazione* / *Uninstall
AppImage*), oppure lancia:

```bash
~/.local/share/applications/appimagekit_*-songpressplusplus.desktop
# oppure, più semplice, dal menu: tasto destro sull'icona → Uninstall AppImage
```

### 4a. Rimuovere anche i dati utente (facoltativo)

I dati personali (spartiti, template, preferenze) **non** vengono toccati
dai passi sopra. Per cancellarli:

```bash
rm -rf ~/.Songpress++
```

⚠️ Questo cancella anche eventuali canzoni/template che hai creato: fanne
una copia prima, se ti servono.

---

## 5. Verifica dell'integrità del file scaricato (facoltativo)

Se hai scaricato l'AppImage da una release GitHub e vuoi verificarne
l'integrità:

```bash
sha256sum SongpressPlusPlus-*.AppImage
```

Confronta l'output con il checksum pubblicato nella pagina della release.

---

## 6. Debug e diagnostica

Per vedere tutti i messaggi GTK/wx senza il filtro applicato dal wrapper
(vedi `AppRun` in `build_appimage.sh`):

```bash
SONGPRESS_VERBOSE=1 ~/Applicazioni/SongpressPlusPlus-*.AppImage
```

Per estrarre il contenuto dell'immagine senza eseguirla (utile per
ispezionare cosa contiene):

```bash
./SongpressPlusPlus-*.AppImage --appimage-extract
ls squashfs-root/
```

---

## 7. Correttore ortografico (dizionari)

L'AppImage include il binding Python `pyenchant` e la libreria di sistema
`libenchant`, ma **non** porta con sé i dizionari (`hunspell-it`,
`hunspell-en-us`, ecc.), che restano quelli eventualmente già installati sul
sistema. Per averli:

```bash
# Debian/Ubuntu
sudo apt install hunspell-it hunspell-en-us

# Fedora
sudo dnf install hunspell-it hunspell-en-US

# openSUSE
sudo zypper install hunspell-it hunspell-en_US
```

In alternativa, Songpress++ permette di scaricare i dizionari dal proprio
menu **Opzioni ortografia → Installa dizionari...**.

---

## 8. Eseguire senza FUSE

Se il sistema non ha FUSE (es. alcuni container o sandbox), l'AppImage può
comunque girare estraendosi da sé:

```bash
export APPIMAGE_EXTRACT_AND_RUN=1
~/Applicazioni/SongpressPlusPlus-*.AppImage
```

Più lento all'avvio (deve estrarre l'immagine ogni volta), ma non richiede
FUSE.

---

## 9. Domande frequenti

**L'AppImage e il pacchetto `.deb` possono stare installati insieme?**
Sì. Non condividono file di sistema; condividono solo la cartella dati
utente `~/.Songpress++`, quindi vedono le stesse canzoni/template.

**Serve essere root per usarlo?**
No, mai. Tutta l'installazione/disinstallazione avviene nello spazio utente.

**Perché l'app parte da terminale ma non ha l'icona nel menu?**
Perché non hai ancora fatto l'integrazione descritta al §2a. È un passo
facoltativo: l'app funziona comunque via doppio clic o da riga di comando.

**"Errore: FUSE non disponibile" all'avvio.**
Installa FUSE (§1) oppure usa la modalità senza FUSE (§8).
