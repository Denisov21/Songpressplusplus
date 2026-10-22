###############################################################
# Name:             SyntaxCheckerDialog.py
# Purpose:          Dialog showing the result of ChordPro syntax checking.
# Author:           Denisov21
# Created:          2026-03-16
# Copyright:        Denisov21
# License:          GNU GPL v2
##############################################################

import wx
from .SyntaxChecker import SyntaxCheckResult, SEVERITY_WARNING

_ = wx.GetTranslation


class SyntaxCheckerDialog(wx.Dialog):
    """
    Dialog showing the result of syntax checking.

    If there are no errors, a success message is displayed.
    If there are errors, they are listed with line, column and description.
    Double-clicking an error moves the editor
    to the corresponding line (requires the caller to bind OnGoToError).
    """

    def __init__(self, parent, result: SyntaxCheckResult, config=None):
        title = _("Syntax check")
        super().__init__(parent, title=title,
                         style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self._result = result
        self._config = config
        self._build_ui()
        # Resize grip in the bottom-right corner
        self._status_bar = wx.StatusBar(self, style=wx.STB_SIZEGRIP)
        self._status_bar.SetStatusText("")
        self.GetSizer().Add(self._status_bar, 0, wx.EXPAND)
        self._fit_height()
        self.CentreOnParent()

    # ------------------------------------------------------------------
    # Auto-fit height
    # ------------------------------------------------------------------

    def _fit_height(self):
        """Set the dialog height to fit the error list content exactly.

        Measures the real row height from the ListCtrl, multiplies by the
        number of rows, adds all surrounding chrome (header, buttons, margins,
        title bar, status bar) and clamps the result between a minimum and a
        maximum so the dialog never looks awkward on either extreme.
        """
        _MIN_W = 550
        _MIN_ROWS, _MAX_ROWS = 2, 12   # visible rows of the error list

        if not self._result.is_valid and hasattr(self, "_list"):
            row_count = self._list.GetItemCount()
            row_h = self._list.GetItemRect(0).height if row_count > 0 else 20
            header_row_h = 24            # column header (not exposed by wx)
            rows = max(_MIN_ROWS, min(row_count, _MAX_ROWS))
            # The list gets exactly the height its rows need; the sizer then
            # computes the real minimum for the rest (band, buttons, status bar).
            self._list.SetMinSize((-1, header_row_h + row_h * rows + 6))

        self.Layout()
        self.Fit()                       # smallest size that shows everything
        w, h = self.GetSize()
        w = max(w, _MIN_W)
        self.SetMinSize((_MIN_W, h))     # never smaller than the content
        self.SetSize(w, h)

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
        vbox.Add(wx.StaticLine(panel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 14)
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        if not self._result.is_valid:
            self._fit_btn = wx.Button(panel, label=_("Fit width"))
            self._fit_btn.SetToolTip(
                _("Resize the dialog so the Description column fits the longest text"))
            self._fit_btn.Bind(wx.EVT_BUTTON, self._on_fit_width)
            btn_sizer.Add(self._fit_btn, 0, wx.RIGHT, 8)


        if not self._result.is_valid:
            # Colour used to highlight the error line in the editor
            btn_sizer.Add(wx.StaticText(panel, label=_("Highlight colour:")),
                          0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 6)
            self._colour_picker = wx.ColourPickerCtrl(panel, colour=self._load_colour())
            self._colour_picker.SetToolTip(
                _("Colour used to highlight the selected error line in the editor"))
            self._colour_picker.Bind(wx.EVT_COLOURPICKER_CHANGED, self._on_colour_changed)
            btn_sizer.Add(self._colour_picker, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)

        btn_sizer.AddStretchSpacer()
        close_btn = wx.Button(panel, wx.ID_CLOSE, _("Close"))
        close_btn.SetDefault()
        close_btn.Bind(wx.EVT_BUTTON, lambda e: self.EndModal(wx.ID_CLOSE))
        btn_sizer.Add(close_btn, 0)

        vbox.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 14)
        panel.SetSizer(vbox)

        # Dialog sizer: panel + status bar
        dlg_sizer = wx.BoxSizer(wx.VERTICAL)
        dlg_sizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(dlg_sizer)

    @staticmethod
    def _make_check_bitmap(size=32, colour=wx.Colour(46, 160, 67),
                           bg=wx.Colour(229, 245, 232)):
        """Draws a round green badge with a white check mark."""
        bmp = wx.Bitmap(size, size, 32)
        try:
            dc = wx.MemoryDC(bmp)
            dc.SetBackground(wx.Brush(bg))  # same colour as the band: no black corners
            dc.Clear()
            gc = wx.GraphicsContext.Create(dc)
            gc.SetBrush(wx.Brush(colour))
            gc.SetPen(wx.TRANSPARENT_PEN)
            gc.DrawEllipse(0, 0, size, size)
            gc.SetPen(wx.Pen(wx.WHITE, max(2, size // 11), wx.PENSTYLE_SOLID))
            path = gc.CreatePath()
            path.MoveToPoint(size * 0.27, size * 0.53)
            path.AddLineToPoint(size * 0.44, size * 0.69)
            path.AddLineToPoint(size * 0.74, size * 0.34)
            gc.StrokePath(path)
            del gc
            dc.SelectObject(wx.NullBitmap)
            return bmp
        except Exception:
            return wx.ArtProvider.GetBitmap(wx.ART_TICK_MARK, wx.ART_MESSAGE_BOX, (size, size))

    def _build_success(self, panel, sizer):
        # Same look as the error list: tinted band on top, neutral body.
        band = wx.Panel(panel)
        band.SetBackgroundColour(wx.Colour(229, 245, 232))
        icon = wx.StaticBitmap(band, bitmap=self._make_check_bitmap(40))
        title = wx.StaticText(band, label=_("No syntax errors found."))
        title.SetForegroundColour(wx.Colour(30, 110, 50))
        font = title.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(font.GetPointSize() + 2)
        title.SetFont(font)
        hint = wx.StaticText(band, label=_("The song is syntactically correct."))
        hint.SetForegroundColour(wx.Colour(90, 90, 90))

        texts = wx.BoxSizer(wx.VERTICAL)
        texts.Add(title, 0)
        texts.Add(hint, 0, wx.TOP, 2)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(icon, 0, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 18)
        hbox.Add(texts, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 16)
        band.SetSizer(hbox)
        sizer.Add(band, 1, wx.EXPAND | wx.BOTTOM, 12)

    def _build_error_list(self, panel, sizer):
        n_err = self._result.error_count
        n_warn = self._result.warning_count

        # Fascia d'intestazione tenue: rosata se ci sono errori veri,
        # ambra se ci sono solo avvertimenti. Il resto del dialogo resta neutro.
        if n_err > 0:
            band_bg = wx.Colour(253, 232, 229)
            accent  = wx.Colour(198, 40, 40)
            art_id  = wx.ART_ERROR
        else:
            band_bg = wx.Colour(255, 244, 214)
            accent  = wx.Colour(176, 112, 0)
            art_id  = wx.ART_WARNING

        # Intestazione: forme dedicate singolare/plurale così l'accordo
        # participio/numero resta corretto anche in italiano. Nel caso misto
        # il totale è sempre >= 2, quindi "Trovati" (plurale) è sempre giusto.
        if n_err > 0 and n_warn > 0:
            err_frag = _("1 error") if n_err == 1 else _("{n} errors").format(n=n_err)
            warn_frag = _("1 warning") if n_warn == 1 else _("{n} warnings").format(n=n_warn)
            header_text = _("Found {errors} and {warnings}:").format(
                errors=err_frag, warnings=warn_frag)
        elif n_err > 0:
            header_text = (_("Found 1 error:") if n_err == 1
                           else _("Found {n} errors:").format(n=n_err))
        else:
            header_text = (_("Found 1 warning:") if n_warn == 1
                           else _("Found {n} warnings:").format(n=n_warn))

        band = wx.Panel(panel)
        band.SetBackgroundColour(band_bg)
        icon = wx.StaticBitmap(
            band, bitmap=wx.ArtProvider.GetBitmap(art_id, wx.ART_MESSAGE_BOX, (32, 32)))
        header = wx.StaticText(band, label=header_text)
        header.SetForegroundColour(accent)
        font = header.GetFont()
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        font.SetPointSize(font.GetPointSize() + 2)
        header.SetFont(font)
        hint = wx.StaticText(band, label=_("Click an error to highlight its line in the editor."))
        hint.SetForegroundColour(wx.Colour(90, 90, 90))

        texts = wx.BoxSizer(wx.VERTICAL)
        texts.Add(header, 0)
        texts.Add(hint, 0, wx.TOP, 2)
        band_sizer = wx.BoxSizer(wx.HORIZONTAL)
        band_sizer.Add(icon, 0, wx.LEFT | wx.TOP | wx.BOTTOM | wx.ALIGN_CENTER_VERTICAL, 14)
        band_sizer.Add(texts, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 12)
        band.SetSizer(band_sizer)
        sizer.Add(band, 0, wx.EXPAND | wx.BOTTOM, 12)

        # Error list
        self._list = wx.ListCtrl(
            panel,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN
        )

        # Icone per la colonna "Tipo" (16x16).
        img_list = wx.ImageList(16, 16)
        self._img_error = img_list.Add(
            wx.ArtProvider.GetBitmap(wx.ART_ERROR, wx.ART_LIST, (16, 16)))
        self._img_warning = img_list.Add(
            wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_LIST, (16, 16)))
        self._list.AssignImageList(img_list, wx.IMAGE_LIST_SMALL)

        self._list.InsertColumn(0, _("Type"),        width=120)
        self._list.InsertColumn(1, _("Line"),        width=60)
        self._list.InsertColumn(2, _("Column"),      width=70)
        self._list.InsertColumn(3, _("Description"), width=-1)  # si espande automaticamente

        for err in self._result.errors:
            if err.severity == SEVERITY_WARNING:
                img, sev_label = self._img_warning, _("Warning")
            else:
                img, sev_label = self._img_error, _("Error")
            idx = self._list.InsertItem(self._list.GetItemCount(), sev_label, img)
            self._list.SetItem(idx, 1, str(err.line))
            self._list.SetItem(idx, 2, str(err.column))
            self._list.SetItem(idx, 3, err.message)
            self._list.SetItemBackgroundColour(
                idx, wx.Colour(255, 246, 220) if err.severity == SEVERITY_WARNING
                else wx.Colour(255, 240, 238))

        self._list.Bind(wx.EVT_LIST_ITEM_SELECTED,  self._on_item_selected)
        self._list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._on_goto)
        self._list.Bind(wx.EVT_SIZE, self._on_list_resize)

        sizer.Add(self._list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 14)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def _on_list_resize(self, event):
        """Keeps the Description column filling the remaining list width."""
        total = self._list.GetClientSize().width
        fixed = (self._list.GetColumnWidth(0)
                 + self._list.GetColumnWidth(1)
                 + self._list.GetColumnWidth(2))
        remaining = total - fixed
        if remaining > 0:
            self._list.SetColumnWidth(3, remaining)
        event.Skip()

    def _on_fit_width(self, _event):
        """Resize the dialog horizontally so the Description column fits the longest text."""
        if not hasattr(self, "_list") or self._list.GetItemCount() == 0:
            return

        dc = wx.ClientDC(self._list)
        dc.SetFont(self._list.GetFont())

        # IMPORTANT: GetItemText() returns the already-truncated string shown
        # in the cell, not the full text.  Read directly from the error objects.
        max_desc_px = 0
        for err in self._result.errors:
            w, _ = dc.GetTextExtent(err.message)
            if w > max_desc_px:
                max_desc_px = w

        col0_w = self._list.GetColumnWidth(0)   # Type
        col1_w = self._list.GetColumnWidth(1)   # Line
        col2_w = self._list.GetColumnWidth(2)   # Column
        fixed_cols_w = col0_w + col1_w + col2_w
        # cell padding (~ 8 px) + vertical scrollbar + list border
        desc_col_w   = max_desc_px + 8
        scrollbar_w  = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
        list_chrome  = scrollbar_w + 4   # 2 px border each side
        dialog_extra = 32                # outer margins (10+10) + panel border

        needed_w = fixed_cols_w + desc_col_w + list_chrome + dialog_extra
        target_w = max(needed_w, 550)    # never shrink below the minimum

        _cur_w, cur_h = self.GetSize()
        if target_w == _cur_w:
            return
        self.SetSize(target_w, cur_h)
        # Let the Description column fill the new list width
        list_inner = target_w - dialog_extra - list_chrome - fixed_cols_w
        self._list.SetColumnWidth(3, max(list_inner, desc_col_w))
        self.Layout()

    def _on_item_selected(self, event):
        # Evidenzia subito la riga dell'errore nell'editor
        self._on_goto(None)
        event.Skip()

    _COLOUR_KEY = 'syntaxErrorHighlightColour'
    _COLOUR_DEFAULT = '#FF7878'

    def _load_colour(self):
        """Reads the saved highlight colour (on open)."""
        col = wx.Colour(self._COLOUR_DEFAULT)
        if self._config is not None:
            c = wx.Colour(self._config.Read(self._COLOUR_KEY, self._COLOUR_DEFAULT))
            if c.IsOk():
                col = c
        return col

    def _save_colour(self):
        """Writes the highlight colour to disk (on close)."""
        if self._config is not None and hasattr(self, "_colour_picker"):
            self._config.Write(self._COLOUR_KEY,
                               self._colour_picker.GetColour().GetAsString(wx.C2S_HTML_SYNTAX))
            self._config.Flush()

    def EndModal(self, retCode):
        self._save_colour()
        super().EndModal(retCode)

    def _on_colour_changed(self, event):
        if self._config is not None:
            # apply immediately: the frame reads the colour from the config
            self._config.Write(self._COLOUR_KEY,
                               self._colour_picker.GetColour().GetAsString(wx.C2S_HTML_SYNTAX))
        self._on_goto(None)

    def _on_goto(self, event):
        """Posts a custom event to move the cursor to the error line."""
        if not hasattr(self, "_list"):
            return
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
