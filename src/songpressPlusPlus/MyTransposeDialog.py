###############################################################
# Name:             MyTransposeDialog.py
# Purpose:      Transposing dialog
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2009-12-02
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
##############################################################

from .TransposeDialog import *
from .Transpose import *

# Notations that represent relative degrees (not absolute pitch):
# transposing them would shift the degree labels, which makes no sense.
_RELATIVE_NOTATION_CLASSES = (NashvilleNotation, RomanNotation)


class MyTransposeDialog(TransposeDialog):
    def __init__(self, parent, notations, text):
        TransposeDialog.__init__(self, parent)
        self.notations = notations
        self.text = text
        fn = autodetectNotation(text, notations)
        self.fk = autodetectKey(text, fn)
        for n in self.notations:
            i = self.notation.Append(n.desc)
            self.notation.SetClientData(i, n)
            if n == fn:
                self.notation.SetSelection(i)
        self.OnNotation()
            
    def OnNotation(self, event=None):
        i = self.notation.GetSelection()
        n = self.notation.GetClientData(i)
        self.fromKey.Clear()
        self.toKey.Clear()
        for k in orderedKeys:
            kn = "%s / %s" % (
                translateChord(k, dNotation=n),
                translateChord(scales[k][1][5] + "m", dNotation=n),
            )
            i = self.fromKey.Append(kn)
            self.fromKey.SetClientData(i, k)
            if chord2pos(self.fk) == chord2pos(k):
                self.fromKey.SetSelection(i)
            i = self.toKey.Append(kn)
            self.toKey.SetClientData(i, k)
        self.UpdateToKey()
        if event is not None:
            event.Skip()
            
    def UpdateToKey(self):
        try:
            s = int(self.semitones.GetValue())
        except:
            return
        self.toKey.SetSelection((self.fromKey.GetSelection() + s) % 12)
        
    def GetTransposed(self):
        s = self.fromKey.GetClientData(self.fromKey.GetSelection())
        d = self.toKey.GetClientData(self.toKey.GetSelection())
        acc = self.accidentals.GetSelection()

        # Apply transposition for every absolute-pitch notation so that
        # a song containing chords written in mixed notations (e.g. both
        # "Sol" and "G" in the same file) is transposed correctly in full.
        # Relative-degree notations (Nashville, Roman) are intentionally
        # skipped: their degree labels do not represent absolute pitches
        # and must not be shifted.
        text = self.text
        for n in self.notations:
            if isinstance(n, _RELATIVE_NOTATION_CLASSES):
                continue
            text = transposeChordPro(s, d, text, n, acc)

        return text
        
    def OnSemitones(self, evt):
        self.UpdateToKey()
        evt.Skip()
        
    def OnFromKey(self, evt):
        self.UpdateToKey()
        evt.Skip()
        
    def OnToKey(self, evt):
        g = (self.toKey.GetSelection() - self.fromKey.GetSelection()) % 12
        if g > 7:
            g = -12 + g
        self.semitones.SetValue(g)
        evt.Skip()
