#!/usr/bin/env python3

from lxml import etree
import itertools
import inkex
from inkex import Circle, Vector2d
from inkex.paths import Path
from inkex.bezier import csplength

class DrawDirectionsTravelMoves(inkex.EffectExtension):

    def drawCircle(self, transform, group, color, point):
        style = inkex.Style({'stroke': 'none', 'fill': color})
        startCircle = group.add(Circle(cx=str(point[0]), cy=str(point[1]), r=str(self.svg.unittouu(str(so.dotsize/2) + "px"))))
        startCircle.style = style
        startCircle.transform = transform

    def find_group(self, groupId):
        ''' check if a group with a given id exists or not. Returns None if not found, else returns the group element '''
        groups = self.document.xpath('//svg:g', namespaces=inkex.NSS)
        for group in groups:
            #inkex.utils.debug(str(layer.get('inkscape:label')) + " == " + layerName)
            if group.get('id') == groupId:
                return group
        return None

    def add_arguments(self, pars):
        pars.add_argument("--nb_main")
        
        pars.add_argument("--draw_dots", type=inkex.Boolean, default=True, help="Start and end point of opened (red + blue) and closed paths (green + yellow)")
        pars.add_argument("--dotsize", type=int, default=10, help="Dot size (px)")
        pars.add_argument("--draw_travel_moves", type=inkex.Boolean, default=False)
        pars.add_argument("--ignore_colors", type=inkex.Boolean, default=False, help="If enabled we connect all lines by order, ignoring the stroke color (normally we have one travel line group per color)")
        pars.add_argument("--dashed_style", type=inkex.Boolean, default=True)
        pars.add_argument("--arrow_style", type=inkex.Boolean, default=True)
        pars.add_argument("--arrow_size", type=float, default=True)
        pars.add_argument("--debug", type=inkex.Boolean, default=False)

    def effect(self):
        global so
        so = self.options
        linePrefix = "travelLine-"
        groupPrefix = "travelLines-"
        ignoreWord = "ignore"
          
        selectedPaths = [] #total list of elements to parse
     
        def parseChildren(element):
            if isinstance(element, inkex.PathElement) and element not in selectedPaths and linePrefix not in element.get('id') and not isinstance(element.getparent(), inkex.Marker):
                selectedPaths.append(element)
            children = element.getchildren()
            if children is not None:
                for child in children:
                    if isinstance(child, inkex.PathElement) and child not in selectedPaths and linePrefix not in element.get('id') and not isinstance(element.getparent(), inkex.Marker):
                        selectedPaths.append(child)
                    parseChildren(child) #go deeper and deeper
        
        #check if we have selectedPaths elements or if we should parse the whole document instead
        if len(self.svg.selected) == 0:
            for element in self.document.getroot().iter(tag=etree.Element):
                if isinstance(element, inkex.PathElement) and element != self.document.getroot() and linePrefix not in element.get('id') and not isinstance(element.getparent(), inkex.Marker):
                    selectedPaths.append(element)
        else:
            for element in self.svg.selected.values():
                parseChildren(element)
            
        dot_group = self.svg.add(inkex.Group())

        if so.arrow_style is True:
            markerId = "travel_move_arrow"
            #add new marker to defs (or overwrite if existent)
            defs = self.svg.defs
            for defi in defs:
                if defi.tag == "{http://www.w3.org/2000/svg}marker" and defi.get('id') == markerId: #delete
                    defi.delete()
            marker = inkex.Marker(id=markerId)
            marker.set("inkscape:isstock", "true")
            marker.set("inkscape:stockid", markerId)
            marker.set("orient", "auto")  
            marker.set("refY", "0.0")
            marker.set("refX", "0.0")
            marker.set("style", "overflow:visible;")
            
            markerPath = inkex.PathElement(id=self.svg.get_unique_id('markerId-'))
            markerPath.style = {"fill-rule": "evenodd", "fill": "context-stroke", "stroke-width": str(self.svg.unittouu('1px'))}
            markerPath.transform = "scale(1.0,1.0) rotate(0) translate(-6.0,0)"
            arrowHeight = 6.0
            markerPath.attrib["transform"] = "scale({},{}) rotate(0) translate(-{},0)".format(so.arrow_size, so.arrow_size, arrowHeight)
            markerPath.path = "M {},0.0 L -3.0,5.0 L -3.0,-5.0 L {},0.0 z".format(arrowHeight, arrowHeight)
            
            marker.append(markerPath)       
            defs.append(marker) #do not append before letting contain it one path. Otherwise Inkscape is going to crash immediately
    
        #collect all different stroke colors to distinguish by groups      
        strokeColors = []
        strokeColorsAndCounts = {}
      
        for element in selectedPaths:
            strokeColor = element.style.get('stroke')
            if strokeColor is None or strokeColor == "none":
                strokeColor = "none"
            if so.ignore_colors is True:
                strokeColor = ignoreWord     
            strokeColors.append(strokeColor)
            groupName = groupPrefix + strokeColor
            travelGroup = self.find_group(groupName)
            if travelGroup is None:
                self.document.getroot().append(inkex.Group(id=groupName))
            else: #exists
                self.document.getroot().append(travelGroup)
                for child in travelGroup:
                    child.delete()

        for strokeColor in strokeColors:
            if strokeColor in strokeColorsAndCounts:
                strokeColorsAndCounts[strokeColor] = strokeColorsAndCounts[strokeColor] + 1
            else:
                strokeColorsAndCounts[strokeColor] = 1
    
        startEndPath = [] #the container for all paths we will loop on
        for element in selectedPaths:
            #points = list(element.path.end_points)
            p = element.path.transform(element.composed_transform())
            points = list(p.end_points)
            start = points[0]
            end = points[len(points) - 1]    
                 
            startEndPath.append([element, start, end])
            
            #if element.getparent() != self.document.getroot():
            #    transform = element.getparent().composed_transform()
            #else:
            #    transform = None
            transform = None
            if so.draw_dots is True:        
                if start[0] == end[0] and start[1] == end[1]:
                    self.drawCircle(transform, dot_group, '#00FF00', start) 
                    self.drawCircle(transform, dot_group, '#FFFF00', points[1]) #draw one point which gives direction of the path
                else: #open contour with start and end point
                    self.drawCircle(transform, dot_group, '#FF0000', start)
                    self.drawCircle(transform, dot_group, '#0000FF', end)

        if so.draw_travel_moves is True:
            for sc in strokeColorsAndCounts: #loop through all unique stroke colors
                colorCount = strokeColorsAndCounts[sc] #the total color count per stroke color
                ran = len(startEndPath) + 1 #one more because the last travel moves goes back to 0,0 (so for 3 elements (1,2,3) the range is 0 to 3 -> makes 4)
                firstOccurence = True 
                createdMoves = 0
                for i in range(0, ran): #loop through the item selection. nested loop. so we loop over alle elements again for each color
                    if i < ran - 1:
                        elementStroke = startEndPath[i][0].style.get('stroke')
                    if i == ran or createdMoves == colorCount:
                        elementStroke = startEndPath[i-1][0].style.get('stroke')
                    if elementStroke is None or elementStroke == "none":
                        elementStroke = "none"
            
                    if so.debug is True: inkex.utils.debug("current stroke color {}, element stroke color{}".format(sc, elementStroke))
                    if sc == elementStroke or sc == ignoreWord:   
                        if firstOccurence is True:
                            travelStart = Vector2d(0,0)
                            firstOccurence = False
                        else:
                            if i <= ran - 1:
                                travelStart = startEndPath[i-1][2] #end point from this path
                        
                        if so.debug is True: inkex.utils.debug("travelStart={}".format(travelStart))
                        if i < ran - 1:
                            travelEnd = startEndPath[i][1]
                        if createdMoves == colorCount:
                            travelEnd = Vector2d(0,0)
                               
                        if so.debug is True: inkex.utils.debug("travelEnd={}".format(travelEnd)) 
        
                        if so.debug is True:
                            if i < ran - 1:   
                                inkex.utils.debug("segment={},{}".format(startEndPath[i][2], startEndPath[i][1]))
                            if i == ran - 1:
                                inkex.utils.debug("segment={},{}".format(startEndPath[i-1][1], travelEnd))

                        travelLine = inkex.PathElement(id=self.svg.get_unique_id(linePrefix) + element.get('id'))
                        #if some objects are at svg:svg level this may cause errors
                        #if element.getparent() != self.document.getroot():
                        #    travelLine.transform = element.getparent().composed_transform()
                        travelLine.set('d', "M{:0.6f},{:0.6f} L{:0.6f},{:0.6f}".format(travelStart[0],travelStart[1],travelEnd[0],travelEnd[1]))
                        travelLine.style = {'stroke': ("#000000" if so.ignore_colors is True else sc), 'fill': 'none', 'stroke-width': str(self.svg.unittouu('1px')), 'marker-end': 'url(#marker1426)'}
                        if so.dashed_style is True:
                            travelLine.style['stroke-dasharray'] = '1,1'
                            travelLine.style['stroke-dashoffset'] = '0'
                        if so.arrow_style is True:
                            travelLine.style["marker-end"] = "url(#{})".format(markerId)
                            
                        #check the length. if zero we do not add
                        slengths, stotal = csplength(travelLine.path.transform(element.composed_transform()).to_superpath()) #get segment lengths and total length of path in document's internal unit
                        if stotal > 0:
                            #finally add the line
                            travelGroup = self.find_group(groupPrefix + sc)
                            travelGroup.add(travelLine)
                        else:
                             if so.debug is True: inkex.utils.debug("Line has length of zero")

                        createdMoves += 1 #each time we created a move we count up. we want to compare against the total count of that color
                        if so.debug is True: inkex.utils.debug("createdMoves={}".format(createdMoves))
                if so.debug is True: inkex.utils.debug("-"*40)
                  
        #cleanup empty groups         
        if len(dot_group) == 0:
            dot_group.delete()
        travelGroups = self.document.xpath("//svg:g[starts-with(@id, 'travelLines-')]", namespaces=inkex.NSS)
        for travelGroup in travelGroups:
            if len(travelGroup) == 0:
                travelGroup.delete()
                                            
if __name__ == '__main__':
    DrawDirectionsTravelMoves().run()