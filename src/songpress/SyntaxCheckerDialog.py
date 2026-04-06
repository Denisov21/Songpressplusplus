###############################################################
# Name:             SyntaxCheckerDialog.py
# Purpose:          Dialog showing the result of ChordPro syntax checking.
# Author:           Denisov21
# Created:          2026-03-16
# Copyright:        Denisov21
# License:          GNU GPL v2
##############################################################

import wx
from .SyntaxChecker import SyntaxCheckResult

_ = wx.GetTranslation


class SyntaxCheckerDialog(wx.Dialog):
    """
    Dialog showing the result of syntax checking.

    If there are no errors, a success message is displayed.
    If there are errors, they are listed with line, column and description.
    Double-clicking an error (or pressing Go to error) moves the editor
    to the corresponding line (requires the caller to bind OnGoToError).
    """

    def __init__(self, parent, result: SyntaxCheckResult):
        title = _("Syntax check")
        super().__init__(parent, title=title,
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._result = result
        self._build_ui()
        # Resize grip in the bottom-right corner
        self._status_bar = wx.StatusBar(self, style=wx.STB_SIZEGRIP)
        self._status_bar.SetStatusText("")
        self.GetSizer().Add(self._status_bar, 0, wx.EXPAND)
        self.SetMinSize((550, 400))
        self.SetSize((550, 400))
        self.CentreOnParent()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        panel = wx.Panel(self)
        vbox = wx.BoxSizer(wx.VERTICAL)

        if self._result.is_valid:
            self._build_success(panel, vbox)
        else:
            self._build_error_list(panel, vbox)

        # Buttons
        btn_sizer = wx.StdDialogButtonSizer()
        if not self._result.is_valid:
            self._goto_btn = wx.Button(panel, label=_("Go to error"))
            self._goto_btn.Bind(wx.EVT_BUTTON, self._on_goto)
            btn_sizer.Add(self._goto_btn, 0, wx.RIGHT, 8)
            self._goto_btn.Enable(False)

        close_btn = wx.Button(panel, wx.ID_CLOSE, _("Close"))
        close_btn.SetDefault()
        btn_sizer.AddButton(close_btn)
        btn_sizer.Realize()
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))

        vbox.Add(btn_sizer, 0, wx.ALIGN_RIGHT | wx.ALL, 10)
        panel.SetSizer(vbox)

        # Dialog sizer: panel + status bar
        dlg_sizer = wx.BoxSizer(wx.VERTICAL)
        dlg_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(dlg_sizer)

    def _build_success(self, panel, sizer):
        panel.SetBackgroundColour(wx.Colour(180, 230, 140))  # verde chiaro tenue
        icon = wx.StaticBitmap(
            panel,
            bitmap=wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_MESSAGE_BOX, (32, 32))
        )
        label = wx.StaticText(panel, label=_("No syntax errors found."))
        label.SetForegroundColour(wx.Colour(0, 0, 0))
        font = label.GetFont()
        font.SetPointSize(font.GetPointSize() + 1)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        label.SetFont(font)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(icon, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        hbox.Add(label, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        sizer.Add(hbox, 1, wx.EXPAND | wx.ALL, 6)

    def _build_error_list(self, panel, sizer):
        panel.SetBackgroundColour(wx.Colour(255, 180, 140))  # arancione-rosso chiaro
        count = len(self._result.errors)
        if count == 1:
            header_text = _("Found 1 syntax error:")
        else:
            header_text = _("Found {count} syntax errors:").format(count=count)

        header = wx.StaticText(panel, label=header_text)
        header.SetForegroundColour(wx.Colour(0, 0, 0))
        font = header.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(font)
        sizer.Add(header, 0, wx.ALL, 10)

        # Error list
        self._list = wx.ListCtrl(
            panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )
        self._list.InsertColumn(0, _("Line"),        width=60)
        self._list.InsertColumn(1, _("Column"),      width=70)
        self._list.InsertColumn(2, _("Description"), width=-1)  # si espande automaticamente

        for err in self._result.errors:
            idx = self._list.InsertItem(self._list.GetItemCount(), str(err.line))
            self._list.SetItem(idx, 1, str(err.column))
            self._list.SetItem(idx, 2, err.message)

        self._list.Bind(wx.EVT_LIST_ITEM_SELECTED,  self._on_item_selected)
        self._list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_goto)
        self._list.Bind(wx.EVT_SIZE, self._on_list_resize)

        sizer.Add(self._list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def _on_list_resize(self, event):
        """Keeps the Description column filling the remaining list width."""
        total = self._list.GetClientSize().width
        fixed = self._list.GetColumnWidth(0) + self._list.GetColumnWidth(1)
        remaining = total - fixed
        if remaining > 0:
            self._list.SetColumnWidth(2, remaining)
        event.Skip()

    def _on_item_selected(self, event):
        if hasattr(self, "_goto_btn"):
            self._goto_btn.Enable(True)
        event.Skip()

    def _on_goto(self, event):
        """Posts a custom event to move the cursor to the error line."""
        idx = self._list.GetFirstSelected()
        if idx == -1:
            return
        error = self._result.errors[idx]
        # Notify the caller via wx event
        goto_event = SyntaxErrorGotoEvent(line=error.line, column=error.column)
        wx.PostEvent(self.GetParent(), goto_event)

    def get_selected_error(self):
        """Returns the currently selected error in the list, or None."""
        if not hasattr(self, "_list"):
            return None
        idx = self._list.GetFirstSelected()
        if idx == -1:
            return None
        return self._result.errors[idx]


# ------------------------------------------------------------------
# Custom event for "go to line"
# ------------------------------------------------------------------

_EVT_SYNTAX_GOTO_ID = wx.NewEventType()
EVT_SYNTAX_GOTO = wx.PyEventBinder(_EVT_SYNTAX_GOTO_ID, 1)


class SyntaxErrorGotoEvent(wx.PyEvent):
    """
    Event fired when the user wants to jump to an error line.
    Attributes:
        line   -- line number (1-based)
        column -- column number (1-based)
    """
    def __init__(self, line: int, column: int):
        super().__init__()
        self.SetEventType(_EVT_SYNTAX_GOTO_ID)
        self.line = line
        self.column = column
