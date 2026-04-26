###############################################################################
# Name: errdlg.py                                                             #
# Purpose: Error Reporter Dialog                                              #
# Author: Denisov21                                                           #
# Copyright: © 2026 Denisov21                                                 #
# License: GNU GPL v2                                                         #
###############################################################################

"""
Error reporter dialog per Songpress++.

Grafica uniforme al dialog di errore immagine:
  - Intestazione: icona ART_ERROR + messaggio breve
  - Sezione collassabile «Dettagli» con wx.CollapsiblePane
  - Lista errori con colonna icona, messaggio e timestamp (wx.ListCtrl)
  - Bottoni: «Forza chiusura» (sinistra) | «Copia» «Invia rapporto d'errore» «Chiudi» (destra)

Collegare in main.py:
    from songpress.errdlg import ExceptionHook
    sys.excepthook = ExceptionHook

Collegare in SongpressApp.OnInit():
    errdlg.install_wx_exception_handler(self)
"""

import os
import sys
import platform
import time
import traceback

import wx

__all__ = ['ExceptionHook', 'install_wx_exception_handler', 'SongpressErrorDialog']

_ = wx.GetTranslation

# ---------------------------------------------------------------------------
# Lettura nome/versione da pyproject.toml
# ---------------------------------------------------------------------------

def _read_pyproject():
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            return None, None
    base = os.path.dirname(os.path.abspath(__file__))
    for _ in range(4):
        candidate = os.path.join(base, 'pyproject.toml')
        if os.path.isfile(candidate):
            try:
                with open(candidate, 'rb') as f:
                    data = tomllib.load(f)
                p = data.get('project', {})
                return p.get('name'), p.get('version')
            except Exception:
                return None, None
        base = os.path.dirname(base)
    return None, None


_PROG_NAME, _PROG_VERSION = _read_pyproject()
_PROG_NAME    = _PROG_NAME    or "Songpress++"
_PROG_VERSION = _PROG_VERSION or ""


def _get_glb():
    try:
        from .Globals import glb
        return glb
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Dialog
# ---------------------------------------------------------------------------

class SongpressErrorDialog(wx.Dialog):
    """
    Dialog per errori imprevisti in Songpress++.

    Grafica identica al dialog di errore immagine:
      - Riga superiore: icona ART_ERROR + testo breve
      - CollapsiblePane «Dettagli» con ListCtrl (icona | messaggio | ora)
      - Bottoni: Forza chiusura  ·  Copia  Invia rapporto  Chiudi
    """

    ABORT           = False
    REPORTER_ACTIVE = False

    _ID_SEND = wx.NewIdRef()

    def __init__(self, message: str):
        glb  = _get_glb()
        prog = glb.PROG_NAME if glb else _PROG_NAME

        super().__init__(
            None,
            title=_("Errore imprevisto"),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        SongpressErrorDialog.REPORTER_ACTIVE = True

        self._report_text = self._build_report(message)

        # Messaggio breve: ultima riga non vuota del traceback
        lines = [l.strip() for l in message.strip().splitlines() if l.strip()]
        self._short_msg = lines[-1] if lines else message

        self._build_ui(prog)
        self.SetMinSize(wx.Size(540, 200))
        self.Fit()
        # Espandi il CollapsiblePane come il dialog immagine
        self._pane.Expand()
        self._on_pane_changed(None)
        self.SetSize(wx.Size(650, 480))
        self.CentreOnScreen()

        self.Bind(wx.EVT_BUTTON, self._on_button)
        self.Bind(wx.EVT_CLOSE,  self._on_close)

    # ── Costruzione UI ───────────────────────────────────────────────────────

    def _build_ui(self, prog: str):
        # ── Riga intestazione: icona + messaggio breve ──────────────────────
        bmp_err = wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_MESSAGE_BOX, (32, 32))
        icon    = wx.StaticBitmap(self, bitmap=bmp_err)
        lbl     = wx.StaticText(
            self,
            label=_(
                "Si è verificato un errore imprevisto in {prog}.\n"
                "Clicca su «Invia rapporto d'errore» per notificare lo sviluppatore,\n"
                "oppure su «Chiudi» per continuare (il programma potrebbe essere instabile)."
            ).format(prog=prog),
        )
        lbl.Wrap(520)

        hdr = wx.BoxSizer(wx.HORIZONTAL)
        hdr.Add(icon, 0, wx.ALIGN_TOP | wx.RIGHT, 12)
        hdr.Add(lbl,  1, wx.EXPAND)

        # ── CollapsiblePane «Dettagli» ──────────────────────────────────────
        self._pane = wx.CollapsiblePane(
            self,
            label=_("Traceback dell'errore:"),
            style=wx.CP_DEFAULT_STYLE | wx.CP_NO_TLW_RESIZE,
        )
        self._pane.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self._on_pane_changed)

        win = self._pane.GetPane()

        # ListCtrl — colonna unica: messaggio
        self._list = wx.ListCtrl(
            win,
            style=wx.LC_REPORT | wx.BORDER_SUNKEN | wx.LC_NO_HEADER,
        )
        self._list.InsertColumn(0, _("Messaggio"), width=600)

        mono = wx.Font(wx.FontInfo(8).FaceName("Consolas").Family(wx.FONTFAMILY_TELETYPE))
        self._list.SetFont(mono)

        self._populate_list()

        pane_sizer = wx.BoxSizer(wx.VERTICAL)
        pane_sizer.Add(self._list, 1, wx.EXPAND | wx.ALL, 4)
        win.SetSizer(pane_sizer)

        # ── Separatore ─────────────────────────────────────────────────────
        sep = wx.StaticLine(self)

        # ── Bottoni ────────────────────────────────────────────────────────
        btn_abort = wx.Button(self, wx.ID_ABORT,             _("Forza chiusura"))
        btn_copy  = wx.Button(self, wx.ID_COPY,              _("Copia"))
        btn_send  = wx.Button(self, self._ID_SEND.GetId(),   _("Invia rapporto d'errore"))
        btn_close = wx.Button(self, wx.ID_CLOSE,             _("Chiudi"))

        btn_abort.SetToolTip(_("Forza la chiusura immediata dell'applicazione"))
        btn_copy.SetToolTip(_("Copia il testo dell'errore negli appunti"))
        btn_send.SetToolTip(_("Invia il rapporto d'errore allo sviluppatore via e-mail"))
        btn_send.SetDefault()

        btns = wx.BoxSizer(wx.HORIZONTAL)
        btns.Add(btn_abort, 0)
        btns.AddStretchSpacer()
        btns.Add(btn_copy,  0, wx.RIGHT, 6)
        btns.Add(btn_send,  0, wx.RIGHT, 6)
        btns.Add(btn_close, 0)

        # ── Layout radice ───────────────────────────────────────────────────
        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(hdr,        0, wx.EXPAND | wx.ALL,              12)
        root.Add(self._pane, 1, wx.EXPAND | wx.LEFT | wx.RIGHT,   8)
        root.Add(sep,        0, wx.EXPAND | wx.TOP,               6)
        root.Add(btns,       0, wx.EXPAND | wx.ALL,               8)
        self.SetSizer(root)

    def _populate_list(self):
        """Inserisce nella ListCtrl ogni riga significativa del report."""
        for raw in self._report_text.splitlines():
            line = raw.rstrip()
            if not line:
                continue
            idx = self._list.InsertItem(self._list.GetItemCount(), line)
            self._list.SetItem(idx, 0, line)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _build_report(self, traceback_text: str) -> str:
        glb = _get_glb()
        if glb:
            prog_line = f"{glb.PROG_NAME} Version: {glb.VERSION}"
        else:
            prog_line = f"{_PROG_NAME} {_PROG_VERSION}".strip()

        lines = [
            "#---- Notes ----#",
            "Provide additional information about the crash here",
            "",
            "#---- System information ----#",
            prog_line,
            f"OS: {wx.GetOsDescription()}",
            f"Python: {sys.version}",
            f"wxPython: {wx.version()}",
            f"Architecture: {platform.architecture()[0]} {platform.machine()}",
            f"Frozen: {getattr(sys, 'frozen', False)}",
            "#---- End system information ----#",
            "",
            "#---- Traceback ----#",
            traceback_text,
            "#---- End traceback ----#",
        ]
        return os.linesep.join(lines)

    def _on_pane_changed(self, evt):
        """Ridimensiona il dialog quando il CollapsiblePane si espande/chiude."""
        self.Layout()
        self.Fit()
        if evt is not None:
            evt.Skip()

    # ── Handler bottoni ──────────────────────────────────────────────────────

    def _on_button(self, evt):
        eid = evt.GetId()
        if eid == wx.ID_CLOSE:
            self.Close()
        elif eid == self._ID_SEND.GetId():
            self._send()
            self.Close()
        elif eid == wx.ID_COPY:
            self._copy()
        elif eid == wx.ID_ABORT:
            SongpressErrorDialog.ABORT = True
            os._exit(1)
        else:
            evt.Skip()

    def _on_close(self, evt):
        SongpressErrorDialog.REPORTER_ACTIVE = False
        evt.Skip()

    def _copy(self):
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(self._report_text))
            wx.TheClipboard.Close()

    def _send(self):
        from urllib.parse import quote
        import webbrowser
        glb     = _get_glb()
        prog    = f"{glb.PROG_NAME} {glb.VERSION}" if glb else f"{_PROG_NAME} {_PROG_VERSION}".strip()
        addr    = (glb.BUG_REPORT_ADDRESS if glb else "") or ""
        subject = quote(f"Error report - {prog}")
        body    = quote(self._report_text[:1800])
        webbrowser.open(f"mailto:{addr}?subject={subject}&body={body}")


# ---------------------------------------------------------------------------
# Funzione interna condivisa tra i due hook
# ---------------------------------------------------------------------------

def _show_error(ftrace: str) -> None:
    """Mostra il dialog di errore; gestisce App assente e fallback MessageBox."""
    if SongpressErrorDialog.ABORT:
        os._exit(1)

    if SongpressErrorDialog.REPORTER_ACTIVE:
        return

    _owned_app = None
    if wx.GetApp() is None:
        _owned_app = wx.App(False)

    try:
        dlg = SongpressErrorDialog(ftrace)
        dlg.ShowModal()
        dlg.Destroy()
    except Exception:
        wx.MessageBox(ftrace[:2000], _("Errore imprevisto"), wx.OK | wx.ICON_ERROR)
    finally:
        if _owned_app is not None:
            _owned_app.Destroy()


# ---------------------------------------------------------------------------
# Hook 1 — eccezioni fuori dagli event handler wx  (sys.excepthook)
# ---------------------------------------------------------------------------

def ExceptionHook(exctype, value, trace):
    """
    sys.excepthook globale — cattura eccezioni fuori dagli event handler wx.

    Collegare in main():
        sys.excepthook = errdlg.ExceptionHook
    """
    if issubclass(exctype, KeyboardInterrupt):
        sys.__excepthook__(exctype, value, trace)
        return

    ftrace = "*** %s ***%s%s" % (
        time.asctime(),
        os.linesep,
        "".join(traceback.format_exception(exctype, value, trace)),
    )
    print(ftrace, file=sys.stderr)
    _show_error(ftrace)


# ---------------------------------------------------------------------------
# Hook 2 — eccezioni negli event handler wx  (OnExceptionInMainLoop)
# ---------------------------------------------------------------------------

def install_wx_exception_handler(app: wx.App) -> None:
    """
    Installa il handler per eccezioni negli event handler wx.

    Chiamare in SongpressApp.OnInit():
        errdlg.install_wx_exception_handler(self)
    """
    def _on_exception_in_main_loop():
        exctype, value, trace = sys.exc_info()
        if exctype is None:
            return
        ftrace = "*** %s ***%s%s" % (
            time.asctime(),
            os.linesep,
            "".join(traceback.format_exception(exctype, value, trace)),
        )
        print(ftrace, file=sys.stderr)
        _show_error(ftrace)

    app.OnExceptionInMainLoop = _on_exception_in_main_loop
