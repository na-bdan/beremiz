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


updateinfo_url = None

import os, sys, getopt, wx
import __builtin__
from wx.lib.agw.advancedsplash import AdvancedSplash
import tempfile
import shutil
import random
import time
from types import ListType

CWD = os.path.split(os.path.realpath(__file__))[0]

def Bpath(*args):
    return os.path.join(CWD,*args)

if __name__ == '__main__':
    def usage():
        print "\nUsage of Beremiz.py :"
        print "\n   %s [Projectpath] [Buildpath]\n"%sys.argv[0]
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hu:e:", ["help", "updatecheck=", "extend="])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)

    extensions=[]
        
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        if o in ("-u", "--updatecheck"):
            updateinfo_url = a
        if o in ("-e", "--extend"):
            extensions.append(a)
    
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
    
    if os.path.exists("BEREMIZ_DEBUG"):
        __builtin__.__dict__["BMZ_DBG"] = True
    else :
        __builtin__.__dict__["BMZ_DBG"] = False

    app = wx.PySimpleApp(redirect=BMZ_DBG)
    app.SetAppName('beremiz')
    wx.InitAllImageHandlers()
    
    # popup splash
    bmp = wx.Image(Bpath("images","splash.png")).ConvertToBitmap()
    #splash=AdvancedSplash(None, bitmap=bmp, style=wx.SPLASH_CENTRE_ON_SCREEN, timeout=4000)
    splash=AdvancedSplash(None, bitmap=bmp)
    wx.Yield()

    if updateinfo_url is not None:
        updateinfo = "Fetching %s" % updateinfo_url
        # warn for possible updates
        def updateinfoproc():
            global updateinfo
            try :
                import urllib2
                updateinfo = urllib2.urlopen(updateinfo_url,None).read()
            except :
                updateinfo = "update info unavailable." 
                
        from threading import Thread
        splash.SetText(text=updateinfo)
        wx.Yield()
        updateinfoThread = Thread(target=updateinfoproc)
        updateinfoThread.start()
        updateinfoThread.join(2)
        splash.SetText(text=updateinfo)
        wx.Yield()

# Import module for internationalization
import gettext

# Get folder containing translation files
localedir = os.path.join(CWD,"locale")
# Get the default language
langid = wx.LANGUAGE_DEFAULT
# Define translation domain (name of translation files)
domain = "Beremiz"

# Define locale for wx
loc = __builtin__.__dict__.get('loc', None)
if loc is None:
    test_loc = wx.Locale(langid)
    test_loc.AddCatalogLookupPathPrefix(localedir)
    if test_loc.AddCatalog(domain):
        loc = wx.Locale(langid)
    else:
        loc = wx.Locale(wx.LANGUAGE_ENGLISH)
    __builtin__.__dict__['loc'] = loc
# Define location for searching translation files
loc.AddCatalogLookupPathPrefix(localedir)
# Define locale domain
loc.AddCatalog(domain)

def unicode_translation(message):
    return wx.GetTranslation(message).encode("utf-8")

if __name__ == '__main__':
    __builtin__.__dict__['_'] = wx.GetTranslation#unicode_translation

base_folder = os.path.split(sys.path[0])[0]
sys.path.append(base_folder)
sys.path.append(os.path.join(base_folder, "plcopeneditor"))

if __name__ == '__main__':
    # Load extensions
    for extfilename in extensions:
        sys.path.append(os.path.split(os.path.realpath(extfilename))[0])
        execfile(extfilename, locals())

import wx.lib.buttons, wx.lib.statbmp
from util.TextCtrlAutoComplete import TextCtrlAutoComplete
import cPickle
from util.BrowseValuesLibraryDialog import BrowseValuesLibraryDialog
import types, time, re, platform, time, traceback, commands
from ProjectController import ProjectController, MATIEC_ERROR_MODEL, ITEM_CONFNODE
from util.MiniTextControler import MiniTextControler
from util.ProcessLogger import ProcessLogger

from docutil import OpenHtmlFrame
from PLCOpenEditor import IDEFrame, AppendMenu, TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU, PROJECTTREE, POUINSTANCEVARIABLESPANEL, LIBRARYTREE, SCALING, PAGETITLES 
from PLCOpenEditor import EditorPanel, Viewer, TextViewer, GraphicViewer, ResourceEditor, ConfigurationEditor, DataTypeEditor
from PLCControler import LOCATION_CONFNODE, LOCATION_MODULE, LOCATION_GROUP, LOCATION_VAR_INPUT, LOCATION_VAR_OUTPUT, LOCATION_VAR_MEMORY, ITEM_PROJECT, ITEM_RESOURCE

MAX_RECENT_PROJECTS = 10

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

                        
from threading import Lock,Timer,currentThread
MainThread = currentThread().ident
REFRESH_PERIOD = 0.1
from time import time as gettime
class LogPseudoFile:
    """ Base class for file like objects to facilitate StdOut for the Shell."""
    def __init__(self, output, risecall):
        self.red_white = wx.TextAttr("RED", "WHITE")
        self.red_yellow = wx.TextAttr("RED", "YELLOW")
        self.black_white = wx.TextAttr("BLACK", "WHITE")
        self.default_style = None
        self.output = output
        self.risecall = risecall
        # to prevent rapid fire on rising log panel
        self.rising_timer = 0
        self.lock = Lock()
        self.YieldLock = Lock()
        self.RefreshLock = Lock()
        self.stack = []
        self.LastRefreshTime = gettime()
        self.LastRefreshTimer = None

    def write(self, s, style = None):
        if self.lock.acquire():
            self.stack.append((s,style))
            self.lock.release()
            current_time = gettime()
            if self.LastRefreshTimer:
                self.LastRefreshTimer.cancel()
                self.LastRefreshTimer=None
            if current_time - self.LastRefreshTime > REFRESH_PERIOD and self.RefreshLock.acquire(False):
                self._should_write()
            else:
                self.LastRefreshTimer = Timer(REFRESH_PERIOD, self._should_write)
                self.LastRefreshTimer.start()

    def _should_write(self):
        wx.CallAfter(self._write)
        if MainThread == currentThread().ident:
            app = wx.GetApp()
            if app is not None:
                if self.YieldLock.acquire(0):
                    app.Yield()
                    self.YieldLock.release()

    def _write(self):
        if self.output :
            self.output.Freeze(); 
            self.lock.acquire()
            for s, style in self.stack:
                if style is None : style=self.black_white
                if self.default_style != style: 
                    self.output.SetDefaultStyle(style)
                    self.default_style = style
                self.output.AppendText(s)
                self.output.ScrollLines(s.count('\n')+1)
            self.stack = []
            self.lock.release()
            self.output.ShowPosition(self.output.GetLastPosition())
            self.output.Thaw()
            self.LastRefreshTime = gettime()
            try:
                self.RefreshLock.release()
            except:
                pass
            newtime = time.time()
            if newtime - self.rising_timer > 1:
                self.risecall()
            self.rising_timer = newtime

    def write_warning(self, s):
        self.write(s,self.red_white)

    def write_error(self, s):
        self.write(s,self.red_yellow)

    def writeyield(self, s):
        self.write(s)
        wx.GetApp().Yield()

    def flush(self):
        self.output.SetValue("")
    
    def isatty(self):
        return false

[ID_BEREMIZ, ID_BEREMIZMAINSPLITTER, 
 ID_BEREMIZPLCCONFIG, ID_BEREMIZLOGCONSOLE, 
 ID_BEREMIZINSPECTOR] = [wx.NewId() for _init_ctrls in range(5)]

[ID_FILEMENURECENTPROJECTS,
] = [wx.NewId() for _init_ctrls in range(1)]

CONFNODEMENU_POSITION = 3

class Beremiz(IDEFrame):
	
    def _init_coll_MenuBar_Menus(self, parent):
        IDEFrame._init_coll_MenuBar_Menus(self, parent)
        
        parent.Insert(pos=CONFNODEMENU_POSITION, 
                      menu=self.ConfNodeMenu, title=_(u'&ConfNode'))
    
    def _init_utils(self):
        self.ConfNodeMenu = wx.Menu(title='')
        self.RecentProjectsMenu = wx.Menu(title='')
        
        IDEFrame._init_utils(self)
        
    def _init_coll_FileMenu_Items(self, parent):
        AppendMenu(parent, help='', id=wx.ID_NEW,
              kind=wx.ITEM_NORMAL, text=_(u'New\tCTRL+N'))
        AppendMenu(parent, help='', id=wx.ID_OPEN,
              kind=wx.ITEM_NORMAL, text=_(u'Open\tCTRL+O'))
        parent.AppendMenu(ID_FILEMENURECENTPROJECTS, _("&Recent Projects"), self.RecentProjectsMenu)
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_SAVE,
              kind=wx.ITEM_NORMAL, text=_(u'Save\tCTRL+S'))
        AppendMenu(parent, help='', id=wx.ID_SAVEAS,
              kind=wx.ITEM_NORMAL, text=_(u'Save as\tCTRL+SHIFT+S'))
        AppendMenu(parent, help='', id=wx.ID_CLOSE,
              kind=wx.ITEM_NORMAL, text=_(u'Close Tab\tCTRL+W'))
        AppendMenu(parent, help='', id=wx.ID_CLOSE_ALL,
              kind=wx.ITEM_NORMAL, text=_(u'Close Project\tCTRL+SHIFT+W'))
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_PAGE_SETUP,
              kind=wx.ITEM_NORMAL, text=_(u'Page Setup\tCTRL+ALT+P'))
        AppendMenu(parent, help='', id=wx.ID_PREVIEW,
              kind=wx.ITEM_NORMAL, text=_(u'Preview\tCTRL+SHIFT+P'))
        AppendMenu(parent, help='', id=wx.ID_PRINT,
              kind=wx.ITEM_NORMAL, text=_(u'Print\tCTRL+P'))
        parent.AppendSeparator()
        AppendMenu(parent, help='', id=wx.ID_EXIT,
              kind=wx.ITEM_NORMAL, text=_(u'Quit\tCTRL+Q'))
        
        self.Bind(wx.EVT_MENU, self.OnNewProjectMenu, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.OnOpenProjectMenu, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSaveProjectMenu, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnSaveProjectAsMenu, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.OnCloseTabMenu, id=wx.ID_CLOSE)
        self.Bind(wx.EVT_MENU, self.OnCloseProjectMenu, id=wx.ID_CLOSE_ALL)
        self.Bind(wx.EVT_MENU, self.OnPageSetupMenu, id=wx.ID_PAGE_SETUP)
        self.Bind(wx.EVT_MENU, self.OnPreviewMenu, id=wx.ID_PREVIEW)
        self.Bind(wx.EVT_MENU, self.OnPrintMenu, id=wx.ID_PRINT)
        self.Bind(wx.EVT_MENU, self.OnQuitMenu, id=wx.ID_EXIT)
    
        self.AddToMenuToolBar([(wx.ID_NEW, "new.png", _(u'New'), None),
                               (wx.ID_OPEN, "open.png", _(u'Open'), None),
                               (wx.ID_SAVE, "save.png", _(u'Save'), None),
                               (wx.ID_SAVEAS, "saveas.png", _(u'Save As...'), None),
                               (wx.ID_PRINT, "print.png", _(u'Print'), None)])
    
    def _init_coll_AddMenu_Items(self, parent):
        IDEFrame._init_coll_AddMenu_Items(self, parent, False)
        new_id = wx.NewId()
        AppendMenu(parent, help='', id=new_id,
                  kind=wx.ITEM_NORMAL, text=_(u'&Resource'))
        for name, XSDClass, help in ProjectController.CTNChildrenTypes:
            new_id = wx.NewId()
            AppendMenu(parent, help='', id=new_id, 
                       kind=wx.ITEM_NORMAL, text=help)
            self.Bind(wx.EVT_MENU, self._GetAddConfNodeFunction(name), id=new_id)
    
    def _init_coll_HelpMenu_Items(self, parent):
        parent.Append(help='', id=wx.ID_ABOUT,
              kind=wx.ITEM_NORMAL, text=_(u'About'))
        self.Bind(wx.EVT_MENU, self.OnAboutMenu, id=wx.ID_ABOUT)
    
    def _init_ctrls(self, prnt):
        IDEFrame._init_ctrls(self, prnt)
        
        self.Bind(wx.EVT_MENU, self.OnOpenWidgetInspector, id=ID_BEREMIZINSPECTOR)
        accels = [wx.AcceleratorEntry(wx.ACCEL_CTRL|wx.ACCEL_ALT, ord('I'), ID_BEREMIZINSPECTOR)]
        for method,shortcut in [("Stop",     wx.WXK_F4),
                                ("Run",      wx.WXK_F5),
                                ("Transfer", wx.WXK_F6),
                                ("Connect",  wx.WXK_F7),
                                ("Build",    wx.WXK_F11)]:
            def OnMethodGen(obj,meth):
                def OnMethod(evt):
                    if obj.CTR is not None:
                       obj.CTR.CallMethod('_'+meth)
                    wx.CallAfter(self.RefreshStatusToolBar)
                return OnMethod
            newid = wx.NewId()
            self.Bind(wx.EVT_MENU, OnMethodGen(self,method), id=newid)
            accels += [wx.AcceleratorEntry(wx.ACCEL_NORMAL, shortcut,newid)]
        
        self.SetAcceleratorTable(wx.AcceleratorTable(accels))
        
        self.LogConsole = wx.TextCtrl(id=ID_BEREMIZLOGCONSOLE, value='',
                  name='LogConsole', parent=self.BottomNoteBook, pos=wx.Point(0, 0),
                  size=wx.Size(0, 0), style=wx.TE_MULTILINE|wx.TE_RICH2)
        self.LogConsole.Bind(wx.EVT_LEFT_DCLICK, self.OnLogConsoleDClick)
        self.MainTabs["LogConsole"] = (self.LogConsole, _("Log Console"))
        self.BottomNoteBook.AddPage(*self.MainTabs["LogConsole"])
        self.BottomNoteBook.Split(self.BottomNoteBook.GetPageIndex(self.LogConsole), wx.RIGHT)

        StatusToolBar = wx.ToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize,
                wx.TB_FLAT | wx.TB_NODIVIDER | wx.NO_BORDER)
        StatusToolBar.SetToolBitmapSize(wx.Size(25, 25))
        StatusToolBar.Realize()
        self.Panes["StatusToolBar"] = StatusToolBar
        self.AUIManager.AddPane(StatusToolBar, wx.aui.AuiPaneInfo().
                  Name("StatusToolBar").Caption(_("Status ToolBar")).
                  ToolbarPane().Top().Position(2).
                  LeftDockable(False).RightDockable(False))
        
        self.AUIManager.Update()
        
    def __init__(self, parent, projectOpen=None, buildpath=None, ctr=None, debug=True):
        IDEFrame.__init__(self, parent, debug)
        self.Log = LogPseudoFile(self.LogConsole,self.RiseLogConsole)
        
        self.local_runtime = None
        self.runtime_port = None
        self.local_runtime_tmpdir = None
        
        self.LastPanelSelected = None
        
        # Define Tree item icon list
        self.LocationImageList = wx.ImageList(16, 16)
        self.LocationImageDict = {}
        
        # Icons for location items
        for imgname, itemtype in [
            ("CONFIGURATION", LOCATION_CONFNODE),
            ("RESOURCE",      LOCATION_MODULE),
            ("PROGRAM",       LOCATION_GROUP),
            ("VAR_INPUT",     LOCATION_VAR_INPUT),
            ("VAR_OUTPUT",    LOCATION_VAR_OUTPUT),
            ("VAR_LOCAL",     LOCATION_VAR_MEMORY)]:
            self.LocationImageDict[itemtype]=self.LocationImageList.Add(wx.Bitmap(os.path.join(base_folder, "plcopeneditor", 'Images', '%s.png'%imgname)))
        
        # Icons for other items
        for imgname, itemtype in [
            ("Extension", ITEM_CONFNODE)]:
            self.TreeImageDict[itemtype]=self.TreeImageList.Add(wx.Bitmap(os.path.join(CWD, 'images', '%s.png'%imgname)))
        
        # Add beremiz's icon in top left corner of the frame
        self.SetIcon(wx.Icon(Bpath( "images", "brz.ico"), wx.BITMAP_TYPE_ICO))
        
        if projectOpen is None and self.Config.HasEntry("currenteditedproject"):
            projectOpen = str(self.Config.Read("currenteditedproject"))
            if projectOpen == "":
                projectOpen = None
        
        if projectOpen is not None and os.path.isdir(projectOpen):
            self.CTR = ProjectController(self, self.Log)
            self.Controler = self.CTR
            result = self.CTR.LoadProject(projectOpen, buildpath)
            if not result:
                self.LibraryPanel.SetControler(self.Controler)
                self.ProjectTree.Enable(True)
                self.PouInstanceVariablesPanel.SetController(self.Controler)
                self.RefreshConfigRecentProjects(os.path.abspath(projectOpen))
                self._Refresh(PROJECTTREE, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)
            else:
                self.ResetView()
                self.ShowErrorMessage(result)
        else:
            self.CTR = ctr
            self.Controler = ctr
            if ctr is not None:
                self.LibraryPanel.SetControler(self.Controler)
                self.ProjectTree.Enable(True)
                self.PouInstanceVariablesPanel.SetController(self.Controler)
                self._Refresh(PROJECTTREE, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)
        if self.EnableDebug:
            self.DebugVariablePanel.SetDataProducer(self.CTR)
        
        self.Bind(wx.EVT_CLOSE, self.OnCloseFrame)
        
        self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU, DISPLAYMENU)
        self.RefreshConfNodeMenu()
        self.RefreshAll()
        self.LogConsole.SetFocus()

    def RiseLogConsole(self):
        self.BottomNoteBook.SetSelection(self.BottomNoteBook.GetPageIndex(self.LogConsole))
        
    def RefreshTitle(self):
        name = _("Beremiz")
        if self.CTR is not None:
            projectname = self.CTR.GetProjectName()
            if self.CTR.ProjectTestModified():
                projectname = "~%s~" % projectname
            self.SetTitle("%s - %s" % (name, projectname))
        else:
            self.SetTitle(name)

    def StartLocalRuntime(self, taskbaricon = True):
        if (self.local_runtime is None) or (self.local_runtime.exitcode is not None):
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
                                                           no_gui=False,
                                                           timeout=500, keyword = "working")
            self.local_runtime.spin()
        return self.runtime_port
    
    def KillLocalRuntime(self):
        if self.local_runtime is not None:
            # shutdown local runtime
            self.local_runtime.kill(gently=False)
            # clear temp dir
            shutil.rmtree(self.local_runtime_tmpdir)
            
            self.local_runtime = None

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
        if self.CTR is not None:
            text = self.LogConsole.GetRange(0, self.LogConsole.GetInsertionPoint())
            line = self.LogConsole.GetLineText(len(text.splitlines()) - 1)
            result = MATIEC_ERROR_MODEL.match(line)
            if result is not None:
                first_line, first_column, last_line, last_column, error = result.groups()
                infos = self.CTR.ShowError(self.Log,
                                                  (int(first_line), int(first_column)), 
                                                  (int(last_line), int(last_column)))
	
    ## Function displaying an Error dialog in PLCOpenEditor.
    #  @return False if closing cancelled.
    def CheckSaveBeforeClosing(self, title=_("Close Project")):
        if self.CTR.ProjectTestModified():
            dialog = wx.MessageDialog(self,
                                      _("There are changes, do you want to save?"),
                                      title,
                                      wx.YES_NO|wx.CANCEL|wx.ICON_QUESTION)
            answer = dialog.ShowModal()
            dialog.Destroy()
            if answer == wx.ID_YES:
                self.CTR.SaveProject()
            elif answer == wx.ID_CANCEL:
                return False
        return True
    
    def GetTabInfos(self, tab):
        if (isinstance(tab, EditorPanel) and 
            not isinstance(tab, (Viewer, 
                                 TextViewer, 
                                 GraphicViewer, 
                                 ResourceEditor, 
                                 ConfigurationEditor, 
                                 DataTypeEditor))):
            return ("confnode", tab.Controler.CTNFullName())
        elif (isinstance(tab, TextViewer) and 
              (tab.Controler is None or isinstance(tab.Controler, MiniTextControler))):
            return ("confnode", None, tab.GetInstancePath())
        else:
            return IDEFrame.GetTabInfos(self, tab)
    
    def LoadTab(self, notebook, page_infos):
        if page_infos[0] == "confnode":
            if page_infos[1] is None:
                confnode = self.CTR
            else:
                confnode = self.CTR.GetChildByName(page_infos[1])
            return notebook.GetPageIndex(confnode._OpenView(*page_infos[2:]))
        else:
            return IDEFrame.LoadTab(self, notebook, page_infos)
    
    def OnCloseFrame(self, event):
        if self.CTR is None or self.CheckSaveBeforeClosing(_("Close Application")):
            if self.CTR is not None:
                self.CTR.KillDebugThread()
            self.KillLocalRuntime()
            
            self.SaveLastState()
            
            if self.CTR is not None:
                project_path = os.path.realpath(self.CTR.GetProjectPath())
            else:
                project_path = ""
            self.Config.Write("currenteditedproject", project_path)    
            self.Config.Flush()
            
            event.Skip()
        else:
            event.Veto()
    
    def RefreshFileMenu(self):
        self.RefreshRecentProjectsMenu()
        
        MenuToolBar = self.Panes["MenuToolBar"]
        if self.CTR is not None:
            selected = self.TabsOpened.GetSelection()
            if selected >= 0:
                graphic_viewer = isinstance(self.TabsOpened.GetPage(selected), Viewer)
            else:
                graphic_viewer = False
            if self.TabsOpened.GetPageCount() > 0:
                self.FileMenu.Enable(wx.ID_CLOSE, True)
                if graphic_viewer:
                    self.FileMenu.Enable(wx.ID_PREVIEW, True)
                    self.FileMenu.Enable(wx.ID_PRINT, True)
                    MenuToolBar.EnableTool(wx.ID_PRINT, True)
                else:
                    self.FileMenu.Enable(wx.ID_PREVIEW, False)
                    self.FileMenu.Enable(wx.ID_PRINT, False)
                    MenuToolBar.EnableTool(wx.ID_PRINT, False)
            else:
                self.FileMenu.Enable(wx.ID_CLOSE, False)
                self.FileMenu.Enable(wx.ID_PREVIEW, False)
                self.FileMenu.Enable(wx.ID_PRINT, False)
                MenuToolBar.EnableTool(wx.ID_PRINT, False)
            self.FileMenu.Enable(wx.ID_PAGE_SETUP, True)
            project_modified = self.CTR.ProjectTestModified()
            self.FileMenu.Enable(wx.ID_SAVE, project_modified)
            MenuToolBar.EnableTool(wx.ID_SAVE, project_modified)
            self.FileMenu.Enable(wx.ID_SAVEAS, True)
            MenuToolBar.EnableTool(wx.ID_SAVEAS, True)
            self.FileMenu.Enable(wx.ID_CLOSE_ALL, True)
        else:
            self.FileMenu.Enable(wx.ID_CLOSE, False)
            self.FileMenu.Enable(wx.ID_PAGE_SETUP, False)
            self.FileMenu.Enable(wx.ID_PREVIEW, False)
            self.FileMenu.Enable(wx.ID_PRINT, False)
            MenuToolBar.EnableTool(wx.ID_PRINT, False)
            self.FileMenu.Enable(wx.ID_SAVE, False)
            MenuToolBar.EnableTool(wx.ID_SAVE, False)
            self.FileMenu.Enable(wx.ID_SAVEAS, False)
            MenuToolBar.EnableTool(wx.ID_SAVEAS, False)
            self.FileMenu.Enable(wx.ID_CLOSE_ALL, False)
    
    def RefreshRecentProjectsMenu(self):
        recent_projects = cPickle.loads(str(self.Config.Read("RecentProjects", cPickle.dumps([]))))
        self.FileMenu.Enable(ID_FILEMENURECENTPROJECTS, len(recent_projects) > 0)
        for idx, projectpath in enumerate(recent_projects):
            text = u'%d: %s' % (idx + 1, projectpath)
            
            if idx < self.RecentProjectsMenu.GetMenuItemCount():
                item = self.RecentProjectsMenu.FindItemByPosition(idx)
                id = item.GetId()
                item.SetItemLabel(text)
                self.Disconnect(id, id, wx.EVT_BUTTON._getEvtType())
            else:
                id = wx.NewId()
                AppendMenu(self.RecentProjectsMenu, help='', id=id, 
                           kind=wx.ITEM_NORMAL, text=text)
            self.Bind(wx.EVT_MENU, self.GenerateOpenRecentProjectFunction(projectpath), id=id)
        
    def GenerateOpenRecentProjectFunction(self, projectpath):
        def OpenRecentProject(event):
            if self.CTR is not None and not self.CheckSaveBeforeClosing():
                return
            
            self.OpenProject(projectpath)
        return OpenRecentProject
    
    def GenerateMenuRecursive(self, items, menu):
        for kind, infos in items:
            if isinstance(kind, ListType):
                text, id = infos
                submenu = wx.Menu('')
                self.GenerateMenuRecursive(kind, submenu)
                menu.AppendMenu(id, text, submenu)
            elif kind == wx.ITEM_SEPARATOR:
                menu.AppendSeparator()
            else:
                text, id, help, callback = infos
                AppendMenu(menu, help='', id=id, kind=kind, text=text)
                if callback is not None:
                    self.Bind(wx.EVT_MENU, callback, id=id)
    
    def RefreshStatusToolBar(self):
        StatusToolBar = self.Panes["StatusToolBar"]
        StatusToolBar.ClearTools()
        
        if self.CTR is not None:
            
            for confnode_method in self.CTR.StatusMethods:
                if "method" in confnode_method and confnode_method.get("shown",True):
                    id = wx.NewId()
                    StatusToolBar.AddSimpleTool(id, 
                        wx.Bitmap(Bpath("images", "%s.png"%confnode_method.get("bitmap", "Unknown"))), 
                        confnode_method["tooltip"])
                    self.Bind(wx.EVT_MENU, self.GetMenuCallBackFunction(confnode_method["method"]), id=id)
            
            StatusToolBar.Realize()
            self.AUIManager.GetPane("StatusToolBar").BestSize(StatusToolBar.GetBestSize()).Show()
        else:
            self.AUIManager.GetPane("StatusToolBar").Hide()
        self.AUIManager.Update()
    
    def RefreshConfNodeMenu(self):
        if self.CTR is not None:
            selected = self.TabsOpened.GetSelection()
            if selected >= 0:
                panel = self.TabsOpened.GetPage(selected)
            else:
                panel = None
            if panel != self.LastPanelSelected:
                for i in xrange(self.ConfNodeMenu.GetMenuItemCount()):
                    item = self.ConfNodeMenu.FindItemByPosition(0)
                    self.ConfNodeMenu.Delete(item.GetId())
                self.LastPanelSelected = panel
                if panel is not None:
                    items = panel.GetConfNodeMenuItems()
                else:
                    items = []
                self.MenuBar.EnableTop(CONFNODEMENU_POSITION, len(items) > 0)
                self.GenerateMenuRecursive(items, self.ConfNodeMenu)
            if panel is not None:
                panel.RefreshConfNodeMenu(self.ConfNodeMenu)
        else:
            self.MenuBar.EnableTop(CONFNODEMENU_POSITION, False)
        self.MenuBar.UpdateMenus()
    
    def RefreshAll(self):
        self.RefreshStatusToolBar()
    
    def _GetAddConfNodeFunction(self, name, confnode=None):
        def OnConfNodeMenu(event):
            wx.CallAfter(self.AddConfNode, name, confnode)
        return OnConfNodeMenu
    
    def GetMenuCallBackFunction(self, method):
        """ Generate the callbackfunc for a given CTR method"""
        def OnMenu(event):
            # Disable button to prevent re-entrant call 
            event.GetEventObject().Disable()
            # Call
            getattr(self.CTR, method)()
            # Re-enable button 
            event.GetEventObject().Enable()
            # Trigger refresh on Idle
            wx.CallAfter(self.RefreshStatusToolBar)
        return OnMenu
    
    def GetConfigEntry(self, entry_name, default):
        return cPickle.loads(str(self.Config.Read(entry_name, cPickle.dumps(default))))
    
    def ResetView(self):
        IDEFrame.ResetView(self)
        self.ConfNodeInfos = {}
        if self.CTR is not None:
            self.CTR.CloseProject()
        self.CTR = None
        self.Log.flush()
        if self.EnableDebug:
            self.DebugVariablePanel.SetDataProducer(None)
    
    def RefreshConfigRecentProjects(self, projectpath):
        recent_projects = cPickle.loads(str(self.Config.Read("RecentProjects", cPickle.dumps([]))))
        if projectpath in recent_projects:
            recent_projects.remove(projectpath)
        recent_projects.insert(0, projectpath)
        self.Config.Write("RecentProjects", cPickle.dumps(recent_projects[:MAX_RECENT_PROJECTS]))
        self.Config.Flush()
    
    def ResetPerspective(self):
        IDEFrame.ResetPerspective(self)
        self.RefreshStatusToolBar()
    
    def RestoreLastLayout(self):
        IDEFrame.RestoreLastLayout(self)
        self.RefreshStatusToolBar()
    
    def OnNewProjectMenu(self, event):
        if self.CTR is not None and not self.CheckSaveBeforeClosing():
            return
        
        if not self.Config.HasEntry("lastopenedfolder"):
            defaultpath = os.path.expanduser("~")
        else:
            defaultpath = self.Config.Read("lastopenedfolder")
        
        dialog = wx.DirDialog(self , _("Choose a project"), defaultpath, wx.DD_NEW_DIR_BUTTON)
        if dialog.ShowModal() == wx.ID_OK:
            projectpath = dialog.GetPath()
            self.Config.Write("lastopenedfolder", os.path.dirname(projectpath))
            self.Config.Flush()
            self.ResetView()
            ctr = ProjectController(self, self.Log)
            result = ctr.NewProject(projectpath)
            if not result:
                self.CTR = ctr
                self.Controler = self.CTR
                self.LibraryPanel.SetControler(self.Controler)
                self.ProjectTree.Enable(True)
                self.PouInstanceVariablesPanel.SetController(self.Controler)
                self.RefreshConfigRecentProjects(projectpath)
                if self.EnableDebug:
                    self.DebugVariablePanel.SetDataProducer(self.CTR)
                self._Refresh(PROJECTTREE, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)
            else:
                self.ResetView()
                self.ShowErrorMessage(result)
            self.RefreshAll()
            self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU)
        dialog.Destroy()
    
    def OnOpenProjectMenu(self, event):
        if self.CTR is not None and not self.CheckSaveBeforeClosing():
            return
        
        if not self.Config.HasEntry("lastopenedfolder"):
            defaultpath = os.path.expanduser("~")
        else:
            defaultpath = self.Config.Read("lastopenedfolder")
        
        dialog = wx.DirDialog(self , _("Choose a project"), defaultpath, wx.DD_NEW_DIR_BUTTON)
        if dialog.ShowModal() == wx.ID_OK:
            self.OpenProject(dialog.GetPath())
        dialog.Destroy()
    
    def OpenProject(self, projectpath):
        if os.path.isdir(projectpath):
            self.Config.Write("lastopenedfolder", os.path.dirname(projectpath))
            self.Config.Flush()
            self.ResetView()
            self.CTR = ProjectController(self, self.Log)
            self.Controler = self.CTR
            result = self.CTR.LoadProject(projectpath)
            if not result:
                self.LibraryPanel.SetControler(self.Controler)
                self.ProjectTree.Enable(True)
                self.PouInstanceVariablesPanel.SetController(self.Controler)
                self.RefreshConfigRecentProjects(projectpath)
                if self.EnableDebug:
                    self.DebugVariablePanel.SetDataProducer(self.CTR)
                self.LoadProjectLayout()
                self._Refresh(PROJECTTREE, POUINSTANCEVARIABLESPANEL, LIBRARYTREE)
            else:
                self.ResetView()
                self.ShowErrorMessage(result)
            self.RefreshAll()
        else:
            self.ShowErrorMessage(_("\"%s\" folder is not a valid Beremiz project\n") % projectpath)
        self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU)
    
    def OnCloseProjectMenu(self, event):
        if self.CTR is not None and not self.CheckSaveBeforeClosing():
            return
        
        self.SaveProjectLayout()
        self.ResetView()
        self._Refresh(TITLE, EDITORTOOLBAR, FILEMENU, EDITMENU)
        self.RefreshAll()
    
    def OnSaveProjectMenu(self, event):
        if self.CTR is not None:
            self.CTR.SaveProject()
            self._Refresh(TITLE, FILEMENU, EDITMENU, PAGETITLES)
    
    def OnSaveProjectAsMenu(self, event):
        if self.CTR is not None:
            self.CTR.SaveProjectAs()
            self._Refresh(TITLE, FILEMENU, EDITMENU, PAGETITLES)
        event.Skip()
    
    def OnQuitMenu(self, event):
        self.Close()
        
    def OnAboutMenu(self, event):
        OpenHtmlFrame(self,_("About Beremiz"), Bpath("doc","about.html"), wx.Size(550, 500))
    
    def OnPouSelectedChanged(self, event):
        wx.CallAfter(self.RefreshConfNodeMenu)
        IDEFrame.OnPouSelectedChanged(self, event)
    
    def OnPageClose(self, event):
        wx.CallAfter(self.RefreshConfNodeMenu)
        IDEFrame.OnPageClose(self, event)
    
    def OnProjectTreeItemBeginEdit(self, event):
        selected = event.GetItem()
        if self.ProjectTree.GetPyData(selected)["type"] == ITEM_CONFNODE:
            event.Veto()
        else:
            IDEFrame.OnProjectTreeItemBeginEdit(self, event)
    
    def OnProjectTreeRightUp(self, event):
        if wx.Platform == '__WXMSW__':
            item = event.GetItem()
        else:
            item, flags = self.ProjectTree.HitTest(wx.Point(event.GetX(), event.GetY()))
        item_infos = self.ProjectTree.GetPyData(item)
        
        if item_infos["type"] == ITEM_CONFNODE:
            confnode_menu = wx.Menu(title='')
            
            confnode = item_infos["confnode"]
            if confnode is not None and len(confnode.CTNChildrenTypes) > 0:
                for name, XSDClass, help in confnode.CTNChildrenTypes:
                    new_id = wx.NewId()
                    confnode_menu.Append(help=help, id=new_id, kind=wx.ITEM_NORMAL, text=name)
                    self.Bind(wx.EVT_MENU, self._GetAddConfNodeFunction(name, confnode), id=new_id)

            new_id = wx.NewId()
            AppendMenu(confnode_menu, help='', id=new_id, kind=wx.ITEM_NORMAL, text=_("Delete"))
            self.Bind(wx.EVT_MENU, self.GetDeleteMenuFunction(confnode), id=new_id)
                
            self.PopupMenu(confnode_menu)
            confnode_menu.Destroy()
            
            event.Skip()
        else:
            IDEFrame.OnProjectTreeRightUp(self, event)
    
    def OnProjectTreeItemActivated(self, event):
        selected = event.GetItem()
        name = self.ProjectTree.GetItemText(selected)
        item_infos = self.ProjectTree.GetPyData(selected)
        if item_infos["type"] == ITEM_CONFNODE:
            item_infos["confnode"]._OpenView()
            event.Skip()
        elif item_infos["type"] == ITEM_PROJECT:
            self.CTR._OpenView()
        else:
            IDEFrame.OnProjectTreeItemActivated(self, event)
    
    def SelectProjectTreeItem(self, tagname):
        if self.ProjectTree is not None:
            root = self.ProjectTree.GetRootItem()
            if root.IsOk():
                words = tagname.split("::")
                if len(words) == 1:
                    if tagname == "Project":
                        self.SelectedItem = root
                        self.ProjectTree.SelectItem(root)
                        wx.CallAfter(self.ResetSelectedItem)
                    else:
                        return self.RecursiveProjectTreeItemSelection(root, 
                              [(word, ITEM_CONFNODE) for word in tagname.split(".")])
                elif words[0] == "R":
                    return self.RecursiveProjectTreeItemSelection(root, [(words[2], ITEM_RESOURCE)])
                else:
                    IDEFrame.SelectProjectTreeItem(self, tagname)
            
    def GetDeleteMenuFunction(self, confnode):
        def DeleteMenuFunction(event):
            wx.CallAfter(self.DeleteConfNode, confnode)
        return DeleteMenuFunction
    
    def AddConfNode(self, ConfNodeType, confnode=None):
        if self.CTR.CheckProjectPathPerm():
            dialog = wx.TextEntryDialog(self, _("Please enter a name for confnode:"), _("Add ConfNode"), "", wx.OK|wx.CANCEL)
            if dialog.ShowModal() == wx.ID_OK:
                ConfNodeName = dialog.GetValue()
                if confnode is not None:
                    confnode.CTNAddChild(ConfNodeName, ConfNodeType)
                else:
                    self.CTR.CTNAddChild(ConfNodeName, ConfNodeType)
                self._Refresh(TITLE, FILEMENU, PROJECTTREE)
            dialog.Destroy()
    
    def DeleteConfNode(self, confnode):
        if self.CTR.CheckProjectPathPerm():
            dialog = wx.MessageDialog(self, _("Really delete confnode ?"), _("Remove confnode"), wx.YES_NO|wx.NO_DEFAULT)
            if dialog.ShowModal() == wx.ID_YES:
                confnode.CTNRemove()
                del confnode
                self._Refresh(TITLE, FILEMENU, PROJECTTREE)
            dialog.Destroy()
    
#-------------------------------------------------------------------------------
#                               Exception Handler
#-------------------------------------------------------------------------------

Max_Traceback_List_Size = 20

def Display_Exception_Dialog(e_type, e_value, e_tb, bug_report_path):
    trcbck_lst = []
    for i,line in enumerate(traceback.extract_tb(e_tb)):
        trcbck = " " + str(i+1) + ". "
        if line[0].find(os.getcwd()) == -1:
            trcbck += "file : " + str(line[0]) + ",   "
        else:
            trcbck += "file : " + str(line[0][len(os.getcwd()):]) + ",   "
        trcbck += "line : " + str(line[1]) + ",   " + "function : " + str(line[2])
        trcbck_lst.append(trcbck)
        
    # Allow clicking....
    cap = wx.Window_GetCapture()
    if cap:
        cap.ReleaseMouse()

    dlg = wx.SingleChoiceDialog(None, 
        _("""
An unhandled exception (bug) occured. Bug report saved at :
(%s)

Please be kind enough to send this file to:
beremiz-devel@lists.sourceforge.net

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
        if ex not in ignored_exceptions:
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
    AddExceptHook(os.getcwd(),updateinfo_url)
    
    frame = Beremiz(None, projectOpen, buildpath)
    splash.Close()
    frame.Show()
    app.MainLoop()
