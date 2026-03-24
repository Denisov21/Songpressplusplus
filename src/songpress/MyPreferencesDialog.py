###############################################################
# Name:             PreferencesDialog.py
# Purpose:     Allow user to set preferences
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2009-10-02
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
##############################################################

import wx

from . import i18n
from .PreferencesDialog import PreferencesDialog
from .MyDecoSlider import MyDecoSlider
from .Transpose import *
from .Globals import glb


_ = wx.GetTranslation


class MyPreferencesDialog(PreferencesDialog):
    def __init__(self, parent, preferences, easyChords, on_apply=None):
        self.pref = preferences
        self.frame = self
        PreferencesDialog.__init__(self, parent)

        self._pinned = False
        self._on_apply = on_apply  # callback chiamato ad ogni OK con pin attivo
        self.easyChords = easyChords
        self.clearRecentFiles = False

        self.fontCB.Bind(wx.EVT_TEXT_ENTER, self.OnFontSelected, self.fontCB)
        self.fontCB.Bind(wx.EVT_COMBOBOX, self.OnFontSelected, self.fontCB)

        previewSong = _("{t:My Bonnie}\n\nMy [D]Bonnie lies [G]over the [D]ocean\noh [G]bring back my [A]Bonnie to [D]me!\n\n{soc}\n[D]Bring back, [E-]bring back,\n[A]bring back my Bonnie to [D]me!\n{eoc}")
        self.editor.SetText(previewSong)
        self.editor.SetFont(self.pref.editorFace, self.pref.editorSize)
        self.editor.SetReadOnly(True)
        self.autoRemoveBlankLines.SetValue(self.pref.autoAdjustSpuriousLines)
        self.autoTab2Chordpro.SetValue(self.pref.autoAdjustTab2Chordpro)
        self.autoAdjustEasyKey.SetValue(self.pref.autoAdjustEasyKey)
        if self.pref.locale is None:
            lang = i18n.getLang()
        else:
            lang = self.pref.locale
        import os as _os
        def _make_flag_bmp(lang_code):
            try:
                _path = glb.AddPath('img/flags/%s.png' % lang_code)
                if not _os.path.isfile(_path):
                    return wx.NullBitmap
                _img = wx.Image(_path, wx.BITMAP_TYPE_PNG)
                if not _img.IsOk():
                    return wx.NullBitmap
                _img = _img.Scale(20, 14, wx.IMAGE_QUALITY_HIGH)
                return wx.Bitmap(_img)
            except Exception:
                return wx.NullBitmap
        for l in glb.languages:
            _bmp = _make_flag_bmp(l)
            i = self.langCh.Append(glb.languages[l], _bmp)
            self.langCh.SetClientData(i, l)
            if lang == l:
                self.langCh.SetSelection(i)
        exts = ["crd", "pro", "chopro", "chordpro", "cho"]
        i = 0
        for e in exts:
            self.extension.Append(e)
            if e == self.pref.defaultExtension:
                self.extension.SetSelection(i)
            i += 1

        # Default notation
        for n in self.pref.notations:
            i = self.notationCh.Append(n.desc)
            self.notationCh.SetClientData(i, n.id)
        self.notationCh.SetSelection(0)

        # Easy chords
        simplifyGrid = wx.FlexGridSizer(len(easyChords), 2, 0, 0)
        simplifyGrid.AddGrowableCol(1, 1)
        self.simplifyPanel.SetSizer(simplifyGrid)
        self.simplifyPanel.Layout()

        self.decoSliders = {}
        for k in easyChordsOrder:
            simplifyGrid.Add(wx.StaticText(self.simplifyPanel, wx.ID_ANY, getEasyChordsDescription(easyChords[k]), wx.DefaultPosition, wx.DefaultSize, 0), 0, wx.ALL | wx.ALIGN_CENTER_HORIZONTAL, 5)
            ds = MyDecoSlider(self.simplifyPanel)
            self.decoSliders[k] = ds
            ds.slider.SetValue(self.pref.GetEasyChordsGroup(k))
            simplifyGrid.Add(ds, 1, wx.EXPAND, 5)

        simplifyGrid.FitInside(self.simplifyPanel)

        # Format tab - inizializza con i valori correnti delle preferenze
        self.titleLineWidthSpin.SetValue(self.pref.titleLineWidth)
        self.verseBoxWidthSpin.SetValue(self.pref.verseBoxWidth)

        # Context menu visibility — valori già caricati da Preferences.Load()
        self.cmUndo.SetValue(self.pref.cmUndo)
        self.cmRedo.SetValue(self.pref.cmRedo)
        self.cmCut.SetValue(self.pref.cmCut)
        self.cmCopy.SetValue(self.pref.cmCopy)
        self.cmPaste.SetValue(self.pref.cmPaste)
        self.cmDelete.SetValue(self.pref.cmDelete)
        self.cmPasteChords.SetValue(self.pref.cmPasteChords)
        self.cmPropagateVerseChords.SetValue(getattr(self.pref, 'cmPropagateVerseChords', True))
        self.cmPropagateChorusChords.SetValue(getattr(self.pref, 'cmPropagateChorusChords', True))
        self.cmCopyTextOnly.SetValue(self.pref.cmCopyTextOnly)
        self.cmSelectAll.SetValue(self.pref.cmSelectAll)

        # Klavier highlight colour
        default_hex = getattr(self.pref, 'klavierHighlightHex', '#D23C3C')
        self.klavierHexCtrl.SetValue(default_hex)
        self.klavierColourSwatch.SetBackgroundColour(self._hex_to_colour(default_hex))

        # Editor background colour
        bg_hex = getattr(self.pref, 'editorBgHex', '#FFFFFF')
        if hasattr(self, 'editorBgHexCtrl'):
            self.editorBgHexCtrl.SetValue(bg_hex)
            self.editorBgSwatch.SetBackgroundColour(self._hex_to_colour(bg_hex))
            self._applyEditorBg(bg_hex)

        # Selection colour
        sel_hex = getattr(self.pref, 'selColourHex', '#C0C0C0')
        if hasattr(self, 'selColourHexCtrl'):
            self.selColourHexCtrl.SetValue(sel_hex)
            self.selColourSwatch.SetBackgroundColour(self._hex_to_colour(sel_hex))
            self._applySelColour(sel_hex)

        # Show print preview
        self.showPrintPreviewCB.SetValue(getattr(self.pref, 'showPrintPreview', True))

        # Multi-cursor
        self.multiCursorCB.SetValue(getattr(self.pref, 'multiCursor', False))

        # Salvataggio geometria finestra
        self.saveWindowGeometryCB.SetValue(getattr(self.pref, 'saveWindowGeometry', True))

        # Dimensione icone tempo
        sz = getattr(self.pref, 'tempoIconSize', 24)
        self.tempoIconSize16.SetValue(sz == 16)
        self.tempoIconSize24.SetValue(sz == 24)
        self.tempoIconSize32.SetValue(sz == 32)

        # File associations (solo Windows)
        if self._fileAssocAvailable:
            import sys as _sys
            exe = _sys.executable if not getattr(_sys, 'frozen', False) else _sys.executable
            for ext, cb in self._fileAssocCBs.items():
                cb.SetValue(self._IsExtAssociated(ext, exe))

    def _hex_to_colour(self, hex_str):
        try:
            h = hex_str.strip().lstrip('#')
            if len(h) == 6:
                return wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
        except Exception:
            pass
        return wx.Colour(255, 255, 255)

    def _applyEditorBg(self, hex_str):
        """Applica il colore di sfondo all'editor di anteprima nelle preferenze."""
        self.editor.SetBgColour(hex_str)

    def _applySelColour(self, hex_str):
        """Applica il colore di selezione all'editor di anteprima nelle preferenze."""
        self.editor.SetSelColour(hex_str)

    def _colour_to_hex(self, colour):
        return '#{:02X}{:02X}{:02X}'.format(colour.Red(), colour.Green(), colour.Blue())

    def _apply_custom_colours(self, data, pref_attr):
        """Carica i colori personalizzati salvati in pref nel ColourData."""
        colours = getattr(self.pref, pref_attr, [])
        for i, hex_str in enumerate(colours[:16]):
            try:
                h = hex_str.strip().lstrip('#')
                if len(h) == 6:
                    c = wx.Colour(int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
                    data.SetCustomColour(i, c)
            except Exception:
                pass

    def _read_custom_colours(self, data, pref_attr):
        """Legge i 16 colori personalizzati dal ColourData e li salva in pref."""
        setattr(self.pref, pref_attr, [
            self._colour_to_hex(data.GetCustomColour(i)) for i in range(16)
        ])

    def OnKlavierHexChanged(self, evt):
        c = self._hex_to_colour(self.klavierHexCtrl.GetValue())
        self.klavierColourSwatch.SetBackgroundColour(c)
        self.klavierColourSwatch.Refresh()
        evt.Skip()

    def OnKlavierPickColour(self, evt):
        current = self._hex_to_colour(self.klavierHexCtrl.GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        self._apply_custom_colours(data, 'customColoursKlavier')
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            self._read_custom_colours(result_data, 'customColoursKlavier')
            self.klavierHexCtrl.SetValue(self._colour_to_hex(chosen))
            self.klavierColourSwatch.SetBackgroundColour(chosen)
            self.klavierColourSwatch.Refresh()
        dlg.Destroy()

    def OnEditorBgHexChanged(self, evt):
        hex_val = self.editorBgHexCtrl.GetValue()
        c = self._hex_to_colour(hex_val)
        self.editorBgSwatch.SetBackgroundColour(c)
        self.editorBgSwatch.Refresh()
        self._applyEditorBg(hex_val)
        evt.Skip()

    def OnSelColourHexChanged(self, evt):
        hex_val = self.selColourHexCtrl.GetValue()
        c = self._hex_to_colour(hex_val)
        self.selColourSwatch.SetBackgroundColour(c)
        self.selColourSwatch.Refresh()
        self._applySelColour(hex_val)
        evt.Skip()

    def OnSelColourPickColour(self, evt):
        current = self._hex_to_colour(self.selColourHexCtrl.GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        self._apply_custom_colours(data, 'customColoursSelColour')
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            hex_val = self._colour_to_hex(chosen)
            self._read_custom_colours(result_data, 'customColoursSelColour')
            self.selColourHexCtrl.SetValue(hex_val)
            self.selColourSwatch.SetBackgroundColour(chosen)
            self.selColourSwatch.Refresh()
            self._applySelColour(hex_val)
        dlg.Destroy()

    def OnEditorBgPickColour(self, evt):
        current = self._hex_to_colour(self.editorBgHexCtrl.GetValue())
        data = wx.ColourData()
        data.SetColour(current)
        data.SetChooseFull(True)
        self._apply_custom_colours(data, 'customColoursEditorBg')
        dlg = wx.ColourDialog(self, data)
        if dlg.ShowModal() == wx.ID_OK:
            result_data = dlg.GetColourData()
            chosen = result_data.GetColour()
            hex_val = self._colour_to_hex(chosen)
            self._read_custom_colours(result_data, 'customColoursEditorBg')
            self.editorBgHexCtrl.SetValue(hex_val)
            self.editorBgSwatch.SetBackgroundColour(chosen)
            self.editorBgSwatch.Refresh()
            self._applyEditorBg(hex_val)
        dlg.Destroy()

    def OnClearRecentFiles(self, evt):
        self.clearRecentFiles = True
        self.clearRecentFilesBtn.Disable()
        evt.Skip()

    def OnFontSelected(self, evt):
        f, s = self.GetFont()
        self.editor.SetFont(f, s)
        evt.Skip()

    def GetFont(self):
        face = self.fontCB.GetValue()
        try:
            s = int(self.sizeCB.GetValue())
        except:
            s = 12
        return (face, s)

    def GetLanguage(self):
        return self.langCh.GetClientData(self.langCh.GetSelection())

    def GetNotation(self):
        return self.notationCh.GetClientData(self.notationCh.GetSelection())

    # ------------------------------------------------------------------
    # File associations (Windows e Linux)
    # ------------------------------------------------------------------

    def _GetExePath(self):
        """Restituisce il percorso dell'eseguibile di Songpress++."""
        import sys as _sys
        return _sys.executable

    # ---- Windows ----

    def _GetLaunchCmd(self, exe):
        """Restituisce la stringa comando per aprire un file con Songpress++ (Windows)."""
        import sys as _sys
        import os as _os
        if getattr(_sys, 'frozen', False):
            return '"{}" "%1"'.format(exe)
        pkg_dir  = _os.path.dirname(_os.path.abspath(__file__))
        src_dir  = _os.path.dirname(pkg_dir)
        root_dir = _os.path.dirname(src_dir)
        main_py  = _os.path.join(root_dir, 'main.py')
        if not _os.path.isfile(main_py):
            main_py = _os.path.join(src_dir, 'main.py')
            root_dir = src_dir
        launcher = self._EnsureWinLauncher(root_dir, main_py)
        pythonw = _os.path.join(_os.path.dirname(exe), 'pythonw.exe')
        if not _os.path.isfile(pythonw):
            pythonw = exe
        return '"{}" "{}" "%1"'.format(pythonw, launcher)

    def _EnsureWinLauncher(self, root_dir, main_py):
        """Crea/aggiorna lo script launcher .pyw nella cartella dati dell'app (Windows)."""
        import os as _os
        launcher_dir = _os.path.join(_os.path.expanduser('~'), 'AppData', 'Local',
                                     'Songpress', 'launcher')
        _os.makedirs(launcher_dir, exist_ok=True)
        launcher_path = _os.path.join(launcher_dir, 'songpress_open.pyw')
        script = (
            'import sys, os\n'
            'sys.path.insert(0, {root!r})\n'
            'if len(sys.argv) > 1:\n'
            '    sys.argv = [sys.argv[0]] + sys.argv[1:]\n'
            'exec(open({main!r}, encoding="utf-8").read())\n'
        ).format(root=root_dir, main=main_py)
        with open(launcher_path, 'w', encoding='utf-8') as f:
            f.write(script)
        return launcher_path

    def _IsExtAssociated(self, ext, exe):
        """Controlla se l'estensione è associata a Songpress++."""
        import platform as _platform
        if _platform.system() == 'Windows':
            return self._IsExtAssociatedWin(ext)
        elif _platform.system() == 'Linux':
            return self._IsExtAssociatedLinux(ext)
        return False

    def _IsExtAssociatedWin(self, ext):
        """Controlla l'associazione in HKCU (Windows).
        Verifica solo che il ProgID punti al nostro — non controlla il percorso exe.
        """
        try:
            import winreg
            prog_id = 'Songpress.{}'.format(ext)
            key_path = r'Software\Classes\.{}'.format(ext)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as k:
                current = winreg.QueryValue(k, '')
            return current == prog_id
        except Exception:
            return False

    def _AssociateExt(self, ext, exe):
        """Associa l'estensione a Songpress++."""
        import platform as _platform
        if _platform.system() == 'Windows':
            self._AssociateExtWin(ext, exe)
        elif _platform.system() == 'Linux':
            self._AssociateExtLinux(ext, exe)

    def _GetWinAppExeName(self):
        """Restituisce il nome exe simbolico usato per Software\\Classes\\Applications\\."""
        import sys as _sys
        import os as _os
        if getattr(_sys, 'frozen', False):
            return _os.path.basename(_sys.executable)
        # In modalità sviluppo usiamo sempre un nome fisso e riconoscibile
        return 'songpress++.exe'

    def _GetWinWrapperCmd(self, exe):
        """In modalità sviluppo crea un wrapper .bat con nome fisso e lo restituisce.
        Win 11 abbina Applications\\<exe> al comando tramite il nome dell'exe nel path.
        """
        import sys as _sys
        import os as _os
        if getattr(_sys, 'frozen', False):
            return '"{}" "%1"'.format(exe)
        # Costruisci il comando reale (pythonw + launcher)
        pkg_dir  = _os.path.dirname(_os.path.abspath(__file__))
        src_dir  = _os.path.dirname(pkg_dir)
        root_dir = _os.path.dirname(src_dir)
        main_py  = _os.path.join(root_dir, 'main.py')
        if not _os.path.isfile(main_py):
            main_py = _os.path.join(src_dir, 'main.py')
            root_dir = src_dir
        launcher = self._EnsureWinLauncher(root_dir, main_py)
        pythonw = _os.path.join(_os.path.dirname(exe), 'pythonw.exe')
        if not _os.path.isfile(pythonw):
            pythonw = exe
        real_cmd = '"{}" "{}" "%1"'.format(pythonw, launcher)
        # Crea un wrapper .bat con nome fisso "songpress++.exe" (come .bat)
        # ma registralo come se fosse l'exe — Win 11 usa il nome nel path del comando
        bat_dir = _os.path.join(_os.path.expanduser('~'), 'AppData', 'Local',
                                'Songpress', 'launcher')
        _os.makedirs(bat_dir, exist_ok=True)
        bat_path = _os.path.join(bat_dir, 'songpress++.bat')
        bat_content = '@echo off\n{}\n'.format(
            real_cmd.replace('%1', '%*')
        )
        with open(bat_path, 'w', encoding='utf-8') as f:
            f.write(bat_content)
        # Il comando registrato nel registro punta al .bat
        return '"{}" "%1"'.format(bat_path)

    def _AssociateExtWin(self, ext, exe):
        """Associa l'estensione a Songpress++ in HKCU (compatibile Win 11)."""
        import winreg
        import os as _os
        prog_id  = 'Songpress.{}'.format(ext)
        app_name = self._GetWinAppExeName()          # nome fisso per Applications\
        cmd      = self._GetLaunchCmd(exe)           # comando nel ProgID
        app_cmd  = self._GetWinWrapperCmd(exe)       # comando in Applications\ (con wrapper)
        ico_path = _os.path.normpath(glb.AddPath('img/songpress++.ico'))

        # 1. ProgID: descrizione, DefaultIcon, shell\open (MUIVerb+Icon), command
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'Software\Classes\{}'.format(prog_id)) as k:
            winreg.SetValue(k, '', winreg.REG_SZ, 'Songpress++ {} file'.format(ext.upper()))
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                  r'Software\Classes\{}\DefaultIcon'.format(prog_id)) as k:
                winreg.SetValue(k, '', winreg.REG_SZ, '{},0'.format(ico_path))
        except Exception:
            pass
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'Software\Classes\{}\shell\open'.format(prog_id)) as k:
            winreg.SetValueEx(k, 'MUIVerb', 0, winreg.REG_SZ, 'Songpress++')
            winreg.SetValueEx(k, 'Icon', 0, winreg.REG_SZ, ico_path)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'Software\Classes\{}\shell\open\command'.format(prog_id)) as k:
            winreg.SetValue(k, '', winreg.REG_SZ, cmd)

        # 2. Applications\<app_name>: FriendlyAppName, DefaultIcon, command, SupportedTypes
        #    Questa chiave è ciò che Win 11 usa per mostrare icona+nome in "Apri con"
        app_key = r'Software\Classes\Applications\{}'.format(app_name)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, app_key) as k:
            winreg.SetValueEx(k, 'FriendlyAppName', 0, winreg.REG_SZ, 'Songpress++')
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                  r'{}\DefaultIcon'.format(app_key)) as k:
                winreg.SetValue(k, '', winreg.REG_SZ, '{},0'.format(ico_path))
        except Exception:
            pass
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'{}\shell\open\command'.format(app_key)) as k:
            winreg.SetValue(k, '', winreg.REG_SZ, app_cmd)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'{}\SupportedTypes'.format(app_key)) as k:
            for s_ext in ["crd", "cho", "chordpro", "chopro", "pro", "tab"]:
                winreg.SetValueEx(k, '.{}'.format(s_ext), 0, winreg.REG_SZ, '')

        # 3. OpenWithList: collega l'app_name all'estensione
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'Software\Classes\.{}\OpenWithList\{}'.format(ext, app_name)) as k:
            pass

        # 4. Default dell'estensione → nostro ProgID
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'Software\Classes\.{}'.format(ext)) as k:
            winreg.SetValue(k, '', winreg.REG_SZ, prog_id)

        # 5. OpenWithProgids
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                              r'Software\Classes\.{}\OpenWithProgids'.format(ext)) as k:
            winreg.SetValueEx(k, prog_id, 0, winreg.REG_NONE, b'')

        # 6. Explorer FileExts OpenWithProgids (Win 10/11)
        try:
            uc_path = r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.{}\UserChoice'.format(ext)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, uc_path,
                                access=winreg.KEY_READ) as k:
                current_prog = winreg.QueryValueEx(k, 'ProgId')[0]
        except Exception:
            current_prog = None
        if current_prog != prog_id:
            try:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER,
                                      r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.{}\OpenWithProgids'.format(ext)) as k:
                    winreg.SetValueEx(k, prog_id, 0, winreg.REG_NONE, b'')
            except Exception:
                pass

    def _UnassociateExt(self, ext):
        """Rimuove l'associazione Songpress++."""
        import platform as _platform
        if _platform.system() == 'Windows':
            self._UnassociateExtWin(ext)
        elif _platform.system() == 'Linux':
            self._UnassociateExtLinux(ext)

    def _UnassociateExtWin(self, ext):
        """Rimuove completamente l'associazione Songpress++ per l'estensione in HKCU."""
        import winreg
        prog_id  = 'Songpress.{}'.format(ext)
        app_name = self._GetWinAppExeName()

        # 1. Rimuovi il valore default dell'estensione (solo se è il nostro ProgID)
        try:
            key_path = r'Software\Classes\.{}'.format(ext)
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path,
                                access=winreg.KEY_READ | winreg.KEY_SET_VALUE) as k:
                current = winreg.QueryValue(k, '')
                if current == prog_id:
                    winreg.DeleteValue(k, '')
        except Exception:
            pass

        # 2. Rimuovi da OpenWithProgids e OpenWithList
        for owp_path in [
            r'Software\Classes\.{}\OpenWithProgids'.format(ext),
            r'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.{}\OpenWithProgids'.format(ext),
        ]:
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, owp_path,
                                    access=winreg.KEY_SET_VALUE) as k:
                    winreg.DeleteValue(k, prog_id)
            except Exception:
                pass
        try:
            self._DeleteRegKeyRecursive(
                winreg.HKEY_CURRENT_USER,
                r'Software\Classes\.{}\OpenWithList\{}'.format(ext, app_name)
            )
        except Exception:
            pass

        # 3. Elimina l'intero albero del ProgID da Software\Classes
        try:
            self._DeleteRegKeyRecursive(
                winreg.HKEY_CURRENT_USER,
                r'Software\Classes\{}'.format(prog_id)
            )
        except Exception:
            pass

        # 4. Rimuovi Applications\<app_name> solo se nessuna altra ext è ancora associata
        other_exts = [e for e in ["crd", "cho", "chordpro", "chopro", "pro", "tab"] if e != ext]
        if not any(self._IsExtAssociatedWin(e) for e in other_exts):
            try:
                self._DeleteRegKeyRecursive(
                    winreg.HKEY_CURRENT_USER,
                    r'Software\Classes\Applications\{}'.format(app_name)
                )
            except Exception:
                pass

    @staticmethod
    def _DeleteRegKeyRecursive(hive, key_path):
        """Elimina ricorsivamente una chiave di registro e tutte le sue sottochiavi."""
        import winreg
        try:
            with winreg.OpenKey(hive, key_path, access=winreg.KEY_READ) as k:
                subkey_count = winreg.QueryInfoKey(k)[0]
                subkeys = [winreg.EnumKey(k, i) for i in range(subkey_count)]
        except FileNotFoundError:
            return  # già assente
        for subkey in subkeys:
            MyPreferencesDialog._DeleteRegKeyRecursive(
                hive, '{}\\{}'.format(key_path, subkey))
        winreg.DeleteKey(hive, key_path)

    # ---- Linux (XDG) ----

    # MIME type usato per tutti i file ChordPro/CRD
    _LINUX_MIME_TYPE = 'text/x-chordpro'
    # Tutte le estensioni condividono lo stesso MIME type
    _LINUX_MIME_EXTS = ["crd", "cho", "chordpro", "chopro", "pro", "tab"]

    def _GetLinuxLaunchCmd(self, exe):
        """Restituisce il comando Exec per il file .desktop (Linux)."""
        import sys as _sys
        import os as _os
        if getattr(_sys, 'frozen', False):
            return '{} %f'.format(exe)
        pkg_dir  = _os.path.dirname(_os.path.abspath(__file__))
        src_dir  = _os.path.dirname(pkg_dir)
        root_dir = _os.path.dirname(src_dir)
        main_py  = _os.path.join(root_dir, 'main.py')
        if not _os.path.isfile(main_py):
            main_py = _os.path.join(src_dir, 'main.py')
        return '{} {} %f'.format(exe, main_py)

    def _GetLinuxDesktopPath(self):
        import os as _os
        apps_dir = _os.path.join(_os.path.expanduser('~'), '.local', 'share', 'applications')
        _os.makedirs(apps_dir, exist_ok=True)
        return _os.path.join(apps_dir, 'songpress.desktop')

    def _GetLinuxMimeXmlPath(self):
        import os as _os
        mime_dir = _os.path.join(_os.path.expanduser('~'), '.local', 'share', 'mime', 'packages')
        _os.makedirs(mime_dir, exist_ok=True)
        return _os.path.join(mime_dir, 'songpress-mime.xml')

    def _EnsureLinuxDesktop(self, exe):
        """Crea/aggiorna il file .desktop per Songpress++ (~/.local/share/applications/)."""
        import os as _os
        desktop_path = self._GetLinuxDesktopPath()
        exec_cmd = self._GetLinuxLaunchCmd(exe)
        # Percorso icona: preferisce il .png, fallback al .ico
        ico_path = glb.AddPath('img/songpress++.png')
        if not _os.path.isfile(ico_path):
            ico_path = glb.AddPath('img/songpress++.ico')
        mime_list = ';'.join(
            ['{}+{}'.format(self._LINUX_MIME_TYPE, ext) for ext in self._LINUX_MIME_EXTS]
            + [self._LINUX_MIME_TYPE]
        ) + ';'
        content = (
            '[Desktop Entry]\n'
            'Type=Application\n'
            'Name=Songpress++\n'
            'Comment=ChordPro song editor\n'
            'Exec={exec_cmd}\n'
            'Icon={icon}\n'
            'MimeType={mime}\n'
            'Categories=Audio;Music;\n'
            'Terminal=false\n'
        ).format(exec_cmd=exec_cmd, icon=ico_path, mime=mime_list)
        with open(desktop_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return desktop_path

    def _EnsureLinuxMimeXml(self):
        """Crea/aggiorna il file XML del MIME type personalizzato."""
        xml_path = self._GetLinuxMimeXmlPath()
        # Costruisce i glob per ogni estensione
        globs = '\n    '.join(
            '<glob pattern="*.{}"/>'.format(ext) for ext in self._LINUX_MIME_EXTS
        )
        content = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">\n'
            '  <mime-type type="{mime}">\n'
            '    <comment>ChordPro song file</comment>\n'
            '    <comment xml:lang="it">File canzone ChordPro</comment>\n'
            '    <icon name="songpress"/>\n'
            '    {globs}\n'
            '  </mime-type>\n'
            '</mime-info>\n'
        ).format(mime=self._LINUX_MIME_TYPE, globs=globs)
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return xml_path

    def _IsExtAssociatedLinux(self, ext):
        """Controlla se l'estensione è associata a Songpress++ via XDG."""
        import subprocess
        try:
            mime = self._LINUX_MIME_TYPE
            result = subprocess.run(
                ['xdg-mime', 'query', 'default', mime],
                capture_output=True, text=True, timeout=5
            )
            return 'songpress' in result.stdout.lower()
        except Exception:
            return False

    def _AssociateExtLinux(self, ext, exe):
        """Associa le estensioni ChordPro a Songpress++ via XDG (Linux).
        Tutte le estensioni condividono lo stesso MIME type, quindi
        questa operazione si esegue una volta sola per tutte.
        """
        import subprocess
        import os as _os
        # 1. Installa il MIME type personalizzato
        xml_path = self._EnsureLinuxMimeXml()
        try:
            subprocess.run(['update-mime-database',
                            _os.path.join(_os.path.expanduser('~'), '.local', 'share', 'mime')],
                           timeout=10)
        except Exception:
            pass
        # 2. Installa il file .desktop
        desktop_path = self._EnsureLinuxDesktop(exe)
        try:
            subprocess.run(['update-desktop-database',
                            _os.path.join(_os.path.expanduser('~'), '.local', 'share', 'applications')],
                           timeout=10)
        except Exception:
            pass
        # 3. Imposta Songpress++ come default per il MIME type
        try:
            subprocess.run(
                ['xdg-mime', 'default', 'songpress.desktop', self._LINUX_MIME_TYPE],
                timeout=10
            )
        except Exception:
            pass

    def _UnassociateExtLinux(self, ext):
        """Rimuove il file .desktop e la registrazione MIME (Linux)."""
        import os as _os
        import subprocess
        # Rimuovi il file .desktop
        desktop_path = self._GetLinuxDesktopPath()
        try:
            if _os.path.isfile(desktop_path):
                _os.remove(desktop_path)
                subprocess.run(['update-desktop-database',
                                _os.path.join(_os.path.expanduser('~'), '.local', 'share', 'applications')],
                               timeout=10)
        except Exception:
            pass
        # Rimuovi il MIME xml
        xml_path = self._GetLinuxMimeXmlPath()
        try:
            if _os.path.isfile(xml_path):
                _os.remove(xml_path)
                subprocess.run(['update-mime-database',
                                _os.path.join(_os.path.expanduser('~'), '.local', 'share', 'mime')],
                               timeout=10)
        except Exception:
            pass

    def OnApplyFileAssoc(self, evt):
        """Applica immediatamente le associazioni file selezionate."""
        import platform as _platform
        exe = self._GetExePath()
        errors = []
        for ext, cb in self._fileAssocCBs.items():
            try:
                if cb.GetValue():
                    self._AssociateExt(ext, exe)
                else:
                    self._UnassociateExt(ext)
            except Exception as e:
                errors.append('.{}: {}'.format(ext, e))
        # Notifica il sistema del cambiamento
        if _platform.system() == 'Windows':
            try:
                import ctypes
                ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
            except Exception:
                pass
        if errors:
            wx.MessageBox(
                _("Some associations could not be changed:\n") + "\n".join(errors),
                _("Songpress++"), wx.OK | wx.ICON_WARNING, self
            )
        else:
            wx.MessageBox(
                _("File associations updated successfully."),
                _("Songpress++"), wx.OK | wx.ICON_INFORMATION, self
            )
        evt.Skip()

    def OnAssociateAll(self, evt):
        """Seleziona tutti i checkbox delle estensioni file."""
        if self._fileAssocAvailable:
            for cb in self._fileAssocCBs.values():
                cb.SetValue(True)
        evt.Skip()

    def OnUnassociateAll(self, evt):
        """Deseleziona tutti i checkbox delle estensioni file."""
        if self._fileAssocAvailable:
            for cb in self._fileAssocCBs.values():
                cb.SetValue(False)
        evt.Skip()

    def OnOk(self, evt):
        # Assign ALL values to pref BEFORE Save() so everything is persisted
        self.pref.editorFace, self.pref.editorSize = self.GetFont()
        l = self.GetLanguage()
        self.pref.locale = l
        self.pref.SetDefaultNotation(self.GetNotation())
        self.pref.autoAdjustSpuriousLines = self.autoRemoveBlankLines.GetValue()
        self.pref.autoAdjustTab2Chordpro = self.autoTab2Chordpro.GetValue()
        self.pref.autoAdjustEasyKey = self.autoAdjustEasyKey.GetValue()
        for k in self.decoSliders:
            self.pref.SetEasyChordsGroup(k, self.decoSliders[k].slider.GetValue())
        self.pref.defaultExtension = self.extension.GetString(self.extension.GetSelection())
        self.pref.titleLineWidth = self.titleLineWidthSpin.GetValue()
        self.pref.verseBoxWidth = self.verseBoxWidthSpin.GetValue()
        self.pref.klavierHighlightHex = self.klavierHexCtrl.GetValue().strip()
        if hasattr(self, 'editorBgHexCtrl'):
            self.pref.editorBgHex = self.editorBgHexCtrl.GetValue().strip()
        if hasattr(self, 'selColourHexCtrl'):
            self.pref.selColourHex = self.selColourHexCtrl.GetValue().strip()
        # Show print preview
        self.pref.showPrintPreview = self.showPrintPreviewCB.GetValue()
        # Multi-cursor
        self.pref.multiCursor = self.multiCursorCB.GetValue()
        # Salvataggio geometria finestra
        self.pref.saveWindowGeometry = self.saveWindowGeometryCB.GetValue()
        # Dimensione icone tempo
        if self.tempoIconSize16.GetValue():
            self.pref.tempoIconSize = 16
        elif self.tempoIconSize32.GetValue():
            self.pref.tempoIconSize = 32
        else:
            self.pref.tempoIconSize = 24
        # Context menu visibility — scritti in pref, Save() chiama _SaveContextMenu()
        self.pref.cmUndo         = self.cmUndo.GetValue()
        self.pref.cmRedo         = self.cmRedo.GetValue()
        self.pref.cmCut          = self.cmCut.GetValue()
        self.pref.cmCopy         = self.cmCopy.GetValue()
        self.pref.cmPaste        = self.cmPaste.GetValue()
        self.pref.cmDelete       = self.cmDelete.GetValue()
        self.pref.cmPasteChords           = self.cmPasteChords.GetValue()
        self.pref.cmPropagateVerseChords  = self.cmPropagateVerseChords.GetValue()
        self.pref.cmPropagateChorusChords = self.cmPropagateChorusChords.GetValue()
        self.pref.cmCopyTextOnly          = self.cmCopyTextOnly.GetValue()
        self.pref.cmSelectAll    = self.cmSelectAll.GetValue()
        self.pref.Save()
        lang = i18n.getLang()
        if l is not None and l != lang:
            msg = _("Language settings will be applied when you restart Songpress.")
            d = wx.MessageDialog(self, msg, _("Songpress"), wx.ICON_INFORMATION | wx.OK)
            d.ShowModal()
        # Se il pin è attivo: applica il callback senza chiudere il dialogo
        if self._pinned:
            if self._on_apply is not None:
                self._on_apply()
        else:
            evt.Skip(True)

    def OnPin(self, evt):
        """Toggling del pin button: mantiene il dialogo aperto dopo OK."""
        self._pinned = not self._pinned
        self.btnPin.SetLabel(u"📍" if self._pinned else u"📌")
