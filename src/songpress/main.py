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
from . import dev_tool


class SongpressApp(wx.App):
    def OnInit(self):
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


def main():
    sys.excepthook = dev_tool.ExceptionHook
    if platform.system() == 'Windows':
        import ctypes
        appid = f'songpress.{glb.VERSION}'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(appid)
    songpressApp = SongpressApp()
    songpressApp.MainLoop()


if __name__ == '__main__':
    main()
