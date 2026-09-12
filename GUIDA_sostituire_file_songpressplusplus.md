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
