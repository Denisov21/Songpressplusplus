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
        songpressFrame = SongpressFrame.SongpressFrame(self.res)
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


def main():
    _log(f"main() avviato  argv={sys.argv}")
    sys.excepthook = errdlg.ExceptionHook
    if platform.system() == 'Windows':
        import ctypes
        # AppUserModelID stabile (senza versione): Windows lo usa per raggruppare
        # le finestre sulla taskbar e per abbinare l'app alle associazioni file.
        # Se cambia ad ogni versione Windows perde il collegamento tra ProgID e app.
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            'Denisov21.SongpressPlusPlus'
        )
    songpressApp = SongpressApp()
    songpressApp.MainLoop()


if __name__ == '__main__':
    main()
