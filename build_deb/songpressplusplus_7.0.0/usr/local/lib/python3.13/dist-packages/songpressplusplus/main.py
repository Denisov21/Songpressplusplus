###############################################################
# Name:             main.py
# Purpose:     Entry point for Songpress
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2009-01-16
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
##############################################################

import sys, os
import platform

import wx

from .Globals import glb
from . import i18n
from . import errdlg

_ = wx.GetTranslation


class SongpressApp(wx.App):
    def __init__(self):
        # redirect=False: non redirigere stdout/stderr verso una finestra di dialogo.
        # Indispensabile nella build frozen (cx_Freeze) su Windows: con redirect=True
        # il framework tenta di creare una finestra di output che può bloccare l'avvio
        # quando l'app viene lanciata per associazione file (doppio click).
        super().__init__(redirect=False)

    def OnInit(self):
        errdlg.install_wx_exception_handler(self)
        self.SetAppName(glb.PROG_NAME)
        self.VERSION = glb.VERSION
        glb.InitDataPath()
        self.config = wx.FileConfig(localFilename=os.path.join(glb.data_path, "config.ini"))
        wx.Config.Set(self.config)
        i18n.init(glb.default_language, [l for l in glb.languages])
        self.config.SetPath("/App")
        l = self.config.Read("locale")
        if l:
            print("Setting language ", l)
            i18n.setLang(l)
        else:
            print("Setting system language ")
            i18n.setSystemLang()

        from . import SongpressFrame
        self.res = wx.xrc.XmlResource(glb.AddPath("xrc/songpress.xrc"))
        self._songpress_frame = SongpressFrame.SongpressFrame(self.res)
        return True


def _log(msg):
    """Scrive un log su file per diagnosticare problemi di avvio da doppio click."""
    import datetime
    try:
        import os as _os
        log_path = _os.path.join(
            _os.path.expanduser('~'), 'AppData', 'Local', 'Songpress++', 'startup.log'
        )
        _os.makedirs(_os.path.dirname(log_path), exist_ok=True)
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{datetime.datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
    except Exception:
        pass


def _get_config_path():
    """Restituisce il path di config.ini usando la stessa logica di glb.InitDataPath(),
    ma senza richiedere wx.App già inizializzata."""
    # 1. Portable mode: config.ini accanto al package sorgente
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    portable = os.path.join(pkg_dir, 'config.ini')
    if os.path.isfile(portable):
        return portable

    # 2. Standard user-data dir — replica wx.StandardPaths.GetUserDataDir()
    #    senza istanza wx.App
    if platform.system() == 'Windows':
        # %APPDATA%\<AppName>  oppure  %LOCALAPPDATA%\<AppName>
        # wx usa APPDATA su Windows per GetUserDataDir
        base = os.environ.get('APPDATA') or os.path.expanduser('~')
        data_dir = os.path.join(base, glb.PROG_NAME)
    elif platform.system() == 'Darwin':
        data_dir = os.path.join(
            os.path.expanduser('~'), 'Library', 'Application Support', glb.PROG_NAME
        )
    else:
        data_dir = os.path.join(os.path.expanduser('~'), f'.{glb.PROG_NAME}')

    return os.path.join(data_dir, 'config.ini')


def _read_single_instance_pref():
    """Legge singleInstance da config.ini senza wx. Default True.

    wx.FileConfig scrive le sezioni in lowercase ma conserva il case
    originale delle chiavi (es. 'singleInstance' con la S maiuscola).
    configparser di default converte tutto in minuscolo, il che fa sì
    che la chiave non venga mai trovata e si cada sempre nel fallback '1'.
    Si risolve passando optionxform=str per disabilitare la normalizzazione.
    """
    try:
        import configparser as _cp
        cfg_path = _get_config_path()
        _log(f"Single-instance: lettura config da {cfg_path!r}")
        if not os.path.isfile(cfg_path):
            _log("Single-instance: config non trovato, uso default True")
            return True
        cfg = _cp.RawConfigParser()
        # Mantiene il case originale delle chiavi (wx scrive 'singleInstance',
        # non 'singleinstance'): senza questa riga configparser non trova mai
        # il valore e restituisce sempre il fallback '1' → bug silenzioso.
        cfg.optionxform = str
        cfg.read(cfg_path, encoding='utf-8')
        # wx.FileConfig scrive le sezioni in lowercase → sezione [app]
        val = cfg.get('app', 'singleInstance', fallback='1')
        result = val.strip() == '1'
        _log(f"Single-instance: singleInstance={val!r} → {result}")
        return result
    except Exception as e:
        _log(f"Single-instance: errore lettura config ({e}), uso default True")
        return True


def main():
    _log(f"main() avviato  argv={sys.argv}")
    sys.excepthook = errdlg.ExceptionHook
    if platform.system() == 'Windows':
        import ctypes
        # ── Nasconde la finestra console se l'app è stata lanciata con
        #    python.exe invece di pythonw.exe (es. da terminale, da uv run,
        #    o con alcuni launcher di terze parti).
        #    GetConsoleWindow() restituisce 0 se non c'è console allocata
        #    (build cx_Freeze con base=gui, doppio click su .exe): in quel
        #    caso ShowWindow non viene chiamata e non ha effetti collaterali.
        _hwnd_console = ctypes.windll.kernel32.GetConsoleWindow()
        if _hwnd_console:
            ctypes.windll.user32.ShowWindow(_hwnd_console, 0)  # SW_HIDE

        # AppUserModelID stabile (senza versione): Windows lo usa per raggruppare
        # le finestre sulla taskbar e per abbinare l'app alle associazioni file.
        # Se cambia ad ogni versione Windows perde il collegamento tra ProgID e app.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            'Denisov21.SongpressPlusPlus'
        )

    # ── Single-instance check ────────────────────────────────────────────
    if _read_single_instance_pref():
        from .SDIMainFrame import SDIMainFrame

        if len(sys.argv) > 1:
            _filepath = sys.argv[1]
            _log(f"Single-instance: tentativo inoltro per {_filepath!r}")

            # Error case: file does not exist
            if not os.path.isfile(_filepath):
                _log(f"Single-instance: file non trovato {_filepath!r}")
                errdlg._show_error(
                    _("Cannot open file:") + f"\n{_filepath}\n\n" +
                    _("The file does not exist or is not accessible.")
                )
                sys.exit(1)

            if SDIMainFrame._TrySendToExistingInstance(_filepath):
                # Normal case: forwarded silently, existing window raises itself
                _log("File inoltrato all'istanza esistente — uscita.")
                sys.exit(0)

            # Fallback: no instance listening (first launch or crashed) — start normally
            _log("Single-instance: nessuna istanza in ascolto, avvio normale.")

        else:
            # No file argument: check if an instance is already running and raise it
            if SDIMainFrame._TrySendToExistingInstance('__RAISE__'):
                _log("Istanza esistente riportata in primo piano — uscita.")
                sys.exit(0)
            _log("Single-instance: nessuna istanza in ascolto, avvio normale.")
    # ── Fine single-instance check ───────────────────────────────────────

    songpressApp = SongpressApp()
    songpressApp.MainLoop()


if __name__ == '__main__':
    main()
