#!/usr/bin/env python3

import inkex
from inkex.paths import Path
from inkex import Circle

class DrawDirections(inkex.EffectExtension):

    def drawCircle(self, group, color, point):
        style = inkex.Style({'stroke': 'none', 'fill': color})
        startCircle = group.add(Circle(cx=str(point[0]), cy=str(point[1]), r=str(self.svg.unittouu(str(self.options.dotsize/2) + "px"))))
        startCircle.style = style

    def add_arguments(self, pars):
        pars.add_argument("--dotsize", type=int, default=10, help="Dot size (px) for self-intersecting points")
   
    def effect(self):
        dot_group = self.svg.add(inkex.Group())
    
        for node in self.svg.selection.filter(inkex.PathElement).values():
            points = list(node.path.end_points)
            start = points[0]
            end = points[len(points) - 1]
                    
            if start[0] == end[0] and start[1] == end[1]:
                self.drawCircle(dot_group, '#00FF00', start) 
                self.drawCircle(dot_group, '#FFFF00', points[1]) #draw one point which gives direction of the path
            else: #open contour with start and end point
                self.drawCircle(dot_group, '#FF0000', start)
                self.drawCircle(dot_group, '#0000FF', end)
                  
if __name__ == '__main__':
    DrawDirections().run()