###############################################################
# Name:             PreviewCanvas.py
# Purpose:          Window containing preview
# Author:           Luca Allulli (webmaster@roma21.it)
# Modified by:      Denisov21
# Created:          2009-02-21
# Copyright:        Luca Allulli (https://www.skeed.it/songpress)
#                   Modifications copyright Denisov21
# License:          GNU GPL v2
###############################################################
#
# CHANGELOG (miglioramenti rispetto alla versione originale):
#
# [Fix 1] Slider zoom: sostituisce i pulsanti +/- con uno slider orizzontale
#         (range 30-300%, step 10%). I pulsanti +/- rimangono ai lati.
#         Lo slider si sincronizza bidirezionalmente con tutti i metodi zoom.
#
# [Fix 2] BestSize pannello AUI: 240x400 → 320x500 (in SongpressFrame)
#
# [Fix 3] Margine orizzontale dinamico: 3% della larghezza client (min 8px)
#         invece di 24px fisso. Si adatta al pannello stretto o largo.
#
#
# [Fix 5] EVT_CHAR_HOOK: intercetta Ctrl+PgUp/PgDn per scroll di pagina
#         prima che ScrolledWindow consumi i tasti freccia.
#
# [Fix 6] pixedScrolled scalato: la granularita' dello scroll e' proporzionale
#         allo zoom (zoom alto = scroll piu' fine).
#
# [Fix 7] Rimosso 'import platform' inutilizzato.
#
# [Fix 8] Rimossa costante _PAGE_W_MM (mai usata).
#
# [Fix 9] Shortcut Ctrl+Shift+G = fit-to-width (mnemonico per tastiera).

#
# [UX] Toolbar compatta sopra il pannello anteprima, con:
#        - pulsante "Copia negli appunti" (sostituisce il vecchio HyperlinkCtrl)
#        - pulsanti Zoom In / Zoom Out / Reset zoom (100%)
#        - label zoom corrente (es. "100%")
#        - pulsante Fit-to-width (adatta larghezza alla finestra)
#
# [Layout & Zoom] Supporto zoom tramite self._zoom_factor (default 1.0).
#        - Ctrl+Scroll sul canvas: zoom in/out a step del 10%
#        - Ctrl++ / Ctrl+- / Ctrl+0: zoom da tastiera
#        - Range: 30% – 300%
#
# [Layout] Sfondo a "pagine":
#        - Canvas con sfondo grigio (simulazione fogli)
#        - Il renderer disegna ogni "pagina" come rettangolo bianco

#        - Calcolo altezza pagina in px in base al formato carta corrente
#        - Il renderer esistente viene lasciato invariato; le pagine
#          vengono simulate nel DC di PreviewCanvas
#
# [Performance] Debounce del refresh (default 300 ms):
#        - Refresh() non ridisegna immediatamente ma avvia un wx.CallLater
#        - Se arriva un nuovo Refresh() prima dello scadere del timer,
#          il vecchio viene cancellato e uno nuovo viene avviato
#        - Questo evita ridisegni continui durante la digitazione rapida
#
# [Indicatore pagina] Label "Pagina X di Y" aggiornata allo scroll
#        - Calcola la pagina corrente in base alla posizione verticale
#          dello scrolled window
#
###############################################################

import re

import wx
import wx.adv

from .Renderer import *

_ = wx.GetTranslation

# ---------------------------------------------------------------------------
# Costanti
# ---------------------------------------------------------------------------
_ZOOM_MIN      = 0.30
_ZOOM_MAX      = 3.00
_ZOOM_STEP     = 0.10
_ZOOM_DEFAULT  = 1.00
_DEBOUNCE_MS   = 300      # millisecondi di attesa prima del ridisegno

# Costanti layout pannello anteprima
_PAGE_H_MM     = 297.0   # altezza A4 default (mm) — usata come fallback
_PAGE_GAP_PX   = 16      # spazio verticale tra una pagina e l'altra (px)
# _PAGE_MARGIN_H e' ora calcolato dinamicamente in OnPaint (3% della larghezza)


class PreviewCanvas(object):
    def __init__(self, parent, sf, notations, sd=SongDecorator(), embedded=False, minSizeEnabled=True):
        object.__init__(self)
        self.main_panel = wx.Window(parent)
        if minSizeEnabled:
            self.main_panel.SetMinSize(wx.Size(370, 520))
        self._zoom_factor = _ZOOM_DEFAULT
        self._debounce_timer = None     # wx.CallLater attivo (o None)
        self._pending_text   = ""       # testo in attesa di refresh

        # Flags opzioni anteprima (applicati dopo la creazione del panel)
        self._showPageIndicator = True
        self._greyBackground    = True
        self._debounceEnabled   = True   # se False: ridisegno immediato ad ogni tasto

        # Dimensioni foglio e margini correnti in mm (aggiornate da SetPageSizeMm /
        # SetPageMarginsMm). Default A4 portrait con margini 15mm.
        # Vengono sincronizzati da SongpressFrame dopo OnPageSetup.
        self._page_w_mm     = 210.0
        self._page_h_mm     = 297.0
        self._margin_top_mm    = 15.0
        self._margin_bottom_mm = 15.0

        # Flags per le linee di interruzione (persistenti anche al cambio decorator)
        self._showPageBreakLines  = True
        self._showColumnBreakLines = True

        # Callback chiamata al doppio-click sull'anteprima:
        # signature: callback(line_number: int) dove line_number e' 0-based
        # Impostata da SongpressFrame con SetClickCallback()
        self._on_click_callback = None
        # Se False il doppio-click non fa nulla (disabilitato da opzioni)
        self._dblClickFocusEnabled = True

        # Riferimento alla finestra fullscreen (None = non aperta)
        self._fullscreen_frame = None

        # ── Layout principale ────────────────────────────────────────────
        outer = wx.BoxSizer(wx.VERTICAL)
        parent_win = self.main_panel

        if not embedded:
            # ── Toolbar compatta ────────────────────────────────────────
            toolbar = wx.Panel(parent_win, style=wx.BORDER_NONE)
            toolbar.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
            tb_sizer = wx.BoxSizer(wx.HORIZONTAL)

            # Pulsante copia (sostituisce HyperlinkCtrl)
            btn_copy = wx.BitmapButton(
                toolbar, wx.ID_ANY,
                wx.ArtProvider.GetBitmap(wx.ART_COPY, wx.ART_TOOLBAR, (16, 16)),
                style=wx.BORDER_NONE,
            )
            btn_copy.SetToolTip(_("Copy formatted song to clipboard"))
            tb_sizer.Add(btn_copy, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)

            tb_sizer.Add(wx.StaticLine(toolbar, style=wx.LI_VERTICAL), 0,
                         wx.EXPAND | wx.LEFT | wx.RIGHT, 4)

            # Zoom out (pulsante piccolo a sinistra dello slider)
            btn_zoom_out = wx.BitmapButton(
                toolbar, wx.ID_ANY,
                wx.ArtProvider.GetBitmap(wx.ART_MINUS, wx.ART_TOOLBAR, (16, 16)),
                style=wx.BORDER_NONE,
            )
            btn_zoom_out.SetToolTip(_("Zoom out (Ctrl+-)"))
            tb_sizer.Add(btn_zoom_out, 0, wx.ALIGN_CENTER_VERTICAL)

            # Slider zoom: range 30-300 in step da 10
            _zoom_pct = int(round(_ZOOM_DEFAULT * 100))
            self._zoom_slider = wx.Slider(
                toolbar, wx.ID_ANY,
                value=_zoom_pct, minValue=int(_ZOOM_MIN * 100), maxValue=int(_ZOOM_MAX * 100),
                size=(90, -1),
                style=wx.SL_HORIZONTAL,
            )
            self._zoom_slider.SetToolTip(_("Zoom level — drag or use Ctrl+Scroll"))
            tb_sizer.Add(self._zoom_slider, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 2)

            # Zoom in (pulsante piccolo a destra dello slider)
            btn_zoom_in = wx.BitmapButton(
                toolbar, wx.ID_ANY,
                wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_TOOLBAR, (16, 16)),
                style=wx.BORDER_NONE,
            )
            btn_zoom_in.SetToolTip(_("Zoom in (Ctrl++)"))
            tb_sizer.Add(btn_zoom_in, 0, wx.ALIGN_CENTER_VERTICAL)

            # Label zoom (mostra la percentuale corrente)
            self._zoom_label = wx.StaticText(toolbar, label="100%", size=(38, -1),
                                             style=wx.ALIGN_CENTRE_HORIZONTAL)
            tb_sizer.Add(self._zoom_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 3)

            # Reset zoom 1:1
            btn_zoom_reset = wx.Button(toolbar, wx.ID_ANY, "1:1",
                                       size=(30, -1), style=wx.BORDER_SIMPLE)
            btn_zoom_reset.SetToolTip(_("Reset zoom to 100% (Ctrl+0)"))
            tb_sizer.Add(btn_zoom_reset, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)

            tb_sizer.Add(wx.StaticLine(toolbar, style=wx.LI_VERTICAL), 0,
                         wx.EXPAND | wx.LEFT | wx.RIGHT, 4)

            # Pulsante tutto schermo
            btn_fullscreen = wx.Button(toolbar, wx.ID_ANY, u"⛶",
                                       size=(28, -1), style=wx.BORDER_SIMPLE)
            btn_fullscreen.SetToolTip(_("Full screen preview (F11)"))
            tb_sizer.Add(btn_fullscreen, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 2)

            tb_sizer.Add(wx.StaticLine(toolbar, style=wx.LI_VERTICAL), 0,
                         wx.EXPAND | wx.LEFT | wx.RIGHT, 4)

            # Fit-to-width — nessuna size fissa: wx calcola la larghezza dal testo
            # tradotto (es. "Adatta" e' piu' largo di "Fit")
            btn_fit = wx.Button(toolbar, wx.ID_ANY, _("Fit"),
                                style=wx.BORDER_SIMPLE)
            btn_fit.SetToolTip(_("Fit preview width to panel (Ctrl+Shift+G)"))
            tb_sizer.Add(btn_fit, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 2)

            # Spacer + label pagina (allineata a destra)
            # La label viene pre-dimensionata sul testo piu' lungo possibile
            # ("Pagina 99 di 99") cosi' non viene mai troncata.
            tb_sizer.AddStretchSpacer()
            _sample = _("Page %d of %d") % (99, 99)
            self._page_label = wx.StaticText(toolbar, label=_sample)
            _w, _h = self._page_label.GetTextExtent(_sample)
            self._page_label.SetMinSize(wx.Size(_w + 8, -1))
            self._page_label.SetLabel("")
            self._page_label.SetForegroundColour(wx.Colour(100, 100, 100))
            tb_sizer.Add(self._page_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)

            toolbar.SetSizer(tb_sizer)
            toolbar.Layout()
            outer.Add(toolbar, 0, wx.EXPAND)

            # ── Separatore ───────────────────────────────────────────────
            outer.Add(wx.StaticLine(parent_win), 0, wx.EXPAND)

            # Salva riferimento al link per retrocompatibilità con SongpressFrame
            # (SongpressFrame fa: self.previewCanvas.main_panel.Bind(EVT_HYPERLINK, ..., self.previewCanvas.link))
            # Creiamo un attributo link fittizio che espone lo stesso id del btn_copy
            self.link = btn_copy

            # Bind toolbar
            btn_copy.Bind(wx.EVT_BUTTON,       self._OnCopyButton)
            btn_zoom_out.Bind(wx.EVT_BUTTON,   lambda e: self._ZoomBy(-_ZOOM_STEP))
            btn_zoom_in.Bind(wx.EVT_BUTTON,    lambda e: self._ZoomBy(+_ZOOM_STEP))
            btn_zoom_reset.Bind(wx.EVT_BUTTON, lambda e: self._SetZoom(_ZOOM_DEFAULT))
            btn_fit.Bind(wx.EVT_BUTTON,        self._OnFitWidth)
            self._zoom_slider.Bind(wx.EVT_SLIDER, self._OnZoomSlider)
            btn_fullscreen.Bind(wx.EVT_BUTTON, self._OnFullscreen)
        else:
            self.link = None
            self._zoom_label  = None
            self._zoom_slider = None
            self._page_label  = None

        # Cache dimensioni ultimo render (px pre-zoom) — inizializzate PRIMA
        # dei bind degli eventi perché EVT_SIZE su Windows può scattare
        # immediatamente durante la costruzione del pannello, prima che
        # __init__ abbia completato l'assegnazione degli attributi.
        self._last_w = 0
        self._last_h = 0

        # ── ScrolledWindow principale ────────────────────────────────────
        self.panel = wx.ScrolledWindow(parent_win, style=wx.BORDER_DOUBLE)
        self.panel.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.pixedScrolled = 10
        self.panel.SetScrollbars(self.pixedScrolled, self.pixedScrolled, 0, 0)
        self.panel.SetBackgroundColour(wx.Colour(160, 160, 160))  # grigio per sfondo pagine

        self.panel.Bind(wx.EVT_PAINT,        self.OnPaint)
        self.panel.Bind(wx.EVT_MOUSEWHEEL,   self._OnMouseWheel)
        self.panel.Bind(wx.EVT_KEY_DOWN,     self._OnKeyDown)
        # Fix 5: EVT_CHAR_HOOK cattura i tasti freccia prima che
        # ScrolledWindow li consumi, permettendo Ctrl+Su/Giu come scroll di pagina
        self.panel.Bind(wx.EVT_CHAR_HOOK,    self._OnCharHook)
        self.panel.Bind(wx.EVT_SCROLLWIN,    self._OnScroll)
        self.panel.Bind(wx.EVT_SIZE,         self._OnPanelSize)
        self.panel.Bind(wx.EVT_LEFT_DCLICK,  self._OnDoubleClick)

        self.text = ""
        outer.Add(self.panel, 1, wx.EXPAND)

        # SongFormat
        self.renderer = Renderer(sf, sd, notations)
        self.main_panel.SetSizer(outer)
        self.main_panel.Layout()

    # -----------------------------------------------------------------------
    # Paint
    # -----------------------------------------------------------------------

    def OnPaint(self, e):
        dc = wx.AutoBufferedPaintDC(self.panel)
        self.panel.PrepareDC(dc)

        # Fix 3: margine orizzontale dinamico (3% della larghezza client, min 8 px)
        panel_client_w, _ = self.panel.GetClientSize()
        margin_h = max(8, int(panel_client_w * 0.03))

        # Sfondo: grigio o bianco in base al flag _greyBackground
        bg_colour = wx.Colour(160, 160, 160) if self._greyBackground else wx.WHITE
        dc.SetBackground(wx.Brush(bg_colour))
        dc.Clear()

        if not self.text.strip():
            self._UpdatePageLabel(0, 0)
            return


        # Applica zoom tramite scala DC
        dc.SetUserScale(self._zoom_factor, self._zoom_factor)

        # Render nella zona virtuale scalata
        w, h = self.renderer.Render(self.text, dc)
        self._last_w = w
        self._last_h = h

        # Ripristina scala per aggiornare la virtual size in pixel reali
        dc.SetUserScale(1.0, 1.0)

        # Aggiorna dimensione virtuale con margine dinamico
        vw = int(w * self._zoom_factor) + margin_h * 2
        vh = int(h * self._zoom_factor) + _PAGE_GAP_PX * 2
        self.panel.SetVirtualSize(wx.Size(vw, vh))

        # Aggiorna label pagina
        self._UpdatePageLabel(h, vh)

    # -----------------------------------------------------------------------
    # Zoom
    # -----------------------------------------------------------------------

    def _SetZoom(self, factor):
        factor = max(_ZOOM_MIN, min(_ZOOM_MAX, factor))
        if abs(factor - self._zoom_factor) < 1e-6:
            return
        self._zoom_factor = factor
        # Fix 6: granularita' scroll proporzionale allo zoom
        self.pixedScrolled = max(1, int(10 / factor))
        self.panel.SetScrollbars(self.pixedScrolled, self.pixedScrolled, 0, 0)
        if self._zoom_label:
            self._zoom_label.SetLabel("%d%%" % round(factor * 100))
        # Fix 1: sincronizza lo slider
        if self._zoom_slider:
            self._zoom_slider.SetValue(int(round(factor * 100)))
        self.panel.Refresh()


    def _ZoomBy(self, delta):
        # Arrotonda al passo piu' vicino per evitare accumulo di errori float
        new = round((self._zoom_factor + delta) / _ZOOM_STEP) * _ZOOM_STEP
        self._SetZoom(new)

    def _OnZoomSlider(self, evt):
        # Converte il valore intero dello slider (30-300) in fattore float
        pct = self._zoom_slider.GetValue()
        factor = round(pct / 100 / _ZOOM_STEP) * _ZOOM_STEP
        self._SetZoom(factor)

    def _OnFitWidth(self, evt):
        """Calcola lo zoom che fa entrare la larghezza del render nel pannello.

        Il calcolo e' stabile: usa la larghezza lorda del pannello (senza
        scrollbar verticale) e il margine dinamico calcolato sulla stessa
        larghezza lorda. Pressioni ripetute su 'Adatta' non cambiano lo zoom.
        """
        if self._last_w <= 0:
            return

        # Larghezza client attuale (potrebbe escludere la scrollbar verticale)
        panel_w, panel_h = self.panel.GetClientSize()

        # Se la scrollbar verticale e' visibile, panel_w e' gia' ridotta;
        # recuperiamo la larghezza lorda sommando la sua ampiezza.
        virtual_h = int(self._last_h * self._zoom_factor) + _PAGE_GAP_PX * 2
        if virtual_h > panel_h:
            sb_w = wx.SystemSettings.GetMetric(wx.SYS_VSCROLL_X)
            panel_w += sb_w if sb_w > 0 else 17

        # Margine calcolato sulla larghezza lorda (stessa formula di OnPaint)
        margin_h = max(8, int(panel_w * 0.03))
        available = panel_w - margin_h * 2
        if available <= 0:
            return

        factor = available / self._last_w

        # Idempotenza: non aggiornare se lo zoom e' gia' convergente (< 0.5%)
        if abs(factor - self._zoom_factor) / max(self._zoom_factor, 0.01) < 0.005:
            return

        self._SetZoom(factor)

    # -----------------------------------------------------------------------
    # Event handlers
    # -----------------------------------------------------------------------

    def _OnCopyButton(self, evt):
        """Rilancia come EVT_HYPERLINK per retrocompatibilità con SongpressFrame."""
        # SongpressFrame si aggancia a EVT_HYPERLINK sul link originale.
        # Poiché ora link == btn_copy (wx.BitmapButton), rilanciamo l'evento
        # come wx.CommandEvent generico catturato da SongpressFrame tramite
        # main_panel.Bind(wx.adv.EVT_HYPERLINK, ..., self.previewCanvas.link).
        # Tuttavia EVT_HYPERLINK e EVT_BUTTON sono tipi diversi; la soluzione
        # più pulita è far sì che SongpressFrame si agganci a EVT_BUTTON.
        # Per non toccare SongpressFrame, creiamo e processiamo un HyperlinkEvent.
        ev = wx.adv.HyperlinkEvent(self.link, self.link.GetId(), "")
        self.link.GetEventHandler().ProcessEvent(ev)

    def _OnMouseWheel(self, evt):
        if evt.ControlDown():
            rot = evt.GetWheelRotation()
            if rot > 0:
                self._ZoomBy(+_ZOOM_STEP)
            elif rot < 0:
                self._ZoomBy(-_ZOOM_STEP)
        else:
            evt.Skip()

    def _OnKeyDown(self, evt):
        key  = evt.GetKeyCode()
        ctrl = evt.ControlDown()
        if ctrl and key == ord('+'):
            self._ZoomBy(+_ZOOM_STEP)
        elif ctrl and key == ord('-'):
            self._ZoomBy(-_ZOOM_STEP)
        elif ctrl and key == ord('0'):
            self._SetZoom(_ZOOM_DEFAULT)
        else:
            evt.Skip()

    def _OnCharHook(self, evt):
        # Fix 5: intercetta Ctrl+PgUp/PgDn per scroll di pagina,
        # Fix 9: Ctrl+Shift+G = fit-to-width
        key  = evt.GetKeyCode()
        ctrl = evt.ControlDown()
        shift = evt.ShiftDown()
        if ctrl and key == wx.WXK_PAGEDOWN:
            # Scorre di un'altezza pagina verso il basso
            _, ph = self.panel.GetClientSize()
            self.panel.Scroll(-1, self.panel.GetScrollPos(wx.VERTICAL) + ph // self.pixedScrolled)
        elif ctrl and key == wx.WXK_PAGEUP:
            # Scorre di un'altezza pagina verso l'alto
            _, ph = self.panel.GetClientSize()
            self.panel.Scroll(-1, max(0, self.panel.GetScrollPos(wx.VERTICAL) - ph // self.pixedScrolled))
        elif ctrl and shift and key == ord('G'):
            # Fix 9: Ctrl+Shift+G = fit-to-width
            self._OnFitWidth(None)
        elif key == wx.WXK_F11:
            self._OnFullscreen(None)
        else:
            evt.Skip()

    def _OnScroll(self, evt):
        self._UpdatePageLabel(self._last_h, int(self._last_h * self._zoom_factor))
        evt.Skip()

    def _OnPanelSize(self, evt):
        # Al ridimensionamento, aggiorna la virtual size se c'e' gia' del contenuto
        if self._last_w > 0:
            panel_client_w, _ = self.panel.GetClientSize()
            margin_h = max(8, int(panel_client_w * 0.03))  # Fix 3: margine dinamico
            vw = int(self._last_w * self._zoom_factor) + margin_h * 2
            vh = int(self._last_h * self._zoom_factor) + _PAGE_GAP_PX * 2
            self.panel.SetVirtualSize(wx.Size(vw, vh))
        evt.Skip()

    # -----------------------------------------------------------------------
    # Label pagina
    # -----------------------------------------------------------------------

    def _UpdatePageLabel(self, content_h_px, virtual_h_px):
        """Aggiorna la label 'Pagina X di Y' in base alla posizione di scroll."""
        if self._page_label is None:
            return
        if content_h_px <= 0:
            self._page_label.SetLabel("")
            return

        # Stima l'altezza di una "pagina" in pixel schermo (96 DPI, A4 portrait)
        page_h_px = self._page_height_px()
        if page_h_px <= 0:
            self._page_label.SetLabel("")
            return

        total_pages = max(1, int(round(content_h_px / page_h_px)))
        # Posizione scroll corrente
        scroll_y = self.panel.GetScrollPos(wx.VERTICAL) * self.pixedScrolled
        current_page = min(total_pages, int(scroll_y / (page_h_px * self._zoom_factor)) + 1)
        self._page_label.SetLabel(_("Page %d of %d") % (current_page, total_pages))

    def _page_height_px(self):
        """Altezza area utile della pagina in pixel a 96 DPI (zoom 1.0).
        = altezza foglio - margine superiore - margine inferiore.
        Usa i valori aggiornati da SetPageSizeMm/SetPageMarginsMm,
        che vengono sincronizzati da SongpressFrame dopo OnPageSetup."""
        usable_h_mm = self._page_h_mm - self._margin_top_mm - self._margin_bottom_mm
        return int(max(10.0, usable_h_mm) / 25.4 * 96)

    # -----------------------------------------------------------------------
    # Debounce refresh
    # -----------------------------------------------------------------------

    def Refresh(self, text):
        """Aggiorna l'anteprima.

        Se _debounceEnabled e' True (default), il ridisegno viene ritardato di
        _DEBOUNCE_MS millisecondi: ogni chiamata successiva prima dello scadere
        del timer annulla e riavvia il timer, cosi' il ridisegno avviene solo
        quando la digitazione si ferma.

        Se _debounceEnabled e' False, il ridisegno avviene immediatamente ad
        ogni chiamata (utile su macchine veloci o per chi preferisce feedback
        istantaneo).
        """
        self._pending_text = text
        # Riapplica layout colonne subito (informazione leggera)
        has_col_break = bool(re.search(r'\{\s*(?:column_break|colb)\s*\}', text, re.IGNORECASE))
        self.renderer.columns = 2 if has_col_break else 1
        self.renderer.columnHeight = 0
        # Riapplica flag
        self.renderer.sd.showPageBreakLines  = self._showPageBreakLines
        self.renderer.sd.showColumnBreakLines = self._showColumnBreakLines

        if not self._debounceEnabled:
            # Ridisegno immediato: cancella eventuale timer pendente e ridisegna subito
            if self._debounce_timer is not None:
                try:
                    self._debounce_timer.Stop()
                except Exception:
                    pass
                self._debounce_timer = None
            self._DoRefresh()
            return

        if self._debounce_timer is not None:
            try:
                self._debounce_timer.Stop()
            except Exception:
                pass
        self._debounce_timer = wx.CallLater(_DEBOUNCE_MS, self._DoRefresh)

    def _DoRefresh(self):
        """Ridisegno effettivo chiamato al termine del debounce."""
        self._debounce_timer = None
        self.text = self._pending_text
        # Riapplica flag anche qui (nel caso il decorator sia cambiato nel frattempo)
        self.renderer.sd.showPageBreakLines  = self._showPageBreakLines
        self.renderer.sd.showColumnBreakLines = self._showColumnBreakLines
        self.panel.Refresh()

    # -----------------------------------------------------------------------
    # Click → focus editor
    # -----------------------------------------------------------------------

    def SetClickCallback(self, callback):
        """Registra una callback chiamata al doppio-click sull'anteprima.

        callback(line_number: int)  — line_number e' 0-based, corrisponde
        alla riga sorgente ChordPro piu' vicina al punto cliccato.
        Impostata da SongpressFrame subito dopo la creazione di PreviewCanvas.
        """
        self._on_click_callback = callback

    # -----------------------------------------------------------------------
    # Hit-test preciso sui SongBox
    # -----------------------------------------------------------------------

    def _HitTestBox(self, click_x, click_y):
        """Restituisce il SongText o SongLine piu' vicino al punto (click_x, click_y)
        nelle coordinate del renderer (pre-zoom, pre-scroll).

        Scende nell'albero SongSong -> SongBlock -> SongLine -> SongText.
        Restituisce (block, line, token) o (None, None, None).
        Le coordinate dei box sono relative al genitore; accumuliamo
        l'offset assoluto durante la discesa.
        """
        song = getattr(self.renderer, 'song', None)
        if song is None:
            return None, None, None

        song_margin_top  = getattr(song, 'marginTop',  0)
        song_margin_left = getattr(song, 'marginLeft', 0)

        best_block = None
        best_line  = None
        best_token = None
        best_dist  = float('inf')

        for block in song.boxes:
            bx = song_margin_left + block.x
            by = song_margin_top  + block.y
            # Distanza verticale dal blocco (0 se siamo dentro)
            dy = max(0, by - click_y, click_y - (by + block.h))
            if dy > best_dist:
                continue
            for line in block.boxes:
                lx = bx + line.x
                ly = by + line.y
                dy2 = max(0, ly - click_y, click_y - (ly + line.h))
                if dy2 > best_dist:
                    continue
                # Cerca il token piu' vicino orizzontalmente
                for token in line.boxes:
                    tx = lx + token.x
                    ty = ly + token.y
                    dx = max(0, tx - click_x, click_x - (tx + token.w))
                    dy3 = max(0, ty - click_y, click_y - (ty + token.h))
                    dist = dx * dx + dy3 * dy3
                    if dist < best_dist:
                        best_dist  = dist
                        best_block = block
                        best_line  = line
                        best_token = token
        return best_block, best_line, best_token

    def _FindSourceLine(self, token_text, block_index):
        """Trova la riga sorgente (0-based) corrispondente a un token renderizzato.

        Strategia a cerchi concentrici attorno alla stima iniziale:
          1. Finestra stretta (±5 righe): cattura il caso esatto
          2. Finestra media (±20 righe): cattura blocchi vicini
          3. Tutto il file: fallback per testo molto ripetuto
        Cosi' un accordo comune come 'DO' che appare 30 volte nel brano
        viene trovato nella posizione giusta invece che alla prima occorrenza.
        """
        if not self.text.strip():
            return 0
        lines = self.text.splitlines()
        n = len(lines)

        # Stima iniziale proporzionale al blocco
        song = self.renderer.song
        total_blocks = max(len(song.boxes), 1)
        start_line = int(block_index / total_blocks * n)
        start_line = max(0, min(start_line, n - 1))

        if not (token_text and token_text.strip()):
            return start_line

        search_text = token_text.strip()

        def _search_range(lo, hi):
            """Cerca search_text nelle righe [lo, hi) in ordine di distanza da start_line."""
            lo = max(0, lo)
            hi = min(n, hi)
            # Ordina per distanza crescente da start_line
            indices = sorted(range(lo, hi), key=lambda i: abs(i - start_line))
            for i in indices:
                if search_text in lines[i]:
                    return i
            return None

        # 1. Finestra stretta: ±5 righe
        result = _search_range(start_line - 5, start_line + 6)
        if result is not None:
            return result

        # 2. Finestra media: ±20 righe
        result = _search_range(start_line - 20, start_line + 21)
        if result is not None:
            return result

        # 3. Tutto il file, sempre per distanza da start_line
        result = _search_range(0, n)
        if result is not None:
            return result

        return start_line

    def _OnDoubleClick(self, evt):
        """Doppio-click sul canvas: hit-test preciso sui SongBox e focus editor.

        Flusso:
          1. Converte le coordinate del click in coordinate renderer
             (corregge scroll e zoom, sottrae il margine dinamico)
          2. Scende nell'albero SongSong->SongBlock->SongLine->SongText
             trovando il token piu' vicino al click
          3. Cerca il testo del token nel sorgente ChordPro
          4. Chiama la callback con il numero di riga 0-based
        """
        if self._on_click_callback is None or self._last_h <= 0:
            evt.Skip()
            return
        if not self._dblClickFocusEnabled:
            evt.Skip()
            return

        # 1. Coordinate del click in pixel virtuali (scroll-corrected)
        click_x_sc, click_y_sc = self.panel.CalcUnscrolledPosition(evt.GetPosition())

        # Rimuovi il margine orizzontale dinamico applicato in OnPaint
        panel_client_w, _ = self.panel.GetClientSize()
        margin_h = max(8, int(panel_client_w * 0.03))

        # Converti in coordinate renderer (pre-zoom)
        rx = (click_x_sc - margin_h) / self._zoom_factor
        ry = click_y_sc / self._zoom_factor

        # 2. Hit-test sull'albero dei box
        block, line, token = self._HitTestBox(rx, ry)

        if token is not None:
            # 3. Trova la riga sorgente
            token_text = getattr(token, 'text', '')
            block_idx  = self.renderer.song.boxes.index(block) if block is not None else 0
            line_num   = self._FindSourceLine(token_text, block_idx)
        else:
            # Fallback: stima lineare sulla Y
            src_lines = self.text.count('\n') + 1 if self.text.strip() else 1
            avg_h = self._last_h / max(src_lines, 1)
            line_num = max(0, min(int(ry / avg_h), src_lines - 1))

        self._on_click_callback(line_num)
        evt.Skip()

    # -----------------------------------------------------------------------
    # Tutto schermo
    # -----------------------------------------------------------------------

    def _OnFullscreen(self, evt):
        """Apre o chiude la finestra fullscreen dell'anteprima."""
        if self._fullscreen_frame is not None:
            # Gia' aperta: chiudi
            try:
                self._fullscreen_frame.Close()
            except Exception:
                pass
            self._fullscreen_frame = None
            return

        # Crea la frame fullscreen
        fs_frame = _FullscreenPreviewFrame(self)
        self._fullscreen_frame = fs_frame
        fs_frame.Show()
        fs_frame.ShowFullScreen(True, wx.FULLSCREEN_ALL)

    # -----------------------------------------------------------------------
    # API pubblica (invariata rispetto alla versione originale)
    # -----------------------------------------------------------------------

    def SetColumns(self, columns):
        """Imposta il numero di colonne per il layout dell'anteprima."""
        self.renderer.columns = columns
        self.renderer.columnHeight = 0

    def SetDecorator(self, sd):
        self.renderer.SetDecorator(sd)
        sd.showPageBreakLines  = self._showPageBreakLines
        sd.showColumnBreakLines = self._showColumnBreakLines

    def SetLineWidths(self, titleLineWidth, verseBoxWidth):
        self.renderer.sd.titleLineWidth = titleLineWidth
        self.renderer.sd.verseBoxWidth  = verseBoxWidth

    def SetChordsBelow(self, below):
        self.renderer.SetChordsBelow(below)

    def SetShowPageBreakLines(self, show):
        """Mostra o nasconde la linea di interruzione di pagina nell'anteprima."""
        self._showPageBreakLines = show
        self.renderer.sd.showPageBreakLines = show

    def SetShowColumnBreakLines(self, show):
        """Mostra o nasconde la linea di interruzione di colonna nell'anteprima."""
        self._showColumnBreakLines = show
        self.renderer.sd.showColumnBreakLines = show

    def SetTempoDisplay(self, tempoDisplay):
        self.renderer.tempoDisplay = tempoDisplay

    def SetTempoIconSize(self, size):
        """Imposta la dimensione in pixel delle icone {tempo_*} (16, 24 o 32)."""
        self.renderer.tempoIconSize = size

    def SetGridDisplayMode(self, mode):
        """Imposta la modalità di visualizzazione dei blocchi {start_of_grid}.

        Valori: 'pipe' | 'plain' | 'table'
        Forza immediatamente il ridisegno del pannello anteprima.
        """
        self.renderer.gridDisplayMode = mode if mode in ('pipe', 'plain', 'table') else 'pipe'
        self.panel.Refresh()

    def SetGridDefaultLabel(self, label):
        """Imposta l'etichetta predefinita per i blocchi {start_of_grid} senza label.

        Forza immediatamente il ridisegno del pannello anteprima.
        """
        self.renderer.gridDefaultLabel = label if label and label.strip() else None
        self.panel.Refresh()

    def SetGridSizeDir(self, sizedir):
        """Imposta la direzione di applicazione di size=N per i blocchi {start_of_grid}.

        Valori: 'both' | 'horizontal' | 'vertical'
        Forza immediatamente il ridisegno del pannello anteprima.
        """
        self.renderer.gridSizeDir = sizedir if sizedir in ('both', 'horizontal', 'vertical') else 'both'
        self.panel.Refresh()

    def SetTimeDisplay(self, show):
        self.renderer.timeDisplay = show

    def SetKeyDisplay(self, show):
        self.renderer.keyDisplay = show

    # -----------------------------------------------------------------------
    # Zoom pubblico (usabile da SongpressFrame se necessario)
    # -----------------------------------------------------------------------

    def SetPageSizeMm(self, w_mm, h_mm):
        """Aggiorna le dimensioni del foglio (mm) usate per il calcolo
        dell'indicatore di pagina. Chiamare dopo ogni modifica in OnPageSetup."""
        self._page_w_mm = float(w_mm)
        self._page_h_mm = float(h_mm)
        if self._last_h > 0:
            self._UpdatePageLabel(self._last_h, int(self._last_h * self._zoom_factor))

    def SetPageMarginsMm(self, top_mm, bottom_mm):
        """Aggiorna i margini superiore e inferiore (mm) per il calcolo
        dell'indicatore di pagina. Chiamare dopo ogni modifica in OnPageSetup."""
        self._margin_top_mm    = float(top_mm)
        self._margin_bottom_mm = float(bottom_mm)
        if self._last_h > 0:
            self._UpdatePageLabel(self._last_h, int(self._last_h * self._zoom_factor))

    def GetZoom(self):
        """Restituisce il fattore di zoom corrente (1.0 = 100%)."""
        return self._zoom_factor

    def SetZoom(self, factor):
        """Imposta il fattore di zoom (es. 0.75 = 75%, 1.5 = 150%)."""
        self._SetZoom(factor)

    def SetShowPageIndicator(self, show):
        """Mostra o nasconde la label 'Pagina X di Y' nella toolbar."""
        if self._page_label is None:
            return
        self._page_label.Show(show)
        # Aggiorna subito il testo se stiamo mostrando
        if show:
            self._UpdatePageLabel(self._last_h, int(self._last_h * self._zoom_factor))
        else:
            self._page_label.SetLabel("")
        # Forza ricalcolo layout della toolbar
        parent = self._page_label.GetParent()
        if parent:
            parent.Layout()

    def SetGreyBackground(self, grey):
        """Imposta sfondo grigio (True) o bianco (False) nel pannello anteprima."""
        self._greyBackground = bool(grey)   # aggiorna il flag letto da OnPaint
        self.panel.Refresh()                # forza ridisegno con il nuovo sfondo

    def SetDblClickFocus(self, enabled):
        """Abilita (True) o disabilita (False) il focus editor al doppio-click.

        Se disabilitato, il doppio-click sull'anteprima non sposta il cursore
        nell'editor. Utile per chi usa il doppio-click per selezionare testo
        nell'anteprima senza voler perdere il contesto nell'editor.
        """
        self._dblClickFocusEnabled = bool(enabled)

    def SetDebounce(self, enabled):
        """Abilita (True) o disabilita (False) il debounce del refresh.

        Con debounce attivo il ridisegno avviene solo dopo _DEBOUNCE_MS ms
        di inattivita' sulla tastiera (risparmia CPU durante la digitazione
        rapida). Con debounce disattivo ogni modifica al testo provoca un
        ridisegno immediato.
        """
        self._debounceEnabled = bool(enabled)

    def SetMinSizeEnabled(self, enabled):
        """Imposta (True) o rimuove (False) la dimensione minima del pannello anteprima.

        Quando abilitato il pannello non puo' essere ridimensionato al di sotto
        di 370x520 px, ne' all'avvio ne' trascinando il separatore AUI.
        Quando disabilitato il pannello non ha vincoli di dimensione minima.
        La modifica e' immediata; per avere effetto al prossimo avvio sull'AUI
        manager occorre che SongpressFrame chiami .MinSize() sul pane.
        """
        if bool(enabled):
            self.main_panel.SetMinSize(wx.Size(370, 520))
        else:
            self.main_panel.SetMinSize(wx.Size(-1, -1))
        parent = self.main_panel.GetParent()
        if parent is not None:
            parent.Layout()


# ---------------------------------------------------------------------------
# Finestra fullscreen per l anteprima
# ---------------------------------------------------------------------------

class _FullscreenPreviewFrame(wx.Frame):
    """Finestra a tutto schermo che mostra una copia sincronizzata dell anteprima.

    Non crea un nuovo PreviewCanvas (per non duplicare il renderer) ma disegna
    direttamente usando lo stesso renderer del canvas originale. Il contenuto e
    sempre aggiornato perche _FullscreenPreviewFrame chiama renderer.Render()
    ad ogni OnPaint con self.owner.text e self.owner._zoom_factor.

    Chiusura: Esc, F11, o il pulsante Chiudi nella toolbar.
    """

    def __init__(self, owner):
        wx.Frame.__init__(
            self, None, wx.ID_ANY,
            title=_("Preview — press Esc or F11 to exit full screen"),
            style=wx.DEFAULT_FRAME_STYLE,
        )
        self.owner = owner

        # ── Toolbar minimale ──────────────────────────────────────────────
        toolbar = wx.Panel(self, style=wx.BORDER_NONE)
        toolbar.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        tb_sz = wx.BoxSizer(wx.HORIZONTAL)

        btn_close = wx.Button(toolbar, wx.ID_ANY, _("Exit full screen (Esc / F11)"),
                              style=wx.BORDER_SIMPLE)
        tb_sz.Add(btn_close, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)

        # Zoom out/slider/in nella finestra fullscreen
        btn_zm = wx.BitmapButton(toolbar, wx.ID_ANY,
            wx.ArtProvider.GetBitmap(wx.ART_MINUS, wx.ART_TOOLBAR, (16, 16)),
            style=wx.BORDER_NONE)
        self._fs_slider = wx.Slider(
            toolbar, wx.ID_ANY,
            value=int(round(owner._zoom_factor * 100)),
            minValue=int(_ZOOM_MIN * 100), maxValue=int(_ZOOM_MAX * 100),
            size=(120, -1), style=wx.SL_HORIZONTAL,
        )
        btn_zp = wx.BitmapButton(toolbar, wx.ID_ANY,
            wx.ArtProvider.GetBitmap(wx.ART_PLUS, wx.ART_TOOLBAR, (16, 16)),
            style=wx.BORDER_NONE)
        self._fs_zoom_label = wx.StaticText(toolbar,
            label="%d%%" % int(round(owner._zoom_factor * 100)),
            size=(40, -1), style=wx.ALIGN_CENTRE_HORIZONTAL)

        btn_fit = wx.Button(toolbar, wx.ID_ANY, _("Fit"), style=wx.BORDER_SIMPLE)
        btn_fit.SetToolTip(_("Fit preview width to panel (Ctrl+Shift+G)"))

        tb_sz.AddSpacer(8)
        tb_sz.Add(btn_zm,              0, wx.ALIGN_CENTER_VERTICAL)
        tb_sz.Add(self._fs_slider,     0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT, 2)
        tb_sz.Add(btn_zp,              0, wx.ALIGN_CENTER_VERTICAL)
        tb_sz.Add(self._fs_zoom_label, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 4)
        tb_sz.AddSpacer(8)
        tb_sz.Add(btn_fit,             0, wx.ALIGN_CENTER_VERTICAL)

        toolbar.SetSizer(tb_sz)
        toolbar.Layout()

        # ── Canvas scrolled ───────────────────────────────────────────────
        self._panel = wx.ScrolledWindow(self, style=wx.BORDER_NONE)
        self._panel.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self._pix = 10
        self._panel.SetScrollbars(self._pix, self._pix, 0, 0)

        outer = wx.BoxSizer(wx.VERTICAL)
        outer.Add(toolbar, 0, wx.EXPAND)
        outer.Add(wx.StaticLine(self), 0, wx.EXPAND)
        outer.Add(self._panel, 1, wx.EXPAND)
        self.SetSizer(outer)

        # ── Bind ─────────────────────────────────────────────────────────
        btn_close.Bind(wx.EVT_BUTTON,  self._OnClose)
        btn_zm.Bind(wx.EVT_BUTTON,     lambda e: self._ZoomBy(-_ZOOM_STEP))
        btn_zp.Bind(wx.EVT_BUTTON,     lambda e: self._ZoomBy(+_ZOOM_STEP))
        btn_fit.Bind(wx.EVT_BUTTON,    self._OnFit)
        self._fs_slider.Bind(wx.EVT_SLIDER, self._OnSlider)
        self._panel.Bind(wx.EVT_PAINT,       self._OnPaint)
        self._panel.Bind(wx.EVT_MOUSEWHEEL,  self._OnWheel)
        self._panel.Bind(wx.EVT_LEFT_DCLICK, self._OnDblClick)
        # EVT_CHAR_HOOK sulla FRAME (non sul panel): in fullscreen il focus
        # iniziale e' sulla frame, non sul ScrolledWindow, quindi ESC/F11
        # non raggiungevano il panel. Bindando sulla frame li catturiamo sempre.
        self.Bind(wx.EVT_CHAR_HOOK, self._OnChar)
        self.Bind(wx.EVT_CLOSE,     self._OnCloseEvt)

        self._zoom = owner._zoom_factor
        self.SetSize(wx.GetDisplaySize())

    # ── Zoom helpers ──────────────────────────────────────────────────────

    def _SetZoom(self, factor):
        factor = max(_ZOOM_MIN, min(_ZOOM_MAX, factor))
        self._zoom = factor
        self._fs_zoom_label.SetLabel("%d%%" % int(round(factor * 100)))
        self._fs_slider.SetValue(int(round(factor * 100)))
        self._panel.Refresh()

    def _ZoomBy(self, delta):
        new = round((self._zoom + delta) / _ZOOM_STEP) * _ZOOM_STEP
        self._SetZoom(new)

    def _OnSlider(self, evt):
        pct = self._fs_slider.GetValue()
        self._SetZoom(round(pct / 100 / _ZOOM_STEP) * _ZOOM_STEP)

    def _OnFit(self, evt):
        pw, ph = self._panel.GetClientSize()
        last_w = getattr(self.owner, '_last_w', 0)
        if last_w > 0 and pw > 16:
            margin = max(8, int(pw * 0.03))
            available = pw - margin * 2
            if available > 0:
                factor = available / last_w
                # Idempotenza: non aggiornare se gia' convergente
                if abs(factor - self._zoom) / max(self._zoom, 0.01) >= 0.005:
                    self._SetZoom(factor)

    # ── Paint ─────────────────────────────────────────────────────────────

    def _OnPaint(self, evt):
        dc = wx.AutoBufferedPaintDC(self._panel)
        self._panel.PrepareDC(dc)
        bg = wx.Colour(160, 160, 160) if self.owner._greyBackground else wx.WHITE
        dc.SetBackground(wx.Brush(bg))
        dc.Clear()
        text = self.owner.text
        if not text.strip():
            return
        dc.SetUserScale(self._zoom, self._zoom)
        w, h = self.owner.renderer.Render(text, dc)
        dc.SetUserScale(1.0, 1.0)
        pw, _ = self._panel.GetClientSize()
        margin = max(8, int(pw * 0.03))
        vw = int(w * self._zoom) + margin * 2
        vh = int(h * self._zoom) + _PAGE_GAP_PX * 2
        self._panel.SetVirtualSize(wx.Size(vw, vh))

    # ── Input ─────────────────────────────────────────────────────────────

    def _OnWheel(self, evt):
        if evt.ControlDown():
            self._ZoomBy(+_ZOOM_STEP if evt.GetWheelRotation() > 0 else -_ZOOM_STEP)
        else:
            evt.Skip()

    def _OnChar(self, evt):
        key = evt.GetKeyCode()
        if key in (wx.WXK_ESCAPE, wx.WXK_F11):
            self._OnClose(evt)
        else:
            evt.Skip()

    def _OnDblClick(self, evt):
        """Doppio-click nella finestra fullscreen: usa lo stesso hit-test preciso."""
        if self.owner._on_click_callback is None:
            evt.Skip()
            return
        if not getattr(self.owner, '_dblClickFocusEnabled', True):
            evt.Skip()
            return
        if getattr(self.owner, '_last_h', 0) <= 0:
            evt.Skip()
            return

        # Coordinate del click corrette per scroll e zoom della finestra fullscreen
        click_x_sc, click_y_sc = self._panel.CalcUnscrolledPosition(evt.GetPosition())
        pw, _ = self._panel.GetClientSize()
        margin_h = max(8, int(pw * 0.03))
        rx = (click_x_sc - margin_h) / self._zoom
        ry = click_y_sc / self._zoom

        # Riusa il hit-test del canvas principale (stesso renderer)
        block, line, token = self.owner._HitTestBox(rx, ry)
        if token is not None:
            token_text = getattr(token, 'text', '')
            block_idx  = self.owner.renderer.song.boxes.index(block) if block is not None else 0
            line_num   = self.owner._FindSourceLine(token_text, block_idx)
        else:
            src_lines = self.owner.text.count('\n') + 1 if self.owner.text.strip() else 1
            avg_h = self.owner._last_h / max(src_lines, 1)
            line_num = max(0, min(int(ry / avg_h), src_lines - 1))

        self.owner._on_click_callback(line_num)
        evt.Skip()

    # ── Chiusura ──────────────────────────────────────────────────────────

    def _OnClose(self, evt):
        self.owner._fullscreen_frame = None
        self.ShowFullScreen(False)
        self.Destroy()

    def _OnCloseEvt(self, evt):
        self.owner._fullscreen_frame = None
        evt.Skip()
