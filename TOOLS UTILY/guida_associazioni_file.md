# Guida: Verifica e sistemazione delle associazioni file in Songpress++

## Panoramica

Songpress++ associa le estensioni `.crd`, `.cho`, `.chordpro`, `.chopro`, `.pro`, `.tab`
all'applicazione tramite il registro di Windows (HKCU — solo per l'utente corrente,
senza privilegi di amministratore).

Il comando nel registro deve avere la forma:

```
"<INSTDIR>\bin\SongPressPlusPlus.exe" "%1"
```

dove `<INSTDIR>` è la cartella di installazione scelta durante il setup
(es. `E:\Users\Utente\AppData\Local\Songpress++`).

---

## 1. Verifica del registro

Apri **PowerShell** e lancia:

```powershell
Get-ItemProperty "HKCU:\Software\Classes\SongpressPlusPlus.ChordPro\shell\open\command"
```

### Risultato corretto

```
(default) : "E:\Users\Utente\AppData\Local\Songpress++\bin\SongPressPlusPlus.exe" "%1"
```

### Risultati errati (e cause)

| Valore `(default)` | Causa |
|---|---|
| `"...pythonw.exe" "C:\...\songpress_open.pyw" "%1"` | Versione precedente del NSIS con wrapper .pyw |
| `"C:\...\bin\SongPressPlusPlus.exe" "%1"` | Installazione su drive diverso (es. `E:`) ma registro punta a `C:` |
| Chiave assente o vuota | Associazione non eseguita durante il setup |

---

## 2. Correzione manuale del registro

Se il valore non è corretto, trova prima il percorso reale dell'exe:

```powershell
# Verifica che l'exe esista
Get-Item "E:\Users\Utente\AppData\Local\Songpress++\bin\SongPressPlusPlus.exe"
```

Sostituisci il percorso con quello reale sul tuo sistema, poi correggi il registro:

```powershell
$exe = "E:\Users\Utente\AppData\Local\Songpress++\bin\SongPressPlusPlus.exe"
Set-ItemProperty `
    "HKCU:\Software\Classes\SongpressPlusPlus.ChordPro\shell\open\command" `
    -Name "(default)" `
    -Value "`"$exe`" `"%1`""
```

Verifica il risultato:

```powershell
Get-ItemProperty "HKCU:\Software\Classes\SongpressPlusPlus.ChordPro\shell\open\command"
```

---

## 3. Verifica che il file si apra correttamente

Testa il lancio con un file reale da PowerShell:

```powershell
& "E:\Users\Utente\AppData\Local\Songpress++\bin\SongPressPlusPlus.exe" "C:\test\brano.crd"
```

> **Nota:** In PowerShell è obbligatorio il `&` prima di un percorso tra virgolette.
> In `cmd.exe` non serve.

Controlla il log di avvio (se presente):

```powershell
Get-Content "C:\Users\Utente\AppData\Local\Songpress++\startup.log" | Select-Object -Last 10
```

### Cosa cercare nel log

```
main() avviato  argv=[..., 'C:\\test\\brano.crd']
FinalizePaneInitialization  argv=[..., 'C:\\test\\brano.crd']
Scheduled OnDropFiles for: 'C:\\test\\brano.crd'  exists=True
OnDropFiles arr=['C:\\test\\brano.crd']
  fn='C:\\test\\brano.crd'  exists=True
  Open() OK
```

Se `exists=False` il percorso del file non è raggiungibile dall'app.
Se `Open() EXCEPTION` c'è un errore nel caricamento del file.

---

## 4. Separazione tra cartella programma e dati utente

Songpress++ mantiene **due cartelle distinte**, indipendentemente dal drive di installazione:

| Cosa | Percorso | Drive |
|---|---|---|
| Eseguibile, Python, tools | `<INSTDIR>\bin\`, `<INSTDIR>\tools\` | Scelto durante il setup (es. `E:`) |
| Config, templates, log | `%APPDATA%\Songpress++\` | Sempre `C:\Users\<nome>\AppData\Roaming\` |

Questo è il comportamento **corretto e intenzionale**: Windows si aspetta che i dati
utente (configurazione, file recenti, preferenze) risiedano in `%APPDATA%` su `C:`,
indipendentemente da dove è installato il programma.

`glb.InitDataPath()` usa `%APPDATA%` per i dati utente, quindi anche se installi
Songpress++ su `E:`, troverai:

- Config → `C:\Users\Utente\AppData\Roaming\Songpress++\config.ini`
- Templates → `C:\Users\Utente\AppData\Roaming\Songpress++\templates\`
- Log di avvio → `C:\Users\Utente\AppData\Local\Songpress++\startup.log`

> **Conseguenza pratica:** se cerchi il log di avvio o i file di configurazione,
> cercali sempre su `C:` anche se il programma è installato su un altro drive.

---

## 5. Verifica del percorso Python

Con `uv tool install`, il Python del venv si trova in:

```
<INSTDIR>\tools\songpressplusplus\Scripts\python.exe
```

Per verificare dove punta `~` (usato per il log e per i dati utente):

```powershell
& "E:\Users\Utente\AppData\Local\Songpress++\tools\songpressplusplus\Scripts\python.exe" `
    -c "import os; print(os.path.expanduser('~'))"
```

> **Attenzione:** Se il profilo utente è su un drive diverso da `C:` (es. `E:`),
> il log di avvio verrà scritto in `C:\Users\<nome>\AppData\Local\Songpress++\startup.log`
> perché `os.path.expanduser('~')` usa il profilo Windows (`USERPROFILE`),
> non necessariamente lo stesso drive di `LOCALAPPDATA`.

---

## 6. Ripristino tramite songpress_cleanup.py

`songpress_cleanup.py` è un tool standalone con GUI che permette di ripristinare
le associazioni file senza reinstallare e senza modificare manualmente il registro.

**Avvio:**

```
python songpress_cleanup.py
```

**Passi:**

1. Avvia lo script — si apre la finestra **Songpress++ Cleanup Tool**
2. Clicca il pulsante **🔗 Ripristina associazioni...** (giallo-verde, in basso)
3. Nel dialog che si apre, il percorso di installazione viene rilevato automaticamente
   dalla scansione di tutte le unità disponibili e dal registro
4. Se il percorso non compare nell'elenco, premi **Sfoglia...** e seleziona
   manualmente la cartella `Songpress++` (quella che contiene la sottocartella `bin\`)
5. Clicca **Ripristina associazioni**

**Cosa fa internamente:**

- Rimuove i ProgID legacy `Songpress.crd` e `Songpress.ChordPro` (se presenti)
- Elimina le voci `OpenWithProgids` sporche per tutte le estensioni gestite
- Riscrive da zero il ProgID `SongpressPlusPlus.ChordPro` con il percorso letterale
  dell'exe rilevato (nessuna variabile d'ambiente — funziona correttamente
  anche su drive diversi da `C:`)
- Associa `.crd .pro .chopro .chordpro .cho .tab` al ProgID corretto
- Notifica la shell (`SHChangeNotify`) per aggiornare Esplora risorse

> **Nota:** se le icone dei file non si aggiornano subito dopo il ripristino,
> riavvia Esplora risorse con `taskkill /f /im explorer.exe` seguito da `explorer.exe`.


---

## 7. Reinstallazione pulita

La reinstallazione corregge automaticamente il registro. Il NSIS scrive il comando
usando `$INSTDIR` risolto a runtime, quindi il percorso sarà sempre corretto
indipendentemente dal drive scelto.

**Passi:**

1. Disinstalla tramite *Impostazioni → App* oppure `uninst.exe` nella cartella di installazione
2. Riavvia il setup
3. Scegli la cartella di installazione (anche su drive diverso da `C:`)
4. Spunta **"Associa estensioni"** nella schermata del tipo di installazione
5. Dopo il completamento, verifica con:

```powershell
Get-ItemProperty "HKCU:\Software\Classes\SongpressPlusPlus.ChordPro\shell\open\command"
```

---

## 8. Verifica dalla scheda "Associazioni file" in Songpress++

Dentro Songpress++, dal menu *Opzioni → Preferenze → Associazioni file*:

- Le estensioni spuntate sono quelle attualmente associate a Songpress++
- **Applica ora** riscrive immediatamente il registro per le estensioni selezionate
- **Associa tutto** / **Disassocia tutto** seleziona/deseleziona tutte le estensioni

> Le modifiche si applicano solo all'utente corrente e non richiedono
> privilegi di amministratore.
