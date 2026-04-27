###############################################################
# Name:        CanzonatorDialog.py
# Purpose:     Dialogo "Canzonatore" — unisce più file ChordPro
#              in un unico file, con separatori {new_page}.
# Author:      Denisov21
# Created:     2026
# Copyright:   © 2026 Denisov21
# License:     GNU GPL v2
###############################################################

import os
import platform
import subprocess
import wx
import wx.adv

_ = wx.GetTranslation

# Estensioni supportate (stessa lista di _import_formats in SongpressFrame)
_SUPPORTED_EXT = {'.crd', '.cho', '.chordpro', '.chopro', '.pro', '.tab', '.cpm'}

# Separatore inserito tra i brani
_SONG_SEPARATOR = '\n{new_page}\n\n'


def _open_path_in_filemanager(path):
    """Apre la cartella contenente il file nel file manager del SO,
    selezionando il file se possibile."""
    try:
        if platform.system() == 'Windows':
            subprocess.Popen(['explorer', '/select,', os.path.normpath(path)])
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', '-R', path])
        else:
            subprocess.Popen(['xdg-open', os.path.dirname(path)])
    except Exception:
        pass


def _open_file_default(path):
    """Apre il file con l'applicazione predefinita del SO."""
    try:
        if platform.system() == 'Windows':
            os.startfile(path)
        elif platform.system() == 'Darwin':
            subprocess.Popen(['open', path])
        else:
            subprocess.Popen(['xdg-open', path])
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────────────
# Dialogo di completamento merge con link cliccabili
# ──────────────────────────────────────────────────────────────────────────────

class _MergeResultDialog(wx.Dialog):
    """Dialogo mostrato al termine del merge, con link cliccabili al file
    e alla cartella di destinazione."""

    def __init__(self, parent, out_path, n_merged, n_errors):
        super().__init__(
            parent,
            title=_("Canzonatore — Merge completed"),
            style=wx.DEFAULT_DIALOG_STYLE,
        )

        self._out_path = out_path

        sz = wx.BoxSizer(wx.VERTICAL)

        # ── Icona + testo principale ───────────────────────────────────
        top_row = wx.BoxSizer(wx.HORIZONTAL)
        icon = wx.StaticBitmap(
            self,
            bitmap=wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_MESSAGE_BOX, (32, 32)),
        )
        top_row.Add(icon, 0, wx.ALIGN_TOP | wx.RIGHT, 12)

        msg_sz = wx.BoxSizer(wx.VERTICAL)

        lbl_ok = wx.StaticText(
            self,
            label=_("Merge completed: %d songs merged.") % n_merged,
        )
        font_bold = lbl_ok.GetFont()
        font_bold.SetWeight(wx.FONTWEIGHT_BOLD)
        lbl_ok.SetFont(font_bold)
        msg_sz.Add(lbl_ok, 0, wx.BOTTOM, 8)

        if n_errors:
            lbl_err = wx.StaticText(
                self,
                label=_("(%d file(s) skipped due to read errors)") % n_errors,
            )
            lbl_err.SetForegroundColour(wx.Colour(180, 60, 0))
            msg_sz.Add(lbl_err, 0, wx.BOTTOM, 8)

        # ── Link al file di output ─────────────────────────────────────
        msg_sz.Add(wx.StaticText(self, label=_("Output file:")), 0, wx.BOTTOM, 2)
        self.link_file = wx.adv.HyperlinkCtrl(
            self,
            label=os.path.basename(out_path),
            url=out_path,
        )
        self.link_file.SetToolTip(_("Open the file with the default application"))
        msg_sz.Add(self.link_file, 0, wx.BOTTOM, 8)

        # ── Link alla cartella contenente il file ──────────────────────
        msg_sz.Add(wx.StaticText(self, label=_("Folder:")), 0, wx.BOTTOM, 2)
        self.link_dir = wx.adv.HyperlinkCtrl(
            self,
            label=os.path.dirname(out_path),
            url='folder://' + os.path.dirname(out_path),
        )
        self.link_dir.SetToolTip(_("Open the containing folder"))
        msg_sz.Add(self.link_dir, 0)

        top_row.Add(msg_sz, 1, wx.EXPAND)
        sz.Add(top_row, 0, wx.EXPAND | wx.ALL, 16)

        sz.Add(wx.StaticLine(self), 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 8)

        # ── Bottone OK ─────────────────────────────────────────────────
        btn_ok = wx.Button(self, wx.ID_OK, _("OK"))
        btn_ok.SetDefault()
        btn_sz2 = wx.BoxSizer(wx.HORIZONTAL)
        btn_sz2.AddStretchSpacer()
        btn_sz2.Add(btn_ok, 0)
        sz.Add(btn_sz2, 0, wx.EXPAND | wx.ALL, 10)

        self.SetSizerAndFit(sz)
        self.CentreOnParent()

        self.link_file.Bind(wx.adv.EVT_HYPERLINK, self._OnLinkFile)
        self.link_dir.Bind(wx.adv.EVT_HYPERLINK,  self._OnLinkDir)

    def _OnLinkFile(self, evt):
        _open_file_default(self._out_path)

    def _OnLinkDir(self, evt):
        _open_path_in_filemanager(self._out_path)


# ──────────────────────────────────────────────────────────────────────────────
# Pannello lista file con pulsanti di gestione
# ──────────────────────────────────────────────────────────────────────────────

class _FileListPanel(wx.Panel):
    """Lista di file con riordino e pulsanti Aggiungi/Rimuovi/Su/Giù.
    Doppio clic (o Invio) su una riga apre il file nell'editor o
    con il programma predefinito del SO."""

    def __init__(self, parent):
        super().__init__(parent)

        self._paths          = []   # lista ordinata dei percorsi assoluti
        self._open_callback  = None # callback(path) per aprire nell'editor

        # ── Lista ──────────────────────────────────────────────────────
        self.lc = wx.ListCtrl(
            self,
            style=wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.BORDER_SUNKEN,
        )
        self.lc.InsertColumn(0, _("File"),   width=320)
        self.lc.InsertColumn(1, _("Folder"), width=220)

        # ── Pulsanti colonna destra ────────────────────────────────────
        self.btn_add     = wx.Button(self, label=_("Add files…"))
        self.btn_add_dir = wx.Button(self, label=_("Add folder…"))
        self.btn_remove  = wx.Button(self, label=_("Remove"))
        self.btn_up      = wx.Button(self, label=_("▲ Up"))
        self.btn_down    = wx.Button(self, label=_("▼ Down"))
        self.btn_clear   = wx.Button(self, label=_("Clear all"))

        btn_sz = wx.BoxSizer(wx.VERTICAL)
        for btn in (self.btn_add, self.btn_add_dir,
                    self.btn_remove, self.btn_up, self.btn_down,
                    self.btn_clear):
            btn_sz.Add(btn, 0, wx.EXPAND | wx.BOTTOM, 4)

        main_sz = wx.BoxSizer(wx.HORIZONTAL)
        main_sz.Add(self.lc,  1, wx.EXPAND | wx.RIGHT, 6)
        main_sz.Add(btn_sz,   0, wx.EXPAND)
        self.SetSizer(main_sz)

        # ── Bind ───────────────────────────────────────────────────────
        self.btn_add.Bind(wx.EVT_BUTTON,     self._OnAdd)
        self.btn_add_dir.Bind(wx.EVT_BUTTON, self._OnAddDir)
        self.btn_remove.Bind(wx.EVT_BUTTON,  self._OnRemove)
        self.btn_up.Bind(wx.EVT_BUTTON,      self._OnUp)
        self.btn_down.Bind(wx.EVT_BUTTON,    self._OnDown)
        self.btn_clear.Bind(wx.EVT_BUTTON,   self._OnClear)
        self.lc.Bind(wx.EVT_LIST_ITEM_SELECTED,   self._UpdateButtons)
        self.lc.Bind(wx.EVT_LIST_ITEM_DESELECTED, self._UpdateButtons)
        # Doppio clic / Invio → apri il file
        self.lc.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self._OnItemActivated)
        self._UpdateButtons()

    # ── public API ─────────────────────────────────────────────────────

    def set_open_callback(self, cb):
        """Registra la funzione(path) per aprire un file nell'editor."""
        self._open_callback = cb

    def GetPaths(self):
        return list(self._paths)

    # ── helpers ────────────────────────────────────────────────────────

    def _is_supported(self, path):
        return os.path.splitext(path)[1].lower() in _SUPPORTED_EXT

    def _rebuild_list(self):
        self.lc.DeleteAllItems()
        for p in self._paths:
            idx = self.lc.InsertItem(self.lc.GetItemCount(), os.path.basename(p))
            self.lc.SetItem(idx, 1, os.path.dirname(p))

    def _selected_index(self):
        return self.lc.GetFirstSelected()

    def _UpdateButtons(self, evt=None):
        sel     = self._selected_index()
        n       = len(self._paths)
        has_sel = (sel != -1)
        self.btn_remove.Enable(has_sel)
        self.btn_up.Enable(has_sel and sel > 0)
        self.btn_down.Enable(has_sel and sel < n - 1)
        self.btn_clear.Enable(n > 0)
        if evt:
            evt.Skip()

    def _add_paths(self, paths):
        added   = 0
        already = set(self._paths)
        for p in paths:
            if self._is_supported(p) and p not in already:
                self._paths.append(p)
                already.add(p)
                added += 1
        if added:
            self._rebuild_list()
            self._UpdateButtons()
        return added

    # ── doppio clic ────────────────────────────────────────────────────

    def _OnItemActivated(self, evt):
        """Doppio clic o Invio: apre il file nell'editor (se c'è il callback)
        o con il programma predefinito del SO."""
        idx = evt.GetIndex()
        if idx < 0 or idx >= len(self._paths):
            return
        path = self._paths[idx]
        if self._open_callback:
            self._open_callback(path)
        else:
            _open_file_default(path)

    # ── event handlers pulsanti ────────────────────────────────────────

    def _OnAdd(self, evt):
        ext_list = ';'.join('*.' + e.lstrip('.') for e in sorted(_SUPPORTED_EXT))
        wildcard = (
            _("All supported files") + ' (%s)|%s' % (ext_list, ext_list) +
            '|' + _("All files") + ' (*.*)|*.*'
        )
        with wx.FileDialog(
            self,
            _("Select files to add"),
            style=wx.FD_OPEN | wx.FD_MULTIPLE | wx.FD_FILE_MUST_EXIST,
            wildcard=wildcard,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                paths   = sorted(dlg.GetPaths())
                skipped = len(paths) - self._add_paths(paths)
                if skipped:
                    wx.MessageBox(
                        _("%d file(s) skipped (unsupported format or already in list).") % skipped,
                        _("Canzonatore"),
                        wx.OK | wx.ICON_INFORMATION,
                        self,
                    )

    def _OnAddDir(self, evt):
        with wx.DirDialog(
            self,
            _("Select folder"),
            style=wx.DD_DEFAULT_STYLE | wx.DD_DIR_MUST_EXIST,
        ) as dlg:
            if dlg.ShowModal() == wx.ID_OK:
                folder = dlg.GetPath()
                try:
                    names = sorted(os.listdir(folder))
                except OSError as e:
                    wx.MessageBox(str(e), _("Canzonatore"), wx.OK | wx.ICON_ERROR, self)
                    return
                paths = [
                    os.path.join(folder, n) for n in names
                    if os.path.isfile(os.path.join(folder, n)) and self._is_supported(n)
                ]
                if self._add_paths(paths) == 0:
                    wx.MessageBox(
                        _("No supported files found in the selected folder."),
                        _("Canzonatore"),
                        wx.OK | wx.ICON_INFORMATION,
                        self,
                    )

    def _OnRemove(self, evt):
        sel = self._selected_index()
        if sel == -1:
            return
        del self._paths[sel]
        self._rebuild_list()
        n = len(self._paths)
        if n > 0:
            self.lc.SetItemState(
                min(sel, n - 1), wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED
            )
        self._UpdateButtons()

    def _OnUp(self, evt):
        sel = self._selected_index()
        if sel <= 0:
            return
        self._paths[sel - 1], self._paths[sel] = self._paths[sel], self._paths[sel - 1]
        self._rebuild_list()
        self.lc.SetItemState(sel - 1, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        self._UpdateButtons()

    def _OnDown(self, evt):
        sel = self._selected_index()
        if sel == -1 or sel >= len(self._paths) - 1:
            return
        self._paths[sel], self._paths[sel + 1] = self._paths[sel + 1], self._paths[sel]
        self._rebuild_list()
        self.lc.SetItemState(sel + 1, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)
        self._UpdateButtons()

    def _OnClear(self, evt):
        if not self._paths:
            return
        if wx.MessageBox(
            _("Remove all files from the list?"),
            _("Canzonatore"),
            wx.YES_NO | wx.ICON_QUESTION,
            self,
        ) == wx.YES:
            self._paths.clear()
            self._rebuild_list()
            self._UpdateButtons()


# ──────────────────────────────────────────────────────────────────────────────
# Dialogo principale
# ──────────────────────────────────────────────────────────────────────────────

class CanzonatorDialog(wx.Dialog):
    """
    Dialogo per creare un "canzonatore": unisce più file ChordPro in uno solo.

    Opzioni:
      - Separatore tra brani: {new_page} (default) oppure riga vuota
      - Encoding output: UTF-8 (default) o latin-1
      - File di destinazione scelto dall'utente
    """

    def __init__(self, parent, title=None):
        if title is None:
            title = _("Canzonatore — Merge songs")
        super().__init__(
            parent,
            title=title,
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER,
        )

        outer = wx.BoxSizer(wx.VERTICAL)

        # ── Lista file ─────────────────────────────────────────────────
        lbl_list = wx.StaticText(
            self,
            label=_("Files to merge (order = order in output) — double-click to open:"),
        )
        outer.Add(lbl_list, 0, wx.LEFT | wx.TOP | wx.RIGHT, 10)

        self.file_panel = _FileListPanel(self)
        outer.Add(self.file_panel, 1, wx.EXPAND | wx.ALL, 10)

        # ── Opzioni ────────────────────────────────────────────────────
        opt_box = wx.StaticBoxSizer(
            wx.StaticBox(self, label=_("Options")), wx.VERTICAL
        )

        sep_row = wx.BoxSizer(wx.HORIZONTAL)
        sep_row.Add(
            wx.StaticText(self, label=_("Song separator:")),
            0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8,
        )
        self.rb_newpage = wx.RadioButton(self, label=_("{new_page}  (page break)"), style=wx.RB_GROUP)
        self.rb_blank   = wx.RadioButton(self, label=_("Blank line"))
        self.rb_newpage.SetValue(True)
        sep_row.Add(self.rb_newpage, 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        sep_row.Add(self.rb_blank,   0, wx.ALIGN_CENTER_VERTICAL)
        opt_box.Add(sep_row, 0, wx.ALL, 6)

        enc_row = wx.BoxSizer(wx.HORIZONTAL)
        enc_row.Add(
            wx.StaticText(self, label=_("Output encoding:")),
            0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 8,
        )
        self.rb_utf8   = wx.RadioButton(self, label="UTF-8", style=wx.RB_GROUP)
        self.rb_latin1 = wx.RadioButton(self, label="Latin-1 (ISO-8859-1)")
        self.rb_utf8.SetValue(True)
        enc_row.Add(self.rb_utf8,   0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 12)
        enc_row.Add(self.rb_latin1, 0, wx.ALIGN_CENTER_VERTICAL)
        opt_box.Add(enc_row, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        self.cb_open = wx.CheckBox(self, label=_("Open the merged file in the editor"))
        self.cb_open.SetValue(True)
        opt_box.Add(self.cb_open, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 6)

        outer.Add(opt_box, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        # ── Bottoni ────────────────────────────────────────────────────
        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_merge  = wx.Button(self, label=_("Merge…"))
        self.btn_cancel = wx.Button(self, wx.ID_CANCEL, _("Close"))
        self.btn_merge.SetDefault()
        btn_row.AddStretchSpacer()
        btn_row.Add(self.btn_merge,  0, wx.RIGHT, 8)
        btn_row.Add(self.btn_cancel, 0)
        outer.Add(btn_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 10)

        self.SetSizerAndFit(outer)
        self.SetMinSize(wx.Size(620, 440))
        self.SetSize(wx.Size(700, 520))
        self.CentreOnParent()

        self.btn_merge.Bind(wx.EVT_BUTTON,  self._OnMerge)
        self.btn_cancel.Bind(wx.EVT_BUTTON, self._OnClose)
        self.Bind(wx.EVT_CLOSE, self._OnClose)

        self._open_callback = None

    def set_open_callback(self, cb):
        """Registra la funzione da chiamare per aprire il file nell'editor."""
        self._open_callback = cb
        # Propaga al pannello lista per il doppio clic sui file in ingresso
        self.file_panel.set_open_callback(cb)

    # ── logica di merge ────────────────────────────────────────────────

    def _OnMerge(self, evt):
        paths = self.file_panel.GetPaths()
        if not paths:
            wx.MessageBox(
                _("Add at least one file to merge."),
                _("Canzonatore"),
                wx.OK | wx.ICON_INFORMATION,
                self,
            )
            return

        ext_list = ';'.join('*.' + e.lstrip('.') for e in sorted(_SUPPORTED_EXT))
        wildcard = (
            _("ChordPro files") + ' (*.crd)|*.crd' +
            '|' + _("All supported files") + ' (%s)|%s' % (ext_list, ext_list) +
            '|' + _("All files") + ' (*.*)|*.*'
        )
        with wx.FileDialog(
            self,
            _("Save merged file as…"),
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            wildcard=wildcard,
        ) as dlg:
            if dlg.ShowModal() != wx.ID_OK:
                return
            out_path = dlg.GetPath()
            if not os.path.splitext(out_path)[1]:
                out_path += '.crd'

        encoding  = 'utf-8' if self.rb_utf8.GetValue() else 'latin-1'
        separator = _SONG_SEPARATOR if self.rb_newpage.GetValue() else '\n\n'

        parts  = []
        errors = []
        for p in paths:
            try:
                for enc in ('utf-8-sig', 'utf-8', 'latin-1'):
                    try:
                        with open(p, 'r', encoding=enc) as f:
                            content = f.read()
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise UnicodeDecodeError('all', b'', 0, 1, 'Unable to decode')
                parts.append(content.rstrip())
            except Exception as e:
                errors.append('%s: %s' % (os.path.basename(p), e))

        if errors:
            wx.MessageBox(
                _("Errors reading the following files:\n\n") + '\n'.join(errors),
                _("Canzonatore"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            if not parts:
                return

        try:
            with open(out_path, 'w', encoding=encoding, errors='replace') as f:
                f.write(separator.join(parts) + '\n')
        except Exception as e:
            wx.MessageBox(
                _("Error writing the merged file:\n\n") + str(e),
                _("Canzonatore"),
                wx.OK | wx.ICON_ERROR,
                self,
            )
            return

        # ── Dialogo di completamento con link cliccabili ───────────────
        result_dlg = _MergeResultDialog(self, out_path, len(parts), len(errors))
        result_dlg.ShowModal()
        result_dlg.Destroy()

        # Apri nell'editor se richiesto
        if self.cb_open.GetValue() and self._open_callback:
            self._open_callback(out_path)

    def _OnClose(self, evt):
        self.Destroy()


# ──────────────────────────────────────────────────────────────────────────────
# Entry point chiamato da SongpressFrame
# ──────────────────────────────────────────────────────────────────────────────

def open_canzonatore(owner, parent_frame):
    """
    Apre il dialogo Canzonatore.

    :param owner:        istanza di SongpressFrame (per aprire file nell'editor)
    :param parent_frame: wx.Frame genitore
    """
    dlg = CanzonatorDialog(parent_frame)

    def _open_in_editor(path):
        try:
            if not owner.AskSaveModified():
                return
            owner.Open(path)
        except Exception as e:
            wx.MessageBox(str(e), _("Canzonatore"), wx.OK | wx.ICON_ERROR, parent_frame)

    dlg.set_open_callback(_open_in_editor)
    dlg.Show()
