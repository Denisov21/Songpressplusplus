# coding: utf-8

###############################################################
# Name:        UpdateChecker.py
# Purpose:     Controllo aggiornamenti di Songpress++ (Windows e Linux)
# Author:      Denisov21 (https://github.com/Denisov21/Songpressplusplus)
# License:     GNU GPL v2
##############################################################
"""Controlla se su GitHub e' stata pubblicata una versione piu' recente.

Mostra solo un messaggio di avviso: non scarica ne' installa nulla.

La parte di logica (parse_version, compare_versions, fetch_latest_version) non
dipende da wx e si puo' provare da sola; wx serve solo a check_for_updates(),
che mostra il messaggio.
"""

import json
import platform
import re
import sys
import threading
import urllib.request

REPO_URL = u"https://github.com/Denisov21/Songpressplusplus"
RELEASES_API = u"https://api.github.com/repos/Denisov21/Songpressplusplus/releases/latest"
TAGS_API = u"https://api.github.com/repos/Denisov21/Songpressplusplus/tags"
TIMEOUT = 10  # secondi

# Esiti di compare_versions()
NEWER_AVAILABLE = 'newer_available'   # su GitHub c'e' una versione piu' recente
UP_TO_DATE = 'up_to_date'             # stessa versione
AHEAD = 'ahead'                       # la versione installata e' piu' recente di quella pubblicata
UNKNOWN = 'unknown'                   # una delle due non ha un numero (es. 'dev')


def _(text):
    """Traduzione via wx, importato solo quando serve (cosi' il resto del
    modulo funziona anche senza wx). Il nome '_' e' quello che gli strumenti
    di estrazione (Poedit, xgettext) cercano."""
    import wx
    return wx.GetTranslation(text)


# ----------------------------------------------------------------------
# Logica (senza wx)
# ----------------------------------------------------------------------

def parse_version(v):
    """'v8.0.2' / '8.0.2rc1' / 'V2.0.0' -> (8, 0, 2, 0); None se non c'e'
    un numero di versione (es. 'dev'). Il tuple e' completato a 4 numeri,
    cosi' (8, 0) e (8, 0, 0) risultano uguali; un eventuale suffisso
    (rc1, -beta...) e' ignorato."""
    m = re.match(r'\s*[vV]?(\d+(?:\.\d+)*)', str(v))
    if not m:
        return None
    nums = [int(n) for n in m.group(1).split('.')]
    while len(nums) < 4:
        nums.append(0)
    return tuple(nums)


def compare_versions(installed, latest):
    cur, new = parse_version(installed), parse_version(latest)
    if cur is None or new is None:
        return UNKNOWN
    if new > cur:
        return NEWER_AVAILABLE
    if new == cur:
        return UP_TO_DATE
    return AHEAD


def get_architecture(machine=None, is_64bit=None):
    """Architettura del programma installato, come testo breve:
    '64 bit' o 'x86 (32 bit)' sui PC; per altre CPU (es. Raspberry Pi)
    '<cpu> (<bit> bit)', ad esempio 'aarch64 (64 bit)'.

    Si basa su Python in esecuzione, cioe' sul programma installato, non sul
    sistema operativo: un'installazione x86 su Windows a 64 bit risulta x86.
    """
    if is_64bit is None:
        is_64bit = sys.maxsize > 2 ** 32
    bits = 64 if is_64bit else 32
    raw = machine if machine is not None else platform.machine()
    if raw.lower() in ('', 'amd64', 'x86_64', 'x64', 'x86', 'i386', 'i486', 'i586', 'i686'):
        return u"64 bit" if bits == 64 else u"x86 (32 bit)"
    return u"{} ({} bit)".format(raw, bits)


def version_with_architecture(version):
    """'8.1.0' -> '8.1.0 (64 bit)'."""
    return u"{} ({})".format(version, get_architecture())


def pick_asset(assets, system=None, is_64bit=None):
    """Sceglie tra i file della release quello adatto a questo computer.

    Windows: l'installer .exe a 64 bit oppure x86, in base ai bit di Python
    (cioe' del programma in esecuzione); se manca quello giusto ripiega
    sull'altro .exe. Linux: il pacchetto .deb. Altri sistemi: nessun file
    (None). Ritorna il dict dell'asset oppure None.
    """
    system = system or platform.system()
    if is_64bit is None:
        is_64bit = sys.maxsize > 2 ** 32
    names = [(a, a['name'].lower()) for a in assets]
    if system == 'Windows':
        exes = [(a, n) for a, n in names if n.endswith('.exe')]
        for a, n in exes:
            if is_64bit and '64' in n:
                return a
            if not is_64bit and ('x86' in n or '32' in n) and '64' not in n:
                return a
        return exes[0][0] if exes else None
    if system == 'Linux':
        for a, n in names:
            if n.endswith('.deb'):
                return a
    return None


def _get_json(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Songpress++ update check',
        'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode('utf-8'))


def fetch_latest_version():
    """Restituisce (tag, url_pagina, assets) dell'ultima versione pubblicata;
    `assets` e' la lista dei file allegati alla release ([{'name', 'url'}]).
    Usa l'ultima release; se il repository non ne ha (404) ripiega sul tag
    con il numero piu' alto (senza file). Solleva un'eccezione se la rete
    non risponde."""
    try:
        d = _get_json(RELEASES_API)
        assets = [{'name': a.get('name', ''), 'url': a.get('browser_download_url', '')}
                  for a in d.get('assets', []) if a.get('name')]
        return d['tag_name'], d.get('html_url') or REPO_URL, assets
    except Exception as e:
        if getattr(e, 'code', None) != 404:
            raise
    best = None
    for t in _get_json(TAGS_API):
        pv = parse_version(t.get('name', ''))
        if pv is not None and (best is None or pv > best[0]):
            best = (pv, t['name'])
    if best is None:
        raise ValueError("no versions found")
    return best[1], REPO_URL, []


# ----------------------------------------------------------------------
# Interfaccia (wx)
# ----------------------------------------------------------------------

def build_message(installed, result):
    """Costruisce (testo, icona_è_warning) per il messaggio da mostrare.
    `result` e' (True, tag, url, assets) oppure (False, errore, None, None)."""
    ok, info, url, assets = result
    shown = version_with_architecture(installed)
    if not ok:
        return (_(u"Could not check for updates.\nCheck your Internet connection and try again.")
                + u"\n\n" + info), True
    outcome = compare_versions(installed, info)
    if outcome == NEWER_AVAILABLE:
        text = _(u"A new version of Songpress++ is available!\n\nInstalled version: {cur}\nLatest version: {new}\n\nDownload it from:\n{url}").format(
            cur=shown, new=info, url=url)
        asset = pick_asset(assets or [])
        if asset:
            text += u"\n\n" + _(u"File to download for your system:\n{file}").format(file=asset['name'])
        return text, False
    if outcome == UP_TO_DATE:
        return _(u"Songpress++ is up to date.\n\nInstalled version: {cur}").format(
            cur=shown), False
    if outcome == AHEAD:
        return _(u"Your version is newer than the latest published release.\n\nInstalled version: {cur}\nLatest published version: {new}").format(
            cur=shown, new=info), False
    return _(u"Installed version: {cur}\nLatest version: {new}\n\n{url}").format(
        cur=shown, new=info, url=url), False


def check_for_updates(parent, installed_version, status_bar=None):
    """Avvia il controllo in un thread (l'interfaccia non si blocca) e al
    termine mostra un solo messaggio di avviso."""
    import wx

    def show(result):
        try:
            if status_bar:
                status_bar.SetStatusText(u"")
        except Exception:
            pass
        text, warning = build_message(installed_version, result)
        wx.MessageBox(text, _(u"Check for updates"),
                      wx.OK | (wx.ICON_WARNING if warning else wx.ICON_INFORMATION),
                      parent)

    def worker():
        try:
            tag, url, assets = fetch_latest_version()
            result = (True, tag, url, assets)
        except Exception as e:
            result = (False, str(e), None, None)
        wx.CallAfter(show, result)

    if status_bar:
        status_bar.SetStatusText(_(u"Checking for updates..."))
    threading.Thread(target=worker, daemon=True).start()
