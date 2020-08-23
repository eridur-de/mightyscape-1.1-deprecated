#!/usr/bin/env python3

"""
Extension for InkScape 1.0

Import any DWG or DXF file using ODA File Converter, sk1 UniConverter, ezdxf and more tools.

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 23.08.2020
Last patch: 23.08.2020
License: GNU GPL v3

Module licenses
- ezdxf (https://github.com/mozman/ezdxf) - MIT License
- node.js (https://raw.githubusercontent.com/nodejs/node/master/LICENSE) - MIT License
- https://github.com/bjnortier/dxf - MIT License
- ODA File Converter - not bundled (due to restrictions by vendor)
- sk1 UniConverter (https://github.com/sk1project/uniconvertor) - AGPL v3.0 - not bundled
"""

import inkex
import sys
import os
import re
import subprocess, tempfile
from lxml import etree
from subprocess import Popen, PIPE
import shutil
from pathlib import Path    

#ezdxf related imports
import matplotlib.pyplot as plt
import ezdxf 
from ezdxf.addons.drawing import RenderContext, Frontend 
from ezdxf.addons.drawing.matplotlib_backend import MatplotlibBackend
from ezdxf.addons import Importer

class DXFDWGImport(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--odafileconverter", default=r"C:\Program Files\ODA\ODAFileConverter_title 21.6.0\ODAFileConverter.exe", help="Full path to 'ODAFileConverter.exe'")
        self.arg_parser.add_argument("--odahidewindow", type=inkex.Boolean, default=True, help="Hide ODA GUI window")
        self.arg_parser.add_argument("--outputformat", default="ACAD2018_DXF", help="ODA AutoCAD Output version")
        self.arg_parser.add_argument("--sk1uniconverter", default=r"C:\Program Files (x86)\sK1 Project\UniConvertor-1.1.6\uniconvertor.cmd", help="Full path to 'uniconvertor.cmd'")
        self.arg_parser.add_argument("--opendironerror", type=inkex.Boolean, default=True, help="Open containing output directory on conversion errors")
        self.arg_parser.add_argument("--skip_dxf_to_dxf", type=inkex.Boolean, default=False, help="Skip conversion from DXF to DXF")
        self.arg_parser.add_argument("--audit_repair", type=inkex.Boolean, default=True, help="Perform audit / autorepair")
        self.arg_parser.add_argument("--dxf_to_svg_parser", default="bjnortier", help="Choose a DXF to SVG parser")
        self.arg_parser.add_argument("--resizetoimport", type=inkex.Boolean, default=True, help="Resize the canvas to the imported drawing's bounding box")
        self.arg_parser.add_argument("--THREE_DFACE", type=inkex.Boolean, default=True) #3DFACE
        self.arg_parser.add_argument("--ARC",         type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--BLOCK",       type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--CIRCLE",      type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--ELLIPSE",     type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--LINE",        type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--LWPOLYLINE",  type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--POINT",       type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--POLYLINE",    type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--POP_TRAFO",   type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--SEQEND",      type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--SOLID",       type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--SPLINE",      type=inkex.Boolean, default=True)   
        self.arg_parser.add_argument("--TABLE",       type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--VERTEX",      type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--VIEWPORT",    type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--inputfile")    
        self.arg_parser.add_argument("--extraborder", type=float, default=0.0)
        self.arg_parser.add_argument("--extraborder_units")      
        self.arg_parser.add_argument("--ezdxf_output_version", default="SAME")    
        self.arg_parser.add_argument("--ezdxf_preprocessing", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--allentities", type=inkex.Boolean, default=True)
        
    def effect(self):         
        #get input file and copy it to some new temporary directory
        inputfile = self.options.inputfile
        
        temp_input_dir = os.path.join(tempfile.gettempdir(),"inkscape-oda-convert-input")
        
        #remove the input directory before doing new job
        shutil.rmtree(temp_input_dir, ignore_errors=True)
        if not os.path.exists(temp_input_dir):
            os.mkdir(temp_input_dir) #recreate blank dir
        
        shutil.copy2(inputfile, os.path.join(temp_input_dir, Path(inputfile).name)) # complete target filename given
        
        #Prepapre output conversion
        outputfilebase = os.path.splitext(os.path.splitext(os.path.basename(inputfile))[0])[0]
        inputfile_ending = os.path.splitext(os.path.splitext(os.path.basename(inputfile))[1])[0]
        temp_output_dir = os.path.join(tempfile.gettempdir(),"inkscape-oda-convert-output")
        
        #remove the output directory before doing new job
        shutil.rmtree(temp_output_dir, ignore_errors=True)
        if not os.path.exists(temp_output_dir):
            os.mkdir(temp_output_dir)
        
        autocad_version   = self.options.outputformat.split("_")[0]
        autocad_format    = self.options.outputformat.split("_")[1]
        if self.options.audit_repair: #overwrite string bool with int value
            self.options.audit_repair = "1" 
        else:
            self.options.audit_repair = "0"
        entityspace = []
        if self.options.allentities or self.options.THREE_DFACE: entityspace.append("3DFACE")
        if self.options.allentities or self.options.ARC:         entityspace.append("ARC")
        if self.options.allentities or self.options.BLOCK:       entityspace.append("BLOCK")
        if self.options.allentities or self.options.CIRCLE:      entityspace.append("CIRCLE")
        if self.options.allentities or self.options.ELLIPSE:     entityspace.append("ELLIPSE")
        if self.options.allentities or self.options.LINE:        entityspace.append("LINE")
        if self.options.allentities or self.options.LWPOLYLINE:  entityspace.append("LWPOLYLINE")
        if self.options.allentities or self.options.POINT:       entityspace.append("POINT")
        if self.options.allentities or self.options.POLYLINE:    entityspace.append("POLYLINE")
        if self.options.allentities or self.options.POP_TRAFO:   entityspace.append("POP_TRAFO")
        if self.options.allentities or self.options.SEQEND:      entityspace.append("SEQEND")
        if self.options.allentities or self.options.SOLID:       entityspace.append("SOLID")
        if self.options.allentities or self.options.SPLINE:      entityspace.append("SPLINE")
        if self.options.allentities or self.options.TABLE:       entityspace.append("TABLE")
        if self.options.allentities or self.options.VERTEX:      entityspace.append("VERTEX")
        if self.options.allentities or self.options.VIEWPORT:    entityspace.append("VIEWPORT")
        
        #ODA to ezdxf mapping
        oda_ezdxf_mapping = []
        oda_ezdxf_mapping.append(["ACAD9","R12","AC1004"]) #this mapping is not supported directly. so we use the lowest possible which is R12
        oda_ezdxf_mapping.append(["ACAD10","R12","AC1006"]) #this mapping is not supported directly. so we use the lowest possible which is R12
        oda_ezdxf_mapping.append(["ACAD12","R12","AC1009"])
        oda_ezdxf_mapping.append(["ACAD13","R2000","AC1012"]) #R13 was overwritten by R2000 which points to AC1015 instead of AC1014 (see documentation)
        oda_ezdxf_mapping.append(["ACAD14","R2000","AC1014"]) #R14 was overwritten by R2000 which points to AC1015 instead of AC1014 (see documentation)
        oda_ezdxf_mapping.append(["ACAD2000","R2000","AC1015"])
        oda_ezdxf_mapping.append(["ACAD2004","R2004","AC1018"])
        oda_ezdxf_mapping.append(["ACAD2007","R2007","AC1021"])
        oda_ezdxf_mapping.append(["ACAD2010","R2010","AC1024"])
        oda_ezdxf_mapping.append(["ACAD2013","R2013","AC1027"])
        oda_ezdxf_mapping.append(["ACAD2018","R2018","AC1032"])
        
        ezdxf_autocad_format = None
        for oe in oda_ezdxf_mapping:
            if oe[0] == autocad_version: 
                ezdxf_autocad_format = oe[1]
                break
        if ezdxf_autocad_format is None:
            inkex.errormsg("ezdxf conversion format version unknown")    
        
        if self.options.skip_dxf_to_dxf == False or inputfile_ending == ".dwg":
            # Build and run ODA File Converter command // "cmd.exe /c start \"\" /MIN /WAIT"
            oda_cmd = [self.options.odafileconverter, temp_input_dir, temp_output_dir, autocad_version, autocad_format, "0", self.options.audit_repair]
            if self.options.odahidewindow:
                info = subprocess.STARTUPINFO() #hide the ODA File Converter window because it is annoying
                info.dwFlags = 1
                info.wShowWindow = 0
                proc = subprocess.Popen(oda_cmd, startupinfo=info, shell=False, stdout=PIPE, stderr=PIPE)
            else: proc = subprocess.Popen(oda_cmd, shell=False, stdout=PIPE, stderr=PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0: 
               inkex.errormsg("ODA File Converter failed: %d %s %s" % (proc.returncode, stdout, stderr))
        if self.options.skip_dxf_to_dxf: #if true we need to move the file to simulate "processed"
            shutil.move(os.path.join(temp_input_dir, Path(inputfile).name), os.path.join(temp_output_dir, Path(inputfile).name))
        
        # Prepare files
        dxf_file = os.path.join(temp_output_dir, outputfilebase + ".dxf")
        svg_file = os.path.join(temp_output_dir, outputfilebase + ".svg")
        
        # Preprocessing DXF to DXF (entity filter)
        if self.options.ezdxf_preprocessing:
            #uniconverter does not handle all entities. we parse the file to exlude stuff which lets uniconverter fail
            dxf = ezdxf.readfile(dxf_file)
            modelspace = dxf.modelspace()
            allowed_entities = []
            # supported entities by UniConverter- impossible: MTEXT TEXT INSERT and a lot of others
            query_string = str(entityspace)[1:-1].replace("'","").replace(",","")
            for e in modelspace.query(query_string):
                allowed_entities.append(e)
            #inkex.utils.debug(ezdxf_autocad_format)
            #inkex.utils.debug(self.options.ezdxf_output_version)
            if self.options.ezdxf_output_version == "SAME":                
                doc = ezdxf.new(ezdxf_autocad_format)
            else:
                doc = ezdxf.new(self.options.ezdxf_output_version) #use the string values from inx file. Required to match the values from ezdxf library. See Python reference
            msp = doc.modelspace()
            for e in allowed_entities:
                msp.add_foreign_entity(e)
            doc.saveas(dxf_file)
        
        # make SVG from DXF
        if self.options.dxf_to_svg_parser == "uniconverter":         
            uniconverter_cmd = [self.options.sk1uniconverter, dxf_file, svg_file]
            #inkex.utils.debug(uniconverter_cmd)
            proc = subprocess.Popen(uniconverter_cmd, shell=False, stdout=PIPE, stderr=PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0: 
               inkex.errormsg("UniConverter failed: %d %s %s" % (proc.returncode, stdout, stderr))
               if self.options.opendironerror:
                   subprocess.Popen(["explorer",temp_output_dir],close_fds=True)
                                    
        elif self.options.dxf_to_svg_parser == "bjnortier":
            bjnortier_cmd = ["node", os.path.join("node_modules","dxf","lib","cli.js"), dxf_file, svg_file]
            #inkex.utils.debug(bjnortier_cmd)
            proc = subprocess.Popen(bjnortier_cmd, shell=False, stdout=PIPE, stderr=PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0: 
               inkex.errormsg("node.js DXF to SVG conversion failed: %d %s %s" % (proc.returncode, stdout, stderr))
               if self.options.opendironerror:
                   subprocess.Popen(["explorer",temp_output_dir],close_fds=True)
        elif self.options.dxf_to_svg_parser == "ezdxf":
            doc = ezdxf.readfile(dxf_file)
            #doc.header['$DIMSCALE'] = 0.2 does not apply to the plot :-(
            #inkex.utils.debug(doc.header['$DIMSCALE'])
            #inkex.utils.debug(doc.header['$MEASUREMENT'])
            auditor = doc.audit() #audit & repair DXF document before rendering
            # The auditor.errors attribute stores severe errors, which *may* raise exceptions when rendering.
            if len(auditor.errors) == 0:
                fig = plt.figure()
                ax = plt.axes([0., 0., 1., 1.], frameon=False, xticks=[], yticks=[])
                #ax.patches = []
                plt.axis('off')
                plt.margins(0, 0)
                plt.gca().xaxis.set_major_locator(plt.NullLocator())
                plt.gca().yaxis.set_major_locator(plt.NullLocator())
                plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
                out = MatplotlibBackend(fig.add_axes(ax))
                Frontend(RenderContext(doc), out).draw_layout(doc.modelspace(), finalize=True)
                #plt.show()
                #fig.savefig(os.path.join(temp_output_dir, outputfilebase + ".png"), dpi=300)  
                fig.savefig(svg_file) #see https://matplotlib.org/3.1.1/api/_as_gen/matplotlib.pyplot.savefig.html
        else:
            inkex.utils.debug("undefined parser")
            exit(1)
        
        # Write the generated SVG into canvas
        stream = open(svg_file, 'r')
        p = etree.XMLParser(huge_tree=True)
        doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True)).getroot()
        stream.close()

        #newGroup = self.document.getroot().add(inkex.Group())
        doc.set('id', self.svg.get_unique_id('dxf_dwg_import'))
        self.document.getroot().append(doc)

        #get children of the doc and move them one group above - we don't do this for bjnortier tool because this has different structure which we don't want to disturb
        if self.options.dxf_to_svg_parser == "uniconverter":
            elements = []
            emptyGroup = None
            for firstGroup in doc.getchildren():
                emptyGroup = firstGroup
                for element in firstGroup.getchildren():
                    elements.append(element)
                #break #only one cycle - could be bad idea or not                
            for element in elements:
                doc.set('id', self.svg.get_unique_id('dxf_dwg_import'))
                doc.insert(doc.index(firstGroup), element)
            
            if emptyGroup is not None:
                 emptyGroup.getparent().remove(emptyGroup)
             
        #empty the following vals because they destroy the size aspects of the import        
        if self.options.dxf_to_svg_parser == "bjnortier":        
            doc.set('width','')
            doc.set('height','')
            doc.set('viewBox','')
            doc.getchildren()[0].set('transform','')
            
        #adjust viewport and width/height to have the import at the center of the canvas - unstable at the moment.
        if self.options.resizetoimport: 
            elements = []
            for child in doc.getchildren():
                #if child.tag == inkex.addNS('g','svg'):
                elements.append(child)

            #build some of bounding boxes and ignore errors for faulty elements (sum function often fails for that usecase!)
            bbox = None
            try:
                bbox = elements[0].bounding_box() #init with the first bounding box of the tree (and hope that it is not a faulty one)
            except:
                pass
            count = 0
            for element in elements:
                if count == 0: continue #skip the first
                try:
                    bbox.add(element.bounding_box())
                except:
                    pass
                count += 1 #some stupid counter
            if bbox is not None:
                root = self.svg.getElement('//svg:svg');
                offset = self.svg.unittouu(str(self.options.extraborder) + self.options.extraborder_units)
                root.set('viewBox', '%f %f %f %f' % (bbox.left - offset, bbox.top - offset, bbox.width + 2 * offset, bbox.height + 2 * offset))
                root.set('width', bbox.width + 2 * offset)
                root.set('height', bbox.height + 2 * offset)
        
DXFDWGImport().run()