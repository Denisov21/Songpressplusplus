###############################################################
# Name:             Preferences.py
# Purpose:     Hold program preferences
# Author:         Luca Allulli (webmaster@roma21.it)
# Created:     2010-01-31
# Modified by:  Denisov21
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
##############################################################

import datetime

from . import i18n
from .SongFormat import *
from .decorators import StandardVerseNumbers
from .Transpose import *

_ = wx.GetTranslation


def get_update_frequencies():
    return {
        0: _("Never"),
        7: _("Week"),
        14: _("Two weeks"),
        30: _("Month"),
        60: _("Two months"),
    }


def get_chords_positions():
    return {
        'above': _("Above text"),
        'below': _("Below text"),
    }
    
class Preferences(object):
    """
        Available preferences

        * format
        * decoratorFormat
        * decorator
        * chorusLabel (None or string)
        * labelVerses
        * editorFace
        * editorSize
        * fontFace
        * defaultNotation
        * notations
        * defaultNotation
        * autoAdjustSpuriousLines
        * autoAdjustTab2Chordpro
        * autoAdjustEasyKey
        * chordsPosition ('above' or 'below')
        * locale
        * updateFrequency (days, or 0 for never)
        * ignoredUpdates
        * updateUrl
        * updateLastCheck
        * Set/GetEasyChordsGroup
        * GetEasyChords
        * showRecentFiles (bool)
    """
    def __init__(self):
        object.__init__(self)
        self.config = wx.Config.Get()
        self.format = SongFormat()
        self.decoratorFormat = StandardVerseNumbers.Format(self.format, _("Chorus"))
        self.decorator = StandardVerseNumbers.Decorator(self.decoratorFormat)
        self.notations = [enNotation, itNotation, itUcNotation, deNotation, tradDeNotation, frNotation, ptNotation, nashvilleNotation, romanNotation]
        self.easyChordsGroup = {}
        self.titleLineWidth = 4
        self.verseBoxWidth = 1
        self.Load()

    def SetFont(self, font, showChords=None):
        self.fontFace = font
        self.format.face = font
        self.format.comment.face = font
        self.format.chord.face = font
        self.format.chorus.face = font
        self.format.chorus.chord.face = font
        self.format.chorus.comment.face = font
        for v in self.format.verse:
            v.face = font
            v.chord.face = font
            v.comment.face = font
        self.format.title.face = font
        self.format.subtitle.face = font
        self.decoratorFormat.face = font
        self.decoratorFormat.chorus.face = font
        if showChords is not None:
            self.format.showChords = showChords

    def Load(self):
        self.notices = {}
        self.config.SetPath('/Format')
        l = self.config.Read('ChorusLabel')
        if l:
            self.chorusLabel = l
            self.decoratorFormat.SetChorusLabel(l)
        else:
            self.chorusLabel = None
        showChords = int(self.config.Read('ShowChords', "2"))
        self.config.SetPath('/Format/Font')
        face = self.config.Read('Face')
        if face:
            self.fontFace = face
        else:
            self.fontFace = "Arial"
        self.SetFont(self.fontFace, showChords)
        self.config.SetPath('/Format/Style')
        labelVerses = self.config.Read('LabelVerses')
        if labelVerses:
            self.labelVerses = bool(int(labelVerses))
        else:
            self.labelVerses = True
        self.config.SetPath('/Editor')
        self.editorFace = self.config.Read('Face')
        self.editorSize = self.config.Read('Size')
        if not self.editorFace:
            self.editorFace = wx.SystemSettings().GetFont(wx.SYS_ANSI_FIXED_FONT).GetFaceName() # "Lucida Console"
            self.editorSize = 12
        else:
            self.editorSize = int(self.editorSize)
        n = self.config.Read('DefaultNotation')
        if n:
            self.defaultNotation = n
            self.notations = [x for x in self.notations if x.id == n] + [x for x in self.notations if x.id != n]
        else:
            lang = i18n.getLang()
            self.defaultNotation = None
            if lang in defaultLangNotation:
                n = defaultLangNotation[lang].id
                self.notations = [x for x in self.notations if x.id == n] + [x for x in self.notations if x.id != n]
        self.config.SetPath('/AutoAdjust')
        spuriousLines = self.config.Read('spuriousLines')
        if spuriousLines:
            self.autoAdjustSpuriousLines = bool(int(spuriousLines))
        else:
            self.autoAdjustSpuriousLines = True
        tab2chordpro = self.config.Read('tab2chordpro')
        if tab2chordpro:
            self.autoAdjustTab2Chordpro = bool(int(tab2chordpro))
        else:
            self.autoAdjustTab2Chordpro = True
        easyKey = self.config.Read('easyKey')
        if easyKey:
            self.autoAdjustEasyKey = bool(int(easyKey))
        else:
            self.autoAdjustEasyKey = False
            self.notices['firstTimeEasyKey'] = True
        chordsPosition = self.config.Read('chordsPosition')
        if chordsPosition in ('above', 'below'):
            self.chordsPosition = chordsPosition
        else:
            self.chordsPosition = 'above'
        self.config.SetPath('/AutoAdjust/EasyChordsGroups')
        for k in easyChordsOrder:
            l = self.config.Read(k)
            if l:
                l = int(l)
            else:
                l = easyChords[k][2]
            self.SetEasyChordsGroup(k, l)
        self.config.SetPath('/App')
        ext = self.config.Read('defaultExtension')
        if not ext:
            self.defaultExtension = 'crd'
        else:
            self.defaultExtension = ext
        lang = self.config.Read('locale')
        if not lang:
            self.locale = None
        else:
            self.locale = lang
        self.config.SetPath('/AutoUpdate')
        f = self.config.Read('frequency')
        if not f:
            self.updateFrequency = 7
        else:
            self.updateFrequency = int(f)
        i = self.config.Read('ignored')
        if not i:
            self.ignoredUpdates = set()
        else:
            self.ignoredUpdates = set(i.split(','))
        u = self.config.Read('url')
        if not u:
            self.updateUrl = 'https://songpress.skeed.it/xmlrpc'
        else:
            self.updateUrl = u
        d = self.config.Read('lastCheck')
        if not d:
            self.updateLastCheck = None
        else:
            self.updateLastCheck = datetime.datetime.fromordinal(int(d))
        self.config.SetPath('/App')
        showRecentFiles = self.config.Read('showRecentFiles')
        if showRecentFiles:
            self.showRecentFiles = bool(int(showRecentFiles))
        else:
            self.showRecentFiles = True
        self.config.SetPath('/Format/Style')
        titleLineWidth = self.config.Read('TitleLineWidth')
        self.titleLineWidth = int(titleLineWidth) if titleLineWidth else 4
        verseBoxWidth = self.config.Read('VerseBoxWidth')
        self.verseBoxWidth = int(verseBoxWidth) if verseBoxWidth else 1
        self._LoadKlavierColour()
        self._LoadFingerNumColour()
        self._LoadContextMenu()
        self._LoadEditorBg()
        self._LoadSelColour()
        self._LoadCaptionColours()
        self._LoadPrintOptions()
        self._LoadMultiCursor()
        self._LoadTempoIconSize()
        self._LoadWindowGeometryPref()
        self._LoadPreviewOptions()
        self._LoadGridDisplayMode()
        self._LoadDurationBeats()
        self._LoadMusicalSymbol()
        self._LoadSyntaxColours()
        self._LoadDebugOptions()
        self._LoadIntellisense()

    def _LoadKlavierColour(self):
        self.config.SetPath('/KlavierColour')
        h = self.config.Read('highlightHex')
        self.klavierHighlightHex = h if h else '#D23C3C'
        self.config.SetPath('/')

    def _LoadFingerNumColour(self):
        self.config.SetPath('/FingerNumColour')
        h = self.config.Read('fingerNumHex')
        self.fingerNumColourHex = h if h else '#1A1A1A'
        self.config.SetPath('/')

    def _LoadContextMenu(self):
        self.config.SetPath('/ContextMenu')
        def rb(key):
            v = self.config.Read(key)
            return bool(int(v)) if v != '' else True
        self.cmUndo         = rb('undo')
        self.cmRedo         = rb('redo')
        self.cmCut          = rb('cut')
        self.cmCopy         = rb('copy')
        self.cmPaste        = rb('paste')
        self.cmDelete       = rb('delete')
        v = self.config.Read('confirmDelete')
        self.cmConfirmDelete = bool(int(v)) if v != '' else False
        self.cmPasteChords           = rb('pasteChords')
        self.cmPropagateVerseChords  = rb('propagateVerseChords')
        self.cmPropagateChorusChords = rb('propagateChorusChords')
        self.cmCopyTextOnly          = rb('copyTextOnly')
        self.cmSelectAll    = rb('selectAll')
        self.config.SetPath('/')

    def _LoadEditorBg(self):
        self.config.SetPath('/Editor')
        h = self.config.Read('BgHex')
        self.editorBgHex = h if h else '#FFFFFF'
        self.config.SetPath('/')

    def _LoadSelColour(self):
        self.config.SetPath('/Editor')
        h = self.config.Read('SelColourHex')
        self.selColourHex = h if h else '#C0C0C0'
        self.config.SetPath('/')

    def _LoadPrintOptions(self):
        self.config.SetPath('/Print')
        v = self.config.Read('showPrintPreview')
        self.showPrintPreview = bool(int(v)) if v != '' else True
        self.config.SetPath('/')

    def _LoadMultiCursor(self):
        self.config.SetPath('/Editor')
        v = self.config.Read('multiCursor')
        self.multiCursor = bool(int(v)) if v != '' else False
        self.config.SetPath('/')

    def _LoadTempoIconSize(self):
        self.config.SetPath('/Format')
        v = self.config.Read('tempoIconSize')
        self.tempoIconSize = int(v) if v in ('16', '24', '32') else 24
        self.config.SetPath('/')

    def _LoadWindowGeometryPref(self):
        self.config.SetPath('/App')
        v = self.config.Read('saveWindowGeometry')
        self.saveWindowGeometry = bool(int(v)) if v != '' else True
        self.config.SetPath('/')

    def _LoadPreviewOptions(self):
        self.config.SetPath('/Preview')
        v = self.config.Read('showPageIndicator')
        self.showPageIndicator = bool(int(v)) if v != '' else True
        v = self.config.Read('greyBackground')
        self.greyBackground = bool(int(v)) if v != '' else True
        v = self.config.Read('debounceRefresh')
        self.debounceRefresh = bool(int(v)) if v != '' else True
        v = self.config.Read('dblClickFocus')
        self.dblClickFocus = bool(int(v)) if v != '' else True
        v = self.config.Read('previewMinSize')
        self.previewMinSize = bool(int(v)) if v != '' else True
        v = self.config.Read('guideViewer')
        self.guideViewer = v if v in ('builtin', 'markdown', 'mistune') else 'markdown'
        v = self.config.Read('guideMarkdownImgPath')
        self.guideMarkdownImgPath = bool(int(v)) if v != '' else False
        self.config.SetPath('/')

    def _LoadGridDisplayMode(self):
        """Carica la modalità di visualizzazione del blocco {start_of_grid}.

        Valori:
            'pipe'  -- | C   | G   | Am  | F   |  (separatori pipe, default)
            'plain' -- C   G   Am  F               (testo spaziato senza pipe)
            'table' -- griglia con celle evidenziate (bordi disegnati)
        """
        self.config.SetPath('/Format')
        v = self.config.Read('gridDisplayMode')
        self.gridDisplayMode = v if v in ('pipe', 'plain', 'table') else 'pipe'
        v2 = self.config.Read('gridDefaultLabel')
        self.gridDefaultLabel = v2 if v2 else _("Grid")
        v3 = self.config.Read('gridSpaceAsPipe')
        self.gridSpaceAsPipe = bool(int(v3)) if v3 != '' else True
        v4 = self.config.Read('gridSizeDir')
        self.gridSizeDir = v4 if v4 in ('both', 'horizontal', 'vertical') else 'both'
        self.config.SetPath('/')

    def Bool2String(self, param):
        return "1" if param else "0"

    def Save(self):
        self.config.SetPath('/Format')
        if self.chorusLabel is not None:
            self.config.Write('ChorusLabel', self.chorusLabel)
        self.config.Write('ShowChords', str(self.format.showChords))
        self.config.SetPath('/Format/Font')
        face = self.config.Write('Face', self.fontFace)
        self.config.SetPath('/Format/Style')
        self.config.Write('LabelVerses', self.Bool2String(self.labelVerses))
        self.config.SetPath('/Editor')
        self.config.Write('Face', self.editorFace)
        self.config.Write('Size', str(self.editorSize))
        if self.defaultNotation is not None:
            self.config.Write('DefaultNotation', self.defaultNotation)
        self.config.SetPath('/AutoAdjust')
        self.config.Write('spuriousLines', self.Bool2String(self.autoAdjustSpuriousLines))
        self.config.Write('tab2chordpro', self.Bool2String(self.autoAdjustTab2Chordpro))
        self.config.Write('easyKey', self.Bool2String(self.autoAdjustEasyKey))
        self.config.Write('chordsPosition', self.chordsPosition)
        self.config.SetPath('/AutoAdjust/EasyChordsGroups')
        for k in easyChordsOrder:
            self.config.Write(k, str(self.GetEasyChordsGroup(k)))
        self.config.SetPath('/App')
        self.config.Write('defaultExtension', self.defaultExtension)
        if self.locale is not None:
            lang = self.config.Write('locale', self.locale)
        self.config.SetPath('/AutoUpdate')
        self.config.Write('frequency', str(self.updateFrequency))
        self.config.Write('ignored', ",".join(self.ignoredUpdates))
        self.config.Write('url', self.updateUrl)
        if self.updateLastCheck is not None:
            self.config.Write('lastCheck', str(self.updateLastCheck.toordinal()))
        self.config.SetPath('/App')
        self.config.Write('showRecentFiles', self.Bool2String(self.showRecentFiles))
        self.config.SetPath('/Format/Style')
        self.config.Write('TitleLineWidth', str(self.titleLineWidth))
        self.config.Write('VerseBoxWidth', str(self.verseBoxWidth))
        self._SaveKlavierColour()
        self._SaveFingerNumColour()
        self._SaveContextMenu()
        self._SaveEditorBg()
        self._SaveSelColour()
        self._SaveCaptionColours()
        self._SavePrintOptions()
        self._SaveMultiCursor()
        self._SaveTempoIconSize()
        self._SaveWindowGeometryPref()
        self._SavePreviewOptions()
        self._SaveGridDisplayMode()
        self._SaveDurationBeats()
        self._SaveMusicalSymbol()
        self._SaveSyntaxColours()
        self._SaveDebugOptions()
        self._SaveIntellisense()
        self.config.Flush()

    def _SaveKlavierColour(self):
        self.config.SetPath('/KlavierColour')
        self.config.Write('highlightHex', getattr(self, 'klavierHighlightHex', '#D23C3C'))
        self.config.SetPath('/')

    def _SaveFingerNumColour(self):
        self.config.SetPath('/FingerNumColour')
        self.config.Write('fingerNumHex', getattr(self, 'fingerNumColourHex', '#1A1A1A'))
        self.config.SetPath('/')

    def _SaveContextMenu(self):
        self.config.SetPath('/ContextMenu')
        self.config.Write('undo',         '1' if getattr(self, 'cmUndo',         True) else '0')
        self.config.Write('redo',         '1' if getattr(self, 'cmRedo',         True) else '0')
        self.config.Write('cut',          '1' if getattr(self, 'cmCut',          True) else '0')
        self.config.Write('copy',         '1' if getattr(self, 'cmCopy',         True) else '0')
        self.config.Write('paste',        '1' if getattr(self, 'cmPaste',        True) else '0')
        self.config.Write('delete',       '1' if getattr(self, 'cmDelete',       True) else '0')
        self.config.Write('confirmDelete', '1' if getattr(self, 'cmConfirmDelete', False) else '0')
        self.config.Write('pasteChords',           '1' if getattr(self, 'cmPasteChords',           True) else '0')
        self.config.Write('propagateVerseChords',  '1' if getattr(self, 'cmPropagateVerseChords',  True) else '0')
        self.config.Write('propagateChorusChords', '1' if getattr(self, 'cmPropagateChorusChords', True) else '0')
        self.config.Write('copyTextOnly',          '1' if getattr(self, 'cmCopyTextOnly',          True) else '0')
        self.config.Write('selectAll',    '1' if getattr(self, 'cmSelectAll',    True) else '0')
        self.config.SetPath('/')

    def _SaveEditorBg(self):
        self.config.SetPath('/Editor')
        self.config.Write('BgHex', getattr(self, 'editorBgHex', '#FFFFFF'))
        self.config.SetPath('/')

    def _SaveSelColour(self):
        self.config.SetPath('/Editor')
        self.config.Write('SelColourHex', getattr(self, 'selColourHex', '#C0C0C0'))
        self.config.SetPath('/')

    def _LoadCaptionColours(self):
        self.config.SetPath('/CaptionColours')
        h = self.config.Read('EditorActiveHex')
        self.captionEditorActiveHex = h if h else '#4682C8'
        h = self.config.Read('PreviewActiveHex')
        self.captionPreviewActiveHex = h if h else '#329B82'
        self.config.SetPath('/')

    def _SaveCaptionColours(self):
        self.config.SetPath('/CaptionColours')
        self.config.Write('EditorActiveHex',  getattr(self, 'captionEditorActiveHex',  '#4682C8'))
        self.config.Write('PreviewActiveHex', getattr(self, 'captionPreviewActiveHex', '#329B82'))
        self.config.SetPath('/')

    # Colori predefiniti per ogni stile sintattico dell'editor
    SYNTAX_COLOUR_DEFAULTS = {
        'normal':   '#000000',
        'chorus':   '#000000',
        'chord':    '#FF0000',
        'command':  '#0000FF',
        'attr':     '#008000',
        'comment':  '#808080',
        'tabgrid':  '#8B5A00',
    }

    def _LoadSyntaxColours(self):
        self.config.SetPath('/EditorSyntaxColours')
        self.syntaxColours = {}
        for key, default in self.SYNTAX_COLOUR_DEFAULTS.items():
            h = self.config.Read(key)
            self.syntaxColours[key] = h if h else default
        self.config.SetPath('/')

    def _SaveSyntaxColours(self):
        self.config.SetPath('/EditorSyntaxColours')
        for key, default in self.SYNTAX_COLOUR_DEFAULTS.items():
            self.config.Write(key, self.syntaxColours.get(key, default))
        self.config.SetPath('/')

    def _LoadDebugOptions(self):
        self.config.SetPath('/Debug')
        v = self.config.Read('showDebugMsg')
        self.showDebugMsg = bool(int(v)) if v != '' else False
        self.config.SetPath('/')

    def _SaveDebugOptions(self):
        self.config.SetPath('/Debug')
        self.config.Write('showDebugMsg', '1' if getattr(self, 'showDebugMsg', False) else '0')
        self.config.SetPath('/')

    def _LoadIntellisense(self):
        self.config.SetPath('/Editor')
        v = self.config.Read('intellisense')
        self.intellisense = bool(int(v)) if v != '' else True
        self.config.SetPath('/')

    def _SaveIntellisense(self):
        self.config.SetPath('/Editor')
        self.config.Write('intellisense', '1' if getattr(self, 'intellisense', True) else '0')
        self.config.SetPath('/')

    def _SavePrintOptions(self):
        self.config.SetPath('/Print')
        self.config.Write('showPrintPreview', '1' if getattr(self, 'showPrintPreview', True) else '0')
        self.config.SetPath('/')

    def _SaveMultiCursor(self):
        self.config.SetPath('/Editor')
        self.config.Write('multiCursor', '1' if getattr(self, 'multiCursor', False) else '0')
        self.config.SetPath('/')

    def _SaveTempoIconSize(self):
        self.config.SetPath('/Format')
        self.config.Write('tempoIconSize', str(getattr(self, 'tempoIconSize', 24)))
        self.config.SetPath('/')

    def _SaveWindowGeometryPref(self):
        self.config.SetPath('/App')
        self.config.Write('saveWindowGeometry', '1' if getattr(self, 'saveWindowGeometry', True) else '0')
        self.config.SetPath('/')

    def _SavePreviewOptions(self):
        self.config.SetPath('/Preview')
        self.config.Write('showPageIndicator', '1' if getattr(self, 'showPageIndicator', True) else '0')
        self.config.Write('greyBackground',    '1' if getattr(self, 'greyBackground',    True) else '0')
        self.config.Write('debounceRefresh',   '1' if getattr(self, 'debounceRefresh',   True) else '0')
        self.config.Write('dblClickFocus',     '1' if getattr(self, 'dblClickFocus',     True) else '0')
        self.config.Write('previewMinSize',    '1' if getattr(self, 'previewMinSize',    True) else '0')
        self.config.Write('guideViewer',           getattr(self, 'guideViewer', 'markdown'))
        self.config.Write('guideMarkdownImgPath',    '1' if getattr(self, 'guideMarkdownImgPath', False) else '0')
        self.config.SetPath('/')

    def _SaveGridDisplayMode(self):
        self.config.SetPath('/Format')
        self.config.Write('gridDisplayMode', getattr(self, 'gridDisplayMode', 'pipe'))
        self.config.Write('gridDefaultLabel', getattr(self, 'gridDefaultLabel', _("Grid")))
        self.config.Write('gridSpaceAsPipe', '1' if getattr(self, 'gridSpaceAsPipe', True) else '0')
        self.config.Write('gridSizeDir', getattr(self, 'gridSizeDir', 'both'))
        self.config.SetPath('/')

    def _LoadDurationBeats(self):
        self.config.SetPath('/Format')
        v = self.config.Read('durationBeatsColourHex')
        self.durationBeatsColourHex = v if v else '#6464C8'
        v2 = self.config.Read('durationBeatsSizePct')
        try:
            self.durationBeatsSizePct = max(30, min(int(v2), 150)) if v2 != '' else 60
        except ValueError:
            self.durationBeatsSizePct = 60
        v3 = self.config.Read('durationBeatsBold')
        self.durationBeatsBold = bool(int(v3)) if v3 != '' else False
        v4 = self.config.Read('durationBeatsAlign')
        self.durationBeatsAlign = v4 if v4 in ('left', 'center', 'right') else 'right'
        self.config.SetPath('/')

    def _LoadMusicalSymbol(self):
        self.config.SetPath('/MusicalSymbol')
        v = self.config.Read('scaleEnabled')
        self.symbolScaleEnabled = bool(int(v)) if v != '' else False
        v2 = self.config.Read('fontSize')
        try:
            self.symbolFontSize = max(6, min(int(v2), 144)) if v2 != '' else 24
        except ValueError:
            self.symbolFontSize = 24
        v3 = self.config.Read('insertVerse')
        self.symbolInsertVerse = bool(int(v3)) if v3 != '' else False
        self.config.SetPath('/')

    def _SaveDurationBeats(self):
        self.config.SetPath('/Format')
        self.config.Write('durationBeatsColourHex', getattr(self, 'durationBeatsColourHex', '#6464C8'))
        self.config.Write('durationBeatsSizePct',   str(getattr(self, 'durationBeatsSizePct', 60)))
        self.config.Write('durationBeatsBold',      '1' if getattr(self, 'durationBeatsBold', False) else '0')
        self.config.Write('durationBeatsAlign',    getattr(self, 'durationBeatsAlign', 'right'))
        self.config.SetPath('/')

    def _SaveMusicalSymbol(self):
        self.config.SetPath('/MusicalSymbol')
        self.config.Write('scaleEnabled', '1' if getattr(self, 'symbolScaleEnabled', False) else '0')
        self.config.Write('fontSize', str(getattr(self, 'symbolFontSize', 24)))
        self.config.Write('insertVerse', '1' if getattr(self, 'symbolInsertVerse', False) else '0')
        self.config.SetPath('/')

    def SetChorusLabel(self, c):
        self.chorusLabel = c
        self.decoratorFormat.SetChorusLabel(c)

    def SetChordsPosition(self, position):
        """Set chords position: 'above' or 'below'."""
        if position in ('above', 'below'):
            self.chordsPosition = position

    def SetDefaultNotation(self, notation):
        self.defaultNotation = notation
        self.notations = [x for x in self.notations if x.id == notation] + [x for x in self.notations if x.id != notation]

    def SetEasyChordsGroup(self, group, level):
        self.easyChordsGroup[group] = level
        self.easyChords = None

    def GetEasyChordsGroup(self, group):
        return self.easyChordsGroup[group]

    def GetEasyChords(self):
        if self.easyChords is None:
            self.easyChords = {'Eb': -1}
            for k in easyChords:
                chords = easyChords[k][1]
                l = self.easyChordsGroup[k] / 4.0
                for c in chords:
                    if c in self.easyChords:
                        self.easyChords[c] = max(self.easyChords[c], l)
                    else:
                        self.easyChords[c] = l

        return self.easyChords
