# -*- coding: utf-8 -*-

import wx

from .FontComboBox import FontComboBox
from . import Editor

_ = wx.GetTranslation

import wx
import wx.xrc
import wx.adv

class PreferencesDialog(wx.Dialog):

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, id=wx.ID_ANY, title=_(u"Songpress++ options"), pos=wx.DefaultPosition,
                                             size=wx.Size(730, 780), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.SetSizeHints(wx.Size(730, 780), wx.DefaultSize)

        bSizer10 = wx.BoxSizer(wx.VERTICAL)

        self.notebook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        self.general = wx.Panel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer11 = wx.BoxSizer(wx.VERTICAL)

        # ── Gruppo: Editor ───────────────────────────────────────────
        grpEditor = wx.StaticBoxSizer(wx.StaticBox(self.general, wx.ID_ANY, _(u"Editor font")), wx.VERTICAL)

        bSizer12 = wx.BoxSizer(wx.HORIZONTAL)
        self.label1 = wx.StaticText(self.general, wx.ID_ANY, _(u"Editor font"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.label1.Wrap(-1)
        bSizer12.Add(self.label1, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.fontCB = FontComboBox(self.general, wx.ID_ANY, self.pref.editorFace)
        bSizer12.Add(self.fontCB, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.m_staticText8 = wx.StaticText(self.general, wx.ID_ANY, _(u"Size"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText8.Wrap(-1)
        bSizer12.Add(self.m_staticText8, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        sizeCBChoices = [_(u"7"), _(u"8"), _(u"9"), _(u"10"), _(u"11"), _(u"12"), _(u"13"), _(u"14"), _(u"16"), _(u"18"), _(u"20")]
        self.sizeCB = wx.ComboBox(self.general, wx.ID_ANY, _(u"12"), wx.DefaultPosition, wx.DefaultSize, sizeCBChoices, 0)
        self.sizeCB.SetMinSize(wx.Size(100, -1))
        bSizer12.Add(self.sizeCB, 0, wx.ALIGN_CENTER_VERTICAL)
        grpEditor.Add(bSizer12, 0, wx.EXPAND | wx.ALL, 5)

        # Editor background colour row
        bSizerEditorBg = wx.BoxSizer(wx.HORIZONTAL)
        self.labelEditorBg = wx.StaticText(self.general, wx.ID_ANY, _(u"Editor background colour"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelEditorBg.Wrap(-1)
        bSizerEditorBg.Add(self.labelEditorBg, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.editorBgHexCtrl = wx.TextCtrl(self.general, wx.ID_ANY, u"#FFFFFF", wx.DefaultPosition, wx.Size(80, -1), 0)
        bSizerEditorBg.Add(self.editorBgHexCtrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.editorBgBtn = wx.Button(self.general, wx.ID_ANY, _(u"Pick…"), wx.DefaultPosition, wx.Size(60, -1), 0)
        bSizerEditorBg.Add(self.editorBgBtn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.editorBgSwatch = wx.Panel(self.general, wx.ID_ANY, wx.DefaultPosition, wx.Size(24, 24), wx.BORDER_SIMPLE)
        bSizerEditorBg.Add(self.editorBgSwatch, 0, wx.ALIGN_CENTER_VERTICAL)
        grpEditor.Add(bSizerEditorBg, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        # Selection colour row
        bSizerSelColour = wx.BoxSizer(wx.HORIZONTAL)
        self.labelSelColour = wx.StaticText(self.general, wx.ID_ANY, _(u"Selection colour"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelSelColour.Wrap(-1)
        bSizerSelColour.Add(self.labelSelColour, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.selColourHexCtrl = wx.TextCtrl(self.general, wx.ID_ANY, u"#C0C0C0", wx.DefaultPosition, wx.Size(80, -1), 0)
        bSizerSelColour.Add(self.selColourHexCtrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.selColourBtn = wx.Button(self.general, wx.ID_ANY, _(u"Pick…"), wx.DefaultPosition, wx.Size(60, -1), 0)
        bSizerSelColour.Add(self.selColourBtn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.selColourSwatch = wx.Panel(self.general, wx.ID_ANY, wx.DefaultPosition, wx.Size(24, 24), wx.BORDER_SIMPLE)
        bSizerSelColour.Add(self.selColourSwatch, 0, wx.ALIGN_CENTER_VERTICAL)
        grpEditor.Add(bSizerSelColour, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        # Caption Editor colour row
        bSizerCapEditor = wx.BoxSizer(wx.HORIZONTAL)
        self.labelCapEditor = wx.StaticText(self.general, wx.ID_ANY, _(u"Editor caption colour"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelCapEditor.Wrap(-1)
        bSizerCapEditor.Add(self.labelCapEditor, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.capEditorHexCtrl = wx.TextCtrl(self.general, wx.ID_ANY, u"#4682C8", wx.DefaultPosition, wx.Size(80, -1), 0)
        bSizerCapEditor.Add(self.capEditorHexCtrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.capEditorBtn = wx.Button(self.general, wx.ID_ANY, _(u"Pick…"), wx.DefaultPosition, wx.Size(60, -1), 0)
        bSizerCapEditor.Add(self.capEditorBtn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.capEditorSwatch = wx.Panel(self.general, wx.ID_ANY, wx.DefaultPosition, wx.Size(24, 24), wx.BORDER_SIMPLE)
        bSizerCapEditor.Add(self.capEditorSwatch, 0, wx.ALIGN_CENTER_VERTICAL)
        grpEditor.Add(bSizerCapEditor, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        # Caption Preview colour row
        bSizerCapPreview = wx.BoxSizer(wx.HORIZONTAL)
        self.labelCapPreview = wx.StaticText(self.general, wx.ID_ANY, _(u"Preview caption colour"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelCapPreview.Wrap(-1)
        bSizerCapPreview.Add(self.labelCapPreview, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.capPreviewHexCtrl = wx.TextCtrl(self.general, wx.ID_ANY, u"#329B82", wx.DefaultPosition, wx.Size(80, -1), 0)
        bSizerCapPreview.Add(self.capPreviewHexCtrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.capPreviewBtn = wx.Button(self.general, wx.ID_ANY, _(u"Pick…"), wx.DefaultPosition, wx.Size(60, -1), 0)
        bSizerCapPreview.Add(self.capPreviewBtn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.capPreviewSwatch = wx.Panel(self.general, wx.ID_ANY, wx.DefaultPosition, wx.Size(24, 24), wx.BORDER_SIMPLE)
        bSizerCapPreview.Add(self.capPreviewSwatch, 0, wx.ALIGN_CENTER_VERTICAL)
        grpEditor.Add(bSizerCapPreview, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        # ── Colori sintassi editor ──────────────────────────────────
        grpSyntax = wx.StaticBoxSizer(wx.StaticBox(self.general, wx.ID_ANY, _(u"Syntax colours")), wx.VERTICAL)

        # Barra temi
        bSizerTheme = wx.BoxSizer(wx.HORIZONTAL)
        self.labelTheme = wx.StaticText(self.general, wx.ID_ANY, _(u"Theme:"))
        bSizerTheme.Add(self.labelTheme, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.themeCh = wx.Choice(self.general, wx.ID_ANY, wx.DefaultPosition, wx.Size(150, -1), [])
        bSizerTheme.Add(self.themeCh, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.themeLoadBtn  = wx.Button(self.general, wx.ID_ANY, _(u"Load"),   wx.DefaultPosition, wx.Size(60, -1))
        self.themeSaveBtn  = wx.Button(self.general, wx.ID_ANY, _(u"Save"),   wx.DefaultPosition, wx.Size(60, -1))
        self.themeDeleteBtn = wx.Button(self.general, wx.ID_ANY, _(u"Delete"), wx.DefaultPosition, wx.Size(60, -1))
        bSizerTheme.Add(self.themeLoadBtn,   0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 3)
        bSizerTheme.Add(self.themeSaveBtn,   0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 3)
        bSizerTheme.Add(self.themeDeleteBtn, 0, wx.ALIGN_CENTER_VERTICAL)
        grpSyntax.Add(bSizerTheme, 0, wx.EXPAND | wx.ALL, 5)

        # Bind eventi temi
        self.themeLoadBtn.Bind(wx.EVT_BUTTON,  self.OnThemeLoad)
        self.themeSaveBtn.Bind(wx.EVT_BUTTON,  self.OnThemeSave)
        self.themeDeleteBtn.Bind(wx.EVT_BUTTON, self.OnThemeDelete)

        _syntax_rows = [
            ('normal',  _(u"Normal text"),  '#000000'),
            ('chorus',  _(u"Chorus"),       '#000000'),
            ('chord',   _(u"Chords"),       '#FF0000'),
            ('command', _(u"Commands"),     '#0000FF'),
            ('attr',    _(u"Attributes"),   '#008000'),
            ('comment', _(u"Comments"),     '#808080'),
            ('tabgrid', _(u"Tab / Grid"),   '#8B5A00'),
        ]
        _syntaxGrid = wx.FlexGridSizer(len(_syntax_rows), 4, 3, 5)
        _syntaxGrid.AddGrowableCol(0, 1)
        self.syntaxHexCtrls   = {}
        self.syntaxSwatches   = {}
        self.syntaxPickBtns   = {}
        for key, label, default in _syntax_rows:
            lbl = wx.StaticText(self.general, wx.ID_ANY, label)
            _syntaxGrid.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL)
            hx = wx.TextCtrl(self.general, wx.ID_ANY, default, wx.DefaultPosition, wx.Size(80, -1))
            _syntaxGrid.Add(hx, 0, wx.ALIGN_CENTER_VERTICAL)
            btn = wx.Button(self.general, wx.ID_ANY, _(u"Pick…"), wx.DefaultPosition, wx.Size(60, -1))
            _syntaxGrid.Add(btn, 0, wx.ALIGN_CENTER_VERTICAL)
            sw = wx.Panel(self.general, wx.ID_ANY, wx.DefaultPosition, wx.Size(24, 24), wx.BORDER_SIMPLE)
            _syntaxGrid.Add(sw, 0, wx.ALIGN_CENTER_VERTICAL)
            self.syntaxHexCtrls[key] = hx
            self.syntaxSwatches[key] = sw
            self.syntaxPickBtns[key] = btn
        grpSyntax.Add(_syntaxGrid, 0, wx.EXPAND | wx.ALL, 5)
        grpEditor.Add(grpSyntax, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        # Bind eventi sintassi
        for key in self.syntaxHexCtrls:
            self.syntaxHexCtrls[key].Bind(wx.EVT_TEXT, self.OnSyntaxHexChanged)
            self.syntaxPickBtns[key].Bind(wx.EVT_BUTTON, self.OnSyntaxPickColour)

        # Preview
        bSizer13 = wx.BoxSizer(wx.HORIZONTAL)
        self.m_staticText9 = wx.StaticText(self.general, wx.ID_ANY, _(u"Preview"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText9.Wrap(-1)
        bSizer13.Add(self.m_staticText9, 0, wx.ALIGN_TOP | wx.RIGHT, 5)
        self.editor = Editor.Editor(self.general, False, self.general)
        bSizer13.Add(self.editor, 1, wx.EXPAND)
        grpEditor.Add(bSizer13, 1, wx.EXPAND | wx.ALL, 5)

        bSizer11.Add(grpEditor, 1, wx.EXPAND | wx.ALL, 8)

        self.general.SetSizer(bSizer11)
        self.general.Layout()
        bSizer11.Fit(self.general)
        self.notebook.AddPage(self.general, _(u"General"), True)

        # ── Tab "Generale 2" ─────────────────────────────────────────
        self.general2 = wx.Panel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer11b = wx.BoxSizer(wx.VERTICAL)

        # ── Gruppo: Canzone ──────────────────────────────────────────
        grpSong = wx.StaticBoxSizer(wx.StaticBox(self.general2, wx.ID_ANY, _(u"Song")), wx.VERTICAL)

        bSizer141 = wx.BoxSizer(wx.HORIZONTAL)
        self.m_staticText101 = wx.StaticText(self.general2, wx.ID_ANY, _(u"Default notation"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText101.Wrap(-1)
        bSizer141.Add(self.m_staticText101, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        notationChChoices = []
        self.notationCh = wx.Choice(self.general2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, notationChChoices, 0)
        self.notationCh.SetSelection(0)
        bSizer141.Add(self.notationCh, 1, wx.ALIGN_CENTER_VERTICAL)
        grpSong.Add(bSizer141, 0, wx.EXPAND | wx.ALL, 5)

        bSizer1412 = wx.BoxSizer(wx.HORIZONTAL)
        self.m_staticText1012 = wx.StaticText(self.general2, wx.ID_ANY, _(u"Default file extension"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText1012.Wrap(-1)
        bSizer1412.Add(self.m_staticText1012, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        extensionChoices = []
        self.extension = wx.Choice(self.general2, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, extensionChoices, 0)
        self.extension.SetSelection(0)
        bSizer1412.Add(self.extension, 1, wx.ALIGN_CENTER_VERTICAL)
        grpSong.Add(bSizer1412, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        bSizer14 = wx.BoxSizer(wx.HORIZONTAL)
        self.m_staticText10 = wx.StaticText(self.general2, wx.ID_ANY, _(u"Language"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText10.Wrap(-1)
        bSizer14.Add(self.m_staticText10, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.langCh = wx.adv.BitmapComboBox(self.general2, wx.ID_ANY, style=wx.CB_READONLY)
        self.langCh.SetSelection(0)
        bSizer14.Add(self.langCh, 1, wx.ALIGN_CENTER_VERTICAL)
        grpSong.Add(bSizer14, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        bSizer11b.Add(grpSong, 0, wx.EXPAND | wx.ALL, 8)

        # ── Gruppo: Generale ─────────────────────────────────────────
        grpGeneral = wx.StaticBoxSizer(wx.StaticBox(self.general2, wx.ID_ANY, _(u"General")), wx.VERTICAL)

        bSizerClearRecent = wx.BoxSizer(wx.HORIZONTAL)
        self.clearRecentFilesBtn = wx.Button(self.general2, wx.ID_ANY, _(u"Clear recent files"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizerClearRecent.Add(self.clearRecentFilesBtn, 0)
        self.openTemplatesFolderBtn = wx.Button(self.general2, wx.ID_ANY, _(u"Open templates folder"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizerClearRecent.Add(self.openTemplatesFolderBtn, 0, wx.LEFT, 8)
        grpGeneral.Add(bSizerClearRecent, 0, wx.ALL, 5)

        self.showPrintPreviewCB = wx.CheckBox(self.general2, wx.ID_ANY, _(u"Show print preview before printing"), wx.DefaultPosition, wx.DefaultSize, 0)
        grpGeneral.Add(self.showPrintPreviewCB, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        self.multiCursorCB = wx.CheckBox(self.general2, wx.ID_ANY, _(u"Enable multi-cursor (Alt+Click, Ctrl+D)"), wx.DefaultPosition, wx.DefaultSize, 0)
        grpGeneral.Add(self.multiCursorCB, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        self.saveWindowGeometryCB = wx.CheckBox(self.general2, wx.ID_ANY, _(u"Save window size and position on exit"), wx.DefaultPosition, wx.DefaultSize, 0)
        grpGeneral.Add(self.saveWindowGeometryCB, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        self.showDebugMsgCB = wx.CheckBox(self.general2, wx.ID_ANY, _(u"Show debug messages (theme save path)"), wx.DefaultPosition, wx.DefaultSize, 0)
        grpGeneral.Add(self.showDebugMsgCB, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        bSizer11b.Add(grpGeneral, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.general2.SetSizer(bSizer11b)
        self.general2.Layout()
        bSizer11b.Fit(self.general2)
        self.notebook.AddPage(self.general2, _(u"General 2"), False)

        self.autoAdjust = wx.Panel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer18 = wx.BoxSizer(wx.VERTICAL)
        self.autoRemoveBlankLines = wx.CheckBox(self.autoAdjust, wx.ID_ANY, _(u"Offer to remove blank lines"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer18.Add(self.autoRemoveBlankLines, 0, wx.ALL, 5)
        self.autoTab2Chordpro = wx.CheckBox(self.autoAdjust, wx.ID_ANY, _(u"Offer to convert songs in tab"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer18.Add(self.autoTab2Chordpro, 0, wx.ALL, 5)
        self.autoAdjustEasyKey = wx.CheckBox(self.autoAdjust, wx.ID_ANY, _(u"Offer to transpose songs to simplify chords"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer18.Add(self.autoAdjustEasyKey, 0, wx.ALL, 5)
        self.simplifyPanel = wx.ScrolledWindow(self.autoAdjust, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL | wx.SUNKEN_BORDER | wx.VSCROLL)
        self.simplifyPanel.SetScrollRate(5, 5)
        self.simplifyPanel.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_WINDOW))
        bSizer18.Add(self.simplifyPanel, 1, wx.EXPAND | wx.ALL, 5)
        self.autoAdjust.SetSizer(bSizer18)
        self.autoAdjust.Layout()
        bSizer18.Fit(self.autoAdjust)
        self.notebook.AddPage(self.autoAdjust, _(u"AutoAdjust"), False)

        # --- Tab "Format" ---
        # Ogni SpinCtrl è in un Panel dedicato per evitare il bug di sincronizzazione wx su Windows
        self.formatPanel = wx.Panel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizerFormat = wx.BoxSizer(wx.VERTICAL)

        # ── Gruppo: Titolo e struttura ───────────────────────────────
        grpTitleStruct = wx.StaticBoxSizer(
            wx.StaticBox(self.formatPanel, wx.ID_ANY, _(u"Title and structure")),
            wx.VERTICAL
        )

        bSizerTitleLine = wx.BoxSizer(wx.HORIZONTAL)
        self.labelTitleLine = wx.StaticText(self.formatPanel, wx.ID_ANY, _(u"Title underline thickness"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelTitleLine.Wrap(-1)
        bSizerTitleLine.Add(self.labelTitleLine, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self._titleSpinPanel = wx.Panel(self.formatPanel, wx.ID_ANY)
        self.titleLineWidthSpin = wx.SpinCtrl(self._titleSpinPanel, wx.ID_ANY, "4", wx.DefaultPosition, wx.Size(60, -1), wx.SP_ARROW_KEYS, 1, 5, 4)
        titleSpinSizer = wx.BoxSizer(wx.HORIZONTAL)
        titleSpinSizer.Add(self.titleLineWidthSpin, 0, 0, 0)
        self._titleSpinPanel.SetSizer(titleSpinSizer)
        bSizerTitleLine.Add(self._titleSpinPanel, 0, wx.ALIGN_CENTER_VERTICAL)
        grpTitleStruct.Add(bSizerTitleLine, 0, wx.EXPAND | wx.ALL, 5)

        bSizerVerseBox = wx.BoxSizer(wx.HORIZONTAL)
        self.labelVerseBox = wx.StaticText(self.formatPanel, wx.ID_ANY, _(u"Verse number box thickness"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelVerseBox.Wrap(-1)
        bSizerVerseBox.Add(self.labelVerseBox, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self._verseSpinPanel = wx.Panel(self.formatPanel, wx.ID_ANY)
        self.verseBoxWidthSpin = wx.SpinCtrl(self._verseSpinPanel, wx.ID_ANY, "1", wx.DefaultPosition, wx.Size(60, -1), wx.SP_ARROW_KEYS, 1, 5, 1)
        verseSpinSizer = wx.BoxSizer(wx.HORIZONTAL)
        verseSpinSizer.Add(self.verseBoxWidthSpin, 0, 0, 0)
        self._verseSpinPanel.SetSizer(verseSpinSizer)
        bSizerVerseBox.Add(self._verseSpinPanel, 0, wx.ALIGN_CENTER_VERTICAL)
        grpTitleStruct.Add(bSizerVerseBox, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        bSizerFormat.Add(grpTitleStruct, 0, wx.EXPAND | wx.ALL, 8)

        # ── Gruppo: Accordi e tempo ──────────────────────────────────
        grpChordsTime = wx.StaticBoxSizer(
            wx.StaticBox(self.formatPanel, wx.ID_ANY, _(u"Chords and tempo")),
            wx.VERTICAL
        )

        bSizerKlavier = wx.BoxSizer(wx.HORIZONTAL)
        self.labelKlavierColour = wx.StaticText(self.formatPanel, wx.ID_ANY, _(u"Klavier key colour"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelKlavierColour.Wrap(-1)
        bSizerKlavier.Add(self.labelKlavierColour, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.klavierHexCtrl = wx.TextCtrl(self.formatPanel, wx.ID_ANY, u"#D23C3C", wx.DefaultPosition, wx.Size(80, -1), 0)
        bSizerKlavier.Add(self.klavierHexCtrl, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.klavierColourBtn = wx.Button(self.formatPanel, wx.ID_ANY, _(u"Pick…"), wx.DefaultPosition, wx.Size(60, -1), 0)
        bSizerKlavier.Add(self.klavierColourBtn, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.klavierColourSwatch = wx.Panel(self.formatPanel, wx.ID_ANY, wx.DefaultPosition, wx.Size(24, 24), wx.BORDER_SIMPLE)
        bSizerKlavier.Add(self.klavierColourSwatch, 0, wx.ALIGN_CENTER_VERTICAL)
        grpChordsTime.Add(bSizerKlavier, 0, wx.EXPAND | wx.ALL, 5)

        # Dimensione icone tempo ({tempo_*})
        bSizerTempoIcon = wx.BoxSizer(wx.HORIZONTAL)
        self.labelTempoIconSize = wx.StaticText(self.formatPanel, wx.ID_ANY, _(u"Tempo icon size"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelTempoIconSize.Wrap(-1)
        bSizerTempoIcon.Add(self.labelTempoIconSize, 1, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        self.tempoIconSize16 = wx.RadioButton(self.formatPanel, wx.ID_ANY, u"16×16", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP)
        self.tempoIconSize24 = wx.RadioButton(self.formatPanel, wx.ID_ANY, u"24×24")
        self.tempoIconSize32 = wx.RadioButton(self.formatPanel, wx.ID_ANY, u"32×32")
        bSizerTempoIcon.Add(self.tempoIconSize16, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        bSizerTempoIcon.Add(self.tempoIconSize24, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        bSizerTempoIcon.Add(self.tempoIconSize32, 0, wx.ALIGN_CENTER_VERTICAL)
        grpChordsTime.Add(bSizerTempoIcon, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        bSizerFormat.Add(grpChordsTime, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # ── Gruppo: Griglia accordi ──────────────────────────────────
        grpGrid = wx.StaticBoxSizer(
            wx.StaticBox(self.formatPanel, wx.ID_ANY, _(u"Chord grid ({start_of_grid}.{end_of_grid})")),
            wx.VERTICAL
        )

        lbl = wx.StaticText(self.formatPanel, wx.ID_ANY,
            _(u"Display mode for {start_of_grid} blocks:"))
        grpGrid.Add(lbl, 0, wx.LEFT | wx.TOP | wx.RIGHT, 5)

        self.gridModePipe = wx.RadioButton(
            self.formatPanel, wx.ID_ANY,
            _(u"Pipe table  —  | C   | G   | Am  | F   |"),
            style=wx.RB_GROUP
        )
        self.gridModePipe.SetToolTip(
            _(u"Each bar is separated by | characters. The raw text in the source "
              u"must already contain | delimiters.")
        )
        grpGrid.Add(self.gridModePipe, 0, wx.ALL, 4)

        self.gridModePlain = wx.RadioButton(
            self.formatPanel, wx.ID_ANY,
            _(u"Plain spacing  —  C   G   Am  F")
        )
        self.gridModePlain.SetToolTip(
            _(u"Chords are rendered spaced out without pipe separators.")
        )
        grpGrid.Add(self.gridModePlain, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 4)

        self.gridModeTable = wx.RadioButton(
            self.formatPanel, wx.ID_ANY,
            _(u"Table  —  cells with borders")
        )
        self.gridModeTable.SetToolTip(
            _(u"Each bar is rendered as a cell with a visible border, "
              u"like a grid table.")
        )
        grpGrid.Add(self.gridModeTable, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 4)

        # ── Etichetta predefinita ────────────────────────────────────
        szLbl = wx.BoxSizer(wx.HORIZONTAL)
        lblDefault = wx.StaticText(
            self.formatPanel, wx.ID_ANY,
            _(u"Default label (used when {start_of_grid} has no label):")
        )
        szLbl.Add(lblDefault, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.gridDefaultLabelCtrl = wx.TextCtrl(
            self.formatPanel, wx.ID_ANY,
            value=_(u"Grid"),
            size=(160, -1)
        )
        self.gridDefaultLabelCtrl.SetToolTip(
            _(u"This text is shown as the section label when {start_of_grid} "
              u"is used without an explicit label argument.\n"
              u"Example: {start_of_grid: label} overrides this value.")
        )
        szLbl.Add(self.gridDefaultLabelCtrl, 0, wx.ALIGN_CENTER_VERTICAL)
        grpGrid.Add(szLbl, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM | wx.TOP, 5)

        self.gridSpaceAsPipeCB = wx.CheckBox(
            self.formatPanel, wx.ID_ANY,
            _(u"Space bar inserts | separator (pipe mode)")
        )
        self.gridSpaceAsPipeCB.SetToolTip(
            _(u"When enabled, pressing the space bar inside a {start_of_grid} block\n"
              u"inserts a | pipe separator, shifting the current cell to the right.\n"
              u"Disable this to type spaces normally inside grid blocks.")
        )
        grpGrid.Add(self.gridSpaceAsPipeCB, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        # ── Direzione di size=N ──────────────────────────────────────
        szSizeDir = wx.BoxSizer(wx.HORIZONTAL)
        lblSizeDir = wx.StaticText(self.formatPanel, wx.ID_ANY,
            _(u"size=N affects:"))
        szSizeDir.Add(lblSizeDir, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        self.gridSizeDirBoth = wx.RadioButton(
            self.formatPanel, wx.ID_ANY,
            _(u"Width and height"),
            style=wx.RB_GROUP
        )
        self.gridSizeDirBoth.SetToolTip(
            _(u"size=N multiplies both horizontal and vertical cell padding.")
        )
        self.gridSizeDirH = wx.RadioButton(
            self.formatPanel, wx.ID_ANY,
            _(u"Width only")
        )
        self.gridSizeDirH.SetToolTip(
            _(u"size=N multiplies only horizontal cell padding; "
              u"vertical padding stays at its base value.")
        )
        self.gridSizeDirV = wx.RadioButton(
            self.formatPanel, wx.ID_ANY,
            _(u"Height only")
        )
        self.gridSizeDirV.SetToolTip(
            _(u"size=N multiplies only vertical cell padding; "
              u"horizontal padding stays at its base value.")
        )
        szSizeDir.Add(self.gridSizeDirBoth, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        szSizeDir.Add(self.gridSizeDirH,    0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8)
        szSizeDir.Add(self.gridSizeDirV,    0, wx.ALIGN_CENTER_VERTICAL)
        grpGrid.Add(szSizeDir, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)

        bSizerFormat.Add(grpGrid, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        # --- Gruppo: inserimento simbolo musicale ---
        grpSymbol = wx.StaticBoxSizer(
            wx.StaticBox(self.formatPanel, wx.ID_ANY, _(u"Musical symbol insertion")),
            wx.VERTICAL,
        )
        szSymbol = wx.BoxSizer(wx.HORIZONTAL)
        self.symbolScaleCB = wx.CheckBox(
            self.formatPanel, wx.ID_ANY,
            _(u"Custom size when inserting musical symbols (pt):"),
        )
        self.symbolScaleCB.SetToolTip(
            _(u"When enabled, inserted musical symbols are wrapped with\n"
              u"{textsize:N}...{textsize:} to apply the chosen point size.")
        )
        self.symbolSizeSpin = wx.SpinCtrl(
            self.formatPanel, wx.ID_ANY,
            min=6, max=144, initial=24,
            style=wx.SP_ARROW_KEYS,
        )
        self.symbolSizeSpin.SetMinSize(wx.Size(60, -1))
        szSymbol.Add(self.symbolScaleCB, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 6)
        szSymbol.Add(self.symbolSizeSpin, 0, wx.ALIGN_CENTER_VERTICAL)
        grpSymbol.Add(szSymbol, 0, wx.LEFT | wx.RIGHT | wx.TOP | wx.BOTTOM, 5)
        self.symbolScaleCB.Bind(
            wx.EVT_CHECKBOX,
            lambda e: self.symbolSizeSpin.Enable(self.symbolScaleCB.GetValue()),
        )
        self.symbolInsertVerseCB = wx.CheckBox(
            self.formatPanel, wx.ID_ANY,
            _(u"Wrap symbol in a verse block (not counted)"),
        )
        self.symbolInsertVerseCB.SetToolTip(
            _(u"When enabled, the inserted symbol is wrapped inside\n"
              u"{start_verse}...{end_verse} so it is not counted\n"
              u"in the verse numbering.")
        )
        grpSymbol.Add(self.symbolInsertVerseCB, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 5)
        bSizerFormat.Add(grpSymbol, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.formatPanel.SetSizer(bSizerFormat)
        self.formatPanel.Layout()
        bSizerFormat.Fit(self.formatPanel)
        self.notebook.AddPage(self.formatPanel, _(u"Format"), False)
        # --- Fine Tab "Format" ---

        # --- Tab "Songpress" ---
        self.songpressPanel = wx.Panel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizerSongpress = wx.BoxSizer(wx.VERTICAL)

        # Gruppo: Anteprima
        grpPreview = wx.StaticBoxSizer(
            wx.StaticBox(self.songpressPanel, wx.ID_ANY, _(u"Songpress++ Preview")),
            wx.VERTICAL
        )

        self.showPageIndicatorCB = wx.CheckBox(
            self.songpressPanel, wx.ID_ANY,
            _(u"Show page indicator (e.g. 'Page 1 of 3')")
        )
        self.showPageIndicatorCB.SetToolTip(
            _(u"Show or hide the page counter label at the top right of the preview panel")
        )
        grpPreview.Add(self.showPageIndicatorCB, 0, wx.ALL, 5)

        self.greyBackgroundCB = wx.CheckBox(
            self.songpressPanel, wx.ID_ANY,
            _(u"Grey background in preview (page style)")
        )
        self.greyBackgroundCB.SetToolTip(
            _(u"Show the preview on a grey background to simulate a printed page. "
              u"When disabled, the background is white.")
        )
        grpPreview.Add(self.greyBackgroundCB, 0, wx.ALL, 5)

        self.debounceRefreshCB = wx.CheckBox(
            self.songpressPanel, wx.ID_ANY,
            _(u"Delay preview refresh while typing (debounce)")
        )
        self.debounceRefreshCB.SetToolTip(
            _(u"When enabled, the preview redraws only after a short pause in typing "
              u"(300 ms), reducing CPU usage. When disabled, every keystroke "
              u"immediately updates the preview.")
        )
        grpPreview.Add(self.debounceRefreshCB, 0, wx.ALL, 5)

        self.dblClickFocusCB = wx.CheckBox(
            self.songpressPanel, wx.ID_ANY,
            _(u"Double-click on preview jumps to source line in editor")
        )
        self.dblClickFocusCB.SetToolTip(
            _(u"When enabled, double-clicking on any word or chord in the preview "
              u"moves the cursor to the corresponding line in the editor.")
        )
        grpPreview.Add(self.dblClickFocusCB, 0, wx.ALL, 5)

        self.previewMinSizeCB = wx.CheckBox(
            self.songpressPanel, wx.ID_ANY,
            _(u"Set minimum size for the preview panel at startup (370×520)")
        )
        self.previewMinSizeCB.SetToolTip(
            _(u"When enabled, the preview panel cannot be resized below 370×520 pixels. "
              u"This prevents the panel from appearing too small when the application starts.")
        )
        grpPreview.Add(self.previewMinSizeCB, 0, wx.ALL, 5)

        bSizerSongpress.Add(grpPreview, 0, wx.EXPAND | wx.ALL, 8)


        self.songpressPanel.SetSizer(bSizerSongpress)
        self.songpressPanel.Layout()
        bSizerSongpress.Fit(self.songpressPanel)
        self.notebook.AddPage(self.songpressPanel, _(u"Songpress++ Preview"), False)
        # --- Fine Tab "Songpress" ---

        # --- Tab "Guida rapida" ---
        self.guidePanel = wx.Panel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizerGuide = wx.BoxSizer(wx.VERTICAL)

        # Gruppo: Visualizzatore Markdown
        grpMdViewer = wx.StaticBoxSizer(
            wx.StaticBox(self.guidePanel, wx.ID_ANY, _(u"Markdown viewer")),
            wx.VERTICAL
        )

        rowViewer = wx.BoxSizer(wx.HORIZONTAL)
        rowViewer.Add(
            wx.StaticText(self.guidePanel, wx.ID_ANY, _(u"Markdown viewer:")),
            0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8
        )
        self.guideViewerCh = wx.Choice(self.guidePanel, wx.ID_ANY)
        self.guideViewerCh.Append(_(u"Automatic (python-markdown → mistune → built-in)"), "markdown")
        self.guideViewerCh.Append(_(u"python-markdown"),  "markdown")
        self.guideViewerCh.Append(_(u"mistune"),           "mistune")
        self.guideViewerCh.Append(_(u"Built-in parser"),   "builtin")
        self.guideViewerCh.SetToolTip(
            _(u"Choose which Markdown engine is used to render the quick guide.\n"
              u"'Automatic' tries python-markdown first, then mistune, then the built-in parser.\n"
              u"python-markdown and mistune must be installed separately.")
        )
        rowViewer.Add(self.guideViewerCh, 1, wx.EXPAND)
        grpMdViewer.Add(rowViewer, 0, wx.EXPAND | wx.ALL, 5)
        bSizerGuide.Add(grpMdViewer, 0, wx.EXPAND | wx.ALL, 8)

        # Gruppo: Percorsi immagini
        grpImgPath = wx.StaticBoxSizer(
            wx.StaticBox(self.guidePanel, wx.ID_ANY, _(u"Image paths")),
            wx.VERTICAL
        )
        self.guideMarkdownImgPathCb = wx.CheckBox(
            self.guidePanel, wx.ID_ANY,
            _(u"Use absolute image paths for Markdown editor (../src/songpress/img/GUIDE/...)")
        )
        self.guideMarkdownImgPathCb.SetToolTip(
            _(u"When enabled, image paths in the guide are rewritten to the full\n"
              u"../src/songpress/img/GUIDE/ form, for use with Markdown editors.\n"
              u"Leave enabled for Songpress++ built-in viewer.")
        )
        grpImgPath.Add(self.guideMarkdownImgPathCb, 0, wx.ALL, 5)
        bSizerGuide.Add(grpImgPath, 0, wx.EXPAND | wx.ALL, 8)

        self.guidePanel.SetSizer(bSizerGuide)
        self.guidePanel.Layout()
        bSizerGuide.Fit(self.guidePanel)
        self.notebook.AddPage(self.guidePanel, _(u"Quick guide"), False)
        # --- Fine Tab "Guida rapida" ---

        # --- Tab "Context menu" ---
        self.contextMenuPanel = wx.Panel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizerCM = wx.BoxSizer(wx.VERTICAL)

        headerCM = wx.StaticText(self.contextMenuPanel, wx.ID_ANY,
            _(u"Select which items to show in the right-click context menu:"),
            wx.DefaultPosition, wx.DefaultSize, 0)
        headerCM.Wrap(480)
        bSizerCM.Add(headerCM, 0, wx.ALL, 8)

        bSizerCM.Add(wx.StaticLine(self.contextMenuPanel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        # --- Gruppo Undo/Redo ---
        grpUndoRedo = wx.StaticBoxSizer(wx.StaticBox(self.contextMenuPanel, wx.ID_ANY, _(u"History")), wx.VERTICAL)
        self.cmUndo  = wx.CheckBox(self.contextMenuPanel, wx.ID_ANY, _(u"Undo"))
        self.cmRedo  = wx.CheckBox(self.contextMenuPanel, wx.ID_ANY, _(u"Redo"))
        grpUndoRedo.Add(self.cmUndo,  0, wx.ALL, 4)
        grpUndoRedo.Add(self.cmRedo,  0, wx.ALL, 4)
        bSizerCM.Add(grpUndoRedo, 0, wx.EXPAND | wx.ALL, 5)

        # --- Gruppo Modifica ---
        grpEdit = wx.StaticBoxSizer(wx.StaticBox(self.contextMenuPanel, wx.ID_ANY, _(u"Edit")), wx.VERTICAL)
        self.cmCut    = wx.CheckBox(self.contextMenuPanel, wx.ID_ANY, _(u"Cut"))
        self.cmCopy   = wx.CheckBox(self.contextMenuPanel, wx.ID_ANY, _(u"Copy"))
        self.cmPaste  = wx.CheckBox(self.contextMenuPanel, wx.ID_ANY, _(u"Paste"))
        self.cmDelete = wx.CheckBox(self.contextMenuPanel, wx.ID_ANY, _(u"Delete"))
        self.cmConfirmDelete = wx.CheckBox(self.contextMenuPanel, wx.ID_ANY, _(u"Ask confirmation before deleting"))
        grpEdit.Add(self.cmCut,    0, wx.ALL, 4)
        grpEdit.Add(self.cmCopy,   0, wx.ALL, 4)
        grpEdit.Add(self.cmPaste,  0, wx.ALL, 4)
        grpEdit.Add(self.cmDelete, 0, wx.ALL, 4)
        grpEdit.Add(self.cmConfirmDelete, 0, wx.LEFT | wx.BOTTOM, 20)  # indentato sotto Delete
        bSizerCM.Add(grpEdit, 0, wx.EXPAND | wx.ALL, 5)

        # --- Gruppo Azioni speciali ---
        grpSpecial = wx.StaticBoxSizer(wx.StaticBox(self.contextMenuPanel, wx.ID_ANY, _(u"Special actions")), wx.VERTICAL)
        self.cmPasteChords           = wx.CheckBox(self.contextMenuPanel, wx.ID_ANY, _(u"Paste chords"))
        self.cmPropagateVerseChords  = wx.CheckBox(self.contextMenuPanel, wx.ID_ANY, _(u"Propagate verse chords"))
        self.cmPropagateChorusChords = wx.CheckBox(self.contextMenuPanel, wx.ID_ANY, _(u"Propagate chorus chords"))
        self.cmCopyTextOnly          = wx.CheckBox(self.contextMenuPanel, wx.ID_ANY, _(u"Copy text only"))
        grpSpecial.Add(self.cmPasteChords,           0, wx.ALL, 4)
        grpSpecial.Add(self.cmPropagateVerseChords,  0, wx.ALL, 4)
        grpSpecial.Add(self.cmPropagateChorusChords, 0, wx.ALL, 4)
        grpSpecial.Add(self.cmCopyTextOnly,          0, wx.ALL, 4)
        bSizerCM.Add(grpSpecial, 0, wx.EXPAND | wx.ALL, 5)

        # --- Gruppo Selezione ---
        grpSel = wx.StaticBoxSizer(wx.StaticBox(self.contextMenuPanel, wx.ID_ANY, _(u"Selection")), wx.VERTICAL)
        self.cmSelectAll = wx.CheckBox(self.contextMenuPanel, wx.ID_ANY, _(u"Select all"))
        grpSel.Add(self.cmSelectAll, 0, wx.ALL, 4)
        bSizerCM.Add(grpSel, 0, wx.EXPAND | wx.ALL, 5)

        self.contextMenuPanel.SetSizer(bSizerCM)
        self.contextMenuPanel.Layout()
        bSizerCM.Fit(self.contextMenuPanel)
        self.notebook.AddPage(self.contextMenuPanel, _(u"Context menu"), False)
        # --- Fine Tab "Context menu" ---

        # --- Tab "File associations" (Windows e Linux) ---
        import platform as _platform
        self._fileAssocAvailable = (_platform.system() in ('Windows', 'Linux'))
        self.fileAssocPanel = wx.Panel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizerFA = wx.BoxSizer(wx.VERTICAL)

        if self._fileAssocAvailable:
            headerFA = wx.StaticText(self.fileAssocPanel, wx.ID_ANY,
                _(u"Associate file extensions with Songpress++.\nChanges apply to the current user only."),
                wx.DefaultPosition, wx.DefaultSize, 0)
            headerFA.Wrap(480)
            bSizerFA.Add(headerFA, 0, wx.ALL, 8)
            bSizerFA.Add(wx.StaticLine(self.fileAssocPanel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

            self._fileAssocExts = ["crd", "cho", "chordpro", "chopro", "pro", "tab"]
            self._fileAssocCBs  = {}
            for ext in self._fileAssocExts:
                cb = wx.CheckBox(self.fileAssocPanel, wx.ID_ANY, u"." + ext)
                self._fileAssocCBs[ext] = cb
                bSizerFA.Add(cb, 0, wx.ALL, 4)

            bSizerFA.Add(wx.StaticLine(self.fileAssocPanel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)

            bSizerFABulk = wx.BoxSizer(wx.HORIZONTAL)
            btnAssocAll = wx.Button(self.fileAssocPanel, wx.ID_ANY, _(u"Associate all"))
            bSizerFABulk.Add(btnAssocAll, 0, wx.ALL, 4)
            btnUnassocAll = wx.Button(self.fileAssocPanel, wx.ID_ANY, _(u"Unassociate all"))
            bSizerFABulk.Add(btnUnassocAll, 0, wx.ALL, 4)
            bSizerFA.Add(bSizerFABulk, 0, wx.LEFT, 4)
            btnAssocAll.Bind(wx.EVT_BUTTON, self.OnAssociateAll)
            btnUnassocAll.Bind(wx.EVT_BUTTON, self.OnUnassociateAll)
            self._btnAssocAll   = btnAssocAll
            self._btnUnassocAll = btnUnassocAll

            bSizerFA.Add(wx.StaticLine(self.fileAssocPanel), 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.TOP, 5)
            btnApply = wx.Button(self.fileAssocPanel, wx.ID_ANY, _(u"Apply now"))
            bSizerFA.Add(btnApply, 0, wx.ALL, 8)
            btnApply.Bind(wx.EVT_BUTTON, self.OnApplyFileAssoc)
            self._btnApplyFileAssoc = btnApply
        else:
            note = wx.StaticText(self.fileAssocPanel, wx.ID_ANY,
                _(u"File association is not available on this operating system."),
                wx.DefaultPosition, wx.DefaultSize, 0)
            bSizerFA.Add(note, 0, wx.ALL, 8)

        self.fileAssocPanel.SetSizer(bSizerFA)
        self.fileAssocPanel.Layout()
        bSizerFA.Fit(self.fileAssocPanel)
        self.notebook.AddPage(self.fileAssocPanel, _(u"File associations"), False)
        # --- Fine Tab "File associations" ---

        # Connect colour events
        self.klavierColourBtn.Bind(wx.EVT_BUTTON, self.OnKlavierPickColour)
        self.klavierHexCtrl.Bind(wx.EVT_TEXT, self.OnKlavierHexChanged)
        self.editorBgBtn.Bind(wx.EVT_BUTTON, self.OnEditorBgPickColour)
        self.editorBgHexCtrl.Bind(wx.EVT_TEXT, self.OnEditorBgHexChanged)
        self.selColourBtn.Bind(wx.EVT_BUTTON, self.OnSelColourPickColour)
        self.selColourHexCtrl.Bind(wx.EVT_TEXT, self.OnSelColourHexChanged)

        self.capEditorBtn.Bind(wx.EVT_BUTTON, self.OnCapEditorPickColour)
        self.capEditorHexCtrl.Bind(wx.EVT_TEXT, self.OnCapEditorHexChanged)
        self.capPreviewBtn.Bind(wx.EVT_BUTTON, self.OnCapPreviewPickColour)
        self.capPreviewHexCtrl.Bind(wx.EVT_TEXT, self.OnCapPreviewHexChanged)

        bSizer10.Add(self.notebook, 1, wx.EXPAND | wx.ALL, 5)

        # --- Barra bottoni con pin button ---
        btnBarSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btnPin = wx.Button(self, wx.ID_ANY, u"📌", size=(32, -1))
        self.btnPin.SetToolTip(_(u"Keep this dialog open after applying"))
        self.m_sdbSizer3OK = wx.Button(self, wx.ID_OK)
        self.m_sdbSizer3Cancel = wx.Button(self, wx.ID_CANCEL)
        self.m_sdbSizer3OK.SetDefault()
        btnBarSizer.Add(self.btnPin, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        btnBarSizer.AddStretchSpacer()
        btnBarSizer.Add(self.m_sdbSizer3OK, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)
        btnBarSizer.Add(self.m_sdbSizer3Cancel, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 4)

        bSizer10.Add(btnBarSizer, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 4)

        self.SetSizer(bSizer10)
        self.Layout()
        self.Centre(wx.BOTH)

        # Connect Events
        self.fontCB.Bind(wx.EVT_KILL_FOCUS, self.OnFontSelected)
        self.sizeCB.Bind(wx.EVT_COMBOBOX, self.OnFontSelected)
        self.sizeCB.Bind(wx.EVT_KILL_FOCUS, self.OnFontSelected)
        self.sizeCB.Bind(wx.EVT_TEXT_ENTER, self.OnFontSelected)
        self.m_sdbSizer3OK.Bind(wx.EVT_BUTTON, self.OnOk)
        self.btnPin.Bind(wx.EVT_BUTTON, self.OnPin)
        self.clearRecentFilesBtn.Bind(wx.EVT_BUTTON, self.OnClearRecentFiles)
        self.openTemplatesFolderBtn.Bind(wx.EVT_BUTTON, self.OnOpenTemplatesFolder)
        self.showDebugMsgCB.Bind(wx.EVT_CHECKBOX, self.OnShowDebugMsgChanged)
        self.cmConfirmDelete.Bind(wx.EVT_CHECKBOX, self.OnCmConfirmDeleteChanged)

    def __del__(self):
        pass

    def OnFontSelected(self, event):
        event.Skip()

    def OnOk(self, event):
        event.Skip()

    def OnPin(self, event):
        event.Skip()

    def OnKlavierHexChanged(self, event):
        event.Skip()

    def OnKlavierPickColour(self, event):
        event.Skip()

    def OnEditorBgHexChanged(self, event):
        event.Skip()

    def OnEditorBgPickColour(self, event):
        event.Skip()

    def OnSelColourHexChanged(self, event):
        event.Skip()

    def OnSelColourPickColour(self, event):
        event.Skip()

    def OnCapEditorHexChanged(self, event):
        event.Skip()

    def OnCapEditorPickColour(self, event):
        event.Skip()

    def OnCapPreviewHexChanged(self, event):
        event.Skip()

    def OnCapPreviewPickColour(self, event):
        event.Skip()

    def OnClearRecentFiles(self, event):
        event.Skip()

    def OnOpenTemplatesFolder(self, event):
        event.Skip()

    def OnApplyFileAssoc(self, event):
        event.Skip()

    def OnAssociateAll(self, event):
        event.Skip()

    def OnUnassociateAll(self, event):
        event.Skip()

    def OnSyntaxHexChanged(self, event):
        event.Skip()

    def OnSyntaxPickColour(self, event):
        event.Skip()

    def OnThemeLoad(self, event):
        event.Skip()

    def OnThemeSave(self, event):
        event.Skip()

    def OnThemeDelete(self, event):
        event.Skip()

    def OnShowDebugMsgChanged(self, event):
        event.Skip()

    def OnCmConfirmDeleteChanged(self, event):
        event.Skip()
