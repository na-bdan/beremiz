#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This file is part of Beremiz, a Integrated Development Environment for
# programming IEC 61131-3 automates supporting plcopen standard and CanFestival.
#
# Copyright (C) 2007: Edouard TISSERANT and Laurent BESSARD
# Copyright (C) 2017: Andrey Skvortsov
#
# See COPYING file for copyrights details.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


from __future__ import print_function
import os
import sys
import getopt

import BeremizIDE
import ProjectController

os.system("")


class LogStdOut(object):
    OK = u'\033[32m' # greem
    OK = u'\033[37m' # white
    WARNING = u'\033[33m'
    FAIL = u'\033[31m'
    ENDC = u'\033[0m'

    def __init__(self, output, risecall):
        pass

    def write(self, s, style=None):
        if s:
            # Translated unicode strings can't be concatenated with ANSI escapes for some reason. Using a workaround:
            print((style if style else self.OK), end="")
            print(s.rstrip(), end="")
            print(self.ENDC)

    def write_warning(self, s):
        self.write(s, self.WARNING)

    def write_error(self, s):
        self.write(s, self.FAIL)

    def flush(self):
        pass

    def progress(self, text):
        pass


class BeremizCompiler(object):
    def __init__(self):
        self.projectOpen = None
        self.buildPath = None
        self.targetname = None

    def Usage(self):
        print("Usage:")
        print("%s [Projectpath] [Buildpath]" % sys.argv[0])
        print("")
        print("Supported options:")
        print("-h --help                    Print this help")
        print("-t --target targetname       Build for specified target (Win32, Linux, Xenomai, etc.)")

    def SetCmdOptions(self):
        self.shortCmdOpts = "ht:"
        self.longCmdOpts = ["help", "target="]

    def ProcessOption(self, o, a):
        if o in ("-h", "--help"):
            self.Usage()
            sys.exit()
        if o in ("-t", "--target"):
            self.targetname = a

    def ProcessCommandLineArgs(self):
        self.SetCmdOptions()
        try:
            opts, args = getopt.getopt(sys.argv[1:], self.shortCmdOpts, self.longCmdOpts)
        except getopt.GetoptError:
            self.Usage()
            sys.exit(2)

        for o, a in opts:
            self.ProcessOption(o, a)

        if len(args) < 1 or len(args) > 2:
            self.Usage()
            sys.exit()

        elif len(args) == 1:
            self.projectOpen = args[0]
            self.builPath = None
        elif len(args) == 2:
            self.projectOpen = args[0]
            self.buildPath = args[1]

    def Compile(self):
        Log = LogStdOut(None, None)
        ctr = ProjectController.ProjectController(None, Log)

        result, err = ctr.LoadProject(self.projectOpen, self.buildPath)
        if err:
            print(result)
        else:
            if self.targetname:
                ctr.SetParamsAttribute("BeremizRoot.TargetType", self.targetname)
            self.targetname = ctr.GetTarget().getcontent().getLocalTag()
            print(self.targetname)
            err = ctr._Build()


if __name__ == '__main__':
    compiler = BeremizCompiler()
    compiler.ProcessCommandLineArgs()
    compiler.Compile()
