#!/usr/bin/env python3

"""
Extension for InkScape 1.0

Converts curves to polylines - a quick and dirty helper for a lot of elements. Basically the same functionality can be done with default UI featureset but with a lot more mouse clicks

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 05.09.2020
Last patch: 05.09.2020
License: GNU GPL v3
"""

import inkex
from inkex.paths import Path

class ConvertToPolylines(inkex.Effect):

    def __init__(self):
        inkex.Effect.__init__(self)

    def convertPath(self, node):
        if node.tag == inkex.addNS('path','svg'):
            polypath = []
            i = 0
            for x, y in node.path.end_points:
                if i == 0:
                    polypath.append(['M', [x,y]])
                else:
                    polypath.append(['L', [x,y]])
                i += 1
                node.set('d', str(Path(polypath)))
        children = node.getchildren()
        if children is not None: 
            for child in children:
                self.convertPath(child) 
 
    def effect(self):
        if len(self.svg.selected) == 0:
             self.convertPath(self.document.getroot())
        else:
            for id, item in self.svg.selected.items():
                self.convertPath(item)
      
if __name__ == '__main__':
    ConvertToPolylines().run()