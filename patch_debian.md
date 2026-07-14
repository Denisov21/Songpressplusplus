# Patch Linux/Debian — SongpressPlusPlus

Questa guida elenca tutte le patch applicate al codice sorgente per la
compatibilità con Linux/Debian, come verificarle e come applicarle manualmente
se necessario.

---

## Patch 1 — Testo nero nella finestra "Informazioni su"

**File:** `src/songpressplusplus/SongpressFrame.py`

**Problema:** Su Linux con tema scuro, il testo della finestra About è bianco
su sfondo bianco e risulta invisibile. wxPython non eredita il colore del testo
da `SetBackgroundColour(wx.WHITE)`.

**Fix:** Aggiunge `SetForegroundColour(wx.BLACK)` su ogni `wx.StaticText`
della finestra About.

### Verifica

```bash
python3 - <<'PY'
with open("src/songpressplusplus/SongpressFrame.py", "r") as f:
    content = f.read()

checks = [
    '            title_lbl.SetForegroundColour(wx.BLACK)',
    '            lbl.SetForegroundColour(wx.BLACK)',
]

for c in checks:
    print(f"{'✅' if c in content else '❌'} {c.strip()!r}")
PY
```

Output atteso:
```
✅ 'title_lbl.SetForegroundColour(wx.BLACK)'
✅ 'lbl.SetForegroundColour(wx.BLACK)'
```

### Applicazione manuale

```bash
python3 - <<'PY'
with open("src/songpressplusplus/SongpressFrame.py", "r") as f:
    content = f.read()

fixes = [
    (
        '            title_lbl.SetFont(font_title)\n            hbox_title.Add(title_lbl, 0, wx.ALIGN_CENTER_VERTICAL)',
        '            title_lbl.SetFont(font_title)\n            title_lbl.SetForegroundColour(wx.BLACK)\n            hbox_title.Add(title_lbl, 0, wx.ALIGN_CENTER_VERTICAL)'
    ),
    (
        '        except Exception:\n            title_lbl = wx.StaticText(panel, label=u"Songpress++ - The Song Editor {}".format(glb.VERSION))\n            vbox.Add(title_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 10)',
        '        except Exception:\n            title_lbl = wx.StaticText(panel, label=u"Songpress++ - The Song Editor {}".format(glb.VERSION))\n            title_lbl.SetForegroundColour(wx.BLACK)\n            vbox.Add(title_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 10)'
    ),
    (
        '        def add_text(text):\n            lbl = wx.StaticText(panel, label=text)\n            vbox.Add(lbl, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 15)',
        '        def add_text(text):\n            lbl = wx.StaticText(panel, label=text)\n            lbl.SetForegroundColour(wx.BLACK)\n            vbox.Add(lbl, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 15)'
    ),
]

count = sum(1 for old, new in fixes if old in content)
for old, new in fixes:
    content = content.replace(old, new)

with open("src/songpressplusplus/SongpressFrame.py", "w") as f:
    f.write(content)
print(f"Fix applicati: {count}/3")
PY
```

### Applicazione sul file installato (senza ricostruire il .deb)

```bash
sudo python3 - <<'PY'
path = "/usr/local/lib/python3.13/dist-packages/songpressplusplus/SongpressFrame.py"

with open(path, "r") as f:
    content = f.read()

fixes = [
    (
        '            title_lbl.SetFont(font_title)\n            hbox_title.Add(title_lbl, 0, wx.ALIGN_CENTER_VERTICAL)',
        '            title_lbl.SetFont(font_title)\n            title_lbl.SetForegroundColour(wx.BLACK)\n            hbox_title.Add(title_lbl, 0, wx.ALIGN_CENTER_VERTICAL)'
    ),
    (
        '        except Exception:\n            title_lbl = wx.StaticText(panel, label=u"Songpress++ - The Song Editor {}".format(glb.VERSION))\n            vbox.Add(title_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 10)',
        '        except Exception:\n            title_lbl = wx.StaticText(panel, label=u"Songpress++ - The Song Editor {}".format(glb.VERSION))\n            title_lbl.SetForegroundColour(wx.BLACK)\n            vbox.Add(title_lbl, 0, wx.ALIGN_CENTER | wx.ALL, 10)'
    ),
    (
        '        def add_text(text):\n            lbl = wx.StaticText(panel, label=text)\n            vbox.Add(lbl, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 15)',
        '        def add_text(text):\n            lbl = wx.StaticText(panel, label=text)\n            lbl.SetForegroundColour(wx.BLACK)\n            vbox.Add(lbl, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 15)'
    ),
]

count = sum(1 for old, new in fixes if old in content)
for old, new in fixes:
    content = content.replace(old, new)

with open(path, "w") as f:
    f.write(content)
print(f"Fix applicati: {count}/3")
PY
```

---

## Patch 2 — Crash colore non valido nel selettore colori

**File:** `src/songpressplusplus/MyPreferencesDialog.py`

**Problema:** Su Linux `GetCustomColour(i)` può restituire un colore non
valido (slot vuoto). Chiamare `Red()` su un colore non valido causa un crash
`wx._core.wxAssertionError`.

**Fix:** Aggiunge un controllo `IsOk()` prima di leggere i componenti RGB.

### Verifica

```bash
python3 - <<'PY'
with open("src/songpressplusplus/MyPreferencesDialog.py", "r") as f:
    content = f.read()

check = "        if not colour.IsOk():"
print(f"{'✅' if check in content else '❌'} Controllo IsOk() presente")
PY
```

### Applicazione manuale

```bash
python3 - <<'PY'
with open("src/songpressplusplus/MyPreferencesDialog.py", "r") as f:
    content = f.read()

old = """    def _colour_to_hex(self, colour):
        return '#{:02X}{:02X}{:02X}'.format(colour.Red(), colour.Green(), colour.Blue())"""

new = """    def _colour_to_hex(self, colour):
        if not colour.IsOk():
            return '#FFFFFF'
        return '#{:02X}{:02X}{:02X}'.format(colour.Red(), colour.Green(), colour.Blue())"""

if old in content:
    content = content.replace(old, new)
    with open("src/songpressplusplus/MyPreferencesDialog.py", "w") as f:
        f.write(content)
    print("OK")
else:
    print("ERRORE - testo non trovato")
PY
```

### Applicazione sul file installato

```bash
sudo python3 - <<'PY'
path = "/usr/local/lib/python3.13/dist-packages/songpressplusplus/MyPreferencesDialog.py"

with open(path, "r") as f:
    content = f.read()

old = """    def _colour_to_hex(self, colour):
        return '#{:02X}{:02X}{:02X}'.format(colour.Red(), colour.Green(), colour.Blue())"""

new = """    def _colour_to_hex(self, colour):
        if not colour.IsOk():
            return '#FFFFFF'
        return '#{:02X}{:02X}{:02X}'.format(colour.Red(), colour.Green(), colour.Blue())"""

if old in content:
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print("OK")
else:
    print("ERRORE - testo non trovato")
PY
```

---

## Patch 3 — Pulsanti associazione file disabilitati su Linux

**File:** `src/songpressplusplus/PreferencesDialog.py`

**Problema:** Su Linux i pulsanti "Associa tutto", "Disassocia tutto" e
"Applica ora" creano file locali in `~/.local/share/` che entrano in conflitto
con le associazioni di sistema installate dal pacchetto `.deb`. Anche i
checkbox delle singole estensioni devono essere disabilitati per evitare
modifiche accidentali.

**Fix:** Disabilita i tre pulsanti e tutti i checkbox delle estensioni
automaticamente quando il sistema è Linux.

### Verifica

```bash
python3 - <<'PY'
with open("src/songpressplusplus/PreferencesDialog.py", "r") as f:
    content = f.read()

checks = [
    ("btnAssocAll.Disable()",   "Disabilita btnAssocAll"),
    ("btnUnassocAll.Disable()", "Disabilita btnUnassocAll"),
    ("btnApply.Disable()",      "Disabilita btnApply"),
    ("cb.Disable()",            "Disabilita checkbox estensioni"),
]

for code, desc in checks:
    print(f"{'✅' if code in content else '❌'} {desc}")
PY
```

Output atteso:
```
✅ Disabilita btnAssocAll
✅ Disabilita btnUnassocAll
✅ Disabilita btnApply
✅ Disabilita checkbox estensioni
```

### Applicazione manuale

```bash
python3 - <<'PY'
with open("src/songpressplusplus/PreferencesDialog.py", "r") as f:
    content = f.read()

fixes = [
    (
        "            self._btnAssocAll   = btnAssocAll\n            self._btnUnassocAll = btnUnassocAll",
        "            self._btnAssocAll   = btnAssocAll\n            self._btnUnassocAll = btnUnassocAll\n            import platform as _pl\n            if _pl.system() == 'Linux':\n                btnAssocAll.Disable()\n                btnUnassocAll.Disable()"
    ),
    (
        "            self._btnApplyFileAssoc = btnApply",
        "            self._btnApplyFileAssoc = btnApply\n            import platform as _pl2\n            if _pl2.system() == 'Linux':\n                btnApply.Disable()"
    ),
]

count = sum(1 for old, new in fixes if old in content)
for old, new in fixes:
    content = content.replace(old, new)

with open("src/songpressplusplus/PreferencesDialog.py", "w") as f:
    f.write(content)
print(f"Fix applicati: {count}/3")
PY
```

### Applicazione manuale checkbox estensioni

```bash
python3 - <<'PY'
with open("src/songpressplusplus/PreferencesDialog.py", "r") as f:
    content = f.read()

old = """            for ext in self._fileAssocExts:
                cb = wx.CheckBox(self.fileAssocPanel, wx.ID_ANY, u"." + ext)
                cb.SetToolTip(_(u"Associate the .%s file extension with Songpress++.") % ext)
                self._fileAssocCBs[ext] = cb
                bSizerFA.Add(cb, 0, wx.ALL, 4)"""

new = """            import platform as _plcb
            for ext in self._fileAssocExts:
                cb = wx.CheckBox(self.fileAssocPanel, wx.ID_ANY, u"." + ext)
                cb.SetToolTip(_(u"Associate the .%s file extension with Songpress++.") % ext)
                self._fileAssocCBs[ext] = cb
                if _plcb.system() == 'Linux':
                    cb.Disable()
                bSizerFA.Add(cb, 0, wx.ALL, 4)"""

if old in content:
    content = content.replace(old, new)
    with open("src/songpressplusplus/PreferencesDialog.py", "w") as f:
        f.write(content)
    print("OK")
else:
    print("ERRORE - testo non trovato")
PY
```

### Applicazione sul file installato

```bash
sudo python3 - <<'PY'
path = "/usr/local/lib/python3.13/dist-packages/songpressplusplus/PreferencesDialog.py"

with open(path, "r") as f:
    content = f.read()

fixes = [
    (
        "            self._btnAssocAll   = btnAssocAll\n            self._btnUnassocAll = btnUnassocAll",
        "            self._btnAssocAll   = btnAssocAll\n            self._btnUnassocAll = btnUnassocAll\n            import platform as _pl\n            if _pl.system() == 'Linux':\n                btnAssocAll.Disable()\n                btnUnassocAll.Disable()"
    ),
    (
        "            self._btnApplyFileAssoc = btnApply",
        "            self._btnApplyFileAssoc = btnApply\n            import platform as _pl2\n            if _pl2.system() == 'Linux':\n                btnApply.Disable()"
    ),
]

count = sum(1 for old, new in fixes if old in content)
for old, new in fixes:
    content = content.replace(old, new)

with open(path, "w") as f:
    f.write(content)
print(f"Fix applicati: {count}/2")
PY
```

---

## Patch 4 — Testo e sfondo nella finestra "Statistiche brano"

**File:** `src/songpressplusplus/SongpressFrame.py`

**Problema:** Su Linux con tema scuro:
- Lo sfondo del dialog è bianco hardcoded (`wx.Colour(250,250,252)`), ignorando il tema di sistema.
- Il testo delle righe chiave/valore (Struttura, Testo, Accordi, Metadati) non ha colore esplicito e risulta invisibile.
- Le stelle e il verdetto ("Ottimo per principianti" ecc.) erano in un `wx.Panel` con sfondo bianco hardcoded.
- Il testo del verdetto non aveva colore esplicito e risultava invisibile su tema scuro.

**Fix:**
- `BG` → `wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)` (segue il tema).
- `wx.WHITE` e `wx.Colour(240,245,255)` → `SYS_COLOUR_WINDOW` (finestra About, eval_panel, tastiera).
- `eval_panel` rimosso: stelle e verdetto aggiunti direttamente al sizer senza pannello con sfondo fisso.
- `wx.BLACK` → `SYS_COLOUR_WINDOWTEXT` su tutti i `SetForegroundColour` hardcoded.
- `SetForegroundColour(SYS_COLOUR_WINDOWTEXT)` esplicito su `k_lbl`, `v_lbl` e `_lbl_verdict`.

### Verifica

Usa la sezione **Verifica rapida** in fondo al documento (controlla Patch 4a–4e).

### Applicazione sul file installato (senza ricostruire il .deb)

```bash
SPPY=/usr/local/lib/python3.13/dist-packages/songpressplusplus/SongpressFrame.py
sudo sed -i \
  -e 's/SetForegroundColour(wx\.BLACK)/SetForegroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))/g' \
  -e 's/SetBackgroundColour(wx\.WHITE)/SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))/g' \
  -e 's/wx\.Colour(240, 245, 255)/wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)/g' \
  "$SPPY"
```

> **Nota:** questa patch è applicata automaticamente da `build_deb.sh` (sezione `1e`).

---

## Patch 5 — Crash `_mgr` al cambio lingua / chiusura

**File:** `src/songpressplusplus/SongpressFrame.py` e
`src/songpressplusplus/SongpressToolbars.py`

**Problema:** Cambiando lingua (es. da Italiano a Inglese) l'app fa un restart:
chiude la finestra e rilancia il processo. Mentre la finestra si chiude GTK
emette un `EVT_SIZE` che programma un aggiornamento differito delle toolbar
(`wx.CallAfter(_deferred_tb_update)`). Quando la callback viene eseguita l'AUI
manager è già stato smontato (`UnInit`) e l'attributo `_mgr` non esiste più sul
frame, quindi:

```
AttributeError: 'SongpressFrame' object has no attribute '_mgr'
  File ".../SongpressToolbars.py", line 202, in _FinalizeToolbarLayout
    pane = self._mgr.GetPane(tb)
```

La guardia `if self.frame:` non basta: `self.frame` resta "truthy" durante la
chiusura mentre `_mgr` è già sparito. È una race di teardown, non un bug di i18n.

**Fix:**
- `_deferred_tb_update` non tocca il layout se `_mgr` è assente o se il frame è
  in chiusura (`_closing`).
- `OnClose` imposta `self._closing = True` come prima istruzione.
- `_FinalizeToolbarLayout` esce subito se `_mgr` è `None` o se le toolbar non
  esistono più (protegge anche gli altri chiamanti).

### Verifica

```bash
python3 - <<'PY'
checks = [
    ("SongpressFrame.py",    "getattr(self, '_mgr', None) is not None"),
    ("SongpressFrame.py",    "self._closing = True"),
    ("SongpressToolbars.py", "if getattr(self, '_mgr', None) is None:"),
]
for fn, needle in checks:
    with open("src/songpressplusplus/" + fn) as f:
        ok = needle in f.read()
    print(f"{'✅' if ok else '❌'} {fn}: {needle!r}")
PY
```

### Applicazione manuale (sorgente)

```bash
python3 - <<'PY'
FR = "src/songpressplusplus/SongpressFrame.py"
TB = "src/songpressplusplus/SongpressToolbars.py"

with open(FR) as f: fr = f.read()
with open(TB) as f: tb = f.read()

# --- Frame: guardia in _deferred_tb_update ---
old_a = '''                    def _deferred_tb_update():
                        self._tb_layout_pending = False
                        if self.frame:
                            self._FinalizeToolbarLayout()'''
new_a = '''                    def _deferred_tb_update():
                        self._tb_layout_pending = False
                        # Durante la chiusura/riavvio l'AUI manager puo' essere
                        # gia' stato smontato (UnInit): _mgr non esiste piu'.
                        # self.frame resta "truthy" ma il layout non va toccato.
                        if (self.frame
                                and getattr(self, '_mgr', None) is not None
                                and not getattr(self, '_closing', False)):
                            self._FinalizeToolbarLayout()'''

# --- Frame: _closing in OnClose ---
old_b = '''    def OnClose(self, evt):
        if hasattr(self, '_lockKeysTimer') and self._lockKeysTimer.IsRunning():'''
new_b = '''    def OnClose(self, evt):
        self._closing = True
        if hasattr(self, '_lockKeysTimer') and self._lockKeysTimer.IsRunning():'''

# --- Toolbars: guardia in _FinalizeToolbarLayout ---
old_c = '''        self._tb_finalizing = True
        try:
            for tb in (self.mainToolBar, self.formatToolBar,
                       self.insertToolBar, self.viewToolBar):
                tb.SetGripperVisible(False)'''
new_c = '''        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        self._tb_finalizing = True
        try:
            for tb in (self.mainToolBar, self.formatToolBar,
                       self.insertToolBar, self.viewToolBar):
                tb.SetGripperVisible(False)'''

count = 0
for old, new, tgt in ((old_a, new_a, 'fr'), (old_b, new_b, 'fr'), (old_c, new_c, 'tb')):
    src = fr if tgt == 'fr' else tb
    if old in src:
        if tgt == 'fr': fr = fr.replace(old, new)
        else:           tb = tb.replace(old, new)
        count += 1

with open(FR, "w") as f: f.write(fr)
with open(TB, "w") as f: f.write(tb)
print(f"Fix applicati: {count}/3")
PY
```

### Applicazione sul file installato

```bash
sudo python3 - <<'PY'
BASE = "/usr/local/lib/python3.13/dist-packages/songpressplusplus/"
FR = BASE + "SongpressFrame.py"
TB = BASE + "SongpressToolbars.py"

with open(FR) as f: fr = f.read()
with open(TB) as f: tb = f.read()

old_a = '''                    def _deferred_tb_update():
                        self._tb_layout_pending = False
                        if self.frame:
                            self._FinalizeToolbarLayout()'''
new_a = '''                    def _deferred_tb_update():
                        self._tb_layout_pending = False
                        # Durante la chiusura/riavvio l'AUI manager puo' essere
                        # gia' stato smontato (UnInit): _mgr non esiste piu'.
                        # self.frame resta "truthy" ma il layout non va toccato.
                        if (self.frame
                                and getattr(self, '_mgr', None) is not None
                                and not getattr(self, '_closing', False)):
                            self._FinalizeToolbarLayout()'''

old_b = '''    def OnClose(self, evt):
        if hasattr(self, '_lockKeysTimer') and self._lockKeysTimer.IsRunning():'''
new_b = '''    def OnClose(self, evt):
        self._closing = True
        if hasattr(self, '_lockKeysTimer') and self._lockKeysTimer.IsRunning():'''

old_c = '''        self._tb_finalizing = True
        try:
            for tb in (self.mainToolBar, self.formatToolBar,
                       self.insertToolBar, self.viewToolBar):
                tb.SetGripperVisible(False)'''
new_c = '''        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        self._tb_finalizing = True
        try:
            for tb in (self.mainToolBar, self.formatToolBar,
                       self.insertToolBar, self.viewToolBar):
                tb.SetGripperVisible(False)'''

count = 0
for old, new, tgt in ((old_a, new_a, 'fr'), (old_b, new_b, 'fr'), (old_c, new_c, 'tb')):
    src = fr if tgt == 'fr' else tb
    if old in src:
        if tgt == 'fr': fr = fr.replace(old, new)
        else:           tb = tb.replace(old, new)
        count += 1

with open(FR, "w") as f: f.write(fr)
with open(TB, "w") as f: f.write(tb)
print(f"Fix applicati: {count}/3")
PY
```

---

## Patch 6 — Warning "Cannot set locale" con locale di sistema mancante

**File:** `src/songpressplusplus/i18n.py`

**Problema:** Cambiando lingua in inglese su un sistema dove il locale C
corrispondente (es. `en_US.UTF-8`) non è stato generato con `locale-gen`,
`wx.Locale(langid)` non riesce a chiamare `setlocale()` e wxWidgets emette un
`wxLogWarning` che, col log target GUI di default, appare come finestra
**"Cannot set locale to language 'English'."**. Inoltre, se
`FindLanguageInfo(l)` restituisce `None` per un codice sconosciuto, l'accesso
a `.Language` provoca un `AttributeError`.

**Fix:**
- Guardia su `FindLanguageInfo`: fallback a `wx.LANGUAGE_DEFAULT` se `None`.
- Costruzione di `wx.Locale` avvolta in `wx.LogNull()`: il warning non genera
  più la finestra. I cataloghi `.mo` si caricano comunque (la traduzione
  dipende dalla lingua impostata in `wx.Locale`, non dal locale C) e l'oggetto
  `mylocale` resta valido per `wx.GetLocale()` usato altrove.

### Verifica

```bash
python3 - <<'PY'
with open("src/songpressplusplus/i18n.py") as f:
    c = f.read()
checks = [
    "info = wx.Locale.FindLanguageInfo(l)",
    "info.Language if info is not None else wx.LANGUAGE_DEFAULT",
    "_nolog = wx.LogNull()",
]
for n in checks:
    print(f"{'✅' if n in c else '❌'} {n!r}")
PY
```

### Applicazione manuale (sorgente)

```bash
python3 - <<'PY'
path = "src/songpressplusplus/i18n.py"
with open(path) as f:
    content = f.read()

old = '''def setLang(l):
    global current_language, mylocale, _
    current_language = l
    langid = wx.Locale.FindLanguageInfo(l).Language
    mylocale = wx.Locale(langid)
    localedir = os.path.join(glb.path, "locale")'''

new = '''def setLang(l):
    global current_language, mylocale, _
    current_language = l
    info = wx.Locale.FindLanguageInfo(l)
    langid = info.Language if info is not None else wx.LANGUAGE_DEFAULT

    # Su sistemi dove il locale C della lingua richiesta (es. en_US.UTF-8)
    # non e' stato generato con locale-gen, wx.Locale non riesce a chiamare
    # setlocale() ed emette un wxLogWarning che, col log target GUI di
    # default, compare come finestra "Cannot set locale to language ...".
    # La traduzione (cataloghi .mo) funziona comunque, perche' dipende dalla
    # lingua impostata in wx.Locale e non dal locale C: silenziamo quindi
    # solo quel warning durante la costruzione, senza perdere le traduzioni
    # ne' l'oggetto mylocale (usato da wx.GetLocale() altrove).
    _nolog = wx.LogNull()
    try:
        mylocale = wx.Locale(langid)
    finally:
        del _nolog

    localedir = os.path.join(glb.path, "locale")'''

if old in content:
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print("OK")
else:
    print("Patch già presente o testo non trovato")
PY
```

### Applicazione sul file installato

```bash
sudo python3 - <<'PY'
path = "/usr/local/lib/python3.13/dist-packages/songpressplusplus/i18n.py"
with open(path) as f:
    content = f.read()

old = '''def setLang(l):
    global current_language, mylocale, _
    current_language = l
    langid = wx.Locale.FindLanguageInfo(l).Language
    mylocale = wx.Locale(langid)
    localedir = os.path.join(glb.path, "locale")'''

new = '''def setLang(l):
    global current_language, mylocale, _
    current_language = l
    info = wx.Locale.FindLanguageInfo(l)
    langid = info.Language if info is not None else wx.LANGUAGE_DEFAULT

    # Su sistemi dove il locale C della lingua richiesta (es. en_US.UTF-8)
    # non e' stato generato con locale-gen, wx.Locale non riesce a chiamare
    # setlocale() ed emette un wxLogWarning che, col log target GUI di
    # default, compare come finestra "Cannot set locale to language ...".
    # La traduzione (cataloghi .mo) funziona comunque, perche' dipende dalla
    # lingua impostata in wx.Locale e non dal locale C: silenziamo quindi
    # solo quel warning durante la costruzione, senza perdere le traduzioni
    # ne' l'oggetto mylocale (usato da wx.GetLocale() altrove).
    _nolog = wx.LogNull()
    try:
        mylocale = wx.Locale(langid)
    finally:
        del _nolog

    localedir = os.path.join(glb.path, "locale")'''

if old in content:
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print("OK")
else:
    print("Patch già presente o testo non trovato")
PY
```

> **Nota — locale di sistema (facoltativo):** la patch fa sì che l'inglese
> compaia senza avvisi anche se il locale C non è generato. Per avere anche
> la formattazione di numeri/date corretta si può generare il locale a livello
> di sistema (operazione manuale dell'utente, **non** inclusa nel `.deb`):
>
> ```bash
> sudo sed -i 's/^# *\(en_US.UTF-8 UTF-8\)/\1/' /etc/locale.gen
> sudo locale-gen
> ```

---

## Patch 7 — Pulsante "copia" anteprima: icona PNG e copia immagine su Wayland

**File:** `src/songpressplusplus/PreviewCanvas.py`, `src/songpressplusplus/SongpressFrame.py`

**Problema (tre parti):**

1. *Icona.* L'icona del pulsante "copia" nella toolbar dell'anteprima era
   disegnata a mano; si voleva usare il PNG del progetto `img/copy_2.png`.
2. *Il pulsante non copiava.* Il pulsante rilanciava un `wx.adv.HyperlinkEvent`
   sintetico confidando nella propagazione dell'evento fino a `main_panel`: su
   wxGTK questa propagazione dal `BitmapButton` non è affidabile, quindi
   `OnCopyAsImage` non veniva mai chiamato.
3. *La copia immagine non funziona su Wayland.* Anche chiamando direttamente
   `CopyAsImage`, la clipboard immagine di wxGTK su Wayland non registra i
   formati immagine (`wl-paste --list-types` mostra solo testo), pur riportando
   successo. È un limite noto di wxGTK/Wayland.

**Fix:**

1. `PreviewCanvas._load_copy_bitmap()` carica `img/copy_2.png` (con
   `glb.AddPath`), scalata a 16px, e ripiega **silenziosamente** sull'icona
   disegnata se il file manca (controllo `os.path.isfile` + `wx.LogNull()` per
   non far comparire il popup d'errore di wxLog).
2. `PreviewCanvas` espone `SetCopyCallback()` e `_OnCopyButton` chiama la
   callback **diretta** (niente più eventi wx). `SongpressFrame` la registra con
   `self.previewCanvas.SetCopyCallback(self.CopyAsImage)`.
3. `CopyAsImage` su **Wayland** genera il PNG e lo mette negli appunti con
   **`wl-copy --type image/png`** (pacchetto `wl-clipboard`). Su **X11/macOS**
   resta la clipboard di wx (SVG + PNG); su **Windows** invariato (metafile).
   Se `wl-copy` manca, avvisa di installare `wl-clipboard`.

> **Packaging:** `wl-clipboard` è aggiunto tra i `Recommends` del `.deb`
> (vedi `build_deb.sh`), così su Wayland viene installato di default da apt.
> Nota: il `.deb` avvia comunque l'app con `GDK_BACKEND=x11` (XWayland); il
> compositor (KDE) fa da ponte tra la clipboard Wayland di `wl-copy` e le app
> X11, quindi la copia funziona in entrambi i casi.

### Verifica

```bash
python3 - <<'PY'
import os
BASE = "src/songpressplusplus"
checks = [
    ("PreviewCanvas.py",  "def _load_copy_bitmap",   "Patch 7a — icona copy_2.png"),
    ("PreviewCanvas.py",  "def SetCopyCallback",     "Patch 7b — callback copia esposta"),
    ("PreviewCanvas.py",  "self._on_copy_callback",  "Patch 7c — _OnCopyButton usa la callback"),
    ("SongpressFrame.py", "SetCopyCallback(self.CopyAsImage)", "Patch 7d — callback registrata"),
    ("SongpressFrame.py", "def _copy_bytes_wayland", "Patch 7e — copia via wl-copy su Wayland"),
    ("SongpressFrame.py", "wl-copy",                 "Patch 7f — uso di wl-copy"),
]
for filename, needle, desc in checks:
    path = os.path.join(BASE, filename)
    try:
        with open(path) as f:
            found = needle in f.read()
        print(f"{'✅' if found else '❌'} {desc}")
    except FileNotFoundError:
        print(f"⚠️  File non trovato: {path}")
PY
```

### Applicazione

Questa patch riscrive interi metodi e ne aggiunge di nuovi in due file: non è
pratica come blocco `content.replace()`. I file sorgente
(`PreviewCanvas.py`, `SongpressFrame.py`) contengono già il fix e sono la fonte
di verità. Per applicarla al file **installato** senza ricostruire il `.deb`,
copiare i due file:

```bash
SRC=~/Songpress_DEFINitiVO3/SongpressPlusPlus/src/songpressplusplus
DST=/usr/local/lib/python3.13/dist-packages/songpressplusplus
sudo cp "$SRC/PreviewCanvas.py"  "$DST/PreviewCanvas.py"
sudo cp "$SRC/SongpressFrame.py" "$DST/SongpressFrame.py"
```

Serve inoltre il PNG dell'icona e il pacchetto wl-clipboard:

```bash
# icona (se non già presente nell'installato)
sudo cp "$SRC/img/copy_2.png" "$DST/img/copy_2.png"
# strumento clipboard Wayland
sudo apt install wl-clipboard
```

### Test funzionale (Wayland)

Per prima cosa, verifica se la sessione è X11 o Wayland (il percorso `wl-copy`
si attiva solo su Wayland):

```bash
# metodo rapido (variabile d'ambiente della sessione grafica)
echo "$XDG_SESSION_TYPE"      # stampa  wayland  oppure  x11

# metodo autorevole (systemd-logind, consigliato sulle distro recenti)
loginctl show-session "$(loginctl --no-legend list-sessions | awk -v u="$USER" '$3==u {print $1; exit}')" -p Type --value
```

Poi prova la copia:

```bash
# dopo aver premuto "copia" in Songpress, con l'app ancora aperta:
wl-paste --list-types                 # deve comparire  image/png
wl-paste --type image/png > /tmp/t.png && xdg-open /tmp/t.png
```

---

## Patch 8 — "Apri cartella template": crash `explorer` e cartella non scrivibile

**File:** `src/songpressplusplus/MyPreferencesDialog.py`,
`src/songpressplusplus/Globals.py`, `build_deb.sh`

**Problema (tre parti):**

1. *Comando Windows su Linux.* `MyPreferencesDialog.OnOpenTemplatesFolder()`
   lanciava `subprocess.Popen(['explorer', path])`, comando che su Linux non
   esiste: premendo **Opzioni → Generale → "Apri cartella template"** compariva
   il dialogo di errore `[Errno 2] File o directory non esistente: 'explorer'`.
2. *Cartella di destinazione sbagliata.* La funzione puntava a
   `templates/` **accanto al pacchetto**, cioè
   `/usr/local/lib/python3.13/dist-packages/songpressplusplus/templates/`: con
   l'installazione `.deb` quella cartella appartiene a `root` ed è in sola
   lettura per l'utente, che quindi non potrebbe comunque salvarvi i propri
   template. Peggio, `os.makedirs(..., exist_ok=True)` **non** solleva errore su
   una cartella già esistente di root, quindi il controllo di scrivibilità non
   scattava.
3. *Crash su `templates/slides` mancante.* `Globals.ListLocalGlobalDir()`
   chiamava `os.listdir()` su entrambe le radici **senza verificarne
   l'esistenza**: se `templates/slides/` non era presente nella cartella dati
   utente (perché `templates/local_dir/` non era stata inclusa nella wheel),
   l'esportazione PowerPoint sollevava `FileNotFoundError`.

**Fix:**

1. `OnOpenTemplatesFolder()` è ora **multipiattaforma**: `os.startfile()` su
   Windows (gestisce spazi e caratteri non ASCII e non lascia processi appesi,
   a differenza di `Popen(['explorer', ...])`), `open` su macOS, **`xdg-open`**
   su Linux/BSD (standard freedesktop: su KDE inoltra a Dolphin, su GNOME a
   Nautilus), lanciato con `start_new_session=True` e output su `DEVNULL`. Se
   `xdg-open` manca, ripiega su `wx.LaunchDefaultApplication()` e in ultima
   istanza suggerisce `sudo apt install xdg-utils`.
2. Nuovo `MyPreferencesDialog._get_templates_dir()`, allineato alle radici che
   `SongpressFrame._PopulateTemplateMenu()` già scandisce: sceglie la prima
   cartella **scrivibile** tra `glb.data_path/templates` (cartella dati utente),
   `glb.path/templates` (pacchetto, valida solo per sorgenti/venv/portable) e
   `~/.Songpress++/templates` (rete di sicurezza). Il nuovo helper
   `_is_writable_templates_dir()` fa un test esplicito con
   `os.access(d, W_OK | X_OK)`, perché `makedirs(exist_ok=True)` da solo non
   rileva una cartella di sistema già esistente.
3. `Globals.ListLocalGlobalDir()` salta le cartelle mancanti o illeggibili e
   gestisce `data_path` non ancora inizializzato (stessa tolleranza di
   `_PopulateTemplateMenu()`). `Globals.InitDataPath()` crea inoltre sempre
   `templates/songs` e `templates/slides` dentro la cartella dati utente, anche
   se `templates/local_dir/` è incompleta o assente.

> **Percorso finale su Debian.** Con il `.deb`, la cartella aperta dal pulsante
> è la cartella dati utente ricavata da `wx.StandardPaths.GetUserDataDir()`:
>
> ```
> ~/.Songpress++/templates/
> ├── songs/     ← template di brani (.crd) → menu "File → Nuovo da template"
> └── slides/    ← template PowerPoint (.pptx) → esportazione presentazioni
> ```
>
> I file qui presenti **hanno la precedenza** sugli omonimi installati a livello
> di sistema dal pacchetto.

> **Packaging:** `xdg-utils` (che fornisce `xdg-open`) è aggiunto tra i
> `Depends` del `.deb`. `build_deb.sh` verifica inoltre, dopo l'installazione
> della wheel, che `templates/local_dir/templates/{songs,slides}` e
> `templates/{songs,slides}` esistano nel pacchetto: se mancano le crea con un
> file segnaposto `.keep` (git non versiona le directory vuote) e stampa un
> avviso con lo snippet `pyproject.toml` per la correzione permanente.

### Verifica

```bash
python3 - <<'PY'
import os
BASE = "src/songpressplusplus"
checks = [
    ("MyPreferencesDialog.py", "def _get_templates_dir",        "Patch 8a — helper cartella template"),
    ("MyPreferencesDialog.py", "def _is_writable_templates_dir","Patch 8b — test di scrivibilità"),
    ("MyPreferencesDialog.py", "xdg-open",                      "Patch 8c — apertura cartella su Linux"),
    ("Globals.py",             "if not os.path.isdir(folder):", "Patch 8d — ListLocalGlobalDir tollerante"),
    ("Globals.py",             "'templates', 'slides'",         "Patch 8e — sottocartelle create in InitDataPath"),
]
for filename, needle, desc in checks:
    path = os.path.join(BASE, filename)
    try:
        with open(path) as f:
            found = needle in f.read()
        print(f"{'✅' if found else '❌'} {desc}")
    except FileNotFoundError:
        print(f"⚠️  File non trovato: {path}")

# 'explorer' non deve più comparire da nessuna parte
p = os.path.join(BASE, "MyPreferencesDialog.py")
if os.path.isfile(p):
    bad = "'explorer'" in open(p).read()
    print(f"{'❌' if bad else '✅'} Patch 8f — nessun residuo di 'explorer'")
PY
```

Verifica che la dipendenza sia dichiarata nel pacchetto costruito:

```bash
grep -n "xdg-utils" build_deb.sh
dpkg-deb -f build_deb/songpressplusplus_*.deb Depends   # deve contenere xdg-utils
```

### Applicazione sul file installato (senza ricostruire il .deb)

La patch riscrive interi metodi in due file: i sorgenti sono la fonte di verità.

```bash
SRC=~/Songpress_DEFINitiVO3/SongpressPlusPlus/src/songpressplusplus
DST=/usr/local/lib/python3.13/dist-packages/songpressplusplus
sudo cp "$SRC/MyPreferencesDialog.py" "$DST/MyPreferencesDialog.py"
sudo cp "$SRC/Globals.py"             "$DST/Globals.py"
sudo apt install xdg-utils
```

### Test funzionale

```bash
# 1. xdg-open è presente?
command -v xdg-open || sudo apt install xdg-utils

# 2. quale gestore file verrebbe usato?
xdg-mime query default inode/directory      # es. org.kde.dolphin.desktop

# 3. la cartella dati utente esiste con le sue sottocartelle?
ls -la ~/.Songpress++/templates/            # deve mostrare songs/ e slides/
```

Poi, in Songpress++: **Strumenti → Opzioni → Generale → "Apri cartella
template"**. Deve aprirsi Dolphin (o il gestore file predefinito) su
`~/.Songpress++/templates/`, **senza** alcun dialogo di errore. Copiando un
file `.crd` in `songs/`, questo compare al riavvio nel menu
**File → Nuovo da template**.

---

## Verifica rapida — tutte le patch in un colpo solo

```bash
python3 - <<'PY'
import os

BASE = "src/songpressplusplus"
FG = "wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)"

checks = [
    ("SongpressFrame.py",      f'            title_lbl.SetForegroundColour({FG})',            "Patch 1a — titolo About leggibile"),
    ("SongpressFrame.py",      f'            lbl.SetForegroundColour({FG})',                   "Patch 1b — testo About leggibile"),
    ("MyPreferencesDialog.py", "        if not colour.IsOk():",                              "Patch 2  — crash colore"),
    ("PreferencesDialog.py",   "btnAssocAll.Disable()",                                      "Patch 3a — disabilita AssocAll"),
    ("PreferencesDialog.py",   "btnApply.Disable()",                                         "Patch 3b — disabilita Apply"),
    ("PreferencesDialog.py",   "cb.Disable()",                                               "Patch 3c — disabilita checkbox ext"),
    ("SongpressFrame.py",      "BG      = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)","Patch 4a — BG statistiche tema sistema"),
    ("SongpressFrame.py",      f"                    _lbl_verdict.SetForegroundColour({FG})","Patch 4b — verdetto multi-tab leggibile"),
    ("SongpressFrame.py",      f"            _lbl_verdict.SetForegroundColour({FG})",        "Patch 4c — verdetto singolo leggibile"),
    ("SongpressFrame.py",      f"                    k_lbl.SetForegroundColour({FG})",       "Patch 4d — testo _row multi-tab leggibile"),
    ("SongpressFrame.py",      f"            k_lbl.SetForegroundColour({FG})",               "Patch 4e — testo _row singolo leggibile"),
    ("SongpressFrame.py",      "getattr(self, '_mgr', None) is not None",                    "Patch 5a — guardia _mgr in _deferred_tb_update"),
    ("SongpressFrame.py",      "self._closing = True",                                       "Patch 5b — _closing in OnClose"),
    ("SongpressToolbars.py",   "if getattr(self, '_mgr', None) is None:",                    "Patch 5c — guardia _mgr in _FinalizeToolbarLayout"),
    ("i18n.py",                "_nolog = wx.LogNull()",                                      "Patch 6  — warning locale silenziato"),
    ("PreviewCanvas.py",       "def _load_copy_bitmap",                                      "Patch 7a — icona copy_2.png"),
    ("PreviewCanvas.py",       "def SetCopyCallback",                                        "Patch 7b — callback copia esposta"),
    ("PreviewCanvas.py",       "self._on_copy_callback",                                     "Patch 7c — _OnCopyButton usa la callback"),
    ("SongpressFrame.py",      "SetCopyCallback(self.CopyAsImage)",                          "Patch 7d — callback registrata"),
    ("SongpressFrame.py",      "def _copy_bytes_wayland",                                    "Patch 7e — copia via wl-copy su Wayland"),
    ("MyPreferencesDialog.py", "def _get_templates_dir",                                     "Patch 8a — helper cartella template"),
    ("MyPreferencesDialog.py", "def _is_writable_templates_dir",                             "Patch 8b — test di scrivibilità"),
    ("MyPreferencesDialog.py", "xdg-open",                                                   "Patch 8c — apertura cartella su Linux"),
    ("Globals.py",             "if not os.path.isdir(folder):",                              "Patch 8d — ListLocalGlobalDir tollerante"),
    ("Globals.py",             "'templates', 'slides'",                                      "Patch 8e — sottocartelle create in InitDataPath"),
]

for filename, needle, desc in checks:
    path = os.path.join(BASE, filename)
    try:
        with open(path) as f:
            found = needle in f.read()
        print(f"{'✅' if found else '❌'} {desc}")
    except FileNotFoundError:
        print(f"⚠️  File non trovato: {path}")
PY
```

---

## Note sulle associazioni file

Il pacchetto `.deb` registra automaticamente tutte le estensioni ChordPro
(`.crd`, `.cho`, `.chordpro`, `.chopro`, `.pro`, `.sng`) tramite il file
`/usr/share/mime/packages/songpressplusplus.xml` e il campo `MimeType=`
nel file `.desktop`. Non è necessario usare la scheda "Associazioni file"
dentro Songpress++ — i pulsanti sono disabilitati automaticamente su Linux.

---

## Build e installazione

```bash
chmod +x ~/Songpress_DEFINitiVO3/SongpressPlusPlus/build_deb.sh
cd ~/Songpress_DEFINitiVO3/SongpressPlusPlus
./build_deb.sh
sudo dpkg -i build_deb/songpressplusplus_*.deb
```

---

## Note

- Tutte le patch sono **idempotenti**: se già presenti nel sorgente,
  lo script le rileva e non le applica due volte.
- Il `build_deb.sh` applica automaticamente tutte le patch **prima** di
  costruire la wheel (ordine: patch → wheel → install). Non è necessario
  applicare nessuna patch manualmente.
- **Importante:** le patch devono essere applicate prima di `pip wheel`,
  non dopo. Se la wheel viene costruita prima delle patch, le modifiche
  al sorgente non entrano nel pacchetto installato.
- Dopo aver applicato una patch al file installato (senza ricostruire
  il `.deb`), il fix è attivo immediatamente al prossimo avvio di
  Songpress++, senza reinstallare nulla.
