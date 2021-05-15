#!/usr/bin/env python3

"""
A Inkscape extension to generate a pattern that allows to bend wood or MDF one it is laser cut.
"""

import inkex
import math
from lxml import etree

class BendWoodCutsPattern(inkex.Effect):
    height = -1.0
    
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument('--width', type=float, default=10, help='Width (mm)')
        self.arg_parser.add_argument('--height', type=float, default=100, help='Height (mm)')
        self.arg_parser.add_argument('--horizontalLineSeparation', type=float, default=1, help='Horizontal Line Separation (mm)')
        self.arg_parser.add_argument('--verticalLineSeparation', type=float, default=3, help='Vertical Line Separation (mm)')
        self.arg_parser.add_argument('--maxLineLength', type=float, default=30, help='Max Line Length (mm)')
        self.arg_parser.add_argument('--addInitMarks', default="false", help='Add Init Marks')
        self.arg_parser.add_argument('--groupLines', default="false", help='Group Lines')

#draw an SVG line segment between the given (raw) points
    def draw_SVG_line(self, x1, y1, x2, y2, parent):
        
        if self.height < 0:
            svg = self.document.getroot()
            self.height = self.svg.unittouu(svg.attrib['height'])
           
        line_style   = { 'stroke-width':self.svg.unittouu(str(0.1)+"mm"), 'stroke':'#000000'}

        line_attribs = {'style' : str(inkex.Style(line_style)),
                        'd' : 'M '+str(x1)+','+str(self.height - y1)+' L '+str(x2)+','+str(self.height - y2)}

        line = etree.SubElement(parent, inkex.addNS('path','svg'), line_attribs )
           
    def effect(self):
        width = self.options.width 
        height = self.options.height
        horizontalLineSeparation = self.options.horizontalLineSeparation
        verticalLineSeparation = self.options.verticalLineSeparation
        maxLineLength = self.options.maxLineLength
        marks = self.options.addInitMarks == "true"
        group = self.options.groupLines == "true"
        
        parent = self.svg.get_current_layer()

        if group: 
            parent = etree.SubElement(parent, 'g')
        
        xLines = int(width / horizontalLineSeparation)
        maxLineLength = self.options.maxLineLength
        
        linesPerColumn = int(math.ceil(height / maxLineLength))
        ll = height / linesPerColumn
        
        for x in range(0, xLines):
            if marks:
                self.draw_SVG_line(x * horizontalLineSeparation, -3, x * horizontalLineSeparation, -2, parent)
                
            if x % 2 == 0:
                for y in range(0, linesPerColumn):
                    self.draw_SVG_line(x * horizontalLineSeparation, y * ll + verticalLineSeparation / 2, x * horizontalLineSeparation, (y + 1) * ll - verticalLineSeparation / 2, parent)
                
            else:
                for y in range(-1, linesPerColumn):
                    incy = ll / 2
                    
                    y0 = y * ll + verticalLineSeparation / 2 + incy
                    if y0 < 0:
                        y0 = -1
                        
                    y1 = (y + 1) * ll - verticalLineSeparation / 2 + incy
                    
                    if y1 > height:
                        y1 = height + 1
                    
                    self.draw_SVG_line(x * horizontalLineSeparation, y0, x * horizontalLineSeparation, y1, parent)
                
if __name__ == '__main__':
    BendWoodCutsPattern().run()