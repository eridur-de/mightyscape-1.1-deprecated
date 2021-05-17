#!/usr/bin/env python3

"""
For each selected path element, this extension creates an additional path element
consisting of horizontal line segments which are the same size as the original
line segments. Has option to extrude as a band (add height; adds vertical lines and another horizontal path)

ToDo:
- option to colorize each line segment of the original curve (we need to split and group the original one to do this). We map the colors to the unwinded paths
- handle combined paths correctly
- copy style of input paths and only apply new colors

"""

import inkex
from inkex import bezier
from lxml import etree
import math

class UnwindPaths(inkex.EffectExtension):
    
    #draw an SVG line segment between the given (raw) points
    def drawline(self, pathData, name, parent):
        line_style   = {'stroke':'#000000','stroke-width':'1px','fill':'none'}
        line_attribs = {'style' : str(inkex.Style(line_style)),
                    inkex.addNS('label','inkscape') : name,
                    'd' : pathData}
        line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )
        
    
    def add_arguments(self, pars):
        pars.add_argument('--extrude', type=inkex.Boolean, default=False)
        pars.add_argument('--extrude_height', type=float, default=10.000)
        pars.add_argument('--unit', default="mm")

    def effect(self):
        path_num = 0  
        shifting = self.svg.unittouu(str(self.options.extrude_height) + self.options.unit)
        
        for element in self.svg.selection.filter(inkex.PathElement).values(): 
            elemGroup = self.svg.get_current_layer().add(inkex.Group(id="unwinding-" + element.get('id')))

            #beginning point of the unwind band:
            bbox = element.bounding_box() #shift the element to the bottom of the element
            xmin = bbox.left
            ymax = bbox.bottom
   
            for sub in element.path.to_superpath():
                new = []
                new.append([sub[0]])
                i = 1
                topPathData = "m {:0.6f},{:0.6f} ".format(xmin, ymax)
                bottomPathData = "m {:0.6f},{:0.6f} ".format(xmin, ymax + shifting)
                lengths = []
                while i <= len(sub) - 1:
                    length = bezier.cspseglength(new[-1][-1], sub[i]) #sub path length
                    lengths.append(length)
                    segment = "l {:0.6f},{:0.0f} ".format(length, 0)
                    topPathData += segment
                    bottomPathData += segment
                    new[-1].append(sub[i])
                    i += 1           
                                     
                self.drawline(topPathData, "hline-top-{0}".format(element.get('id')), elemGroup)
                if self.options.extrude is True:
                    self.drawline(bottomPathData, "hline-bottom-{0}".format(element.get('id')), elemGroup)
                    
                    #draw as much vertical lines as segments in bezier + start + end vertical line
                    self.drawline("m {:0.6f},{:0.6f} v {:0.6f}".format(xmin, ymax, shifting),"vline{0}".format(path_num), elemGroup)
                    self.drawline("m {:0.6f},{:0.6f} v {:0.6f}".format(xmin + sum([length for length in lengths]), ymax, shifting),"vline{0}".format(path_num), elemGroup)
                    x = 0
                    for n in range(0, i-1):           
                        x += lengths[n]
                        self.drawline("m {:0.6f},{:0.6f} v {:0.6f}".format(xmin + x, ymax, shifting),"vline{0}".format(path_num), elemGroup)

if __name__ == '__main__':
    UnwindPaths().run()
