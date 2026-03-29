###############################################################
# Name:             MyUpdateDialog.py
# Purpose:     Dialog to select updates to apply
# Author:         Luca Allulli (webmaster@roma21.it)
# Modified by:  Denisov21
# Created:     2010-12-14
# Copyright: Luca Allulli (https://www.skeed.it/songpress)
#               Modifications copyright Denisov21
# License:     GNU GPL v2
##############################################################
from xmlrpc.client import Server
import traceback
import logging

import wx.lib.delayedresult as delayedresult
import wx

from .UpdateDialog import *
from .Globals import glb
from .MyUpdatePanel import MyUpdatePanel


_ = wx.GetTranslation

def check_and_update(parent, preferences, force=False):
    """
    Check for updates, and interact with user.
    
    Update mode is automatic if force=False, else manual.
    
    parent: parent window of any created modal dialogs
    """
    def check_for_updates():
        # Controllo aggiornamenti disabilitato (fork locale)
        return []

    def consume_updates(dr):
        try:
            u = dr.get()
            if len(u) > 0:
                d = MyUpdateDialog(parent, preferences, u)
                d.ShowModal()
            elif force:
                d = wx.MessageDialog(
                    parent,
                    _("Your version of Songpress is up to date."),
                    _("Songpress"),
                    wx.OK | wx.ICON_INFORMATION
                )
                d.ShowModal()
        except Exception as e:
            logging.error(traceback.format_exc())
            if force:
                d = wx.MessageDialog(
                    parent,
                    _("There was an error while checking for updates.\nPlease try again later."),
                    _("Update error"),
                    wx.OK | wx.ICON_ERROR
                )
                d.ShowModal()

    delayedresult.startWorker(consume_updates, check_for_updates)


class MyUpdateDialog(UpdateDialog):
    def __init__(self, parent, preferences, updates):
        UpdateDialog.__init__(self, parent)
        self.preferences = preferences
        self.updates = updates
        self.updatePanels = set()
        for u in updates:
            up = MyUpdatePanel(self, preferences, u[0], u[1], u[2])
            self.updatePanels.add(up)
            self.updatesSizer.Add(up, 1, wx.EXPAND, 5 )
        self.SetSize((400, 400))
        
    def RemoveChild(self, child):
        self.updatesSizer.Layout()
        self.updatePanels.remove(child)
        if len(self.updatePanels) == 0:
            self.Show(False)
            self.Destroy()
            
    def OnDonate(self, evt):
        wx.LaunchDefaultBrowser(_("https://www.skeed.it/songpress#donate"))
        evt.Skip()

