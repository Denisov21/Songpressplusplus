#!/usr/bin/env bash
# =============================================================================
# build_appimage.sh — Costruisce l'AppImage per SongpressPlusPlus
#
# Uso:
#   chmod +x build_appimage.sh
#   ./build_appimage.sh            # interattivo
#   ./build_appimage.sh -y         # senza domande (CI)
#
# Prerequisiti sul sistema di BUILD:
#   - Python >= 3.12 con pip
#   - Un wxPython FUNZIONANTE già installato (su Debian/Ubuntu: python3-wxgtk4.0).
#     L'AppImage riusa QUEL wxPython, così evitiamo la compilazione da sorgente
#     (che pip farebbe: su Linux wxPython non ha wheel manylinux su PyPI).
#   - Connessione a Internet (scarica le dipendenze pure-Python da PyPI e gli
#     strumenti appimagetool/linuxdeploy/plugin-gtk da GitHub).
#   - ImageMagick (facoltativo, per ridimensionare l'icona .ico → .png).
#
# Cosa fa lo script:
#   1. Legge nome e versione dal pyproject.toml
#   2. Costruisce la wheel con pip (dai sorgenti già eventualmente patchati da
#      build_deb.sh: le due pipeline condividono l'albero src/)
#   3. Prepara un AppDir con interprete Python + stdlib IMPACCHETTATI (portabile)
#   4. Installa nell'AppDir: app + dipendenze pure-Python (PyPI) + wxPython (dal
#      sistema)
#   5. Scrive .desktop, icona hicolor, metainfo AppStream, tipo MIME ChordPro
#   6. Scarica (se mancano) appimagetool + linuxdeploy + linuxdeploy-plugin-gtk
#   7. Con linuxdeploy impacchetta le librerie native (GTK, wx, ...) e produce
#      il file .AppImage finale
#
# NOTA sulla portabilità: l'AppImage prodotto include Python, wxPython e le
# librerie GTK necessarie. Resta comunque legato alla ABI glibc della macchina
# di build: per la massima compatibilità conviene compilare sulla distro più
# vecchia che si vuole supportare.
# =============================================================================

set -euo pipefail

# ── Marcatori di stato ────────────────────────────────────────
# Stessa convenzione di build_deb.sh: colori ANSI solo se stdout è un terminale.
#   OK ✔ verde   WARN ⚠ giallo   ERR ✘ rosso   NET 🌐 ciano (operazione di rete)
if [[ -t 1 ]]; then
    OK=$'\e[1;32m✔\e[0m'
    WARN=$'\e[1;33m⚠\e[0m'
    ERR=$'\e[1;31m✘\e[0m'
    NET=$'\e[1;36m🌐\e[0m'
else
    OK='✔'; WARN='⚠'; ERR='✘'; NET='🌐'
fi
export OK WARN ERR NET

DONE='✅'; PKG='📦'
export DONE PKG

# ── Lingua dei messaggi ───────────────────────────────────────
# Inglese di base; italiano solo se il locale è italiano. Forzabile con
# SPP_BUILD_LANG=it|en. Identico a build_deb.sh.
case "${SPP_BUILD_LANG:-${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}}" in
    it | it_* | it.* | it_*.*) BUILD_LANG=it ;;
    *)                          BUILD_LANG=en ;;
esac
export BUILD_LANG

# bmsg ENGLISH ITALIAN → stampa la variante corretta (con newline).
bmsg() {
    if [ "$BUILD_LANG" = it ]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi
}

# ── Trappola di errore ────────────────────────────────────────
_on_err() {
    local rc=$?; local line=$1; local cmd=$2
    echo "" >&2
    bmsg "$ERR ERROR (exit $rc) at line $line of ${BASH_SOURCE[0]##*/}" \
         "$ERR ERRORE (exit $rc) alla riga $line di ${BASH_SOURCE[0]##*/}" >&2
    bmsg "$ERR    command: $cmd" "$ERR    comando: $cmd" >&2
    bmsg "$ERR    AppImage NOT created." "$ERR    AppImage NON creato." >&2
    exit "$rc"
}
trap '_on_err "$LINENO" "$BASH_COMMAND"' ERR

# ── Configurazione base ───────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"   # tutti i percorsi (pyproject.toml, src/, installer/) sono relativi

# Architettura: appimagetool/linuxdeploy hanno binari per x86_64 e aarch64.
ARCH="$(uname -m)"
export ARCH
case "$ARCH" in
    x86_64|aarch64) ;;
    *)
        bmsg "$ERR Unsupported architecture: $ARCH (only x86_64 / aarch64)." \
             "$ERR Architettura non supportata: $ARCH (solo x86_64 / aarch64)." >&2
        exit 1
        ;;
esac

# ── Conferma: serve la rete ───────────────────────────────────
ASSUME_YES="${SPP_ASSUME_YES:-0}"
for _arg in "$@"; do
    case "$_arg" in -y|--yes) ASSUME_YES=1 ;; esac
done

if [[ "$ASSUME_YES" != "1" ]]; then
    echo ""
    echo "=================================================================="
    bmsg "Songpress++ — AN INTERNET CONNECTION IS REQUIRED $NET" \
         "Songpress++ — È RICHIESTA UNA CONNESSIONE A INTERNET $NET"
    echo ""
    bmsg "Building the AppImage downloads:" \
         "La creazione dell'AppImage scarica:"
    bmsg "    - the pure-Python dependencies from PyPI (bundled inside)" \
         "    - le dipendenze pure-Python da PyPI (impacchettate dentro)"
    bmsg "    - appimagetool, linuxdeploy and the GTK plugin from GitHub" \
         "    - appimagetool, linuxdeploy e il plugin GTK da GitHub"
    echo "=================================================================="
    echo ""
    if [[ -t 0 ]]; then
        _prompt=$(bmsg "$NET Do you want to continue? [Y/N] " \
                       "$NET Vuoi continuare? [S/N] ")
        read -r -p "$_prompt" _risposta || _risposta=""
    else
        bmsg "$ERR stdin is not interactive and no -y/--yes given: aborting." \
             "$ERR stdin non interattivo e nessun -y/--yes: interrompo." >&2
        exit 1
    fi
    case "${_risposta,,}" in
        s|si|sì|y|yes) ;;
        *)
            bmsg "$ERR Operation cancelled by the user. AppImage NOT created." \
                 "$ERR Operazione annullata dall'utente. AppImage NON creato."
            exit 1
            ;;
    esac
    echo ""
fi

# ── Helper ImageMagick (magick su IM7, convert su IM6) ────────
if command -v magick &>/dev/null; then
    IM() { magick "$@"; }; HAVE_IM=1
elif command -v convert &>/dev/null; then
    IM() { convert "$@"; }; HAVE_IM=1
else
    IM() { return 1; }; HAVE_IM=0
fi

PYTHON="${VIRTUAL_ENV:+$VIRTUAL_ENV/bin/python3}"
PYTHON="${PYTHON:-python3}"

# ── Nome e versione dal pyproject.toml ────────────────────────
PKG_NAME=$("$PYTHON" - <<'PY'
import tomllib
with open("pyproject.toml", "rb") as f:
    print(tomllib.load(f)["project"]["name"])
PY
)
PKG_VERSION=$("$PYTHON" - <<'PY'
import tomllib
with open("pyproject.toml", "rb") as f:
    print(tomllib.load(f)["project"]["version"])
PY
)

APP_LOWER=$(echo "$PKG_NAME" | tr '[:upper:]' '[:lower:]' | tr '_' '-')
APP_VERSION="$PKG_VERSION"

# Identità applicazione (stessa di build_deb.sh)
APP_ID="io.github.denisov21.songpressplusplus"
AUTHOR_NAME="Denisov21"
LICENSE="GPL-2.0-only"
HOMEPAGE="https://github.com/Denisov21/Songpressplusplus"

# Nome del binario/entry-point come lo installa la wheel.
APP_BIN="SongpressPlusPlus"

# Dipendenze pure-Python da impacchettare nell'AppImage. wxPython NON è qui: lo
# copiamo dal sistema (vedi sotto). pywin32 è escluso (solo Windows).
# Gli import corrispondenti sono già coperti dalle wheel manylinux di PyPI.
PIP_BUNDLE=(
    requests
    reportlab
    markdown
    mistune
    pypdf
    python-pptx
    pyshortcuts
    pyenchant
)

# ── Cartelle di lavoro ────────────────────────────────────────
BUILD_DIR="$SCRIPT_DIR/build_appimage"
WHEEL_DIR="$BUILD_DIR/wheel"
APPDIR="$BUILD_DIR/${APP_BIN}.AppDir"
TOOLS_DIR="$BUILD_DIR/.tools"

# Versione di Python della macchina di build: definisce i percorsi stdlib.
PYVER=$("$PYTHON" -c 'import sys;print(f"{sys.version_info.major}.{sys.version_info.minor}")')
SITE_PKG="$APPDIR/usr/lib/python$PYVER/site-packages"

# ── Pulizia build precedente ──────────────────────────────────
bmsg "$OK Cleaning previous build..." "$OK Pulizia build precedente..."
rm -rf "$APPDIR" "$WHEEL_DIR"
rm -f  "$BUILD_DIR/"*.AppImage
mkdir -p "$WHEEL_DIR" "$APPDIR/usr/bin" "$APPDIR/usr/lib" "$TOOLS_DIR"

# ── 1. Costruzione della wheel ────────────────────────────────
# Nessuna patch qui: se vuoi le stesse correzioni del .deb (crash colour-picker,
# _mgr, Gtk-CRITICAL, tema scuro...) lancia PRIMA build_deb.sh, che patcha
# l'albero src/ in-place; questa wheel eredita quelle modifiche.
bmsg "$OK Building wheel with pip..." "$OK Costruzione wheel con pip..."
"$PYTHON" -m pip wheel --no-deps --wheel-dir "$WHEEL_DIR" "$SCRIPT_DIR"
WHEEL_FILE=$(ls "$WHEEL_DIR"/*.whl | head -n1)
echo "    Wheel: $WHEEL_FILE"

# ── 2. Interprete Python + stdlib IMPACCHETTATI ───────────────
# Copiamo l'interprete reale e l'intera libreria standard dentro l'AppDir: così
# l'AppImage non richiede alcun Python installato sulla macchina di destinazione.
bmsg "$OK Bundling the Python interpreter and stdlib (portable)..." \
     "$OK Impacchettamento interprete Python e stdlib (portabile)..."

REAL_PY=$(readlink -f "$("$PYTHON" -c 'import sys;print(sys.executable)')")
cp "$REAL_PY" "$APPDIR/usr/bin/python3"
ln -sf python3 "$APPDIR/usr/bin/python$PYVER"

# stdlib (contiene anche lib-dynload/ su Debian); NON copia dist-packages, che
# vive in /usr/lib/python3/dist-packages ed è roba di terze parti.
STDLIB_SRC=$("$PYTHON" -c 'import sysconfig;print(sysconfig.get_path("stdlib"))')
cp -a "$STDLIB_SRC" "$APPDIR/usr/lib/python$PYVER"
mkdir -p "$SITE_PKG"
# Byte-code e moduli pesanti/inutili della stdlib: via, alleggeriscono l'immagine.
find "$APPDIR/usr/lib/python$PYVER" -depth -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
rm -rf "$APPDIR/usr/lib/python$PYVER/test" \
       "$APPDIR/usr/lib/python$PYVER/idlelib" \
       "$APPDIR/usr/lib/python$PYVER/turtledemo" 2>/dev/null || true

# ── 3. App + dipendenze pure-Python ───────────────────────────
bmsg "$OK Installing app + PyPI dependencies into the AppDir..." \
     "$OK Installazione app + dipendenze PyPI nell'AppDir..."
# --target mette tutto, in piano, in site-packages: percorso deterministico,
# indipendente dallo schema "posix_local" di Debian.
"$PYTHON" -m pip install --no-deps --no-compile --target "$SITE_PKG" "$WHEEL_FILE"
"$PYTHON" -m pip install          --no-compile --target "$SITE_PKG" "${PIP_BUNDLE[@]}"

# ── 3b. wxPython dal sistema ──────────────────────────────────
# Copiamo il pacchetto wx già funzionante (niente compilazione da sorgente).
bmsg "$OK Copying system wxPython into the AppDir..." \
     "$OK Copia di wxPython di sistema nell'AppDir..."
WX_DIR=$("$PYTHON" -c 'import os,wx;print(os.path.dirname(wx.__file__))' 2>/dev/null || true)
if [[ -z "$WX_DIR" || ! -d "$WX_DIR" ]]; then
    bmsg "$ERR wxPython not found on this system." \
         "$ERR wxPython non trovato su questo sistema." >&2
    bmsg "$ERR    Install it first, e.g.: sudo apt install python3-wxgtk4.0" \
         "$ERR    Installalo prima, es.: sudo apt install python3-wxgtk4.0" >&2
    exit 1
fi
cp -a "$WX_DIR" "$SITE_PKG/"
# Metadati wxPython (facoltativi, per pip freeze dentro l'immagine)
WX_PARENT=$(dirname "$WX_DIR")
( shopt -s nullglob
  for meta in "$WX_PARENT"/wxPython-*.dist-info "$WX_PARENT"/wxPython-*.egg-info \
              "$WX_PARENT"/wxpython-*.dist-info; do
      cp -a "$meta" "$SITE_PKG/" 2>/dev/null || true
  done )
echo "    wxPython: $WX_DIR"

# ── 3c. Verifica dell'albero templates/ ───────────────────────
# Come nel .deb: se la wheel non ha portato le sottocartelle templates/*, le
# creiamo con un .keep, altrimenti "Nuovo da template" resta vuoto.
bmsg "$OK Checking templates/ tree..." "$OK Verifica albero templates/..."
PKG_DIR=$(find "$SITE_PKG" -type f -name "Globals.py" -printf '%h\n' 2>/dev/null | head -n1 || true)
TEMPLATE_SUBDIRS=(fonts local_dir slides songs themes)
if [[ -n "$PKG_DIR" ]]; then
    for SUB in "${TEMPLATE_SUBDIRS[@]}"; do
        if [[ ! -d "$PKG_DIR/templates/$SUB" ]]; then
            bmsg "$WARN templates/$SUB missing in the wheel: creating it." \
                 "$WARN templates/$SUB mancante nella wheel: la creo."
            mkdir -p "$PKG_DIR/templates/$SUB"
            printf '%s\n' "# Placeholder: keeps this directory inside the package." \
                > "$PKG_DIR/templates/$SUB/.keep"
        fi
    done
else
    bmsg "$WARN Package folder not found: skipping template check." \
         "$WARN Cartella del pacchetto non individuata: salto la verifica templates."
fi

# ── 4. Entry-point → launcher ─────────────────────────────────
# Leggiamo module:func dal console_scripts della dist-info dell'app e generiamo
# un piccolo launcher. Con --target pip non crea lo script bin/, quindi lo
# ricaviamo dai metadati.
bmsg "$OK Resolving the application entry-point..." \
     "$OK Individuazione entry-point dell'applicazione..."
EP_TARGET=$("$PYTHON" - "$SITE_PKG" "$PKG_NAME" <<'PY'
import sys, glob, os, configparser
sp, pkg = sys.argv[1], sys.argv[2].lower().replace("-", "").replace("_", "")
best = None
for ep in glob.glob(os.path.join(sp, "*.dist-info", "entry_points.txt")):
    cp = configparser.ConfigParser()
    try:
        cp.read(ep)
    except Exception:
        continue
    if not cp.has_section("console_scripts"):
        continue
    dist = os.path.basename(os.path.dirname(ep)).lower()
    for name, target in cp.items("console_scripts"):
        # Preferisci la dist-info dell'app stessa
        if dist.startswith(pkg):
            print(target.strip()); raise SystemExit
        if best is None:
            best = target.strip()
if best:
    print(best)
PY
)

if [[ -n "$EP_TARGET" && "$EP_TARGET" == *:* ]]; then
    EP_MODULE="${EP_TARGET%%:*}"
    EP_FUNC="${EP_TARGET##*:}"
else
    # Fallback ragionevole: modulo pacchetto con __main__
    EP_MODULE=$(echo "$PKG_NAME" | tr '[:upper:]' '[:lower:]' | tr '-' '_')
    EP_FUNC=""
    bmsg "$WARN No console_scripts entry-point found: falling back to 'python -m $EP_MODULE'." \
         "$WARN Nessun entry-point console_scripts: uso 'python -m $EP_MODULE'."
fi
echo "    Entry-point: ${EP_MODULE}${EP_FUNC:+:$EP_FUNC}"

cat > "$APPDIR/usr/bin/songpress-launch.py" <<LAUNCH
#!/usr/bin/env python3
# Launcher generato da build_appimage.sh
import sys
sys.argv[0] = "$APP_BIN"
LAUNCH
if [[ -n "$EP_FUNC" ]]; then
    cat >> "$APPDIR/usr/bin/songpress-launch.py" <<LAUNCH
from ${EP_MODULE} import ${EP_FUNC} as _main
sys.exit(_main())
LAUNCH
else
    cat >> "$APPDIR/usr/bin/songpress-launch.py" <<LAUNCH
import runpy
runpy.run_module("${EP_MODULE}", run_name="__main__", alter_sys=True)
LAUNCH
fi
chmod 0644 "$APPDIR/usr/bin/songpress-launch.py"

# ── 5. Icona, .desktop, MIME, metainfo ────────────────────────
bmsg "$OK Creating icon, .desktop, MIME and metainfo..." \
     "$OK Creazione icona, .desktop, MIME e metainfo..."

ICON_ICO="$SCRIPT_DIR/installer/songpressplusplus.ico"
ICON_PNG="$SCRIPT_DIR/installer/songpressplusplus.png"
mkdir -p "$APPDIR/usr/share/pixmaps"
TOP_ICON="$APPDIR/$APP_LOWER.png"   # appimagetool vuole l'icona anche in cima all'AppDir

if [[ -f "$ICON_PNG" ]]; then
    cp "$ICON_PNG" "$APPDIR/usr/share/pixmaps/$APP_LOWER.png"
elif [[ -f "$ICON_ICO" && "$HAVE_IM" -eq 1 ]]; then
    IM "${ICON_ICO}[0]" -resize 256x256 "$APPDIR/usr/share/pixmaps/$APP_LOWER.png" 2>/dev/null || \
    IM "$ICON_ICO"      -thumbnail 256x256 "$APPDIR/usr/share/pixmaps/$APP_LOWER.png" 2>/dev/null || true
    rm -f "$APPDIR/usr/share/pixmaps/$APP_LOWER-"*.png 2>/dev/null || true
fi

if [[ -f "$APPDIR/usr/share/pixmaps/$APP_LOWER.png" ]]; then
    cp "$APPDIR/usr/share/pixmaps/$APP_LOWER.png" "$TOP_ICON"
    for SIZE in 256 128 64 48; do
        DST="$APPDIR/usr/share/icons/hicolor/${SIZE}x${SIZE}/apps"
        mkdir -p "$DST"
        if [[ "$HAVE_IM" -eq 1 ]]; then
            IM "$APPDIR/usr/share/pixmaps/$APP_LOWER.png" -resize "${SIZE}x${SIZE}" \
               "$DST/$APP_LOWER.png" 2>/dev/null || cp "$APPDIR/usr/share/pixmaps/$APP_LOWER.png" "$DST/$APP_LOWER.png"
        else
            cp "$APPDIR/usr/share/pixmaps/$APP_LOWER.png" "$DST/$APP_LOWER.png"
        fi
    done
else
    bmsg "$WARN No icon found (installer/songpressplusplus.png|.ico): using a placeholder." \
         "$WARN Nessuna icona (installer/songpressplusplus.png|.ico): uso un segnaposto."
    # Segnaposto 256x256 così appimagetool non fallisce.
    if [[ "$HAVE_IM" -eq 1 ]]; then
        IM -size 256x256 xc:'#3465a4' "$TOP_ICON" 2>/dev/null || : > "$TOP_ICON"
    else
        : > "$TOP_ICON"
    fi
    mkdir -p "$APPDIR/usr/share/icons/hicolor/256x256/apps"
    cp "$TOP_ICON" "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP_LOWER.png" 2>/dev/null || true
fi

# Tipo MIME ChordPro (identico al .deb)
mkdir -p "$APPDIR/usr/share/mime/packages"
cat > "$APPDIR/usr/share/mime/packages/$APP_LOWER.xml" <<'MIME'
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

# .desktop — Exec=AppRun perché dentro l'AppImage è il punto d'ingresso.
# GDK_BACKEND lo forza l'AppRun, non serve ripeterlo qui.
mkdir -p "$APPDIR/usr/share/applications"
DESKTOP_FILE="$APPDIR/usr/share/applications/$APP_LOWER.desktop"
cat > "$DESKTOP_FILE" <<DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Songpress++
GenericName=Song Typesetter
Comment=Genera canzonieri di alta qualità in PDF e PPTX
Exec=AppRun %f
Icon=$APP_LOWER
Terminal=false
Categories=Office;Publishing;Education;
Keywords=song;chords;songbook;pdf;
MimeType=text/x-chordpro;
StartupNotify=true
DESKTOP
# Copia anche in cima all'AppDir (richiesto da appimagetool/linuxdeploy).
cp "$DESKTOP_FILE" "$APPDIR/$APP_LOWER.desktop"

# metainfo AppStream (identico al .deb)
mkdir -p "$APPDIR/usr/share/metainfo"
cat > "$APPDIR/usr/share/metainfo/${APP_ID}.metainfo.xml" <<METAINFO
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>${APP_ID}</id>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>${LICENSE}</project_license>
  <name>Songpress++</name>
  <developer id="io.github.denisov21">
    <name>${AUTHOR_NAME}</name>
  </developer>
  <summary>Song typesetting program that generates high-quality songbooks</summary>
  <description>
    <p>
      Songpress++ is a free, easy-to-use song typesetting program
      that generates high-quality songbooks in PDF and PPTX.
    </p>
  </description>
  <launchable type="desktop-id">${APP_LOWER}.desktop</launchable>
  <icon type="stock">${APP_LOWER}</icon>
  <url type="homepage">${HOMEPAGE}</url>
  <categories>
    <category>Office</category>
    <category>Publishing</category>
  </categories>
  <content_rating type="oars-1.1"/>
</component>
METAINFO

# ── 6. AppRun personalizzato ──────────────────────────────────
# Imposta l'ambiente Python impacchettato, sorgente gli hook dei plugin
# linuxdeploy (il plugin GTK registra qui pixbuf loaders, moduli GIO, temi...),
# forza X11 come nel wrapper del .deb e filtra lo stesso rumore GTK innocuo.
bmsg "$OK Writing custom AppRun..." "$OK Scrittura AppRun personalizzato..."
cat > "$APPDIR/AppRun" <<APPRUN
#!/bin/bash
HERE="\$(dirname "\$(readlink -f "\${0}")")"
export APPDIR="\${APPDIR:-\$HERE}"

# Hook dei plugin linuxdeploy (GTK ecc.). Vanno sorgenti PRIMA di lanciare.
if [ -d "\$APPDIR/apprun-hooks" ]; then
    for _hook in "\$APPDIR/apprun-hooks/"*.sh; do
        [ -e "\$_hook" ] && . "\$_hook"
    done
fi

# Python impacchettato
export PYTHONHOME="\$APPDIR/usr"
export PYTHONPATH="\$APPDIR/usr/lib/python$PYVER/site-packages\${PYTHONPATH:+:\$PYTHONPATH}"
export PYTHONDONTWRITEBYTECODE=1
export LD_LIBRARY_PATH="\$APPDIR/usr/lib\${LD_LIBRARY_PATH:+:\$LD_LIBRARY_PATH}"

# wxPython/Wayland: forza il backend X11 (XWayland). Dopo gli hook, così vince.
export GDK_BACKEND=x11

PYBIN="\$APPDIR/usr/bin/python3"
LAUNCH="\$APPDIR/usr/bin/songpress-launch.py"

# SONGPRESS_VERBOSE=1 → nessun filtro, tutto visibile (debug).
if [ -n "\${SONGPRESS_VERBOSE:-}" ]; then
    exec "\$PYBIN" "\$LAUNCH" "\$@"
fi

# Righe GTK innocue da scartare (stessa lista del wrapper .deb).
SPP_NOISE='gtk_image_menu_item_set_image'
SPP_NOISE="\$SPP_NOISE|invalid cast from .GtkMenuItem. to .GtkImageMenuItem."
SPP_NOISE="\$SPP_NOISE|ScreenToClient cannot work when toplevel window is not shown"
SPP_NOISE="\$SPP_NOISE|gtk_combo_box_text_insert"
SPP_NOISE="\$SPP_NOISE|for_size smaller than min-size"

exec 2> >(grep --line-buffered -v -E "\$SPP_NOISE" >&2)
exec "\$PYBIN" "\$LAUNCH" "\$@"
APPRUN
chmod 0755 "$APPDIR/AppRun"

# ── 7. Strumenti: appimagetool + linuxdeploy + plugin GTK ─────
# Gli AppImage degli strumenti girano senza FUSE grazie a EXTRACT_AND_RUN.
export APPIMAGE_EXTRACT_AND_RUN=1

fetch() { # fetch URL DEST
    local url="$1" dest="$2"
    [[ -f "$dest" ]] && return 0
    bmsg "$NET Downloading $(basename "$dest")..." \
         "$NET Scaricamento $(basename "$dest")..."
    if command -v curl &>/dev/null; then
        curl -fSL --retry 3 -o "$dest" "$url"
    elif command -v wget &>/dev/null; then
        wget -q -O "$dest" "$url"
    else
        bmsg "$ERR Neither curl nor wget available." \
             "$ERR Né curl né wget disponibili." >&2
        return 1
    fi
    chmod +x "$dest" 2>/dev/null || true
}

LD_BIN="$TOOLS_DIR/linuxdeploy-$ARCH.AppImage"
AT_BIN="$TOOLS_DIR/appimagetool-$ARCH.AppImage"
GTK_PLUGIN="$TOOLS_DIR/linuxdeploy-plugin-gtk.sh"

fetch "https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-$ARCH.AppImage" "$LD_BIN"
fetch "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-$ARCH.AppImage" "$AT_BIN"
fetch "https://raw.githubusercontent.com/linuxdeploy/linuxdeploy-plugin-gtk/master/linuxdeploy-plugin-gtk.sh" "$GTK_PLUGIN"
chmod +x "$LD_BIN" "$AT_BIN" "$GTK_PLUGIN"

# appimagetool e il plugin GTK devono stare nel PATH per linuxdeploy.
export PATH="$TOOLS_DIR:$PATH"
ln -sf "$AT_BIN" "$TOOLS_DIR/appimagetool" 2>/dev/null || true

# ── 8. Librerie native da impacchettare ───────────────────────
# I .so di wxPython e di enchant vengono caricati via dlopen da Python, quindi
# linuxdeploy non li scopre analizzando solo l'interprete: gli passiamo a mano,
# con -l, le librerie ESTERNE da cui dipendono (libwx_*, libgtk-3, ...).
# linuxdeploy applica poi la propria excludelist e sistema gli rpath.
bmsg "$OK Collecting native libraries needed by wxPython/enchant..." \
     "$OK Raccolta librerie native di wxPython/enchant..."
declare -A LIBSET
while read -r libpath; do
    [[ -n "$libpath" && -e "$libpath" ]] && LIBSET["$libpath"]=1
done < <(
    { for so in "$SITE_PKG/wx/"*.so "$SITE_PKG/wx/"*.so.*; do
          [[ -e "$so" ]] && ldd "$so" 2>/dev/null
      done
    } | awk '/=>/ && $3 ~ /^\// {print $3}' | sort -u
)
# libenchant è aperta per nome da pyenchant: aggiungila se presente.
if command -v ldconfig &>/dev/null; then
    while read -r p; do
        [[ -e "$p" ]] && LIBSET["$p"]=1
    done < <(ldconfig -p 2>/dev/null | awk '/libenchant-2\.so/{print $NF}')
fi

LD_LIB_ARGS=()
for lib in "${!LIBSET[@]}"; do
    LD_LIB_ARGS+=( -l "$lib" )
done
echo "    ${#LIBSET[@]} $(bmsg 'external libraries queued' 'librerie esterne in coda')"

# ── 9. linuxdeploy → .AppImage ────────────────────────────────
bmsg "$OK Bundling native libraries and building the AppImage..." \
     "$OK Impacchettamento librerie native e creazione AppImage..."

export OUTPUT="${APP_BIN}-${APP_VERSION}-${ARCH}.AppImage"
export VERSION="$APP_VERSION"
export DEPLOY_GTK_VERSION=3   # wxPython usa GTK3

# --custom-apprun: usa il NOSTRO AppRun (imposta PYTHONHOME e sorgente gli hook).
"$LD_BIN" \
    --appdir "$APPDIR" \
    --executable "$APPDIR/usr/bin/python3" \
    --desktop-file "$APPDIR/$APP_LOWER.desktop" \
    --icon-file "$APPDIR/$APP_LOWER.png" \
    --custom-apprun "$APPDIR/AppRun" \
    "${LD_LIB_ARGS[@]}" \
    --plugin gtk \
    --output appimage

# linuxdeploy scrive l'AppImage nella cwd (SCRIPT_DIR). Spostiamolo in build.
if [[ -f "$SCRIPT_DIR/$OUTPUT" ]]; then
    mv -f "$SCRIPT_DIR/$OUTPUT" "$BUILD_DIR/$OUTPUT"
fi
APPIMAGE_PATH="$BUILD_DIR/$OUTPUT"

# Fallback: se per qualsiasi motivo il nome differisce, prendi l'ultimo prodotto.
if [[ ! -f "$APPIMAGE_PATH" ]]; then
    APPIMAGE_PATH=$(ls -t "$BUILD_DIR"/*.AppImage "$SCRIPT_DIR"/*.AppImage 2>/dev/null | head -n1 || true)
fi

echo ""
if [[ -n "${APPIMAGE_PATH:-}" && -f "$APPIMAGE_PATH" ]]; then
    chmod +x "$APPIMAGE_PATH"
    bmsg "$DONE  AppImage created: $APPIMAGE_PATH" \
         "$DONE  AppImage creato: $APPIMAGE_PATH"
    echo ""
    bmsg "$PKG  To run it:" "$PKG  Per eseguirlo:"
    echo "   chmod +x \"$APPIMAGE_PATH\""
    echo "   \"$APPIMAGE_PATH\""
    echo ""
    bmsg "$PKG  Debug (show all GTK/wx messages):" \
         "$PKG  Debug (mostra tutti i messaggi GTK/wx):"
    echo "   SONGPRESS_VERBOSE=1 \"$APPIMAGE_PATH\""
else
    bmsg "$ERR AppImage not found after build." \
         "$ERR AppImage non trovato dopo la build." >&2
    exit 1
fi
