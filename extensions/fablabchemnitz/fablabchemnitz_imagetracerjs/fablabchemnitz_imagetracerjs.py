#!/usr/bin/env python3

import sys
import inkex
import os
import base64
import urllib.request as urllib
from PIL import Image
from io import BytesIO
from lxml import etree

"""
Extension for InkScape 1.X
Features
 - will vectorize your beautiful image into a more beautiful SVG trace with separated infills(break apart into single surfaces like a puzzle)
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 18.08.2020
Last patch: 18.08.2020
License: GNU GPL v3

Used version of imagetracerjs: https://github.com/jankovicsandras/imagetracerjs/commit/4d0f429efbb936db1a43db80815007a2cb113b34
"""

class Imagetracerjs (inkex.Effect):

    def checkImagePath(self, node):
        xlink = node.get('xlink:href')
        if xlink and xlink[:5] == 'data:':
            # No need, data alread embedded
            return

        url = urllib.urlparse(xlink)
        href = urllib.url2pathname(url.path)

        # Primary location always the filename itself.
        path = self.absolute_href(href or '')

        # Backup directory where we can find the image
        if not os.path.isfile(path):
            path = node.get('sodipodi:absref', path)

        if not os.path.isfile(path):
            inkex.errormsg('File not found "{}". Unable to embed image.').format(path)
            return

        if (os.path.isfile(path)):
            return path

    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--tabs")
        self.arg_parser.add_argument("--keeporiginal", type=inkex.Boolean, default=False, help="Keep original image on canvas")
        self.arg_parser.add_argument("--ltres", type=float, default=1.0, help="Error treshold straight lines")
        self.arg_parser.add_argument("--qtres", type=float, default=1.0, help="Error treshold quadratic splines")
        self.arg_parser.add_argument("--pathomit", type=int, default=8, help="Noise reduction - discard edge node paths shorter than")         
        self.arg_parser.add_argument("--rightangleenhance", type=inkex.Boolean, default=True, help="Enhance right angle corners")
        self.arg_parser.add_argument("--colorsampling", default="2",help="Color sampling")      
        self.arg_parser.add_argument("--numberofcolors", type=int, default=16, help="Number of colors to use on palette")
        self.arg_parser.add_argument("--mincolorratio", type=int, default=0, help="Color randomization ratio")
        self.arg_parser.add_argument("--colorquantcycles", type=int, default=3, help="Color quantization will be repeated this many times")           
        self.arg_parser.add_argument("--layering", default="0",help="Layering")
        self.arg_parser.add_argument("--strokewidth", type=float, default=1.0, help="SVG stroke-width")
        self.arg_parser.add_argument("--linefilter", type=inkex.Boolean, default=False, help="Noise reduction line filter")
        #self.arg_parser.add_argument("--scale", type=float, default=1.0, help="Coordinate scale factor")
        self.arg_parser.add_argument("--roundcoords", type=int, default=1, help="Decimal places for rounding")
        self.arg_parser.add_argument("--viewbox", type=inkex.Boolean, default=False, help="Enable or disable SVG viewBox")
        self.arg_parser.add_argument("--desc", type=inkex.Boolean, default=False, help="SVG descriptions")
        self.arg_parser.add_argument("--blurradius", type=int, default=0, help="Selective Gaussian blur preprocessing")
        self.arg_parser.add_argument("--blurdelta", type=float, default=20.0, help="RGBA delta treshold for selective Gaussian blur preprocessing")
  
    def effect(self):
    
        # internal overwrite for scale:
        self.options.scale = 1.0
    
        if (self.options.ids):
            for node in self.svg.selected.values():
                if node.tag == inkex.addNS('image', 'svg'):
                    self.path = self.checkImagePath(node)  # This also ensures the file exists
                    if self.path is None:  # check if image is embedded or linked
                        image_string = node.get('{http://www.w3.org/1999/xlink}href')
                        # find comma position
                        i = 0
                        while i < 40:
                            if image_string[i] == ',':
                                break
                            i = i + 1
                        image = Image.open(BytesIO(base64.b64decode(image_string[i + 1:len(image_string)])))
                    else:
                        image = Image.open(self.path)
                    
                    # Write the embedded or linked image to temporary directory
                    if os.name == "nt":
                         exportfile = "imagetracerjs.png"
                    else:
                         exportfile ="/tmp/imagetracerjs.png"
                    image.save(exportfile, "png")
           
                    nodeclipath = os.path.join("imagetracerjs-master", "nodecli", "nodecli.js")
                    
                    ## Build up imagetracerjs command according to your settings from extension GUI
                    command = "node " # "node.exe" or "node" on Windows or just "node" on Linux
                    if os.name=="nt": # your OS is Windows. We handle path separator as "\\" instead of unix-like "/"
                        command += str(nodeclipath).replace("\\", "\\\\")
                    else:
                        command += str(nodeclipath)
                    command += " " + exportfile
                    command += " ltres "             + str(self.options.ltres)
                    command += " qtres "             + str(self.options.qtres)
                    command += " pathomit "          + str(self.options.pathomit)
                    command += " rightangleenhance " + str(self.options.rightangleenhance).lower()
                    command += " colorsampling "     + str(self.options.colorsampling)
                    command += " numberofcolors "    + str(self.options.numberofcolors) 
                    command += " mincolorratio "     + str(self.options.mincolorratio)         
                    command += " numberofcolors "    + str(self.options.numberofcolors) 
                    command += " colorquantcycles "  + str(self.options.colorquantcycles)         
                    command += " layering "          + str(self.options.layering)          
                    command += " strokewidth "       + str(self.options.strokewidth)        
                    command += " linefilter "        + str(self.options.linefilter).lower()        
                    command += " scale "             + str(self.options.scale)   
                    command += " roundcoords "       + str(self.options.roundcoords)   
                    command += " viewbox "           + str(self.options.viewbox).lower()
                    command += " desc "              + str(self.options.desc).lower()
                    command += " blurradius "        + str(self.options.blurradius)   
                    command += " blurdelta "         + str(self.options.blurdelta)  
                     
                    #inkex.utils.debug(command)
                    
                    # Create the vector traced SVG file
                    with os.popen(command, "r") as tracerprocess:
                        result = tracerprocess.read()
                        #inkex.utils.debug(result)

                    # proceed if traced SVG file was successfully created
                    if os.path.exists(exportfile + ".svg"):
                        # Delete the temporary png file again because we do not need it anymore
                        if os.path.exists(exportfile):
                            os.remove(exportfile)
                        
                        # new parse the SVG file and insert it as new group into the current document tree
                        doc = etree.parse(exportfile + ".svg").getroot()
                        newGroup = self.document.getroot().add(inkex.Group())
                        newGroup.attrib['transform'] = "matrix(" + \
                            str(float(node.get('width')) / float(doc.get('width'))) + \
                            ", 0, 0 , " + \
                            str(float(node.get('height')) / float(doc.get('height'))) + \
                            "," + node.get('x') + \
                            "," + node.get('y') + ")"
                        newGroup.append(doc)

                        # Delet the temporary svg file
                        if os.path.exists(exportfile + ".svg"):
                            os.remove(exportfile + ".svg")
                    
                    #remove the old image or not                    
                    if self.options.keeporiginal is not True:
                        node.getparent().remove(node)                    
        else:
            inkex.utils.debug("No image found for tracing. Please select an image first.")        

Imagetracerjs().run()
