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
            #inkex.utils.debug("os.getcwd(): "+os.getcwd())
            #inkex.utils.debug(os.path.splitext(stl_filename)[0])
            cmd = os.getcwd() + "\\papercraft\\unfold.exe" + " < \"" + stl_filename + "\" > " + outname
            #inkex.utils.debug("cmd: "+cmd)
            p = Popen(cmd, shell=True)
            #inkex.utils.debug(p.communicate())	
            p.wait()
            if p.returncode == 0:
              #inkex.utils.debug("OK")			
              doc = etree.parse(os.getcwd() + "\\" + outname)
              #inkex.utils.debug(etree.tostring(doc))
              doc.write(sys.stdout.buffer)
if __name__ == '__main__':
    gc = Unfold()