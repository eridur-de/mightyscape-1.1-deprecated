#!/usr/bin/env python3

import inkex
from inkex.paths import Path
from inkex import Circle

# Draws red points at the path's beginning and blue point at the path's end

class StartEndPoints(inkex.Effect):

    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--dotsize", type=int, default=10, help="Dot size (px) for self-intersecting points")
   
    def effect(self):
        dot_group = node.getparent().add(inkex.Group())
    
        for node in self.svg.selection.values():
        
            points = list(node.path.end_points)
            start = points[0]
            end = points[len(points) - 1]
                       
            style = inkex.Style({'stroke': 'none', 'fill': '#FF0000'})
            startCircle = dot_group.add(Circle(cx=str(start[0]), cy=str(start[1]), r=str(self.svg.unittouu(str(self.options.dotsize/2) + "px"))))
            startCircle.style = style
            
            style = inkex.Style({'stroke': 'none', 'fill': '#0000FF'})
            endCircle = dot_group.add(Circle(cx=str(end[0]), cy=str(end[1]), r=str(self.svg.unittouu(str(self.options.dotsize/2) + "px"))))
            endCircle.style = style
            
StartEndPoints().run()