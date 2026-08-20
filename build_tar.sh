#!/usr/bin/env bash
# =============================================================================
# build_tar.sh — Costruisce l'installazione .tar(.gz/.xz) per Songpress++
#
# Uso:
#   chmod +x build_tar.sh
#   ./build_tar.sh                 # produce un .tar.gz
#   ./build_tar.sh --format xz     # produce un .tar.xz (compressione migliore)
#   ./build_tar.sh --format tar    # tar non compresso
#   ./build_tar.sh --rebuild       # ricostruisce il payload anche se già presente
#   ./build_tar.sh -y              # niente domande (utile in CI)
#
# Idea di fondo:
#   Il .deb fa automaticamente tre cose che un tarball NON ha:
#     1. installa le dipendenze di sistema (campo Depends:)
#     2. esegue preinst/postinst/postrm
#     3. tiene traccia dei file installati (per rimuoverli in modo pulito)
#   Qui le replichiamo dentro install.sh / uninstall.sh, che finiscono nel
#   tarball insieme al payload.
#
#   Per NON duplicare le patch ai sorgenti e la build della wheel (che vivono
#   in build_deb.sh) RIUSIAMO il payload che build_deb.sh già produce:
#       build_deb/<nome>_<versione>/usr
#   Se non esiste, lo costruiamo lanciando build_deb.sh. Da quell'albero e dai
#   file DEBIAN/control e DEBIAN/postinst leggiamo anche l'elenco delle
#   dipendenze (di sistema e solo-PyPI), così restano allineate al .deb.
#
# Prerequisiti:
#   - gli stessi di build_deb.sh (Python>=3.12, pip, hatchling via rete, ...)
#   - tar, gzip (per .tar.gz) o xz-utils (per .tar.xz)
# =============================================================================

set -euo pipefail

# ── Marcatori di stato (come in build_deb.sh) ─────────────────────────────────
if [[ -t 1 ]]; then
    OK=$'\e[1;32m✔\e[0m'; WARN=$'\e[1;33m⚠\e[0m'
    ERR=$'\e[1;31m✘\e[0m'; NET=$'\e[1;36m🌐\e[0m'
else
    OK='✔'; WARN='⚠'; ERR='✘'; NET='🌐'
fi
DONE='✅'; PKG='📦'
export OK WARN ERR NET DONE PKG

# ── Lingua dei messaggi di build (en base, it se locale italiano) ─────────────
case "${SPP_BUILD_LANG:-${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}}" in
    it | it_* | it.* | it_*.*) BUILD_LANG=it ;;
    *)                          BUILD_LANG=en ;;
esac
bmsg() { if [ "$BUILD_LANG" = it ]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi; }

# ── Trappola di errore ────────────────────────────────────────────────────────
_on_err() {
    local rc=$? line=$1 cmd=$2
    echo "" >&2
    bmsg "$ERR ERROR (exit $rc) at line $line of ${BASH_SOURCE[0]##*/}" \
         "$ERR ERRORE (exit $rc) alla riga $line di ${BASH_SOURCE[0]##*/}" >&2
    bmsg "$ERR    command: $cmd" "$ERR    comando: $cmd" >&2
    bmsg "$ERR    archive NOT created." "$ERR    archivio NON creato." >&2
    exit "$rc"
}
trap '_on_err "$LINENO" "$BASH_COMMAND"' ERR

# ── Opzioni ───────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

FORMAT="${SPP_TAR_FORMAT:-gz}"     # gz | xz | tar
REBUILD=0
ASSUME_YES="${SPP_ASSUME_YES:-0}"
DEB_SCRIPT="${SPP_DEB_SCRIPT:-$SCRIPT_DIR/build_deb.sh}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --format) FORMAT="${2:-gz}"; shift 2 ;;
        --format=*) FORMAT="${1#*=}"; shift ;;
        -z|--gzip) FORMAT=gz; shift ;;
        -J|--xz)   FORMAT=xz; shift ;;
        --rebuild) REBUILD=1; shift ;;
        -y|--yes)  ASSUME_YES=1; shift ;;
        -h|--help)
            sed -n '2,30p' "${BASH_SOURCE[0]}"; exit 0 ;;
        *) bmsg "$WARN Unknown option: $1" "$WARN Opzione sconosciuta: $1" >&2; shift ;;
    esac
done

case "$FORMAT" in
    gz)  TAR_FLAG="-z"; TAR_EXT="tar.gz" ;;
    xz)  TAR_FLAG="-J"; TAR_EXT="tar.xz" ;;
    tar|none|"") TAR_FLAG="";  TAR_EXT="tar" ;;
    *) bmsg "$ERR Unknown format '$FORMAT' (use gz|xz|tar)." \
            "$ERR Formato '$FORMAT' sconosciuto (usa gz|xz|tar)." >&2; exit 1 ;;
esac

# ── Nome e versione da pyproject.toml ─────────────────────────────────────────
read_toml() {  # $1 = chiave TOML "project.<x>"
    python3 - "$1" <<'PY'
import sys, tomllib
key = sys.argv[1].split(".")
with open("pyproject.toml","rb") as f:
    d = tomllib.load(f)
cur = d
for k in key:
    cur = cur[k]
print(cur)
PY
}
PKG_NAME="$(read_toml project.name)"
PKG_VERSION="$(read_toml project.version)"
DEB_NAME="$(echo "$PKG_NAME" | tr '[:upper:]' '[:lower:]' | tr '_' '-')"
DEB_VERSION="$PKG_VERSION"

BUILD_DIR="$SCRIPT_DIR/build_deb"     # payload prodotto da build_deb.sh (sola lettura)
TAR_DIR="$SCRIPT_DIR/build_tar"       # output e staging del tarball (questo script)
PKG_ROOT="$BUILD_DIR/${DEB_NAME}_${DEB_VERSION}"
PAYLOAD="$PKG_ROOT/usr"
CONTROL="$PKG_ROOT/DEBIAN/control"
POSTINST="$PKG_ROOT/DEBIAN/postinst"

# ── 1. Payload: riusa quello di build_deb.sh, o costruiscilo ──────────────────
if [[ "$REBUILD" -eq 1 || ! -d "$PAYLOAD" ]]; then
    bmsg "$OK Payload not found (or --rebuild): running build_deb.sh ..." \
         "$OK Payload assente (o --rebuild): eseguo build_deb.sh ..."
    if [[ ! -x "$DEB_SCRIPT" && ! -f "$DEB_SCRIPT" ]]; then
        bmsg "$ERR build_deb.sh not found at: $DEB_SCRIPT" \
             "$ERR build_deb.sh non trovato in: $DEB_SCRIPT" >&2
        exit 1
    fi
    # -y a build_deb.sh: la creazione della wheel scarica da PyPI (serve rete).
    SPP_ASSUME_YES=1 bash "$DEB_SCRIPT" -y
else
    bmsg "$OK Reusing existing payload: ${PAYLOAD#$SCRIPT_DIR/}" \
         "$OK Riuso il payload esistente: ${PAYLOAD#$SCRIPT_DIR/}"
fi

[[ -d "$PAYLOAD" ]] || { bmsg "$ERR payload usr/ still missing." \
                              "$ERR payload usr/ ancora assente." >&2; exit 1; }

# ── 2. Dipendenze lette dagli artefatti del .deb (restano allineate) ──────────
# Depends/Recommends sono una riga sola nel control (le abbiamo tolte le
# continuazioni già in build_deb.sh), quindi basta un grep.
grep_field() {  # $1 = "Depends" | "Recommends"
    [[ -f "$CONTROL" ]] || { echo ""; return; }
    sed -n "s/^$1: //p" "$CONTROL" | head -n1
}
DEPENDS_LINE="$(grep_field Depends)"
RECOMMENDS_LINE="$(grep_field Recommends)"

# PIP_DEPS è un blocco multi-riga "nome:modulo" dentro postinst: lo estraiamo
# fra le virgolette della riga  PIP_DEPS="...".
extract_pip_deps() {
    [[ -f "$POSTINST" ]] || { echo ""; return; }
    awk '
        /^PIP_DEPS="/ { sub(/^PIP_DEPS="/,""); grab=1 }
        grab {
            if ($0 ~ /"/) { sub(/".*/,""); print; exit }
            else print
        }
    ' "$POSTINST"
}
PIP_DEPS="$(extract_pip_deps)"
# Fallback: se per qualche motivo non trovati, valori noti del progetto.
[[ -z "$PIP_DEPS" ]] && PIP_DEPS=$'python-pptx:pptx\npyshortcuts:pyshortcuts'

bmsg "$OK Dependencies read from the .deb metadata." \
     "$OK Dipendenze lette dai metadati del .deb."
echo "    Depends:    ${DEPENDS_LINE:-(none)}"
echo "    Recommends: ${RECOMMENDS_LINE:-(none)}"
echo "    PyPI:       $(echo "$PIP_DEPS" | tr '\n' ' ')"

# ── 3. Assemblaggio dell'albero del tarball ───────────────────────────────────
STAGE_PARENT="$TAR_DIR/stage"
TOPDIR="${DEB_NAME}-${DEB_VERSION}"
STAGE="$STAGE_PARENT/$TOPDIR"
bmsg "$OK Assembling the archive tree ..." \
     "$OK Assemblaggio dell'albero dell'archivio ..."
rm -rf "$STAGE"
mkdir -p "$STAGE"
# copia integrale del payload preservando permessi e symlink (cp -a)
cp -a "$PAYLOAD" "$STAGE/usr"

# ── 3a. install.sh — testata iniettata + corpo letterale ──────────────────────
# Testata (heredoc NON quotato): inietta i valori calcolati sopra.
cat > "$STAGE/install.sh" <<INSTALL_HEAD
#!/usr/bin/env bash
# Installer di Songpress++ (versione tarball). Generato da build_tar.sh.
SPP_DEB_NAME="$DEB_NAME"
SPP_VERSION="$DEB_VERSION"
SPP_DEPENDS="$DEPENDS_LINE"
SPP_RECOMMENDS="$RECOMMENDS_LINE"
SPP_PIP_DEPS="$PIP_DEPS"
INSTALL_HEAD

# Corpo (heredoc quotato): logica eseguita sul sistema di destinazione.
cat >> "$STAGE/install.sh" <<'INSTALL_BODY'
set -euo pipefail

if [ -t 1 ]; then
    C_OK=$'\e[1;32m✔\e[0m'; C_WARN=$'\e[1;33m⚠\e[0m'
    C_ERR=$'\e[1;31m✘\e[0m'; C_NET=$'\e[1;36m🌐\e[0m'
else
    C_OK='✔'; C_WARN='⚠'; C_ERR='✘'; C_NET='🌐'
fi
case "${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}" in
    it | it_* | it.* | it_*.*) L=it ;;
    *)                          L=en ;;
esac
m() { if [ "$L" = it ]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi; }
die() { m "$C_ERR $1" "$C_ERR $2" >&2; exit 1; }

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$HERE/usr"

PREFIX="/usr"
ASSUME_YES=0
DO_DEPS=1

usage() {
    cat <<USAGE
Songpress++ installer (tarball)
  sudo ./install.sh [--prefix DIR] [-y|--yes] [--no-deps]

  --prefix DIR   Prefisso di installazione (default /usr).
                 Con un prefisso diverso da /usr i percorsi assoluti nel
                 wrapper e nel .desktop vengono riscritti e viene impostato
                 PYTHONPATH, così i moduli Python restano importabili.
  -y, --yes      Non fare domande (assume "sì" per apt e pip).
  --no-deps      Non installare le dipendenze (apt + pip): solo i file.
USAGE
}

while [ $# -gt 0 ]; do
    case "$1" in
        --prefix)   PREFIX="${2:?}"; shift 2 ;;
        --prefix=*) PREFIX="${1#*=}"; shift ;;
        -y|--yes)   ASSUME_YES=1; shift ;;
        --no-deps)  DO_DEPS=0; shift ;;
        -h|--help)  usage; exit 0 ;;
        *) m "$C_WARN Unknown option: $1" "$C_WARN Opzione sconosciuta: $1" >&2; shift ;;
    esac
done
PREFIX="${PREFIX%/}"; [ -z "$PREFIX" ] && PREFIX="/"

[ -d "$PAYLOAD" ] || die "payload 'usr/' not found next to install.sh." \
                         "payload 'usr/' non trovato accanto a install.sh."

# Serve root per scrivere sotto $PREFIX ed eventualmente usare apt.
if [ "$(id -u)" -ne 0 ]; then
    m "$C_NET Re-running with sudo ..." "$C_NET Rilancio con sudo ..."
    exec sudo -E bash "$0" --prefix "$PREFIX" \
        $( [ "$ASSUME_YES" -eq 1 ] && echo -y ) \
        $( [ "$DO_DEPS" -eq 0 ] && echo --no-deps )
fi

ask() {  # $1 en $2 it ; ritorna 0 se sì. Con -y o non-interattivo: sì.
    [ "$ASSUME_YES" -eq 1 ] && return 0
    [ -t 0 ] || return 0
    local p ans
    if [ "$L" = it ]; then p="$2 [S/n] "; else p="$1 [Y/n] "; fi
    read -r -p "$p" ans || ans=""
    case "${ans,,}" in n|no) return 1 ;; *) return 0 ;; esac
}

echo ""
m "$C_NET Songpress++ $SPP_VERSION — installer (tarball)" \
  "$C_NET Songpress++ $SPP_VERSION — installer (tarball)"
m "    Prefix: $PREFIX" "    Prefisso: $PREFIX"
echo ""

# ── preinst: migrazione dal vecchio layout /usr/local ─────────────────────────
# Le versioni <=7.0.1 installavano sotto /usr/local, che precede /usr nel PATH
# e in sys.path: lasciarne i residui farebbe caricare codice vecchio. Rimuoviamo
# SOLO ciò che non appartiene a nessun pacchetto dpkg (se dpkg è presente).
legacy_cleanup() {
    local removed=0 target owner
    remove_if_unowned() {
        target="$1"; [ -e "$target" ] || return 0
        if command -v dpkg-query >/dev/null 2>&1 \
           && owner=$(dpkg-query -S "$target" 2>/dev/null); then
            echo "Songpress++: '$target' -> ${owner%%:*}: lo lascio."
            return 0
        fi
        echo "Songpress++: rimuovo residuo vecchio layout: $target"
        rm -rf "$target"; removed=1
    }
    local f d info
    for f in SongpressPlusPlus SongpressPlusPlus_bin songpressplusplus; do
        remove_if_unowned "/usr/local/bin/$f"
    done
    for d in /usr/local/lib/python3*/dist-packages /usr/local/lib/python3*/site-packages; do
        [ -d "$d" ] || continue
        remove_if_unowned "$d/songpressplusplus"
        for info in "$d"/songpressplusplus-*.dist-info "$d"/songpressplusplus-*.egg-info; do
            [ -e "$info" ] || continue
            remove_if_unowned "$info"
        done
    done
    [ "$removed" = 1 ] && m "$C_OK Legacy /usr/local layout cleaned." \
                            "$C_OK Vecchio layout /usr/local ripulito."
    return 0
}
legacy_cleanup

# ── Dipendenze di sistema (ciò che il .deb tira via Depends:) ─────────────────
# Un tarball non ha un package manager alle spalle: se apt c'è le installiamo,
# altrimenti le elenchiamo perché l'utente le metta con il suo gestore.
resolve_apt() {  # legge una stringa "a (>=x), b | c, d" e stampa i pacchetti
    local spec="$1" tok a chosen
    local out=""
    local IFS=','
    local -a toks; read -ra toks <<< "$spec"
    for tok in "${toks[@]}"; do
        tok="${tok%%(*}"                         # via il vincolo di versione
        tok="$(echo "$tok" | xargs || true)"     # trim
        [ -z "$tok" ] && continue
        if [[ "$tok" == *"|"* ]]; then           # alternative: scegli la 1a valida
            chosen=""
            for a in ${tok//|/ }; do
                a="$(echo "$a" | xargs)"
                if apt-cache show "$a" >/dev/null 2>&1; then chosen="$a"; break; fi
            done
            [ -z "$chosen" ] && chosen="$(echo "${tok%%|*}" | xargs)"
            out="$out $chosen"
        else
            out="$out $tok"
        fi
    done
    echo "$out" | xargs || true
}

if [ "$DO_DEPS" -eq 1 ]; then
    if command -v apt-get >/dev/null 2>&1; then
        SYS_PKGS="$(resolve_apt "$SPP_DEPENDS")"
        REC_PKGS="$(resolve_apt "$SPP_RECOMMENDS")"
        m "$C_NET System dependencies to install (apt):" \
          "$C_NET Dipendenze di sistema da installare (apt):"
        echo "    $SYS_PKGS"
        [ -n "$REC_PKGS" ] && { \
            m "    recommended: $REC_PKGS" "    consigliate: $REC_PKGS"; }
        if ask "Install them now with apt?" "Installarle ora con apt?"; then
            apt-get update || true
            # shellcheck disable=SC2086
            apt-get install -y $SYS_PKGS || \
                m "$C_WARN apt could not install all packages; continuing." \
                  "$C_WARN apt non ha installato tutto; proseguo comunque."
            # shellcheck disable=SC2086
            [ -n "$REC_PKGS" ] && apt-get install -y $REC_PKGS || true
        else
            m "$C_WARN Skipped. Install them manually before running the app." \
              "$C_WARN Saltate. Installale a mano prima di usare l'app."
        fi
    else
        m "$C_WARN apt not found. Install these packages with your package manager:" \
          "$C_WARN apt non trovato. Installa questi pacchetti col tuo gestore:"
        echo "    $SPP_DEPENDS"
        [ -n "$SPP_RECOMMENDS" ] && echo "    (consigliati: $SPP_RECOMMENDS)"
    fi
    echo ""
fi

# ── Copia dei file + manifest per la disinstallazione ─────────────────────────
MANIFEST_DIR="$PREFIX/share/$SPP_DEB_NAME"
MANIFEST="$MANIFEST_DIR/install-manifest.txt"
m "$C_OK Installing files into $PREFIX ..." \
  "$C_OK Installazione dei file in $PREFIX ..."
mkdir -p "$PREFIX"
# Copia preservando permessi e symlink (il wrapper è eseguibile, c'è un symlink
# minuscolo songpressplusplus -> SongpressPlusPlus).
( cd "$PAYLOAD" && tar cf - . ) | ( cd "$PREFIX" && tar xpf - )

# Manifest: elenco assoluto di file e symlink installati (per uninstall.sh).
mkdir -p "$MANIFEST_DIR"
{
    echo "# Songpress++ $SPP_VERSION — installed files"
    echo "# prefix: $PREFIX"
    ( cd "$PAYLOAD" && find . \( -type f -o -type l \) -printf '%P\n' ) \
        | sed "s#^#$PREFIX/#"
} > "$MANIFEST"
# il manifest stesso fa parte dell'installazione: registralo
echo "$MANIFEST" >> "$MANIFEST"

# ── Rilocazione: se PREFIX != /usr, correggi i percorsi assoluti ──────────────
if [ "$PREFIX" != "/usr" ]; then
    m "$C_OK Relocating absolute paths for prefix $PREFIX ..." \
      "$C_OK Adatto i percorsi assoluti al prefisso $PREFIX ..."
    WRAP="$PREFIX/bin/SongpressPlusPlus"
    DESK="$PREFIX/share/applications/$SPP_DEB_NAME.desktop"
    if [ -f "$WRAP" ]; then
        sed -i "s#/usr/bin/#$PREFIX/bin/#g" "$WRAP"
        # PYTHONPATH: rende importabili i moduli sotto un prefisso non standard
        sed -i "2i export PYTHONPATH=\"$PREFIX/lib/python3/dist-packages\${PYTHONPATH:+:\$PYTHONPATH}\"" "$WRAP"
        ln -sf "$PREFIX/bin/SongpressPlusPlus" "$PREFIX/bin/songpressplusplus"
    fi
    [ -f "$DESK" ] && sed -i "s#/usr/bin/#$PREFIX/bin/#g" "$DESK"
fi

# ── postinst: aggiornamento cache desktop/MIME/icone/AppStream ────────────────
m "$C_OK Updating desktop / MIME / icon caches ..." \
  "$C_OK Aggiornamento cache desktop / MIME / icone ..."
command -v update-mime-database   >/dev/null 2>&1 && update-mime-database "$PREFIX/share/mime" || true
command -v update-desktop-database>/dev/null 2>&1 && update-desktop-database -q "$PREFIX/share/applications" || true
command -v gtk-update-icon-cache  >/dev/null 2>&1 && gtk-update-icon-cache -qf "$PREFIX/share/icons/hicolor" || true
command -v appstreamcli           >/dev/null 2>&1 && appstreamcli refresh-cache --force >/dev/null 2>&1 || true

# ── Dipendenze solo-PyPI (non nei repo Debian): python-pptx, pyshortcuts ──────
if [ "$DO_DEPS" -eq 1 ]; then
    PY="$(command -v python3 || true)"
    if [ -n "$PY" ] && [ -n "$SPP_PIP_DEPS" ]; then
        if ask "Download PyPI dependencies now (needs Internet)?" \
               "Scaricare ora le dipendenze PyPI (serve Internet)?"; then
            BSP=""
            "$PY" -m pip install --help 2>/dev/null | grep -q -- --break-system-packages \
                && BSP="--break-system-packages"
            printf '%s\n' "$SPP_PIP_DEPS" | while IFS=: read -r pip_name mod_name; do
                [ -z "$pip_name" ] && continue
                if "$PY" -c "import $mod_name" >/dev/null 2>&1; then
                    m "$C_OK PyPI dep '$pip_name' already present." \
                      "$C_OK dipendenza PyPI '$pip_name' già presente."
                else
                    m "$C_NET installing '$pip_name' ..." "$C_NET installo '$pip_name' ..."
                    if "$PY" -m pip install $BSP --root-user-action=ignore \
                             --no-warn-script-location "$pip_name"; then
                        m "$C_OK '$pip_name' installed." "$C_OK '$pip_name' installato."
                    else
                        m "$C_ERR could not install '$pip_name'. Do it with: sudo pip3 install $BSP $pip_name" \
                          "$C_ERR impossibile installare '$pip_name'. Fallo con: sudo pip3 install $BSP $pip_name"
                    fi
                fi
            done
        else
            m "$C_WARN Skipped. Later:  sudo pip3 install --break-system-packages $(printf '%s' "$SPP_PIP_DEPS" | cut -d: -f1 | tr '\n' ' ')" \
              "$C_WARN Saltate. Più tardi:  sudo pip3 install --break-system-packages $(printf '%s' "$SPP_PIP_DEPS" | cut -d: -f1 | tr '\n' ' ')"
        fi
    fi
fi

echo ""
m "$C_OK Installation complete." "$C_OK Installazione completata."
m "    Launch:  SongpressPlusPlus   (or: songpressplusplus)" \
  "    Avvio:   SongpressPlusPlus   (oppure: songpressplusplus)"
m "    Uninstall:  sudo ./uninstall.sh --prefix $PREFIX" \
  "    Disinstalla: sudo ./uninstall.sh --prefix $PREFIX"
INSTALL_BODY
chmod 0755 "$STAGE/install.sh"

# ── 3b. uninstall.sh ──────────────────────────────────────────────────────────
cat > "$STAGE/uninstall.sh" <<UNINSTALL_HEAD
#!/usr/bin/env bash
# Disinstallatore di Songpress++ (versione tarball). Generato da build_tar.sh.
SPP_DEB_NAME="$DEB_NAME"
SPP_VERSION="$DEB_VERSION"
UNINSTALL_HEAD

cat >> "$STAGE/uninstall.sh" <<'UNINSTALL_BODY'
set -euo pipefail

if [ -t 1 ]; then
    C_OK=$'\e[1;32m✔\e[0m'; C_WARN=$'\e[1;33m⚠\e[0m'; C_ERR=$'\e[1;31m✘\e[0m'
else
    C_OK='✔'; C_WARN='⚠'; C_ERR='✘'
fi
case "${LC_ALL:-${LC_MESSAGES:-${LANG:-}}}" in
    it | it_* | it.* | it_*.*) L=it ;;
    *)                          L=en ;;
esac
m() { if [ "$L" = it ]; then printf '%s\n' "$2"; else printf '%s\n' "$1"; fi; }
die() { m "$C_ERR $1" "$C_ERR $2" >&2; exit 1; }

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOAD="$HERE/usr"
PREFIX="/usr"
PURGE=0

while [ $# -gt 0 ]; do
    case "$1" in
        --prefix)   PREFIX="${2:?}"; shift 2 ;;
        --prefix=*) PREFIX="${1#*=}"; shift ;;
        --purge)    PURGE=1; shift ;;   # rimuove anche i dati utente ~/.Songpress++
        -h|--help)
            echo "sudo ./uninstall.sh [--prefix DIR] [--purge]"; exit 0 ;;
        *) m "$C_WARN Unknown option: $1" "$C_WARN Opzione sconosciuta: $1" >&2; shift ;;
    esac
done
PREFIX="${PREFIX%/}"; [ -z "$PREFIX" ] && PREFIX="/"

if [ "$(id -u)" -ne 0 ]; then
    m "$C_WARN Re-running with sudo ..." "$C_WARN Rilancio con sudo ..."
    exec sudo -E bash "$0" --prefix "$PREFIX" $( [ "$PURGE" -eq 1 ] && echo --purge )
fi

MANIFEST="$PREFIX/share/$SPP_DEB_NAME/install-manifest.txt"

# Elenco file: prima dal manifest scritto in fase di installazione; in mancanza
# (utente che ha spostato/cancellato tutto) si ricade sul payload accanto allo
# script, ricostruendo gli stessi percorsi relativi.
FILES=""
if [ -f "$MANIFEST" ]; then
    m "$C_OK Reading manifest: $MANIFEST" "$C_OK Leggo il manifest: $MANIFEST"
    FILES="$(grep -v '^#' "$MANIFEST" || true)"
elif [ -d "$PAYLOAD" ]; then
    m "$C_WARN No manifest; using the payload next to the script." \
      "$C_WARN Nessun manifest; uso il payload accanto allo script."
    FILES="$( ( cd "$PAYLOAD" && find . \( -type f -o -type l \) -printf '%P\n' ) \
              | sed "s#^#$PREFIX/#" )"
else
    die "no manifest and no payload: cannot determine what to remove." \
        "nessun manifest e nessun payload: impossibile sapere cosa rimuovere."
fi

# Rimozione file.
printf '%s\n' "$FILES" | while IFS= read -r f; do
    [ -z "$f" ] && continue
    rm -f "$f" 2>/dev/null || true
done
# symlink/eseguibili noti, per sicurezza
rm -f "$PREFIX/bin/songpressplusplus" "$PREFIX/bin/SongpressPlusPlus" \
      "$PREFIX/bin/SongpressPlusPlus_bin" 2>/dev/null || true

# Pota le directory rimaste vuote. Per ogni file si generano TUTTE le directory
# antenate (fino a $PREFIX escluso), poi si prova a rimuoverle dalla più
# profonda: così spariscono anche le cartelle intermedie (es. .../templates)
# che non sono il dirname diretto di alcun file. rmdir --ignore-fail-on-non-empty
# protegge automaticamente le cartelle condivise (bin, share, ...).
printf '%s\n' "$FILES" | while IFS= read -r f; do
    [ -z "$f" ] && continue
    d="$(dirname "$f")"
    while [ -n "$d" ] && [ "$d" != "$PREFIX" ] && [ "$d" != "/" ] && [ "$d" != "." ]; do
        echo "$d"
        d="$(dirname "$d")"
    done
done | awk -F/ '{ print NF, $0 }' | sort -rn | cut -d' ' -f2- | \
while IFS= read -r d; do
    rmdir --ignore-fail-on-non-empty "$d" 2>/dev/null || true
done

# postrm: ripristina le cache come faceva il .deb.
m "$C_OK Updating desktop / MIME / icon caches ..." \
  "$C_OK Aggiornamento cache desktop / MIME / icone ..."
command -v update-desktop-database>/dev/null 2>&1 && update-desktop-database -q "$PREFIX/share/applications" || true
command -v update-mime-database   >/dev/null 2>&1 && update-mime-database "$PREFIX/share/mime" || true
command -v gtk-update-icon-cache  >/dev/null 2>&1 && gtk-update-icon-cache -qf "$PREFIX/share/icons/hicolor" || true
command -v appstreamcli           >/dev/null 2>&1 && appstreamcli refresh-cache --force >/dev/null 2>&1 || true

if [ "$PURGE" -eq 1 ]; then
    for home in /root /home/*; do
        d="$home/.Songpress++"
        [ -d "$d" ] && { rm -rf "$d"; m "$C_OK removed $d" "$C_OK rimosso $d"; }
    done
fi

echo ""
m "$C_OK Songpress++ removed." "$C_OK Songpress++ rimosso."
m "    Note: apt/pip dependencies are left installed." \
  "    Nota: le dipendenze apt/pip restano installate."
[ "$PURGE" -eq 0 ] && m "    User data in ~/.Songpress++ kept (use --purge to remove)." \
                        "    Dati utente in ~/.Songpress++ conservati (usa --purge per rimuoverli)."
UNINSTALL_BODY
chmod 0755 "$STAGE/uninstall.sh"

# ── 3c. README bilingue ───────────────────────────────────────────────────────
cat > "$STAGE/README.txt" <<README
Songpress++ ${DEB_VERSION} — installazione da tarball
======================================================

ENGLISH
-------
1. Extract:      tar xf ${DEB_NAME}-${DEB_VERSION}.${TAR_EXT}
2. Enter:        cd ${DEB_NAME}-${DEB_VERSION}
3. Install:      sudo ./install.sh
   Options:      --prefix DIR   install elsewhere (default /usr)
                 --no-deps      do not install apt/pip dependencies
                 -y             answer yes to everything
4. Launch:       SongpressPlusPlus     (or: songpressplusplus)
5. Uninstall:    sudo ./uninstall.sh   (add --purge to drop ~/.Songpress++)

An Internet connection is used to install the dependencies (apt + a couple of
PyPI-only packages). With --no-deps only the files are copied.

ITALIANO
--------
1. Estrai:       tar xf ${DEB_NAME}-${DEB_VERSION}.${TAR_EXT}
2. Entra:        cd ${DEB_NAME}-${DEB_VERSION}
3. Installa:     sudo ./install.sh
   Opzioni:      --prefix DIR   installa altrove (default /usr)
                 --no-deps      non installare le dipendenze apt/pip
                 -y             rispondi sì a tutto
4. Avvia:        SongpressPlusPlus     (oppure: songpressplusplus)
5. Disinstalla:  sudo ./uninstall.sh   (aggiungi --purge per ~/.Songpress++)

Serve una connessione Internet per installare le dipendenze (apt + un paio di
pacchetti solo-PyPI). Con --no-deps vengono copiati solo i file.
README

# ── 4. Creazione del tarball ──────────────────────────────────────────────────
OUT="$TAR_DIR/${DEB_NAME}-${DEB_VERSION}.${TAR_EXT}"
mkdir -p "$TAR_DIR"
rm -f "$OUT"
bmsg "$OK Creating the tarball ($TAR_EXT) ..." \
     "$OK Creazione del tarball ($TAR_EXT) ..."
# --owner/--group=root:0 → i file appartengono a root anche se il build gira da
# utente normale (il .deb faceva lo stesso via fakeroot). Percorsi riproducibili.
if tar --help 2>/dev/null | grep -q -- --sort; then SORT_FLAG="--sort=name"; else SORT_FLAG=""; fi
tar -C "$STAGE_PARENT" $TAR_FLAG $SORT_FLAG \
    --owner=root --group=root --numeric-owner \
    -cf "$OUT" "$TOPDIR"

echo ""
bmsg "$DONE  Archive created: $OUT" \
     "$DONE  Archivio creato: $OUT"
echo ""
bmsg "$PKG  To install it:" "$PKG  Per installarlo:"
echo "   tar xf \"$OUT\""
echo "   cd $TOPDIR"
echo "   sudo ./install.sh"
echo ""
bmsg "$NET  NOTE: installation uses the network for apt + PyPI dependencies (skip with --no-deps)." \
     "$NET  NOTA: l'installazione usa la rete per le dipendenze apt + PyPI (si salta con --no-deps)."
