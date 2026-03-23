# Struttura del progetto Songpress

Descrizione di ogni file presente nella cartella del progetto.

---

## File principali (entry point e core)

| File | Descrizione |
| ---- | ----------- |
| `main.py` | **Entry point** dell'applicazione. Avvia il programma, inizializza wxPython e lancia la finestra principale. |
| `__init__.py` | Marca la cartella come package Python. Di norma vuoto o con import di inizializzazione. |

---

## Finestre e frame

| File | Descrizione |
| ---- | ----------- |
| `SongpressFrame.py` | Finestra principale dell'applicazione. Gestisce il layout generale, la barra dei menu, la toolbar e il coordinamento tra editor e anteprima. |
| `SDIMainFrame.py` | Frame base SDI (Single Document Interface) da cui `SongpressFrame` eredita. Fornisce la struttura base della finestra con supporto per apertura/salvataggio file. |

---

## Editor e rendering

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

---

## Renderer specifici

| File | Descrizione |
| ---- | ----------- |
| `KlavierRenderer.py` | Renderer per le tastiere di pianoforte (`{taste:}`). Disegna i tasti con le note dell'accordo evidenziate. |
| `GuitarDiagramRenderer.py` | Renderer per i diagrammi di chitarra (`{define:}`). Disegna la tastiera con le dita posizionate. |

---

## Esportatori

| File | Descrizione |
| ---- | ----------- |
| `SongbookExporter.py` | Esporta una raccolta di canzoni come songbook (canzoniere) in un unico documento. |
| `PdfExporter.py` | Esporta la canzone (o il canzoniere) in formato PDF. |

---

## Preferenze e impostazioni

| File | Descrizione |
| ---- | ----------- |
| `Preferences.py` | Logica delle preferenze dell'applicazione (font, colori, layout, ecc.). |
| `PreferencesDialog.py` | Finestra di dialogo principale delle preferenze (wxPython). |
| `MyPreferencesDialog.py` | Variante o estensione della finestra preferenze, con personalizzazioni specifiche di Songpress. |
| `Pref.py` | Modulo di utilità per la lettura/scrittura delle preferenze su disco (es. file INI o registro). |
| `PrefTest.py` | Script di test per il modulo delle preferenze. |

---

## Dialoghi

| File | Descrizione |
| ---- | ----------- |
| `MyTransposeDialog.py` | Dialogo per la trasposizione degli accordi. Permette di scegliere il numero di semitoni e la direzione. |
| `TransposeDialog.py` | Versione base o alternativa del dialogo di trasposizione. |
| `MyNormalizeDialog.py` | Dialogo per la normalizzazione della notazione degli accordi (es. da inglese a italiano o viceversa). |
| `NormalizeDialog.py` | Versione base del dialogo di normalizzazione. |
| `MyNotationDialog.py` | Dialogo per la scelta della notazione musicale (italiana, inglese, ecc.). |
| `NotationDialog.py` | Versione base del dialogo di notazione. |
| `MyUpdateDialog.py` | Dialogo di aggiornamento dell'applicazione (verifica nuove versioni). |
| `UpdateDialog.py` | Versione base del dialogo di aggiornamento. |
| `UpdatePanel.py` | Pannello interno al dialogo di aggiornamento. |
| `MyUpdatePanel.py` | Variante del pannello di aggiornamento con personalizzazioni. |
| `ListDialog.py` | Dialogo generico con lista di elementi selezionabili. |
| `FontFaceDialog.py` | Dialogo per la scelta del font (faccia tipografica). |
| `FontComboBox.py` | Widget ComboBox per la selezione del font, usato nei dialoghi di formattazione. |
| `errdlg.py` | Dialogo per la visualizzazione degli errori dell'applicazione. |

---

## Trasposizione e normalizzazione

| File | Descrizione |
| ---- | ----------- |
| `Transpose.py` | Logica di trasposizione degli accordi. Calcola la trasposizione di ogni accordo in base ai semitoni indicati. |
| `EditDistance.py` | Calcola la distanza di modifica (Levenshtein) tra stringhe. Usato probabilmente nella normalizzazione o nel riconoscimento degli accordi. |

---

## Decoratori e slider

| File | Descrizione |
| ---- | ----------- |
| `DecoSlider.py` | Slider personalizzato usato nei pannelli di decorazione/formattazione. |
| `MyDecoSlider.py` | Variante del `DecoSlider` con personalizzazioni specifiche. |
| `SimplePropertyPanel.py` | Pannello proprietà semplificato per configurare attributi di un elemento. |
| `CompositePropertyPanel.py` | Pannello proprietà composito, con più sezioni o schede. |

---

## Internazionalizzazione (i18n)

| File | Descrizione |
| ---- | ----------- |
| `i18n.py` | Gestione dell'internazionalizzazione. Carica i cataloghi di traduzione `.po`/`.mo` e fornisce la funzione `_()` per le stringhe localizzate. |
| `shortcuts.py` | Definisce e gestisce le scorciatoie da tastiera dell'applicazione. |

---

## Utilità e strumenti

| File | Descrizione |
| ---- | ----------- |
| `Globals.py` | Variabili e costanti globali condivise tra i moduli dell'applicazione. |
| `utils.py` | Funzioni di utilità generiche usate in più moduli. |
| `Enumerate.py` | Fornisce una classe o funzione di enumerazione (probabilmente compatibilità con versioni Python precedenti). |
| `dev_tool.py` | Strumenti di sviluppo e debug, non usati in produzione. |
| `proxiedxmlrpclib.py` | Wrapper per `xmlrpc.client` con supporto proxy. Usato per le comunicazioni di rete (es. verifica aggiornamenti). |
| `songimpress.py` | Importazione o integrazione con il formato SongImpress (LibreOffice Impress). |

---

## File di localizzazione (`.pot` / `.po`)

I file `.pot` sono i **template** di traduzione (generati dal codice sorgente).
I file `.po` sono le **traduzioni** vere e proprie (uno per lingua, nella cartella `locale/`).

| File `.pot` | Modulo di riferimento |
| ----------- | --------------------- |
| `CompositePropertyPanel.pot` | `CompositePropertyPanel.py` |
| `errdlg.pot` | `errdlg.py` |
| `FontFaceDialog.pot` | `FontFaceDialog.py` |
| `MyPreferences.pot` | `Preferences.py` / `MyPreferencesDialog.py` |
| `MyPreferencesDialog.pot` | `MyPreferencesDialog.py` |
| `MyUpdateDialog.pot` | `MyUpdateDialog.py` |
| `NormalizeDialog.pot` | `NormalizeDialog.py` / `MyNormalizeDialog.py` |
| `NotationDialog.pot` | `NotationDialog.py` / `MyNotationDialog.py` |
| `Preferences.pot` | `Preferences.py` |
| `PreferencesDialog.pot` | `PreferencesDialog.py` |
| `PreviewCanvas.pot` | `PreviewCanvas.py` |
| `SimplePropertyPanel.pot` | `SimplePropertyPanel.py` |
| `Transpose.pot` | `Transpose.py` |
| `TransposeDialog.pot` | `TransposeDialog.py` |
| `UpdateDialog.pot` | `UpdateDialog.py` |
| `UpdatePanel.pot` | `UpdatePanel.py` |

---

## Cartelle

| Cartella | Descrizione |
| -------- | ----------- |
| `__pycache__/` | Cache dei bytecode Python (`.pyc`). Generata automaticamente, non va inclusa nel controllo versione. |
| `xrc/` | File di risorse wxPython in formato XRC (XML Resource). Definiscono il layout delle finestre in modo dichiarativo. |
| `templates/` | Template di canzone predefiniti, usati per la creazione di nuovi file. |
| `img/` | Immagini e icone dell'interfaccia grafica. |
| `decorators/` | Moduli o risorse per le decorazioni visive delle sezioni (stili grafici dei blocchi). |
| `locale/` | Cataloghi di traduzione compilati (`.mo`) e sorgenti (`.po`), organizzati per lingua (es. `locale/it/LC_MESSAGES/`). |
