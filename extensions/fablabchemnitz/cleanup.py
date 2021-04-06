#!/usr/bin/env python3
'''
Copyright (C) 2013 Matthew Dockrey  (gfish @ cyphertext.net)

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

Based on coloreffect.py by Jos Hirth and Aaron C. Spike
'''

import inkex
import re

class Cleanup(inkex.EffectExtension):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--stroke_width", type=float, default=0.1, help="Stroke width")
        self.arg_parser.add_argument("--stroke_units", default="mm", help="Stroke unit")
        self.arg_parser.add_argument("--opacity", type=float, default="100.0", help="Opacity")
        self.arg_parser.add_argument("--reset_style_attributes", type=inkex.Boolean, help="Remove stroke style attributes like stroke-dasharray, stroke-dashoffset, stroke-linejoin, linecap, stroke-miterlimit")
        self.arg_parser.add_argument("--reset_fill_attributes", type=inkex.Boolean, help="Sets 'fill:none;' to style attribute")
        self.arg_parser.add_argument("--apply_hairlines", type=inkex.Boolean, help="Adds 'vector-effect:non-scaling-stroke;' and '-inkscape-stroke:hairline;' Hint: stroke-width is kept in background. All hairlines still have a valued width.")
        self.arg_parser.add_argument("--apply_black_strokes", type=inkex.Boolean, help="Adds 'stroke:#000000;' to style attribute")


    def effect(self):
        if len(self.svg.selected) == 0:
            self.getAttribs(self.document.getroot())
        else:
            for id, node in self.svg.selected.items():
                self.getAttribs(node)

    def getAttribs(self, node):
        self.changeStyle(node)
        for child in node:
            self.getAttribs(child)

    #stroke and fill styles can be included in style attribute or they can exist separately (can occure in older SVG files). We do not parse other attributes than style
    def changeStyle(self, node):
        nodeDict = []
        nodeDict.append(inkex.addNS('line','svg'))
        nodeDict.append(inkex.addNS('polyline','svg'))
        nodeDict.append(inkex.addNS('polygon','svg'))
        nodeDict.append(inkex.addNS('circle','svg'))
        nodeDict.append(inkex.addNS('ellipse','svg'))
        nodeDict.append(inkex.addNS('rect','svg'))
        nodeDict.append(inkex.addNS('path','svg'))
        nodeDict.append(inkex.addNS('g','svg'))
        if node.tag in nodeDict:
            if node.attrib.has_key('style'):
                style = node.get('style')
                if style:  
                    #add missing style attributes if required
                    if style.endswith(';') is False:
                        style += ';'
                    if re.search('(;|^)stroke:(.*?)(;|$)', style) is None: #if "stroke" is None, add one. We need to distinguish because there's also attribute "-inkscape-stroke" that's why we check starting with ^ or ;
                        style += 'stroke:none;'
                    if "stroke-width:" not in style:
                        style += 'stroke-width:{:1.4f};'.format(self.svg.unittouu(str(self.options.stroke_width) + self.options.stroke_units))
                    if "stroke-opacity:" not in style:
                        style += 'stroke-opacity:{:1.1f};'.format(self.options.opacity / 100)

                    if self.options.apply_hairlines is True:
                        if "vector-effect:non-scaling-stroke" not in style:
                            style += 'vector-effect:non-scaling-stroke;'
                        if "-inkscape-stroke:hairline" not in style:
                            style += '-inkscape-stroke:hairline;'
                       
                    if re.search('fill:(.*?)(;|$)', style) is None: #if "fill" is None, add one.
                        style += 'fill:none;'
                                           
                    #then parse the content and check what we need to adjust   
                    declarations = style.split(';')
                    for i, decl in enumerate(declarations):
                        parts = decl.split(':', 2)
                        if len(parts) == 2:
                            (prop, val) = parts
                            prop = prop.strip().lower()
                            if prop == 'stroke-width':
                                new_val = self.svg.unittouu(str(self.options.stroke_width) + self.options.stroke_units)
                                declarations[i] = prop + ':{:1.4f}'.format(new_val)
                            if prop == 'stroke-opacity':
                                new_val = self.options.opacity / 100
                                declarations[i] = prop + ':{:1.1f}'.format(new_val)
                            if self.options.reset_style_attributes is True:
                                if prop == 'stroke-dasharray':
                                    declarations[i] = ''
                                if prop == 'stroke-dashoffset':
                                    declarations[i] = ''
                                if prop == 'stroke-linejoin':
                                    declarations[i] = ''
                                if prop == 'stroke-linecap':
                                    declarations[i] = ''
                                if prop == 'stroke-miterlimit':
                                    declarations[i] = ''
                            if self.options.apply_black_strokes is True:
                                if prop == 'stroke':
                                    if val == 'none':
                                        new_val = '#000000'
                                        declarations[i] = prop + ':' + new_val
                            if self.options.reset_fill_attributes is True:
                                if prop == 'fill':
                                        new_val = 'none'
                                        declarations[i] = prop + ':' + new_val
                    node.set('style', ';'.join(declarations))

if __name__ == '__main__':
    Cleanup().run()