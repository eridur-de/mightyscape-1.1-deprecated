#!/usr/bin/env python3

import inkex
from inkex.bezier import csplength, csparea
from lxml import etree
import re
import math
import datetime

class LaserCheck(inkex.EffectExtension):
    
    '''
    ToDos:
     - Handlungsempfehlungen einbauen
        - verweisen auf diverse plugins, die man nutzen kann:
            - migrate ungrouper
            - pointy paths
            - cleaner
            - styles to layers
            - apply transforms
            - epilog bbox adjust
        - wege zum Pfade fixen:
            - cut slower ( > muss aber auch leistung reduzieren - inb welchem umfang?)
            - sort
            - chaining with touching neighbours
            - remove path
            - remove modes/simplify
    - find duplicate lines
    - visualize results as a nice SVG rendered check list page with 
        - red/green/grey icons (failed, done, skipped) and calculate some scores
        - preview image
        - statistics
        - export as PDF
    - run as script to generate quick results for users
    - check for old styles which should be upgraded
    - self-intersecting paths
    - number of parts (isles) to weed in total
    - number of parts which are smaller than vector grid
    - add some inkex.Desc to all elements which were checked and which have some issue. use special syntax to remove old stuff each time the check is applied again
    - this code is horrible ugly stuff
    - output time/cost estimations per stroke color
    - add check for stroke colors -> make some useful predefinitions like (for default modes)
        - black = general cutting
        - blue = cutting inside
        - green = cutting outside
        - pink = vector engraving
    '''
    
    def add_arguments(self, pars):
        pars.add_argument('--tab')
        
        pars.add_argument('--machine_size', default="812x508")
        pars.add_argument('--max_cutting_speed', type=float, default=500)
        pars.add_argument('--max_travel_speed', type=float, default=150)
        pars.add_argument('--cut_travel_factor', type=float, default=0.60)
        pars.add_argument('--price_per_minute_gross', type=float, default=2.0)
        pars.add_argument('--vector_grid_xy', type=float, default=12.0) #TODO
        
        pars.add_argument('--show_issues_only', type=inkex.Boolean, default=False)  
        pars.add_argument('--checks', default="check_all")
        pars.add_argument('--bbox', type=inkex.Boolean, default=False)
        pars.add_argument('--bbox_offset', type=float, default=5.000)
        pars.add_argument('--cutting_estimation', type=inkex.Boolean, default=False)
        pars.add_argument('--elements_outside_canvas', type=inkex.Boolean, default=False)
        pars.add_argument('--groups_and_layers', type=inkex.Boolean, default=False)
        pars.add_argument('--clones', type=inkex.Boolean, default=False)
        pars.add_argument('--clippaths', type=inkex.Boolean, default=False)
        pars.add_argument('--images', type=inkex.Boolean, default=False)
        pars.add_argument('--texts', type=inkex.Boolean, default=False)
        pars.add_argument('--lowlevelstrokes', type=inkex.Boolean, default=False)
        pars.add_argument('--stroke_colors', type=inkex.Boolean, default=False)
        pars.add_argument('--stroke_colors_max', type=int, default=3)
        pars.add_argument('--stroke_widths', type=inkex.Boolean, default=False)
        pars.add_argument('--stroke_widths_max', type=int, default=1)
        pars.add_argument('--stroke_opacities', type=inkex.Boolean, default=False)
        pars.add_argument('--cosmestic_dashes', type=inkex.Boolean, default=False)
        pars.add_argument('--invisible_shapes', type=inkex.Boolean, default=False)
        pars.add_argument('--pointy_paths', type=inkex.Boolean, default=False)
        pars.add_argument('--transformations', type=inkex.Boolean, default=False)
        pars.add_argument('--short_paths', type=inkex.Boolean, default=False)
        pars.add_argument('--short_paths_min', type=float, default=1.000)
        pars.add_argument('--non_path_shapes', type=inkex.Boolean, default=False)
        pars.add_argument('--nodes_per_path', type=inkex.Boolean, default=False)
        pars.add_argument('--nodes_per_path_max', type=int, default=2)
        pars.add_argument('--nodes_per_path_interval', type=float, default=10.000)
        
    def effect(self):
        
        so = self.options
        machineWidth = self.svg.unittouu(so.machine_size.split('x')[0] + "mm")
        machineHeight = self.svg.unittouu(so.machine_size.split('x')[1] + "mm")
        selected = [] #total list of elements to parse

        
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
        if len(self.svg.selected) == 0:
            for element in self.document.getroot().iter(tag=etree.Element):
                if element != self.document.getroot():

                    selected.append(element)
        else:
            for element in self.svg.selected.values():
                parseChildren(element)
                
        namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
        doc_units = namedView.get(inkex.addNS('document-units', 'inkscape'))        
        user_units = namedView.get(inkex.addNS('units'))  
        pagecolor = namedView.get('pagecolor')
        inkex.utils.debug("---------- Default checks")
        inkex.utils.debug("Document units: {}".format(doc_units))
        inkex.utils.debug("User units: {}".format(user_units))
        
        '''
        The SVG format is highly complex and offers a lot of possibilities. Most things of SVG we do not
        need for a laser cutter. Usually we need svg:path and maybe svg:image; we can drop a lot of stuff
        like svg:defs, svg:desc, gradients, etc.
        '''
        nonShapes = []
        shapes = []
        for element in selected:       
            if not isinstance(element, inkex.ShapeElement):
                nonShapes.append(element)
            else:
                shapes.append(element)
        if so.show_issues_only is False:        
            inkex.utils.debug("{} shape elements in total".format(len(shapes)))
            inkex.utils.debug("{} non-shape elements in total".format(len(nonShapes)))
        for nonShape in nonShapes:
            inkex.utils.debug("non-shape id={}".format(nonShape.get('id')))
        
        
        '''
        Nearly each laser job needs a bit of border to place the material inside the laser. Often
        we have to fixate on vector grid, pin grid or task plate. Thus we need tapes or pins. So we 
        leave some borders off the actual part geometries.
        '''
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
                        if isinstance (element, inkex.Rectangle) or \
                           isinstance (element, inkex.Circle) or \
                           isinstance (element, inkex.Ellipse):
                            bbox += element.bounding_box() * scale_factor   
                        elif isinstance (element, inkex.TextElement) or \
                             isinstance (element, inkex.Tspan):
                            continue
                        else:  
                            bbox += element.bounding_box(transform)
                    except Exception:
                        transform = element.composed_transform()
                        x1, y1 = transform.apply_to_point([0, 0])
                        x2, y2 = transform.apply_to_point([1, 1])
                        bbox += inkex.BoundingBox((x1, x2), (y1, y2))
     
            if abs(bbox.width) == math.inf or abs(bbox.height) == math.inf:
                inkex.utils.debug("bounding box could not be calculated. SVG seems to be empty.")
            #else:
            #    inkex.utils.debug("bounding box is {}".format(bbox))
            scale_factor = self.svg.unittouu("1px")
            page_width = self.svg.unittouu(self.document.getroot().attrib['width'])
            width_height = self.svg.unittouu(self.document.getroot().attrib['height'])
            fmm = self.svg.unittouu(str(so.bbox_offset) + "mm")
            bb_left = round(bbox.left, 3)
            bb_right = round(bbox.right, 3)
            bb_top = round(bbox.top, 3)
            bb_bottom = round(bbox.bottom, 3)
            bb_width = round(bbox.width, 3)
            bb_height = round(bbox.height, 3)
            if bb_left >= fmm:
                if so.show_issues_only is False:
                    inkex.utils.debug("left border... ok")
            else:
                inkex.utils.debug("left border... fail: {:0.3f} mm".format(self.svg.uutounit(bb_left, "mm")))
                 
            if bb_top >= fmm:
                if so.show_issues_only is False:
                    inkex.utils.debug("top border... ok")
            else:
                inkex.utils.debug("top border... fail: {:0.3f} mm".format(self.svg.uutounit(bb_top, "mm")))
                
            if bb_right + fmm <= page_width:
                if so.show_issues_only is False:
                    inkex.utils.debug("right border... ok")
            else:
                inkex.utils.debug("right border... fail: {:0.3f} mm".format(self.svg.uutounit(bb_right, "mm")))
                
            if bb_bottom + fmm <= width_height:
                if so.show_issues_only is False:
                    inkex.utils.debug("bottom border... ok")
            else:
                inkex.utils.debug("bottom border... fail: {:0.3f} mm".format(self.svg.uutounit(bb_bottom, "mm")))
            if bb_width <= machineWidth:
                if so.show_issues_only is False:
                    inkex.utils.debug("page width... ok")
            else:
                inkex.utils.debug("page width... fail: {:0.3f} mm".format(bb_width))
            if bb_height <= machineHeight:
                if so.show_issues_only is False:
                    inkex.utils.debug("page height... ok")
            else:
                inkex.utils.debug("page height... fail: {:0.3f} mm".format(bb_height))
             
        
        if so.checks == "check_all" or so.groups_and_layers is True:
            inkex.utils.debug("\n---------- Groups and layers")
            global md
            md = 0
            def maxDepth(element, level): 
                global md
                if (level == md):
                    md += 1
                for child in element:
                    maxDepth(child, level + 1) 
            maxDepth(self.document.getroot(), -1)
            if so.show_issues_only is False:        
               inkex.utils.debug("Maximum group depth={}".format(md - 1))
            if md - 1 > 2:
                self.msg("Warning: this group depth might cause issues!")
            groups = []
            layers = []
            for element in selected:
                if element.tag == inkex.addNS('g','svg'):
                    if element.get('inkscape:groupmode') == 'layer':
                        layers.append(element)
                    else:
                        groups.append(element)
            if so.show_issues_only is False:  
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

        '''
        Clones should be unlinked because they cause similar issues like transformations
        '''
        if so.checks == "check_all" or so.clones is True:
            inkex.utils.debug("\n---------- Clones (svg:use) - maybe unlink") 
            uses = []
            for element in selected:
                if element.tag == inkex.addNS('use','svg'):
                    uses.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} svg:use clones in total".format(len(uses)))
            for use in uses:
                inkex.utils.debug("id={}".format(use.get('id')))
   
   
        '''
        Clip paths are neat to visualize things, but they do not perform a real path cutting.
        Please perform real intersections to have an intact target geometry.
        '''
        if so.checks == "check_all" or so.clippaths is True:
            inkex.utils.debug("\n---------- Clippings (svg:clipPath) - please replace with real cut paths") 
            clipPaths = []
            for element in selected:
                if element.tag == inkex.addNS('clipPath','svg'):
                    clipPaths.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} svg:clipPath in total".format(len(clipPaths)))
            for clipPath in clipPaths:
                inkex.utils.debug("id={}".format(clipPath.get('id')))
   
   
        '''
        Sometimes images look like vector but they are'nt. In case you dont want to perform engraving, either
        check to drop or trace to vector paths
        '''
        if so.checks == "check_all" or so.images is True:
            inkex.utils.debug("\n---------- Images (svg:image) - maybe trace to svg") 
            images = []
            for element in selected:
                if element.tag == inkex.addNS('image','svg'):
                    images.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} svg:image in total".format(len(images)))
            for image in images:
                inkex.utils.debug("image id={}".format(image.get('id')))
    
    
        '''
        Low level strokes cannot be properly edited in Inkscape (no node handles). Converting helps
        '''
        if so.checks == "check_all" or so.lowlevelstrokes is True:
            inkex.utils.debug("\n---------- Low level strokes (svg:line/polyline/polygon) - maybe convert to path") 
            lowlevels = []
            for element in selected:
                if element.tag in (inkex.addNS('line','svg'), inkex.addNS('polyline','svg'), inkex.addNS('polygon','svg')):
                    lowlevels.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} low level strokes in total".format(len(lowlevels)))
            for lowlevel in lowlevels:
                inkex.utils.debug("id={}".format(lowlevel.get('id')))
    
    
        '''
        Texts cause problems when sharing with other people. You must ensure that everyone has the
        font files installed you used. Convert to paths avoids this issue and guarantees same result
        everywhere.
        '''
        if so.checks == "check_all" or so.texts is True:
            inkex.utils.debug("\n---------- Texts (should be converted to paths)") 
            texts = []
            for element in selected:
                if element.tag == inkex.addNS('text','svg'):
                    texts.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} svg:text in total".format(len(texts)))
            for text in texts:
                inkex.utils.debug("id={}".format(text.get('id')))
             

        
        '''
        The more stroke colors the more laser job configuration is required. Reduce the SVG file
        to a minimum of stroke colors to be quicker
        '''
        if so.checks == "check_all" or so.stroke_colors is True:
            inkex.utils.debug("\n---------- Stroke colors ({} are allowed)".format(so.stroke_colors_max))
            strokeColors = []
            for element in shapes:          
                style = element.get('style')
                if style is not None:
                    stroke = re.search('(;|^)stroke:(.*?)(;|$)', style)
                    if stroke is not None:
                        strokeColor = stroke[0].split("stroke:")[1].split(";")[0]
                        if strokeColor not in strokeColors:
                            strokeColors.append(strokeColor)
            if so.show_issues_only is False:
                inkex.utils.debug("{} different stroke colors in total".format(len(strokeColors)))
            if len(strokeColors) > so.stroke_colors_max:
                for strokeColor in strokeColors:
                    inkex.utils.debug("stroke color {}".format(strokeColor))
                    
      
        '''
        Different stroke widths might behave the same like different stroke colors. Reduce to a minimum set.
        Ideally all stroke widths are set to 1 pixel.
        '''
        if so.checks == "check_all" or so.stroke_widths is True:              
            inkex.utils.debug("\n---------- Stroke widths ({} are allowed)".format(so.stroke_widths_max))
            strokeWidths = []
            for element in shapes:          
                style = element.get('style')
                if style is not None:
                    stroke_width = re.search('stroke-width:(.*?)(;|$)', style)
                    if stroke_width is not None:
                        strokeWidth = stroke_width[0].split("stroke-width:")[1].split(";")[0] #possibly w/o units. could contain units from css
                        if strokeWidth not in strokeWidths:
                            strokeWidths.append(strokeWidth)
            if so.show_issues_only is False:
                inkex.utils.debug("{} different stroke widths in total".format(len(strokeWidths)))
            if len(strokeWidths) > so.stroke_widths_max:
                for strokeWidth in strokeWidths:
                    swConverted = self.svg.uutounit(float(self.svg.unittouu(strokeWidth))) #possibly w/o units. we unify to some internal float
                    inkex.utils.debug("stroke width {}px ({}mm)".format(
                        round(self.svg.uutounit(swConverted, "px"),4),
                        round(self.svg.uutounit(swConverted, "mm"),4),
                        )
                    )
                
                
        '''
        Cosmetic dashes cause simulation issues and are no real cut paths. It's similar to the thing
        with clip paths. Please convert lines to real dash segments if you want to laser them.
        '''
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
            if so.show_issues_only is False:
                inkex.utils.debug("{} different stroke dash arrays in total".format(len(strokeDasharrays)))
            for strokeDasharray in strokeDasharrays:
                inkex.utils.debug("stroke dash array {}".format(strokeDasharray))
     
  
        '''
        Shapes/paths with the same color like the background, 0% opacity, etc. lead to strange
        laser cutting results, like duplicated edges, enlarged laser times and more. Please double
        check for such occurences.
        '''
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
            if so.show_issues_only is False:
                inkex.utils.debug("{} invisible shapes in total".format(len(invisibles)))
            for invisible in invisibles:
                inkex.utils.debug("id={}".format(invisible.get('id')))
          
                
        '''
        Additionally, stroke opacities less than 1.0 cause problems in most laser softwares. Please
        adjust all strokes to use full opacity.
        '''
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
            if so.show_issues_only is False:
                inkex.utils.debug("{} objects with stroke transparencies < 1.0 in total".format(len(transparencies)))
            for transparency in transparencies:
                inkex.utils.debug("id={}".format(transparency.get('id')))  
      
        '''
        We look for paths which are just points. Those are useless in case of lasercutting.
        Note: this scan only works for paths, not for subpaths. If so, you need to break apart before
        '''
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
            if so.show_issues_only is False:
                inkex.utils.debug("{} pointy paths in total".format(len(pointyPaths)))
            for pointyPath in pointyPaths:
                inkex.utils.debug("id={}".format(pointyPath.get('id')))    
   
   
        '''
        Transformations often lead to wrong stroke widths or mis-rendering in end software. The best we
        can do with a final SVG is to remove all relative translations, rotations and scalings. We should
        apply absolute coordinates only.
        '''
        if so.checks == "check_all" or so.transformations is True:
            inkex.utils.debug("\n---------- Transformations - should be applied to absolute")
            transformations = []
            for element in shapes:
                if element.get('transform') is not None:
                    transformations.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} transformation in total".format(len(transformations)))
            for transformation in transformations:
                inkex.utils.debug("transformation in id={}".format(transformation.get('id')))    
          
        '''
        Really short paths can cause issues with laser cutter mechanics and should be avoided to 
        have healthier stepper motor belts, etc.
        '''
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
                        shortPaths.append([element, stotal])
                        totalDropLength += stotal
            if so.show_issues_only is False:
                inkex.utils.debug("{} short paths in total".format(len(shortPaths)))
            if totalDropLength > 0:
                inkex.utils.debug("{:0.2f}% of total ({:0.2f} mm /{:0.2f} mm)".format(totalDropLength / totalLength, self.svg.uutounit(str(totalDropLength), "mm"), self.svg.uutounit(str(totalLength), "mm")))
            for shortPath in shortPaths:
                inkex.utils.debug("id={}, length={}mm".format(shortPath[0].get('id'), round(self.svg.uutounit(str(shortPath[1]), "mm"), 3)))    
          
        '''
        Really short paths can cause issues with laser cutter mechanics and should be avoided to 
        have healthier stepper motor belts, etc.
        '''
        if so.checks == "check_all" or so.cutting_estimation is True:
            inkex.utils.debug("\n---------- Cutting time estimation")
            totalCuttingLength = 0
            for element in shapes:
                if isinstance(element, inkex.PathElement):
                    slengths, stotal = csplength(element.path.transform(element.composed_transform()).to_superpath())
                    totalCuttingLength += stotal
            extraTraveLength = (machineWidth / 3 + machineHeight / 3) * 2.0 #from top-left to the ~1/3 of the bed and back again
            totalTravelLength = totalCuttingLength * (1.0 - so.cut_travel_factor) + extraTraveLength
            totalLength = totalCuttingLength + totalTravelLength
            inkex.utils.debug("(measured) cutting length (mm) = {:0.2f} mm".format(self.svg.uutounit(str(totalCuttingLength), "mm"), self.svg.uutounit(str(totalCuttingLength), "mm")))
            inkex.utils.debug("(estimated) travel length (mm) = {:0.2f} mm".format(self.svg.uutounit(str(totalTravelLength), "mm"), self.svg.uutounit(str(totalTravelLength), "mm")))
            inkex.utils.debug("(estimated) total length (mm) = {:0.2f} mm".format(self.svg.uutounit(str(totalLength), "mm"), self.svg.uutounit(str(totalLength), "mm")))
            for speedFactor in [100,90,80,70,60,50,40,30,20,10,5]:
                v_cut    = so.max_cutting_speed * speedFactor/100.0
                v_travel = so.max_travel_speed #this is always at maximum
                tsec_cut    = self.svg.uutounit(str(totalCuttingLength)) / v_cut
                tsec_travel = self.svg.uutounit(str(totalTravelLength))  / v_travel
                tsec_total = tsec_cut + tsec_travel
                minutes, seconds = divmod(tsec_total, 60)  # split the seconds to minutes and seconds
                partial_minutes = round(seconds/60 * 2) / 2
                inkex.utils.debug("@{:03.0f}% (cut={:06.2f}mm/s | travel={:06.2f}mm/s) > {:03.0f}min {:02.0f}sec | cost={:02.0f}€".format(speedFactor, v_cut, v_travel, minutes, seconds, so.price_per_minute_gross * (minutes + partial_minutes)))

        
        '''
        Paths with a high amount of nodes will cause issues because each node means slowing down/speeding up the laser mechanics
        '''
        if so.checks == "check_all" or so.nodes_per_path is True:  
            inkex.utils.debug("\n---------- Heavy node-loaded paths (allowed: {} node(s) per {} mm) - should be simplified".format(so.nodes_per_path_max, round(so.nodes_per_path_interval, 3)))
            heavyPaths = []
            for element in shapes:
                if isinstance(element, inkex.PathElement):
                    slengths, stotal = csplength(element.path.transform(element.composed_transform()).to_superpath())
                    nodes = len(element.path)
                    if nodes /  stotal > so.nodes_per_path_max / self.svg.unittouu(str(so.nodes_per_path_interval) + "mm"):
                        heavyPaths.append([element, nodes, stotal])
            if so.show_issues_only is False:
                inkex.utils.debug("{} Heavy node-loaded paths in total".format(len(heavyPaths)))
            for heavyPath in heavyPaths:
                inkex.utils.debug("id={}, nodes={}, length={}mm, density={}nodes/mm".format(
                        heavyPath[0].get('id'), 
                        heavyPath[1], 
                        round(self.svg.uutounit(str(heavyPath[2]), "mm"), 3),
                        round(heavyPath[1] / self.svg.uutounit(str(heavyPath[2]), "mm"), 3)
                        )
                    )
          
        '''
        Elements outside canvas or touching the border. These are critical because they won't be lasered or not correctly lasered
        '''
        if so.checks == "check_all" or so.elements_outside_canvas is True:  
            inkex.utils.debug("\n---------- Elements outside canvas or touching the border")
            elementsOutside = []
            for element in shapes:
                if element.tag != inkex.addNS('g', 'svg'):
                    ebbox = element.bounding_box()
                    precision = 3
                    #inkex.utils.debug("{} | bbox: left = {:0.3f} right = {:0.3f} top = {:0.3f} bottom = {:0.3f}".format(element.get('id'), ebbox.left, ebbox.right, ebbox.top, ebbox.bottom))
                    pagew = round(self.svg.unittouu(self.svg.get('width')), precision)
                    pageh = round(self.svg.unittouu(self.svg.get('height')), precision)
                    if round(ebbox.right,  precision) == 0 or \
                       round(ebbox.left,   precision) == pagew or \
                       round(ebbox.top,    precision) == 0 or \
                       round(ebbox.bottom, precision) == pageh:
                        elementsOutside.append([element, "touching"])
                    elif \
                       round(ebbox.right,  precision) < 0 or \
                       round(ebbox.left,   precision) > pagew or \
                       round(ebbox.top,    precision) < 0 or \
                       round(ebbox.bottom, precision) > pageh:
                        elementsOutside.append([element, "fully outside"])
                    else: #fully inside or partially inside/outside. we check if one or more corners is outside the canvas
                        rightOutside = False
                        leftOutside = False
                        topOutside = False
                        bottomOutside = False
                        if round(ebbox.right,  precision) < 0 or round(ebbox.right,  precision) > pagew:
                           rightOutside = True
                        if round(ebbox.left,  precision) < 0 or round(ebbox.left,  precision) > pagew:
                           leftOutside = True  
                        if round(ebbox.top,  precision) < 0 or round(ebbox.top,  precision) > pageh:
                           topOutside = True
                        if round(ebbox.bottom,  precision) < 0 or round(ebbox.bottom,  precision) > pageh:
                           bottomOutside = True
                        if rightOutside is True or leftOutside is True or topOutside is True or bottomOutside is True:
                            elementsOutside.append([element, "partially outside"])
            if so.show_issues_only is False:
                inkex.utils.debug("{} Elements outside canvas or touching the border in total".format(len(elementsOutside)))
            for elementOutside in elementsOutside:
                inkex.utils.debug("id={}, status={}".format(
                        elementOutside[0].get('id'), 
                        elementOutside[1]
                        )
                    )    
             
                   
        '''
        Shapes like rectangles, ellipses, arcs, spirals should be converted to svg:path to have more
        convenience in the file
        '''
        if so.checks == "check_all" or so.non_path_shapes is True:          
            inkex.utils.debug("\n---------- Non-path shapes - should be converted to paths")
            nonPathShapes = []
            for element in shapes:
                if not isinstance(element, inkex.PathElement) and not isinstance(element, inkex.Group):
                    nonPathShapes.append(element)
            if so.show_issues_only is False:
                inkex.utils.debug("{} non-path shapes in total".format(len(nonPathShapes)))
            for nonPathShape in nonPathShapes:
                inkex.utils.debug("id={}".format(nonPathShape.get('id')))         
         
        exit(0)
                             
if __name__ == '__main__':
    LaserCheck().run()