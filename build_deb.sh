#!/usr/bin/env bash
# =============================================================================
# build_deb.sh — Costruisce il pacchetto .deb per SongpressPlusPlus
#
# Uso:
#   chmod +x build_deb.sh
#   ./build_deb.sh
#
# Prerequisiti sul sistema:
#   - Python >= 3.12
#   - pip, venv
#   - dpkg-deb  (pacchetto dpkg, già presente su ogni Debian/Ubuntu)
#   - fakeroot  (facoltativo ma raccomandato per creare il .deb senza root)
#
# Lo script:
#   1. Legge versione e nome dal pyproject.toml presente nella stessa cartella
#   2. Costruisce la wheel con pip/hatchling
#   3. Crea l'albero di directory DEBIAN-compliant
#   4. Installa la wheel nell'albero con pip --prefix
#   5. Crea wrapper GDK_BACKEND=x11 e symlink minuscolo
#   6. Scrive il file DEBIAN/control
#   7. Chiama fakeroot dpkg-deb per produrre il .deb finale
# =============================================================================

set -euo pipefail

# ── Configurazione ────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Legge versione e nome da pyproject.toml
PKG_NAME=$(python3 - <<'PY'
import tomllib
with open("pyproject.toml", "rb") as f:
    d = tomllib.load(f)
print(d["project"]["name"])
PY
)
PKG_VERSION=$(python3 - <<'PY'
import tomllib
with open("pyproject.toml", "rb") as f:
    d = tomllib.load(f)
print(d["project"]["version"])
PY
)

# Nome del pacchetto deb: tutto minuscolo, trattini al posto di trattini bassi
DEB_NAME=$(echo "$PKG_NAME" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
DEB_VERSION="$PKG_VERSION"
DEB_ARCH="all"
MAINTAINER="Denisov21"
DESCRIPTION="Songpress++ is a free, easy-to-use song typesetting program
 that generates high-quality songbooks (PDF, PPTX)."
HOMEPAGE="https://github.com/Denisov21/Songpressplusplus"

# Dipendenze runtime Debian/Ubuntu equivalenti
DEPENDS="python3 (>= 3.12), python3-wxgtk4.0 | python3-wxpython4, \
python3-requests, python3-reportlab, python3-markdown, python3-mistune, \
python3-pypdf"

# Cartelle di lavoro
BUILD_DIR="$SCRIPT_DIR/build_deb"
PKG_ROOT="$BUILD_DIR/${DEB_NAME}_${DEB_VERSION}"
INSTALL_PREFIX="$PKG_ROOT/usr"

# ── Pulizia precedente build ──────────────────────────────────────────────────
echo "==> Pulizia build precedente..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# ── 1. Build della wheel ──────────────────────────────────────────────────────
echo "==> Costruzione wheel con pip + hatchling..."
WHEEL_DIR="$BUILD_DIR/wheel"
mkdir -p "$WHEEL_DIR"

PYTHON="${VIRTUAL_ENV:+$VIRTUAL_ENV/bin/python3}"
PYTHON="${PYTHON:-python3}"

"$PYTHON" -m pip wheel \
    --no-deps \
    --wheel-dir "$WHEEL_DIR" \
    "$SCRIPT_DIR"

WHEEL_FILE=$(ls "$WHEEL_DIR"/*.whl | head -n1)
echo "    Wheel: $WHEEL_FILE"

# ── 1b. Patch SongpressFrame.py: SetForegroundColour nella finestra About ────
echo "==> Patch SetForegroundColour finestra About..."
"$PYTHON" - <<'PATCH'
import re, sys

path = None
import subprocess
result = subprocess.run(
    ["find", "src/songpressplusplus", "-name", "SongpressFrame.py"],
    capture_output=True, text=True
)
candidates = result.stdout.strip().splitlines()
if candidates:
    path = candidates[0]

if not path:
    print("    SongpressFrame.py non trovato, skip patch.")
    sys.exit(0)

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
print(f"    Patch applicata: {count}/3 fix in {path}")
PATCH

# ── 1c. Patch PreferencesDialog.py: disabilita pulsanti assoc su Linux ───────
echo "==> Patch pulsanti associazione file (Linux)..."
"$PYTHON" - <<'PATCH2'
import subprocess, sys

result = subprocess.run(
    ["find", "src/songpressplusplus", "-name", "PreferencesDialog.py"],
    capture_output=True, text=True
)
candidates = result.stdout.strip().splitlines()
if not candidates:
    print("    PreferencesDialog.py non trovato, skip patch.")
    sys.exit(0)

path = candidates[0]
with open(path, "r") as f:
    content = f.read()

fixes = [
    (
        '            btnAssocAll.Bind(wx.EVT_BUTTON, self.OnAssociateAll)\n            btnUnassocAll.Bind(wx.EVT_BUTTON, self.OnUnassociateAll)\n            self._btnAssocAll   = btnAssocAll\n            self._btnUnassocAll = btnUnassocAll',
        '            btnAssocAll.Bind(wx.EVT_BUTTON, self.OnAssociateAll)\n            btnUnassocAll.Bind(wx.EVT_BUTTON, self.OnUnassociateAll)\n            self._btnAssocAll   = btnAssocAll\n            self._btnUnassocAll = btnUnassocAll\n            import platform as _pl\n            if _pl.system() == \'Linux\':\n                btnAssocAll.Disable()\n                btnUnassocAll.Disable()'
    ),
    (
        '            btnApply.Bind(wx.EVT_BUTTON, self.OnApplyFileAssoc)\n            self._btnApplyFileAssoc = btnApply',
        '            btnApply.Bind(wx.EVT_BUTTON, self.OnApplyFileAssoc)\n            self._btnApplyFileAssoc = btnApply\n            import platform as _pl2\n            if _pl2.system() == \'Linux\':\n                btnApply.Disable()'
    ),
    (
        '            for ext in self._fileAssocExts:\n                cb = wx.CheckBox(self.fileAssocPanel, wx.ID_ANY, u"." + ext)\n                cb.SetToolTip(_(u"Associate the .%s file extension with Songpress++.") % ext)\n                self._fileAssocCBs[ext] = cb\n                bSizerFA.Add(cb, 0, wx.ALL, 4)',
        '            import platform as _plcb\n            for ext in self._fileAssocExts:\n                cb = wx.CheckBox(self.fileAssocPanel, wx.ID_ANY, u"." + ext)\n                cb.SetToolTip(_(u"Associate the .%s file extension with Songpress++.") % ext)\n                self._fileAssocCBs[ext] = cb\n                if _plcb.system() == \'Linux\':\n                    cb.Disable()\n                bSizerFA.Add(cb, 0, wx.ALL, 4)'
    ),
]

count = sum(1 for old, new in fixes if old in content)
for old, new in fixes:
    content = content.replace(old, new)

with open(path, "w") as f:
    f.write(content)
print(f"    Patch applicata: {count}/3 fix in {path}")
PATCH2

# ── 1d. Patch MyPreferencesDialog.py: IsOk() prima di Red()/Green()/Blue() ────
echo "==> Patch crash colore selettore (IsOk)..."
"$PYTHON" - <<'PATCH3'
import subprocess, sys

result = subprocess.run(
    ["find", "src/songpressplusplus", "-name", "MyPreferencesDialog.py"],
    capture_output=True, text=True
)
candidates = result.stdout.strip().splitlines()
if not candidates:
    print("    MyPreferencesDialog.py non trovato, skip patch.")
    sys.exit(0)

path = candidates[0]
with open(path, "r") as f:
    content = f.read()

old = '''    def _colour_to_hex(self, colour):
        return '#{:02X}{:02X}{:02X}'.format(colour.Red(), colour.Green(), colour.Blue())'''

new = '''    def _colour_to_hex(self, colour):
        if not colour.IsOk():
            return '#FFFFFF'
        return '#{:02X}{:02X}{:02X}'.format(colour.Red(), colour.Green(), colour.Blue())'''

if old in content:
    content = content.replace(old, new)
    with open(path, "w") as f:
        f.write(content)
    print(f"    Patch applicata: 1/1 fix in {path}")
else:
    print(f"    Patch già presente o testo non trovato in {path}")
PATCH3

# ── 2. Installazione nell'albero del pacchetto ────────────────────────────────
echo "==> Installazione nell'albero del pacchetto..."
mkdir -p "$INSTALL_PREFIX/share/applications"
mkdir -p "$INSTALL_PREFIX/share/pixmaps"
mkdir -p "$INSTALL_PREFIX/share/mime/packages"

"$PYTHON" -m pip install \
    --no-deps \
    --ignore-installed \
    --prefix "$INSTALL_PREFIX" \
    --no-compile \
    "$WHEEL_FILE"

# Corregge il path site-packages → dist-packages (convenzione Debian)
SITE_PKG=$(find "$INSTALL_PREFIX" -maxdepth 5 -type d -name "site-packages" | head -n1)
if [[ -n "$SITE_PKG" ]]; then
    DIST_PKG="${SITE_PKG/site-packages/dist-packages}"
    mkdir -p "$(dirname "$DIST_PKG")"
    mv "$SITE_PKG" "$DIST_PKG"
    rmdir "$(dirname "$SITE_PKG")" 2>/dev/null || true
fi

# ── 3. Desktop entry & icona ─────────────────────────────────────────────────
echo "==> Creazione .desktop e icona..."

ICON_SRC="$SCRIPT_DIR/installer/songpressplusplus.ico"
ICON_PNG="$SCRIPT_DIR/installer/songpressplusplus.png"
if [[ -f "$ICON_PNG" ]]; then
    cp "$ICON_PNG" "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png"
elif [[ -f "$ICON_SRC" ]]; then
    if command -v convert &>/dev/null; then
        # Estrae solo il primo layer [0] dell'ico → PNG con nome corretto
        convert "${ICON_SRC}[0]" -resize 64x64 \
            "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png" 2>/dev/null || \
        convert "$ICON_SRC" -thumbnail 64x64 \
            "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png" 2>/dev/null || true
    fi
fi
# Fallback: se convert ha prodotto file numerati (nome-0.png, nome-1.png...)
# invece del file atteso (nome.png), usa il primo layer e rimuovi gli altri.
if [[ ! -f "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png" ]]; then
    FIRST_LAYER=$(ls "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}-"*.png 2>/dev/null | sort | head -n1)
    if [[ -n "$FIRST_LAYER" ]]; then
        cp "$FIRST_LAYER" "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png"
        echo "    Icona: usato layer $FIRST_LAYER"
    fi
fi
# Rimuove sempre i layer numerati residui
rm -f "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}-"*.png

# Installa icona nelle cartelle hicolor/mimetypes per KDE/GNOME
# (necessario perché KDE usa hicolor per le icone dei tipi MIME)
if [[ -f "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png" ]]; then
    for SIZE in 256 128 64 48; do
        mkdir -p "$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/apps"
        mkdir -p "$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/mimetypes"
        if command -v convert &>/dev/null; then
            convert "$INSTALL_PREFIX/share/pixmaps/${DEB_NAME}.png"                 -resize "${SIZE}x${SIZE}"                 "$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/apps/${DEB_NAME}.png"                 2>/dev/null || true
            cp "$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/apps/${DEB_NAME}.png"                "$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/mimetypes/${DEB_NAME}.png"                2>/dev/null || true
        fi
    done
    echo "    Icone hicolor installate (256/128/64/48)"
fi

# File XML tipo MIME per estensioni ChordPro
cat > "$INSTALL_PREFIX/share/mime/packages/${DEB_NAME}.xml" <<'MIME'
<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
  <mime-type type="text/x-chordpro">
    <comment>ChordPro song file</comment>
    <comment xml:lang="it">File canzone ChordPro</comment>
    <glob pattern="*.crd"/>
    <glob pattern="*.cho"/>
    <glob pattern="*.chordpro"/>
    <glob pattern="*.chopro"/>
    <glob pattern="*.pro"/>
    <glob pattern="*.sng"/>
    <icon name="songpressplusplus"/>
  </mime-type>
</mime-info>
MIME

cat > "$INSTALL_PREFIX/share/applications/${DEB_NAME}.desktop" <<DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Songpress++
GenericName=Song Typesetter
Comment=Genera canzonieri di alta qualità in PDF e PPTX
Exec=env GDK_BACKEND=x11 /usr/local/bin/SongpressPlusPlus %f
Icon=${DEB_NAME}
Terminal=false
Categories=Office;Publishing;Education;
Keywords=song;chords;songbook;pdf;
MimeType=text/x-chordpro;
StartupNotify=true
DESKTOP

# ── 4. File DEBIAN/control ────────────────────────────────────────────────────
echo "==> Scrittura DEBIAN/control..."
mkdir -p "$PKG_ROOT/DEBIAN"

INSTALLED_SIZE=$(du -sk "$INSTALL_PREFIX" | awk '{print $1}')

cat > "$PKG_ROOT/DEBIAN/control" <<CONTROL
Package: ${DEB_NAME}
Version: ${DEB_VERSION}
Architecture: ${DEB_ARCH}
Maintainer: ${MAINTAINER}
Installed-Size: ${INSTALLED_SIZE}
Depends: ${DEPENDS}
Section: utils
Priority: optional
Homepage: ${HOMEPAGE}
Description: ${DESCRIPTION}
CONTROL

# ── 5. Script postinst / postrm ───────────────────────────────────────────────
cat > "$PKG_ROOT/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database /usr/share/mime || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -qf /usr/share/icons/hicolor || true
fi
POSTINST
chmod 0755 "$PKG_ROOT/DEBIAN/postinst"

cat > "$PKG_ROOT/DEBIAN/postrm" <<'POSTRM'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
POSTRM
chmod 0755 "$PKG_ROOT/DEBIAN/postrm"

# ── 6. Permessi ───────────────────────────────────────────────────────────────
echo "==> Impostazione permessi..."
find "$PKG_ROOT" -type d -exec chmod 0755 {} \;
find "$PKG_ROOT" -type f -exec chmod 0644 {} \;
# Rende eseguibili tutti i file in qualsiasi cartella bin/ (usr/bin e usr/local/bin)
find "$PKG_ROOT" -path "*/bin/*" -type f -exec chmod 0755 {} \;
chmod 0755 "$PKG_ROOT/DEBIAN/postinst"
chmod 0755 "$PKG_ROOT/DEBIAN/postrm"

# ── 6b. Wrapper GDK_BACKEND=x11 e symlink minuscolo ──────────────────────────
# Fatto DOPO il passo permessi per evitare che chmod 0644 azzeri il wrapper.
# pip --prefix installa in usr/local/bin (non usr/bin) — cerchiamo ovunque.
echo "==> Creazione wrapper GDK_BACKEND=x11..."
REAL_BIN=$(find "$PKG_ROOT" -path "*/bin/SongpressPlusPlus" -not -name "*_bin" | head -n1)
echo "    Binario trovato: ${REAL_BIN:-(nessuno)}"

if [[ -n "$REAL_BIN" ]]; then
    BIN_DIR=$(dirname "$REAL_BIN")
    # Percorso assoluto di installazione (es. /usr/local/bin)
    INSTALLED_BIN_DIR="${BIN_DIR#$PKG_ROOT}"

    mv "$REAL_BIN" "${REAL_BIN}_bin"

    cat > "$REAL_BIN" <<WRAPPER
#!/bin/sh
# Wrapper: forza backend X11 per compatibilità wxPython/Wayland
export GDK_BACKEND=x11
exec ${INSTALLED_BIN_DIR}/SongpressPlusPlus_bin "\$@" 2>/dev/null
WRAPPER
    chmod 0755 "$REAL_BIN"
    chmod 0755 "${REAL_BIN}_bin"
    echo "    Wrapper creato: $REAL_BIN → ${INSTALLED_BIN_DIR}/SongpressPlusPlus_bin"

    # Symlink minuscolo: songpressplusplus → SongpressPlusPlus
    # Nota: chmod su symlink non è supportato, il target eredita i permessi
    ln -sf "${INSTALLED_BIN_DIR}/SongpressPlusPlus" "$BIN_DIR/songpressplusplus" || true
    echo "    Symlink creato: $BIN_DIR/songpressplusplus"
else
    echo "    [ATTENZIONE] Binario non trovato. Struttura bin:"
    find "$PKG_ROOT" -name "bin" -type d -exec ls -la {} \; || true
fi

# ── 7. Costruzione del .deb ───────────────────────────────────────────────────
DEB_FILE="$BUILD_DIR/${DEB_NAME}_${DEB_VERSION}_${DEB_ARCH}.deb"
echo "==> Costruzione del pacchetto .deb..."

if command -v fakeroot &>/dev/null; then
    fakeroot dpkg-deb --build "$PKG_ROOT" "$DEB_FILE"
else
    echo "    [ATTENZIONE] fakeroot non trovato."
    dpkg-deb --build "$PKG_ROOT" "$DEB_FILE"
fi

echo ""
echo "✅  Pacchetto creato: $DEB_FILE"
echo ""
echo "📦  Per installarlo:"
echo "   sudo dpkg -i \"$DEB_FILE\""
echo "   sudo apt-get install -f"
