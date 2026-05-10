# -*- coding: utf-8 -*-
###############################################################
# Name:             CopyAIBeatsPrompt.py
# Purpose:    Adds the command **"Copy AI beats_time prompt"** (Ctrl+Shift+B):
#copies a ready-to-paste prompt to the clipboard for use in an AI terminal
#to add {beats_time: ...} directives from a PDF score.
# Author:         Denisov21
# Created:     2026-05-10
# Copyright:  Denisov21 
# License:     GNU GPL v2
##############################################################

"""
CopyAIBeatsPrompt.py
========================

Adds the command **"Copy AI beats_time prompt"** (Ctrl+Shift+B):
copies a ready-to-paste prompt to the clipboard for use in an AI terminal
to add {beats_time: ...} directives from a PDF score.



STRUCTURE OF THE COPIED PROMPT
--------------------------------
Add beats_time to <file.crd> using the score <file.pdf>.
The eighth note equals 1 beat. The beats_time must be written before the
chord line, example:
`{beats_time: DO=2 SOL=2 RE-=2 LA-=2}` / `[DO]Ecco[SOL]mi, [RE-]ecco[LA-]mi!`
"""

import os
import wx

_ = wx.GetTranslation


class CopyAIBeatsPromptMixin:
    """
    Mixin that adds the "Copy AI beats_time prompt" command to SongpressFrame.

    Requires self.document (path to the current .crd file) and self.frame
    to be available, as they already are in SongpressFrame.
    """

    # ------------------------------------------------------------------
    # Constants
    # ------------------------------------------------------------------

    #: Keyboard shortcut (also shown in the tooltip)
    AI_BEATS_ACCEL = u"Ctrl+Shift+B"

    #: Prompt template key for gettext. The placeholders {crd} and {pdf}
    #: are replaced at runtime with the actual file names.
    AI_BEATS_TEMPLATE_MSGID = (
        u"Add beats_time to {crd} using the score {pdf}.\n"
        u"The eighth note equals 1 beat. The beats_time must be written "
        u"before the chord line, example:\n"
        u"`{{beats_time: DO=2 SOL=2 RE-=2 LA-=2}}` / "
        u"`[DO]Ecco[SOL]mi, [RE-]ecco[LA-]mi!`"
    )

    #: Supported song file extensions (ChordPro and compatible)
    AI_BEATS_SONG_EXTENSIONS = {
        '.crd', '.cho', '.chordpro', '.chopro', '.pro', '.tab', '.sng'
    }

    # ------------------------------------------------------------------
    # Main handler
    # ------------------------------------------------------------------

    def OnCopyAIBeatsPrompt(self, evt):
        """
        Build the AI prompt and copy it to the clipboard.

        * If a song file is open, its base name is used.
        * The PDF name is assumed to be the same as the song file with a .pdf
          extension (default behaviour; the user can edit the text after
          pasting it into the AI terminal).
        * If no file is open, a warning dialog is shown.
        """
        # -- Get the current document path --------------------------------
        crd_path = getattr(self, 'document', '') or ''

        if not crd_path:
            wx.MessageBox(
                _(u"No song file is open.\n"
                  u"Please open a song file before copying the prompt."),
                _(u"Copy IA {beats_time} prompt"),
                wx.OK | wx.ICON_WARNING,
                self.frame,
            )
            return

        # -- File names (base name only, no directory) --------------------
        crd_name = os.path.basename(crd_path)
        pdf_name = os.path.splitext(crd_name)[0] + u".pdf"

        # -- Build the prompt ---------------------------------------------
        prompt = _(self.AI_BEATS_TEMPLATE_MSGID).format(
            crd=crd_name,
            pdf=pdf_name,
        )

        # -- Copy to clipboard --------------------------------------------
        if wx.TheClipboard.Open():
            wx.TheClipboard.SetData(wx.TextDataObject(prompt))
            wx.TheClipboard.Close()
            wx.MessageBox(
                _(u"Prompt copied to the clipboard!\n\n"
                  u"Paste it into the AI terminal and replace "
                  u"the PDF name if necessary."),
                _(u"Copy IA {beats_time} prompt"),
                wx.OK | wx.ICON_INFORMATION,
                self.frame,
            )
        else:
            wx.MessageBox(
                _(u"Cannot access the clipboard."),
                _(u"Error"),
                wx.OK | wx.ICON_ERROR,
                self.frame,
            )


# ======================================================================
# XML INSTRUCTIONS FOR XRC FILES
# ======================================================================
#
# -- songpress.xrc  (English) ------------------------------------------
# Paste this block AFTER the "insertDuration" item in the "insert" menu:
#
#   <object class="wxMenuItem" name="copyAIBeatsPrompt">
#     <label>Copy &amp;AI beats_time prompt</label>
#     <accel>Ctrl+Shift+B</accel>
#     <help>Copy a ready-to-paste AI prompt to add beats_time directives using a PDF score</help>
#     <bitmap>../img/beats.png</bitmap>
#   </object>
#
# -- songpress_it.xrc  (Italian) ---------------------------------------
# Paste this block AFTER the "insertDuration" item in the "insert" menu:
#
#   <object class="wxMenuItem" name="copyAIBeatsPrompt">
#     <label>Copia prompt &amp;AI per beats_time</label>
#     <accel>Ctrl+Shift+B</accel>
#     <help>Copia negli appunti il prompt per l'AI per aggiungere i beats_time usando uno spartito PDF</help>
#     <bitmap>../img/beats.png</bitmap>
#   </object>
#
# ======================================================================
