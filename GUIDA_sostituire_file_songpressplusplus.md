# Sostituire un file di Songpress++ (Linux)

Guida generica per rimpiazzare **un singolo file** dell'app già installata
(es. `Editor.py`, `SongDecorator.py`, …) con una versione corretta scaricata
in **`~/Scaricati`**. Non serve reinstallare nulla.

> In questi comandi si usa `NOMEFILE` come segnaposto: **sostituiscilo** col
> nome reale del file (es. `Editor.py`). La cartella di installazione tipica è
> `/usr/lib/python3/dist-packages/songpressplusplus/` — se sul tuo sistema è
> diversa, vedi la sezione **"Trovare la cartella giusta"** in fondo.

---

## Riepilogo veloce (copia-incolla)

Sostituisci `NOMEFILE` col nome reale, poi esegui in sequenza:

```bash
# Cartella di installazione dell'app
DEST=/usr/lib/python3/dist-packages/songpressplusplus

# 1. Backup dell'originale (una sola volta)
sudo cp "$DEST/NOMEFILE" "$DEST/NOMEFILE.backup"

# 2. Copia la versione corretta da ~/Scaricati al posto di quella vecchia
sudo cp ~/Scaricati/NOMEFILE "$DEST/NOMEFILE"

# 3. Pulisci la cache compilata (altrimenti Python può usare la versione vecchia)
sudo rm -f "$DEST/__pycache__/"*.pyc
```

Poi **chiudi e riapri Songpress++**.

---

## Passo per passo

### 1. Verifica che il file scaricato ci sia

```bash
ls -l ~/Scaricati/NOMEFILE
```

Se non compare, il file è altrove: correggi il percorso (es. `~/Downloads/NOMEFILE`)
nei comandi successivi.

### 2. Backup dell'originale

Da fare **la prima volta**, così puoi sempre tornare indietro:

```bash
sudo cp /usr/lib/python3/dist-packages/songpressplusplus/NOMEFILE \
        /usr/lib/python3/dist-packages/songpressplusplus/NOMEFILE.backup
```

### 3. Copia la versione corretta

```bash
sudo cp ~/Scaricati/NOMEFILE \
        /usr/lib/python3/dist-packages/songpressplusplus/NOMEFILE
```

> Serve `sudo` perché `/usr/lib/...` è una zona di sistema.

### 4. Pulisci la cache dei `.pyc` (importante)

Python conserva una copia compilata: se non la rimuovi, potrebbe continuare a
usare la versione vecchia anche dopo la copia.

```bash
sudo rm -f /usr/lib/python3/dist-packages/songpressplusplus/__pycache__/*.pyc
```

### 5. Riavvia l'app

Chiudi completamente Songpress++ e riaprilo. La modifica è attiva.

---

## Tornare all'originale (rollback)

Se qualcosa non va, ripristina il backup fatto al passo 2:

```bash
sudo cp /usr/lib/python3/dist-packages/songpressplusplus/NOMEFILE.backup \
        /usr/lib/python3/dist-packages/songpressplusplus/NOMEFILE
sudo rm -f /usr/lib/python3/dist-packages/songpressplusplus/__pycache__/*.pyc
```

Poi riavvia l'app.

---

## Trovare la cartella giusta

Se la cartella di installazione non fosse quella indicata, cercala così:

```bash
find / -name "SongTokenizer.py" 2>/dev/null
```

La cartella che contiene `SongTokenizer.py` (e `SDIMainFrame.py`) è quella
giusta: usala al posto di
`/usr/lib/python3/dist-packages/songpressplusplus` in tutti i comandi.

Ricerca alternativa, direttamente per nome del file da sostituire:

```bash
find / -name "NOMEFILE" -path "*ongpress*" 2>/dev/null
```

---

## Note utili

- **Aggiornamenti dell'app**: se un domani reinstalli o aggiorni Songpress++
  dal pacchetto (`apt`, `.deb`, `.rpm`…), il file in `/usr/lib/...` può essere
  **sovrascritto** e la modifica manuale andare persa. In tal caso ricopia di
  nuovo la versione corretta con gli stessi comandi.

- **Verifica sintassi (facoltativa)**: prima di riavviare puoi controllare che
  il file non abbia errori di sintassi Python:

  ```bash
  python3 -m py_compile /usr/lib/python3/dist-packages/songpressplusplus/NOMEFILE \
    && echo "OK" || echo "ERRORE di sintassi"
  ```

- **App "congelata" (AppImage / PyInstaller)**: se hai installato Songpress++
  come **AppImage** o eseguibile unico, il singolo file **non** è modificabile a
  mano con questo metodo (i sorgenti sono impacchettati dentro l'immagine). In
  quel caso serve ricostruire il pacchetto con la versione corretta del file.

- **Font per i simboli musicali**: se stai sostituendo `Editor.py` per il fix
  dei glifi musicali SMP, assicurati che ci sia un font che li copre. FreeSerif
  è già incluso nell'app; per una resa ottimale (come su Windows) puoi
  installare Noto Music:

  ```bash
  fc-list | grep -i "noto music"        # verifica se è presente
  sudo apt install fonts-noto-extra     # installalo se manca (Debian/Ubuntu)
  ```

---

## Esempio pratico

Supponiamo di dover sostituire **`Editor.py`**, appena scaricato in
**`~/Scaricati/Editor.py`**. I comandi diventano:

```bash
# 0. (Consigliato) verifica che il file scaricato ci sia
ls -l ~/Scaricati/Editor.py

# 1. Backup dell'originale (una sola volta)
sudo cp /usr/lib/python3/dist-packages/songpressplusplus/Editor.py \
        /usr/lib/python3/dist-packages/songpressplusplus/Editor.py.backup

# 2. Copia la versione corretta al posto di quella vecchia
sudo cp ~/Scaricati/Editor.py \
        /usr/lib/python3/dist-packages/songpressplusplus/Editor.py

# 3. Pulisci la cache compilata
sudo rm -f /usr/lib/python3/dist-packages/songpressplusplus/__pycache__/*.pyc
```

Poi chiudi e riapri Songpress++ e prova a scrivere una riga con il simbolo ♪.

Se qualcosa non va, ripristina il backup:

```bash
sudo cp /usr/lib/python3/dist-packages/songpressplusplus/Editor.py.backup \
        /usr/lib/python3/dist-packages/songpressplusplus/Editor.py
sudo rm -f /usr/lib/python3/dist-packages/songpressplusplus/__pycache__/*.pyc
```

<br>

---
---

<br>

# Replacing a Songpress++ file (Linux)

Generic guide to replace **a single file** of the already-installed app
(e.g. `Editor.py`, `SongDecorator.py`, …) with a fixed version downloaded to
**`~/Downloads`**. No reinstall needed.

> These commands use `FILENAME` as a placeholder: **replace it** with the real
> file name (e.g. `Editor.py`). The typical install folder is
> `/usr/lib/python3/dist-packages/songpressplusplus/` — if it's different on
> your system, see **"Finding the right folder"** at the bottom.

---

## Quick version (copy-paste)

Replace `FILENAME` with the real file name, then run in sequence:

```bash
# App install folder
DEST=/usr/lib/python3/dist-packages/songpressplusplus

# 1. Back up the original (only once)
sudo cp "$DEST/FILENAME" "$DEST/FILENAME.backup"

# 2. Copy the fixed version from ~/Downloads over the old one
sudo cp ~/Downloads/FILENAME "$DEST/FILENAME"

# 3. Clear the compiled cache (otherwise Python may use the old version)
sudo rm -f "$DEST/__pycache__/"*.pyc
```

Then **close and reopen Songpress++**.

---

## Step by step

### 1. Check the downloaded file is there

```bash
ls -l ~/Downloads/FILENAME
```

If it doesn't show up, the file is elsewhere: fix the path (e.g.
`~/Scaricati/FILENAME`) in the following commands.

### 2. Back up the original

Do this **the first time**, so you can always roll back:

```bash
sudo cp /usr/lib/python3/dist-packages/songpressplusplus/FILENAME \
        /usr/lib/python3/dist-packages/songpressplusplus/FILENAME.backup
```

### 3. Copy the fixed version

```bash
sudo cp ~/Downloads/FILENAME \
        /usr/lib/python3/dist-packages/songpressplusplus/FILENAME
```

> `sudo` is needed because `/usr/lib/...` is a system location.

### 4. Clear the `.pyc` cache (important)

Python keeps a compiled copy: if you don't remove it, it may keep using the old
version even after copying.

```bash
sudo rm -f /usr/lib/python3/dist-packages/songpressplusplus/__pycache__/*.pyc
```

### 5. Restart the app

Fully close Songpress++ and reopen it. The change is now active.

---

## Rolling back to the original

If something goes wrong, restore the backup made in step 2:

```bash
sudo cp /usr/lib/python3/dist-packages/songpressplusplus/FILENAME.backup \
        /usr/lib/python3/dist-packages/songpressplusplus/FILENAME
sudo rm -f /usr/lib/python3/dist-packages/songpressplusplus/__pycache__/*.pyc
```

Then restart the app.

---

## Finding the right folder

If the install folder isn't the one shown above, locate it like this:

```bash
find / -name "SongTokenizer.py" 2>/dev/null
```

The folder containing `SongTokenizer.py` (and `SDIMainFrame.py`) is the right
one: use it instead of `/usr/lib/python3/dist-packages/songpressplusplus` in all
commands.

Alternative search, directly by the name of the file to replace:

```bash
find / -name "FILENAME" -path "*ongpress*" 2>/dev/null
```

---

## Useful notes

- **App updates**: if you later reinstall or update Songpress++ from the package
  (`apt`, `.deb`, `.rpm`…), the file in `/usr/lib/...` may be **overwritten** and
  your manual change lost. If so, just copy the fixed version again with the same
  commands.

- **Syntax check (optional)**: before restarting you can verify the file has no
  Python syntax errors:

  ```bash
  python3 -m py_compile /usr/lib/python3/dist-packages/songpressplusplus/FILENAME \
    && echo "OK" || echo "SYNTAX ERROR"
  ```

- **"Frozen" app (AppImage / PyInstaller)**: if you installed Songpress++ as an
  **AppImage** or single executable, the individual file **cannot** be edited by
  hand this way (the sources are packed inside the image). In that case you need
  to rebuild the package with the fixed file.

- **Fonts for musical symbols**: if you're replacing `Editor.py` for the SMP
  musical-glyph fix, make sure a font that covers them is present. FreeSerif is
  already bundled with the app; for the best rendering (like on Windows) you can
  install Noto Music:

  ```bash
  fc-list | grep -i "noto music"        # check if present
  sudo apt install fonts-noto-extra     # install if missing (Debian/Ubuntu)
  ```

---

## Practical example

Say you need to replace **`Editor.py`**, just downloaded to
**`~/Downloads/Editor.py`**. The commands become:

```bash
# 0. (Recommended) check the downloaded file is there
ls -l ~/Downloads/Editor.py

# 1. Back up the original (only once)
sudo cp /usr/lib/python3/dist-packages/songpressplusplus/Editor.py \
        /usr/lib/python3/dist-packages/songpressplusplus/Editor.py.backup

# 2. Copy the fixed version over the old one
sudo cp ~/Downloads/Editor.py \
        /usr/lib/python3/dist-packages/songpressplusplus/Editor.py

# 3. Clear the compiled cache
sudo rm -f /usr/lib/python3/dist-packages/songpressplusplus/__pycache__/*.pyc
```

Then close and reopen Songpress++ and try typing a line with the ♪ symbol.

If something goes wrong, restore the backup:

```bash
sudo cp /usr/lib/python3/dist-packages/songpressplusplus/Editor.py.backup \
        /usr/lib/python3/dist-packages/songpressplusplus/Editor.py
sudo rm -f /usr/lib/python3/dist-packages/songpressplusplus/__pycache__/*.pyc
```
