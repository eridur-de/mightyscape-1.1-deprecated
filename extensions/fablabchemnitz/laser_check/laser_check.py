#!/usr/bin/env python3

import inkex
from inkex.bezier import csplength, csparea
from lxml import etree
import re
import math

class LaserCheck(inkex.EffectExtension):
    
    '''
    check for old styles which should be upgraded
    '''
    
    def add_arguments(self, pars):
        pars.add_argument('--tab')
        pars.add_argument('--checks', default="check_all")
        pars.add_argument('--bbox', type=inkex.Boolean, default=False)
        pars.add_argument('--bbox_offset', type=float, default=5.000)
        pars.add_argument('--groups_and_layers', type=inkex.Boolean, default=False)
        pars.add_argument('--clones', type=inkex.Boolean, default=False)
        pars.add_argument('--clippaths', type=inkex.Boolean, default=False)
        pars.add_argument('--images', type=inkex.Boolean, default=False)
        pars.add_argument('--texts', type=inkex.Boolean, default=False)
        pars.add_argument('--lowlevelstrokes', type=inkex.Boolean, default=False)
        pars.add_argument('--stroke_colors', type=inkex.Boolean, default=False)
        pars.add_argument('--stroke_widths', type=inkex.Boolean, default=False)
        pars.add_argument('--stroke_opacities', type=inkex.Boolean, default=False)
        pars.add_argument('--cosmestic_dashes', type=inkex.Boolean, default=False)
        pars.add_argument('--invisible_shapes', type=inkex.Boolean, default=False)
        pars.add_argument('--pointy_paths', type=inkex.Boolean, default=False)
        pars.add_argument('--transformations', type=inkex.Boolean, default=False)
        pars.add_argument('--short_paths', type=inkex.Boolean, default=False)
        pars.add_argument('--short_paths_min', type=float, default=1.000)
        pars.add_argument('--non_path_shapes', type=inkex.Boolean, default=False)
        
    def effect(self):
        
        so = self.options
        
        def parseChildren(element):
            if element not in selected:
                selected.append(element)
            children = element.getchildren()
            if children is not None:
                for child in children:
                    if child not in selected:
                        selected.append(child)
                    parseChildren(child) #go deeper and deeper       
        
        #check if we have selected elements or if we should parse the whole document instead
        selected = [] #total list of elements to parse
        if len(self.svg.selected) == 0:
            for element in self.document.getroot().iter(tag=etree.Element):
                if element != self.document.getroot():

                    selected.append(element)
        else:
            for element in self.svg.selected.values():
                parseChildren(element)     
        namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
        doc_units = namedView.get(inkex.addNS('document-units', 'inkscape'))            
        pagecolor = namedView.get('pagecolor')
        inkex.utils.debug("---------- Default checks")
        inkex.utils.debug("Document units: {}".format(doc_units))
        nonShapes = []
        shapes = []
        for element in selected:       
            if not isinstance(element, inkex.ShapeElement):
                nonShapes.append(element)
            else:
                shapes.append(element)  
        inkex.utils.debug("{} shape elements in total".format(len(shapes)))
        inkex.utils.debug("{} non-shape elements in total".format(len(nonShapes)))
        for nonShape in nonShapes:
            inkex.utils.debug("non-shape id={}".format(nonShape.get('id')))
        
        if so.checks == "check_all" or so.groups_and_layers is True:
            inkex.utils.debug("\n---------- Groups and layers") 
            groups = []
            layers = []
            for element in selected:
                if element.tag == inkex.addNS('g','svg'):
                    if element.get('inkscape:groupmode') == 'layer':
                        layers.append(element)
                    else:
                        groups.append(element)
            inkex.utils.debug("{} groups in total".format(len(groups)))
            inkex.utils.debug("{} layers in total".format(len(layers)))
    
            #check for empty groups
            for group in groups:
                if len(group) == 0:
                    inkex.utils.debug("id={} is empty group".format(group.get('id')))
    
            #check for empty layers
            for layer in layers:
                if len(layer) == 0:
                    inkex.utils.debug("id={} is empty layer".format(layer.get('id')))


        if so.checks == "check_all" or so.clones is True:
            inkex.utils.debug("\n---------- Clones (svg:use) - maybe unlink") 
            uses = []
            for element in selected:
                if element.tag == inkex.addNS('use','svg'):
                    uses.append(element)
            inkex.utils.debug("{} svg:use clones in total".format(len(uses)))
            for use in uses:
                inkex.utils.debug("id={}".format(use.get('id')))
   
   
        if so.checks == "check_all" or so.clippaths is True:
            inkex.utils.debug("\n---------- Clippings (svg:clipPath) - please replace with real cut paths") 
            clipPaths = []
            for element in selected:
                if element.tag == inkex.addNS('clipPath','svg'):
                    clipPaths.append(element)
            inkex.utils.debug("{} svg:clipPath in total".format(len(clipPaths)))
            for clipPath in clipPaths:
                inkex.utils.debug("id={}".format(clipPath.get('id')))
   
   
        if so.checks == "check_all" or so.images is True:
            inkex.utils.debug("\n---------- Images (svg:image) - maybe trace to svg") 
            images = []
            for element in selected:
                if element.tag == inkex.addNS('image','svg'):
                    images.append(element)
            inkex.utils.debug("{} svg:image in total".format(len(images)))
            for image in images:
                inkex.utils.debug("image id={}".format(image.get('id')))
    
    
        if so.checks == "check_all" or so.lowlevelstrokes is True:
            inkex.utils.debug("\n---------- Low level strokes (svg:line/polyline/polygon) - maybe convert to path") 
            lowlevels = []
            for element in selected:
                if element.tag in (inkex.addNS('line','svg'), inkex.addNS('polyline','svg'), inkex.addNS('polygon','svg')):
                    lowlevels.append(element)
            inkex.utils.debug("{} low level strokes in total".format(len(lowlevels)))
            for lowlevel in lowlevels:
                inkex.utils.debug("id={}".format(lowlevel.get('id')))
    
    
        if so.checks == "check_all" or so.texts is True:
            inkex.utils.debug("\n---------- Texts (should be converted to paths)") 
            texts = []
            for element in selected:
                if element.tag == inkex.addNS('text','svg'):
                    texts.append(element)
            inkex.utils.debug("{} svg:text in total".format(len(texts)))
            for text in texts:
                inkex.utils.debug("id={}".format(text.get('id')))
             

        if so.checks == "check_all" or so.stroke_colors is True:
            inkex.utils.debug("\n---------- Stroke colors")
            strokeColors = []
            for element in shapes:          
                style = element.get('style')
                if style is not None:
                    stroke = re.search('(;|^)stroke:(.*?)(;|$)', style)
                    if stroke is not None:
                        strokeColor = stroke[0].split("stroke:")[1].split(";")[0]
                        if strokeColor not in strokeColors:
                            strokeColors.append(strokeColor)
            inkex.utils.debug("{} different stroke colors in total".format(len(strokeColors)))
            for strokeColor in strokeColors:
                inkex.utils.debug("stroke color {}".format(strokeColor))
      
      
        if so.checks == "check_all" or so.bbox is True:  
            inkex.utils.debug("\n---------- Borders around all elements - minimum offset {} mm from each side".format(so.bbox_offset))
            bbox = inkex.BoundingBox()
            for element in self.document.getroot().iter(tag=etree.Element):
                if element != self.document.getroot() and isinstance(element, inkex.ShapeElement) and element.tag != inkex.addNS('use','svg') and element.get('inkscape:groupmode') != 'layer': #bbox fails for svg:use elements and layers
                    transform = inkex.Transform()
                    parent = element.getparent()
                    if parent is not None and isinstance(parent, inkex.ShapeElement):
                        transform = parent.composed_transform()
                    try:
                        bbox += element.bounding_box(transform)
                    except Exception:
                        transform = element.composed_transform()
                        x1, y1 = transform.apply_to_point([0, 0])
                        x2, y2 = transform.apply_to_point([1, 1])
                        bbox += inkex.BoundingBox((x1, x2), (y1, y2))
     
            if abs(bbox.width) == math.inf or abs(bbox.height) == math.inf:
                inkex.utils.debug("bounding box could not be calculated")
            #else:
            #    inkex.utils.debug("bounding box is {}".format(bbox))
            page_width = self.svg.unittouu(self.document.getroot().attrib['width'])
            width_height = self.svg.unittouu(self.document.getroot().attrib['height'])
            fmm = self.svg.unittouu(str(so.bbox_offset) + "mm")
            if bbox.left > fmm:
                inkex.utils.debug("left border... ok")
            else:
                inkex.utils.debug("left border... fail")
                 
            if bbox.top > fmm:
                inkex.utils.debug("top border... ok")
            else:
                inkex.utils.debug("top border... fail")
                
            if bbox.right + fmm <= page_width:
                inkex.utils.debug("right border... ok")
            else:
                inkex.utils.debug("right border... fail")
                
            if bbox.bottom + fmm <= width_height:
                inkex.utils.debug("bottom border... ok")
            else:
                inkex.utils.debug("bottom border... fail")
             
             
        if so.checks == "check_all" or so.stroke_widths is True:              
            inkex.utils.debug("\n---------- Stroke widths")
            strokeWidths = []
            for element in shapes:          
                style = element.get('style')
                if style is not None:
                    stroke_width = re.search('stroke-width:(.*?)(;|$)', style)
                    if stroke_width is not None:
                        strokeWidth = self.svg.unittouu(stroke_width[0].split("stroke-width:")[1].split(";")[0])
                        if strokeWidth not in strokeWidths:
                            strokeWidths.append(strokeWidth)
            inkex.utils.debug("{} different stroke widths in total".format(len(strokeWidths)))
            for strokeWidth in strokeWidths:
                inkex.utils.debug("stroke width {}".format(strokeWidth))
          
          
        if so.checks == "check_all" or so.cosmestic_dashes is True:   
            inkex.utils.debug("\n---------- Cosmetic dashes - should be converted to paths")
            strokeDasharrays = []
            for element in shapes:          
                style = element.get('style')
                if style is not None:
                    stroke_dasharray = re.search('stroke-dasharray:(.*?)(;|$)', style)
                    if stroke_dasharray is not None:
                        strokeDasharray = stroke_dasharray[0].split("stroke-dasharray:")[1].split(";")[0]
                        if strokeDasharray not in strokeDasharrays:
                            strokeDasharrays.append(strokeDasharray)
            inkex.utils.debug("{} different stroke dash arrays in total".format(len(strokeDasharrays)))
            for strokeDasharray in strokeDasharrays:
                inkex.utils.debug("stroke dash array {}".format(strokeDasharray))
     
  
        if so.checks == "check_all" or so.invisible_shapes is True:     
            inkex.utils.debug("\n---------- Invisible shapes")
            invisibles = []
            for element in shapes:
                if element.tag not in (inkex.addNS('tspan','svg')):      
                    style = element.get('style')
                    if style is not None:              
                        stroke = re.search('stroke:(.*?)(;|$)', style) #filter white on white (we guess the background color of the document is white too but we do not check)
                        if stroke is None:
                            strokeVis = 0
                        elif stroke[0].split("stroke:")[1].split(";")[0] == 'none':
                            strokeVis = 0
                        elif stroke[0].split("stroke:")[1].split(";")[0] in ('#ffffff', 'white', 'rgb(255,255,255)'):
                            strokeVis = 0
                        else:
                            strokeVis = 1
                        
                        stroke_width = re.search('stroke-width:(.*?)(;|$)', style)
                        if stroke_width is None:
                            widthVis = 0
                        elif self.svg.unittouu(stroke_width[0].split("stroke-width:")[1].split(";")[0]) < 0.005: #really thin (0,005pc = 0,080px)
                            widthVis = 0
                        else:
                            widthVis = 1
      
                        stroke_opacity = re.search('stroke-opacity:(.*?)(;|$)', style)
                        if stroke_opacity is None:
                            strokeOpacityVis = 0
                        elif float(stroke_opacity[0].split("stroke-opacity:")[1].split(";")[0]) < 0.05: #nearly invisible (<5% opacity)
                            strokeOpacityVis = 0
                        else:
                            strokeOpacityVis = 1
      
                        if pagecolor == '#ffffff':
                            invisColors = [pagecolor, 'white', 'rgb(255,255,255)']
                        else:
                            invisColors = [pagecolor] #we could add some parser to convert pagecolor to rgb/hsl/cmyk
                        fill = re.search('fill:(.*?)(;|$)', style)
                        if fill is None:
                            fillVis = 0
                        elif fill[0].split("fill:")[1].split(";")[0] == 'none':
                            fillVis = 0
                        elif fill[0].split("fill:")[1].split(";")[0] in invisColors:
                            fillVis = 0
                        else:
                            fillVis = 1
                  
                        fill_opacity = re.search('fill-opacity:(.*?)(;|$)', style)
                        if fill_opacity is None:
                            fillOpacityVis = 0
                        elif float(fill_opacity[0].split("fill-opacity:")[1].split(";")[0]) < 0.05: #nearly invisible (<5% opacity)
                            fillOpacityVis = 0
                        else:
                            fillOpacityVis = 1  
                                  
                        #inkex.utils.debug("strokeVis={}, widthVis={}, strokeOpacityVis={}, fillVis={}, fillOpacityVis={}".format(strokeVis, widthVis, strokeOpacityVis, fillVis, fillOpacityVis))
                        if (strokeVis == 0 or widthVis == 0 or strokeOpacityVis == 0) and (fillVis == 0 or fillOpacityVis == 0):
                            if element not in invisibles:
                                invisibles.append(element)
            inkex.utils.debug("{} invisible shapes in total".format(len(invisibles)))
            for invisible in invisibles:
                inkex.utils.debug("id={}".format(invisible.get('id')))
          
                
        if so.checks == "check_all" or so.stroke_opacities is True:
            inkex.utils.debug("\n---------- Objects with stroke transparencies < 1.0 - should be set to 1.0")
            transparencies = []
            for element in shapes:
                  style = element.get('style')
                  if style is not None:              
                      stroke_opacity = re.search('stroke-opacity:(.*?)(;|$)', style)
                      if stroke_opacity is not None:
                          if float(stroke_opacity[0].split("stroke-opacity:")[1].split(";")[0]) < 1.0:
                              if element not in transparencies:
                                  transparencies.append(element)
            inkex.utils.debug("{} objects with stroke transparencies < 1.0 in total".format(len(transparencies)))
            for transparency in transparencies:
                inkex.utils.debug("id={}".format(transparency.get('id')))  
      
              
        if so.checks == "check_all" or so.pointy_paths is True:          
            inkex.utils.debug("\n---------- Pointy paths - should be deleted")
            pointyPaths = []
            for element in shapes:
                if isinstance(element, inkex.PathElement):
                    p = element.path
                    commandsCoords = p.to_arrays()
                    if len(commandsCoords) == 1 or \
                        (len(commandsCoords) == 2 and commandsCoords[0][1] == commandsCoords[1][1]) or \
                        (len(commandsCoords) == 2 and commandsCoords[-1][0] == 'Z') or \
                        (len(commandsCoords) == 3 and commandsCoords[0][1] == commandsCoords[1][1] and commandsCoords[2][1] == 'Z'):
                        pointyPaths.append(element)
            inkex.utils.debug("{} pointy paths in total".format(len(pointyPaths)))
            for pointyPath in pointyPaths:
                inkex.utils.debug("id={}".format(pointyPath.get('id')))    
   
   
        if so.checks == "check_all" or so.transformations is True:
            inkex.utils.debug("\n---------- Transformations - should be applied to absolute")
            transformations = []
            for element in shapes:
                if element.get('transform') is not None:
                    transformations.append(element)
            inkex.utils.debug("{} transformation in total".format(len(transformations)))
            for transformation in transformations:
                inkex.utils.debug("transformation in id={}".format(transformation.get('id')))    
          
          
        if so.checks == "check_all" or so.short_paths is True:  
            inkex.utils.debug("\n---------- Short paths (< {} mm)".format(so.short_paths_min))
            shortPaths = []
            totalLength = 0
            totalDropLength = 0
            for element in shapes:
                if isinstance(element, inkex.PathElement):
                    slengths, stotal = csplength(element.path.transform(element.composed_transform()).to_superpath())
                    totalLength += stotal
                    if stotal < self.svg.unittouu(str(so.short_paths_min) + "mm"):
                        shortPaths.append(element)
                        totalDropLength += stotal
            inkex.utils.debug("{} short paths in total".format(len(shortPaths)))
            if totalLength > 0:
                inkex.utils.debug("{:0.2f}% of total ({:0.2f} mm /{:0.2f} mm)".format(totalDropLength / totalLength, totalDropLength, totalLength))
            for shortPath in shortPaths:
                inkex.utils.debug("id={}".format(shortPath.get('id')))    
          
                   
        if so.checks == "check_all" or so.non_path_shapes is True:          
            inkex.utils.debug("\n---------- Non-path shapes - should be converted to paths")
            nonPathShapes = []
            for element in shapes:
                if not isinstance(element, inkex.PathElement) and not isinstance(element, inkex.Group):
                    nonPathShapes.append(element)
            inkex.utils.debug("{} non-path shapes in total".format(len(nonPathShapes)))
            for nonPathShape in nonPathShapes:
                inkex.utils.debug("id={}".format(nonPathShape.get('id')))         
         
                             
if __name__ == '__main__':
    LaserCheck().run()