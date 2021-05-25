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
Last patch: 19.05.2021
License: GNU GPL v3

ToDo:
- add option to replace last segment of closed paths by 'Z' or 'z' in case the first and last segment touch each other (coincident point)
"""

import sys
from math import *
from lxml import etree
import poly_point_isect
import copy
import inkex
from inkex.paths import Path, CubicSuperPath
from inkex import Style, Color, Circle

class ContourScanner(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--main_tabs")
        pars.add_argument("--breakapart", type=inkex.Boolean, default=False, help="Break apart selection into single contours")
        pars.add_argument("--apply_transformations", type=inkex.Boolean, default=False, help="Run 'Apply Transformations' extension before running to avoid IndexErrors in calculation.")
        pars.add_argument("--removefillsetstroke", type=inkex.Boolean, default=False, help="Remove fill and define stroke")
        pars.add_argument("--strokewidth", type=float, default=1.0, help="Stroke width (px)")
        pars.add_argument("--highlight_opened", type=inkex.Boolean, default=True, help="Highlight opened contours")
        pars.add_argument("--color_opened", type=Color, default='4012452351', help="Color opened contours")
        pars.add_argument("--highlight_closed", type=inkex.Boolean, default=True, help="Highlight closed contours")
        pars.add_argument("--color_closed", type=Color, default='2330080511', help="Color closed contours")
        pars.add_argument("--highlight_selfintersecting", type=inkex.Boolean, default=True, help="Highlight self-intersecting contours")
        pars.add_argument("--highlight_intersectionpoints", type=inkex.Boolean, default=True, help="Highlight self-intersecting points")
        pars.add_argument("--color_selfintersecting", type=Color, default='1923076095', help="Color closed contours")
        pars.add_argument("--color_intersectionpoints", type=Color, default='4239343359', help="Color closed contours")
        pars.add_argument("--addlines", type=inkex.Boolean, default=True, help="Add closing lines for self-crossing contours")
        pars.add_argument("--polypaths", type=inkex.Boolean, default=True, help="Add polypath outline for self-crossing contours")
        pars.add_argument("--dotsize", type=int, default=10, help="Dot size (px) for self-intersecting points")
        pars.add_argument("--remove_opened", type=inkex.Boolean, default=False, help="Remove opened contours")
        pars.add_argument("--remove_closed", type=inkex.Boolean, default=False, help="Remove closed contours")
        pars.add_argument("--remove_selfintersecting", type=inkex.Boolean, default=False, help="Remove self-intersecting contours")
        pars.add_argument("--show_debug", type=inkex.Boolean, default=False, help="Show debug info")

    #function to refine the style of the lines  
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
        else:
            node.set('style', 'stroke:#000000;stroke-opacity:1.0')

  
    #get polyline from path
    def getPolyline(self, node):
        if node.tag == inkex.addNS('path','svg'):
            polypath = []
            i = 0
            for x, y in node.path.end_points:
                if i == 0:
                    polypath.append(['M', [x,y]])
                else:
                    polypath.append(['L', [x,y]])
                    if i == 1 and polypath[len(polypath)-2][1] == polypath[len(polypath)-1][1]:
                        polypath.pop(len(polypath)-1) #special handling for the seconds point after M command
                    elif polypath[len(polypath)-2] == polypath[len(polypath)-1]: #get the previous point
                        polypath.pop(len(polypath)-1)
                i += 1
            return Path(polypath)
   
   
    #split combined contours into single contours if enabled - this is exactly the same as "Path -> Break Apart"
    replacedNodes = [] 
    def breakContours(self, node): #this does the same as "CTRL + SHIFT + K"
        if node.tag == inkex.addNS('path','svg'):
            parent = node.getparent()
            idx = parent.index(node)
            idSuffix = 0    
            raw = Path(node.get("d")).to_arrays()
            subPaths, prev = [], 0
            for i in range(len(raw)): # Breaks compound paths into simple paths
                if raw[i][0] == 'M' and i != 0:
                    subPaths.append(raw[prev:i])
                    prev = i
            subPaths.append(raw[prev:])  
            for subpath in subPaths:
                replacedNode = copy.copy(node)
                oldId = replacedNode.get('id')
                
                replacedNode.set('d', CubicSuperPath(subpath))
                replacedNode.set('id', oldId + str(idSuffix).zfill(5))
                parent.insert(idx, replacedNode)
                idSuffix += 1
                self.replacedNodes.append(replacedNode)
            node.delete()
        for child in node:
            self.breakContours(child)
    
    def scanContours(self, node):
        if node.tag == inkex.addNS('path','svg'):
            if self.options.removefillsetstroke:
                self.adjustStyle(node)
      
            intersectionGroup = node.getparent().add(inkex.Group())

            raw = (Path(node.get('d')).to_arrays())
            subPaths, prev = [], 0
            for i in range(len(raw)): # Breaks compound paths into simple paths
                if raw[i][0] == 'M' and i != 0:
                    subPaths.append(raw[prev:i])
                    prev = i
            subPaths.append(raw[prev:])
            
            for simpath in subPaths:

                closed = False
                if simpath[-1][0] == 'Z' or \
                    (simpath[-1][0] == 'L' and simpath[0][1] == simpath[-1][1]) or \
                    (simpath[-1][0] == 'C' and simpath[0][1] == [simpath[-1][1][-2], simpath[-1][1][-1]]) :  #if first is last point the path is also closed. The "Z" command is not required
                    closed = True   
                    
                    if simpath[-2][0] == 'L': simpath[-1][1] = simpath[0][1]
                    else: simpath.pop()
                points = []
                for i in range(len(simpath)):
                    if simpath[i][0] == 'V': # vertical and horizontal lines only have one point in args, but 2 are required
                        simpath[i][0]='L' #overwrite V with regular L command
                        add=simpath[i-1][1][0] #read the X value from previous segment
                        simpath[i][1].append(simpath[i][1][0]) #add the second (missing) argument by taking argument from previous segment
                        simpath[i][1][0]=add #replace with recent X after Y was appended
                    if simpath[i][0] == 'H': # vertical and horizontal lines only have one point in args, but 2 are required
                        simpath[i][0]='L' #overwrite H with regular L command
                        simpath[i][1].append(simpath[i-1][1][1]) #add the second (missing) argument by taking argument from previous segment                
                    points.append(simpath[i][1][-2:])
                if points[0] == points[-1]: #if first is last point the path is also closed. The "Z" command is not required
                    closed = True

                if closed == False:
                    if self.options.highlight_opened:                        
                         style = {'stroke-linejoin': 'miter', 'stroke-width': str(self.svg.unittouu(str(self.options.strokewidth) +"px")), 
                             'stroke-opacity': '1.0', 'fill-opacity': '1.0', 
                             'stroke': self.options.color_opened, 'stroke-linecap': 'butt', 'fill': 'none'}
                         node.attrib['style'] = Style(style).to_str()
                    if self.options.remove_opened:
                        try:
                            node.delete()
                        except AttributeError:
                            pass #we ignore that parent can be None
                if closed == True:
                    if self.options.highlight_closed:                        
                        style = {'stroke-linejoin': 'miter', 'stroke-width': str(self.svg.unittouu(str(self.options.strokewidth) +"px")), 
                            'stroke-opacity': '1.0', 'fill-opacity': '1.0', 
                            'stroke': self.options.color_closed, 'stroke-linecap': 'butt', 'fill': 'none'}
                        node.attrib['style'] = Style(style).to_str()
                    if self.options.remove_closed:
                        try:
                            node.delete()
                        except AttributeError:
                            pass #we ignore that parent can be None
 
                #if one of the options is activated we also check for self-intersecting
                if self.options.highlight_selfintersecting or self.options.highlight_intersectionpoints:    
                    
                    #Style definitions        
                    closingLineStyle = Style({'stroke-linejoin': 'miter', 'stroke-width': str(self.svg.unittouu(str(self.options.strokewidth) +"px")), 
                        'stroke-opacity': '1.0', 'fill-opacity': '1.0', 
                        'stroke': self.options.color_intersectionpoints, 'stroke-linecap': 'butt', 'fill': 'none'}).to_str()
                    
                    intersectionPointStyle = Style({'stroke': 'none', 'fill': self.options.color_intersectionpoints}).to_str()
                    
                    intersectionStyle = Style({'stroke-linejoin': 'miter', 'stroke-width': str(self.svg.unittouu(str(self.options.strokewidth) +"px")), 
                        'stroke-opacity': '1.0', 'fill-opacity': '1.0', 
                        'stroke': self.options.color_selfintersecting, 'stroke-linecap': 'butt', 'fill': 'none'}).to_str()
                    
                    try: 
                        if len(points) > 2: #try to find self-intersecting /overlapping polygons. We need at least 3 points to detect for intersections (only possible if first points matched last point)
                            isect = poly_point_isect.isect_polygon(points, validate=True)         
                            if len(isect) > 0:
                                if closed == False and self.options.addlines == True: #if contour is open and we found intersection points those points might be not relevant
                                    closingLine = intersectionGroup.add(inkex.PathElement())
                                    closingLine.set('id', self.svg.get_unique_id('closingline-'))
                                    closingLine.path = [
                                        ['M', [points[0][0],points[0][1]]],
                                        ['L', [points[-1][0],points[-1][1]]],
                                        ['Z', []]
                                    ]
                                    closingLine.attrib['style'] = closingLineStyle
                                    
                                #draw polylines if option is enabled
                                if self.options.polypaths == True:
                                    polyNode = intersectionGroup.add(inkex.PathElement())
                                    polyNode.set('id', self.svg.get_unique_id('polypath-'))
                                    polyNode.set('d', str(self.getPolyline(node)))
                                    polyNode.attrib['style'] = closingLineStyle
                                    
                                #make dot markings at the intersection points
                                if self.options.highlight_intersectionpoints:
                                    for xy in isect:
                                        #Add a dot label for this path element
                                        intersectionPoint = intersectionGroup.add(Circle(cx=str(xy[0]), cy=str(xy[1]), r=str(self.svg.unittouu(str(self.options.dotsize/2) + "px"))))
                                        intersectionPoint.set('id', self.svg.get_unique_id('intersectionpoint-'))
                                        intersectionPoint.style = intersectionPointStyle
                         
                                if self.options.highlight_selfintersecting:
                                    node.attrib['style'] = intersectionStyle
                                if self.options.remove_selfintersecting:
                                    if node.getparent() is not None: #might be already been deleted by previously checked settings so check again
                                        node.delete()
                                        
                        #draw intersections segment lines - useless at the moment. We could use this information to cut the original polyline to get a new curve path which included the intersection points
                        #isectSegs = poly_point_isect.isect_polygon_include_segments(points)
                        #for seg in isectSegs:
                        #    isectSegsPath = []    
                        #    isecX = seg[0][0] #the intersection point - X
                        #    isecY = seg[0][1] #the intersection point - Y
                        #    isecSeg1X = seg[1][0][0][0] #the first intersection point segment - X
                        #    isecSeg1Y = seg[1][0][0][1] #the first intersection point segment - Y
                        #    isecSeg2X = seg[1][1][0][0] #the second intersection point segment - X
                        #    isecSeg2Y = seg[1][1][0][1] #the second intersection point segment - Y
                        #    isectSegsPath.append(['L', [isecSeg2X, isecSeg2Y]])
                        #    isectSegsPath.append(['L', [isecX, isecY]])
                        #    isectSegsPath.append(['L', [isecSeg1X, isecSeg1Y]])
                        #    #fix the really first point. Has to be an 'M' command instead of 'L'
                        #    isectSegsPath[0][0] = 'M'
                        #    polySegsNode = intersectionGroup.add(inkex.PathElement())
                        #    polySegsNode.set('id', self.svg.get_unique_id('intersectsegments-'))
                        #    polySegsNode.set('d', str(Path(isectSegsPath)))
                        #    polySegsNode.attrib['style'] = closingLineStyle

                    except AssertionError as e: # we skip AssertionError
                        if self.options.show_debug is True:
                            inkex.utils.debug("AssertionError at " + node.get('id'))
                        continue
                    except IndexError as i: # we skip IndexError
                        if self.options.show_debug is True:
                            inkex.utils.debug("IndexError at " + node.get('id'))
                        continue 
                #if the intersectionGroup was created but nothing attached we delete it again to prevent messing the SVG XML tree
                if len(intersectionGroup.getchildren()) == 0:
                    intersectionGroupParent = intersectionGroup.getparent()
                    if intersectionGroupParent is not None:
                        intersectionGroup.delete()
                #put the node into the intersectionGroup to bundle the path with it's error markers. If removal is selected we need to avoid intersectionGroup.insert(), because it will break the removal
                elif self.options.remove_selfintersecting == False:
                    intersectionGroup.insert(0, node)
        children = node.getchildren()
        if children is not None: 
            for child in children:
                self.scanContours(child) 
 
    def effect(self):
    
        applyTransformAvailable = False
        # at first we apply external extension
        try:
            sys.path.append("../applytransform") # add parent directory to path to allow importing applytransform (vpype extension is encapsulated in sub directory)
            import applytransform
            applyTransformAvailable = True
        except Exception as e:
            #inkex.utils.debug(e)
            inkex.utils.debug("Calling 'Apply Transformations' extension failed. Maybe the extension is not installed. You can download it from official InkScape Gallery. Skipping this step")
    
        '''
        we need to apply transfoms to the complete document even if there are only some single paths selected. 
        If we apply it to selected nodes only the parent groups still might contain transforms. 
        This messes with the coordinates and creates hardly controllable behaviour
        '''
        if self.options.apply_transformations is True and applyTransformAvailable is True:
            applytransform.ApplyTransform().recursiveFuseTransform(self.document.getroot())
    
        if self.options.breakapart is True:    
            if len(self.svg.selected) == 0:
                 self.breakContours(self.document.getroot())
                 self.scanContours(self.document.getroot())  
            else:
                newContourSet = []
                for element in self.svg.selected.values():
                    self.breakContours(element)
                for newContours in self.replacedNodes:
                    self.scanContours(newContours) 
        else:
            if len(self.svg.selected) == 0:
                 self.scanContours(self.document.getroot())
            else:
                for element in self.svg.selected.values():
                    self.scanContours(element)
      
if __name__ == '__main__':
    ContourScanner().run()