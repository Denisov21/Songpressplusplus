# Struttura del progetto Songpress++

Descrizione di ogni file e cartella presente nel progetto.

---

## Cartelle radice

| Cartella | Descrizione |
| -------- | ----------- |
| `src/` | Codice sorgente dell'applicazione (vedi dettaglio sotto). |
| `installer/` | File per la creazione dell'installer. |
| `build/` | Output di compilazione e packaging. |
| `dist/` | Distribuzione finale: contiene i file pronti per la distribuzione (es. eseguibili PyInstaller, archivi). |
| `.venv-build/` | Ambiente virtuale Python dedicato alla build/packaging (es. PyInstaller). Separato dall'ambiente di sviluppo principale. |
| `.idea/` | Configurazione IDE (PyCharm). |
| `.git/` | Repository Git. |

---

## File radice

### Configurazione

| File | Descrizione |
| ---- | ----------- |
| `pyproject.toml` | Configurazione del progetto Python (dipendenze, metadata, build system). Fonte unica di verità per versione app e dipendenze. |
| `requirements.txt` | Elenco delle dipendenze Python necessarie per l'esecuzione dell'applicazione. Generato da `pyproject.toml` o mantenuto manualmente; usato da `pip install -r requirements.txt` per installare l'ambiente di sviluppo. |
| `.gitignore` | Elenco di file e cartelle esclusi dal controllo versione Git (es. `.venv-build/`, `.idea/`, `build/`, `dist/`, `__pycache__/`). Quindi non vengono caricate in Git. |
| `.gitattributes` | Attributi Git per la gestione dei fine riga e dei file binari. |

### Documentazione

| File | Descrizione |
| ---- | ----------- |
| `README.md` | Documentazione principale del progetto in inglese. |
| `README_italian.md` | Documentazione principale del progetto in italiano. |
| `struttura_progetto_it.md` | Questo file. Descrizione di ogni file e cartella del progetto. |
| `guida_associazioni_file.md` | Guida alla verifica e sistemazione delle associazioni file su Windows. Copre: verifica del registro, correzione manuale tramite PowerShell, separazione tra cartella programma (`%LOCALAPPDATA%`) e dati utente (`%APPDATA%`), test di avvio con log diagnostico, reinstallazione pulita e uso della scheda "Associazioni file" in Songpress++. |
| `Elenco programmi, pacchetti Python e versioni.md` | Elenco dei programmi, pacchetti Python e versioni utilizzate. |

### Licenza

| File | Descrizione |
| ---- | ----------- |
| `license.txt` | Testo completo della licenza del progetto. |
| `license.txt.tpl` | Template usato per generare `license.txt`. |

### Script di supporto

| File | Descrizione |
| ---- | ----------- |
| `sync_deps.py` | Sincronizza automaticamente versione app e dipendenze da `pyproject.toml` a `src/install_check.vbs`. Eseguire dopo ogni modifica al toml: `python sync_deps.py` |
| `menu_sorter.py` | Strumento standalone wxPython per l'ordinamento alfabetico delle voci di menu nei file **XRC** (wxWidgets) e **FBP** (wxFormBuilder). Carica il file, mostra i menu trovati in un pannello a sinistra e, per il menu selezionato, elenca i gruppi di voci (separati da separatori) con checkbox individuali per scegliere quali ordinare. Supporta "Ordina selezionati", "Ordina tutti" e salvataggio con backup automatico (`.bak`). I colori dell'interfaccia sono personalizzabili tramite `menu_sorter_colors.json` e un dialogo opzioni integrato. Eseguibile direttamente: `python menu_sorter.py` |
| `menu_sorter_colors.json` | File di configurazione JSON dei colori dell'interfaccia di `menu_sorter.py`. Sovrascrive i valori predefiniti per le chiavi: `DARK_BG`, `PANEL_BG`, `ACCENT`, `ACCENT_LIGHT`, `TEXT_MAIN`, `TEXT_DIM`, `SUCCESS`, `WARNING`. Generato automaticamente dal dialogo Opzioni di `menu_sorter.py`; modificabile anche manualmente. |
| `fix_songpress_assoc.reg` | ~~Script del Registro di Windows per correggere l'associazione dei file `.crd` a Songpress++.~~ **Obsoleto** — le associazioni vengono ora gestite correttamente dal NSIS installer e dalla scheda "Associazioni file" in Songpress++. Può essere eliminato. |

---

## Contenuto di `src/`

### Script VBScript

| File | Descrizione |
| ---- | ----------- |
| `install_check.vbs` | Verifica che Python >= 3.12 sia installato, installa o aggiorna le dipendenze e ne controlla le versioni. Dipendenze e versione app sincronizzate da `pyproject.toml` tramite `sync_deps.py`. |
| `diagnostica.vbs` | Script di diagnostica dell'ambiente (Python, pacchetti, percorsi). |
| `Avvio SONGPRESS.vbs` | Avvia Songpress++ in modalità normale. |
| `Avvio SONGPRESS TEST.vbs` | Avvia Songpress++ in modalità test/debug. |

### Entry point e core

| File | Descrizione |
| ---- | ----------- |
| `main.py` | **Entry point** dell'applicazione. Avvia il programma, inizializza wxPython e lancia la finestra principale. |
| `__init__.py` | Marca la cartella come package Python. Di norma vuoto o con import di inizializzazione. |

### Finestre e frame

| File | Descrizione |
| ---- | ----------- |
| `SongpressFrame.py` | Finestra principale dell'applicazione. Gestisce il layout generale, la barra dei menu, la toolbar e il coordinamento tra editor e anteprima. |
| `SDIMainFrame.py` | Frame base SDI (Single Document Interface) da cui `SongpressFrame` eredita. Fornisce la struttura base della finestra con supporto per apertura/salvataggio file. SetMinSize(wx.Size(370, 520)) |

### Editor e rendering

| File | Descrizione |
| ---- | ----------- |
| `Editor.py` | Componente editor di testo. Gestisce l'immissione del testo ChordPro, la colorazione sintattica e le interazioni con la tastiera. |
| `Renderer.py` | Motore di rendering principale. Converte il testo ChordPro in output grafico per l'anteprima e la stampa. |
| `PreviewCanvas.py` | Canvas wxPython che mostra l'anteprima formattata della canzone in tempo reale mentre si modifica. |
| `SongTokenizer.py` | Tokenizer del formato ChordPro. Analizza il testo e lo scompone in token (accordi, comandi, testo) interpretabili dal renderer. |
| `Tokenizer.py` | Tokenizer generico di supporto, usato da `SongTokenizer` o da altri moduli di parsing. |
| `SongBoxes.py` | Definisce le "box" (blocchi grafici) che compongono il layout di una canzone: strofe, ritornelli, sezioni accordi, ecc. |
| `SongDecorator.py` | Applica decorazioni visive alle box (bordi, sfondi, stili) in base al tipo di sezione. |
| `SongFormat.py` | Gestisce il formato di visualizzazione della canzone: margini, colonne, spaziatura. |
| `HTML.py` | Esportazione della canzone in formato HTML. |

### Renderer specifici

| File | Descrizione |
| ---- | ----------- |
| `KlavierRenderer.py` | Renderer per le tastiere di pianoforte (`{taste:}`). Disegna i tasti con le note dell'accordo evidenziate. |
| `GuitarDiagramRenderer.py` | Renderer per i diagrammi di chitarra (`{define:}`). Disegna la tastiera con le dita posizionate. |

### Esportatori

| File | Descrizione |
| ---- | ----------- |
| `SongbookExporter.py` | Esporta una raccolta di canzoni come songbook (canzoniere) in un unico documento. |
| `PdfExporter.py` | Esporta la canzone (o il canzoniere) in formato PDF. |

### Preferenze e impostazioni

| File | Descrizione |
| ---- | ----------- |
| `Preferences.py` | Logica delle preferenze dell'applicazione (font, colori, layout, ecc.). |
| `PreferencesDialog.py` | Finestra di dialogo principale delle preferenze (wxPython). |
| `MyPreferencesDialog.py` | Variante o estensione della finestra preferenze, con personalizzazioni specifiche di Songpress. |
| `Pref.py` | Modulo di utilità per la lettura/scrittura delle preferenze su disco (es. file INI o registro). |
| `PrefTest.py` | Script di test per il modulo delle preferenze. |

### Dialoghi

| File | Descrizione |
| ---- | ----------- |
| `MyTransposeDialog.py` | Dialogo per la trasposizione degli accordi. Permette di scegliere il numero di semitoni e la direzione. |
| `TransposeDialog.py` | Versione base o alternativa del dialogo di trasposizione. |
| `MyNormalizeDialog.py` | Dialogo per la normalizzazione della notazione degli accordi (es. da inglese a italiano o viceversa). |
| `NormalizeDialog.py` | Versione base del dialogo di normalizzazione. |
| `MyNotationDialog.py` | Dialogo per la scelta della notazione musicale (italiana, inglese, ecc.). |
| `NotationDialog.py` | Versione base del dialogo di notazione. |
| `ListDialog.py` | Dialogo generico con lista di elementi selezionabili. |
| `FontFaceDialog.py` | Dialogo per la scelta del font (faccia tipografica). |
| `FontComboBox.py` | Widget ComboBox per la selezione del font, usato nei dialoghi di formattazione. |
| `errdlg.py` | Dialogo per la visualizzazione degli errori dell'applicazione. |
| `MusicalSymbolDialog.py` | Dialogo modale per scegliere e inserire simboli musicali Unicode (U+1D100–U+1D1FF e altri) nell'editor. Organizza i simboli in schede tematiche (note, pause, alterazioni, dinamiche, ecc.) con griglia di selezione, anteprima del glifo e descrizione. Carica automaticamente font SMP dalla cartella `fonts/` (FreeSerif, Bravura, Noto Music) tramite `wx.Font.AddPrivateFont`; espone `get_smp_faces()` usata da `SongDecorator` per il rendering GDI+. |
| `SyntaxCheckerDialog.py` | Dialogo che mostra l'elenco degli errori rilevati da `SyntaxChecker`. Permette di navigare direttamente alla riga errata nell'editor con un doppio clic. |

### Trasposizione e normalizzazione

| File | Descrizione |
| ---- | ----------- |
| `Transpose.py` | Logica di trasposizione degli accordi. Calcola la trasposizione di ogni accordo in base ai semitoni indicati. |
| `EditDistance.py` | Calcola la distanza di modifica (Levenshtein) tra stringhe. Usato nella normalizzazione o nel riconoscimento degli accordi. |

### Decoratori e pannelli

| File | Descrizione |
| ---- | ----------- |
| `DecoSlider.py` | Slider personalizzato usato nei pannelli di decorazione/formattazione. |
| `MyDecoSlider.py` | Variante del `DecoSlider` con personalizzazioni specifiche. |
| `SimplePropertyPanel.py` | Pannello proprietà semplificato per configurare attributi di un elemento. |
| `CompositePropertyPanel.py` | Pannello proprietà composito, con più sezioni o schede. |

### Internazionalizzazione (i18n)

| File | Descrizione |
| ---- | ----------- |
| `i18n.py` | Gestione dell'internazionalizzazione. Carica i cataloghi di traduzione `.po`/`.mo` e fornisce la funzione `_()` per le stringhe localizzate. |
| `shortcuts.py` | Definisce e gestisce le scorciatoie da tastiera dell'applicazione. |

### Utilità e strumenti

| File | Descrizione |
| ---- | ----------- |
| `Globals.py` | Variabili e costanti globali condivise tra i moduli dell'applicazione. |
| `SyntaxChecker.py` | Controllo sintattico del formato ChordPro. Verifica parentesi quadre (accordi) e graffe (comandi): rileva parentesi non chiuse, accordi vuoti `[]`, comandi sconosciuti e comandi privi di valore obbligatorio. Restituisce una lista di `SyntaxError` con riga, colonna e messaggio. |
| `utils.py` | Utilità condivise tra i moduli. Fornisce `undo_action(stc)`: context manager che raggruppa le modifiche su una `StyledTextCtrl` in un'unica azione annullabile, con supporto al nesting (le chiamate innestate sono no-op). Fornisce `temp_dir(keep=False)`: context manager che crea una directory temporanea e la elimina all'uscita (se `keep=True` la mantiene e ne registra il percorso nel log). |
| `Enumerate.py` | Fornisce una classe o funzione di enumerazione (compatibilità con versioni Python precedenti). |
| `songimpress.py` | Importazione o integrazione con il formato SongImpress (LibreOffice Impress). |

### Sottocartelle di `src/`

| Cartella | Descrizione |
| -------- | ----------- |
| `songpress/` | Package principale dell'applicazione. |
| `xrc/` | File di risorse wxPython in formato XRC (XML Resource). Definiscono il layout delle finestre in modo dichiarativo. |
| `templates/` | Template di canzone predefiniti, usati per la creazione di nuovi file. |
| `img/` | Immagini e icone dell'interfaccia grafica. |
| `decorators/` | Moduli o risorse per le decorazioni visive delle sezioni (stili grafici dei blocchi). |
| `locale/` | Cataloghi di traduzione compilati (`.mo`) e sorgenti (`.po`), organizzati per lingua (es. `locale/it/LC_MESSAGES/`). |
| `__pycache__/` | Cache dei bytecode Python (`.pyc`). Generata automaticamente. |

---

## File di localizzazione (`.po` / `.mo`)

I file `.po` sono le **traduzioni** sorgente (uno per lingua, nella cartella `locale/`).
I file `.mo` sono le versioni **compilate** dei `.po`, lette a runtime da wxPython.

| File `.po` / `.mo` | Modulo di riferimento |
| ------------------- | --------------------- |
| `CompositePropertyPanel.po` / `.mo` | `CompositePropertyPanel.py` |
| `Editor.po` / `.mo` | `Editor.py` |
| `errdlg.po` / `.mo` | `errdlg.py` |
| `FontFaceDialog.po` / `.mo` | `FontFaceDialog.py` |
| `MusicalSymbolDialog.po` / `.mo` | `MusicalSymbolDialog.py` |
| `MyPreferencesDialog.po` / `.mo` | `MyPreferencesDialog.py` |
| `NormalizeDialog.po` / `.mo` | `NormalizeDialog.py` / `MyNormalizeDialog.py` |
| `NotationDialog.po` / `.mo` | `NotationDialog.py` / `MyNotationDialog.py` |
| `Preferences.po` / `.mo` | `Preferences.py` |
| `PreferencesDialog.po` / `.mo` | `PreferencesDialog.py` |
| `PreviewCanvas.po` / `.mo` | `PreviewCanvas.py` |
| `SDIMainFrame.po` / `.mo` | `SDIMainFrame.py` |
| `SimplePropertyPanel.po` / `.mo` | `SimplePropertyPanel.py` |
| `SongbookExporter.po` / `.mo` | `SongbookExporter.py` |
| `SongpressFrame.po` / `.mo` | `SongpressFrame.py` |
| `SyntaxCheckerDialog.po` / `.mo` | `SyntaxCheckerDialog.py` |
| `Transpose.po` / `.mo` | `Transpose.py` |
| `TransposeDialog.po` / `.mo` | `TransposeDialog.py` / `MyTransposeDialog.py` |

---

## Codifica dei file

Tutti i file di testo del progetto (`.py`, `.md`, `.po`, `.vbs`, `.toml`, `.json`, `.txt`, `.xrc`, `.fbp`) devono essere salvati in codifica **UTF-8** (senza BOM).

I file `.mo` sono binari e non hanno una codifica di testo propria.



---
*Questo file è codificato UTF-8 senza BOM.*
