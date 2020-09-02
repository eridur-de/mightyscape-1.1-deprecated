#!/usr/bin/env python3
import sys
import os
import inkex
import subprocess
from subprocess import Popen
from lxml import etree

class Unfold(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        stl_filename = sys.argv[1]
        #inkex.utils.debug("stl_filename: "+stl_filename)
        if os.name=="nt":
            outname = "papercraft_unfold_output.svg"
            #remove old file if existent
            if os.path.exists(outname):
              os.remove(outname)
            if os.path.exists("unfold.exe.stackdump"):
              os.remove("unfold.exe.stackdump")
            #convert the STL to have a binary one and wait until conversion finished before running papercraft
            cmd = os.getcwd() + "\\papercraft\\STLConverter.exe" + " \"" + stl_filename + "\""
            p = Popen(cmd, shell=True)
            #inkex.utils.debug(cmd)
            #inkex.utils.debug("os.getcwd(): "+os.getcwd())
            #inkex.utils.debug(os.path.splitext(stl_filename)[0])
            p.wait()
            cmd2 = os.getcwd() + "\\papercraft\\unfold.exe" + " < \"" + os.path.splitext(stl_filename)[0] + "-binary.stl\" > " + outname
            #inkex.utils.debug("cmd2: "+cmd2)
            p2 = Popen(cmd2, shell=True)
            #inkex.utils.debug(p2.communicate())
            p2.wait()
            if p2.returncode == 0:
              #inkex.utils.debug("OK")			
              doc = etree.parse(os.getcwd() + "\\" + outname)
              doc.write(sys.stdout.buffer)
              
if __name__ == '__main__':
    gc = Unfold()