#!/usr/bin/env python3

"""
Extension for InkScape 1.0
Features
 - helps to find contours which are closed or not. Good for repairing contours, closing contours,...
 - works for paths which are packed into groups or groups of groups. #
 - can break contours apart like in "Path -> Break Apart"
 - implements Bentley-Ottmann algorithm from https://github.com/ideasman42/isect_segments-bentley_ottmann to scan for self-intersecting paths. You might get "assert(event.in_sweep == False) AssertionError". Don't know how to fix rgis
 - colorized paths respective to their type
 - can add dots to intersection points you'd like to fix
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 09.08.2020
Last patch: 11.08.2020
License: GNU GPL v3
"""

from math import *
import inkex
from inkex.paths import Path, CubicSuperPath
from inkex import Style, Color, Circle
from lxml import etree
import fablabchemnitz_poly_point_isect
import copy

def adjustStyle(self, node):
    if node.attrib.has_key('style'):
        style = node.get('style')
        if style:
            declarations = style.split(';')
            for i,decl in enumerate(declarations):
                parts = decl.split(':', 2)
                if len(parts) == 2:
                    (prop, val) = parts
                    prop = prop.strip().lower()
                    if prop == 'stroke-width':
                        declarations[i] = prop + ':' + str(self.svg.unittouu(str(self.options.strokewidth) +"px"))
                    if prop == 'fill':
                        declarations[i] = prop + ':none'
            node.set('style', ';'.join(declarations) + ';stroke:#000000;stroke-opacity:1.0')  

class ContourScanner(inkex.Effect):

    def getColorString(self, pickerColor):
        longcolor = int(pickerColor)
        if longcolor < 0:
            longcolor = longcolor & 0xFFFFFFFF
        return '#' + format(longcolor >> 8, '06X')

  
        
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--breakapart", type=inkex.Boolean, default=False, help="Break apart contours")
        self.arg_parser.add_argument("--removefillsetstroke", type=inkex.Boolean, default=False, help="Remove fill and define stroke")
        self.arg_parser.add_argument("--strokewidth", type=float, default=1.0, help="Stroke width (px)")
        self.arg_parser.add_argument("--highlight_opened", type=inkex.Boolean, default=True, help="Highlight opened contours")
        self.arg_parser.add_argument("--color_opened", type=Color, default='4012452351', help="Color opened contours")
        self.arg_parser.add_argument("--highlight_closed", type=inkex.Boolean, default=True, help="Highlight closed contours")
        self.arg_parser.add_argument("--color_closed", type=Color, default='2330080511', help="Color closed contours")
        self.arg_parser.add_argument("--highlight_selfintersecting", type=inkex.Boolean, default=True, help="Highlight self-intersecting contours")
        self.arg_parser.add_argument("--highlight_intersectionpoints", type=inkex.Boolean, default=True, help="Highlight self-intersecting points")
        self.arg_parser.add_argument("--color_selfintersecting", type=Color, default='1923076095', help="Color closed contours")
        self.arg_parser.add_argument("--color_intersectionpoints", type=Color, default='4239343359', help="Color closed contours")
        self.arg_parser.add_argument("--dotsize", type=int, default=10, help="Dot size (px) for self-intersecting points")
        self.arg_parser.add_argument("--remove_opened", type=inkex.Boolean, default=False, help="Remove opened contours")
        self.arg_parser.add_argument("--remove_closed", type=inkex.Boolean, default=False, help="Remove closed contours")
        self.arg_parser.add_argument("--remove_selfintersecting", type=inkex.Boolean, default=False, help="Remove self-intersecting contours")
        self.arg_parser.add_argument("--main_tabs")
  
    #split combined contours into single contours if enabled - this is exactly the same as "Path -> Break Apart"
    def breakContours(self, node):
        replacedNodes = []
        if node.tag == inkex.addNS('path','svg'):
            parent = node.getparent()
            idx = parent.index(node)
            idSuffix = 0    
            raw = Path(node.get("d")).to_arrays()
            subpaths, prev = [], 0
            for i in range(len(raw)): # Breaks compound paths into simple paths
                if raw[i][0] == 'M' and i != 0:
                    subpaths.append(raw[prev:i])
                    prev = i
            subpaths.append(raw[prev:])  
            for subpath in subpaths:
                replacedNode = copy.copy(node)
                oldId = replacedNode.get('id')
                
                replacedNode.set('d', CubicSuperPath(subpath))
                replacedNode.set('id', oldId + str(idSuffix).zfill(5))
                parent.insert(idx, replacedNode)
                idSuffix += 1
                replacedNodes.append(replacedNode)
            parent.remove(node)
        for child in node:
            self.breakContours(child)
        return replacedNodes
    
    def scanContours(self, node):
        if node.tag == inkex.addNS('path','svg'):
            if self.options.removefillsetstroke:
                adjustStyle(self, node)
      
            dot_group = node.getparent().add(inkex.Group())

            raw = (Path(node.get('d')).to_arrays())
            subpaths, prev = [], 0
            for i in range(len(raw)): # Breaks compound paths into simple paths
                if raw[i][0] == 'M' and i != 0:
                    subpaths.append(raw[prev:i])
                    prev = i
            subpaths.append(raw[prev:])
            
            for simpath in subpaths:
                if len(simpath) > 0:
                    closed = False
                    if simpath[-1][0] == 'Z':
                        closed = True

                    if not closed:
                        if self.options.highlight_opened:                        
                             style = {'stroke-linejoin': 'miter', 'stroke-width': str(self.svg.unittouu(str(self.options.strokewidth) +"px")), 
                                 'stroke-opacity': '1.0', 'fill-opacity': '1.0', 
                                 'stroke': self.options.color_opened, 'stroke-linecap': 'butt', 'fill': 'none'}
                             node.attrib['style'] = Style(style).to_str()
                        if self.options.remove_opened:
                            try:
                                node.getparent().remove(node)
                            except AttributeError:
                                pass #we ignore that parent can be None
                    if closed:
                        if self.options.highlight_closed:                        
                            style = {'stroke-linejoin': 'miter', 'stroke-width': str(self.svg.unittouu(str(self.options.strokewidth) +"px")), 
                                'stroke-opacity': '1.0', 'fill-opacity': '1.0', 
                                'stroke': self.options.color_closed, 'stroke-linecap': 'butt', 'fill': 'none'}
                            node.attrib['style'] = Style(style).to_str()
                        if self.options.remove_closed:
                            try:
                                node.getparent().remove(node)
                            except AttributeError:
                                pass #we ignore that parent can be None
 
            for simpath in subpaths:
                closed = False
                if simpath[-1][0] == 'Z':
                    closed = True
                    if simpath[-2][0] == 'L': simpath[-1][1] = simpath[0][1]
                    else: simpath.pop()
                nodes = []
                for i in range(len(simpath)):
                    if simpath[i][0] == 'V': # vertical and horizontal lines only have one point in args, but 2 are required
                        simpath[i][0]='L' #overwrite V with regular L command
                        add=simpath[i-1][1][0] #read the X value from previous segment
                        simpath[i][1].append(simpath[i][1][0]) #add the second (missing) argument by taking argument from previous segment
                        simpath[i][1][0]=add #replace with recent X after Y was appended
                    if simpath[i][0] == 'H': # vertical and horizontal lines only have one point in args, but 2 are required
                        simpath[i][0]='L' #overwrite H with regular L command
                        simpath[i][1].append(simpath[i-1][1][1]) #add the second (missing) argument by taking argument from previous segment				
                    nodes.append(simpath[i][1][-2:])
            
                #if one of the options is activated we also check for self-intersecting
                if self.options.highlight_selfintersecting or self.options.highlight_intersectionpoints:
                    try: 
                        if len(nodes) > 0: #try to find self-intersecting /overlapping polygons
                            isect = fablabchemnitz_poly_point_isect.isect_polygon(nodes) #TODO: FIND OUT HOW TO HANDLE OPEN CONTOURS TO OMIT VIRTUALLY CROSSING LINES (WHICH DO NOT INTERSECT)
                            if len(isect) > 0:
                                #make dot markings at the intersection points
                                if self.options.highlight_intersectionpoints:
                                    for xy in isect:
                                        #Add a dot label for this path element
                                        style = inkex.Style({'stroke': 'none', 'fill': self.getColorString(self.options.color_intersectionpoints)})
                                        circle = dot_group.add(Circle(cx=str(xy[0]), cy=str(xy[1]), r=str(self.svg.unittouu(str(self.options.dotsize/2) + "px"))))
                                        circle.style = style
                                
                                if self.options.highlight_selfintersecting:
                                    style = {'stroke-linejoin': 'miter', 'stroke-width': str(self.svg.unittouu(str(self.options.strokewidth) +"px")), 
                                        'stroke-opacity': '1.0', 'fill-opacity': '1.0', 
                                        'stroke': self.getColorString(self.options.color_selfintersecting), 'stroke-linecap': 'butt', 'fill': 'none'}
                                    node.attrib['style'] = Style(style).to_str()
                                if self.options.remove_selfintersecting:
                                    if node.getparent() is not None: #might be already been deleted by previously checked settings so check again
                                        node.getparent().remove(node)
                    except Exception as e: # we skip AssertionError
                        #inkex.utils.debug("Accuracy Error. Try to reduce the precision of the paths using the extension called Rounder to cutoff unrequired decimals.")        
                        print(str(e))        
        for child in node:
            self.scanContours(child) 
 
    def effect(self):
        if self.options.breakapart:    
            if len(self.svg.selected) == 0:
                 self.breakContours(self.document.getroot())
                 self.scanContours(self.document.getroot())  
            else:
                newContourSet = []
                for id, item in self.svg.selected.items():
                    newContourSet.append(self.breakContours(item))    
                    for newContours in newContourSet:
                        for newContour in newContours:                        
                            self.scanContours(newContour) 
        else:
            if len(self.svg.selected) == 0:
                 self.scanContours(self.document.getroot())
            else:
                for id, item in self.svg.selected.items():
                    self.scanContours(item)
      
ContourScanner().run()