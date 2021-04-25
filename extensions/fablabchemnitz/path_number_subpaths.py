#!/usr/bin/env python3
#
# Copyright (C) 2005 Aaron Spike, aaron@ekips.org
# Modified by Ellen Wasbo, ellen@wasbo.net 2021 - number subpaths and mark start/end node with green/red dot
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
import math
import inkex
from inkex import TextElement, Circle

class NumberSubpaths(inkex.EffectExtension):
    """Mark start and end nodes with numbered dots according to the options"""
    def add_arguments(self, pars):
        pars.add_argument("--dotsize", default="10px", help="Size of the dots on the path nodes")
        pars.add_argument("--fontsize", default="10px", help="Size of node labels")
        pars.add_argument("--showID", type=inkex.Boolean, default=False)
        pars.add_argument("--tab", help="The selected UI-tab when OK was pressed")

    def effect(self):
        if not self.svg.selected:
            raise inkex.AbortExtension("Please select an object.")
        for id, node in self.svg.selection.id_dict().items():
            self.add_dot(node)

    def add_dot(self, node):
        """Add a dot label for this path element"""
        group = node.getparent().add(inkex.Group())
        dot_group = group.add(inkex.Group())
        num_group = group.add(inkex.Group())
        group.transform = node.transform
        
        styleStart = inkex.Style({'stroke': 'none', 'fill': '#00ff00'})
        styleEnd = inkex.Style({'stroke': 'none', 'fill': '#ff0000'})
        
        idTxt=''
        if self.options.showID==True:
            idTxt=node.get('id')+', '
                
        cc=0
        for sub in node.path.to_superpath():
            x=sub[0][1][0]
            y=sub[0][1][1]
            circle = dot_group.add(Circle(cx=str(x), cy=str(y), r=str(self.svg.unittouu(self.options.dotsize) / 2)))
            circle.style = styleStart
            num_group.append(self.add_text(
                x + (self.svg.unittouu(self.options.dotsize) / 3),
                y - (self.svg.unittouu(self.options.dotsize) / 3), idTxt+str(cc)))
            x=sub[-1][1][0]
            y=sub[-1][1][1]
            circle = dot_group.add(Circle(cx=str(x), cy=str(y), r=str(self.svg.unittouu(self.options.dotsize) *0.9 / 2)))
            circle.style = styleEnd
            num_group.append(self.add_text(
                x + (self.svg.unittouu(self.options.dotsize) / 3),
                y - (self.svg.unittouu(self.options.dotsize) / 3), idTxt+str(cc)))
            cc+=1

    def add_text(self, x, y, text):
        """Add a text label at the given location"""
        elem = TextElement(x=str(x), y=str(y))
        elem.text = str(text)
        elem.style = {
            'font-size': self.svg.unittouu(self.options.fontsize),
            'fill-opacity': '1.0',
            'stroke': 'none',
            'font-weight': 'normal',
            'font-style': 'normal',
            'fill': '#999'}
        return elem

if __name__ == '__main__':
    NumberSubpaths().run()
