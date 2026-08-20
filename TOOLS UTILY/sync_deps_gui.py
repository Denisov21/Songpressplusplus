#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""
sync_deps_gui.py — GUI (wxPython) per sincronizzare le dipendenze da
pyproject.toml verso i vari target del progetto Songpress++.

DEVE STARE NELLA CARTELLA PRINCIPALE DEL PROGETTO (accanto a pyproject.toml).

Target sincronizzati:
  - src/install_check.vbs        APP_VERSION, array DEPS(N,3), loop For i/For j
  - installer/Build-Portable.ps1 array $Deps = @(...)

Nota sul PS1: l'array $Deps contiene voci che NON sono in pyproject.toml
(es. 'cx_Freeze', tool di build). Queste vengono PRESERVATE al loro posto;
vengono aggiornate solo le voci il cui nome-pacchetto compare in pyproject,
e vengono aggiunte in coda le dipendenze nuove.

Uso:
    python sync_deps_gui.py

Copyright (C) 2026 Denisov21  <progetto Songpress++>
Licenza: GNU General Public License versione 2 (solo) — vedi il menu ?.
"""

import json
import re
from pathlib import Path

import wx
import wx.adv

try:
    import tomllib
except ImportError:  # Python < 3.11
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        tomllib = None  # type: ignore[assignment]  # gestito a runtime


# ─────────────────────────────────────────────────────────────────────────────
#  METADATI (versione, link, descrizione, licenza)
# ─────────────────────────────────────────────────────────────────────────────

TOOL_NAME = "Sync deps — Songpress++"
TOOL_VERSION = "1.0.0"

# TODO: sostituisci con l'URL reale del repository Songpress++.
PROJECT_URL = "https://github.com/songpressplusplus/songpressplusplus"

ABOUT_DESCRIPTION = (
    "Sincronizza le dipendenze del progetto da un'unica fonte "
    "(pyproject.toml) verso i target che ne mantengono una copia:\n"
    "\n"
    "  • src/install_check.vbs — installer Windows: APP_VERSION, array\n"
    "    DEPS(N,3) e i cicli For i/For j vengono riallineati.\n"
    "  • installer/Build-Portable.ps1 — build portabile: viene aggiornato\n"
    "    l'array $Deps, preservando le voci extra (es. cx_Freeze).\n"
    "\n"
    "Guida rapida:\n"
    "  1. Indica la Cartella progetto (o lascia quella corrente): "
    "pyproject.toml e i due target vengono trovati in automatico e un "
    "messaggio nel log indica quali file sono stati trovati o mancano.\n"
    "  2. Spunta i target da aggiornare.\n"
    "  3. Usa \u201cSolo anteprima\u201d per vedere le modifiche senza "
    "scrivere.\n"
    "  4. Premi Sincronizza; il log mostra cosa è stato cambiato.\n"
    "\n"
    "\u201cMostra differenze\u201d confronta le versioni delle dipendenze tra\n"
    "pyproject.toml e Build-Portable.ps1 senza scrivere nulla (le voci extra\n"
    "del PS1, es. cx_Freeze, sono segnalate come \u201csolo in PS1\u201d).\n"
    "\n"
    "File \u203a Preferenze: scegli la dimensione del testo (9\u201318) e il\n"
    "carattere del log; le scelte sono salvate in un file JSON accanto allo\n"
    "script (sync_deps_gui.prefs.json) e riapplicate a ogni avvio.\n"
    "\n"
    "Marker di piattaforma (es. pywin32; sys_platform=='win32') vengono\n"
    "valutati: le voci non-Windows sono escluse da VBS e PS1."
)

LICENSE_TEXT = (
    "Questo programma è software libero: puoi ridistribuirlo e/o\n"
    "modificarlo secondo i termini della GNU General Public License\n"
    "versione 2 (solo), come pubblicata dalla Free Software Foundation.\n"
    "\n"
    "Questo programma è distribuito nella speranza che sia utile, ma\n"
    "SENZA ALCUNA GARANZIA; senza neppure la garanzia implicita di\n"
    "COMMERCIABILITÀ o IDONEITÀ PER UN PARTICOLARE SCOPO. Vedi la GNU\n"
    "General Public License per maggiori dettagli.\n"
    "\n"
    "Dovresti aver ricevuto una copia della GNU General Public License\n"
    "insieme a questo programma; in caso contrario, vedi\n"
    "<https://www.gnu.org/licenses/old-licenses/gpl-2.0.html>.\n"
    "\n"
    "SPDX-License-Identifier: GPL-2.0-only"
)


# ─────────────────────────────────────────────────────────────────────────────
#  LOGICA DI SINCRONIZZAZIONE (pura, senza GUI — restituisce messaggi)
# ─────────────────────────────────────────────────────────────────────────────

# Limite massimo fittizio per dipendenze senza upper-bound (es. pywin32>=308).
# Il VBS richiede sempre un max per VersionInRange; questo valore lo rende
# di fatto illimitato senza toccare la logica del .vbs.
VBS_OPEN_MAX = "99999"


def split_requirement(dep_str):
    """
    Analizza una specifica PEP 508 tipo:
        'wxPython>=4.2.4,<5.0.0'
        'pywin32>=308'
        "pywin32>=308; sys_platform == 'win32'"
    Restituisce dict(name, spec, min, max, marker) o None se non parsabile.
      - spec   : parte versione senza marker (es. '>=308' o '>=4.2.4,<5.0.0')
      - min/max: estratti da >= e < (max può essere None)
      - marker : testo dopo ';' (stringa vuota se assente)
    """
    s = dep_str.strip()
    marker = ""
    if ";" in s:
        s, marker = s.split(";", 1)
        s, marker = s.strip(), marker.strip()
    m = re.match(r'^([A-Za-z0-9_.\-]+)\s*(.*)$', s)
    if not m:
        return None
    name = m.group(1)
    spec = m.group(2).strip()
    vmin = vmax = None
    mm = re.search(r'>=\s*([^,\s]+)', spec)
    if mm:
        vmin = mm.group(1)
    mx = re.search(r'<\s*([^,\s=]+)', spec)   # '<' ma non '<='
    if mx:
        vmax = mx.group(1)
    return {"name": name, "spec": spec, "min": vmin, "max": vmax, "marker": marker}


def marker_allows_windows(marker):
    """
    True se una dipendenza con questo marker va inclusa nei target Windows
    (install_check.vbs e Build-Portable.ps1). Usa 'packaging' se disponibile,
    altrimenti ricade su un'euristica sui nomi di piattaforma.
    """
    if not marker:
        return True
    try:
        from packaging.markers import Marker
        env = {
            "sys_platform": "win32",
            "platform_system": "Windows",
            "os_name": "nt",
            "platform_machine": "AMD64",
            "python_version": "3.12",
            "python_full_version": "3.12.0",
            "implementation_name": "cpython",
        }
        return bool(Marker(marker).evaluate(env))
    except Exception:
        pass
    m = marker.lower()
    if "win32" in m or "windows" in m or "'nt'" in m:
        return True
    if "linux" in m or "darwin" in m or "macos" in m:
        return False
    return True  # marker non di piattaforma (es. python_version): includi


def windows_spec(dep):
    """
    Specifica da usare nei target Windows (marker rimosso, che su Windows è
    sempre vero). Restituisce None se il marker esclude Windows.
    """
    if not marker_allows_windows(dep["marker"]):
        return None
    return f"{dep['name']}{dep['spec']}" if dep["spec"] else dep["name"]


def dep_name(spec):
    """
    Estrae il nome-pacchetto normalizzato da una specifica qualsiasi
    ('wxPython>=4.2.4,<5.0.0', 'pywin32>=308', 'cx_Freeze', "pkg; marker").
    Normalizza a minuscolo con '-' (equivalenza PyPI _/-).
    """
    s = spec.strip().strip("'\"")
    s = s.split(";")[0]     # via marker ambiente
    s = s.split("[")[0]     # via extras
    m = re.match(r'^([A-Za-z0-9_.\-]+)', s)
    name = m.group(1) if m else s
    return name.lower().replace("_", "-")


def load_pyproject(toml_path):
    """Restituisce (version, raw_deps: list[str])."""
    if tomllib is None:
        raise RuntimeError(
            "Manca il modulo TOML: usa Python >= 3.11 oppure 'pip install tomli'."
        )
    with open(toml_path, "rb") as f:
        toml = tomllib.load(f)
    version = toml["project"]["version"]
    raw_deps = list(toml["project"]["dependencies"])
    return version, raw_deps


def build_deps_block(deps_parsed):
    """Righe VBS per dichiarazione e popolamento di DEPS."""
    n = len(deps_parsed) - 1
    lines = [f"Dim DEPS({n}, 3)"]
    for i, (pip_name, ver_min, ver_max) in enumerate(deps_parsed):
        lines.append(
            f'DEPS({i},0) = "{pip_name:<14}" : DEPS({i},1) = "{pip_name:<14}" '
            f': DEPS({i},2) = "{ver_min:<7}" : DEPS({i},3) = "{ver_max}"'
        )
    return "\n".join(lines)


def sync_vbs_text(vbs_text, version, raw_deps):
    """Aggiorna il testo del VBS. Restituisce (nuovo_testo, messaggi).

    Se dopo gli aggiornamenti il testo coincide con l'originale, restituisce
    l'originale intatto e lo segnala (no-op): nulla verra' riscritto.
    """
    original = vbs_text
    msgs = []
    deps_parsed = []  # tuple (pip_name, ver_min, ver_max)
    for raw in raw_deps:
        d = split_requirement(raw)
        if d is None:
            msgs.append(f"    VBS: ignorata (non parsabile): {raw!r}")
            continue
        if d["marker"] and not marker_allows_windows(d["marker"]):
            msgs.append(f"    VBS: esclusa (marker non-Windows): {raw!r}")
            continue
        if d["min"] is None:
            msgs.append(f"    VBS: ignorata (manca versione minima >=): {raw!r}")
            continue
        ver_max = d["max"]
        if ver_max is None:
            ver_max = VBS_OPEN_MAX
            msgs.append(f"    VBS: {d['name']} senza upper-bound, "
                        f"uso max fittizio {VBS_OPEN_MAX}.")
        deps_parsed.append((d["name"], d["min"], ver_max))

    if not deps_parsed:
        raise RuntimeError("Nessuna dipendenza compatibile col formato VBS.")

    n = len(deps_parsed) - 1

    # 1. APP_VERSION
    vbs_text = re.sub(
        r'(Const APP_VERSION\s*=\s*")[^"]*(")',
        rf'\g<1>{version}\g<2>',
        vbs_text,
    )
    # 2. Blocco DEPS
    vbs_text = re.sub(
        r'Dim DEPS\(\d+,\s*3\).*?(?=\r?\n\')',
        build_deps_block(deps_parsed),
        vbs_text,
        flags=re.DOTALL,
    )
    # 3. Loop installazione
    vbs_text = re.sub(r'(For j = 0 To )\d+', rf'\g<1>{n}', vbs_text)
    # 4. Loop verifica
    vbs_text = re.sub(r'(For i = 0 To )\d+', rf'\g<1>{n}', vbs_text)

    msgs.append(f"    VBS: {len(deps_parsed)} dipendenze, indice max {n}.")
    if vbs_text == original:
        msgs.append("    VBS: gia' allineato, nessuna modifica.")
        return original, msgs
    return vbs_text, msgs


def sync_ps1_text(ps1_text, raw_deps):
    """
    Aggiorna il blocco $Deps = @(...) preservando le voci extra
    (non presenti in pyproject). Restituisce (nuovo_testo, messaggi).

    Preservazione della struttura:
      - se l'elenco risultante coincide con quello gia' presente, restituisce
        il testo ORIGINALE intatto (nessuna riscrittura del blocco: riga vuota,
        indentazione e fine-riga restano esattamente com'erano);
      - se invece qualcosa cambia, riscrive solo l'elenco delle voci mantenendo
        il testo che precede la prima voce e quello che segue l'ultima, cosi'
        un'eventuale riga vuota prima della ')' e la ')' stessa restano al loro
        posto.
    """
    msgs = []
    m = re.search(r'(\$Deps\s*=\s*@\()(.*?)(\n[ \t]*\))', ps1_text, re.DOTALL)
    if not m:
        return ps1_text, ["    PS1: blocco '$Deps = @(...)' non trovato, saltato."]

    head, body, tail = m.group(1), m.group(2), m.group(3)

    # posizioni esatte delle voci quotate: servono per conservare il testo che
    # le precede (indentazione iniziale) e che le segue (es. riga vuota finale).
    quotes = list(re.finditer(r"'([^']*)'", body))
    existing = [q.group(1) for q in quotes]

    indent_m = re.search(r'\n([ \t]+)\S', body)
    indent = indent_m.group(1) if indent_m else "    "

    # nome normalizzato -> specifica Windows (marker rimosso) o None se esclusa
    pyproj = {}
    for d in raw_deps:
        parsed = split_requirement(d)
        if parsed is None:
            continue
        pyproj[dep_name(d)] = windows_spec(parsed)

    used = set()
    new_entries = []
    changes = []  # descrizioni delle modifiche effettive alle voci

    for e in existing:
        n = dep_name(e)
        if n in pyproj:
            spec = pyproj[n]
            used.add(n)
            if spec is None:
                changes.append(f"    PS1: rimosso {e.strip()} (marker non-Windows).")
                continue
            if spec != e.strip():
                changes.append(f"    PS1: aggiornato {e.strip()} -> {spec}")
            new_entries.append(spec)
        else:
            new_entries.append(e)  # extra preservato (es. cx_Freeze)

    for d in raw_deps:
        n = dep_name(d)
        if n not in used:
            spec = pyproj.get(n)
            used.add(n)
            if spec is None:
                changes.append(f"    PS1: saltato {d.strip()} (marker non-Windows).")
                continue
            new_entries.append(spec)
            changes.append(f"    PS1: aggiunto {spec}")

    kept_extra = [e for e in existing if dep_name(e) not in pyproj]

    # --- no-op: elenco risultante identico all'attuale -> non tocco nulla e
    #     restituisco il testo originale byte-per-byte.
    if new_entries == existing:
        if kept_extra:
            msgs.append(f"    PS1: preservate voci extra: {', '.join(kept_extra)}")
        msgs.append("    PS1: gia' allineato, nessuna modifica.")
        return ps1_text, msgs

    # --- ricostruzione: preservo cio' che sta prima della prima voce e dopo
    #     l'ultima (indentazione iniziale ed eventuale riga vuota prima di ')').
    if quotes:
        leading = body[:quotes[0].start()]
        trailing = body[quotes[-1].end():]
        sep = "\n" + indent
        new_body = leading + sep.join(f"'{ent}'" for ent in new_entries) + trailing
    else:
        # array originariamente vuoto: layout normalizzato di default
        new_body = "\n" + "\n".join(f"{indent}'{ent}'" for ent in new_entries) + "\n"

    new_text = ps1_text[:m.start()] + head + new_body + tail + ps1_text[m.end():]

    msgs.extend(changes)
    if kept_extra:
        msgs.append(f"    PS1: preservate voci extra: {', '.join(kept_extra)}")
    msgs.append(f"    PS1: {len(new_entries)} voci totali nell'array $Deps.")
    return new_text, msgs


def run_sync(toml_path, targets, preview=False):
    """
    targets: dict con chiavi opzionali 'vbs', 'ps1' -> Path.
    preview: se True non scrive nulla.
    Restituisce lista di righe di log.
    """
    log = []
    version, raw_deps = load_pyproject(toml_path)
    log.append(f"pyproject : {toml_path}")
    log.append(f"Versione  : {version}")
    log.append(f"Dipendenze: {len(raw_deps)} -> "
               f"{', '.join(dep_name(d) for d in raw_deps)}")
    log.append("")

    def write(path, content):
        if preview:
            log.append(f"  [ANTEPRIMA] non scritto: {path}")
        else:
            Path(path).write_text(content, encoding="utf-8")
            log.append(f"  scritto: {path}")

    # VBS
    p = targets.get("vbs")
    if p:
        if p.exists():
            original = p.read_text(encoding="utf-8")
            new_text, msgs = sync_vbs_text(original, version, raw_deps)
            log.extend(msgs)
            if new_text == original:
                log.append(f"  invariato (non riscritto): {p}")
            else:
                write(p, new_text)
        else:
            log.append(f"  ATTENZIONE: VBS non trovato: {p}")

    # PS1
    p = targets.get("ps1")
    if p:
        if p.exists():
            original = p.read_text(encoding="utf-8")
            new_text, msgs = sync_ps1_text(original, raw_deps)
            log.extend(msgs)
            if new_text == original:
                log.append(f"  invariato (non riscritto): {p}")
            else:
                write(p, new_text)
        else:
            log.append(f"  ATTENZIONE: PS1 non trovato: {p}")

    log.append("")
    log.append("Anteprima completata (nessun file modificato)." if preview
               else "Fatto.")
    return log


def diff_ps1_versions(toml_path, ps1_path):
    """
    Confronta le versioni delle dipendenze tra pyproject.toml e l'array
    $Deps di Build-Portable.ps1 (i marker vengono valutati per Windows, come
    fa la sincronizzazione). Non modifica nulla: restituisce solo righe di log.

    Per ogni dipendenza segnala uno di questi stati:
      - coincide          : stessa specifica in entrambi
      - diversa           : specifica differente (mostra pyproject | PS1)
      - solo in pyproject : presente in pyproject ma assente dal PS1
      - solo in PS1       : voce extra del PS1 (es. cx_Freeze), non in pyproject
      - marker non-Windows: esclusa su Windows dal marker di pyproject
    """
    log = []
    _version, raw_deps = load_pyproject(toml_path)

    # pyproject: nome normalizzato -> spec Windows (marker rimosso) o None se
    # esclusa su Windows; disp conserva il nome con il case originale.
    pyproj = {}
    disp = {}
    order = []
    for d in raw_deps:
        parsed = split_requirement(d)
        if parsed is None:
            continue
        n = dep_name(d)
        pyproj[n] = windows_spec(parsed)
        disp[n] = parsed["name"]
        order.append(n)

    # PS1: estrae l'array $Deps = @( '...' '...' ) e mappa nome -> voce.
    ps1_text = Path(ps1_path).read_text(encoding="utf-8")
    m = re.search(r'\$Deps\s*=\s*@\((.*?)\n[ \t]*\)', ps1_text, re.DOTALL)
    if not m:
        return ["Errore: blocco '$Deps = @(...)' non trovato in "
                "Build-Portable.ps1."]
    ps1_entries = [e.strip() for e in re.findall(r"'([^']*)'", m.group(1))]
    ps1_map = {dep_name(e): e for e in ps1_entries}
    for e in ps1_entries:
        n = dep_name(e)
        if n not in disp:
            p = split_requirement(e)
            disp[n] = p["name"] if p else e

    log.append(f"pyproject          : {toml_path}")
    log.append(f"Build-Portable.ps1 : {ps1_path}")
    log.append("Confronto versioni dipendenze (marker valutati per Windows)")
    log.append("")

    n_equal = n_diff = n_only_py = n_only_ps1 = n_excluded = 0

    # ordine: prima le dipendenze di pyproject, poi le voci extra del PS1.
    names = list(order)
    for n in ps1_map:
        if n not in pyproj:
            names.append(n)

    ABSENT = object()
    for n in names:
        py_spec = pyproj.get(n, ABSENT)
        ps1_entry = ps1_map.get(n)
        name = disp.get(n, n)

        # esclusa su Windows dal marker di pyproject
        if py_spec is None:
            if ps1_entry is not None:
                log.append(f"    {name:<16} marker non-Windows: presente nel "
                           f"PS1 ({ps1_entry}), andrebbe rimossa.")
            else:
                log.append(f"    {name:<16} marker non-Windows: assente da "
                           f"entrambi, ok.")
            n_excluded += 1
            continue

        # solo in pyproject (mancante nel PS1)
        if py_spec is not ABSENT and ps1_entry is None:
            log.append(f"    {name:<16} solo in pyproject: '{py_spec}' "
                       f"(assente dal PS1).")
            n_only_py += 1
            continue

        # solo nel PS1 (voce extra, es. cx_Freeze)
        if py_spec is ABSENT and ps1_entry is not None:
            log.append(f"    {name:<16} solo in PS1: '{ps1_entry}' "
                       f"(voce extra, non in pyproject).")
            n_only_ps1 += 1
            continue

        # presente in entrambi: confronto della specifica
        if py_spec == ps1_entry:
            log.append(f"    {name:<16} coincide: '{py_spec}'.")
            n_equal += 1
        else:
            log.append(f"    {name:<16} diversa: pyproject '{py_spec}'  |  "
                       f"PS1 '{ps1_entry}'.")
            n_diff += 1

    log.append("")
    log.append(f"Riepilogo: {n_diff} diverse, {n_equal} coincidono, "
               f"{n_only_py} solo in pyproject, {n_only_ps1} solo in PS1, "
               f"{n_excluded} escluse (non-Windows).")
    if n_diff == 0 and n_only_py == 0 and n_excluded == 0:
        log.append("Nessuna differenza rilevante: PS1 allineato a pyproject.")
    return log


# ─────────────────────────────────────────────────────────────────────────────
#  GUI
# ─────────────────────────────────────────────────────────────────────────────

#  Colori e simboli del log
LOG_STYLE_LIGHT = {
    "ok":      (wx.Colour(0x1A, 0x7F, 0x37), "\u2713"),  # ✓ verde
    "warn":    (wx.Colour(0xB0, 0x6A, 0x00), "!"),        # ! ambra
    "error":   (wx.Colour(0xC0, 0x2B, 0x2B), "\u2717"),  # ✗ rosso
    "change":  (wx.Colour(0x1F, 0x5F, 0xBF), "\u00BB"),  # » blu
    "add":     (wx.Colour(0x1F, 0x5F, 0xBF), "+"),        # + blu
    "head":    (wx.Colour(0x33, 0x33, 0x33), "\u2022"),  # • grigio scuro
    "info":    (wx.Colour(0x55, 0x55, 0x55), "\u00B7"),  # · grigio
    "muted":   (wx.Colour(0x88, 0x88, 0x88), "\u25CB"),  # ○ grigio chiaro
    "plain":   (wx.Colour(0x33, 0x33, 0x33), ""),
}

# Retrocompatibilità: alcuni riferimenti storici usano LOG_STYLE.
LOG_STYLE = LOG_STYLE_LIGHT


# ─────────────────────────────────────────────────────────────────────────────
#  PREFERENZE (tema, dimensione testo, carattere) + persistenza JSON
# ─────────────────────────────────────────────────────────────────────────────

PREFS_FILENAME = "sync_deps_gui.prefs.json"

FONT_SIZE_MIN = 9
FONT_SIZE_MAX = 18

DEFAULT_FONT_SIZE = 10        # int
DEFAULT_FONT_FAMILY = ""      # str ("" = monospazio predefinito)

DEFAULT_PREFS = {
    "font_size": DEFAULT_FONT_SIZE,      # tra FONT_SIZE_MIN e FONT_SIZE_MAX
    "font_family": DEFAULT_FONT_FAMILY,  # "" oppure face name del carattere
}


def prefs_path():
    """File JSON delle preferenze, salvato ACCANTO a questo script."""
    try:
        base = Path(__file__).resolve().parent
    except NameError:  # __file__ assente (es. ambiente interattivo)
        base = Path.cwd()
    return base / PREFS_FILENAME


def load_prefs():
    """Carica le preferenze dal JSON con default e validazione (clamp)."""
    raw = {}
    try:
        parsed = json.loads(prefs_path().read_text(encoding="utf-8"))
        if isinstance(parsed, dict):
            raw = parsed
    except (OSError, ValueError):
        pass  # file assente o non valido -> si usano i default

    # font_size: intero nell'intervallo consentito, altrimenti default
    size = DEFAULT_FONT_SIZE
    val = raw.get("font_size", DEFAULT_FONT_SIZE)
    if isinstance(val, (int, float, str)):
        try:
            size = int(val)
        except ValueError:
            size = DEFAULT_FONT_SIZE
    size = max(FONT_SIZE_MIN, min(FONT_SIZE_MAX, size))

    # font_family: stringa, altrimenti stringa vuota
    family = raw.get("font_family", DEFAULT_FONT_FAMILY)
    if not isinstance(family, str):
        family = DEFAULT_FONT_FAMILY

    return {"font_size": size, "font_family": family}


def save_prefs(prefs):
    """Salva le preferenze nel JSON, creando la cartella se necessario."""
    path = prefs_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {k: prefs.get(k, DEFAULT_PREFS[k]) for k in DEFAULT_PREFS}
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def build_log_font(family, size_pt):
    """Font del log: face 'family' (o monospazio predefinito) a 'size_pt' punti."""
    info = wx.FontInfo(int(size_pt)).Family(wx.FONTFAMILY_TELETYPE)
    if family:
        info = info.FaceName(family)
    return wx.Font(info)


def classify_log_line(line):
    """Mappa una riga di log a (livello, testo_pulito)."""
    s = line.strip()
    if s == "":
        return "plain", ""
    low = s.lower()
    if low.startswith("errore") or "errore durante" in low:
        return "error", s
    if "attenzione" in low or "non trovato" in low or "non parsabile" in low:
        return "warn", s
    if any(k in low for k in ("esclusa", "ignorata", "saltato", "rimosso",
                              "upper-bound")):
        return "warn", s
    if low.startswith("scritto:"):
        return "ok", s
    if low.startswith("invariato") or "gia' allineato" in low or "già allineato" in low:
        return "muted", s
    if "[anteprima]" in low:
        return "muted", s
    # messaggio automatico di ricerca file (pyproject/vbs/ps1)
    if low.startswith("ricerca file"):
        return "head", s
    if low.startswith("trovato:") or low.startswith("tutti i file trovati"):
        return "ok", s
    if low.startswith("mancante:") or low.startswith("alcuni file"):
        return "warn", s
    # righe del confronto versioni (pulsante "Mostra differenze").
    # Il riepilogo e le intestazioni vanno controllati per primi: contengono
    # sottostringhe (es. "solo in pyproject") che matcherebbero le righe di voce.
    if low.startswith("riepilogo") or "nessuna differenza" in low:
        return "ok", s
    if low.startswith("build-portable.ps1") or low.startswith("confronto vers"):
        return "head", s
    if "marker non-windows" in low:
        return "warn", s
    if "diversa:" in low:
        return "change", s
    if "solo in pyproject" in low:
        return "add", s
    if "solo in ps1" in low:
        return "info", s
    if "coincide:" in low:
        return "muted", s
    if low.startswith("fatto") or "anteprima completata" in low:
        return "ok", s
    if "aggiornato" in low:
        return "change", s
    if "aggiunto" in low:
        return "add", s
    if low.startswith(("vbs:", "ps1:")):
        return "info", s
    if low.startswith(("pyproject", "versione", "dipendenze")):
        return "head", s
    return "plain", s


class PreferencesDialog(wx.Dialog):
    """Finestra Preferenze: dimensione testo e carattere del log.

    get_prefs() restituisce un dict con le chiavi font_size/font_family.
    """

    MONO_DEFAULT_LABEL = "(monospazio predefinito)"

    def __init__(self, parent, prefs):
        super().__init__(parent, title="Preferenze",
                         style=wx.DEFAULT_DIALOG_STYLE)

        outer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(rows=2, cols=2, vgap=10, hgap=12)
        grid.AddGrowableCol(1, 1)

        # Dimensione testo
        grid.Add(wx.StaticText(self, label="Dimensione testo:"), 0,
                 wx.ALIGN_CENTER_VERTICAL)
        self.sp_size = wx.SpinCtrl(self, min=FONT_SIZE_MIN, max=FONT_SIZE_MAX,
                                   initial=int(prefs.get("font_size", 10)))
        grid.Add(self.sp_size, 0)

        # Carattere
        grid.Add(wx.StaticText(self, label="Carattere:"), 0,
                 wx.ALIGN_CENTER_VERTICAL)
        faces = self._available_faces()
        self.ch_font = wx.Choice(self, choices=faces)
        cur_face = prefs.get("font_family", "") or self.MONO_DEFAULT_LABEL
        self.ch_font.SetSelection(faces.index(cur_face)
                                  if cur_face in faces else 0)
        grid.Add(self.ch_font, 0, wx.EXPAND)

        outer.Add(grid, 1, wx.EXPAND | wx.ALL, 14)

        hint = wx.StaticText(
            self,
            label="Le preferenze vengono salvate e riapplicate all'avvio.")
        hint.SetForegroundColour(wx.Colour(0x77, 0x77, 0x77))
        outer.Add(hint, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)

        btns = self.CreateButtonSizer(wx.OK | wx.CANCEL)
        if btns:
            outer.Add(btns, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.SetSizerAndFit(outer)
        self.Centre()

    def _available_faces(self):
        try:
            faces = sorted(set(wx.FontEnumerator.GetFacenames()))
        except Exception:  # noqa: BLE001
            faces = []
        return [self.MONO_DEFAULT_LABEL] + faces

    def get_prefs(self):
        face = self.ch_font.GetStringSelection()
        if face == self.MONO_DEFAULT_LABEL:
            face = ""
        return {
            "font_size": int(self.sp_size.GetValue()),
            "font_family": face,
        }


class SyncFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Sync deps — Songpress++",
                         size=(880, 620))
        self.SetMinSize((640, 420))

        # Preferenze (tema, dimensione testo, carattere) da file JSON.
        self.prefs = load_prefs()
        # Palette log corrente (impostata da _apply_appearance); default chiaro.
        self.log_style = LOG_STYLE_LIGHT
        # Ultime righe mostrate: servono per ridisegnare il log quando cambia
        # il tema o il carattere senza rilanciare l'operazione.
        self._last_lines = []

        # Barra dei menu: File > Preferenze… / Esci
        menubar = wx.MenuBar()
        file_menu = wx.Menu()
        prefs_item = file_menu.Append(wx.ID_PREFERENCES, "Preferenze…\tCtrl+,",
                                      "Dimensione testo e carattere del log")
        file_menu.AppendSeparator()
        exit_item = file_menu.Append(wx.ID_EXIT, "Esci\tCtrl+Q",
                                     "Chiudi il programma")
        menubar.Append(file_menu, "&File")

        help_menu = wx.Menu()
        about_item = help_menu.Append(wx.ID_ABOUT, "Informazioni…",
                                      "Versione, guida e licenza")
        menubar.Append(help_menu, "&?")

        self.SetMenuBar(menubar)
        self.Bind(wx.EVT_MENU, self.on_prefs, prefs_item)
        self.Bind(wx.EVT_MENU, self.on_exit, exit_item)
        self.Bind(wx.EVT_MENU, self.on_about, about_item)

        panel = wx.Panel(self)
        self.panel = panel
        outer = wx.BoxSizer(wx.VERTICAL)

        # Righe percorsi
        grid = wx.FlexGridSizer(rows=4, cols=4, vgap=6, hgap=6)
        grid.AddGrowableCol(1, 1)

        self.rows = {}
        # Stato "trovato/mancante" dell'ultima ricerca file, per non ridisegnare
        # il log a ogni tasto: il messaggio automatico compare solo quando lo
        # stato cambia davvero (None = mai calcolato, così la prima volta stampa).
        self._last_found = None
        self._add_row(grid, "Cartella progetto", "root",
                      with_check=False, picker="dir")
        self._add_row(grid, "pyproject.toml", "toml", with_check=False)
        self._add_row(grid, "install_check.vbs", "vbs")
        self._add_row(grid, "Build-Portable.ps1", "ps1")

        outer.Add(grid, 0, wx.EXPAND | wx.ALL, 10)

        # Opzioni
        opt = wx.BoxSizer(wx.HORIZONTAL)
        self.chk_preview = wx.CheckBox(panel, label="Solo anteprima (non scrive)")
        opt.Add(self.chk_preview, 0, wx.ALIGN_CENTER_VERTICAL)
        opt.AddStretchSpacer()
        btn_diff = wx.Button(panel, label="Mostra differenze")
        btn_diff.SetToolTip("Confronta le versioni delle dipendenze tra "
                            "pyproject.toml e Build-Portable.ps1 (non scrive).")
        btn_diff.Bind(wx.EVT_BUTTON, self.on_diff)
        opt.Add(btn_diff, 0)
        opt.Add((8, 0))
        btn_sync = wx.Button(panel, label="Sincronizza")
        btn_sync.Bind(wx.EVT_BUTTON, self.on_sync)
        opt.Add(btn_sync, 0)
        outer.Add(opt, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # Log (TE_RICH2 abilita i colori su Windows; su GTK i colori
        # funzionano comunque via SetDefaultStyle)
        self.log = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_DONTWRAP | wx.TE_RICH2,
        )
        self.log.SetFont(wx.Font(wx.FontInfo(10).Family(wx.FONTFAMILY_TELETYPE)))
        outer.Add(self.log, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        panel.SetSizer(outer)

        self._prefill_from_cwd()
        self.Centre()

        # Applica dimensione/carattere del log dalle preferenze salvate.
        self._apply_appearance()

    # --- costruzione righe --------------------------------------------------
    def _add_row(self, grid, label, key, with_check=True, picker="file"):
        panel = self.panel
        lbl = wx.StaticText(panel, label=label)
        txt = wx.TextCtrl(panel, size=(420, -1))
        txt.Bind(wx.EVT_TEXT, lambda e, k=key: self._on_text(k))
        btn = wx.Button(panel, label="Sfoglia…")
        btn.Bind(wx.EVT_BUTTON, lambda e, k=key: self.on_browse(k))
        if with_check:
            chk = wx.CheckBox(panel, label="")
            chk.SetValue(True)
        else:
            chk = None  # cella vuota per allineare la griglia
        grid.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL)
        grid.Add(txt, 1, wx.EXPAND)
        grid.Add(btn, 0)
        if chk is not None:
            grid.Add(chk, 0, wx.ALIGN_CENTER_VERTICAL)
        else:
            grid.Add((0, 0))
        self.rows[key] = {"txt": txt, "chk": chk, "picker": picker}

    # --- helpers ------------------------------------------------------------
    def _update_tooltip(self, key):
        txt = self.rows[key]["txt"]
        txt.SetToolTip(txt.GetValue() or "")

    def _set_path(self, key, value):
        """Imposta il percorso senza generare EVT_TEXT, vista all'inizio."""
        txt = self.rows[key]["txt"]
        txt.ChangeValue(str(value))
        txt.SetInsertionPoint(0)
        self._update_tooltip(key)

    def _on_text(self, key):
        """Digitazione manuale: aggiorna tooltip e ricalcola i derivati."""
        self._update_tooltip(key)
        if key == "root":
            val = self.rows["root"]["txt"].GetValue().strip()
            if val:
                self._apply_root(Path(val))
        elif key == "toml":
            val = self.rows["toml"]["txt"].GetValue().strip()
            if val:
                self._derive_paths(Path(val))

    def _apply_root(self, root):
        """Dalla cartella progetto: trova pyproject.toml e deriva il resto."""
        toml = root / "pyproject.toml"
        self._set_path("toml", toml)
        self._derive_paths(toml)

    # --- prefill ------------------------------------------------------------
    def _prefill_from_cwd(self):
        cwd = Path.cwd()
        self._set_path("root", cwd)
        self._apply_root(cwd)

    def _derive_paths(self, toml_path):
        root = Path(toml_path).parent
        self._set_path("vbs", root / "src" / "install_check.vbs")
        self._set_path("ps1", root / "installer" / "Build-Portable.ps1")
        self._report_paths_status()

    def _report_paths_status(self):
        """
        Mostra automaticamente nel log quali dei tre file del progetto sono
        stati trovati (pyproject.toml, install_check.vbs, Build-Portable.ps1).

        Per non ridisegnare il log a ogni carattere digitato, il messaggio
        viene (ri)stampato solo quando lo stato trovato/mancante cambia rispetto
        alla volta precedente: così, digitando un percorso, il messaggio compare
        nell'istante in cui i file iniziano (o smettono) di essere trovati.
        """
        checks = [
            ("pyproject.toml", "toml"),
            ("install_check.vbs", "vbs"),
            ("Build-Portable.ps1", "ps1"),
        ]
        paths = {key: self.rows[key]["txt"].GetValue().strip()
                 for _, key in checks}
        state = tuple(bool(paths[key]) and Path(paths[key]).is_file()
                      for _, key in checks)

        if state == self._last_found:
            return
        self._last_found = state

        lines = ["Ricerca file del progetto:"]
        for (label, key), found in zip(checks, state):
            p = paths[key]
            if found:
                lines.append(f"    trovato: {label:<20} -> {p}")
            else:
                where = p if p else "(percorso vuoto)"
                lines.append(f"    mancante: {label:<19} {where}")
        lines.append("")
        if all(state):
            lines.append("Tutti i file trovati: pronto per "
                         "\u201cMostra differenze\u201d o \u201cSincronizza\u201d.")
        else:
            lines.append("Alcuni file non sono stati trovati: verifica la "
                         "Cartella progetto (deve contenere pyproject.toml).")
        self._render_log(lines)

    # --- browse -------------------------------------------------------------
    def on_browse(self, key):
        if self.rows[key]["picker"] == "dir":
            current = self.rows[key]["txt"].GetValue().strip()
            start = current if current and Path(current).is_dir() else str(Path.cwd())
            with wx.DirDialog(self, "Seleziona la cartella del progetto",
                              defaultPath=start) as dlg:
                if dlg.ShowModal() == wx.ID_OK:
                    self._set_path(key, dlg.GetPath())
                    self._apply_root(Path(dlg.GetPath()))
            return

        wildcard = {
            "toml": "TOML (*.toml)|*.toml|Tutti|*.*",
            "vbs":  "VBScript (*.vbs)|*.vbs|Tutti|*.*",
            "ps1":  "PowerShell (*.ps1)|*.ps1|Tutti|*.*",
        }[key]
        current = self.rows[key]["txt"].GetValue().strip()
        start_dir = str(Path(current).parent) if current else str(Path.cwd())
        with wx.FileDialog(
            self, f"Seleziona {key}", defaultDir=start_dir, wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST if key == "toml"
            else wx.FD_OPEN,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                self._set_path(key, dlg.GetPath())
                if key == "toml":
                    self._derive_paths(Path(dlg.GetPath()))

    # --- log colorato -------------------------------------------------------
    def _render_log(self, lines):
        self._last_lines = list(lines)
        style = getattr(self, "log_style", LOG_STYLE)
        font = getattr(self, "log_font", None)

        def _attr(colour):
            attr = wx.TextAttr(colour)
            if font is not None:
                attr.SetFont(font)
            return attr

        self.log.SetValue("")
        for line in lines:
            level, text = classify_log_line(line)
            colour, symbol = style[level]
            self.log.SetDefaultStyle(_attr(colour))
            if text == "":
                self.log.AppendText("\n")
            else:
                prefix = f"{symbol}  " if symbol else "   "
                self.log.AppendText(prefix + text + "\n")
        self.log.SetDefaultStyle(_attr(style["plain"][0]))
        self.log.ShowPosition(0)

    # --- aspetto (carattere del log) ----------------------------------------
    def _apply_appearance(self):
        """Applica dimensione e carattere correnti al log e ridisegna."""
        self.log_font = build_log_font(self.prefs.get("font_family", ""),
                                       self.prefs.get("font_size", 10))
        self.log.SetFont(self.log_font)
        self.log.Refresh()
        self._render_log(self._last_lines)

    def on_prefs(self, _evt):
        dlg = PreferencesDialog(self, self.prefs)
        try:
            if dlg.ShowModal() == wx.ID_OK:
                self.prefs = dlg.get_prefs()
                try:
                    save_prefs(self.prefs)
                except OSError as exc:  # noqa: BLE001
                    self._error(f"Impossibile salvare le preferenze: {exc}")
                self._apply_appearance()
        finally:
            dlg.Destroy()

    # --- diff versioni ------------------------------------------------------
    def on_diff(self, _evt):
        """Confronta le versioni delle dipendenze pyproject.toml <-> PS1.

        È di sola lettura: non serve spuntare il target PS1 e non scrive nulla.
        """
        toml_path = Path(self.rows["toml"]["txt"].GetValue().strip())
        ps1_path = Path(self.rows["ps1"]["txt"].GetValue().strip())
        if not toml_path.exists():
            self._error(f"pyproject.toml non trovato: {toml_path}")
            return
        if not ps1_path.exists():
            self._error(f"Build-Portable.ps1 non trovato: {ps1_path}")
            return
        try:
            log = diff_ps1_versions(toml_path, ps1_path)
        except Exception as exc:  # noqa: BLE001
            self._error(f"Errore durante il confronto: {exc}")
            return
        self._render_log(log)

    # --- sync ---------------------------------------------------------------
    def on_sync(self, _evt):
        toml_path = Path(self.rows["toml"]["txt"].GetValue().strip())
        if not toml_path.exists():
            self._error(f"pyproject.toml non trovato: {toml_path}")
            return

        targets = {}
        for key in ("vbs", "ps1"):
            row = self.rows[key]
            if row["chk"] is not None and row["chk"].GetValue():
                val = row["txt"].GetValue().strip()
                if val:
                    targets[key] = Path(val)

        if not targets:
            self._error("Nessun target selezionato.")
            return

        preview = self.chk_preview.GetValue()
        try:
            log = run_sync(toml_path, targets, preview=preview)
        except Exception as exc:  # noqa: BLE001
            self._error(f"Errore durante la sincronizzazione: {exc}")
            return

        self._render_log(log)

    def _error(self, message):
        self._render_log([f"Errore: {message}"])
        wx.MessageBox(message, "Errore", wx.OK | wx.ICON_ERROR)

    def on_exit(self, _evt):
        self.Close()

    def on_about(self, _evt):
        info = wx.adv.AboutDialogInfo()
        info.SetName(TOOL_NAME)
        info.SetVersion(TOOL_VERSION)
        info.SetDescription(ABOUT_DESCRIPTION)
        info.SetCopyright("(C) 2026 Denis — progetto Songpress++")
        info.SetLicense(LICENSE_TEXT)
        if PROJECT_URL:
            info.SetWebSite(PROJECT_URL, "Repository del progetto")
        wx.adv.AboutBox(info, self)


def main():
    app = wx.App(False)
    frame = SyncFrame()
    frame.Show()
    app.MainLoop()


if __name__ == "__main__":
    main()
