###############################################################
# Name:         GuitarDiagramRenderer.py
# Purpose:      Esportazione Songbook in PDF per Songpress
# Author:       Denisov21
# Created:      2026-03-12
# Copyright:    Denisov21
# License:      GNU GPL v2
###############################################################
#
# Flusso:
#   1. L'utente sceglie una cartella con file .sng/.cho/.crd/.txt
#   2. Dialog di configurazione (titolo songbook, autore, anno)
#   3. Songpress ordina i brani per titolo ({t:} o nome file)
#   4. Genera PDF con reportlab:
#        - Copertina
#        - Un brano per pagina (o più se lungo)
#        - Indice finale con titolo e numero di pagina
#
###############################################################

import os
import sys
import re
import tempfile

import wx

_ = wx.GetTranslation


# ------------------------------------------------------------------ #
#  Dialog di configurazione Songbook                                  #
# ------------------------------------------------------------------ #

class SongbookDialog(wx.Dialog):
    def __init__(self, parent):
        super().__init__(parent, title=_("Create Songbook"), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.folder = None
        self.title_val = "Songbook"
        self.author_val = ""
        self.year_val = ""
        self.output_path = None
        # Dati impostazione pagina (condivisi fra i due dialoghi)
        self._print_data = wx.PrintData()
        self._print_data.SetPaperId(wx.PAPER_A4)
        self._print_data.SetOrientation(wx.PORTRAIT)
        self._page_setup_data = wx.PageSetupDialogData(self._print_data)
        self._page_setup_data.SetMarginTopLeft(wx.Point(15, 15))
        self._page_setup_data.SetMarginBottomRight(wx.Point(15, 15))
        self._two_pages_per_sheet = False
        self._build_ui()

    def _build_ui(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        grid = wx.FlexGridSizer(cols=3, hgap=8, vgap=8)
        grid.AddGrowableCol(1)

        # Cartella sorgente
        grid.Add(wx.StaticText(self, label=_("Songs folder:")), 0, wx.ALIGN_CENTER_VERTICAL)
        self._folder_ctrl = wx.TextCtrl(self, style=wx.TE_READONLY)
        grid.Add(self._folder_ctrl, 1, wx.EXPAND)
        btn_folder = wx.Button(self, label=_("Browse..."))
        btn_folder.Bind(wx.EVT_BUTTON, self._on_browse_folder)
        grid.Add(btn_folder)

        # File PDF di output
        grid.Add(wx.StaticText(self, label=_("Save PDF as:")), 0, wx.ALIGN_CENTER_VERTICAL)
        self._output_ctrl = wx.TextCtrl(self, style=wx.TE_READONLY)
        grid.Add(self._output_ctrl, 1, wx.EXPAND)
        btn_output = wx.Button(self, label=_("Browse..."))
        btn_output.Bind(wx.EVT_BUTTON, self._on_browse_output)
        grid.Add(btn_output)

        # Titolo
        grid.Add(wx.StaticText(self, label=_("Songbook title:")), 0, wx.ALIGN_CENTER_VERTICAL)
        self._title_ctrl = wx.TextCtrl(self, value="Songbook")
        grid.Add(self._title_ctrl, 1, wx.EXPAND)
        grid.Add((0, 0))

        # Autore / gruppo
        grid.Add(wx.StaticText(self, label=_("Author / Group:")), 0, wx.ALIGN_CENTER_VERTICAL)
        self._author_ctrl = wx.TextCtrl(self)
        grid.Add(self._author_ctrl, 1, wx.EXPAND)
        grid.Add((0, 0))

        # Anno
        grid.Add(wx.StaticText(self, label=_("Year:")), 0, wx.ALIGN_CENTER_VERTICAL)
        self._year_ctrl = wx.TextCtrl(self)
        grid.Add(self._year_ctrl, 1, wx.EXPAND)
        grid.Add((0, 0))

        # Estensioni da includere
        grid.Add(wx.StaticText(self, label=_("Extensions:")), 0, wx.ALIGN_CENTER_VERTICAL)
        ext_panel = wx.Panel(self)
        ext_sizer = wx.WrapSizer(wx.HORIZONTAL)
        self._ext_checks = {}
        _all_exts = [
            ("crd", True),
            ("cho", True),
            ("chordpro", True),
            ("chopro", True),
            ("pro", True),
            ("tab", True),
            ("sng", True),
            ("txt", False),
        ]
        for ext, default in _all_exts:
            cb = wx.CheckBox(ext_panel, label="." + ext)
            cb.SetValue(default)
            self._ext_checks[ext] = cb
            ext_sizer.Add(cb, 0, wx.RIGHT, 8)
        ext_panel.SetSizer(ext_sizer)
        grid.Add(ext_panel, 1, wx.EXPAND)
        grid.Add((0, 0))

        sizer.Add(grid, 1, wx.EXPAND | wx.ALL, 12)

        # --- Riga pulsanti impostazioni pagina ---
        page_row = wx.BoxSizer(wx.HORIZONTAL)
        page_row.Add(wx.StaticText(self, label=_("Page settings:")), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        btn_page_setup = wx.Button(self, label=_("Page setup..."))
        btn_page_setup.Bind(wx.EVT_BUTTON, self._on_page_setup)
        page_row.Add(btn_page_setup, 0, wx.RIGHT, 8)
        btn_print_opts = wx.Button(self, label=_("Print options..."))
        btn_print_opts.Bind(wx.EVT_BUTTON, self._on_print_options)
        page_row.Add(btn_print_opts, 0)
        sizer.Add(page_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        btn_sizer = self.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        sizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 8)
        self.SetSizer(sizer)
        self.SetMinSize((480, 340))
        self.Fit()

    def _on_browse_folder(self, evt):
        dlg = wx.DirDialog(self, _("Choose the songs folder"),
                           style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST)
        if dlg.ShowModal() == wx.ID_OK:
            self.folder = dlg.GetPath()
            self._folder_ctrl.SetValue(self.folder)
            # Suggerisci output nella stessa cartella
            if not self._output_ctrl.GetValue():
                self._output_ctrl.SetValue(os.path.join(self.folder, "songbook.pdf"))
        dlg.Destroy()

    def _on_browse_output(self, evt):
        dlg = wx.FileDialog(self, _("Save Songbook PDF"),
                            wildcard=_("PDF files (*.pdf)|*.pdf|All files (*.*)|*.*"),
                            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            if not path.lower().endswith('.pdf'):
                path += '.pdf'
            self._output_ctrl.SetValue(path)
        dlg.Destroy()

    def _on_page_setup(self, evt):
        self._page_setup_data.SetPrintData(self._print_data)
        dlg = wx.PageSetupDialog(self, self._page_setup_data)
        if dlg.ShowModal() == wx.ID_OK:
            self._page_setup_data = wx.PageSetupDialogData(dlg.GetPageSetupData())
            self._print_data = wx.PrintData(self._page_setup_data.GetPrintData())
        dlg.Destroy()

    def _on_print_options(self, evt):
        dlg = wx.Dialog(self, title=_("Print options"),
                        style=wx.DEFAULT_DIALOG_STYLE)
        vsizer = wx.BoxSizer(wx.VERTICAL)
        cb = wx.CheckBox(dlg, label=_("Print 2 pages per sheet"))
        cb.SetValue(self._two_pages_per_sheet)
        vsizer.Add(cb, 0, wx.ALL, 12)
        btn_sizer = dlg.CreateStdDialogButtonSizer(wx.OK | wx.CANCEL)
        vsizer.Add(btn_sizer, 0, wx.EXPAND | wx.ALL, 8)
        dlg.SetSizer(vsizer)
        vsizer.Fit(dlg)
        if dlg.ShowModal() == wx.ID_OK:
            self._two_pages_per_sheet = cb.GetValue()
        dlg.Destroy()

    def GetValues(self):
        selected_exts = {
            '.' + ext for ext, cb in self._ext_checks.items() if cb.GetValue()
        }
        tl = self._page_setup_data.GetMarginTopLeft()
        br = self._page_setup_data.GetMarginBottomRight()
        return {
            'folder':      self._folder_ctrl.GetValue().strip(),
            'output':      self._output_ctrl.GetValue().strip(),
            'title':       self._title_ctrl.GetValue().strip() or "Songbook",
            'author':      self._author_ctrl.GetValue().strip(),
            'year':        self._year_ctrl.GetValue().strip(),
            'exts':        selected_exts,
            'print_data':  self._print_data,
            'margin_top':    tl.y,
            'margin_left':   tl.x,
            'margin_bottom': br.y,
            'margin_right':  br.x,
            'two_pages_per_sheet': self._two_pages_per_sheet,
        }


# ------------------------------------------------------------------ #
#  Parsing titolo da file ChordPro                                    #
# ------------------------------------------------------------------ #

def _extract_title(filepath):
    """Legge il titolo dal comando {t:} o {title:}; fallback al nome file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                m = re.search(r'\{(?:t|title)\s*:\s*(.+?)\}', line, re.IGNORECASE)
                if m:
                    return m.group(1).strip()
    except Exception:
        pass
    return os.path.splitext(os.path.basename(filepath))[0]


def _collect_songs(folder, exts=None):
    """Raccoglie tutti i file brano nella cartella, ordinati per titolo."""
    if exts is None:
        exts = {'.sng', '.cho', '.crd', '.txt', '.chopro', '.chordpro'}
    files = []
    for fn in os.listdir(folder):
        if os.path.splitext(fn)[1].lower() in exts:
            fp = os.path.join(folder, fn)
            title = _extract_title(fp)
            files.append((title, fp))
    files.sort(key=lambda x: x[0].lower())
    return files  # list of (title, filepath)


# ------------------------------------------------------------------ #
#  Generazione PDF con reportlab                                       #
# ------------------------------------------------------------------ #

def _render_song_to_png(frame_obj, song_text, scale=2):
    """Renderizza un testo ChordPro su bitmap PNG temporanea.
    Restituisce (tmp_path, width_px, height_px) oppure None in caso di errore."""
    import wx
    from .Renderer import Renderer
    from .SongDecorator import SongDecorator

    try:
        # Misura
        dc_measure = wx.MemoryDC(wx.Bitmap(1, 1))
        if frame_obj.pref.labelVerses:
            decorator = frame_obj.pref.decorator
        else:
            decorator = SongDecorator()
        decorator.showKlavier = False
        r = Renderer(frame_obj.pref.format, decorator, frame_obj.pref.notations)
        w, h = r.Render(song_text, dc_measure)
        w, h = max(1, int(w)), max(1, int(h))

        # Disegna
        bmp = wx.Bitmap(int(w * scale), int(h * scale))
        dc = wx.MemoryDC(bmp)
        dc.SetUserScale(scale, scale)
        dc.SetBackground(wx.WHITE_BRUSH)
        dc.Clear()
        if frame_obj.pref.labelVerses:
            decorator2 = frame_obj.pref.decorator
        else:
            decorator2 = SongDecorator()
        decorator2.showKlavier = False
        r2 = Renderer(frame_obj.pref.format, decorator2, frame_obj.pref.notations)
        r2.Render(song_text, dc)
        del dc

        img = bmp.ConvertToImage()
        tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        tmp.close()
        img.SaveFile(tmp.name, wx.BITMAP_TYPE_PNG)
        return tmp.name, w, h
    except Exception as e:
        return None


def _build_pdf(frame_obj, songs, output_path, sb_title, sb_author, sb_year, progress_cb=None,
               print_data=None, margin_top=15, margin_left=15, margin_bottom=15, margin_right=15,
               two_pages_per_sheet=False):
    """
    Costruisce il PDF completo.
    songs: list of (title, filepath)
    progress_cb: callable(current, total, message) oppure None
    """
    try:
        from reportlab.pdfgen import canvas as rl_canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.colors import HexColor, black, white, grey
    except ImportError:
        wx.MessageBox(
            _("The 'reportlab' library is not installed.\n"
            "Run: pip install reportlab"),
            _("Missing library"),
            wx.OK | wx.ICON_ERROR,
        )
        return False

    # Formato carta dal PrintData (se disponibile), altrimenti A4
    if print_data is not None:
        from reportlab.lib.pagesizes import A4, A3, LETTER, LEGAL, landscape
        _paper_map = {
            wx.PAPER_A4:     A4,
            wx.PAPER_A3:     A3,
            wx.PAPER_LETTER: LETTER,
            wx.PAPER_LEGAL:  LEGAL,
        }
        page_size = _paper_map.get(print_data.GetPaperId(), A4)
        if print_data.GetOrientation() == wx.LANDSCAPE:
            page_size = landscape(page_size)
    else:
        from reportlab.lib.pagesizes import A4
        page_size = A4
    page_w, page_h = page_size
    # Margini in mm (dal PageSetupDialog)
    ml = margin_left   * mm
    mr = margin_right  * mm
    mt = margin_top    * mm
    mb = margin_bottom * mm
    avail_w = page_w - ml - mr
    avail_h = page_h - mt - mb

    # In modalità 2 pagine per foglio ogni "slot" è metà larghezza del foglio
    if two_pages_per_sheet:
        gap = 5 * mm          # separazione centrale
        slot_w = (avail_w - gap) / 2.0
        slot_h = avail_h
    else:
        slot_w = avail_w
        slot_h = avail_h

    tmp_files = []
    # (title, [page_numbers]) per l'indice
    index_entries = []  # list of (title, first_page)

    c = rl_canvas.Canvas(output_path, pagesize=page_size)
    page_num = [0]  # mutabile in closure

    def next_page():
        c.showPage()
        page_num[0] += 1

    def draw_page_number(n):
        c.setFont("Helvetica", 8)
        c.setFillColor(grey)
        c.drawCentredString(page_w / 2, 8 * mm, str(n))
        c.setFillColor(black)

    # ---- COPERTINA ----
    page_num[0] = 1
    # Sfondo colorato
    c.setFillColor(HexColor("#1a3a5c"))
    c.rect(0, 0, page_w, page_h, fill=1, stroke=0)
    # Banda decorativa
    c.setFillColor(HexColor("#e8a020"))
    c.rect(0, page_h * 0.38, page_w, 6 * mm, fill=1, stroke=0)
    c.rect(0, page_h * 0.38 - 2 * mm, page_w, 1.5 * mm, fill=1, stroke=0)
    # Titolo
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(page_w / 2, page_h * 0.52, sb_title)
    # Autore
    if sb_author:
        c.setFont("Helvetica", 18)
        c.setFillColor(HexColor("#e8a020"))
        c.drawCentredString(page_w / 2, page_h * 0.45, sb_author)
    # Anno
    if sb_year:
        c.setFont("Helvetica", 14)
        c.setFillColor(HexColor("#aaaaaa"))
        c.drawCentredString(page_w / 2, page_h * 0.40, sb_year)
    # Numero brani
    c.setFont("Helvetica-Oblique", 11)
    c.setFillColor(HexColor("#aaaaaa"))
    c.drawCentredString(page_w / 2, mb, _("%d songs") % len(songs))

    next_page()  # pagina 2

    # ---- BRANI ----
    SCALE = 2  # ~192 dpi

    # In modalità 2 pagine per foglio teniamo traccia dello slot corrente
    # (0 = sinistra, 1 = destra). Passiamo alla pagina successiva solo dopo
    # aver riempito entrambi gli slot.
    _slot = [0]   # 0=sinistra/unica, 1=destra

    def _slot_origin():
        """Restituisce (x0, y0) dell'angolo inferiore sinistro dello slot corrente."""
        if two_pages_per_sheet:
            if _slot[0] == 0:
                x0 = ml
            else:
                x0 = ml + slot_w + gap
            y0 = mb
        else:
            x0 = ml
            y0 = mb
        return x0, y0

    def _finish_slot():
        """Chiude lo slot corrente; in modalità 2pp cambia slot o va alla pagina successiva."""
        if two_pages_per_sheet:
            if _slot[0] == 0:
                _slot[0] = 1   # prossimo brano va a destra
            else:
                _slot[0] = 0
                draw_page_number(page_num[0])
                next_page()
        else:
            draw_page_number(page_num[0])
            next_page()

    def _flush_slot():
        """Se rimane uno slot sinistro aperto (ultimo foglio dispari), chiude il foglio."""
        if two_pages_per_sheet and _slot[0] == 1:
            draw_page_number(page_num[0])
            next_page()
            _slot[0] = 0

    def _draw_song_in_slot(tmp_path, song_w_px, song_h_px):
        """Disegna il brano nello slot corrente, scalato per stare nello slot."""
        song_w_pt = song_w_px / 96.0 * 72.0
        song_h_pt = song_h_px / 96.0 * 72.0
        scale_fit = min(slot_w / song_w_pt, slot_h / song_h_pt, 1.0)
        draw_w = song_w_pt * scale_fit
        draw_h = song_h_pt * scale_fit
        x0, y0 = _slot_origin()
        x = x0 + (slot_w - draw_w) / 2.0
        y = y0 + (slot_h - draw_h)   # allineato in alto nello slot
        c.drawImage(tmp_path, x, y, width=draw_w, height=draw_h,
                    preserveAspectRatio=True)
        # Linea divisoria verticale in modalità 2pp
        if two_pages_per_sheet and _slot[0] == 0:
            cx = ml + slot_w + gap / 2.0
            c.setStrokeColor(HexColor("#cccccc"))
            c.setLineWidth(0.5)
            c.line(cx, mb, cx, mb + slot_h)

    for i, (title, filepath) in enumerate(songs):
        if progress_cb:
            progress_cb(i + 1, len(songs), _("Processing: %s") % title)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                song_text = f.read()
        except Exception:
            continue

        result = _render_song_to_png(frame_obj, song_text, scale=SCALE)
        if result is None:
            continue
        tmp_path, song_w_px, song_h_px = result
        tmp_files.append(tmp_path)

        first_song_page = page_num[0]
        index_entries.append((title, first_song_page))

        _draw_song_in_slot(tmp_path, song_w_px, song_h_px)
        _finish_slot()

    # Chiudi eventuale foglio rimasto a metà
    _flush_slot()

    # ---- INDICE ----
    index_start_page = page_num[0]
    ROWS_PER_PAGE = 35
    row = 0

    def start_index_page():
        c.setFont("Helvetica-Bold", 16)
        c.setFillColor(HexColor("#1a3a5c"))
        c.drawString(ml, page_h - mt - 10 * mm, _("Index"))
        c.setFillColor(HexColor("#e8a020"))
        c.rect(ml, page_h - mt - 13 * mm, avail_w, 0.8 * mm, fill=1, stroke=0)
        c.setFillColor(black)

    start_index_page()
    top_y = page_h - mt - 18 * mm
    row_h = (top_y - mb) / ROWS_PER_PAGE

    for idx, (title, pg) in enumerate(index_entries):
        if row > 0 and row % ROWS_PER_PAGE == 0:
            draw_page_number(page_num[0])
            next_page()
            start_index_page()

        y_row = top_y - (row % ROWS_PER_PAGE) * row_h
        # Riga alternata leggera
        if (row % 2) == 0:
            c.setFillColor(HexColor("#f4f4f4"))
            c.rect(ml, y_row - 1 * mm, avail_w, row_h, fill=1, stroke=0)
        c.setFillColor(black)
        # Numero d'ordine
        c.setFont("Helvetica", 9)
        c.setFillColor(HexColor("#888888"))
        c.drawString(ml + 1 * mm, y_row + 1.5 * mm, "%d." % (idx + 1))
        # Titolo
        c.setFont("Helvetica", 10)
        c.setFillColor(black)
        c.drawString(ml + 8 * mm, y_row + 1.5 * mm, title)
        # Puntini e numero pagina
        c.setFont("Helvetica", 9)
        c.setFillColor(HexColor("#444444"))
        pg_str = str(pg)
        pg_w = c.stringWidth(pg_str, "Helvetica", 9)
        c.drawString(ml + avail_w - pg_w, y_row + 1.5 * mm, pg_str)
        # Puntini di connessione
        dots_x1 = ml + 8 * mm + c.stringWidth(title, "Helvetica", 10) + 3 * mm
        dots_x2 = ml + avail_w - pg_w - 3 * mm
        if dots_x2 > dots_x1:
            c.setFont("Helvetica", 8)
            c.setFillColor(HexColor("#bbbbbb"))
            dots = ". " * int((dots_x2 - dots_x1) / c.stringWidth(". ", "Helvetica", 8))
            c.drawString(dots_x1, y_row + 1.5 * mm, dots)
        row += 1

    draw_page_number(page_num[0])
    c.save()

    # Pulizia file temporanei
    for tp in tmp_files:
        try:
            os.unlink(tp)
        except Exception:
            pass

    return True


# ------------------------------------------------------------------ #
#  Punto di ingresso                                                   #
# ------------------------------------------------------------------ #

def create_songbook(frame_obj, parent_window):
    """Mostra la dialog, raccoglie i brani ed esporta il PDF."""

    # Verifica reportlab disponibile subito
    try:
        import reportlab
    except ImportError:
        wx.MessageBox(
            _("The 'reportlab' library is not installed.\n"
            "Run: pip install reportlab"),
            _("Missing library"),
            wx.OK | wx.ICON_ERROR,
            parent_window,
        )
        return

    dlg = SongbookDialog(parent_window)
    if dlg.ShowModal() != wx.ID_OK:
        dlg.Destroy()
        return
    vals = dlg.GetValues()
    dlg.Destroy()

    folder = vals['folder']
    output = vals['output']

    if not folder or not os.path.isdir(folder):
        wx.MessageBox(_("Please select a valid folder."), _("Error"), wx.OK | wx.ICON_ERROR, parent_window)
        return
    if not output:
        wx.MessageBox(_("Please select the output PDF file."), _("Error"), wx.OK | wx.ICON_ERROR, parent_window)
        return

    songs = _collect_songs(folder, vals.get('exts'))
    if not songs:
        wx.MessageBox(
            _("No songs found in the folder.\n"
            "Check the selected extensions."),
            _("Empty folder"),
            wx.OK | wx.ICON_INFORMATION,
            parent_window,
        )
        return

    # Barra di avanzamento
    progress = wx.ProgressDialog(
        _("Creating Songbook"),
        _("Initializing..."),
        maximum=len(songs),
        parent=parent_window,
        style=wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME,
    )

    def progress_cb(current, total, message):
        progress.Update(current, message)

    try:
        ok = _build_pdf(
            frame_obj, songs, output,
            vals['title'], vals['author'], vals['year'],
            progress_cb,
            print_data=vals.get('print_data'),
            margin_top=vals.get('margin_top', 15),
            margin_left=vals.get('margin_left', 15),
            margin_bottom=vals.get('margin_bottom', 15),
            margin_right=vals.get('margin_right', 15),
            two_pages_per_sheet=vals.get('two_pages_per_sheet', False),
        )
    finally:
        progress.Destroy()

    if ok:
        wx.MessageBox(
            _("Songbook exported successfully!\n\n"
            "%d songs included.\n\n%s") % (len(songs), output),
            _("Songbook created"),
            wx.OK | wx.ICON_INFORMATION,
            parent_window,
        )
