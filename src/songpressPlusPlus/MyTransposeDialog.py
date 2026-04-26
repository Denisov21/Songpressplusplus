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
    def __init__(self, parent, notations, full_text, selected_text=None):
        TransposeDialog.__init__(self, parent)
        self.notations = notations
        self.full_text = full_text
        self.selected_text = selected_text  # None if no selection

        # Use selected text for autodetect when available, otherwise full text
        detect_text = selected_text if selected_text else full_text
        self.text = detect_text  # kept for compatibility / autodetect

        fn = autodetectNotation(detect_text, notations)
        self.fk = autodetectKey(detect_text, fn)
        for n in self.notations:
            i = self.notation.Append(n.desc)
            self.notation.SetClientData(i, n)
            if n == fn:
                self.notation.SetSelection(i)

        # Checkbox: enabled only when there is an actual selection
        has_sel = bool(selected_text)
        self.selectionOnly.SetValue(has_sel)
        self.selectionOnly.Enable(has_sel)

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
        
    def _transposeBeatsTimes(self, text, s, d, n, acc):
        """Transpose chord roots inside every {beats_time: ...} directive.

        The directive has the form::

            {beats_time: DO=4 SOL=4 LA-=2 FA#=1}

        Each token before '=' is a chord root (with optional quality suffix
        like '-') that must be transposed exactly like a normal bracketed chord.
        The numeric value after '=' is left untouched.
        """
        import re as _re

        def _transpose_bt_match(m):
            content = m.group(1)          # e.g. "DO=4 SOL=4 LA-=2"
            tokens = content.split()
            out_tokens = []
            for tok in tokens:
                eq = tok.find('=')
                if eq == -1:
                    out_tokens.append(tok)
                    continue
                root_raw = tok[:eq]        # e.g. "LA-"
                value    = tok[eq:]        # e.g. "=2"
                # Wrap as a ChordPro bracket, transpose, then unwrap
                bracketed  = '[%s]' % root_raw
                transposed = transposeChordPro(s, d, bracketed, n, acc)
                # transposed is "[XY]" → extract inner text
                inner = (transposed[1:-1]
                         if (transposed.startswith('[') and transposed.endswith(']'))
                         else root_raw)
                out_tokens.append(inner + value)
            return '{beats_time: %s}' % ' '.join(out_tokens)

        pat = _re.compile(r'\{beats_time:\s*([^}]*)\}', _re.IGNORECASE)
        return pat.sub(_transpose_bt_match, text)

    def _get_params(self):
        """Return (s, d, acc, n) from the current dialog state."""
        s   = self.fromKey.GetClientData(self.fromKey.GetSelection())
        d   = self.toKey.GetClientData(self.toKey.GetSelection())
        acc = self.accidentals.GetSelection()
        i   = self.notation.GetSelection()
        n   = self.notation.GetClientData(i)
        return s, d, acc, n

    def GetTransposed(self):
        """Return the transposed text for the working scope (selection or full).

        When SelectionOnly() is True this returns only the transposed selection;
        {beats_time:} directives (which live outside the selection) are NOT
        touched here — call GetTransposedFullText() to obtain the complete
        document with both the transposed selection and the updated directives.

        When SelectionOnly() is False the whole document is returned, including
        {beats_time:} directives if the checkbox is checked.
        """
        s, d, acc, n = self._get_params()

        if self.selectionOnly.IsChecked() and self.selected_text:
            work_text = self.selected_text
        else:
            work_text = self.full_text

        if isinstance(n, _RELATIVE_NOTATION_CLASSES):
            return work_text

        result = transposeChordPro(s, d, work_text, n, acc)

        # When working on the full document, also handle {beats_time:} here.
        # When selection-only, beats_time are handled by GetTransposedFullText()
        # which applies them to the same scope as the chord transposition.
        if self.transposeBeatTime.IsChecked() and not self.SelectionOnly():
            result = self._transposeBeatsTimes(result, s, d, n, acc)

        return result

    def GetTransposedFullText(self, transposed_selection):
        """Return the complete document for a SelectionOnly transposition.

        Splices *transposed_selection* back into full_text at the position of
        the original selected_text. If transposeBeatTime is checked, {beats_time}
        directives are transposed in the same scope as the chord transposition:
        since SelectionOnly() is True, that means only inside the selection.

        Parameters
        ----------
        transposed_selection : str
            The string returned by GetTransposed() when SelectionOnly() is True.
        """
        s, d, acc, n = self._get_params()

        orig = self.selected_text or ''
        pos = self.full_text.find(orig)
        if pos == -1 or not orig:
            return self.full_text

        if isinstance(n, _RELATIVE_NOTATION_CLASSES):
            return (self.full_text[:pos]
                    + transposed_selection
                    + self.full_text[pos + len(orig):])

        # Transpose {beats_time} directives within the selection only,
        # consistent with selectionOnly scoping for chord brackets.
        if self.transposeBeatTime.IsChecked():
            transposed_selection = self._transposeBeatsTimes(
                transposed_selection, s, d, n, acc)

        return (self.full_text[:pos]
                + transposed_selection
                + self.full_text[pos + len(orig):])

    def SelectionOnly(self):
        """Return True if the result should replace only the selection."""
        return self.selectionOnly.IsChecked() and bool(self.selected_text)
        
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
