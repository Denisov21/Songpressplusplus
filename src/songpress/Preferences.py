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
        self.notations = [enNotation, itNotation, itUcNotation, deNotation, tradDeNotation, frNotation, ptNotation]
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
        self._LoadContextMenu()
        self._LoadEditorBg()
        self._LoadSelColour()
        self._LoadPrintOptions()
        self._LoadMultiCursor()
        self._LoadTempoIconSize()
        self._LoadWindowGeometryPref()

    def _LoadKlavierColour(self):
        self.config.SetPath('/KlavierColour')
        h = self.config.Read('highlightHex')
        self.klavierHighlightHex = h if h else '#D23C3C'
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
        self._SaveContextMenu()
        self._SaveEditorBg()
        self._SaveSelColour()
        self._SavePrintOptions()
        self._SaveMultiCursor()
        self._SaveTempoIconSize()
        self._SaveWindowGeometryPref()
        self.config.Flush()

    def _SaveKlavierColour(self):
        self.config.SetPath('/KlavierColour')
        self.config.Write('highlightHex', getattr(self, 'klavierHighlightHex', '#D23C3C'))
        self.config.SetPath('/')

    def _SaveContextMenu(self):
        self.config.SetPath('/ContextMenu')
        self.config.Write('undo',         '1' if getattr(self, 'cmUndo',         True) else '0')
        self.config.Write('redo',         '1' if getattr(self, 'cmRedo',         True) else '0')
        self.config.Write('cut',          '1' if getattr(self, 'cmCut',          True) else '0')
        self.config.Write('copy',         '1' if getattr(self, 'cmCopy',         True) else '0')
        self.config.Write('paste',        '1' if getattr(self, 'cmPaste',        True) else '0')
        self.config.Write('delete',       '1' if getattr(self, 'cmDelete',       True) else '0')
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
