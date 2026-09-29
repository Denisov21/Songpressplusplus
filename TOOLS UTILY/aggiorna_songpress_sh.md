## Caso reale: script Bash con symlink

### Scenario
Lo script `aggiorna_songpress.sh` si trova in:
```
/home/denis/Songpress_DEFINitiVO3/SongpressPlusPlus/TOOLS UTILY/aggiorna_songpress.sh
```
Si vuole richiamarlo comodamente dalla cartella principale del progetto tramite un collegamento simbolico.

### Creare il collegamento (percorso assoluto)
```bash
ln -s "/home/denis/Songpress_DEFINitiVO3/SongpressPlusPlus/TOOLS UTILY/aggiorna_songpress.sh" \
      /home/denis/Songpress_DEFINitiVO3/SongpressPlusPlus/aggiorna_songpress.sh
```

### Creare il collegamento (percorso relativo — consigliato)
```bash
cd /home/denis/Songpress_DEFINitiVO3/SongpressPlusPlus
ln -s "TOOLS UTILY/aggiorna_songpress.sh" aggiorna_songpress.sh
```

### Rendere eseguibile lo script originale
```bash
chmod +x "/home/denis/Songpress_DEFINitiVO3/SongpressPlusPlus/TOOLS UTILY/aggiorna_songpress.sh"
```

### Verificare il collegamento
```bash
ls -l /home/denis/Songpress_DEFINitiVO3/SongpressPlusPlus/aggiorna_songpress.sh
# output atteso:
# aggiorna_songpress.sh -> TOOLS UTILY/aggiorna_songpress.sh
```

### Eseguire lo script dal collegamento
```bash
cd /home/denis/Songpress_DEFINitiVO3/SongpressPlusPlus
./aggiorna_songpress.sh

# oppure con il percorso completo:
/home/denis/Songpress_DEFINitiVO3/SongpressPlusPlus/aggiorna_songpress.sh
```

### Come funziona `aggiorna_songpress.sh`

Lo script copia un file `.py` da `~/Scaricati` in
`/usr/lib/python3/dist-packages/songpressplusplus`, creando prima una copia di
sicurezza `.bak`. Richiede `sudo` per scrivere in quella cartella di sistema.

**Flusso:**
1. Chiede il nome del file da aggiornare (es. `MyPreferencesDialog.py`)
2. Verifica che esista in `~/Scaricati`
3. Crea `nomefile.py.bak` nella destinazione (se il file esiste già)
4. Copia il nuovo file nella destinazione
5. Confronta i due file con `cmp` per confermare l'integrità

**⚠️ Nota su `$0` e symlink**

Lo script non usa `dirname "$0"`, quindi non è affetto dal problema
del percorso relativo. Se in futuro dovesse usarlo, ricorda:

```bash
# ❌ Restituisce la cartella del collegamento, non dello script reale
SCRIPT_DIR="$(dirname "$0")"

# ✅ Restituisce sempre la cartella dello script reale
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
```**
```

### Primo avvio: rendere eseguibile e lanciare

Se è la prima volta che si usa lo script (o il collegamento appena creato):

```bash
# 1. Entra nella cartella del progetto
cd /home/denis/Songpress_DEFINitiVO3/SongpressPlusPlus

# 2. Rendi eseguibile il file ORIGINALE (non il collegamento)
chmod +x "TOOLS UTILY/aggiorna_songpress.sh"

# 3. Avvia lo script tramite il collegamento
./aggiorna_songpress.sh
```

> **Nota:** `chmod +x` va dato sull'originale in `TOOLS UTILY/`, non sul collegamento.
> Il collegamento eredita automaticamente i permessi del file reale.