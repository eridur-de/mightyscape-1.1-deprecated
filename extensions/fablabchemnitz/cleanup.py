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

class Cleanup(inkex.EffectExtension):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--stroke_width", type=float, default=0.1, help="Stroke width")
        self.arg_parser.add_argument("--stroke_units", default="mm", help="Stroke unit")
        self.arg_parser.add_argument("--remove_styles", type=inkex.Boolean, help="Remove stroke styles")
        self.arg_parser.add_argument("--opacity", type=float, default="100.0", help="Opacity")

    def effect(self):
        if len(self.svg.selected)==0:
            self.getAttribs(self.document.getroot())
        else:
            for id,node in self.svg.selected.items():
                self.getAttribs(node)

    def getAttribs(self,node):
        self.changeStyle(node)
        for child in node:
            self.getAttribs(child)

    def changeStyle(self,node):
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
                            new_val = self.svg.unittouu(str(self.options.stroke_width)+self.options.stroke_units)
                            declarations[i] = prop + ':' + str(new_val)
                        if prop == 'stroke-opacity':
                            new_val = str(self.options.opacity / 100)
                            declarations[i] = prop + ':' + new_val
                        if self.options.remove_styles == True:
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
                node.set('style', ';'.join(declarations))

if __name__ == '__main__':
    Cleanup().run()