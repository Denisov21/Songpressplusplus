###############################################################
# Name:         SongpressToolbars.py
# Purpose:      Toolbar construction mixin for Songpress++
# Author:       Denisov21
# Created:      2026
# Copyright:    Modifications © 2026 Denisov21
# License:      GNU GPL v2
###############################################################

import wx
import wx.lib.agw.aui as aui
from wx import xrc

from .FontComboBox import FontComboBox
from .Globals import glb

_ = wx.GetTranslation


class ShowChordsChoice(wx.Choice):
    """Menu a tendina a 3 voci che sostituisce il vecchio wx.Slider
    "mostra accordi".

    Vantaggi rispetto allo Slider:
      * segue nativamente il tema chiaro/scuro di GTK3 (niente riquadro
        chiaro fisso sul tema scuro);
      * le tre modalità sono etichettate in chiaro invece di essere tre
        tacche mute.

    L'indice selezionato (0/1/2) coincide con pref.format.showChords, quindi
    l'API GetValue()/SetValue() del vecchio Slider è mantenuta e il resto del
    codice (OnFontSelected, SetFont, ...) non richiede modifiche.

    Le etichette riusano stringhe gettext già presenti nel menu
    "Show chords for", così non servono nuove traduzioni nei .po.
    """

    def __init__(self, parent, id=wx.ID_ANY, value=0,
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0):
        labels = [
            _(u"No chords"),
            _(u"One verse for each chord pattern"),
            _(u"Whole song"),
        ]
        super().__init__(parent, id, pos, size, choices=labels, style=style)
        self.SetSelection(max(0, min(2, int(value))))
        self._freezeSize()

    #: Margine (px) per la freccia del dropdown + bordi, che GTK3 non
    #: include in modo affidabile nella sola misura del testo.
    _ARROW_MARGIN = 44
    #: Larghezza minima di sicurezza contro il width=0 su GTK3.
    _MIN_WIDTH = 120

    def _freezeSize(self):
        """Fissa una dimensione esplicita e deterministica, larga quanto
        l'etichetta più lunga.

        Su GTK3, quando un wx.Choice viene aggiunto a una AuiToolBar con
        AddControl, la toolbar interroga GetBestSize()/MinSize durante il
        Realize: se il widget non è ancora completamente realizzato può
        restituire larghezza 0 e la toolbar riserva 0 px → il menu a tendina
        "a volte non appare" (in tema chiaro e scuro). Congelando una MinSize
        concreta la toolbar riserva sempre lo spazio corretto e il controllo
        viene disegnato in modo affidabile.

        La larghezza è calcolata sull'etichetta più lunga misurata con il
        font reale del controllo (GetTextExtent) più un margine per la
        freccia del dropdown e i bordi, così il testo non viene mai troncato.
        Nessun tetto massimo: la voce "Una strofa per ogni schema di accordi"
        deve rientrare per intero.
        """
        best = self.GetBestSize()
        # Etichette effettive del controllo (già tradotte).
        labels = [self.GetString(i) for i in range(self.GetCount())]
        text_w = max((self.GetTextExtent(lbl).width for lbl in labels),
                     default=0)
        w = max(text_w + self._ARROW_MARGIN, best.width, self._MIN_WIDTH)
        h = best.height if best.height > 10 else -1
        size = wx.Size(int(w), h)
        self.SetInitialSize(size)
        self.SetMinSize(size)

    # ── Compatibilità con l'API del vecchio wx.Slider ────────────────
    def GetValue(self):
        sel = self.GetSelection()
        return sel if sel != wx.NOT_FOUND else 0

    def SetValue(self, v):
        self.SetSelection(max(0, min(2, int(v))))


class SongpressToolbarsMixin:
    """Mixin che raccoglie la costruzione delle tre AuiToolBar di Songpress++.

    Deve essere ereditato insieme a SongpressFrame (o la sua base SDIMainFrame)
    in modo che self.frame, self.pref, self.AddPane, self.AddTool e i bind
    agli handler siano già disponibili quando _BuildToolbars() viene chiamato.

    Uso tipico nel __init__ di SongpressFrame, subito dopo la creazione dei pane
    principali::

        self._BuildToolbars()
    """

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _toolbarBitmapSize(self):
        """Restituisce la dimensione corrente delle icone toolbar come wx.Size."""
        px = getattr(self.pref, 'toolbarIconPx', 16)
        return wx.Size(px, px)

    def _toolbarControlHeight(self):
        """Altezza massima per i controlli custom (Slider, ComboBox)
        aggiunti alla toolbar via AddControl.

        Corrisponde all'altezza del contenuto di un tool standard
        (icona + 2 × tool_border_padding) così la riga della format
        toolbar non diventa più alta delle altre.
        """
        px = getattr(self.pref, 'toolbarIconPx', 16)
        return px + 6  # 6 = 2 × tool_border_padding (default 3)

    @staticmethod
    def _styleSliderForTheme(slider):
        """Fa sì che un wx.Slider segua il tema di sistema (chiaro/scuro).

        Su GTK3 (Debian/KDE) wx.Slider disegna uno sfondo chiaro fisso
        (#F0F0F0): con un tema scuro appare come un riquadro chiaro
        "sospeso" nella toolbar (il controllo "non si vede"). Allineando
        background e foreground ai colori di sistema il controllo si fonde
        con la toolbar sia in tema chiaro sia in tema scuro.

        SYS_COLOUR_BTNFACE è lo stesso colore base usato dall'art provider
        di AuiToolBar con AUI_TB_PLAIN_BACKGROUND, quindi lo slider combacia
        con lo sfondo della toolbar su cui è collocato.
        """
        if slider is None:
            return
        slider.SetBackgroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_BTNFACE))
        slider.SetForegroundColour(
            wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOWTEXT))

    def _scaledToolbarBitmap(self, image_path):
        """Carica un'immagine e, se la dimensione toolbar è maggiore,
        la centra su un canvas trasparente più grande senza riscalare,
        così l'icona resta nitida pixel-per-pixel."""
        img = wx.Image(glb.AddPath(image_path))
        px = getattr(self.pref, 'toolbarIconPx', 16)
        if px != 16 and img.IsOk():
            img = self._padImageToSize(img, px)
        return wx.Bitmap(img)

    @staticmethod
    def _padImageToSize(img, px):
        """Centra un wx.Image su un canvas trasparente px×px."""
        w, h = img.GetWidth(), img.GetHeight()
        canvas = wx.Image(px, px)
        canvas.InitAlpha()
        # Imposta tutto il canvas trasparente con un blocco di byte
        canvas.SetAlpha(bytes(px * px))
        # Centra l'icona originale
        ox = (px - w) // 2
        oy = (px - h) // 2
        canvas.Paste(img, ox, oy)
        return canvas

    def _RealizeToolbar(self, toolbar):
        """Realize della toolbar + vincoli di dimensione sul pane.

        NON chiama _mgr.Update(): quando più toolbar vengono ricostruite
        insieme, serve un singolo Update finale tramite
        _FinalizeToolbarLayout() per evitare layout intermedi incoerenti.
        """
        toolbar.SetGripperVisible(False)
        toolbar.Realize()
        sz = toolbar.GetMinSize()
        pane = self._mgr.GetPane(toolbar)
        if pane.IsOk():
            pane.BestSize(sz)
            pane.MaxSize(sz)
            pane.MinSize(sz)

    def _FinalizeToolbarLayout(self):
        """Ricalcola il layout di tutte le toolbar con MaxSize = contenuto.

        MaxSize impedisce ad AUI di allargare il pane oltre la
        dimensione reale del contenuto → niente spazio bianco.
        MinSize(1,1) resta basso per consentire l'overflow (»»)
        quando la finestra è troppo stretta.
        """
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
        # toolbar non esistono piu', non c'e' layout da ricalcolare.
        if getattr(self, '_mgr', None) is None:
            return
        if not all(getattr(self, name, None) is not None for name in
                   ('mainToolBar', 'formatToolBar',
                    'insertToolBar', 'viewToolBar')):
            return
        # Se l'AUI manager e' gia' stato smontato (chiusura/riavvio) o le
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
                tb.SetGripperVisible(False)
                tb.Realize()
                sz = tb.GetMinSize()
                pane = self._mgr.GetPane(tb)
                if pane.IsOk():
                    pane.BestSize(sz)
                    pane.MaxSize(sz)
                    pane.MinSize(sz)
            self._mgr.DoUpdate()
            # DoUpdate → SwitchToolBarOrientation forza
            # SetGripperVisible(True) sulle toolbar: resettiamo
            # subito perché il pane ha Gripper(False) e AUI non
            # riserva spazio per il gripper nel layout.
            for tb in (self.mainToolBar, self.formatToolBar,
                       self.insertToolBar, self.viewToolBar):
                tb.SetGripperVisible(False)
            self.frame.SendSizeEvent()

            # Windows: dopo un rebuild i vecchi StaticBitmap (icone font,
            # accordi) vengono distrutti e ricreati; la zona che occupavano
            # non viene invalidata, così i pixel della vecchia icona restano
            # come "fantasma" (icona doppia) finché un WM_PAINT — tipicamente
            # il passaggio del mouse — non ridisegna quell'area. Forziamo qui
            # un erase+repaint pulito di ogni toolbar e dei suoi controlli
            # figli, eliminando il fantasma senza bisogno dell'hover.
            # È un problema specifico di wxMSW: su GTK/macOS non serve.
            if wx.Platform == '__WXMSW__':
                for tb in (self.mainToolBar, self.formatToolBar,
                           self.insertToolBar, self.viewToolBar):
                    tb.Refresh(eraseBackground=True)
                    for child in tb.GetChildren():
                        child.Refresh()
                    tb.Update()
        finally:
            self._tb_finalizing = False

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def _BuildToolbars(self):
        """Costruisce mainToolBar, formatToolBar, insertToolBar e viewToolBar e
        le aggiunge all'AUI manager."""
        self._BuildMainToolBar()
        self._BuildFormatToolBar()
        self._BuildInsertToolBar()
        self._BuildViewToolBar()

    # ------------------------------------------------------------------
    # Standard toolbar — mappa icone/flag di visibilità
    # ------------------------------------------------------------------

    MAIN_TOOLBAR_ITEMS = [
        ('new',          _(u'New'),            'tbm_new'),
        ('open',         _(u'Open'),           'tbm_open'),
        ('save',         _(u'Save'),           'tbm_save'),
        ('printPreview', _(u'Print preview'),  'tbm_printPreview'),
        ('print',        _(u'Print'),          'tbm_print'),
        ('undo',         _(u'Undo'),           'tbm_undo'),
        ('redo',         _(u'Redo'),           'tbm_redo'),
        ('cut',          _(u'Cut'),            'tbm_cut'),
        ('copy',         _(u'Copy'),           'tbm_copy'),
        ('copyAsImage',  _(u'Copy as image'),  'tbm_copyAsImage'),
        ('paste',        _(u'Paste'),          'tbm_paste'),
        ('pasteChords',  _(u'Paste chords'),   'tbm_pasteChords'),
        ('syntaxCheck',  _(u'Check syntax'),   'tbm_syntaxCheck'),
        ('options',      _(u'Options...'),     'tbm_options'),
    ]

    _MAIN_TOOLBAR_SEPARATORS_AFTER = {
        'save', 'print', 'redo', 'pasteChords', 'syntaxCheck',
    }

    def _ApplyMainToolBarVisibility(self):
        """Ricostruisce la main toolbar rispettando i flag tbm_* in self.pref."""
        self.mainToolBar.SetToolBitmapSize(self._toolbarBitmapSize())
        self.mainToolBar.ClearTools()

        prev_was_sep = True
        last_added = None

        for xrc_name, label, pref_key in self.MAIN_TOOLBAR_ITEMS:
            if not getattr(self.pref, pref_key, True):
                continue
            if last_added in self._MAIN_TOOLBAR_SEPARATORS_AFTER and not prev_was_sep:
                self.mainToolBar.AddSeparator()
                prev_was_sep = True
            tool = self.AddTool(self.mainToolBar, xrc_name,
                                self._main_toolbar_icons[xrc_name],
                                label,
                                self._main_toolbar_helps[xrc_name])
            # Aggiorna i riferimenti agli strumenti usati da OnIdle / UpdateUI
            if xrc_name == 'save':
                self.saveTool = tool
            elif xrc_name == 'undo':
                self.undoTool = tool
            elif xrc_name == 'redo':
                self.redoTool = tool
            elif xrc_name == 'cut':
                self.cutTool = tool
            elif xrc_name == 'copy':
                self.copyTool = tool
            elif xrc_name == 'paste':
                self.pasteTool = tool
            elif xrc_name == 'pasteChords':
                self.pasteChordsTool = tool
            elif xrc_name == 'syntaxCheck':
                self.syntaxCheckTool = tool
            prev_was_sep = False
            last_added = xrc_name

        self._RealizeToolbar(self.mainToolBar)

    # ------------------------------------------------------------------
    # Format toolbar — mappa icone/flag di visibilità
    # ------------------------------------------------------------------

    FORMAT_TOOLBAR_ITEMS = [
        ('fontChooser',       _(u'Font used in the Songpress++ preview'),      'tbf_fontChooser'),
        ('showChordsChooser', _(u'Hide or show chords in the formatted song'), 'tbf_showChords'),
        ('insertLinespacing', _(u'Linespacing'),                               'tbf_insertLinespacing'),
    ]

    _FORMAT_TOOLBAR_SEPARATORS_AFTER = {'showChordsChooser'}

    def _ApplyFormatToolBarVisibility(self):
        """Ricostruisce la format toolbar in base ai flag tbf_* in self.pref.

        AuiToolBar non gestisce in modo affidabile Show/Hide sui controlli
        custom (FontComboBox, Slider) aggiunti via AddControl: l'unico approccio
        robusto è distruggere i controlli esistenti e ricrearli, esattamente come
        fanno _ApplyMainToolBarVisibility e _ApplyInsertToolBarVisibility.
        """
        show_font   = getattr(self.pref, 'tbf_fontChooser',       True)
        show_chords = getattr(self.pref, 'tbf_showChords',         True)
        show_ls     = getattr(self.pref, 'tbf_insertLinespacing',  True)

        # Salva il valore corrente di fontChooser e showChordsChooser
        # prima di distruggerli, per poterlo ripristinare dopo.
        saved_font_face   = self.pref.format.face
        saved_show_chords = self.pref.format.showChords

        # Distrugge i controlli custom (FontComboBox e Slider) prima di
        # ClearTools, altrimenti restano orfani nella toolbar.
        for ctrl in getattr(self, '_format_font_controls', []):
            ctrl.Destroy()
        self._format_font_controls = []
        for ctrl in getattr(self, '_format_chords_controls', []):
            ctrl.Destroy()
        self._format_chords_controls = []

        self.formatToolBar.SetToolBitmapSize(self._toolbarBitmapSize())
        self.formatToolBar.ClearTools()

        # ── Carattere ─────────────────────────────────────────────────
        if show_font:
            fontIcon = wx.StaticBitmap(
                self.formatToolBar, -1,
                self._scaledToolbarBitmap('img/font1.png')
            )
            fontIcon.SetToolTip(_("Font used in the Songpress++ preview"))
            self.formatToolBar.AddControl(fontIcon)
            self.fontChooser = FontComboBox(self.formatToolBar, -1, saved_font_face)
            self.fontChooser.SetToolTip(_("Font used in the Songpress++ preview"))
            self.formatToolBar.AddControl(self.fontChooser)
            self.frame.Bind(wx.EVT_COMBOBOX,        self.OnFontSelected, self.fontChooser)
            self.fontChooser.Bind(wx.EVT_TEXT_ENTER, self.OnFontSelected, self.fontChooser)
            self.fontChooser.Bind(wx.EVT_KILL_FOCUS, self.OnFontSelected, self.fontChooser)
            self._format_font_controls = [fontIcon, self.fontChooser]
        else:
            # fontChooser non esiste più: crea un dummy non visibile per
            # non rompere il codice che chiama self.fontChooser.SetValue()
            self.fontChooser = FontComboBox(self.formatToolBar, -1, saved_font_face)
            self.fontChooser.Hide()
            self._format_font_controls = []

        # ── Mostra/nascondi accordi ────────────────────────────────────
        if show_chords:
            showChordsIcon = wx.StaticBitmap(
                self.formatToolBar, -1,
                self._scaledToolbarBitmap('img/showChords.png')
            )
            self.formatToolBar.AddControl(showChordsIcon)
            self.showChordsChooser = ShowChordsChoice(
                self.formatToolBar, -1, saved_show_chords
            )
            tt1 = wx.ToolTip(_("Hide or show chords in the formatted song"))
            tt2 = wx.ToolTip(_("Hide or show chords in the formatted song"))
            self.showChordsChooser.SetToolTip(tt1)
            showChordsIcon.SetToolTip(tt2)
            self.frame.Bind(wx.EVT_CHOICE, self.OnFontSelected, self.showChordsChooser)
            self.formatToolBar.AddControl(self.showChordsChooser, "pippo")
            self._format_chords_controls = [showChordsIcon, self.showChordsChooser]
        else:
            # showChordsChooser non esiste più: dummy nascosto
            self.showChordsChooser = ShowChordsChoice(
                self.formatToolBar, -1, saved_show_chords
            )
            self.showChordsChooser.Hide()
            self._format_chords_controls = []

        # ── Interlinea ─────────────────────────────────────────────────
        if show_font or show_chords:
            self.formatToolBar.AddSeparator()
        if show_ls:
            self.AddTool(self.formatToolBar, 'insertLinespacing', 'img/line_spacing.png',
                         _(u"Linespacing"), _(u"Insert a {linespacing} command"))

        self._RealizeToolbar(self.formatToolBar)

    # ------------------------------------------------------------------
    # Main toolbar  (Standard)
    # ------------------------------------------------------------------

    def _BuildMainToolBar(self):
        self.mainToolBar = aui.AuiToolBar(
            self.frame, wx.ID_ANY, wx.DefaultPosition,
            agwStyle=aui.AUI_TB_PLAIN_BACKGROUND | aui.AUI_TB_OVERFLOW
        )
        self.mainToolBar.SetToolBitmapSize(self._toolbarBitmapSize())

        self._main_toolbar_icons = {
            'new':          'img/new.png',
            'open':         'img/open.png',
            'save':         'img/save.png',
            'printPreview': 'img/printPreview.png',
            'print':        'img/print.png',
            'undo':         'img/undo.png',
            'redo':         'img/redo.png',
            'cut':          'img/cut.png',
            'copy':         'img/copy.png',
            'copyAsImage':  'img/copyAsImage2.png',
            'paste':        'img/paste.png',
            'pasteChords':  'img/pasteChords.png',
            'syntaxCheck':  'img/syntaxCheck.png',
            'options':      'img/setting.png',
        }
        self._main_toolbar_helps = {
            'new':          _("Create a new song"),
            'open':         _("Open an existing song"),
            'save':         _("Save the song with the current file name"),
            'printPreview': _(u"Preview the song before printing"),
            'print':        _(u"Print the song"),
            'undo':         _("Undo the last change"),
            'redo':         _("Redo the last undone change"),
            'cut':          _("Move selected text to the clipboard"),
            'copy':         _("Copy selected text to the clipboard"),
            'copyAsImage':  _("Copy the entire FORMATTED song (or selected verses) to the clipboard"),
            'paste':        _("Read text from the clipboard and insert it at the cursor position"),
            'pasteChords':  _("Merge chords from the copied text into the current selection"),
            'syntaxCheck':  _("Check ChordPro syntax of the document"),
            'options':      _(u"Set program options"),
        }

        # copyOnlyText è solo un ID menu, non un tool nella toolbar
        self.copyOnlyTextTool = wx.xrc.XRCID('copyOnlyText')

        self._ApplyMainToolBarVisibility()

        self.mainToolBarPane = self.AddPane(
            self.mainToolBar,
            aui.AuiPaneInfo().ToolbarPane().Top().Row(1).Position(1).PaneBorder(False).Gripper(False),
            _('Standard'), 'standard'
        )

    # ------------------------------------------------------------------
    # Format toolbar
    # ------------------------------------------------------------------

    def _BuildFormatToolBar(self):
        self.formatToolBar = aui.AuiToolBar(
            self.frame, wx.ID_ANY, wx.DefaultPosition,
            agwStyle=aui.AUI_TB_PLAIN_BACKGROUND | aui.AUI_TB_OVERFLOW
        )
        self.formatToolBar.SetToolBitmapSize(self._toolbarBitmapSize())
        self.formatToolBar.SetExtraStyle(aui.AUI_TB_PLAIN_BACKGROUND)

        # Font chooser
        fontIcon = wx.StaticBitmap(
            self.formatToolBar, -1,
            self._scaledToolbarBitmap('img/font1.png')
        )
        fontIcon.SetToolTip(_("Font used in the Songpress++ preview"))
        self.formatToolBar.AddControl(fontIcon)
        self.fontChooser = FontComboBox(self.formatToolBar, -1, self.pref.format.face)
        self.fontChooser.SetToolTip(_("Font used in the Songpress++ preview"))
        self.formatToolBar.AddControl(self.fontChooser)
        self.frame.Bind(wx.EVT_COMBOBOX,    self.OnFontSelected, self.fontChooser)
        self.fontChooser.Bind(wx.EVT_TEXT_ENTER, self.OnFontSelected, self.fontChooser)
        self.fontChooser.Bind(wx.EVT_KILL_FOCUS, self.OnFontSelected, self.fontChooser)
        # Teniamo i riferimenti per Show/Hide
        self._format_font_controls = [fontIcon, self.fontChooser]

        # Binding globali legati al format toolbar (non puramente al controllo)
        wx.UpdateUIEvent.SetUpdateInterval(500)
        self.frame.Bind(wx.EVT_UPDATE_UI,  self.OnIdle,        self.frame)
        self.frame.Bind(wx.EVT_TEXT_CUT,   self.OnTextCutCopy, self.text)
        self.frame.Bind(wx.EVT_TEXT_COPY,  self.OnTextCutCopy, self.text)

        # Show-chords slider
        showChordsIcon = wx.StaticBitmap(
            self.formatToolBar, -1,
            self._scaledToolbarBitmap('img/showChords.png')
        )
        self.formatToolBar.AddControl(showChordsIcon)
        self.showChordsChooser = ShowChordsChoice(
            self.formatToolBar, -1, 0
        )
        tt1 = wx.ToolTip(_("Hide or show chords in the formatted song"))
        tt2 = wx.ToolTip(_("Hide or show chords in the formatted song"))
        self.showChordsChooser.SetToolTip(tt1)
        showChordsIcon.SetToolTip(tt2)
        self.frame.Bind(wx.EVT_CHOICE, self.OnFontSelected, self.showChordsChooser)
        self.formatToolBar.AddControl(self.showChordsChooser, "pippo")
        # Teniamo i riferimenti per Show/Hide
        self._format_chords_controls = [showChordsIcon, self.showChordsChooser]

        self.formatToolBar.AddSeparator()
        self.AddTool(self.formatToolBar, 'insertLinespacing', 'img/line_spacing.png',
                     _(u"Linespacing"), _(u"Insert a {linespacing} command"))

        self.formatToolBar.Realize()
        # NB: NON forzare qui SetMinSize alla larghezza della main toolbar.
        # Farlo "gonfiava" la format toolbar fino alla larghezza della
        # Standard quando il suo contenuto è più stretto, lasciando spazio
        # bianco a destra; ed era incoerente con il percorso di rebuild
        # (_ApplyFormatToolBarVisibility -> _RealizeToolbar), che usa invece
        # la dimensione reale. Dopo Realize() il MinSize è già quello giusto.
        self.formatToolBarPane = self.AddPane(
            self.formatToolBar,
            aui.AuiPaneInfo().ToolbarPane().Top().Row(1).Position(2).PaneBorder(False).Gripper(False),
            _('Format'), 'format'
        )

    # ------------------------------------------------------------------
    # Insert toolbar — mappa icone/flag di visibilità
    # ------------------------------------------------------------------

    # Ogni voce: (xrc_name, label_i18n, pref_key)
    # pref_key è il nome dell'attributo booleano in self.pref (default True).
    INSERT_TOOLBAR_ITEMS = [
        ('title',                             _(u'Title'),                                              'tb_title'),
        ('subtitle',                          _(u'Subtitle'),                                           'tb_subtitle'),
        ('chord',                             _(u'Chord...'),                                           'tb_chord'),
        ('chorus',                            _(u'Chorus...'),                                          'tb_chorus'),
        ('verseWithCustomLabelOrWithoutLabel',_(u'Verse with custom label or without label...'),        'tb_verse'),
        ('comment',                           _(u'Comment...'),                                         'tb_comment'),
        ('insertPageBreak',                   _(u'Page break'),                         'tb_pageBreak'),
        ('insertColumnBreak',                 _(u'Column break'),                       'tb_columnBreak'),
        ('insertVerse',                       _(u'Unnumbered verse {start_verse}\\{end_verse}'),          'tb_insertVerse'),
        ('insertVerseNum',                    _(u'Numbered verse {start_verse_num}\\{end_verse_num}'),    'tb_insertVerseNum'),
        ('insertChorusBlock',                 _(u'Chorus {start_chorus}\\{end_chorus}...'),               'tb_insertChorusBlock'),
        ('insertChordBlock',                  _(u'Intro chords {start_chord}\\{end_chord}...'),           'tb_insertChordBlock'),
        ('insertBridge',                      _(u'Bridge {start_bridge}\\{end_bridge}...'),               'tb_insertBridge'),
        ('insertGrid',                        _(u'Grid {start_of_grid}\\{end_of_grid}...'),               'tb_insertGrid'),
        ('insertTempo',                       _(u'Tempo {tempo:}...'),                                    'tb_insertTempo'),
        ('insertTempoLabel',                  _(u'Tempo marking {tempo_label:}...'),                      'tb_insertTempoLabel'),
        ('insertTime',                        _(u'Time signature {time:}...'),                            'tb_insertTime'),
        ('insertKey',                         _(u'Key {key:}'),                                           'tb_insertKey'),
        ('insertDuration',                    _(u'Duration {beats_time:}...'),                            'tb_insertDuration'),
        ('insertTaste',                       _(u'Chord keyboard {taste:}...'),                           'tb_insertTaste'),
        ('insertFingering',                   _(u'First chord fingering {fingering:}...'),                'tb_insertFingering'),
        ('insertDefine',                      _(u'Guitar chord diagram {define:}...'),                    'tb_insertDefine'),
        ('insertImage',                       _(u'Image {image:}...'),                                    'tb_insertImage'),
        ('insertTransposerImage',             _(u'Transposer image {start_of_tab:TP}\\{end_of_tab}'),     'tb_insertTransposerImage'),
        ('insertMusicalSymbol',               _(u'Musical symbol (Unicode)'),                             'tb_insertMusicalSymbol'),
    ]

    # Separatori: dopo quale xrc_name inserire un separatore
    _INSERT_TOOLBAR_SEPARATORS_AFTER = {
        'comment', 'insertColumnBreak', 'insertGrid',
        'insertDuration', 'insertDefine',
    }

    def _ApplyInsertToolBarVisibility(self):
        """Ricostruisce la insert toolbar mostrando solo i tool con pref.tb_* == True.

        AuiToolBar non supporta Show/Hide per singola icona: l'unico modo
        affidabile è cancellare tutti i tool e reinserire quelli visibili.
        """
        self.insertToolBar.SetToolBitmapSize(self._toolbarBitmapSize())
        self.insertToolBar.ClearTools()

        prev_was_separator = True   # evita separatore iniziale
        last_added_xrc = None

        for xrc_name, label, pref_key in self.INSERT_TOOLBAR_ITEMS:
            visible = getattr(self.pref, pref_key, True)
            if not visible:
                continue

            # Separatore prima del gruppo (se necessario)
            # Il separatore viene aggiunto *prima* del primo elemento del nuovo
            # gruppo, non dopo l'ultimo del gruppo precedente, così non restano
            # separatori finali orphan quando tutti gli elementi di un gruppo
            # sono nascosti.
            needs_sep = (last_added_xrc in self._INSERT_TOOLBAR_SEPARATORS_AFTER)
            if needs_sep and not prev_was_separator:
                self.insertToolBar.AddSeparator()
                prev_was_separator = True

            self.AddTool(self.insertToolBar, xrc_name,
                         self._insert_toolbar_icons[xrc_name],
                         label,
                         self._insert_toolbar_helps[xrc_name])
            prev_was_separator = False
            last_added_xrc = xrc_name

        self._RealizeToolbar(self.insertToolBar)

    # ------------------------------------------------------------------
    # Insert toolbar
    # ------------------------------------------------------------------

    def _BuildInsertToolBar(self):
        self.insertToolBar = aui.AuiToolBar(
            self.frame, wx.ID_ANY, wx.DefaultPosition,
            agwStyle=aui.AUI_TB_PLAIN_BACKGROUND | aui.AUI_TB_OVERFLOW
        )
        self.insertToolBar.SetToolBitmapSize(self._toolbarBitmapSize())

        # Dizionari icon-path e help per ogni tool: usati da _ApplyInsertToolBarVisibility
        # per ricostruire la toolbar quando la visibilità cambia.
        self._insert_toolbar_icons = {
            'title':                             'img/title.png',
            'subtitle':                          'img/subtitle.png',
            'chord':                             'img/chord.png',
            'chorus':                            'img/chorus.png',
            'verseWithCustomLabelOrWithoutLabel':'img/verse.png',
            'comment':                           'img/comment.png',
            'insertPageBreak':                   'img/new_page.png',
            'insertColumnBreak':                 'img/column.png',
            'insertVerse':                       'img/verse_un_num.png',
            'insertVerseNum':                    'img/verse_num.png',
            'insertChorusBlock':                 'img/repeat.png',
            'insertChordBlock':                  'img/chord_intro.png',
            'insertBridge':                      'img/bridge.png',
            'insertGrid':                        'img/grid.png',
            'insertTempo':                       'img/metronome.png',
            'insertTempoLabel':                  'img/agogic.png',
            'insertTime':                        'img/time.png',
            'insertKey':                         'img/key.png',
            'insertDuration':                    'img/beats.png',
            'insertTaste':                       'img/taste.png',
            'insertFingering':                   'img/taste2.png',
            'insertDefine':                      'img/guitar.png',
            'insertImage':                       'img/picture.png',
            'insertTransposerImage':             'img/transposer.png',
            'insertMusicalSymbol':               'img/symbol.png',
        }
        self._insert_toolbar_helps = {
            'title':                             _(u"Insert a command to display the song title"),
            'subtitle':                          _(u"Insert a command to display the song subtitle"),
            'chord':                             _(u"Insert square brackets that will contain a chord"),
            'chorus':                            _(u"Insert a pair of commands that will contain the chorus"),
            'verseWithCustomLabelOrWithoutLabel':_(u"Insert a verse with a custom label or without label"),
            'comment':                           _(u"Insert a command to display a comment"),
            'insertPageBreak':                   _(u"Insert an explicit page break for printing"),
            'insertColumnBreak':                 _(u"Insert a column break"),
            'insertVerse':                       _(u"Insert an unnumbered verse {start_verse}\\{end_verse}"),
            'insertVerseNum':                    _(u"Insert a numbered verse {start_verse_num}\\{end_verse_num}"),
            'insertChorusBlock':                 _(u"Insert a chorus block {start_chorus}\\{end_chorus}"),
            'insertChordBlock':                  _(u"Insert an intro chord section {start_chord}\\{end_chord}"),
            'insertBridge':                      _(u"Insert a bridge block {start_bridge}\\{end_bridge}"),
            'insertGrid':                        _(u"Insert a chord grid block {start_of_grid}\\{end_of_grid}"),
            'insertTempo':                       _(u"Insert a {tempo:} command"),
            'insertTempoLabel':                  _(u"Insert a {tempo_label:} command"),
            'insertTime':                        _(u"Insert a {time:} command"),
            'insertKey':                         _(u"Insert a {key:} command"),
            'insertDuration':                    _(u"Insert a {beats_time:} command"),
            'insertTaste':                       _(u"Insert a chord keyboard {taste:}"),
            'insertFingering':                   _(u"Insert a {fingering:} command"),
            'insertDefine':                      _(u"Insert a {define:} command"),
            'insertImage':                       _(u"Insert an image (PNG, JPG, GIF) into the song"),
            'insertTransposerImage':             _(u"Insert the Transposer image and choose its position in the document"),
            'insertMusicalSymbol':               _(u"Insert a Unicode musical symbol"),
        }

        # Costruisce i tool rispettando la visibilità corrente
        self._ApplyInsertToolBarVisibility()

        self.insertToolBarPane = self.AddPane(
            self.insertToolBar,
            aui.AuiPaneInfo().ToolbarPane().Top().Row(1).Position(3).PaneBorder(False).Gripper(False),
            _('Insert'), 'insert'
        )

    # ------------------------------------------------------------------
    # View toolbar  (Visualizza)
    # ------------------------------------------------------------------

    VIEW_TOOLBAR_ITEMS = [
        ('preview',    _(u'Show Songpress++ Preview'),    'tbv_preview'),
        ('labelVerses',_(u'Show verse and chorus labels'),'tbv_labelVerses'),
    ]

    def _ApplyViewToolBarVisibility(self):
        """Ricostruisce la view toolbar rispettando i flag tbv_* in self.pref.

        I tool della view toolbar sono toggle, non normali: vanno reinseriti con
        AddToggleTool. Salviamo lo stato toggle corrente per ripristinarlo.
        """
        # Salva lo stato corrente dei toggle prima di cancellare
        _toggle_states = {}
        for xrc_name, _label, _pref_key in self.VIEW_TOOLBAR_ITEMS:
            tid = wx.xrc.XRCID(xrc_name)
            item = self.viewToolBar.FindTool(tid)
            if item is not None:
                _toggle_states[xrc_name] = self.viewToolBar.GetToolToggled(tid)

        self.viewToolBar.SetToolBitmapSize(self._toolbarBitmapSize())
        self.viewToolBar.ClearTools()

        for xrc_name, label, pref_key in self.VIEW_TOOLBAR_ITEMS:
            if not getattr(self.pref, pref_key, True):
                continue
            icon_path = self._view_toolbar_icons[xrc_name]
            tool = self.viewToolBar.AddToggleTool(
                wx.xrc.XRCID(xrc_name),
                self._scaledToolbarBitmap(icon_path),
                wx.NullBitmap,
                True,
                None,
                label,
                self._view_toolbar_helps[xrc_name],
            )
            # Ripristina bind e riferimento per il toggle preview
            if xrc_name == 'preview':
                self.togglePreviewViewToolId = tool.GetId()
                self.frame.Bind(wx.EVT_TOOL, self.OnTogglePaneView,
                                id=self.togglePreviewViewToolId)
            elif xrc_name == 'labelVerses':
                self.labelVersesViewToolId = tool.GetId()
            # Ripristina lo stato toggle se era già impostato
            if xrc_name in _toggle_states:
                self.viewToolBar.ToggleTool(wx.xrc.XRCID(xrc_name),
                                            _toggle_states[xrc_name])

        self._RealizeToolbar(self.viewToolBar)

    def _BuildViewToolBar(self):
        self.viewToolBar = aui.AuiToolBar(
            self.frame, wx.ID_ANY, wx.DefaultPosition,
            agwStyle=aui.AUI_TB_PLAIN_BACKGROUND | aui.AUI_TB_OVERFLOW
        )
        self.viewToolBar.SetToolBitmapSize(self._toolbarBitmapSize())

        self._view_toolbar_icons = {
            'preview':    'img/preview.png',
            'labelVerses':'img/labelVerses.png',
        }
        self._view_toolbar_helps = {
            'preview':    _(u"Show or hide the Songpress++ Preview panel"),
            'labelVerses':_(u"Show or hide verse and chorus labels"),
        }

        # Toggle "Mostra anteprima Songpress++"
        togglePreviewViewTool = self.viewToolBar.AddToggleTool(
            wx.xrc.XRCID('preview'),
            self._scaledToolbarBitmap("img/preview.png"),
            wx.NullBitmap,
            True,
            None,
            _("Show Songpress++ Preview"),
            _("Show or hide the Songpress++ Preview panel"),
        )
        self.togglePreviewViewToolId = togglePreviewViewTool.GetId()
        self.frame.Bind(wx.EVT_TOOL, self.OnTogglePaneView, id=self.togglePreviewViewToolId)

        # Toggle "Mostra le etichette delle strofe e ritornelli"
        labelVersesViewTool = self.viewToolBar.AddToggleTool(
            wx.xrc.XRCID('labelVerses'),
            self._scaledToolbarBitmap("img/labelVerses.png"),
            wx.NullBitmap,
            True,
            None,
            _("Show verse and chorus labels"),
            _("Show or hide verse and chorus labels"),
        )
        self.labelVersesViewToolId = labelVersesViewTool.GetId()

        self.viewToolBar.Realize()
        self.viewToolBarPane = self.AddPane(
            self.viewToolBar,
            aui.AuiPaneInfo().ToolbarPane().Top().Row(1).Position(4).PaneBorder(False).Gripper(False),
            _('View'), 'view'
        )
