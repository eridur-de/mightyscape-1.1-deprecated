#!/usr/bin/env python3

"""
Extension for InkScape 1.0

CutOptim OS Wrapper script to make CutOptim work on Windows and Linux systems without duplicating .inx files

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 31.08.2020
Last patch: 31.08.2020
License: GNU GPL v3

"""

import inkex
import sys
import os
from lxml import etree

class CutOptimWrapper(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        args = sys.argv[1:] 
        for arg in args:
            key=arg.split("=")[0]
            if len(arg.split("=")) == 2:
                value=arg.split("=")[1]
                try:
                    self.arg_parser.add_argument(key, default=key)
                except:
                    pass #ignore duplicate id arg

    def effect(self):
        cmd=""
        if os.name == "nt":
            cutoptim="CutOptim.exe"
        else:
            cutoptim="./CutOptim"
        #inkex.utils.debug(cmd)
        cmd += cutoptim
        for arg in vars(self.options):
            if arg != "output" and arg != "ids" and arg != "selected_nodes":
                #inkex.utils.debug(str(arg) + " = " + str(getattr(self.options, arg)))
                #fix behaviour of "original" arg which does not correctly gets interpreted if set to false
                if arg == "original" and str(getattr(self.options, arg)) == "false":
                    continue
                if arg == "input_file":
                   cmd += " --file " + str(getattr(self.options, arg))
                else:
                    cmd += " --" + arg + " " + str(getattr(self.options, arg))

        if os.name == "nt":
            cmd += " --output cutoptim.svg"    
        else:
            cmd += " --output /tmp/cutoptim.svg"
        #inkex.utils.debug(str(cmd))
        
        # run CutOptim with the parameters provided
        with os.popen(cmd, "r") as cutoptim:
            result = cutoptim.read()
        
        # check output existence
        try:
            stream = open("/tmp/cutoptim.svg", 'r')
        except FileNotFoundError as e:
            inkex.utils.debug("There was no SVG output generated. Cannot continue")
            exit(1)
            
        # write the generated SVG into InkScape's canvas
        p = etree.XMLParser(huge_tree=True)
        doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True))
        stream.close()
        doc.write(sys.stdout.buffer)
        
if __name__ == '__main__':
    CutOptimWrapper().run()