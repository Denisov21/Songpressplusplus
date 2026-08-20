#!/usr/bin/env bash
# =============================================================================
# build_rpm.sh — Costruisce il pacchetto .rpm per SongpressPlusPlus
#
# Gemello di build_deb.sh: STESSA logica di patch del sorgente, STESSA wheel,
# STESSO albero di file (.desktop, icone, MIME, AppStream, wrapper). Cambia solo
# l'ULTIMA fase: invece di DEBIAN/control + dpkg-deb si genera un file .spec e
# si chiama rpmbuild. I maintainer script Debian (postinst/postrm) diventano
# gli scriptlet RPM %post / %postun.
#
# Uso:
#   chmod +x build_rpm.sh
#   ./build_rpm.sh
#
# Prerequisiti sul sistema (Fedora/RHEL/openSUSE/Mageia...):
#   - Python >= 3.12
#   - pip
#   - rpm-build       (fornisce rpmbuild)      → Fedora: dnf install rpm-build
#                                                openSUSE: zypper install rpm-build
#   - ImageMagick     (facoltativo, per l'icona da .ico)
#
# NOTA SUI NOMI DEI PACCHETTI RUNTIME (Requires/Recommends piu' sotto):
#   lo script RILEVA la famiglia della distro da /etc/os-release e sceglie i
#   nomi giusti per Fedora/RHEL oppure openSUSE/SLE. Forzabile con
#   SPP_DISTRO=fedora|suse. Con --check-deps (o SPP_CHECK_DEPS=1) verifica i
#   nomi contro il gestore pacchetti locale prima di costruire (non bloccante).
#   I nomi openSUSE, in particolare, andrebbero confermati con "zypper se".
#
# NOTA SU noarch + versione di Python:
#   il pacchetto e' "noarch" (puro Python) ma i moduli finiscono in
#   /usr/lib/pythonX.Y/site-packages, dove X.Y e' la versione di Python del
#   sistema su cui GIRA questo script. Installa l'rpm su una macchina con la
#   stessa minor version di Python usata per costruirlo (come da convenzione
#   Fedora, dove ogni release ha un solo python3).
# =============================================================================

set -euo pipefail

# ── Marcatori di stato ────────────────────────────────────────
# Se stdout è un terminale usa i colori ANSI, altrimenti solo il carattere.
#   OK   ✔ verde   passo completato
#   WARN ⚠ giallo  problema NON bloccante (il build prosegue)
#   ERR  ✘ rosso   errore: lo script si ferma
#   NET  🌐 ciano  operazione che richiede la rete (download da PyPI, ecc.)
# Esportati perché li rileggono anche gli heredoc Python.
if [[ -t 1 ]]; then
    OK=$'\e[1;32m✔\e[0m'
    WARN=$'\e[1;33m⚠\e[0m'
    ERR=$'\e[1;31m✘\e[0m'
    NET=$'\e[1;36m🌐\e[0m'
else
    OK='✔'
    WARN='⚠'
    ERR='✘'
    NET='🌐'
fi
export OK WARN ERR NET

# ── Icone di sezione ──────────────────────────────────────────
# NON sono livelli di stato come OK/WARN/ERR/NET: sono icone decorative usate
# solo nel riepilogo conclusivo. Essendo emoji già a colori non hanno ANSI.
DONE='✅'
PKG='📦'
export DONE PKG

# ── Lingua dei messaggi di build ──────────────────────────────
# Inglese come lingua base; italiano SOLO se il locale di sistema è italiano.
# Stessa logica del %post, così i messaggi di creazione del .rpm e quelli
# di installazione parlano la stessa lingua. Forzabile con SPP_BUILD_LANG=it|en.
case "${SPP_BUILD_LANG:-${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}}" in
    it | it_* | it.* | it_*.*) BUILD_LANG=it ;;
    *)                          BUILD_LANG=en ;;
esac
export BUILD_LANG

# bmsg ENGLISH_STRING ITALIAN_STRING → stampa la variante corretta (con newline).
# Per i messaggi solo verso stderr si usa: bmsg "en" "it" >&2
bmsg() {
    if [ "$BUILD_LANG" = it ]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi
}

# ── Trappola di errore ────────────────────────────────────────
# Con "set -e" lo script muore in silenzio alla prima riga fallita: si vedrebbe
# solo l'ultimo ✔ e nessuna spiegazione. Il trap stampa riga e comando colpevoli
# in rosso su stderr, poi propaga il codice di uscita originale.
_on_err() {
    local rc=$?
    local line=$1
    local cmd=$2
    echo "" >&2
    bmsg "$ERR ERROR (exit $rc) at line $line of ${BASH_SOURCE[0]##*/}" \
         "$ERR ERRORE (exit $rc) alla riga $line di ${BASH_SOURCE[0]##*/}" >&2
    bmsg "$ERR    command: $cmd" \
         "$ERR    comando: $cmd" >&2
    bmsg "$ERR    package NOT created." \
         "$ERR    pacchetto NON creato." >&2
    exit "$rc"
}
trap '_on_err "$LINENO" "$BASH_COMMAND"' ERR

# ── Configurazione ────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Come in build_deb.sh: tutto il resto (lettura pyproject.toml, find su
# src/songpressplusplus nelle patch) usa percorsi RELATIVI. Senza questo cd lo
# script funziona solo se lanciato dalla propria cartella.
cd "$SCRIPT_DIR"

# ── Prerequisito: rpmbuild ────────────────────────────────────────────────────
if ! command -v rpmbuild &>/dev/null; then
    bmsg "$ERR 'rpmbuild' not found. Install it:  (Fedora) sudo dnf install rpm-build  |  (openSUSE) sudo zypper install rpm-build" \
         "$ERR 'rpmbuild' non trovato. Installalo:  (Fedora) sudo dnf install rpm-build  |  (openSUSE) sudo zypper install rpm-build" >&2
    exit 1
fi

# ── Conferma: serve una connessione a Internet ────────────────────────────────
# Il pacchetto prodotto, durante l'installazione (%post), scarica via pip le
# dipendenze non presenti nei repository (python-pptx, pyshortcuts). Avvisiamo
# l'utente PRIMA di iniziare, così può annullare senza aver toccato nulla.
#   - Con -y / --yes (o SPP_ASSUME_YES=1) la domanda viene saltata: utile in CI.
#   - Se stdin non è un terminale e manca -y, meglio fermarsi che proseguire alla cieca.
ASSUME_YES="${SPP_ASSUME_YES:-0}"
for _arg in "$@"; do
    case "$_arg" in
        -y|--yes) ASSUME_YES=1 ;;
    esac
done

if [[ "$ASSUME_YES" != "1" ]]; then
    echo ""
    echo "=================================================================="
    bmsg "Songpress++ — AN INTERNET CONNECTION IS REQUIRED $NET" \
         "Songpress++ — È RICHIESTA UNA CONNESSIONE A INTERNET $NET"
    echo ""
    bmsg "Building the .rpm package requires an Internet connection." \
         "La creazione del pacchetto .rpm richiede una connessione a Internet."
    bmsg "    pip downloads from PyPI the components needed to build the wheel" \
         "    pip scarica da PyPI i componenti necessari a costruire la wheel"
    bmsg "    (hatchling and the build dependencies)." \
         "    (hatchling e le dipendenze di build)."
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
        s|si|sì|y|yes) ;;                 # S, s, Si, sì / Y, y, Yes
        *)
            bmsg "$ERR Operation cancelled by the user. Package NOT created." \
                 "$ERR Operazione annullata dall'utente. Pacchetto NON creato."
            exit 1
            ;;
    esac
    echo ""
fi

# ── Helper ImageMagick ────────────────────────────────────────────────────────
# Su ImageMagick 7 il comando "convert" non esiste più: si usa "magick".
# Qui rileviamo una volta sola quale è presente.
if command -v magick &>/dev/null; then
    IM() { magick "$@"; }
    HAVE_IM=1
elif command -v convert &>/dev/null; then
    IM() { convert "$@"; }
    HAVE_IM=1
else
    IM() { return 1; }
    HAVE_IM=0
fi

# Legge versione e nome da pyproject.toml
PKG_NAME=$(python3 - <<'PY'
import os as _os
_W = _os.environ.get("WARN", "!")   # marcatore avviso ereditato da build_rpm.sh
import tomllib
with open("pyproject.toml", "rb") as f:
    d = tomllib.load(f)
print(d["project"]["name"])
PY
)
PKG_VERSION=$(python3 - <<'PY'
import os as _os
_W = _os.environ.get("WARN", "!")   # marcatore avviso ereditato da build_rpm.sh
import tomllib
with open("pyproject.toml", "rb") as f:
    d = tomllib.load(f)
print(d["project"]["version"])
PY
)

# Nome del pacchetto rpm: tutto minuscolo, trattini al posto di trattini bassi
RPM_NAME=$(echo "$PKG_NAME" | tr '[:upper:]' '[:lower:]' | tr '_' '-')

# Version RPM: il campo Version NON può contenere '-' (separa Version da Release
# in RPM). Se la versione upstream ha un '-' (es. pre-release "1.0-rc1") lo
# convertiamo in '~', che RPM ordina PRIMA della release finale.
RPM_VERSION=$(echo "$PKG_VERSION" | tr '-' '~')
RPM_RELEASE="1"
RPM_ARCH="noarch"     # puro Python → indipendente dall'architettura

# ID applicazione AppStream in formato reverse-DNS (vedi note in build_deb.sh).
# Il file metainfo DEVE chiamarsi "<APP_ID>.metainfo.xml".
APP_ID="io.github.denisov21.songpressplusplus"
MAINTAINER="Denisov21 <Denisov21@users.noreply.github.com>"
AUTHOR_NAME="Denisov21"
# Licenza in formato SPDX.
LICENSE="GPL-2.0-only"
SUMMARY="Song typesetting program that generates high-quality songbooks (PDF, PPTX)"
HOMEPAGE="https://github.com/Denisov21/Songpressplusplus"

# ── Rilevamento della distribuzione ───────────────────────────────────────────
# I nomi dei pacchetti runtime differiscono tra Fedora/RHEL e openSUSE/SLE:
# rileviamo la famiglia da /etc/os-release e scegliamo il set giusto.
# Forzabile con SPP_DISTRO=fedora|suse (utile per costruire "cross" o in CI).
#
#   ID / ID_LIKE tipici:
#     Fedora            ID=fedora
#     RHEL/Rocky/Alma   ID=rhel|rocky|almalinux   ID_LIKE="...fedora"
#     openSUSE Leap     ID=opensuse-leap          ID_LIKE="suse opensuse"
#     openSUSE TW       ID=opensuse-tumbleweed     ID_LIKE="suse opensuse"
#     SLES              ID=sles                    ID_LIKE="suse"
detect_distro() {
    # 1) override esplicito
    case "${SPP_DISTRO:-}" in
        fedora|rhel|redhat) echo fedora; return ;;
        suse|opensuse|sles) echo suse;   return ;;
    esac
    # 2) da /etc/os-release
    local ID="" ID_LIKE=""
    if [ -r /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
    fi
    case " ${ID} ${ID_LIKE} " in
        *" suse "*|*opensuse*|*sles*) echo suse ;;
        *" fedora "*|*" rhel "*|*fedora*|*rhel*|*centos*|*rocky*|*almalinux*) echo fedora ;;
        *) echo unknown ;;
    esac
}
DISTRO=$(detect_distro)
if [ "$DISTRO" = unknown ]; then
    bmsg "$WARN Distro not recognised: assuming Fedora names. Override with SPP_DISTRO=fedora|suse." \
         "$WARN Distro non riconosciuta: uso i nomi Fedora. Forza con SPP_DISTRO=fedora|suse." >&2
    DISTRO=fedora
fi
bmsg "$OK Detected distribution family: $DISTRO" \
     "$OK Famiglia distribuzione rilevata: $DISTRO"

# ── Dipendenze runtime per famiglia ───────────────────────────────────────────
# Ogni voce è una riga "Requires:"/"Recommends:" che finirà nel .spec.
# La dipendenza su wxPython usa una "rich dependency" (RPM >= 4.13): accetta uno
# qualsiasi dei pacchetti elencati; se il tuo rpm è più vecchio, lasciane uno solo.
#
# ATTENZIONE: i nomi openSUSE sono i più soggetti a variazioni tra Leap e
# Tumbleweed. Prima di distribuire, verificali sul sistema reale con:
#     zypper se -s python3-... ;  oppure lancia questo script con --check-deps
if [ "$DISTRO" = suse ]; then
    # ── openSUSE / SLE ────────────────────────────────────────────────────────
    # Differenze note rispetto a Fedora:
    #   markdown → python3-Markdown (openSUSE conserva la maiuscola PyPI)
    #   enchant  → python3-pyenchant
    #   wxPython → python3-wxPython
    #   dizionari hunspell forniti dai pacchetti myspell-<locale>
    REQUIRES=$(cat <<'REQ'
Requires:       python3 >= 3.12
Requires:       python3-pip
Requires:       (python3-wxPython or python3-wxWidgets)
Requires:       python3-requests
Requires:       python3-reportlab
Requires:       python3-Markdown
Requires:       python3-mistune
Requires:       python3-pypdf
Requires:       python3-pyenchant
Requires:       xdg-utils
Requires:       bash
REQ
)
    RECOMMENDS=$(cat <<'REC'
Recommends:     wl-clipboard
Recommends:     myspell-it_IT
Recommends:     myspell-en_US
REC
)
else
    # ── Fedora / RHEL / Rocky / Alma ──────────────────────────────────────────
    REQUIRES=$(cat <<'REQ'
Requires:       python3 >= 3.12
Requires:       python3-pip
Requires:       (python3-wxpython4 or python3-wxGTK)
Requires:       python3-requests
Requires:       python3-reportlab
Requires:       python3-markdown
Requires:       python3-mistune
Requires:       python3-pypdf
Requires:       python3-enchant
Requires:       xdg-utils
Requires:       bash
REQ
)
    RECOMMENDS=$(cat <<'REC'
Recommends:     wl-clipboard
Recommends:     hunspell-it
Recommends:     hunspell-en
REC
)
fi

# ── (Opzionale) verifica dei nomi contro il gestore pacchetti locale ──────────
# Attivabile con --check-deps o SPP_CHECK_DEPS=1. NON bloccante: segnala solo i
# nomi che il gestore pacchetti non riesce a risolvere, così puoi correggerli
# PRIMA di distribuire. Richiede i repo configurati (e di norma la rete).
CHECK_DEPS="${SPP_CHECK_DEPS:-0}"
for _arg in "$@"; do
    case "$_arg" in --check-deps) CHECK_DEPS=1 ;; esac
done
if [ "$CHECK_DEPS" = 1 ]; then
    bmsg "$NET Verifying dependency names against the local package manager..." \
         "$NET Verifica dei nomi delle dipendenze col gestore pacchetti locale..."
    # Estrae il nome nudo del pacchetto da una riga Requires/Recommends,
    # scartando il vincolo di versione e le rich-deps fra parentesi.
    _dep_names() {
        printf '%s\n%s\n' "$REQUIRES" "$RECOMMENDS" \
        | sed -E 's/^(Requires|Recommends):[[:space:]]*//' \
        | tr '()' '  ' | sed -E 's/[[:space:]]+or[[:space:]]+/\n/g' \
        | awk '{print $1}' | sort -u | grep -v '^$'
    }
    _resolves() {  # $1 = nome pacchetto → 0 se risolvibile
        if command -v dnf >/dev/null 2>&1; then
            dnf -q --cacheonly repoquery --whatprovides "$1" >/dev/null 2>&1 \
              || dnf -q repoquery "$1" >/dev/null 2>&1
        elif command -v zypper >/dev/null 2>&1; then
            zypper -q se -x -t package "$1" >/dev/null 2>&1
        elif command -v rpm >/dev/null 2>&1; then
            rpm -q --whatprovides "$1" >/dev/null 2>&1
        else
            return 2   # nessun gestore disponibile
        fi
    }
    _missing=0
    while IFS= read -r _d; do
        [ -z "$_d" ] && continue
        if _resolves "$_d"; then
            bmsg "  $OK $_d" "  $OK $_d"
        else
            _rc=$?
            if [ "$_rc" = 2 ]; then
                bmsg "$WARN No package manager to verify names (skipping)." \
                     "$WARN Nessun gestore pacchetti per verificare i nomi (salto)." >&2
                break
            fi
            bmsg "  $WARN $_d — NOT found: adjust the name for this distro." \
                 "  $WARN $_d — NON trovato: correggi il nome per questa distro." >&2
            _missing=1
        fi
    done <<< "$(_dep_names)"
    [ "$_missing" = 1 ] && bmsg \
        "$WARN Some names did not resolve (build continues; the .rpm may be uninstallable as-is)." \
        "$WARN Alcuni nomi non risolti (il build prosegue; l'.rpm potrebbe non installarsi così com'è)." >&2
fi

# Dipendenze che NON esistono nei repo: si installano via pip nel %post.
# Formato: "nome_pip:nome_modulo_import" (uno per riga).
#   - python-pptx  → modulo "pptx"
#   - pyshortcuts  → modulo "pyshortcuts"
# NB: pywin32 è escluso di proposito, è solo per Windows.
PIP_DEPS="python-pptx:pptx
pyshortcuts:pyshortcuts"

# ── Cartelle di lavoro ────────────────────────────────────────────────────────
BUILD_DIR="$SCRIPT_DIR/build_rpm"
# TREE è la radice dell'albero da impacchettare: contiene ./usr/...  Verrà
# copiato nel %{buildroot} dallo spec (fase %install).
TREE="$BUILD_DIR/tree"
INSTALL_PREFIX="$TREE/usr"
RPMBUILD_TOP="$BUILD_DIR/rpmbuild"     # _topdir isolato, così non tocchiamo ~/rpmbuild
SPEC_FILE="$BUILD_DIR/${RPM_NAME}.spec"
FILES_LIST="$BUILD_DIR/files.list"

# ── Pulizia precedente build ──────────────────────────────────────────────────
bmsg "$OK Cleaning previous build..." \
     "$OK Pulizia build precedente..."
mkdir -p "$BUILD_DIR"
# Pulizia MIRATA: come in build_deb.sh non si cancella l'intera cartella
# build_rpm/ (può contenere documentazione versionata), solo gli artefatti.
rm -rf "$TREE"
rm -rf "$RPMBUILD_TOP"
rm -rf "$BUILD_DIR/wheel"
rm -f  "$BUILD_DIR/"*.rpm
rm -f  "$SPEC_FILE" "$FILES_LIST"

PYTHON="${VIRTUAL_ENV:+$VIRTUAL_ENV/bin/python3}"
PYTHON="${PYTHON:-python3}"

# =============================================================================
# DA QUI FINO ALLA COSTRUZIONE DELLA WHEEL: identico a build_deb.sh.
# Le patch operano sul sorgente Python e NON dipendono dalla distribuzione.
# =============================================================================

# ── 1b. Patch SongpressFrame.py: SetForegroundColour nella finestra About ────
bmsg "$OK Patch SetForegroundColour About window..." \
     "$OK Patch SetForegroundColour finestra About..."
"$PYTHON" - <<'PATCH'
import os as _os
_W = _os.environ.get("WARN", "!")
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
    print(f"{_W} SongpressFrame.py non trovato, skip patch.")
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

# ── 1e. Patch SongpressFrame.py: Statistiche brano tema scuro ────────────────
bmsg "$OK Patch Song statistics (system BG, stars+verdict, dark-theme text)..." \
     "$OK Patch Statistiche brano (BG sistema, stelle+verdetto, testo tema scuro)..."
"$PYTHON" - <<'PATCH_STATS'
import os as _os
_W = _os.environ.get("WARN", "!")
import re, subprocess, sys

result = subprocess.run(
    ["find", "src/songpressplusplus", "-name", "SongpressFrame.py"],
    capture_output=True, text=True
)
candidates = result.stdout.strip().splitlines()
if not candidates:
    print(f"{_W} SongpressFrame.py non trovato, skip patch.")
    sys.exit(0)

path = candidates[0]
with open(path, encoding='utf-8') as f:
    content = f.read()

FG = "wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT)"
fixes = []

# 1. BG hardcoded → colore di sistema
fixes.append((
    'BG      = wx.Colour(250, 250, 252)',
    'BG      = wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW)'
))

# 2. eval_panel caso multi-tab → sizer diretto su page, senza pannello bianco
fixes.append((
    "                    eval_panel = wx.Panel(page)\n"
    "                    eval_panel.SetBackgroundColour(wx.Colour(240, 245, 255))\n"
    "                    eval_sz = wx.BoxSizer(wx.HORIZONTAL)\n"
    "                    lbl_stars = wx.StaticText(eval_panel, label=st['stars'])\n"
    "                    f_s = lbl_stars.GetFont()\n"
    "                    f_s.SetPointSize(f_s.GetPointSize() + 6)\n"
    "                    lbl_stars.SetFont(f_s)\n"
    "                    lbl_stars.SetForegroundColour(STAR_ON)\n"
    "                    lbl_verdict = wx.StaticText(eval_panel, label='  ' + st['verdict'])\n"
    "                    f_v = lbl_verdict.GetFont()\n"
    "                    f_v.SetWeight(wx.FONTWEIGHT_BOLD)\n"
    "                    lbl_verdict.SetFont(f_v)\n"
    "                    eval_sz.Add(lbl_stars,   0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)\n"
    "                    eval_sz.Add(lbl_verdict, 0, wx.ALIGN_CENTER_VERTICAL)\n"
    "                    eval_panel.SetSizer(eval_sz)\n"
    "                    body.Add(eval_panel, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 6)",
    "                    _eval_sz = wx.BoxSizer(wx.HORIZONTAL)\n"
    "                    _lbl_stars = wx.StaticText(page, label=st['stars'])\n"
    "                    _fs = _lbl_stars.GetFont()\n"
    "                    _fs.SetPointSize(_fs.GetPointSize() + 6)\n"
    "                    _lbl_stars.SetFont(_fs)\n"
    "                    _lbl_stars.SetForegroundColour(STAR_ON)\n"
    "                    _lbl_verdict = wx.StaticText(page, label='  ' + st['verdict'])\n"
    "                    _fv = _lbl_verdict.GetFont()\n"
    "                    _fv.SetWeight(wx.FONTWEIGHT_BOLD)\n"
    "                    _lbl_verdict.SetFont(_fv)\n"
    f"                    _lbl_verdict.SetForegroundColour({FG})\n"
    "                    _eval_sz.Add(_lbl_stars,   0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)\n"
    "                    _eval_sz.Add(_lbl_verdict, 0, wx.ALIGN_CENTER_VERTICAL)\n"
    "                    body.Add(_eval_sz, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 6)"
))

# 3. eval_panel caso singolo brano → sizer diretto su scroll
fixes.append((
    "            eval_panel = wx.Panel(scroll)\n"
    "            eval_panel.SetBackgroundColour(wx.Colour(240, 245, 255))\n"
    "            eval_sz = wx.BoxSizer(wx.HORIZONTAL)\n"
    "            lbl_stars = wx.StaticText(eval_panel, label=st['stars'])\n"
    "            f_s = lbl_stars.GetFont()\n"
    "            f_s.SetPointSize(f_s.GetPointSize() + 6)\n"
    "            lbl_stars.SetFont(f_s)\n"
    "            lbl_stars.SetForegroundColour(STAR_ON)\n"
    "            lbl_verdict = wx.StaticText(eval_panel, label='  ' + st['verdict'])\n"
    "            f_v = lbl_verdict.GetFont()\n"
    "            f_v.SetWeight(wx.FONTWEIGHT_BOLD)\n"
    "            lbl_verdict.SetFont(f_v)\n"
    "            eval_sz.Add(lbl_stars,   0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)\n"
    "            eval_sz.Add(lbl_verdict, 0, wx.ALIGN_CENTER_VERTICAL)\n"
    "            eval_panel.SetSizer(eval_sz)\n"
    "            body.Add(eval_panel, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 6)",
    "            _eval_sz = wx.BoxSizer(wx.HORIZONTAL)\n"
    "            _lbl_stars = wx.StaticText(scroll, label=st['stars'])\n"
    "            _fs = _lbl_stars.GetFont()\n"
    "            _fs.SetPointSize(_fs.GetPointSize() + 6)\n"
    "            _lbl_stars.SetFont(_fs)\n"
    "            _lbl_stars.SetForegroundColour(STAR_ON)\n"
    "            _lbl_verdict = wx.StaticText(scroll, label='  ' + st['verdict'])\n"
    "            _fv = _lbl_verdict.GetFont()\n"
    "            _fv.SetWeight(wx.FONTWEIGHT_BOLD)\n"
    "            _lbl_verdict.SetFont(_fv)\n"
    f"            _lbl_verdict.SetForegroundColour({FG})\n"
    "            _eval_sz.Add(_lbl_stars,   0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 12)\n"
    "            _eval_sz.Add(_lbl_verdict, 0, wx.ALIGN_CENTER_VERTICAL)\n"
    "            body.Add(_eval_sz, 0, wx.LEFT | wx.TOP | wx.BOTTOM, 6)"
))

# 4. Testo _row multi-tab → SYS_COLOUR_WINDOWTEXT
fixes.append((
    "                    k_lbl = wx.StaticText(_page, label=key)\n"
    "                    v_lbl = wx.StaticText(_page, label=str(value))",
    "                    k_lbl = wx.StaticText(_page, label=key)\n"
    f"                    k_lbl.SetForegroundColour({FG})\n"
    "                    v_lbl = wx.StaticText(_page, label=str(value))\n"
    f"                    v_lbl.SetForegroundColour({FG})"
))

# 5. Testo _row singolo brano → SYS_COLOUR_WINDOWTEXT
fixes.append((
    "            k_lbl = wx.StaticText(scroll, label=key)\n"
    "            v_lbl = wx.StaticText(scroll, label=str(value))",
    "            k_lbl = wx.StaticText(scroll, label=key)\n"
    f"            k_lbl.SetForegroundColour({FG})\n"
    "            v_lbl = wx.StaticText(scroll, label=str(value))\n"
    f"            v_lbl.SetForegroundColour({FG})"
))

# 6. Rimuovi gauge rimasti
lines = content.splitlines(keepends=True)
lines = [l for l in lines if not re.search(
    r'gauge\s*=\s*wx\.Gauge|gauge\.SetValue|body\.Add\(gauge', l)]
content = ''.join(lines)

count = sum(1 for old, _ in fixes if old in content)
for old, new in fixes:
    content = content.replace(old, new)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"    Patch 1e: {count}/{len(fixes)} fix applicati in {path}")
PATCH_STATS

# ── 1c. Patch PreferencesDialog.py: disabilita pulsanti assoc su Linux ───────
bmsg "$OK Patch file-association buttons (Linux)..." \
     "$OK Patch pulsanti associazione file (Linux)..."
"$PYTHON" - <<'PATCH2'
import os as _os
_W = _os.environ.get("WARN", "!")
import subprocess, sys

result = subprocess.run(
    ["find", "src/songpressplusplus", "-name", "PreferencesDialog.py"],
    capture_output=True, text=True
)
candidates = result.stdout.strip().splitlines()
if not candidates:
    print(f"{_W} PreferencesDialog.py non trovato, skip patch.")
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
bmsg "$OK Patch colour-picker crash (IsOk)..." \
     "$OK Patch crash colore selettore (IsOk)..."
"$PYTHON" - <<'PATCH3'
import os as _os
_W = _os.environ.get("WARN", "!")
import subprocess, sys

result = subprocess.run(
    ["find", "src/songpressplusplus", "-name", "MyPreferencesDialog.py"],
    capture_output=True, text=True
)
candidates = result.stdout.strip().splitlines()
if not candidates:
    print(f"{_W} MyPreferencesDialog.py non trovato, skip patch.")
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
    print(f"{_W} Patch già presente o testo non trovato in {path}")
PATCH3

# ── 1f. Patch crash _mgr al cambio lingua / chiusura ─────────────────────────
bmsg "$OK Patch _mgr crash (language switch / teardown)..." \
     "$OK Patch crash _mgr (cambio lingua / teardown)..."
"$PYTHON" - <<'PATCH1F'
import os as _os
_W = _os.environ.get("WARN", "!")
import subprocess, sys

def find(name):
    r = subprocess.run(["find", "src/songpressplusplus", "-name", name],
                       capture_output=True, text=True)
    c = r.stdout.strip().splitlines()
    return c[0] if c else None

fr = find("SongpressFrame.py")
tb = find("SongpressToolbars.py")
if not fr or not tb:
    print(f"{_W} File non trovati, skip patch 1f.")
    sys.exit(0)

with open(fr) as f: frc = f.read()
with open(tb) as f: tbc = f.read()

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
for old, new in ((old_a, new_a), (old_b, new_b)):
    if old in frc:
        frc = frc.replace(old, new); count += 1
if old_c in tbc:
    tbc = tbc.replace(old_c, new_c); count += 1

with open(fr, "w") as f: f.write(frc)
with open(tb, "w") as f: f.write(tbc)
print(f"    Patch 1f: {count}/3 fix applicati")
PATCH1F

# ── 1g. Patch warning "Cannot set locale" (i18n.py) ──────────────────────────
bmsg "$OK Patch missing-locale warning (i18n)..." \
     "$OK Patch warning locale mancante (i18n)..."
"$PYTHON" - <<'PATCH1G'
import os as _os
_W = _os.environ.get("WARN", "!")
import subprocess, sys

r = subprocess.run(["find", "src/songpressplusplus", "-name", "i18n.py"],
                   capture_output=True, text=True)
c = r.stdout.strip().splitlines()
if not c:
    print(f"{_W} i18n.py non trovato, skip patch 1g.")
    sys.exit(0)
path = c[0]

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
    print(f"    Patch 1g: 1/1 fix applicato in {path}")
else:
    print(f"{_W} Patch 1g già presente o testo non trovato in {path}")
PATCH1G

# ── 1h. Patch Gtk-CRITICAL sui menu: SetBitmap prima di Append ───────────────
bmsg "$OK Patch Gtk-CRITICAL menu (SetBitmap before Append)..." \
     "$OK Patch Gtk-CRITICAL menu (SetBitmap prima di Append)..."
"$PYTHON" - <<'PATCH1H'
import os as _os
_W = _os.environ.get("WARN", "!")
import re, subprocess, sys

r = subprocess.run(["find", "src/songpressplusplus", "-name", "*.py"],
                   capture_output=True, text=True)
files = [f for f in r.stdout.strip().splitlines() if f]
if not files:
    print(f"{_W} Nessun sorgente trovato, skip patch 1h.")
    sys.exit(0)

# Cattura la coppia di righe consecutive:
#     <ind><item> = <menu>.Append(<args>)
#     <ind><item>.SetBitmap(<bmp>)
PAT = re.compile(
    r'^(?P<ind>[ \t]*)(?P<item>[A-Za-z_][\w.]*)[ \t]*=[ \t]*'
    r'(?P<menu>[A-Za-z_][\w.]*)\.Append\((?P<args>[^\n]*)\)[ \t]*$\n'
    r'(?P=ind)(?P=item)\.SetBitmap\((?P<bmp>[^\n]*)\)[ \t]*$',
    re.MULTILINE)

def repl(m):
    d = m.groupdict()
    args = d['args'].strip()
    sep = ', ' if args else ''
    return (f"{d['ind']}{d['item']} = wx.MenuItem({d['menu']}{sep}{args})\n"
            f"{d['ind']}{d['item']}.SetBitmap({d['bmp']})\n"
            f"{d['ind']}{d['menu']}.Append({d['item']})")

total = 0
touched = []
notutf8 = []
for path in files:
    try:
        with open(path, encoding='utf-8') as f:
            content = f.read()
        enc_errors = 'strict'
    except UnicodeDecodeError:
        with open(path, encoding='utf-8', errors='surrogateescape') as f:
            content = f.read()
        enc_errors = 'surrogateescape'
        notutf8.append(path)

    new, n = PAT.subn(repl, content)
    if n:
        with open(path, 'w', encoding='utf-8', errors=enc_errors) as f:
            f.write(new)
        total += n
        touched.append(f"{path} ({n})")

if notutf8:
    print(f"{_W} Nota: {len(notutf8)} file non sono UTF-8 validi "
          f"(letti e riscritti byte-per-byte):")
    for p in notutf8:
        print(f"{_W}   - {p}")

if total:
    print(f"    Patch 1h: {total} riordini applicati")
    for t in touched:
        print(f"      - {t}")
else:
    print(f"{_W} Patch 1h: nessuna occorrenza (già applicata o forma diversa)")
PATCH1H

# ── 2. Build della wheel (DOPO le patch) ─────────────────────────────────────
bmsg "$OK Building wheel with pip + hatchling..." \
     "$OK Costruzione wheel con pip + hatchling..."
WHEEL_DIR="$BUILD_DIR/wheel"
mkdir -p "$WHEEL_DIR"

"$PYTHON" -m pip wheel \
    --no-deps \
    --wheel-dir "$WHEEL_DIR" \
    "$SCRIPT_DIR"

WHEEL_FILE=$(ls "$WHEEL_DIR"/*.whl | head -n1)
echo "    Wheel: $WHEEL_FILE"

# ── 3. Installazione nell'albero del pacchetto ────────────────────────────────
bmsg "$OK Installing into the package tree..." \
     "$OK Installazione nell'albero del pacchetto..."
mkdir -p "$INSTALL_PREFIX/share/applications"
mkdir -p "$INSTALL_PREFIX/share/pixmaps"
mkdir -p "$INSTALL_PREFIX/share/mime/packages"

"$PYTHON" -m pip install \
    --no-deps \
    --ignore-installed \
    --prefix "$INSTALL_PREFIX" \
    --no-compile \
    "$WHEEL_FILE"

# ── 3a. Normalizzazione layout (specifica RPM) ───────────────────────────────
# Diversamente da Debian, il pip di Fedora NON applica lo schema "posix_local":
# con --prefix installa direttamente in <prefix>/lib/pythonX.Y/site-packages e
# <prefix>/bin. Manteniamo comunque una fusione difensiva di un eventuale
# <prefix>/local (se un pip patchato lo creasse) e NON tocchiamo il nome
# site-packages: su Fedora è quello atteso (versionato per minor version).
bmsg "$OK Normalising layout (merge usr/local if present)..." \
     "$OK Normalizzazione layout (fusione usr/local se presente)..."
if [[ -d "$INSTALL_PREFIX/local" ]]; then
    ( cd "$INSTALL_PREFIX/local" && tar cf - . ) | ( cd "$INSTALL_PREFIX" && tar xf - )
    rm -rf "$INSTALL_PREFIX/local"
    bmsg "    usr/local merged into usr and removed" \
         "    usr/local fuso in usr e rimosso"
fi

# Rileva la cartella site-packages reale (serve per il check template e i %files)
PY_SITE_SRC=$(find "$INSTALL_PREFIX/lib" "$INSTALL_PREFIX/lib64" -maxdepth 2 -type d \
    \( -name "site-packages" -o -name "dist-packages" \) 2>/dev/null | head -n1 || true)
bmsg "    Python modules in: ${PY_SITE_SRC#$TREE}" \
     "    Moduli Python in: ${PY_SITE_SRC#$TREE}"

# ── 3a-bis. Individuazione anticipata dell'eseguibile ────────────────────────
# Il file .desktop (passo 4) e il wrapper (passo 6b) devono puntare al percorso
# REALE del binario. Lo rileviamo qui, subito dopo l'installazione.
REAL_BIN=$(find "$TREE" -path "*/bin/SongpressPlusPlus" -not -name "*_bin" | head -n1 || true)
if [[ -n "$REAL_BIN" ]]; then
    BIN_DIR=$(dirname "$REAL_BIN")
    INSTALLED_BIN_DIR="${BIN_DIR#"$TREE"}"      # es. /usr/bin
else
    BIN_DIR=""
    INSTALLED_BIN_DIR="/usr/bin"
    bmsg "$WARN executable not found: the .desktop will use /usr/bin." \
         "$WARN eseguibile non trovato: il .desktop userà /usr/bin."
fi
bmsg "    Executable installed in: $INSTALLED_BIN_DIR" \
     "    Eseguibile installato in: $INSTALLED_BIN_DIR"

# ── 3b. Verifica dei template ────────────────────────────────────────────────
# Come in build_deb.sh: Globals.InitDataPath() copia templates/local_dir/ nella
# cartella dati utente. Se la wheel non include quelle cartelle le creiamo qui.
bmsg "$OK Checking the templates/ tree in the package..." \
     "$OK Verifica dell'albero templates/ nel pacchetto..."
PKG_DIR=$(find "$INSTALL_PREFIX" -type f -name "Globals.py" \
    \( -path "*site-packages*" -o -path "*dist-packages*" \) \
    -printf '%h\n' 2>/dev/null | head -n1)

TEMPLATE_SUBDIRS=(fonts local_dir slides songs themes)

if [[ -z "$PKG_DIR" ]]; then
    bmsg "$WARN Package folder not found: skipping template check." \
         "$WARN Cartella del pacchetto non individuata: salto la verifica dei template."
else
    MISSING=0
    for SUB in "${TEMPLATE_SUBDIRS[@]}"; do
        if [[ -d "$PKG_DIR/templates/$SUB" ]]; then
            echo "  ✓ templates/$SUB"
        else
            bmsg "$WARN templates/$SUB MISSING in the wheel: creating it." \
                 "$WARN templates/$SUB MANCANTE nella wheel: la creo."
            MISSING=1
            mkdir -p "$PKG_DIR/templates/$SUB"
            cat > "$PKG_DIR/templates/$SUB/.keep" <<'KEEP'
# Placeholder: keeps this directory inside the package.
# Songpress++ needs the full templates/ tree (fonts, local_dir, slides,
# songs, themes). Safe to delete once the folder holds real files.
KEEP
        fi
    done

    LOCAL_DIR="$PKG_DIR/templates/local_dir"
    for SUB in "${TEMPLATE_SUBDIRS[@]}"; do
        [[ "$SUB" == "local_dir" ]] && continue
        if [[ ! -d "$LOCAL_DIR/templates/$SUB" ]]; then
            bmsg "$WARN templates/local_dir/templates/$SUB MISSING: creating it." \
                 "$WARN templates/local_dir/templates/$SUB MANCANTE: la creo."
            MISSING=1
            mkdir -p "$LOCAL_DIR/templates/$SUB"
            cp "$PKG_DIR/templates/$SUB/.keep" \
               "$LOCAL_DIR/templates/$SUB/.keep" 2>/dev/null || true
        fi
    done

    if [[ "$MISSING" -eq 1 ]]; then
        bmsg "  → The missing folders were created in the package, but to" \
             "  → Le cartelle mancanti sono state create nel pacchetto, ma per"
        bmsg "    make them permanent by declaring them in pyproject.toml, e.g.:" \
             "    renderle permanenti dichiarale in pyproject.toml, es.:"
        echo "        [tool.hatch.build.targets.wheel.force-include]"
        echo "        \"src/songpressplusplus/templates\" = \"songpressplusplus/templates\""
    fi
fi

# ── 4. Desktop entry & icona ─────────────────────────────────────────────────
bmsg "$OK Creating .desktop and icon..." \
     "$OK Creazione .desktop e icona..."

ICON_SRC="$SCRIPT_DIR/installer/songpressplusplus.ico"
ICON_PNG="$SCRIPT_DIR/installer/songpressplusplus.png"
if [[ -f "$ICON_PNG" ]]; then
    cp "$ICON_PNG" "$INSTALL_PREFIX/share/pixmaps/${RPM_NAME}.png"
elif [[ -f "$ICON_SRC" ]]; then
    if [[ "$HAVE_IM" -eq 1 ]]; then
        IM "${ICON_SRC}[0]" -resize 64x64 \
            "$INSTALL_PREFIX/share/pixmaps/${RPM_NAME}.png" 2>/dev/null || \
        IM "$ICON_SRC" -thumbnail 64x64 \
            "$INSTALL_PREFIX/share/pixmaps/${RPM_NAME}.png" 2>/dev/null || true
    fi
fi
if [[ ! -f "$INSTALL_PREFIX/share/pixmaps/${RPM_NAME}.png" ]]; then
    FIRST_LAYER=$(ls "$INSTALL_PREFIX/share/pixmaps/${RPM_NAME}-"*.png 2>/dev/null | sort | head -n1 || true)
    if [[ -n "$FIRST_LAYER" ]]; then
        cp "$FIRST_LAYER" "$INSTALL_PREFIX/share/pixmaps/${RPM_NAME}.png"
        bmsg "    Icon: used layer $FIRST_LAYER" \
             "    Icona: usato layer $FIRST_LAYER"
    fi
fi
rm -f "$INSTALL_PREFIX/share/pixmaps/${RPM_NAME}-"*.png

if [[ -f "$INSTALL_PREFIX/share/pixmaps/${RPM_NAME}.png" ]]; then
    for SIZE in 256 128 64 48; do
        mkdir -p "$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/apps"
        mkdir -p "$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/mimetypes"
        DST_APP="$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/apps/${RPM_NAME}.png"
        DST_MIME="$INSTALL_PREFIX/share/icons/hicolor/${SIZE}x${SIZE}/mimetypes/${RPM_NAME}.png"
        if [[ "$HAVE_IM" -eq 1 ]]; then
            IM "$INSTALL_PREFIX/share/pixmaps/${RPM_NAME}.png" \
                -resize "${SIZE}x${SIZE}" "$DST_APP" 2>/dev/null || \
                cp "$INSTALL_PREFIX/share/pixmaps/${RPM_NAME}.png" "$DST_APP"
        else
            cp "$INSTALL_PREFIX/share/pixmaps/${RPM_NAME}.png" "$DST_APP"
        fi
        cp "$DST_APP" "$DST_MIME" 2>/dev/null || true
    done
    bmsg "    hicolor icons installed (256/128/64/48)" \
         "    Icone hicolor installate (256/128/64/48)"
else
    bmsg "$WARN No icon found!" \
         "$WARN Nessuna icona trovata!"
    bmsg "                 Put a PNG in: installer/songpressplusplus.png" \
         "                 Metti un PNG in: installer/songpressplusplus.png"
    bmsg "                 (or installer/songpressplusplus.ico + ImageMagick)." \
         "                 (oppure installer/songpressplusplus.ico + ImageMagick)."
fi

# File XML tipo MIME per estensioni ChordPro
cat > "$INSTALL_PREFIX/share/mime/packages/${RPM_NAME}.xml" <<'MIME'
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

cat > "$INSTALL_PREFIX/share/applications/${RPM_NAME}.desktop" <<DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Songpress++
GenericName=Song Typesetter
Comment=Genera canzonieri di alta qualità in PDF e PPTX
Exec=env GDK_BACKEND=x11 ${INSTALLED_BIN_DIR}/SongpressPlusPlus %f
Icon=${RPM_NAME}
Terminal=false
Categories=Office;Publishing;Education;
Keywords=song;chords;songbook;pdf;
MimeType=text/x-chordpro;
StartupNotify=true
DESKTOP

# ── 4b. AppStream metainfo ───────────────────────────────────────────────────
bmsg "$OK Creating AppStream metainfo..." \
     "$OK Creazione AppStream metainfo..."
mkdir -p "$INSTALL_PREFIX/share/metainfo"
cat > "$INSTALL_PREFIX/share/metainfo/${APP_ID}.metainfo.xml" <<METAINFO
<?xml version="1.0" encoding="UTF-8"?>
<component type="desktop-application">
  <id>${APP_ID}</id>
  <pkgname>${RPM_NAME}</pkgname>
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
  <launchable type="desktop-id">${RPM_NAME}.desktop</launchable>
  <icon type="stock">${RPM_NAME}</icon>
  <url type="homepage">${HOMEPAGE}</url>
  <categories>
    <category>Office</category>
    <category>Publishing</category>
  </categories>
  <content_rating type="oars-1.1"/>
</component>
METAINFO

# ── 4c. File copyright ───────────────────────────────────────────────────────
# Convenzione: la licenza sotto /usr/share/doc/<pkg>/. In RPM il campo License
# porta già l'informazione SPDX; il file è comodità aggiuntiva.
bmsg "$OK Writing copyright..." \
     "$OK Scrittura copyright..."
DOC_DIR="$INSTALL_PREFIX/share/doc/${RPM_NAME}"
mkdir -p "$DOC_DIR"
cat > "$DOC_DIR/copyright" <<COPYRIGHT
Upstream-Name: Songpress++
Source: ${HOMEPAGE}
Copyright: $(date +%Y) ${AUTHOR_NAME}
License: ${LICENSE}
COPYRIGHT

# ── 5. Permessi ───────────────────────────────────────────────────────────────
bmsg "$OK Setting permissions..." \
     "$OK Impostazione permessi..."
find "$TREE" -type d -exec chmod 0755 {} \;
find "$TREE" -type f -exec chmod 0644 {} \;
find "$TREE" -path "*/bin/*" -type f -exec chmod 0755 {} \;

# ── 5b. Wrapper GDK_BACKEND=x11 e symlink minuscolo ──────────────────────────
# Fatto DOPO il passo permessi per evitare che chmod 0644 azzeri il wrapper.
bmsg "$OK Creating GDK_BACKEND=x11 wrapper..." \
     "$OK Creazione wrapper GDK_BACKEND=x11..."
bmsg "    Binary found: ${REAL_BIN:-(none)}" \
     "    Binario trovato: ${REAL_BIN:-(nessuno)}"

if [[ -n "$REAL_BIN" && -f "$REAL_BIN" ]]; then
    mv "$REAL_BIN" "${REAL_BIN}_bin"

    # Filtro che scarta SOLO alcune righe note e innocue (vedi build_deb.sh).
    cat > "$REAL_BIN" <<WRAPPER
#!/bin/bash
# Wrapper: forza backend X11 per compatibilità wxPython/Wayland
export GDK_BACKEND=x11

# SONGPRESS_VERBOSE=1 disattiva il filtro e mostra tutto (per il debug).
if [ -n "\${SONGPRESS_VERBOSE:-}" ]; then
    exec ${INSTALLED_BIN_DIR}/SongpressPlusPlus_bin "\$@"
fi

SPP_NOISE='gtk_image_menu_item_set_image'
SPP_NOISE="\$SPP_NOISE|invalid cast from .GtkMenuItem. to .GtkImageMenuItem."
SPP_NOISE="\$SPP_NOISE|ScreenToClient cannot work when toplevel window is not shown"
SPP_NOISE="\$SPP_NOISE|gtk_combo_box_text_insert"
SPP_NOISE="\$SPP_NOISE|for_size smaller than min-size"

exec 2> >(grep --line-buffered -v -E "\$SPP_NOISE" >&2)
exec ${INSTALLED_BIN_DIR}/SongpressPlusPlus_bin "\$@"
WRAPPER
    chmod 0755 "$REAL_BIN"
    chmod 0755 "${REAL_BIN}_bin"
    bmsg "    Wrapper created: $REAL_BIN → ${INSTALLED_BIN_DIR}/SongpressPlusPlus_bin" \
         "    Wrapper creato: $REAL_BIN → ${INSTALLED_BIN_DIR}/SongpressPlusPlus_bin"

    ln -sf "${INSTALLED_BIN_DIR}/SongpressPlusPlus" "$BIN_DIR/songpressplusplus" || true
    bmsg "    Symlink created: $BIN_DIR/songpressplusplus" \
         "    Symlink creato: $BIN_DIR/songpressplusplus"
else
    bmsg "$WARN Binary not found. bin structure:" \
         "$WARN Binario non trovato. Struttura bin:"
    find "$TREE" -name "bin" -type d -exec ls -la {} \; || true
fi

# =============================================================================
# DA QUI: packaging RPM (sostituisce DEBIAN/control + dpkg-deb).
# =============================================================================

# ── 6. Generazione della lista %files ────────────────────────────────────────
# Elenchiamo ogni file/symlink con percorso ASSOLUTO (un file appartiene a un
# solo pacchetto → nessun conflitto). Le directory vengono marcate "%dir" SOLO
# se sono "nostre": le directory di sistema condivise (/usr, /usr/bin,
# /usr/share/..., /usr/lib/pythonX.Y/site-packages, hicolor/*, ...) NON vanno
# possedute perché appartengono ad altri pacchetti (filesystem, python3-libs,
# hicolor-icon-theme, shared-mime-info).
bmsg "$OK Generating %files list..." \
     "$OK Generazione lista %files..."

# Regex delle directory di SISTEMA da NON possedere.
SYS_DIRS_RE='^(/usr|/usr/bin|/usr/lib|/usr/lib64|/usr/share|/usr/share/applications|/usr/share/pixmaps|/usr/share/mime|/usr/share/mime/packages|/usr/share/metainfo|/usr/share/doc|/usr/share/icons|/usr/share/icons/hicolor|/usr/share/icons/hicolor/[0-9]+x[0-9]+|/usr/share/icons/hicolor/[0-9]+x[0-9]+/(apps|mimetypes)|/usr/lib/python[0-9.]+|/usr/lib/python[0-9.]+/site-packages|/usr/lib/python[0-9.]+/dist-packages|/usr/lib64/python[0-9.]+|/usr/lib64/python[0-9.]+/site-packages|/usr/lib64/python[0-9.]+/dist-packages)$'

{
    echo "%defattr(-,root,root,-)"
    # File regolari e symlink (percorso assoluto)
    ( cd "$TREE" && find . -mindepth 1 \( -type f -o -type l \) -printf '/%P\n' ) | sort
    # Directory "nostre" → %dir (escludendo quelle di sistema)
    ( cd "$TREE" && find . -mindepth 1 -type d -printf '/%P\n' ) | sort | \
        grep -Ev "$SYS_DIRS_RE" | sed 's/^/%dir /'
} > "$FILES_LIST"

_N_FILES=$(grep -c '^/' "$FILES_LIST" || true)
_N_DIRS=$(grep -c '^%dir ' "$FILES_LIST" || true)
bmsg "    Listed: $_N_FILES files, $_N_DIRS owned directories" \
     "    Elencati: $_N_FILES file, $_N_DIRS directory possedute"

# ── 7. Generazione del file .spec ────────────────────────────────────────────
bmsg "$OK Writing the .spec file..." \
     "$OK Scrittura del file .spec..."

# Parte 1 (heredoc NON quotato): preambolo con valori espansi.
#   - debug_package %{nil}        → niente sotto-pacchetto -debuginfo (è noarch)
#   - __brp_python_bytecompile    → niente .pyc (coerente con pip --no-compile;
#                                    altrimenti i .pyc generati non sarebbero in
#                                    %files → errore "installed but unpackaged").
#   - AutoReqProv: no             → dipendenze SOLO quelle dichiarate a mano,
#                                    come in build_deb.sh (niente autoreq che
#                                    inventi nomi di moduli Python).
cat > "$SPEC_FILE" <<SPEC_HEAD
%global debug_package %{nil}
%global __brp_python_bytecompile %{nil}

Name:           ${RPM_NAME}
Version:        ${RPM_VERSION}
Release:        ${RPM_RELEASE}%{?dist}
Summary:        ${SUMMARY}

License:        ${LICENSE}
URL:            ${HOMEPAGE}
BuildArch:      ${RPM_ARCH}

AutoReqProv:    no
${REQUIRES}
${RECOMMENDS}

%description
Songpress++ is a free, easy-to-use song typesetting program
that generates high-quality songbooks in PDF and PPTX.

# Nessun %prep/%build: l'albero è già pronto, costruito da build_rpm.sh.
%install
rm -rf %{buildroot}
mkdir -p %{buildroot}
cp -a "${TREE}"/. %{buildroot}/

SPEC_HEAD

# Parte 2: scriptlet %post (equivale a DEBIAN/postinst "configure").
#   Testa NON quotata → inietta PIP_DEPS da build_rpm.sh.
cat >> "$SPEC_FILE" <<POST_HEAD
%post
PIP_DEPS="${PIP_DEPS}"
POST_HEAD

# Corpo QUOTATO (letterale). Attenzione: RPM espande le macro '%' negli
# scriptlet, quindi i '%' letterali (printf) sono RADDOPPIATI: '%%s'.
cat >> "$SPEC_FILE" <<'POST_BODY'
# In RPM lo scriptlet %post riceve $1 = numero di istanze DOPO l'operazione:
#   1 = prima installazione, 2 = aggiornamento. In entrambi i casi vogliamo
#   aggiornare le cache desktop/MIME/icone e controllare le dipendenze PyPI.

if [ -t 1 ]; then
    SPP_OK=$(printf '\033[1;32m✔\033[0m')
    SPP_WARN=$(printf '\033[1;33m⚠\033[0m')
    SPP_ERR=$(printf '\033[1;31m✘\033[0m')
    SPP_NET=$(printf '\033[1;36m🌐\033[0m')
else
    SPP_OK='✔'; SPP_WARN='⚠'; SPP_ERR='✘'; SPP_NET='🌐'
fi

case "${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}" in
    it | it_* | it.* | it_*.*) SPP_LANG=it ;;
    *)                          SPP_LANG=en ;;
esac

sppmsg() {
    if [ "$SPP_LANG" = it ]; then printf '%%s\n' "$2"; else printf '%%s\n' "$1"; fi
}

if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database /usr/share/mime || true
fi
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -qf /usr/share/icons/hicolor || true
fi
if command -v appstreamcli >/dev/null 2>&1; then
    appstreamcli refresh-cache --force >/dev/null 2>&1 || true
fi

# ── Dipendenze Python presenti solo su PyPI (python-pptx, pyshortcuts) ────────
PY=$(command -v python3 || true)

# Avviso interattivo: chiede conferma prima di scaricare da PyPI. Se non c'è un
# terminale (dnf/zypper non interattivi, script automatici) NON blocca: procede.
# NB: gli scriptlet RPM interattivi sono sconsigliati dalle linee guida di
# packaging; qui il prompt è comunque best-effort e si autodisabilita.
SP_SKIP=0
if [ -n "$PY" ]; then
    SP_ANSWER="s"
    if [ "${SPP_NONINTERACTIVE:-}" != "1" ] && [ -r /dev/tty ] && [ -w /dev/tty ]; then
        {
            echo ""
            echo "=================================================================="
            if [ "$SPP_LANG" = it ]; then
                echo "Songpress++ — È RICHIESTA UNA CONNESSIONE A INTERNET $SPP_NET"
                echo ""
                echo "  Alcune dipendenze Python non esistono nei repository"
                echo "  (python-pptx, pyshortcuts) e verranno scaricate ORA via pip."
                echo ""
                echo "  Se rispondi No il pacchetto viene installato lo stesso, ma"
                echo "  dovrai installare le dipendenze a mano in un secondo momento"
                echo "  e l'applicazione potrebbe non funzionare correttamente."
            else
                echo "Songpress++ — AN INTERNET CONNECTION IS REQUIRED $SPP_NET"
                echo ""
                echo "  Some Python dependencies are not available in the distro"
                echo "  repositories (python-pptx, pyshortcuts) and will be"
                echo "  downloaded NOW via pip."
                echo ""
                echo "  If you answer No the package is still installed, but you"
                echo "  will have to install the dependencies manually later and"
                echo "  the application may not work correctly."
            fi
            echo "=================================================================="
            if [ "$SPP_LANG" = it ]; then
                printf "$SPP_NET  Continuare e scaricare le dipendenze ora? [S/n] "
            else
                printf "$SPP_NET  Continue and download the dependencies now? [Y/n] "
            fi
        } > /dev/tty
        read SP_ANSWER < /dev/tty || SP_ANSWER="s"
        echo "" > /dev/tty
    fi

    case "$SP_ANSWER" in
        [nN]*)
            SP_SKIP=1
            sppmsg \
"$SPP_WARN Songpress++: dependency download skipped at the user's request." \
"$SPP_WARN Songpress++: download delle dipendenze saltato su richiesta dell'utente."
            sppmsg \
"Songpress++: to install them later, run:" \
"Songpress++: per installarle più tardi esegui:"
            echo "    sudo pip3 install --break-system-packages python-pptx pyshortcuts"
            ;;
    esac
fi

if [ -n "$PY" ] && [ "$SP_SKIP" -eq 0 ]; then
    sppmsg \
"$SPP_NET Songpress++: checking PyPI dependencies (requires an Internet connection)..." \
"$SPP_NET Songpress++: controllo dipendenze PyPI (richiede una connessione a Internet)..."
    BSP=""
    if "$PY" -m pip install --help 2>/dev/null | grep -q -- --break-system-packages; then
        BSP="--break-system-packages"
    fi
    echo "$PIP_DEPS" | while IFS=: read PIP_NAME MOD_NAME; do
        [ -z "$PIP_NAME" ] && continue
        if "$PY" -c "import $MOD_NAME" >/dev/null 2>&1; then
            sppmsg \
"$SPP_OK Songpress++: dependency '$PIP_NAME' already present." \
"$SPP_OK Songpress++: dipendenza '$PIP_NAME' già presente."
        else
            sppmsg \
"$SPP_NET Songpress++: installing '$PIP_NAME' via pip..." \
"$SPP_NET Songpress++: installo '$PIP_NAME' via pip..."
            if "$PY" -m pip install $BSP --root-user-action=ignore --no-warn-script-location "$PIP_NAME"; then
                sppmsg \
"$SPP_OK Songpress++: '$PIP_NAME' installed." \
"$SPP_OK Songpress++: '$PIP_NAME' installato."
            else
                sppmsg \
"$SPP_ERR Songpress++: could not install '$PIP_NAME'. Do it manually with:  sudo pip3 install $BSP $PIP_NAME" \
"$SPP_ERR Songpress++: non sono riuscito a installare '$PIP_NAME'. Fallo a mano con:  sudo pip3 install $BSP $PIP_NAME"
            fi
        fi
    done
fi

exit 0
POST_BODY

# ── Scriptlet %postun (equivale a DEBIAN/postrm): aggiorna le cache ───────────
# In RPM %postun riceve $1 = istanze rimaste: 0 = disinstallazione definitiva,
# 1 = aggiornamento. Aggiornare le cache va bene in entrambi i casi.
cat >> "$SPEC_FILE" <<'POSTUN_BODY'
%postun
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
if command -v update-mime-database >/dev/null 2>&1; then
    update-mime-database /usr/share/mime || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -qf /usr/share/icons/hicolor || true
fi
if command -v appstreamcli >/dev/null 2>&1; then
    appstreamcli refresh-cache --force >/dev/null 2>&1 || true
fi
exit 0
POSTUN_BODY

# ── Sezione %files (dalla lista generata al passo 6) ──────────────────────────
cat >> "$SPEC_FILE" <<FILES_SECTION
%files -f ${FILES_LIST}

%changelog
* $(LC_ALL=C date '+%a %b %d %Y') ${MAINTAINER} - ${RPM_VERSION}-${RPM_RELEASE}
- Automated build produced by build_rpm.sh
FILES_SECTION

# ── 8. Costruzione dell'.rpm ─────────────────────────────────────────────────
bmsg "$OK Building the .rpm package..." \
     "$OK Costruzione del pacchetto .rpm..."
mkdir -p "$RPMBUILD_TOP"/{BUILD,BUILDROOT,RPMS,SRPMS,SOURCES,SPECS}

# _topdir isolato: non tocca ~/rpmbuild. _rpmdir → i .rpm finiscono in build_rpm/.
rpmbuild -bb \
    --define "_topdir $RPMBUILD_TOP" \
    --define "_rpmdir $BUILD_DIR" \
    --define "_build_id_links none" \
    "$SPEC_FILE"

# rpmbuild scrive in $BUILD_DIR/<arch>/<nome>.rpm : lo spostiamo in build_rpm/.
RPM_FILE=$(find "$BUILD_DIR" -name "${RPM_NAME}-${RPM_VERSION}-*.rpm" -type f | head -n1)
if [[ -n "$RPM_FILE" && "$(dirname "$RPM_FILE")" != "$BUILD_DIR" ]]; then
    mv -f "$RPM_FILE" "$BUILD_DIR/"
    RPM_FILE="$BUILD_DIR/$(basename "$RPM_FILE")"
    rmdir "$BUILD_DIR/${RPM_ARCH}" 2>/dev/null || true
fi

echo ""
bmsg "$DONE  Package created: $RPM_FILE" \
     "$DONE  Pacchetto creato: $RPM_FILE"
echo ""
bmsg "$PKG  To install it (Fedora/RHEL):" \
     "$PKG  Per installarlo (Fedora/RHEL):"
echo "   sudo dnf install \"$RPM_FILE\""
echo ""
bmsg "$PKG  On openSUSE:" \
     "$PKG  Su openSUSE:"
echo "   sudo zypper install \"$RPM_FILE\""
echo ""
bmsg "$PKG  Or with rpm directly (does NOT resolve dependencies):" \
     "$PKG  Oppure con rpm diretto (NON risolve le dipendenze):"
echo "   sudo rpm -i \"$RPM_FILE\""
echo ""
bmsg "$NET  NOTE: installation requires an Internet connection." \
     "$NET  NOTA: l'installazione richiede una connessione a Internet."
bmsg "    During %post, pip downloads the dependencies not present in the" \
     "    Durante il %post vengono scaricate via pip le dipendenze non presenti"
bmsg "    distro repositories (python-pptx, pyshortcuts)." \
     "    nei repository della distro (python-pptx, pyshortcuts)."
