###############################################################
# Name:             MyUpdatePanel.py
# Purpose:     Panel for software update notification
# Author:         Denisov21
# Created:     2026
# Copyright: © 2026 Denisov21
# License:     GNU GPL v2
##############################################################

#!/usr/bin/env python

import wx

from .UpdatePanel import UpdatePanel


class MyUpdatePanel(UpdatePanel):
    def __init__(self, parent, preferences, version, description, downloadUrl):
        UpdatePanel.__init__(self, parent)
        self.parent = parent
        self.preferences = preferences
        self.downloadUrl = downloadUrl
        self.v = version
        self.version.SetValue(version)
        self.new_features.SetPage(description)
        
    def __Hide(self):
        self.Show(False)
        self.Destroy()
        
    def OnDownload(self, evt):
        wx.LaunchDefaultBrowser(self.downloadUrl)
        self.__Hide()
        evt.Skip()
        
    def OnSkip(self, evt):
        self.preferences.ignoredUpdates.add(self.v)
        self.__Hide()
        evt.Skip()
        
    def OnRemind(self, evt):
        self.__Hide()
        evt.Skip()

