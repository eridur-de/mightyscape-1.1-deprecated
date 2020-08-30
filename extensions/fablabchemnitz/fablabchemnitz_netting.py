#!/usr/bin/env python3
'''
netting.py
Sunabe kazumichi 2010/3/4
http://dp48069596.lolipop.jp/


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

this program nets in the line.
'''
import random
import math
import inkex
import cubicsuperpath
from lxml import etree
from inkex.paths import Path, CubicSuperPath

class RadiusRandomize(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--s_width", type=float, default=1.0, help="stroke width")
        self.arg_parser.add_argument("--title")

    def effect(self):
        path_strings = []
        net_strings= ["M"]
        my_path = etree.Element(inkex.addNS('path','svg'))
        s = {'stroke-width': self.options.s_width, 'stroke': '#000000', 'fill': 'none' }
        my_path.set('style', str(inkex.Style(s)))
        for id, node in self.svg.selected.items():
            if node.tag == inkex.addNS('path','svg'):
                d = node.get('d')
                p = CubicSuperPath(Path(d))
                for subpath in p:
                    for i, csp in enumerate(subpath):
                        path_strings.append("%f,%f" % ( csp[1][0], csp[1][1]))
                node.set('d',str(Path(p)))
                
                while len(path_strings)>0 :
                    net_strings.append(path_strings.pop(0))
                    if len(path_strings)>0 :
                        net_strings.append(path_strings.pop())
                my_path.set('d', " ".join(net_strings))
                self.svg.get_current_layer().append( my_path )
                    
RadiusRandomize().run()