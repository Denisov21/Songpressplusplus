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
                                             size=wx.Size(535, 530), style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        bSizer10 = wx.BoxSizer(wx.VERTICAL)

        self.notebook = wx.Notebook(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, 0)
        self.general = wx.Panel(self.notebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer11 = wx.BoxSizer(wx.VERTICAL)

        bSizer12 = wx.BoxSizer(wx.HORIZONTAL)

        self.label1 = wx.StaticText(self.general, wx.ID_ANY, _(u"Editor font"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.label1.Wrap(-1)
        bSizer12.Add(self.label1, 0, wx.ALL, 5)

        self.fontCB = FontComboBox(self.general, wx.ID_ANY, self.pref.editorFace)
        bSizer12.Add(self.fontCB, 1, wx.ALL, 5)

        self.m_staticText8 = wx.StaticText(self.general, wx.ID_ANY, _(u"Size"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText8.Wrap(-1)
        bSizer12.Add(self.m_staticText8, 0, wx.ALL, 5)

        sizeCBChoices = [_(u"7"), _(u"8"), _(u"9"), _(u"10"), _(u"11"), _(u"12"), _(u"13"), _(u"14"), _(u"16"), _(u"18"), _(u"20")]
        self.sizeCB = wx.ComboBox(self.general, wx.ID_ANY, _(u"12"), wx.DefaultPosition, wx.DefaultSize, sizeCBChoices, 0)
        self.sizeCB.SetMinSize(wx.Size(100, -1))
        bSizer12.Add(self.sizeCB, 0, wx.ALL, 5)

        bSizer11.Add(bSizer12, 0, wx.EXPAND, 5)

        # Editor background colour row
        bSizerEditorBg = wx.BoxSizer(wx.HORIZONTAL)
        self.labelEditorBg = wx.StaticText(self.general, wx.ID_ANY, _(u"Editor background colour"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelEditorBg.Wrap(-1)
        bSizerEditorBg.Add(self.labelEditorBg, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.editorBgHexCtrl = wx.TextCtrl(self.general, wx.ID_ANY, u"#FFFFFF", wx.DefaultPosition, wx.Size(80, -1), 0)
        bSizerEditorBg.Add(self.editorBgHexCtrl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.editorBgBtn = wx.Button(self.general, wx.ID_ANY, _(u"Pick…"), wx.DefaultPosition, wx.Size(60, -1), 0)
        bSizerEditorBg.Add(self.editorBgBtn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.editorBgSwatch = wx.Panel(self.general, wx.ID_ANY, wx.DefaultPosition, wx.Size(24, 24), wx.BORDER_SIMPLE)
        bSizerEditorBg.Add(self.editorBgSwatch, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        bSizer11.Add(bSizerEditorBg, 0, wx.EXPAND, 5)

        # Editor selection colour row
        bSizerSelColour = wx.BoxSizer(wx.HORIZONTAL)
        self.labelSelColour = wx.StaticText(self.general, wx.ID_ANY, _(u"Selection colour"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelSelColour.Wrap(-1)
        bSizerSelColour.Add(self.labelSelColour, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.selColourHexCtrl = wx.TextCtrl(self.general, wx.ID_ANY, u"#C0C0C0", wx.DefaultPosition, wx.Size(80, -1), 0)
        bSizerSelColour.Add(self.selColourHexCtrl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.selColourBtn = wx.Button(self.general, wx.ID_ANY, _(u"Pick…"), wx.DefaultPosition, wx.Size(60, -1), 0)
        bSizerSelColour.Add(self.selColourBtn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.selColourSwatch = wx.Panel(self.general, wx.ID_ANY, wx.DefaultPosition, wx.Size(24, 24), wx.BORDER_SIMPLE)
        bSizerSelColour.Add(self.selColourSwatch, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        bSizer11.Add(bSizerSelColour, 0, wx.EXPAND, 5)

        bSizer13 = wx.BoxSizer(wx.HORIZONTAL)
        self.m_staticText9 = wx.StaticText(self.general, wx.ID_ANY, _(u"Preview"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText9.Wrap(-1)
        bSizer13.Add(self.m_staticText9, 0, wx.ALL, 5)
        self.editor = Editor.Editor(self.general, False, self.general)
        bSizer13.Add(self.editor, 1, wx.ALL | wx.EXPAND, 5)
        bSizer11.Add(bSizer13, 1, wx.EXPAND, 5)

        bSizer141 = wx.BoxSizer(wx.HORIZONTAL)
        self.m_staticText101 = wx.StaticText(self.general, wx.ID_ANY, _(u"Default notation"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText101.Wrap(-1)
        bSizer141.Add(self.m_staticText101, 0, wx.ALL, 5)
        notationChChoices = []
        self.notationCh = wx.Choice(self.general, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, notationChChoices, 0)
        self.notationCh.SetSelection(0)
        bSizer141.Add(self.notationCh, 1, wx.ALL, 5)
        bSizer11.Add(bSizer141, 0, wx.EXPAND, 5)


        bSizer1412 = wx.BoxSizer(wx.HORIZONTAL)
        self.m_staticText1012 = wx.StaticText(self.general, wx.ID_ANY, _(u"Default file extension"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText1012.Wrap(-1)
        bSizer1412.Add(self.m_staticText1012, 0, wx.ALL, 5)
        extensionChoices = []
        self.extension = wx.Choice(self.general, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, extensionChoices, 0)
        self.extension.SetSelection(0)
        bSizer1412.Add(self.extension, 1, wx.ALL, 5)
        bSizer11.Add(bSizer1412, 0, wx.EXPAND, 5)

        bSizer14 = wx.BoxSizer(wx.HORIZONTAL)
        self.m_staticText10 = wx.StaticText(self.general, wx.ID_ANY, _(u"Language"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText10.Wrap(-1)
        bSizer14.Add(self.m_staticText10, 0, wx.ALL, 5)
        self.langCh = wx.adv.BitmapComboBox(self.general, wx.ID_ANY, style=wx.CB_READONLY)
        self.langCh.SetSelection(0)
        bSizer14.Add(self.langCh, 1, wx.ALL, 5)
        bSizer11.Add(bSizer14, 0, wx.EXPAND, 5)

        bSizerClearRecent = wx.BoxSizer(wx.HORIZONTAL)
        self.clearRecentFilesBtn = wx.Button(self.general, wx.ID_ANY, _(u"Clear recent files"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizerClearRecent.Add(self.clearRecentFilesBtn, 0, wx.ALL, 5)
        bSizer11.Add(bSizerClearRecent, 0, wx.EXPAND, 5)

        self.showPrintPreviewCB = wx.CheckBox(self.general, wx.ID_ANY, _(u"Show print preview before printing"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer11.Add(self.showPrintPreviewCB, 0, wx.ALL, 5)

        self.multiCursorCB = wx.CheckBox(self.general, wx.ID_ANY, _(u"Enable multi-cursor (Alt+Click, Ctrl+D)"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer11.Add(self.multiCursorCB, 0, wx.ALL, 5)

        self.saveWindowGeometryCB = wx.CheckBox(self.general, wx.ID_ANY, _(u"Save window size and position on exit"), wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer11.Add(self.saveWindowGeometryCB, 0, wx.ALL, 5)

        self.general.SetSizer(bSizer11)
        self.general.Layout()
        bSizer11.Fit(self.general)
        self.notebook.AddPage(self.general, _(u"General"), True)

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

        bSizerTitleLine = wx.BoxSizer(wx.HORIZONTAL)
        self.labelTitleLine = wx.StaticText(self.formatPanel, wx.ID_ANY, _(u"Title underline thickness"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelTitleLine.Wrap(-1)
        bSizerTitleLine.Add(self.labelTitleLine, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self._titleSpinPanel = wx.Panel(self.formatPanel, wx.ID_ANY)
        self.titleLineWidthSpin = wx.SpinCtrl(self._titleSpinPanel, wx.ID_ANY, "4", wx.DefaultPosition, wx.Size(60, -1), wx.SP_ARROW_KEYS, 1, 5, 4)
        titleSpinSizer = wx.BoxSizer(wx.HORIZONTAL)
        titleSpinSizer.Add(self.titleLineWidthSpin, 0, 0, 0)
        self._titleSpinPanel.SetSizer(titleSpinSizer)
        bSizerTitleLine.Add(self._titleSpinPanel, 0, wx.ALL, 5)
        bSizerFormat.Add(bSizerTitleLine, 0, wx.EXPAND, 5)

        bSizerVerseBox = wx.BoxSizer(wx.HORIZONTAL)
        self.labelVerseBox = wx.StaticText(self.formatPanel, wx.ID_ANY, _(u"Verse number box thickness"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelVerseBox.Wrap(-1)
        bSizerVerseBox.Add(self.labelVerseBox, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self._verseSpinPanel = wx.Panel(self.formatPanel, wx.ID_ANY)
        self.verseBoxWidthSpin = wx.SpinCtrl(self._verseSpinPanel, wx.ID_ANY, "1", wx.DefaultPosition, wx.Size(60, -1), wx.SP_ARROW_KEYS, 1, 5, 1)
        verseSpinSizer = wx.BoxSizer(wx.HORIZONTAL)
        verseSpinSizer.Add(self.verseBoxWidthSpin, 0, 0, 0)
        self._verseSpinPanel.SetSizer(verseSpinSizer)
        bSizerVerseBox.Add(self._verseSpinPanel, 0, wx.ALL, 5)
        bSizerFormat.Add(bSizerVerseBox, 0, wx.EXPAND, 5)

        bSizerKlavier = wx.BoxSizer(wx.HORIZONTAL)
        self.labelKlavierColour = wx.StaticText(self.formatPanel, wx.ID_ANY, _(u"Klavier key colour"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelKlavierColour.Wrap(-1)
        bSizerKlavier.Add(self.labelKlavierColour, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.klavierHexCtrl = wx.TextCtrl(self.formatPanel, wx.ID_ANY, u"#D23C3C", wx.DefaultPosition, wx.Size(80, -1), 0)
        bSizerKlavier.Add(self.klavierHexCtrl, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.klavierColourBtn = wx.Button(self.formatPanel, wx.ID_ANY, _(u"Pick…"), wx.DefaultPosition, wx.Size(60, -1), 0)
        bSizerKlavier.Add(self.klavierColourBtn, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.klavierColourSwatch = wx.Panel(self.formatPanel, wx.ID_ANY, wx.DefaultPosition, wx.Size(24, 24), wx.BORDER_SIMPLE)
        bSizerKlavier.Add(self.klavierColourSwatch, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        bSizerFormat.Add(bSizerKlavier, 0, wx.EXPAND, 5)

        # --- Dimensione icone tempo ({tempo_*}) ---
        bSizerTempoIcon = wx.BoxSizer(wx.HORIZONTAL)
        self.labelTempoIconSize = wx.StaticText(self.formatPanel, wx.ID_ANY, _(u"Tempo icon size"), wx.DefaultPosition, wx.DefaultSize, 0)
        self.labelTempoIconSize.Wrap(-1)
        bSizerTempoIcon.Add(self.labelTempoIconSize, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        self.tempoIconSize16 = wx.RadioButton(self.formatPanel, wx.ID_ANY, u"16×16", wx.DefaultPosition, wx.DefaultSize, wx.RB_GROUP)
        self.tempoIconSize24 = wx.RadioButton(self.formatPanel, wx.ID_ANY, u"24×24")
        self.tempoIconSize32 = wx.RadioButton(self.formatPanel, wx.ID_ANY, u"32×32")
        bSizerTempoIcon.Add(self.tempoIconSize16, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        bSizerTempoIcon.Add(self.tempoIconSize24, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        bSizerTempoIcon.Add(self.tempoIconSize32, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        bSizerFormat.Add(bSizerTempoIcon, 0, wx.EXPAND, 5)

        self.formatPanel.SetSizer(bSizerFormat)
        self.formatPanel.Layout()
        bSizerFormat.Fit(self.formatPanel)
        self.notebook.AddPage(self.formatPanel, _(u"Format"), False)
        # --- Fine Tab "Format" ---

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
        grpEdit.Add(self.cmCut,    0, wx.ALL, 4)
        grpEdit.Add(self.cmCopy,   0, wx.ALL, 4)
        grpEdit.Add(self.cmPaste,  0, wx.ALL, 4)
        grpEdit.Add(self.cmDelete, 0, wx.ALL, 4)
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

    def OnClearRecentFiles(self, event):
        event.Skip()

    def OnApplyFileAssoc(self, event):
        event.Skip()

    def OnAssociateAll(self, event):
        event.Skip()

    def OnUnassociateAll(self, event):
        event.Skip()
