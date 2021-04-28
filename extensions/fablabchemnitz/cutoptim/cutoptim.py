#!/usr/bin/env python3

"""
Extension for InkScape 1.0

CutOptim OS Wrapper script to make CutOptim work on Windows and Linux systems without duplicating .inx files

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 31.08.2020
Last patch: 14.01.2021
License: GNU GPL v3

"""

import inkex
import sys
import os
from lxml import etree
import subprocess

class CutOptimWrapper(inkex.EffectExtension):
  
    def openDebugFile(self, file):
        DETACHED_PROCESS = 0x00000008
        if os.name == 'nt':
            subprocess.Popen(["explorer", file], close_fds=True, creationflags=DETACHED_PROCESS).wait()
        else:
            subprocess.Popen(["xdg-open", file], close_fds=True, start_new_session=True).wait()
        
    def add_arguments(self, pars):
        args = sys.argv[1:] 
        for arg in args:
            key=arg.split("=")[0]
            if len(arg.split("=")) == 2:
                value=arg.split("=")[1]
                try:
                    if key != "--id":
                        pars.add_argument(key, default=key)             
                except:
                    pass #ignore duplicate id arg

    def effect(self):
        cmd=""
        if os.name == "nt":
            cutoptim="CutOptim.exe"
        else:
            cutoptim="./CutOptim"
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

        output_file = None
        if os.name == "nt":
            output_file = "cutoptim.svg"    
        else:
            output_file = "/tmp/cutoptim.svg"
        
        cmd += " --output " + output_file 
        
        # run CutOptim with the parameters provided
        with os.popen(cmd, "r") as cutoptim:
            result = cutoptim.read()
        
        # check output existence
        try:
            stream = open(output_file, 'r')
        except FileNotFoundError as e:
            inkex.utils.debug("There was no SVG output generated. Cannot continue. Command was:")
            inkex.utils.debug(cmd)
            exit(1)

        if self.options.original == "false": #we need to use string representation of bool
            for element in self.document.getroot():
                if isinstance(element, inkex.ShapeElement):
                    element.delete()

        if self.options.debug_file == "true": #we need to use string representation of bool
            self.openDebugFile("Debug_CutOptim.txt")

        # write the generated SVG into Inkscape's canvas
        p = etree.XMLParser(huge_tree=True)
        doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True))
        stream.close()
        group = inkex.Group(id="CutOptim")
        targetLayer = doc.xpath('//svg:g[@inkscape:label="Placed_Layer"]', namespaces=inkex.NSS)[0]#.getchildren()[0]
        for element in targetLayer.getchildren():
            group.append(element)
        self.document.getroot().append(group)
                
if __name__ == '__main__':
    CutOptimWrapper().run()