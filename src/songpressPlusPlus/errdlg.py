###############################################################################
# Name: errdlg.py                                                             #
# Purpose: Error Reporter Dialog                                              #
# Author: Denisov21                                                           #
# Copyright: © 2026 Denisov21                                                 #
# License: GNU GPL v2                                                         #
###############################################################################

"""
Error reporter dialog per Songpress++.

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
    """Dialog per errori imprevisti in Songpress++."""

    ABORT           = False
    REPORTER_ACTIVE = False

    _ID_SEND = wx.NewIdRef()

    def __init__(self, message: str):
        glb  = _get_glb()
        prog = glb.PROG_NAME if glb else _PROG_NAME

        super().__init__(
            None,
            title=_("Unexpected error").format(prog=prog),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )
        SongpressErrorDialog.REPORTER_ACTIVE = True

        err_text = self._build_report(message)

        # ── Layout ──────────────────────────────────────────────────────────
        icon = wx.StaticBitmap(self, bitmap=wx.ArtProvider.GetBitmap(wx.ART_ERROR))
        desc = wx.StaticText(
            self,
            label=_("An unexpected error occurred in {prog}.\n"
                    "Click \"Send error report\" to notify the developer,\n"
                    "or \"Close\" to continue (the program may be unstable)."
                    ).format(prog=prog),
        )

        lbl_trace = wx.StaticText(self, label=_("Error traceback:"))
        self._trace = wx.TextCtrl(
            self, value=err_text,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL,
        )
        self._trace.SetFont(wx.Font(
            wx.FontInfo(9).FaceName("Consolas").Family(wx.FONTFAMILY_TELETYPE)
        ))

        btn_abort = wx.Button(self, wx.ID_ABORT,           _("Force close"))
        btn_copy  = wx.Button(self, wx.ID_COPY,            _("Copy"))
        btn_send  = wx.Button(self, self._ID_SEND.GetId(), _("Send error report"))
        btn_close = wx.Button(self, wx.ID_CLOSE,           _("Close"))
        btn_abort.SetToolTip(_("Force immediate application shutdown"))
        btn_copy.SetToolTip(_("Copy error message to clipboard"))
        btn_send.SetDefault()

        top = wx.BoxSizer(wx.HORIZONTAL)
        top.Add(icon, 0, wx.ALIGN_TOP | wx.RIGHT, 12)
        top.Add(desc, 1, wx.EXPAND)

        btns = wx.BoxSizer(wx.HORIZONTAL)
        btns.Add(btn_abort, 0)
        btns.AddStretchSpacer()
        btns.Add(btn_copy,  0, wx.RIGHT, 6)
        btns.Add(btn_send,  0, wx.RIGHT, 6)
        btns.Add(btn_close, 0)

        root = wx.BoxSizer(wx.VERTICAL)
        root.Add(top,         0, wx.EXPAND | wx.ALL, 10)
        root.Add(lbl_trace,   0, wx.LEFT,             10)
        root.Add(self._trace, 1, wx.EXPAND | wx.ALL,   8)
        root.Add(btns,        0, wx.EXPAND | wx.ALL,   8)
        self.SetSizer(root)

        self.SetMinSize(wx.Size(520, 360))
        self.SetSize(wx.Size(620, 430))
        self.CentreOnScreen()

        self.Bind(wx.EVT_BUTTON, self._on_button)
        self.Bind(wx.EVT_CLOSE,  self._on_close)

    # ── Internals ───────────────────────────────────────────────────────────

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
            wx.TheClipboard.SetData(wx.TextDataObject(self._trace.GetValue()))
            wx.TheClipboard.Close()

    def _send(self):
        from urllib.parse import quote
        import webbrowser
        glb  = _get_glb()
        prog = f"{glb.PROG_NAME} {glb.VERSION}" if glb else f"{_PROG_NAME} {_PROG_VERSION}".strip()
        addr = (glb.BUG_REPORT_ADDRESS if glb else "") or ""
        subject = quote(f"Error report - {prog}")
        body    = quote(self._trace.GetValue()[:1800])
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
        wx.MessageBox(ftrace[:2000], _("Unexpected error"), wx.OK | wx.ICON_ERROR)
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
