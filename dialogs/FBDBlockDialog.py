#!/usr/bin/env python
# -*- coding: utf-8 -*-

#This file is part of PLCOpenEditor, a library implementing an IEC 61131-3 editor
#based on the plcopen standard. 
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

import re

import wx

from graphics.FBD_Objects import FBD_Block
from controls.LibraryPanel import LibraryPanel
from BlockPreviewDialog import BlockPreviewDialog

#-------------------------------------------------------------------------------
#                         Set Block Parameters Dialog
#-------------------------------------------------------------------------------

"""
Class that implements a dialog for defining parameters of a FBD block graphic
element
"""

class FBDBlockDialog(BlockPreviewDialog):
    
    def __init__(self, parent, controller, tagname):
        """
        Constructor
        @param parent: Parent wx.Window of dialog for modal
        @param controller: Reference to project controller
        @param tagname: Tagname of project POU edited
        """
        BlockPreviewDialog.__init__(self, parent, controller, tagname,
              size=wx.Size(600, 450), title=_('Block Properties'))
        
        # Create dialog main sizer
        main_sizer = wx.FlexGridSizer(cols=1, hgap=0, rows=4, vgap=10)
        main_sizer.AddGrowableCol(0)
        main_sizer.AddGrowableRow(0)
        
        # Create a sizer for dividing FBD block parameters in two columns
        column_sizer = wx.BoxSizer(wx.HORIZONTAL)
        main_sizer.AddSizer(column_sizer, border=20, 
              flag=wx.GROW|wx.TOP|wx.LEFT|wx.RIGHT)
        
        # Create static box around library panel
        type_staticbox = wx.StaticBox(self, label=_('Type:'))
        left_staticboxsizer = wx.StaticBoxSizer(type_staticbox, wx.VERTICAL)
        column_sizer.AddSizer(left_staticboxsizer, 1, border=5, 
              flag=wx.GROW|wx.RIGHT)
        
        # Create Library panel and add it to static box
        self.LibraryPanel = LibraryPanel(self)
        # Set function to call when selection in Library panel changed
        setattr(self.LibraryPanel, "_OnTreeItemSelected", 
              self.OnLibraryTreeItemSelected)
        left_staticboxsizer.AddWindow(self.LibraryPanel, 1, border=5, 
              flag=wx.GROW|wx.TOP)
        
        # Create sizer for other block parameters and preview panle
        right_gridsizer = wx.FlexGridSizer(cols=1, hgap=0, rows=3, vgap=5)
        right_gridsizer.AddGrowableCol(0)
        right_gridsizer.AddGrowableRow(2)
        column_sizer.AddSizer(right_gridsizer, 1, border=5, 
              flag=wx.GROW|wx.LEFT)
        
        # Create sizer for other block parameters
        top_right_gridsizer = wx.FlexGridSizer(cols=2, hgap=0, rows=4, vgap=5)
        top_right_gridsizer.AddGrowableCol(1)
        right_gridsizer.AddSizer(top_right_gridsizer, flag=wx.GROW)
        
        # Create label for block name
        name_label = wx.StaticText(self, label=_('Name:'))
        top_right_gridsizer.AddWindow(name_label, 
              flag=wx.ALIGN_CENTER_VERTICAL)
        
        # Create text control for defining block name
        self.BlockName = wx.TextCtrl(self)
        self.Bind(wx.EVT_TEXT, self.OnNameChanged, self.BlockName)
        top_right_gridsizer.AddWindow(self.BlockName, flag=wx.GROW)
        
        # Create label for extended block input number
        inputs_label = wx.StaticText(self, label=_('Inputs:'))
        top_right_gridsizer.AddWindow(inputs_label, 
              flag=wx.ALIGN_CENTER_VERTICAL)
        
        # Create spin control for defining extended block input number
        self.Inputs = wx.SpinCtrl(self, min=2, max=20,
              style=wx.SP_ARROW_KEYS)
        self.Bind(wx.EVT_SPINCTRL, self.OnInputsChanged, self.Inputs)
        top_right_gridsizer.AddWindow(self.Inputs, flag=wx.GROW)
        
        # Create label for block execution order
        execution_order_label = wx.StaticText(self, 
              label=_('Execution Order:'))
        top_right_gridsizer.AddWindow(execution_order_label, 
              flag=wx.ALIGN_CENTER_VERTICAL)
        
        # Create spin control for defining block execution order
        self.ExecutionOrder = wx.SpinCtrl(self, min=0, style=wx.SP_ARROW_KEYS)
        self.Bind(wx.EVT_SPINCTRL, self.OnExecutionOrderChanged, 
                  self.ExecutionOrder)
        top_right_gridsizer.AddWindow(self.ExecutionOrder, flag=wx.GROW)
                
        # Create label for block execution control
        execution_control_label = wx.StaticText(self, 
              label=_('Execution Control:'))
        top_right_gridsizer.AddWindow(execution_control_label, 
              flag=wx.ALIGN_CENTER_VERTICAL)
        
        # Create check box to enable block execution control
        self.ExecutionControl = wx.CheckBox(self)
        self.Bind(wx.EVT_CHECKBOX, self.OnExecutionOrderChanged, 
                  self.ExecutionControl)
        top_right_gridsizer.AddWindow(self.ExecutionControl, flag=wx.GROW)
        
        # Add preview panel and associated label to sizers
        right_gridsizer.AddWindow(self.PreviewLabel, flag=wx.GROW)
        right_gridsizer.AddWindow(self.Preview, flag=wx.GROW)
        
        main_sizer.AddSizer(self.ButtonSizer, border=20, 
              flag=wx.ALIGN_RIGHT|wx.BOTTOM|wx.LEFT|wx.RIGHT)
        
        self.SetSizer(main_sizer)
        
        self.ParamsControl = {
            "extension": self.Inputs,
            "executionOrder": self.ExecutionOrder,
            "executionControl": self.ExecutionControl
        }
        
        # Init controls value and sensibility
        self.BlockName.SetValue("")
        self.BlockName.Enable(False)
        self.Inputs.Enable(False)
        
        # Variable containing last name typed
        self.CurrentBlockName = None
        
        # Refresh Library panel values
        self.LibraryPanel.SetBlockList(controller.GetBlockTypes(tagname))
        self.LibraryPanel.SetFocus()
    
    def OnOK(self, event):
        """
        Called when dialog OK button is pressed
        Test if parameters defined are valid
        @param event: wx.Event from OK button
        """
        message = None
        
        # Get block type selected
        selected = self.LibraryPanel.GetSelectedBlock()
        
        # Get block type name and if block is a function block
        block_name = self.BlockName.GetValue()
        name_enabled = self.BlockName.IsEnabled()
        
        # Test that a type has been selected for block
        if selected is None:
            message = _("Form isn't complete. Valid block type must be selected!")
        
        # Test, if block is a function block, that a name have been defined
        elif name_enabled and block_name == "":
            message = _("Form isn't complete. Name must be filled!")
        
        # Show error message if an error is detected
        if message is not None:
            self.ShowMessage(message)
        
        # Test block name validity if necessary
        elif not name_enabled or self.TestBlockName(block_name):
            BlockPreviewDialog.OnOK(self, event)
    
    def SetValues(self, values):
        """
        Set default block parameters
        @param values: Block parameters values
        """
        # Extract block type defined in parameters
        blocktype = values.get("type", None)
        
        # Define regular expression for determine if block name is block
        # default name
        default_name_model = re.compile(
            "%s[0-9]+" % blocktype if blocktype is not None else ".*")
        
        # Select block type in library panel    
        if blocktype is not None:
            self.LibraryPanel.SelectTreeItem(blocktype, 
                                             values.get("inputs", None))
        
        # For each parameters defined, set corresponding control value
        for name, value in values.items():
            if name == "name":
                # Parameter is block name
                if value != "":
                    # Set default block name for testing
                    self.DefaultBlockName = value
                    
                    # Test if block name is type default block name and save
                    # block name if not (name have been typed by user)
                    if default_name_model.match(value) is None:
                        self.CurrentBlockName = value
            
                self.BlockName.ChangeValue(value)
            
            else:
                control = self.ParamsControl.get(name, None)
                if control is not None:
                    control.SetValue(value)
        
        # Refresh preview panel
        self.RefreshPreview()

    def GetValues(self):
        """
        Return block parameters defined in dialog
        @return: {parameter_name: parameter_value,...}
        """
        values = self.LibraryPanel.GetSelectedBlock()
        if self.BlockName.IsEnabled() and self.BlockName.GetValue() != "":
            values["name"] = self.BlockName.GetValue()
        values["width"], values["height"] = self.Block.GetSize()
        values.update({
            name: control.GetValue()
            for name, control in self.ParamsControl.iteritems()})
        return values
        
    def OnLibraryTreeItemSelected(self, event):
        """
        Called when block type selected in library panel
        @param event: wx.TreeEvent
        """
        # Get type selected in library panel
        values = self.LibraryPanel.GetSelectedBlock()
        
        # Get block type informations
        blocktype = (self.Controller.GetBlockType(values["type"], 
                                                  values["inputs"])
                     if values is not None else None)
        
        # Set input number spin control according to block type informations
        if blocktype is not None:
            self.Inputs.SetValue(len(blocktype["inputs"]))
            self.Inputs.Enable(blocktype["extensible"])
        else:
            self.Inputs.SetValue(2)
            self.Inputs.Enable(False)
        
        # Update block name with default value if block type is a function and
        # current block name wasn't typed by user
        if blocktype is not None and blocktype["type"] != "function":
            self.BlockName.Enable(True)
            self.BlockName.ChangeValue(
                self.CurrentBlockName
                if self.CurrentBlockName is not None
                else self.Controller.GenerateNewName(
                    self.TagName, None, values["type"]+"%d", 0))
        else:
            self.BlockName.Enable(False)
            self.BlockName.ChangeValue("")
        
        # Refresh preview panel
        self.RefreshPreview()
    
    def OnNameChanged(self, event):
        """
        Called when block name value changed
        @param event: wx.TextEvent
        """
        if self.BlockName.IsEnabled():
            # Save block name typed by user
            self.CurrentBlockName = self.BlockName.GetValue()
            self.RefreshPreview()
        event.Skip()
    
    def OnInputsChanged(self, event):
        """
        Called when block inputs number changed
        @param event: wx.SpinEvent
        """
        if self.Inputs.IsEnabled():
            self.RefreshPreview()
        event.Skip()
    
    def OnExecutionOrderChanged(self, event):
        """
        Called when block execution order value changed
        @param event: wx.SpinEvent
        """
        self.RefreshPreview()
        event.Skip()
    
    def OnExecutionControlChanged(self, event):
        """
        Called when block execution control value changed
        @param event: wx.SpinEvent
        """
        self.RefreshPreview()
        event.Skip()
    
    def RefreshPreview(self):
        """
        Refresh preview panel of graphic element
        Override BlockPreviewDialog function
        """
        # Get type selected in library panel
        values = self.LibraryPanel.GetSelectedBlock()
        
        # If a block type is selected in library panel
        if values is not None:
            blockname = (self.BlockName.GetValue()
                         if self.BlockName.IsEnabled()
                         else "")
            
            # Set graphic element displayed, creating a FBD block element
            self.Block = FBD_Block(self.Preview, values["type"], 
                    blockname, 
                    extension = self.Inputs.GetValue(), 
                    inputs = values["inputs"], 
                    executionControl = self.ExecutionControl.GetValue(), 
                    executionOrder = self.ExecutionOrder.GetValue())
        
        # Reset graphic element displayed
        else:
            self.Block = None 
        
        # Call BlockPreviewDialog function
        BlockPreviewDialog.RefreshPreview(self)
