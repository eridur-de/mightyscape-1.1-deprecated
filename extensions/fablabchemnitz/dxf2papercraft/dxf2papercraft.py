#!/usr/bin/env python3
import sys
import os
import inkex
import tempfile
import subprocess
from subprocess import Popen, PIPE
from lxml import etree
from inkex import Transform

"""
Extension for InkScape 1.0

Unfold and import DXF into InkScape using dxf2papercraft. This is some kind of wrapper extension utilizing kabeja to convert the dxf output from dxf2papercraft into SVG.
To make it work you need to install at least java

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 11.09.2020
Last patch: 11.09.2020
License: GNU GPL v3

Module licenses
- dxf2papercraft (dxf2papercraft.sourceforge.net) - GPL v3 License
- kabeja (http://kabeja.sourceforge.net/) - Apache v2

ToDos:
- in case of errors maybe think about adding ezdxf library to filter unsupported entities (similar like done in dxfdwgimporter extension)
- maybe add some DXF model preview tool (maybe a useless idea at all)
"""

class PapercraftUnfold(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--inputfile")
        self.arg_parser.add_argument("--resizetoimport", type=inkex.Boolean, default=True, help="Resize the canvas to the imported drawing's bounding box") 
        self.arg_parser.add_argument("--extraborder", type=float, default=0.0)
        self.arg_parser.add_argument("--extraborder_units")
        self.arg_parser.add_argument("--scalefactor", type=float, default=1.0, help="Manual scale factor")
        self.arg_parser.add_argument("--nomerge", type=inkex.Boolean, default=False, help="No merging of faces into single polygon")
        self.arg_parser.add_argument("--number", type=inkex.Boolean, default=False, help="Print face numbers (labels)")
        self.arg_parser.add_argument("--divide", type=inkex.Boolean, default=False, help="Draw each face separate")
        self.arg_parser.add_argument("--overlap", type=inkex.Boolean, default=False, help="Allow overlapping faces in cut-out sheet")
        self.arg_parser.add_argument("--hide", type=inkex.Boolean, default=False, help="Hide glue tabs")
        self.arg_parser.add_argument("--force", type=inkex.Boolean, default=False, help="Force glue tabs, even if intersecting faces")
        self.arg_parser.add_argument("--split", default="", help="Comma separated list of face numbers to disconnect from the rest")
        self.arg_parser.add_argument("--strategy", default=0, help="Generation strategy")
                   
    def effect(self):
        dxf_input = self.options.inputfile
        if not os.path.exists(dxf_input):
            inkex.utils.debug("The input file does not exist. Please select a proper file and try again.")
            exit(1)

        # Prepare output
        dxf_output = os.path.join(tempfile.gettempdir(), os.path.splitext(os.path.basename(dxf_input))[0] + ".dxf")
        svg_output = os.path.join(tempfile.gettempdir(), os.path.splitext(os.path.basename(dxf_input))[0] + ".svg")

        # Clean up possibly previously generated output file from dxf2papercraft
        if os.path.exists(dxf_output):
            try:
                os.remove(dxf_output)
            except OSError as e: 
                inkex.utils.debug("Error while deleting previously generated output file " + dxf_input)

        if os.path.exists("delete_me_later"):
            try:
                os.remove("delete_me_later")
            except OSError as e: 
                pass
        if os.path.exists("debug.dat"):
            try:
                os.remove("debug.dat")
            except OSError as e: 
                pass

        # Run dxf2papercraft (make unfold)
        if os.name=="nt":
            dxf2ppc_cmd = "dxf2papercraft\\dxf2papercraft.exe "
        else:
            dxf2ppc_cmd = "./dxf2papercraft/dxf2papercraft "
        if self.options.nomerge  == True: dxf2ppc_cmd += "--nomerge "
        if self.options.number   == True: dxf2ppc_cmd += "--number "
        if self.options.divide   == True: dxf2ppc_cmd += "--divide "
        if self.options.overlap  == True: dxf2ppc_cmd += "--overlap "
        if self.options.hide     == True: dxf2ppc_cmd += "--hide "
        if self.options.force    == True: dxf2ppc_cmd += "--force "
        if self.options.split is not None and self.options.split != "": 
            dxf2ppc_cmd += "--split " + str(self.options.split) + " " #warning. this option has no validator! 
        dxf2ppc_cmd += "--strategy " + self.options.strategy + " "
        dxf2ppc_cmd += "\"" + dxf_input + "\" "
        dxf2ppc_cmd += "\"" + dxf_output + "\""
        p = Popen(dxf2ppc_cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        p.wait()
        if p.returncode != 0: 
           inkex.utils.debug("dxf2papercraft failed: %d %s %s" % (p.returncode, stdout, stderr))
           exit(1)
         
        #print command 
        #inkex.utils.debug(dxf2ppc_cmd)
          
        if not os.path.exists(dxf_output):
            inkex.utils.debug("There was no DXF output generated by dxf2papercraft. Maybe the input file is not a correct 3D DXF. Please check your model file.")
            exit(1)
          
        # Convert the DXF output to SVG
        wd = os.path.join(os.getcwd(), "kabeja")
        proc = subprocess.Popen("java -jar launcher.jar -nogui -pipeline svg " + dxf_output + " " + svg_output, cwd=wd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = proc.communicate()
        if proc.returncode != 0: 
           inkex.errormsg("kabeja failed: %d %s %s" % (proc.returncode, stdout, stderr))  

        # Write the generated SVG into InkScape's canvas
        try:
            stream = open(svg_output, 'r')
        except FileNotFoundError as e:
            inkex.utils.debug("There was no SVG output generated by kabeja. Cannot continue")
            exit(1)
        p = etree.XMLParser(huge_tree=True)
        doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True)).getroot()
        stream.close()
        doc.set('id', self.svg.get_unique_id('dxf2papercraft-'))
        self.document.getroot().append(doc)              

        #do some viewport adjustments
        doc.set('width','')
        doc.set('height','')
        doc.set('viewBox','')
        doc.getchildren()[0].set('transform','')

        #apply scale factor
        node = doc.getchildren()[1]
        translation_matrix = [[self.options.scalefactor, 0.0, 0.0], [0.0, self.options.scalefactor, 0.0]]            
        node.transform = Transform(translation_matrix) * node.transform

        #Adjust viewport and width/height to have the import at the center of the canvas - unstable at the moment.
        if self.options.resizetoimport: 
            elements = []
            for child in doc.getchildren():
                #if child.tag == inkex.addNS('g','svg'):
                elements.append(child)

            #build sum of bounding boxes and ignore errors for faulty elements (sum function often fails for that usecase!)
            bbox = None
            try:
                bbox = elements[0].bounding_box() #init with the first bounding box of the tree (and hope that it is not a faulty one)
            except Exception as e:
                #inkex.utils.debug(str(e))
                pass
            count = 0
            for element in elements:
                if count != 0: #skip the first
                    try:
                        bbox += element.bounding_box()
                    except Exception as e:
                        #inkex.utils.debug(str(e))
                        pass
                count += 1 #some stupid counter
            if bbox is not None:
                root = self.svg.getElement('//svg:svg');
                offset = self.svg.unittouu(str(self.options.extraborder) + self.options.extraborder_units)
                root.set('viewBox', '%f %f %f %f' % (bbox.left - offset, bbox.top - offset, bbox.width + 2 * offset, bbox.height + 2 * offset))
                root.set('width', bbox.width + 2 * offset)
                root.set('height', bbox.height + 2 * offset)

if __name__ == '__main__':
    PapercraftUnfold().run()