#!/usr/bin/env python
# -*- coding: utf-8 -*-

#This file is part of Beremiz, a Integrated Development Environment for
#programming IEC 61131-3 automates supporting plcopen standard and CanFestival. 
#
#Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
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

__version__ = "$Revision$"

import os, sys, getopt, wx
import tempfile
import shutil
import random

CWD = os.path.split(os.path.realpath(__file__))[0]

def Bpath(*args):
    return os.path.join(CWD,*args)

if __name__ == '__main__':
    def usage():
        print "\nUsage of Beremiz.py :"
        print "\n   %s [Projectpath] [Buildpath]\n"%sys.argv[0]
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
    
    if len(args) > 2:
        usage()
        sys.exit()
    elif len(args) == 1:
        projectOpen = args[0]
        buildpath = None
    elif len(args) == 2:
        projectOpen = args[0]
        buildpath = args[1]
    else:
        projectOpen = None
        buildpath = None
    
    app = wx.PySimpleApp()
    app.SetAppName('beremiz')
    config = wx.ConfigBase.Get()
    wx.InitAllImageHandlers()
    
    bmp = wx.Image(Bpath("images","splash.png")).ConvertToBitmap()
    splash=wx.SplashScreen(bmp,wx.SPLASH_CENTRE_ON_SCREEN, 1000, None)
    wx.Yield()

# Import module for internationalization
import gettext
import __builtin__

# Get folder containing translation files
localedir = os.path.join(CWD,"locale")
# Get the default language
langid = wx.LANGUAGE_DEFAULT
# Define translation domain (name of translation files)
domain = "Beremiz"

# Define locale for wx
loc = __builtin__.__dict__.get('loc', None)
if loc is None:
    loc = wx.Locale(langid)
    __builtin__.__dict__['loc'] = loc
# Define location for searching translation files
loc.AddCatalogLookupPathPrefix(localedir)
# Define locale domain
loc.AddCatalog(domain)

def unicode_translation(message):
    return wx.GetTranslation(message).encode("utf-8")

if __name__ == '__main__':
    __builtin__.__dict__['_'] = wx.GetTranslation#unicode_translation

import wx.lib.buttons, wx.lib.statbmp
import TextCtrlAutoComplete, cPickle
import types, time, re, platform, time, traceback, commands
from plugger import PluginsRoot, MATIEC_ERROR_MODEL
from wxPopen import ProcessLogger

base_folder = os.path.split(sys.path[0])[0]
sys.path.append(base_folder)
from docutils import *

SCROLLBAR_UNIT = 10
WINDOW_COLOUR = wx.Colour(240,240,240)
TITLE_COLOUR = wx.Colour(200,200,220)
CHANGED_TITLE_COLOUR = wx.Colour(220,200,220)
CHANGED_WINDOW_COLOUR = wx.Colour(255,240,240)

if wx.Platform == '__WXMSW__':
    faces = { 'times': 'Times New Roman',
              'mono' : 'Courier New',
              'helv' : 'Arial',
              'other': 'Comic Sans MS',
              'size' : 16,
             }
else:
    faces = { 'times': 'Times',
              'mono' : 'Courier',
              'helv' : 'Helvetica',
              'other': 'new century schoolbook',
              'size' : 18,
             }

# Some helpers to tweak GenBitmapTextButtons
# TODO: declare customized classes instead.
gen_mini_GetBackgroundBrush = lambda obj:lambda dc: wx.Brush(obj.GetParent().GetBackgroundColour(), wx.SOLID)
gen_textbutton_GetLabelSize = lambda obj:lambda:(wx.lib.buttons.GenButton._GetLabelSize(obj)[:-1] + (False,))

def make_genbitmaptogglebutton_flat(button):
    button.GetBackgroundBrush = gen_mini_GetBackgroundBrush(button)
    button.labelDelta = 0
    button.SetBezelWidth(0)
    button.SetUseFocusIndicator(False)

# Patch wx.lib.imageutils so that gray is supported on alpha images
import wx.lib.imageutils
from wx.lib.imageutils import grayOut as old_grayOut
def grayOut(anImage):
    if anImage.HasAlpha():
        AlphaData = anImage.GetAlphaData()
    else :
        AlphaData = None

    old_grayOut(anImage)

    if AlphaData is not None:
        anImage.SetAlphaData(AlphaData)

wx.lib.imageutils.grayOut = grayOut

class GenBitmapTextButton(wx.lib.buttons.GenBitmapTextButton):
    def _GetLabelSize(self):
        """ used internally """
        w, h = self.GetTextExtent(self.GetLabel())
        if not self.bmpLabel:
            return w, h, False       # if there isn't a bitmap use the size of the text

        w_bmp = self.bmpLabel.GetWidth()+2
        h_bmp = self.bmpLabel.GetHeight()+2
        height = h + h_bmp
        if w_bmp > w:
            width = w_bmp
        else:
            width = w
        return width, height, False

    def DrawLabel(self, dc, width, height, dw=0, dy=0):
        bmp = self.bmpLabel
        if bmp != None:     # if the bitmap is used
            if self.bmpDisabled and not self.IsEnabled():
                bmp = self.bmpDisabled
            if self.bmpFocus and self.hasFocus:
                bmp = self.bmpFocus
            if self.bmpSelected and not self.up:
                bmp = self.bmpSelected
            bw,bh = bmp.GetWidth(), bmp.GetHeight()
            if not self.up:
                dw = dy = self.labelDelta
            hasMask = bmp.GetMask() != None
        else:
            bw = bh = 0     # no bitmap -> size is zero

        dc.SetFont(self.GetFont())
        if self.IsEnabled():
            dc.SetTextForeground(self.GetForegroundColour())
        else:
            dc.SetTextForeground(wx.SystemSettings.GetColour(wx.SYS_COLOUR_GRAYTEXT))

        label = self.GetLabel()
        tw, th = dc.GetTextExtent(label)        # size of text
        if not self.up:
            dw = dy = self.labelDelta

        pos_x = (width-bw)/2+dw      # adjust for bitmap and text to centre
        pos_y = (height-bh-th)/2+dy
        if bmp !=None:
            dc.DrawBitmap(bmp, pos_x, pos_y, hasMask) # draw bitmap if available
            pos_x = (width-tw)/2+dw      # adjust for bitmap and text to centre
            pos_y += bh + 2

        dc.DrawText(label, pos_x, pos_y)      # draw the text


class GenStaticBitmap(wx.lib.statbmp.GenStaticBitmap):
    """ Customized GenStaticBitmap, fix transparency redraw bug on wx2.8/win32, 
    and accept image name as __init__ parameter, fail silently if file do not exist"""
    def __init__(self, parent, ID, bitmapname,
                 pos = wx.DefaultPosition, size = wx.DefaultSize,
                 style = 0,
                 name = "genstatbmp"):
        
        bitmappath = Bpath( "images", bitmapname)
        if os.path.isfile(bitmappath):
            bitmap = wx.Bitmap(bitmappath)
        else:
            bitmap = None
        wx.lib.statbmp.GenStaticBitmap.__init__(self, parent, ID, bitmap,
                 pos, size,
                 style,
                 name)
        
    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        colour = self.GetParent().GetBackgroundColour()
        dc.SetPen(wx.Pen(colour))
        dc.SetBrush(wx.Brush(colour ))
        dc.DrawRectangle(0, 0, *dc.GetSizeTuple())
        if self._bitmap:
            dc.DrawBitmap(self._bitmap, 0, 0, True)

                        
class LogPseudoFile:
    """ Base class for file like objects to facilitate StdOut for the Shell."""
    def __init__(self, output):
        self.red_white = wx.TextAttr("RED", "WHITE")
        self.red_yellow = wx.TextAttr("RED", "YELLOW")
        self.black_white = wx.TextAttr("BLACK", "WHITE")
        self.default_style = None
        self.output = output

    def write(self, s, style = None):
        if style is None : style=self.black_white
        self.output.Freeze(); 
        if self.default_style != style: 
            self.output.SetDefaultStyle(style)
            self.default_style = style
        self.output.AppendText(s)
        self.output.ScrollLines(s.count('\n')+1)
        self.output.ShowPosition(self.output.GetLastPosition())
        self.output.Thaw()

    def write_warning(self, s):
        self.write(s,self.red_white)

    def write_error(self, s):
        self.write(s,self.red_yellow)

    def flush(self):
        self.output.SetValue("")
    
    def isatty(self):
        return false

[ID_BEREMIZ, ID_BEREMIZMAINSPLITTER, 
 ID_BEREMIZPLCCONFIG, ID_BEREMIZLOGCONSOLE, 
 ID_BEREMIZINSPECTOR] = [wx.NewId() for _init_ctrls in range(5)]

[ID_BEREMIZRUNMENUBUILD, ID_BEREMIZRUNMENUSIMULATE, 
 ID_BEREMIZRUNMENURUN, ID_BEREMIZRUNMENUSAVELOG, 
] = [wx.NewId() for _init_coll_EditMenu_Items in range(4)]

class Beremiz(wx.Frame):
	
    def _init_coll_FileMenu_Items(self, parent):
        parent.Append(help='', id=wx.ID_NEW,
              kind=wx.ITEM_NORMAL, text=_(u'New\tCTRL+N'))
        parent.Append(help='', id=wx.ID_OPEN,
              kind=wx.ITEM_NORMAL, text=_(u'Open\tCTRL+O'))
        parent.Append(help='', id=wx.ID_SAVE,
              kind=wx.ITEM_NORMAL, text=_(u'Save\tCTRL+S'))
        parent.Append(help='', id=wx.ID_CLOSE_ALL,
              kind=wx.ITEM_NORMAL, text=_(u'Close Project'))
        parent.AppendSeparator()
        parent.Append(help='', id=wx.ID_PROPERTIES,
              kind=wx.ITEM_NORMAL, text=_(u'Properties'))
        parent.AppendSeparator()
        parent.Append(help='', id=wx.ID_EXIT,
              kind=wx.ITEM_NORMAL, text=_(u'Quit\tCTRL+Q'))
        self.Bind(wx.EVT_MENU, self.OnNewProjectMenu, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.OnOpenProjectMenu, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSaveProjectMenu, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnCloseProjectMenu, id=wx.ID_CLOSE_ALL)
        self.Bind(wx.EVT_MENU, self.OnPropertiesMenu, id=wx.ID_PROPERTIES)
        self.Bind(wx.EVT_MENU, self.OnQuitMenu, id=wx.ID_EXIT)
        
    def _init_coll_EditMenu_Items(self, parent):
        parent.Append(help='', id=wx.ID_EDIT,
              kind=wx.ITEM_NORMAL, text=_(u'Edit PLC\tCTRL+R'))
        parent.AppendSeparator()
        parent.Append(help='', id=wx.ID_ADD,
              kind=wx.ITEM_NORMAL, text=_(u'Add Plugin'))
        parent.Append(help='', id=wx.ID_DELETE,
              kind=wx.ITEM_NORMAL, text=_(u'Delete Plugin'))
        self.Bind(wx.EVT_MENU, self.OnEditPLCMenu, id=wx.ID_EDIT)
        self.Bind(wx.EVT_MENU, self.OnAddMenu, id=wx.ID_ADD)
        self.Bind(wx.EVT_MENU, self.OnDeleteMenu, id=wx.ID_DELETE)
    
    def _init_coll_RunMenu_Items(self, parent):
        parent.Append(help='', id=ID_BEREMIZRUNMENUBUILD,
              kind=wx.ITEM_NORMAL, text=_(u'Build\tCTRL+R'))
        parent.AppendSeparator()
        parent.Append(help='', id=ID_BEREMIZRUNMENUSIMULATE,
              kind=wx.ITEM_NORMAL, text=_(u'Simulate'))
        parent.Append(help='', id=ID_BEREMIZRUNMENURUN,
              kind=wx.ITEM_NORMAL, text=_(u'Run'))
        parent.AppendSeparator()
        parent.Append(help='', id=ID_BEREMIZRUNMENUSAVELOG,
              kind=wx.ITEM_NORMAL, text=_(u'Save Log'))
        self.Bind(wx.EVT_MENU, self.OnBuildMenu,
              id=ID_BEREMIZRUNMENUBUILD)
        self.Bind(wx.EVT_MENU, self.OnSimulateMenu,
              id=ID_BEREMIZRUNMENUSIMULATE)
        self.Bind(wx.EVT_MENU, self.OnRunMenu,
              id=ID_BEREMIZRUNMENURUN)
        self.Bind(wx.EVT_MENU, self.OnSaveLogMenu,
              id=ID_BEREMIZRUNMENUSAVELOG)
    
    def _init_coll_HelpMenu_Items(self, parent):
        parent.Append(help='', id=wx.ID_HELP,
              kind=wx.ITEM_NORMAL, text=_(u'Beremiz\tF1'))
        parent.Append(help='', id=wx.ID_ABOUT,
              kind=wx.ITEM_NORMAL, text=_(u'About'))
        self.Bind(wx.EVT_MENU, self.OnBeremizMenu, id=wx.ID_HELP)
        self.Bind(wx.EVT_MENU, self.OnAboutMenu, id=wx.ID_ABOUT)
    
    def _init_coll_MenuBar_Menus(self, parent):
        parent.Append(menu=self.FileMenu, title=_(u'File'))
        #parent.Append(menu=self.EditMenu, title=u'Edit')
        #parent.Append(menu=self.RunMenu, title=u'Run')
        parent.Append(menu=self.HelpMenu, title=_(u'Help'))
    
    def _init_utils(self):
        self.MenuBar = wx.MenuBar()
        self.FileMenu = wx.Menu(title=u'')
        #self.EditMenu = wx.Menu(title=u'')
        #self.RunMenu = wx.Menu(title=u'')
        self.HelpMenu = wx.Menu(title=u'')
        
        self._init_coll_MenuBar_Menus(self.MenuBar)
        self._init_coll_FileMenu_Items(self.FileMenu)
        #self._init_coll_EditMenu_Items(self.EditMenu)
        #self._init_coll_RunMenu_Items(self.RunMenu)
        self._init_coll_HelpMenu_Items(self.HelpMenu)
    
    def _init_coll_PLCConfigMainSizer_Items(self, parent):
        parent.AddSizer(self.PLCParamsSizer, 0, border=10, flag=wx.GROW|wx.TOP|wx.LEFT|wx.RIGHT)
        parent.AddSizer(self.PluginTreeSizer, 0, border=10, flag=wx.BOTTOM|wx.LEFT|wx.RIGHT)
        
    def _init_coll_PLCConfigMainSizer_Growables(self, parent):
        parent.AddGrowableCol(0)
        parent.AddGrowableRow(1)
    
    def _init_coll_PluginTreeSizer_Growables(self, parent):
        parent.AddGrowableCol(0)
        parent.AddGrowableCol(1)
        
    def _init_sizers(self):
        self.PLCConfigMainSizer = wx.FlexGridSizer(cols=1, hgap=2, rows=2, vgap=2)
        self.PLCParamsSizer = wx.BoxSizer(wx.VERTICAL)
        #self.PluginTreeSizer = wx.FlexGridSizer(cols=3, hgap=0, rows=0, vgap=2)
        self.PluginTreeSizer = wx.FlexGridSizer(cols=2, hgap=0, rows=0, vgap=2)
        
        self._init_coll_PLCConfigMainSizer_Items(self.PLCConfigMainSizer)
        self._init_coll_PLCConfigMainSizer_Growables(self.PLCConfigMainSizer)
        self._init_coll_PluginTreeSizer_Growables(self.PluginTreeSizer)
        
        self.PLCConfig.SetSizer(self.PLCConfigMainSizer)
        
    def _init_ctrls(self, prnt):
        wx.Frame.__init__(self, id=ID_BEREMIZ, name=u'Beremiz',
              parent=prnt, pos=wx.Point(0, 0), size=wx.Size(1000, 600),
              style=wx.DEFAULT_FRAME_STYLE|wx.CLIP_CHILDREN, title=_(u'Beremiz'))
        self._init_utils()
        self.SetClientSize(wx.Size(1000, 600))
        self.SetMenuBar(self.MenuBar)
        self.Bind(wx.EVT_ACTIVATE, self.OnFrameActivated)
        self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)

        self.Bind(wx.EVT_MENU, self.OnOpenWidgetInspector, id=ID_BEREMIZINSPECTOR)
        accel = wx.AcceleratorTable([wx.AcceleratorEntry(wx.ACCEL_CTRL|wx.ACCEL_ALT, ord('I'), ID_BEREMIZINSPECTOR)])
        self.SetAcceleratorTable(accel)
        
        if wx.VERSION < (2, 8, 0):
            self.MainSplitter = wx.SplitterWindow(id=ID_BEREMIZMAINSPLITTER,
                  name='MainSplitter', parent=self, point=wx.Point(0, 0),
                  size=wx.Size(0, 0), style=wx.SP_3D)
            self.MainSplitter.SetNeedUpdating(True)
            self.MainSplitter.SetMinimumPaneSize(1)
        
            parent = self.MainSplitter
        else:
            parent = self
        
        self.PLCConfig = wx.ScrolledWindow(id=ID_BEREMIZPLCCONFIG,
              name='PLCConfig', parent=parent, pos=wx.Point(0, 0),
              size=wx.Size(-1, -1), style=wx.TAB_TRAVERSAL|wx.SUNKEN_BORDER|wx.HSCROLL|wx.VSCROLL)
        self.PLCConfig.SetBackgroundColour(wx.WHITE)
        self.PLCConfig.Bind(wx.EVT_LEFT_DOWN, self.OnPanelLeftDown)
        self.PLCConfig.Bind(wx.EVT_SIZE, self.OnMoveWindow)
        
        self.LogConsole = wx.TextCtrl(id=ID_BEREMIZLOGCONSOLE, value='',
                  name='LogConsole', parent=parent, pos=wx.Point(0, 0),
                  size=wx.Size(0, 0), style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.LogConsole.Bind(wx.EVT_LEFT_DCLICK, self.OnLogConsoleDClick)
        
        if wx.VERSION < (2, 8, 0):
            self.MainSplitter.SplitHorizontally(self.PLCConfig, self.LogConsole, -250)
        else:
            self.AUIManager = wx.aui.AuiManager(self)
            self.AUIManager.SetDockSizeConstraint(0.5, 0.5)
            
            self.AUIManager.AddPane(self.PLCConfig, wx.aui.AuiPaneInfo().CenterPane())
            
            self.AUIManager.AddPane(self.LogConsole, wx.aui.AuiPaneInfo().
                Caption(_("Log Console")).Bottom().Layer(1).
                BestSize(wx.Size(800, 200)).CloseButton(False))
        
            self.AUIManager.Update()

        self._init_sizers()

    def __init__(self, parent, projectOpen, buildpath):
        self._init_ctrls(parent)
        
        self.Log = LogPseudoFile(self.LogConsole)

        self.local_runtime = None
        self.runtime_port = None
        self.local_runtime_tmpdir = None
        
        # Add beremiz's icon in top left corner of the frame
        self.SetIcon(wx.Icon(Bpath( "images", "brz.ico"), wx.BITMAP_TYPE_ICO))
        
        self.DisableEvents = False
        
        self.PluginInfos = {}
        
        if projectOpen:
            self.PluginRoot = PluginsRoot(self, self.Log)
            self.PluginRoot.LoadProject(projectOpen, buildpath)
            self.RefreshAll()
        else:
            self.PluginRoot = None
        
        self.RefreshMainMenu()

    def StartLocalRuntime(self, taskbaricon = True):
        if self.local_runtime is None or self.local_runtime.finished:
            # create temporary directory for runtime working directory
            self.local_runtime_tmpdir = tempfile.mkdtemp()
            # choose an arbitrary random port for runtime
            self.runtime_port = int(random.random() * 1000) + 61131
            # launch local runtime
            self.local_runtime = ProcessLogger(self.Log,
                                               "\"%s\" \"%s\" -p %s -i localhost %s %s"%(sys.executable,
                                                           Bpath("Beremiz_service.py"),
                                                           self.runtime_port,
                                                           {False : "-x 0", True :"-x 1"}[taskbaricon],
                                                           self.local_runtime_tmpdir),
                                                           no_gui=False)
            self.local_runtime.spin(timeout=500, keyword = "working", kill_it = False)
        return self.runtime_port
    
    def KillLocalRuntime(self):
        if self.local_runtime is not None:
            # shutdown local runtime
            self.local_runtime.kill(gently=False)
            # clear temp dir
            shutil.rmtree(self.local_runtime_tmpdir)

    def OnOpenWidgetInspector(self, evt):
        # Activate the widget inspection tool
        from wx.lib.inspection import InspectionTool
        if not InspectionTool().initialized:
            InspectionTool().Init()

        # Find a widget to be selected in the tree.  Use either the
        # one under the cursor, if any, or this frame.
        wnd = wx.FindWindowAtPointer()
        if not wnd:
            wnd = self
        InspectionTool().Show(wnd, True)

    def OnLogConsoleDClick(self, event):
        wx.CallAfter(self.SearchLineForError)
        event.Skip()

    def SearchLineForError(self):
        if self.PluginRoot is not None:
            text = self.LogConsole.GetRange(0, self.LogConsole.GetInsertionPoint())
            line = self.LogConsole.GetLineText(len(text.splitlines()) - 1)
            result = MATIEC_ERROR_MODEL.match(line)
            if result is not None:
                first_line, first_column, last_line, last_column, error = result.groups()
                infos = self.PluginRoot.ShowError(self.Log,
                                                  (int(first_line), int(first_column)), 
                                                  (int(last_line), int(last_column)))
		
    def OnCloseFrame(self, event):
        if self.PluginRoot is not None:
            if self.PluginRoot.ProjectTestModified():
                dialog = wx.MessageDialog(self,
                                          _("Save changes ?"),
                                          _("Close Application"), 
                                          wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
                answer = dialog.ShowModal()
                dialog.Destroy()
                if answer == wx.ID_YES:
                    self.PluginRoot.SaveProject()
                    event.Skip()
                elif answer == wx.ID_NO:
                    event.Skip()
                    return
                else:
                    event.Veto()
                    return

        self.KillLocalRuntime()
        
        event.Skip()
    
    def OnMoveWindow(self, event):
        self.GetBestSize()
        self.RefreshScrollBars()
        event.Skip()
    
    def OnFrameActivated(self, event):
        if not event.GetActive() and self.PluginRoot is not None:
            self.PluginRoot.RefreshPluginsBlockLists()
    
    def OnPanelLeftDown(self, event):
        focused = self.FindFocus()
        if isinstance(focused, TextCtrlAutoComplete.TextCtrlAutoComplete):
            focused._showDropDown(False)
        event.Skip()
    
    def RefreshMainMenu(self):
        if self.PluginRoot is not None:
##            self.MenuBar.EnableTop(1, True)
##            self.MenuBar.EnableTop(2, True)
            self.FileMenu.Enable(wx.ID_SAVE, True)
            self.FileMenu.Enable(wx.ID_CLOSE_ALL, True)
            self.FileMenu.Enable(wx.ID_PROPERTIES, True)
        else:
##            self.MenuBar.EnableTop(1, False)
##            self.MenuBar.EnableTop(2, False)
            self.FileMenu.Enable(wx.ID_SAVE, False)
            self.FileMenu.Enable(wx.ID_CLOSE_ALL, False)
            self.FileMenu.Enable(wx.ID_PROPERTIES, False)

    def RefreshScrollBars(self):
        xstart, ystart = self.PLCConfig.GetViewStart()
        window_size = self.PLCConfig.GetClientSize()
        sizer = self.PLCConfig.GetSizer()
        if sizer:
            maxx, maxy = sizer.GetMinSize()
            self.PLCConfig.SetScrollbars(SCROLLBAR_UNIT, SCROLLBAR_UNIT, 
                maxx / SCROLLBAR_UNIT, maxy / SCROLLBAR_UNIT, 
                max(0, min(xstart, (maxx - window_size[0]) / SCROLLBAR_UNIT)), 
                max(0, min(ystart, (maxy - window_size[1]) / SCROLLBAR_UNIT)))

    def RefreshPLCParams(self):
        self.Freeze()
        self.ClearSizer(self.PLCParamsSizer)
        
        if self.PluginRoot is not None:    
            plcwindow = wx.Panel(self.PLCConfig, -1, size=wx.Size(-1, -1))
            if self.PluginRoot.PlugTestModified():
                bkgdclr = CHANGED_TITLE_COLOUR
            else:
                bkgdclr = TITLE_COLOUR
                
            if self.PluginRoot not in self.PluginInfos:
                self.PluginInfos[self.PluginRoot] = {"middle_visible" : False}
            
            plcwindow.SetBackgroundColour(TITLE_COLOUR)
            plcwindow.Bind(wx.EVT_LEFT_DOWN, self.OnPanelLeftDown)
            self.PLCParamsSizer.AddWindow(plcwindow, 0, border=0, flag=wx.GROW)
            
            plcwindowsizer = wx.BoxSizer(wx.HORIZONTAL)
            plcwindow.SetSizer(plcwindowsizer)
            
            st = wx.StaticText(plcwindow, -1)
            st.SetFont(wx.Font(faces["size"], wx.DEFAULT, wx.NORMAL, wx.BOLD, faceName = faces["helv"]))
            st.SetLabel(self.PluginRoot.GetProjectName())
            plcwindowsizer.AddWindow(st, 0, border=5, flag=wx.ALL|wx.ALIGN_CENTER)
            
            addbutton_id = wx.NewId()
            addbutton = wx.lib.buttons.GenBitmapButton(id=addbutton_id, bitmap=wx.Bitmap(Bpath( 'images', 'Add.png')),
                  name='AddPluginButton', parent=plcwindow, pos=wx.Point(0, 0),
                  size=wx.Size(16, 16), style=wx.NO_BORDER)
            addbutton.SetToolTipString(_("Add a sub plugin"))
            addbutton.Bind(wx.EVT_BUTTON, self.Gen_AddPluginMenu(self.PluginRoot), id=addbutton_id)
            plcwindowsizer.AddWindow(addbutton, 0, border=5, flag=wx.RIGHT|wx.ALIGN_CENTER)
    
            plcwindowmainsizer = wx.BoxSizer(wx.VERTICAL)
            plcwindowsizer.AddSizer(plcwindowmainsizer, 0, border=5, flag=wx.ALL)
            
            plcwindowbuttonsizer = wx.BoxSizer(wx.HORIZONTAL)
            plcwindowmainsizer.AddSizer(plcwindowbuttonsizer, 0, border=0, flag=wx.ALIGN_CENTER)
            
            msizer = self.GenerateMethodButtonSizer(self.PluginRoot, plcwindow, not self.PluginInfos[self.PluginRoot]["middle_visible"])
            plcwindowbuttonsizer.AddSizer(msizer, 0, border=0, flag=wx.GROW)
            
            paramswindow = wx.Panel(plcwindow, -1, size=wx.Size(-1, -1), style=wx.TAB_TRAVERSAL)
            paramswindow.SetBackgroundColour(TITLE_COLOUR)
            paramswindow.Bind(wx.EVT_LEFT_DOWN, self.OnPanelLeftDown)
            plcwindowbuttonsizer.AddWindow(paramswindow, 0, border=0, flag=0)
            
            psizer = wx.BoxSizer(wx.HORIZONTAL)
            paramswindow.SetSizer(psizer)
            
            plugin_infos = self.PluginRoot.GetParamsAttributes()
            self.RefreshSizerElement(paramswindow, psizer, self.PluginRoot, plugin_infos, None, False)
            
            if not self.PluginInfos[self.PluginRoot]["middle_visible"]:
                paramswindow.Hide()
            
            minimizebutton_id = wx.NewId()
            minimizebutton = wx.lib.buttons.GenBitmapToggleButton(id=minimizebutton_id, bitmap=wx.Bitmap(Bpath( 'images', 'Maximize.png')),
                  name='MinimizeButton', parent=plcwindow, pos=wx.Point(0, 0),
                  size=wx.Size(24, 24), style=wx.NO_BORDER)
            make_genbitmaptogglebutton_flat(minimizebutton)
            minimizebutton.SetBitmapSelected(wx.Bitmap(Bpath( 'images', 'Minimize.png')))
            minimizebutton.SetToggle(self.PluginInfos[self.PluginRoot]["middle_visible"])
            plcwindowbuttonsizer.AddWindow(minimizebutton, 0, border=5, flag=wx.ALL)
            
#            if len(self.PluginRoot.PlugChildsTypes) > 0:
#                addsizer = self.GenerateAddButtonSizer(self.PluginRoot, plcwindow)
#                plcwindowbuttonsizer.AddSizer(addsizer, 0, border=0, flag=0)
#            else:
#                addsizer = None

            def togglewindow(event):
                if minimizebutton.GetToggle():
                    paramswindow.Show()
                    msizer.SetCols(1)
#                    if addsizer is not None:
#                        addsizer.SetCols(1)
                else:
                    paramswindow.Hide()
                    msizer.SetCols(len(self.PluginRoot.PluginMethods))
#                    if addsizer is not None:
#                        addsizer.SetCols(len(self.PluginRoot.PlugChildsTypes))
                self.PluginInfos[self.PluginRoot]["middle_visible"] = minimizebutton.GetToggle()
                self.PLCConfigMainSizer.Layout()
                self.RefreshScrollBars()
                event.Skip()
            minimizebutton.Bind(wx.EVT_BUTTON, togglewindow, id=minimizebutton_id)
        
            self.PluginInfos[self.PluginRoot]["main"] = plcwindow
            self.PluginInfos[self.PluginRoot]["params"] = paramswindow
            
        self.PLCConfigMainSizer.Layout()
        self.RefreshScrollBars()
        self.Thaw()

#    def GenerateAddButtonSizer(self, plugin, parent, horizontal = True):
#        if horizontal:
#            addsizer = wx.FlexGridSizer(cols=len(plugin.PluginMethods))
#        else:
#            addsizer = wx.FlexGridSizer(cols=1)
#        for name, XSDClass, help in plugin.PlugChildsTypes:
#            addbutton_id = wx.NewId()
#            addbutton = wx.lib.buttons.GenButton(id=addbutton_id, label="Add %s"%help,
#                  name='AddPluginButton', parent=parent, pos=wx.Point(0, 0),
#                  style=wx.NO_BORDER)
#            font = addbutton.GetFont()
#            font.SetUnderlined(True)
#            addbutton.SetFont(font)
#            addbutton._GetLabelSize = gen_textbutton_GetLabelSize(addbutton)
#            addbutton.SetForegroundColour(wx.BLUE)
#            addbutton.SetToolTipString("Add a \"%s\" plugin to this one"%name)
#            addbutton.Bind(wx.EVT_BUTTON, self._GetAddPluginFunction(name, plugin), id=addbutton_id)
#            addsizer.AddWindow(addbutton, 0, border=0, flag=0)
#        return addsizer

    normal_bt_font=wx.Font(faces["size"] / 3, wx.DEFAULT, wx.NORMAL, wx.NORMAL, faceName = faces["helv"])
    mouseover_bt_font=wx.Font(faces["size"] / 3, wx.DEFAULT, wx.NORMAL, wx.NORMAL, underline=True, faceName = faces["helv"])
    def GenerateMethodButtonSizer(self, plugin, parent, horizontal = True):
        if horizontal:
            msizer = wx.FlexGridSizer(cols=len(plugin.PluginMethods))
        else:
            msizer = wx.FlexGridSizer(cols=1)
        for plugin_method in plugin.PluginMethods:
            if "method" in plugin_method and plugin_method.get("shown",True):
                id = wx.NewId()
                label = plugin_method["name"]
                button = GenBitmapTextButton(id=id, parent=parent,
                    bitmap=wx.Bitmap(Bpath( "%s.png"%plugin_method.get("bitmap", os.path.join("images", "Unknown")))), label=label, 
                    name=label, pos=wx.DefaultPosition, style=wx.NO_BORDER)
                button.SetFont(self.normal_bt_font)
                button.SetToolTipString(plugin_method["tooltip"])
                button.Bind(wx.EVT_BUTTON, self.GetButtonCallBackFunction(plugin, plugin_method["method"]), id=id)
                # a fancy underline on mouseover
                def setFontStyle(b, s):
                    def fn(event):
                        b.SetFont(s)
                        b.Refresh()
                        event.Skip()
                    return fn
                button.Bind(wx.EVT_ENTER_WINDOW, setFontStyle(button, self.mouseover_bt_font))
                button.Bind(wx.EVT_LEAVE_WINDOW, setFontStyle(button, self.normal_bt_font))
                #hack to force size to mini
                if not plugin_method.get("enabled",True):
                    button.Disable()
                msizer.AddWindow(button, 0, border=0, flag=wx.ALIGN_CENTER)
        return msizer

    def RefreshPluginTree(self):
        self.Freeze()
        self.ClearSizer(self.PluginTreeSizer)
        if self.PluginRoot is not None:
            for child in self.PluginRoot.IECSortedChilds():
                self.GenerateTreeBranch(child)
                if not self.PluginInfos[child]["expanded"]:
                    self.CollapsePlugin(child)
        self.PLCConfigMainSizer.Layout()
        self.RefreshScrollBars()
        self.Thaw()

    def SetPluginParamsAttribute(self, plugin, *args, **kwargs):
        res, StructChanged = plugin.SetParamsAttribute(*args, **kwargs)
        if StructChanged:
            wx.CallAfter(self.RefreshPluginTree)
        else:
            if plugin == self.PluginRoot:
                bkgdclr = CHANGED_TITLE_COLOUR
                items = ["main", "params"]
            else:
                bkgdclr = CHANGED_WINDOW_COLOUR
                items = ["left", "middle", "params"]
            for i in items:
                self.PluginInfos[plugin][i].SetBackgroundColour(bkgdclr)
                self.PluginInfos[plugin][i].Refresh()
        return res

    def ExpandPlugin(self, plugin, force = False):
        for child in self.PluginInfos[plugin]["children"]:
            self.PluginInfos[child]["left"].Show()
            self.PluginInfos[child]["middle"].Show()
#            self.PluginTreeSizer.Show(self.PluginInfos[child]["right"])
            if force or not self.PluginInfos[child]["expanded"]:
                self.ExpandPlugin(child, force)
                if force:
                    self.PluginInfos[child]["expanded"] = True
    
    def CollapsePlugin(self, plugin, force = False):
        for child in self.PluginInfos[plugin]["children"]:
            self.PluginInfos[child]["left"].Hide()
            self.PluginInfos[child]["middle"].Hide()
#            self.PluginTreeSizer.Hide(self.PluginInfos[child]["right"])
            if force or self.PluginInfos[child]["expanded"]:
                self.CollapsePlugin(child, force)
                if force:
                    self.PluginInfos[child]["expanded"] = False

    def GenerateTreeBranch(self, plugin):
        leftwindow = wx.Panel(self.PLCConfig, -1, size=wx.Size(-1, -1))
        if plugin.PlugTestModified():
            bkgdclr=CHANGED_WINDOW_COLOUR
        else:
            bkgdclr=WINDOW_COLOUR

        leftwindow.SetBackgroundColour(bkgdclr)
        
        if plugin not in self.PluginInfos:
            self.PluginInfos[plugin] = {"expanded" : False, "left_visible" : False, "middle_visible" : False}
            
        self.PluginInfos[plugin]["children"] = plugin.IECSortedChilds()
        
        self.PluginTreeSizer.AddWindow(leftwindow, 0, border=0, flag=wx.GROW)
        
        leftwindowsizer = wx.FlexGridSizer(cols=1, rows=3)
        leftwindowsizer.AddGrowableCol(0)
        leftwindowsizer.AddGrowableRow(2)
        leftwindow.SetSizer(leftwindowsizer)
        
        leftbuttonmainsizer = wx.FlexGridSizer(cols=3, rows=1)
        leftbuttonmainsizer.AddGrowableCol(0)
        leftwindowsizer.AddSizer(leftbuttonmainsizer, 0, border=5, flag=wx.GROW|wx.LEFT|wx.RIGHT) #|wx.TOP
        
        leftbuttonsizer = wx.BoxSizer(wx.HORIZONTAL)
        leftbuttonmainsizer.AddSizer(leftbuttonsizer, 0, border=5, flag=wx.GROW|wx.RIGHT)
        
        leftsizer = wx.BoxSizer(wx.VERTICAL)
        leftbuttonsizer.AddSizer(leftsizer, 0, border=5, flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)

        rolesizer = wx.BoxSizer(wx.HORIZONTAL)
        leftsizer.AddSizer(rolesizer, 0, border=0, flag=wx.GROW|wx.RIGHT)

        enablebutton_id = wx.NewId()
        enablebutton = wx.lib.buttons.GenBitmapToggleButton(id=enablebutton_id, bitmap=wx.Bitmap(Bpath( 'images', 'Disabled.png')),
              name='EnableButton', parent=leftwindow, size=wx.Size(16, 16), pos=wx.Point(0, 0), style=0)#wx.NO_BORDER)
        enablebutton.SetToolTipString(_("Enable/Disable this plugin"))
        make_genbitmaptogglebutton_flat(enablebutton)
        enablebutton.SetBitmapSelected(wx.Bitmap(Bpath( 'images', 'Enabled.png')))
        enablebutton.SetToggle(plugin.MandatoryParams[1].getEnabled())
        def toggleenablebutton(event):
            res = self.SetPluginParamsAttribute(plugin, "BaseParams.Enabled", enablebutton.GetToggle())
            enablebutton.SetToggle(res)
            event.Skip()
        enablebutton.Bind(wx.EVT_BUTTON, toggleenablebutton, id=enablebutton_id)
        rolesizer.AddWindow(enablebutton, 0, border=0, flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)

        roletext = wx.StaticText(leftwindow, -1)
        roletext.SetLabel(plugin.PlugHelp)
        rolesizer.AddWindow(roletext, 0, border=5, flag=wx.RIGHT|wx.ALIGN_LEFT)
        
        plugin_IECChannel = plugin.BaseParams.getIEC_Channel()
        
        iecsizer = wx.BoxSizer(wx.HORIZONTAL)
        leftsizer.AddSizer(iecsizer, 0, border=5, flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)

        st = wx.StaticText(leftwindow, -1)
        st.SetFont(wx.Font(faces["size"], wx.DEFAULT, wx.NORMAL, wx.BOLD, faceName = faces["helv"]))
        st.SetLabel(plugin.GetFullIEC_Channel())
        iecsizer.AddWindow(st, 0, border=0, flag=0)

        updownsizer = wx.BoxSizer(wx.VERTICAL)
        iecsizer.AddSizer(updownsizer, 0, border=5, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL)

        if plugin_IECChannel > 0:
            ieccdownbutton_id = wx.NewId()
            ieccdownbutton = wx.lib.buttons.GenBitmapButton(id=ieccdownbutton_id, bitmap=wx.Bitmap(Bpath( 'images', 'IECCDown.png')),
                  name='IECCDownButton', parent=leftwindow, pos=wx.Point(0, 0),
                  size=wx.Size(16, 16), style=wx.NO_BORDER)
            ieccdownbutton.Bind(wx.EVT_BUTTON, self.GetItemChannelChangedFunction(plugin, plugin_IECChannel - 1), id=ieccdownbutton_id)
            updownsizer.AddWindow(ieccdownbutton, 0, border=0, flag=wx.ALIGN_LEFT)

        ieccupbutton_id = wx.NewId()
        ieccupbutton = wx.lib.buttons.GenBitmapTextButton(id=ieccupbutton_id, bitmap=wx.Bitmap(Bpath( 'images', 'IECCUp.png')),
              name='IECCUpButton', parent=leftwindow, pos=wx.Point(0, 0),
              size=wx.Size(16, 16), style=wx.NO_BORDER)
        ieccupbutton.Bind(wx.EVT_BUTTON, self.GetItemChannelChangedFunction(plugin, plugin_IECChannel + 1), id=ieccupbutton_id)
        updownsizer.AddWindow(ieccupbutton, 0, border=0, flag=wx.ALIGN_LEFT)

        adddeletesizer = wx.BoxSizer(wx.VERTICAL)
        iecsizer.AddSizer(adddeletesizer, 0, border=5, flag=wx.LEFT|wx.ALIGN_CENTER_VERTICAL)

        deletebutton_id = wx.NewId()
        deletebutton = wx.lib.buttons.GenBitmapButton(id=deletebutton_id, bitmap=wx.Bitmap(Bpath( 'images', 'Delete.png')),
              name='DeletePluginButton', parent=leftwindow, pos=wx.Point(0, 0),
              size=wx.Size(16, 16), style=wx.NO_BORDER)
        deletebutton.SetToolTipString(_("Delete this plugin"))
        deletebutton.Bind(wx.EVT_BUTTON, self.GetDeleteButtonFunction(plugin), id=deletebutton_id)
        adddeletesizer.AddWindow(deletebutton, 0, border=5, flag=wx.RIGHT|wx.ALIGN_CENTER)

        if len(plugin.PlugChildsTypes) > 0:
            addbutton_id = wx.NewId()
            addbutton = wx.lib.buttons.GenBitmapButton(id=addbutton_id, bitmap=wx.Bitmap(Bpath( 'images', 'Add.png')),
                  name='AddPluginButton', parent=leftwindow, pos=wx.Point(0, 0),
                  size=wx.Size(16, 16), style=wx.NO_BORDER)
            addbutton.SetToolTipString(_("Add a sub plugin"))
            addbutton.Bind(wx.EVT_BUTTON, self.Gen_AddPluginMenu(plugin), id=addbutton_id)
            adddeletesizer.AddWindow(addbutton, 0, border=5, flag=wx.RIGHT|wx.ALIGN_CENTER)
        
        expandbutton_id = wx.NewId()
        expandbutton = wx.lib.buttons.GenBitmapToggleButton(id=expandbutton_id, bitmap=wx.Bitmap(Bpath( 'images', 'plus.png')),
              name='ExpandButton', parent=leftwindow, pos=wx.Point(0, 0),
              size=wx.Size(13, 13), style=wx.NO_BORDER)
        expandbutton.labelDelta = 0
        expandbutton.SetBezelWidth(0)
        expandbutton.SetUseFocusIndicator(False)
        expandbutton.SetBitmapSelected(wx.Bitmap(Bpath( 'images', 'minus.png')))
        expandbutton.SetToggle(self.PluginInfos[plugin]["expanded"])
            
        if len(self.PluginInfos[plugin]["children"]) > 0:
            def togglebutton(event):
                if expandbutton.GetToggle():
                    self.ExpandPlugin(plugin)
                else:
                    self.CollapsePlugin(plugin)
                self.PluginInfos[plugin]["expanded"] = expandbutton.GetToggle()
                self.PLCConfigMainSizer.Layout()
                self.RefreshScrollBars()
                event.Skip()
            expandbutton.Bind(wx.EVT_BUTTON, togglebutton, id=expandbutton_id)
        else:
            expandbutton.Enable(False)
        iecsizer.AddWindow(expandbutton, 0, border=5, flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
        
        tc_id = wx.NewId()
        tc = wx.TextCtrl(leftwindow, tc_id, size=wx.Size(150, 25), style=wx.NO_BORDER)
        tc.SetFont(wx.Font(faces["size"] * 0.75, wx.DEFAULT, wx.NORMAL, wx.BOLD, faceName = faces["helv"]))
        tc.ChangeValue(plugin.MandatoryParams[1].getName())
        tc.Bind(wx.EVT_TEXT, self.GetTextCtrlCallBackFunction(tc, plugin, "BaseParams.Name"), id=tc_id)
        iecsizer.AddWindow(tc, 0, border=5, flag=wx.RIGHT|wx.ALIGN_CENTER_VERTICAL)
       

        leftminimizebutton_id = wx.NewId()
        leftminimizebutton = wx.lib.buttons.GenBitmapToggleButton(id=leftminimizebutton_id, bitmap=wx.Bitmap(Bpath( 'images', 'ShowVars.png')),
              name='MinimizeButton', parent=leftwindow, pos=wx.Point(0, 0),
              size=wx.Size(24, 24), style=wx.NO_BORDER)
        make_genbitmaptogglebutton_flat(leftminimizebutton)
        leftminimizebutton.SetBitmapSelected(wx.Bitmap(Bpath( 'images', 'HideVars.png')))
        leftminimizebutton.SetToggle(self.PluginInfos[plugin]["left_visible"])
        def toggleleftwindow(event):
            if leftminimizebutton.GetToggle():
                leftwindowsizer.Show(1)
            else:
                leftwindowsizer.Hide(1)
            self.PluginInfos[plugin]["left_visible"] = leftminimizebutton.GetToggle()
            self.PLCConfigMainSizer.Layout()
            self.RefreshScrollBars()
            event.Skip()
        leftminimizebutton.Bind(wx.EVT_BUTTON, toggleleftwindow, id=leftminimizebutton_id)
        leftbuttonmainsizer.AddWindow(leftminimizebutton, 0, border=5, flag=wx.RIGHT|wx.ALIGN_CENTER)

        locations = plugin.GetLocations()
        lb = wx.ListBox(leftwindow, -1, size=wx.Size(-1, max(1, min(len(locations), 4)) * 25), style=wx.NO_BORDER)
        for location in locations:
            lb.Append(location["NAME"].replace("__", "%").replace("_", "."))
        if not self.PluginInfos[plugin]["left_visible"]:
            lb.Hide()
        self.PluginInfos[plugin]["variable_list"] = lb
        leftwindowsizer.AddWindow(lb, 0, border=5, flag=wx.GROW|wx.LEFT|wx.RIGHT|wx.BOTTOM)

        middlewindow = wx.Panel(self.PLCConfig, -1, size=wx.Size(-1, -1))
        middlewindow.SetBackgroundColour(bkgdclr)
        
        self.PluginTreeSizer.AddWindow(middlewindow, 0, border=0, flag=wx.GROW)
        
        middlewindowmainsizer = wx.BoxSizer(wx.VERTICAL)
        middlewindow.SetSizer(middlewindowmainsizer)
        
        middlewindowsizer = wx.FlexGridSizer(cols=2, rows=1)
        middlewindowsizer.AddGrowableCol(1)
        middlewindowsizer.AddGrowableRow(0)
        middlewindowmainsizer.AddSizer(middlewindowsizer, 0, border=8, flag=wx.TOP|wx.GROW)
        
        msizer = self.GenerateMethodButtonSizer(plugin, middlewindow, not self.PluginInfos[plugin]["middle_visible"])
        middlewindowsizer.AddSizer(msizer, 0, border=0, flag=wx.GROW)
        
        middleparamssizer = wx.BoxSizer(wx.HORIZONTAL)
        middlewindowsizer.AddSizer(middleparamssizer, 0, border=0, flag=wx.ALIGN_RIGHT)
        
        paramswindow = wx.Panel(middlewindow, -1, size=wx.Size(-1, -1))
        paramswindow.SetBackgroundColour(bkgdclr)
        
        psizer = wx.BoxSizer(wx.HORIZONTAL)
        paramswindow.SetSizer(psizer)
        self.PluginInfos[plugin]["params"] = paramswindow
        
        middleparamssizer.AddWindow(paramswindow, 0, border=5, flag=wx.ALL)
        
        plugin_infos = plugin.GetParamsAttributes()
        self.RefreshSizerElement(paramswindow, psizer, plugin, plugin_infos, None, False)
        
        if not self.PluginInfos[plugin]["middle_visible"]:
            paramswindow.Hide()
        
        middleminimizebutton_id = wx.NewId()
        middleminimizebutton = wx.lib.buttons.GenBitmapToggleButton(id=middleminimizebutton_id, bitmap=wx.Bitmap(Bpath( 'images', 'Maximize.png')),
              name='MinimizeButton', parent=middlewindow, pos=wx.Point(0, 0),
              size=wx.Size(24, 24), style=wx.NO_BORDER)
        make_genbitmaptogglebutton_flat(middleminimizebutton)
        middleminimizebutton.SetBitmapSelected(wx.Bitmap(Bpath( 'images', 'Minimize.png')))
        middleminimizebutton.SetToggle(self.PluginInfos[plugin]["middle_visible"])
        middleparamssizer.AddWindow(middleminimizebutton, 0, border=5, flag=wx.ALL)
        
#        rightwindow = wx.Panel(self.PLCConfig, -1, size=wx.Size(-1, -1))
#        rightwindow.SetBackgroundColour(wx.Colour(240,240,240))
#        
#        self.PluginTreeSizer.AddWindow(rightwindow, 0, border=0, flag=wx.GROW)
#        
#        rightsizer = wx.BoxSizer(wx.VERTICAL)
#        rightwindow.SetSizer(rightsizer)
#        
#        rightmainsizer = wx.BoxSizer(wx.VERTICAL)
#        rightsizer.AddSizer(rightmainsizer, 0, border=5, flag=wx.ALL)
#        
#        if len(plugin.PlugChildsTypes) > 0:
#            addsizer = self.GenerateAddButtonSizer(plugin, rightwindow)
#            rightmainsizer.AddSizer(addsizer, 0, border=4, flag=wx.TOP)
#        else:
#            addsizer = None
            
        def togglemiddlerightwindow(event):
            if middleminimizebutton.GetToggle():
                middleparamssizer.Show(0)
                msizer.SetCols(1)
#                if addsizer is not None:
#                    addsizer.SetCols(1)
            else:
                middleparamssizer.Hide(0)
                msizer.SetCols(len(plugin.PluginMethods))
#                if addsizer is not None:
#                    addsizer.SetCols(len(plugin.PlugChildsTypes))
            self.PluginInfos[plugin]["middle_visible"] = middleminimizebutton.GetToggle()
            self.PLCConfigMainSizer.Layout()
            self.RefreshScrollBars()
            event.Skip()
        middleminimizebutton.Bind(wx.EVT_BUTTON, togglemiddlerightwindow, id=middleminimizebutton_id)
        
        self.PluginInfos[plugin]["left"] = leftwindow
        self.PluginInfos[plugin]["middle"] = middlewindow
#        self.PluginInfos[plugin]["right"] = rightwindow
        for child in self.PluginInfos[plugin]["children"]:
            self.GenerateTreeBranch(child)
            if not self.PluginInfos[child]["expanded"]:
                self.CollapsePlugin(child)

    def RefreshVariableLists(self):
        for plugin, infos in self.PluginInfos.items():
            locations = plugin.GetLocations()
            infos["variable_list"].SetSize(wx.Size(-1, max(1, min(len(locations), 4)) * 25))
            infos["variable_list"].Clear()
            for location in locations:
                infos["variable_list"].Append(location["NAME"].replace("__", "%").replace("_", "."))
        self.PLCConfigMainSizer.Layout()
        self.RefreshScrollBars()
        
    def RefreshAll(self):
        self.RefreshPLCParams()
        self.RefreshPluginTree()
        
    def GetItemChannelChangedFunction(self, plugin, value):
        def OnPluginTreeItemChannelChanged(event):
            res = self.SetPluginParamsAttribute(plugin, "BaseParams.IEC_Channel", value)
            event.Skip()
        return OnPluginTreeItemChannelChanged
    
    def _GetAddPluginFunction(self, name, plugin):
        def OnPluginMenu(event):
            wx.CallAfter(self.AddPlugin, name, plugin)
            event.Skip()
        return OnPluginMenu
    
    def Gen_AddPluginMenu(self, plugin):
        def AddPluginMenu(event):
            main_menu = wx.Menu(title='')
            if len(plugin.PlugChildsTypes) > 0:
                for name, XSDClass, help in plugin.PlugChildsTypes:
                    new_id = wx.NewId()
                    main_menu.Append(help=help, id=new_id, kind=wx.ITEM_NORMAL, text=_("Append ")+help)
                    self.Bind(wx.EVT_MENU, self._GetAddPluginFunction(name, plugin), id=new_id)
            self.PopupMenuXY(main_menu)
            event.Skip()
        return AddPluginMenu
    
    def GetButtonCallBackFunction(self, plugin, method):
        """ Generate the callbackfunc for a given plugin method"""
        def OnButtonClick(event):
            # Disable button to prevent re-entrant call 
            event.GetEventObject().Disable()
            # Call
            getattr(plugin,method)()
            # Re-enable button 
            event.GetEventObject().Enable()
            # Trigger refresh on Idle
            wx.CallAfter(self.RefreshAll)
            event.Skip()
        return OnButtonClick
    
    def GetChoiceCallBackFunction(self, choicectrl, plugin, path):
        def OnChoiceChanged(event):
            res = self.SetPluginParamsAttribute(plugin, path, choicectrl.GetStringSelection())
            choicectrl.SetStringSelection(res)
            event.Skip()
        return OnChoiceChanged
    
    def GetChoiceContentCallBackFunction(self, choicectrl, staticboxsizer, plugin, path):
        def OnChoiceContentChanged(event):
            res = self.SetPluginParamsAttribute(plugin, path, choicectrl.GetStringSelection())
            if wx.VERSION < (2, 8, 0):
                self.ParamsPanel.Freeze()
                choicectrl.SetStringSelection(res)
                infos = self.PluginRoot.GetParamsAttributes(path)
                staticbox = staticboxsizer.GetStaticBox()
                staticbox.SetLabel("%(name)s - %(value)s"%infos)
                self.RefreshSizerElement(self.ParamsPanel, staticboxsizer, infos["children"], "%s.%s"%(path, infos["name"]), selected=selected)
                self.ParamsPanelMainSizer.Layout()
                self.ParamsPanel.Thaw()
                self.ParamsPanel.Refresh()
            else:
                wx.CallAfter(self.RefreshAll)
            event.Skip()
        return OnChoiceContentChanged
    
    def GetTextCtrlCallBackFunction(self, textctrl, plugin, path):
        def OnTextCtrlChanged(event):
            res = self.SetPluginParamsAttribute(plugin, path, textctrl.GetValue())
            if res != textctrl.GetValue():
                textctrl.ChangeValue(res)
            event.Skip()
        return OnTextCtrlChanged
    
    def GetCheckBoxCallBackFunction(self, chkbx, plugin, path):
        def OnCheckBoxChanged(event):
            res = self.SetPluginParamsAttribute(plugin, path, chkbx.IsChecked())
            chkbx.SetValue(res)
            event.Skip()
        return OnCheckBoxChanged
    
    def ClearSizer(self, sizer):
        staticboxes = []
        for item in sizer.GetChildren():
            if item.IsSizer():
                item_sizer = item.GetSizer()
                self.ClearSizer(item_sizer)
                if isinstance(item_sizer, wx.StaticBoxSizer):
                    staticboxes.append(item_sizer.GetStaticBox())
        sizer.Clear(True)
        for staticbox in staticboxes:
            staticbox.Destroy()
                
    def RefreshSizerElement(self, parent, sizer, plugin, elements, path, clean = True):
        if clean:
            if wx.VERSION < (2, 8, 0):
                self.ClearSizer(sizer)
            else:
                sizer.Clear(True)
        first = True
        for element_infos in elements:
            if path:
                element_path = "%s.%s"%(path, element_infos["name"])
            else:
                element_path = element_infos["name"]
            if element_infos["type"] == "element":
                label = element_infos["name"]
                staticbox = wx.StaticBox(id=-1, label=_(label), 
                    name='%s_staticbox'%element_infos["name"], parent=parent,
                    pos=wx.Point(0, 0), size=wx.Size(10, 0), style=0)
                staticboxsizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
                if first:
                    sizer.AddSizer(staticboxsizer, 0, border=0, flag=wx.GROW|wx.TOP)
                else:
                    sizer.AddSizer(staticboxsizer, 0, border=0, flag=wx.GROW)
                self.RefreshSizerElement(parent, staticboxsizer, plugin, element_infos["children"], element_path)
            else:
                boxsizer = wx.FlexGridSizer(cols=3, rows=1)
                boxsizer.AddGrowableCol(1)
                if first:
                    sizer.AddSizer(boxsizer, 0, border=5, flag=wx.GROW|wx.ALL)
                else:
                    sizer.AddSizer(boxsizer, 0, border=5, flag=wx.GROW|wx.LEFT|wx.RIGHT|wx.BOTTOM)
                staticbitmap = GenStaticBitmap(ID=-1, bitmapname="%s.png"%element_infos["name"],
                    name="%s_bitmap"%element_infos["name"], parent=parent,
                    pos=wx.Point(0, 0), size=wx.Size(24, 24), style=0)
                boxsizer.AddWindow(staticbitmap, 0, border=5, flag=wx.RIGHT)
                label = element_infos["name"]
                statictext = wx.StaticText(id=-1, label="%s:"%_(label), 
                    name="%s_label"%element_infos["name"], parent=parent, 
                    pos=wx.Point(0, 0), size=wx.DefaultSize, style=0)
                boxsizer.AddWindow(statictext, 0, border=5, flag=wx.ALIGN_CENTER_VERTICAL|wx.RIGHT)
                id = wx.NewId()
                if isinstance(element_infos["type"], types.ListType):
                    combobox = wx.ComboBox(id=id, name=element_infos["name"], parent=parent, 
                        pos=wx.Point(0, 0), size=wx.Size(150, 28), style=wx.CB_READONLY)
                    boxsizer.AddWindow(combobox, 0, border=0, flag=0)
                    if element_infos["use"] == "optional":
                        combobox.Append("")
                    if len(element_infos["type"]) > 0 and isinstance(element_infos["type"][0], types.TupleType):
                        for choice, xsdclass in element_infos["type"]:
                            combobox.Append(choice)
                        name = element_infos["name"]
                        value = element_infos["value"]
                        staticbox = wx.StaticBox(id=-1, label="%s - %s"%(_(name), _(value)), 
                            name='%s_staticbox'%element_infos["name"], parent=parent,
                            pos=wx.Point(0, 0), size=wx.Size(10, 0), style=0)
                        staticboxsizer = wx.StaticBoxSizer(staticbox, wx.VERTICAL)
                        sizer.AddSizer(staticboxsizer, 0, border=5, flag=wx.GROW|wx.BOTTOM)
                        self.RefreshSizerElement(parent, staticboxsizer, plugin, element_infos["children"], element_path)
                        callback = self.GetChoiceContentCallBackFunction(combobox, staticboxsizer, plugin, element_path)
                    else:
                        for choice in element_infos["type"]:
                            combobox.Append(choice)
                        callback = self.GetChoiceCallBackFunction(combobox, plugin, element_path)
                    if element_infos["value"] is None:
                        combobox.SetStringSelection("")
                    else:
                        combobox.SetStringSelection(element_infos["value"])
                    combobox.Bind(wx.EVT_COMBOBOX, callback, id=id)
                elif isinstance(element_infos["type"], types.DictType):
                    scmin = -(2**31)
                    scmax = 2**31-1
                    if "min" in element_infos["type"]:
                        scmin = element_infos["type"]["min"]
                    if "max" in element_infos["type"]:
                        scmax = element_infos["type"]["max"]
                    spinctrl = wx.SpinCtrl(id=id, name=element_infos["name"], parent=parent, 
                        pos=wx.Point(0, 0), size=wx.Size(150, 25), style=wx.SP_ARROW_KEYS|wx.ALIGN_RIGHT)
                    spinctrl.SetRange(scmin,scmax)
                    boxsizer.AddWindow(spinctrl, 0, border=0, flag=0)
                    spinctrl.SetValue(element_infos["value"])
                    spinctrl.Bind(wx.EVT_SPINCTRL, self.GetTextCtrlCallBackFunction(spinctrl, plugin, element_path), id=id)
                else:
                    if element_infos["type"] == "boolean":
                        checkbox = wx.CheckBox(id=id, name=element_infos["name"], parent=parent, 
                            pos=wx.Point(0, 0), size=wx.Size(17, 25), style=0)
                        boxsizer.AddWindow(checkbox, 0, border=0, flag=0)
                        checkbox.SetValue(element_infos["value"])
                        checkbox.Bind(wx.EVT_CHECKBOX, self.GetCheckBoxCallBackFunction(checkbox, plugin, element_path), id=id)
                    elif element_infos["type"] in ["unsignedLong", "long","integer"]:
                        if element_infos["type"].startswith("unsigned"):
                            scmin = 0
                        else:
                            scmin = -(2**31)
                        scmax = 2**31-1
                        spinctrl = wx.SpinCtrl(id=id, name=element_infos["name"], parent=parent, 
                            pos=wx.Point(0, 0), size=wx.Size(150, 25), style=wx.SP_ARROW_KEYS|wx.ALIGN_RIGHT)
                        spinctrl.SetRange(scmin, scmax)
                        boxsizer.AddWindow(spinctrl, 0, border=0, flag=0)
                        spinctrl.SetValue(element_infos["value"])
                        spinctrl.Bind(wx.EVT_SPINCTRL, self.GetTextCtrlCallBackFunction(spinctrl, plugin, element_path), id=id)
                    else:
                        choices = cPickle.loads(str(config.Read(element_path, cPickle.dumps([""]))))                           
                        textctrl = TextCtrlAutoComplete.TextCtrlAutoComplete(id=id, 
                                                                     name=element_infos["name"], 
                                                                     parent=parent, 
                                                                     choices=choices, 
                                                                     element_path=element_path,
                                                                     pos=wx.Point(0, 0), 
                                                                     size=wx.Size(150, 25), 
                                                                     style=0)
                        
                        boxsizer.AddWindow(textctrl, 0, border=0, flag=0)
                        textctrl.ChangeValue(str(element_infos["value"]))
                        textctrl.Bind(wx.EVT_TEXT, self.GetTextCtrlCallBackFunction(textctrl, plugin, element_path))
            first = False
    
    def OnNewProjectMenu(self, event):
        if not config.HasEntry("lastopenedfolder"):
            defaultpath = os.path.expanduser("~")
        else:
            defaultpath = config.Read("lastopenedfolder")
        
        dialog = wx.DirDialog(self , _("Choose a project"), defaultpath, wx.DD_NEW_DIR_BUTTON)
        if dialog.ShowModal() == wx.ID_OK:
            projectpath = dialog.GetPath()
            dialog.Destroy()
            config.Write("lastopenedfolder", os.path.dirname(projectpath))
            config.Flush()
            self.PluginInfos = {}
            if self.PluginRoot is not None:
                self.PluginRoot.CloseProject()
            self.PluginRoot = PluginsRoot(self, self.Log)
            res = self.PluginRoot.NewProject(projectpath)
            if not res :
                self.RefreshAll()
                self.RefreshMainMenu()
            else:
                message = wx.MessageDialog(self, res, _("ERROR"), wx.OK|wx.ICON_ERROR)
                message.ShowModal()
                message.Destroy()
        event.Skip()
    
    def OnOpenProjectMenu(self, event):
        if not config.HasEntry("lastopenedfolder"):
            defaultpath = os.path.expanduser("~")
        else:
            defaultpath = config.Read("lastopenedfolder")
        
        dialog = wx.DirDialog(self , _("Choose a project"), defaultpath, wx.DD_NEW_DIR_BUTTON)
        if dialog.ShowModal() == wx.ID_OK:
            projectpath = dialog.GetPath()
            if os.path.isdir(projectpath):
                config.Write("lastopenedfolder", os.path.dirname(projectpath))
                config.Flush()
                self.PluginInfos = {}
                if self.PluginRoot is not None:
                    self.PluginRoot.CloseProject()
                self.PluginRoot = PluginsRoot(self, self.Log)
                result = self.PluginRoot.LoadProject(projectpath)
                if not result:
                    self.RefreshAll()
                    self.RefreshMainMenu()
                else:
                    message = wx.MessageDialog(self, result, _("Error"), wx.OK|wx.ICON_ERROR)
                    message.ShowModal()
                    message.Destroy()
            else:
                message = wx.MessageDialog(self, _("\"%s\" folder is not a valid Beremiz project\n")%projectpath, _("Error"), wx.OK|wx.ICON_ERROR)
                message.ShowModal()
                message.Destroy()
        dialog.Destroy()
        event.Skip()
    
    def OnCloseProjectMenu(self, event):
        if self.PluginRoot is not None:
            if self.PluginRoot.ProjectTestModified():
                dialog = wx.MessageDialog(self,
                                          _("Save changes ?"),
                                          _("Close Application"), 
                                          wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
                answer = dialog.ShowModal()
                dialog.Destroy()
                if answer == wx.ID_YES:
                    self.PluginRoot.SaveProject()
                elif answer == wx.ID_CANCEL:
                    return
            self.PluginInfos = {}
            self.PluginRoot.CloseProject()
            self.PluginRoot = None
            self.Log.flush()
            self.RefreshAll()
            self.RefreshMainMenu()
        event.Skip()
    
    def OnSaveProjectMenu(self, event):
        if self.PluginRoot is not None:
            self.PluginRoot.SaveProject()
            self.RefreshAll()
        event.Skip()
    
    def OnPropertiesMenu(self, event):
        event.Skip()
    
    def OnQuitMenu(self, event):
        self.Close()
        event.Skip()
    
    def OnEditPLCMenu(self, event):
        self.EditPLC()
        event.Skip()
    
    def OnAddMenu(self, event):
        self.AddPlugin()
        event.Skip()
    
    def OnDeleteMenu(self, event):
        self.DeletePlugin()
        event.Skip()

    def OnBuildMenu(self, event):
        #self.BuildAutom()
        event.Skip()

    def OnSimulateMenu(self, event):
        event.Skip()
    
    def OnRunMenu(self, event):
        event.Skip()
    
    def OnSaveLogMenu(self, event):
        event.Skip()
    
    def OnBeremizMenu(self, event):
        open_pdf(Bpath( "doc", "manual_beremiz.pdf"))
        event.Skip()
    
    def OnAboutMenu(self, event):
        OpenHtmlFrame(self,_("About Beremiz"), Bpath("doc","about.html"), wx.Size(550, 500))
        event.Skip()
    
    def OnAddButton(self, event):
        PluginType = self.PluginChilds.GetStringSelection()
        if PluginType != "":
            self.AddPlugin(PluginType)
        event.Skip()
    
    def OnDeleteButton(self, event):
        self.DeletePlugin()
        event.Skip()
    
    def GetAddButtonFunction(self, plugin, window):
        def AddButtonFunction(event):
            if plugin and len(plugin.PlugChildsTypes) > 0:
                plugin_menu = wx.Menu(title='')
                for name, XSDClass, help in plugin.PlugChildsTypes:
                    new_id = wx.NewId()
                    plugin_menu.Append(help=help, id=new_id, kind=wx.ITEM_NORMAL, text=name)
                    self.Bind(wx.EVT_MENU, self._GetAddPluginFunction(name, plugin), id=new_id)
                window_pos = window.GetPosition()
                wx.CallAfter(self.PLCConfig.PopupMenu, plugin_menu)
            event.Skip()
        return AddButtonFunction
    
    def GetDeleteButtonFunction(self, plugin):
        def DeleteButtonFunction(event):
            wx.CallAfter(self.DeletePlugin, plugin)
            event.Skip()
        return DeleteButtonFunction
    
    def AddPlugin(self, PluginType, plugin):
        dialog = wx.TextEntryDialog(self, _("Please enter a name for plugin:"), _("Add Plugin"), "", wx.OK|wx.CANCEL)
        if dialog.ShowModal() == wx.ID_OK:
            PluginName = dialog.GetValue()
            plugin.PlugAddChild(PluginName, PluginType)
            self.RefreshPluginTree()
        dialog.Destroy()
    
    def DeletePlugin(self, plugin):
        dialog = wx.MessageDialog(self, _("Really delete plugin ?"), _("Remove plugin"), wx.YES_NO|wx.NO_DEFAULT)
        if dialog.ShowModal() == wx.ID_YES:
            self.PluginInfos.pop(plugin)
            plugin.PlugRemove()
            del plugin
            self.RefreshPluginTree()
        dialog.Destroy()

#-------------------------------------------------------------------------------
#                               Exception Handler
#-------------------------------------------------------------------------------

Max_Traceback_List_Size = 20

def Display_Exception_Dialog(e_type, e_value, e_tb, bug_report_path):
    trcbck_lst = []
    for i,line in enumerate(traceback.extract_tb(e_tb)):
        trcbck = " " + str(i+1) + _(". ")
        if line[0].find(os.getcwd()) == -1:
            trcbck += _("file : ") + str(line[0]) + _(",   ")
        else:
            trcbck += _("file : ") + str(line[0][len(os.getcwd()):]) + _(",   ")
        trcbck += _("line : ") + str(line[1]) + _(",   ") + _("function : ") + str(line[2])
        trcbck_lst.append(trcbck)
        
    # Allow clicking....
    cap = wx.Window_GetCapture()
    if cap:
        cap.ReleaseMouse()

    dlg = wx.SingleChoiceDialog(None, 
        _("""
An unhandled exception (bug) occured. Bug report saved at :
(%s)

Please contact LOLITech at:
+33 (0)3 29 57 60 42
or please be kind enough to send this file to:
bugs_beremiz@lolitech.fr

You should now restart Beremiz.

Traceback:
""") % bug_report_path +
        str(e_type) + " : " + str(e_value), 
        _("Error"),
        trcbck_lst)
    try:
        res = (dlg.ShowModal() == wx.ID_OK)
    finally:
        dlg.Destroy()

    return res

def Display_Error_Dialog(e_value):
    message = wxMessageDialog(None, str(e_value), _("Error"), wxOK|wxICON_ERROR)
    message.ShowModal()
    message.Destroy()

def get_last_traceback(tb):
    while tb.tb_next:
        tb = tb.tb_next
    return tb


def format_namespace(d, indent='    '):
    return '\n'.join(['%s%s: %s' % (indent, k, repr(v)[:10000]) for k, v in d.iteritems()])


ignored_exceptions = [] # a problem with a line in a module is only reported once per session

def AddExceptHook(path, app_version='[No version]'):#, ignored_exceptions=[]):
    
    def handle_exception(e_type, e_value, e_traceback):
        traceback.print_exception(e_type, e_value, e_traceback) # this is very helpful when there's an exception in the rest of this func
        last_tb = get_last_traceback(e_traceback)
        ex = (last_tb.tb_frame.f_code.co_filename, last_tb.tb_frame.f_lineno)
        if str(e_value).startswith("!!!"):
            Display_Error_Dialog(e_value)
        elif ex not in ignored_exceptions:
            date = time.ctime()
            bug_report_path = path+os.sep+"bug_report_"+date.replace(':','-').replace(' ','_')+".txt"
            result = Display_Exception_Dialog(e_type,e_value,e_traceback,bug_report_path)
            if result:
                ignored_exceptions.append(ex)
                info = {
                    'app-title' : wx.GetApp().GetAppName(), # app_title
                    'app-version' : app_version,
                    'wx-version' : wx.VERSION_STRING,
                    'wx-platform' : wx.Platform,
                    'python-version' : platform.python_version(), #sys.version.split()[0],
                    'platform' : platform.platform(),
                    'e-type' : e_type,
                    'e-value' : e_value,
                    'date' : date,
                    'cwd' : os.getcwd(),
                    }
                if e_traceback:
                    info['traceback'] = ''.join(traceback.format_tb(e_traceback)) + '%s: %s' % (e_type, e_value)
                    last_tb = get_last_traceback(e_traceback)
                    exception_locals = last_tb.tb_frame.f_locals # the locals at the level of the stack trace where the exception actually occurred
                    info['locals'] = format_namespace(exception_locals)
                    if 'self' in exception_locals:
                        info['self'] = format_namespace(exception_locals['self'].__dict__)
                
                output = open(bug_report_path,'w')
                lst = info.keys()
                lst.sort()
                for a in lst:
                    output.write(a+":\n"+str(info[a])+"\n\n")

    #sys.excepthook = lambda *args: wx.CallAfter(handle_exception, *args)
    sys.excepthook = handle_exception

if __name__ == '__main__':
    # Install a exception handle for bug reports
    AddExceptHook(os.getcwd(),__version__)
    
    frame = Beremiz(None, projectOpen, buildpath)
    frame.Show()
    splash.Close()
    app.MainLoop()
