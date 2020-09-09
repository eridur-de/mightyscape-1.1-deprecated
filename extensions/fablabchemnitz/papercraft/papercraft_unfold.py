#!/usr/bin/env python3
import sys
import os
import inkex
import tempfile

import subprocess
from subprocess import Popen, PIPE
from lxml import etree

#specific imports for model-converter-python
import functools as fc
import d3.model.tools as mt
from d3.model.basemodel import Vector

"""
Extension for InkScape 1.0

Import any DWG or DXF file using ODA File Converter, sk1 UniConvertor, ezdxf and more tools.

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 08.09.2020
Last patch: 08.09.2020
License: GNU GPL v3

#################################################################


This tool converts a lot of different formats into STL Format. The STL then gets unfolded (flattened) to make a papercraft model. You can select between different engines. The used tools are
- converters
    - openjscad
    - model-converter-python
- repairers
    - ADMesh
- unfolders
    - osresearch/papercraft

#################################################################

openjscad [-v] <file> [-of <format>] [-o <output>]
    <file>  :    input file (Supported types: .jscad, .js, .scad, .stl, .amf, .obj, .gcode, .svg, .json)
    <output>:    output file (Supported types: .jscad, .stl, .amf, .dxf, .svg, .json)
    <format>:    'jscad', 'stla' (STL ASCII, default), 'stlb' (STL Binary), 'amf', 'dxf', 'svg', 'json'

#################################################################

ADMesh version 0.99.0dev
Copyright (C) 1995, 1996  Anthony D. Martin
Usage: /usr/share/inkscape/extensions/mightyscape-1.X/extensions/fablabchemnitz/papercraft/.libs/admesh [OPTION]... file

     --x-rotate=angle     Rotate CCW about x-axis by angle degrees
     --y-rotate=angle     Rotate CCW about y-axis by angle degrees
     --z-rotate=angle     Rotate CCW about z-axis by angle degrees
     --xy-mirror          Mirror about the xy plane
     --yz-mirror          Mirror about the yz plane
     --xz-mirror          Mirror about the xz plane
     --scale=factor       Scale the file by factor (multiply by factor)
     --scale-xyz=x,y,z    Scale the file by a non uniform factor
     --translate=x,y,z    Translate the file to x, y, and z
     --merge=name         Merge file called name with input file
 -e, --exact              Only check for perfectly matched edges
 -n, --nearby             Find and connect nearby facets. Correct bad facets
 -t, --tolerance=tol      Initial tolerance to use for nearby check = tol
 -i, --iterations=i       Number of iterations for nearby check = i
 -m, --increment=inc      Amount to increment tolerance after iteration=inc
 -u, --remove-unconnected Remove facets that have 0 neighbors
 -f, --fill-holes         Add facets to fill holes
 -d, --normal-directions  Check and fix direction of normals(ie cw, ccw)
     --reverse-all        Reverse the directions of all facets and normals
 -v, --normal-values      Check and fix normal values
 -c, --no-check           Don't do any check on input file
 -b, --write-binary-stl=name   Output a binary STL file called name
 -a, --write-ascii-stl=name    Output an ascii STL file called name
     --write-off=name     Output a Geomview OFF format file called name
     --write-dxf=name     Output a DXF format file called name
     --write-vrml=name    Output a VRML format file called name
     --help               Display this help and exit
     --version            Output version information and exit

The functions are executed in the same order as the options shown here.
So check here to find what happens if, for example, --translate and --merge
options are specified together.  The order of the options specified on the
command line is not important.

#################################################################

Module licenses
- papercraft      (https://github.com/osresearch/papercraft)            - GPL v2 License
- openjscad       (https://github.com/jscad/OpenJSCAD.org)              - MIT License and other, not bundled. Install it separately
- model-converter (https://github.com/tforgione/model-converter-python) - MIT License
- admesh          (https://github.com/admesh/admesh)                    - GPL License

#TODO
- admesh Parameter als extra Tab in InkScape
- fix canvas resize
- Windows Executables
- Doku Seite mit HowTo Compile / install openjscad + admesh

"""

class Unfold(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--tab")
        self.arg_parser.add_argument("--inputfile")
        self.arg_parser.add_argument("--resizetoimport", type=inkex.Boolean, default=True, help="Resize the canvas to the imported drawing's bounding box") 
        self.arg_parser.add_argument("--extraborder", type=float, default=0.0)
        self.arg_parser.add_argument("--extraborder_units")              
        self.arg_parser.add_argument("--show_fstl", type=inkex.Boolean, default=True, help="Show converted (and fixed) STL in fstl Viewer")
        self.arg_parser.add_argument("--fixmesh", type=inkex.Boolean, default=True)    
        self.arg_parser.add_argument("--exact", type=inkex.Boolean, default=True, help="Only check for perfectly matched edges")
        self.arg_parser.add_argument("--nearby", type=inkex.Boolean, default=True, help="Find and connect nearby facets. Correct bad facets")
        self.arg_parser.add_argument("--tolerance", type=float, default=0.0, help="Initial tolerance to use for nearby check")
        self.arg_parser.add_argument("--iterations", type=int, default=1, help="Number of iterations for nearby check")
        self.arg_parser.add_argument("--increment", type=float, default=0.0, help="Amount to increment tolerance after iteration")
        self.arg_parser.add_argument("--remove_unconnected", type=inkex.Boolean, default=True, help="Remove facets that have 0 neighbors")
        self.arg_parser.add_argument("--fill_holes", type=inkex.Boolean, default=True, help="Add facets to fill holes")
        self.arg_parser.add_argument("--normal_directions", type=inkex.Boolean, default=True, help="Check and fix direction of normals (ie cw, ccw)")
        self.arg_parser.add_argument("--reverse_all", type=inkex.Boolean, default=True, help="Reverse the directions of all facets and normals")
        self.arg_parser.add_argument("--normal_values", type=inkex.Boolean, default=True, help="Check and fix normal values")
                     
    def effect(self):
        import_formats_model_converter=[".obj", ".off", ".ply"] #we could also handle stl but openscad does the better job 
        import_formats_openjscad=[".jscad", ".js", ".scad", ".stl", ".amf", ".gcode", ".json"] #we could also handle obj but model converter does the better job
        
        inputfile = self.options.inputfile
        if not os.path.exists(inputfile):
            inkex.utils.debug("The input file does not exist. Please select a proper file and try again.")
            exit(1)
        inputfile_format = (os.path.splitext(os.path.basename(inputfile))[1]).lower()
        if inputfile_format not in import_formats_model_converter and inputfile_format not in import_formats_openjscad:
            inkex.utils.debug("The input file format cannot be converted to a required format for flattening.")
            exit(1)
          
        converted_inputfile = os.path.join(tempfile.gettempdir(), os.path.splitext(os.path.basename(inputfile))[0] + ".stl")
        if os.path.exists(converted_inputfile):
              os.remove(converted_inputfile) #remove previously generated conversion file

        if inputfile_format in import_formats_model_converter:
            up_conversion = None
            with open(converted_inputfile, 'w') as f:
                f.write(mt.convert(inputfile, converted_inputfile, up_conversion))
        if inputfile_format in import_formats_openjscad:
            cmd = "openjscad \"" + inputfile + "\" -of stlb -o \"" + converted_inputfile + "\""
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            p.wait()
            if p.returncode != 0 or len(stderr) > 0: 
               inkex.utils.debug("openjscad conversion failed: %d %s %s" % (p.returncode, stdout, stderr))

        #we do this to convert possibly previously generated ASCII STL from model converter to binary STL to ensure always binary STLs
        cmd = "openjscad \"" + converted_inputfile + "\" -of stlb -o \"" + converted_inputfile + "\""
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        p.wait()
        if p.returncode != 0 or len(stderr) > 0: 
           inkex.utils.debug("openjscad conversion failed: %d %s %s" % (p.returncode, stdout, stderr))
               
        if not os.path.exists(converted_inputfile):
            inkex.utils.debug("Cannot find conversion output. Unable to continue")
            exit(1)
            
        # Run ADMesh mesh fixer to overwrite the STL with fixed output (binary output too)
        if self.options.fixmesh == True:
            if os.name=="nt":
                cmd = "admesh\\admesh.exe "
            else:
                cmd = "./admesh/admesh " 
            if self.options.exact == True: cmd += "--exact "
            if self.options.nearby == True: cmd += "--nearby "
            if self.options.tolerance > 0.0: cmd += "--tolerance " + str(self.options.tolerance) + " "
            if self.options.iterations > 1: cmd += "--iterations " + str(self.options.iterations) + " "
            if self.options.increment > 0.0: cmd += "--increment " + str(self.options.increment) + " "
            if self.options.remove_unconnected == True: cmd += "--remove-unconnected "
            if self.options.normal_directions == True: cmd += "--normal-directions "
            if self.options.fill_holes == True: cmd += "--fill-holes "
            if self.options.reverse_all == True: cmd += "--reverse-all "
            if self.options.normal_values == True: cmd += "--normal-values "    
            cmd += "\"" + converted_inputfile + "\" "
            cmd += "-b \"" + converted_inputfile + "\""
            p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
            stdout, stderr = p.communicate()
            p.wait()
            if p.returncode != 0: 
               inkex.utils.debug("admesh failed: %d %s %s" % (p.returncode, stdout, stderr))
         
        # Run papercraft flattening   
        converted_flattenfile = os.path.join(tempfile.gettempdir(), os.path.splitext(os.path.basename(inputfile))[0] + ".svg")
        if os.path.exists(converted_flattenfile):
              os.remove(converted_flattenfile) #remove previously generated conversion file  
        if os.name=="nt":
            cmd = "unfold\\unfold.exe" + " < \"" + converted_inputfile + "\" > \"" + converted_flattenfile + "\""
        else:
            cmd = "./unfold/unfold" + " < \"" + converted_inputfile + "\" > \"" + converted_flattenfile + "\"" 
        p = Popen(cmd, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        p.wait()
        if p.returncode != 0: 
           inkex.utils.debug("osresearch/papercraft unfold failed: %d %s %s" % (p.returncode, stdout, stderr))
               
        # Open converted output in fstl       
        if self.options.show_fstl == True:
            if os.name=="nt":
                cmd = "fstl\\fstl.exe \"" + converted_inputfile + "\""
            else:
                cmd = "./fstl/fstl \"" + converted_inputfile + "\""
            p = Popen(cmd, shell=True)
            p.wait()
               
        # Write the generated SVG into InkScape's canvas
        try:
            stream = open(converted_flattenfile, 'r')
        except FileNotFoundError as e:
            inkex.utils.debug("There was no SVG output generated. Cannot continue")
            exit(1)
        p = etree.XMLParser(huge_tree=True)
        doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True)).getroot()
        stream.close()
        doc.set('id', self.svg.get_unique_id('papercraft_unfold'))
        self.document.getroot().append(doc)              

        #adjust viewport and width/height to have the import at the center of the canvas - unstable at the moment.
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
                        #bbox.add(element.bounding_box())
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
    Unfold().run()