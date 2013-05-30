#!/usr/bin/env python
# -*- coding: utf-8 -*-

#This file is part of PLCOpenEditor, a library implementing an IEC 61131-3 editor
#based on the plcopen standard. 
#
#Copyright (C) 2012: Edouard TISSERANT and Laurent BESSARD
#
#See COPYING file for copyrights details.
#
#This library is free software; you can redistribute it and/or
#modify it under the terms of the GNU General Public
#License as published by the Free Software Foundation; either
#version 2.1 of the License, or (at your option) any later version.
#
#This library is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#General Public License for more details.
#
#You should have received a copy of the GNU General Public
#License along with this library; if not, write to the Free Software
#Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import wx

from util.BitmapLibrary import GetBitmap

#-------------------------------------------------------------------------------
#                        Custom button for Graphic Viewer Class
#-------------------------------------------------------------------------------

"""
Class that implements a custom button for graphic Viewer
"""

class GraphButton():
    
    def __init__(self, x, y, bitmap, callback):
        """
        Constructor
        @param x: X coordinate of Button in Graphic Viewer
        @param y: Y coordinate of Button in Graphic Viewer
        @param bitmap: Name of bitmap to use for button
        @param callback: Reference to function to call when button is pressed
        """
        # Save button position
        self.SetPosition(x, y)
        # Get wx.Bitmap object corresponding to bitmap
        self.Bitmap = GetBitmap(bitmap)
        
        # By default button is shown and enabled
        self.Shown = True
        self.Enabled = True
        
        # Save reference to callback function
        self.Callback = callback
    
    def __del__(self):
        """
        Destructor
        """
        # Remove reference to callback function
        self.callback = None
    
    def GetSize(self):
        """
        Return size of button
        @return: wx.Size object containing button size
        """
        # Button size is size of bitmap
        return self.Bitmap.GetSize()
    
    def SetPosition(self, x, y):
        """
        Set button position
        @param x: X coordinate of Button in Graphic Viewer
        @param y: Y coordinate of Button in Graphic Viewer
        """
        self.Position = wx.Point(x, y)
    
    def Show(self, show=True):
        """
        Mark if button to be displayed in Graphic Viewer
        @param show: True if button to be displayed in Graphic Viewer
        (default True)
        """
        self.Shown = show
        
    def Hide(self):
        """
        Hide button from Graphic Viewer
        """
        self.Show(False)
    
    def IsShown(self):
        """
        Return if button is displayed in Graphic Viewer
        @return: True if button is displayed in Graphic Viewer
        """
        return self.Shown
    
    def Enable(self, enable=True):
        """
        Mark if button is active in Graphic Viewer
        @param enable: True if button is active in Graphic Viewer
        (default True)
        """
        self.Enabled = True
    
    def Disable(self):
        """
        Deactivate button in Graphic Viewer
        """
        self.Enabled = False
    
    def IsEnabled(self):
        """
        Return if button is active in Graphic Viewer
        @return: True if button is active in Graphic Viewer
        """
        return self.Enabled
    
    def HitTest(self, x, y):
        """
        Test if point is inside button
        @param x: X coordinate of point
        @param y: Y coordinate of point
        @return: True if button is active and displayed and point is inside
        button 
        """
        # Return immediately if button is hidden or inactive
        if not (self.IsShown() and self.IsEnabled()):
            return False
        
        # Test if point is inside button
        w, h = self.Bitmap.GetSize()
        rect = wx.Rect(self.Position.x, self.Position.y, w, h)
        return rect.InsideXY(x, y)
    
    def ProcessCallback(self):
        """
        Call callback function if defined
        """
        if self.Callback is not None:
            wx.CallAfter(self.Callback)
    
    def Draw(self, dc):
        """
        Draw button in Graphic Viewer
        @param dc: wx.DC object corresponding to Graphic Viewer device context
        """
        # Only draw button if button is active and displayed
        if self.Shown and self.Enabled:
            dc.DrawBitmap(self.Bitmap, self.Position.x, self.Position.y, True)
