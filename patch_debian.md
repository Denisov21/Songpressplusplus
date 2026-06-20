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

## Patch 4 — Testo nero nella finestra "Statistiche brano"

**File:** `src/songpressplusplus/SongpressFrame.py`

**Problema:** Su Linux con tema scuro, il testo della finestra Statistiche
brano (righe chiave/valore di Struttura, Testo, Accordi, Metadati) è bianco
su sfondo bianco e risulta invisibile.

**Fix:** Aggiunge `SetForegroundColour(wx.BLACK)` su `k_lbl` e `v_lbl`
nella funzione interna `_row`.

### Verifica

```bash
python3 - <<'PY'
with open("src/songpressplusplus/SongpressFrame.py", "r") as f:
    content = f.read()

check = "                k_lbl.SetForegroundColour(wx.BLACK)"
print(f"{'\u2705' if check in content else '\u274c'} SetForegroundColour in _row statistiche")
PY
```

### Applicazione manuale

```bash
python3 - <<'PY'
with open("src/songpressplusplus/SongpressFrame.py", "r") as f:
    content = f.read()

old = (
    "            def _row(key, value):\n"
    "                hz = wx.BoxSizer(wx.HORIZONTAL)\n"
    "                k_lbl = wx.StaticText(scroll, label=key)\n"
    "                v_lbl = wx.StaticText(scroll, label=str(value))\n"
    "                fv = v_lbl.GetFont()\n"
    "                fv.SetWeight(wx.FONTWEIGHT_BOLD)\n"
    "                v_lbl.SetFont(fv)\n"
    "                hz.Add(k_lbl, 1, wx.ALIGN_CENTER_VERTICAL)\n"
    "                hz.Add(v_lbl, 0, wx.ALIGN_CENTER_VERTICAL)"
)
new = (
    "            def _row(key, value):\n"
    "                hz = wx.BoxSizer(wx.HORIZONTAL)\n"
    "                k_lbl = wx.StaticText(scroll, label=key)\n"
    "                k_lbl.SetForegroundColour(wx.BLACK)\n"
    "                v_lbl = wx.StaticText(scroll, label=str(value))\n"
    "                v_lbl.SetForegroundColour(wx.BLACK)\n"
    "                fv = v_lbl.GetFont()\n"
    "                fv.SetWeight(wx.FONTWEIGHT_BOLD)\n"
    "                v_lbl.SetFont(fv)\n"
    "                hz.Add(k_lbl, 1, wx.ALIGN_CENTER_VERTICAL)\n"
    "                hz.Add(v_lbl, 0, wx.ALIGN_CENTER_VERTICAL)"
)
if old in content:
    content = content.replace(old, new)
    with open("src/songpressplusplus/SongpressFrame.py", "w") as f:
        f.write(content)
    print("OK")
else:
    print("ERRORE - testo non trovato")
PY
```

### Applicazione sul file installato

```bash
sudo python3 - <<'PY'
path = "/usr/local/lib/python3.13/dist-packages/songpressplusplus/SongpressFrame.py"
with open(path, "r") as f:
    content = f.read()

old = (
    "            def _row(key, value):\n"
    "                hz = wx.BoxSizer(wx.HORIZONTAL)\n"
    "                k_lbl = wx.StaticText(scroll, label=key)\n"
    "                v_lbl = wx.StaticText(scroll, label=str(value))\n"
    "                fv = v_lbl.GetFont()\n"
    "                fv.SetWeight(wx.FONTWEIGHT_BOLD)\n"
    "                v_lbl.SetFont(fv)\n"
    "                hz.Add(k_lbl, 1, wx.ALIGN_CENTER_VERTICAL)\n"
    "                hz.Add(v_lbl, 0, wx.ALIGN_CENTER_VERTICAL)"
)
new = (
    "            def _row(key, value):\n"
    "                hz = wx.BoxSizer(wx.HORIZONTAL)\n"
    "                k_lbl = wx.StaticText(scroll, label=key)\n"
    "                k_lbl.SetForegroundColour(wx.BLACK)\n"
    "                v_lbl = wx.StaticText(scroll, label=str(value))\n"
    "                v_lbl.SetForegroundColour(wx.BLACK)\n"
    "                fv = v_lbl.GetFont()\n"
    "                fv.SetWeight(wx.FONTWEIGHT_BOLD)\n"
    "                v_lbl.SetFont(fv)\n"
    "                hz.Add(k_lbl, 1, wx.ALIGN_CENTER_VERTICAL)\n"
    "                hz.Add(v_lbl, 0, wx.ALIGN_CENTER_VERTICAL)"
)
if old in content:
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print("OK")
else:
    print("ERRORE")
PY
```

---

## Verifica rapida — tutte le patch in un colpo solo

```bash
python3 - <<'PY'
import os

BASE = "src/songpressplusplus"

checks = [
    ("SongpressFrame.py",      '            title_lbl.SetForegroundColour(wx.BLACK)',  "Patch 1a — titolo About nero"),
    ("SongpressFrame.py",      '            lbl.SetForegroundColour(wx.BLACK)',         "Patch 1b — testo About nero"),
    ("MyPreferencesDialog.py", "        if not colour.IsOk():",                        "Patch 2  — crash colore"),
    ("PreferencesDialog.py",   "btnAssocAll.Disable()",                                "Patch 3a — disabilita AssocAll"),
    ("PreferencesDialog.py",   "btnApply.Disable()",                                   "Patch 3b — disabilita Apply"),
    ("PreferencesDialog.py",   "cb.Disable()",                                         "Patch 3c — disabilita checkbox ext"),
    ("SongpressFrame.py",      "                k_lbl.SetForegroundColour(wx.BLACK)",  "Patch 4  — testo nero statistiche brano"),
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

## Note

- Tutte le patch sono **idempotenti**: se già presenti nel sorgente,
  lo script le rileva e non le applica due volte.
- Il `build_deb.sh` applica automaticamente le patch 1, 2 e 3 prima di
  costruire la wheel. Non è necessario applicare nessuna patch manualmente.
- Dopo aver applicato una patch al file installato (senza ricostruire
  il `.deb`), il fix è attivo immediatamente al prossimo avvio di
  Songpress++, senza reinstallare nulla.
