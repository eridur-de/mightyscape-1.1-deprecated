#!/usr/bin/env python3

import inkex
import math
from lxml import etree

class DrawBBoxes(inkex.EffectExtension):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument('--offset', type=float, default=0.0, help='Offset from object (all directions)')
        self.arg_parser.add_argument('--box', type=inkex.Boolean, default=0.0, help='Draw boxes')
        self.arg_parser.add_argument('--circle', type=inkex.Boolean, default=0.0, help='Draw circles')
        self.arg_parser.add_argument('--split', type = inkex.Boolean, default = True, help = 'Handle selection as group')
      
    def drawBBox(self, bbox):
        if self.options.box:
            attribs = {
                'style' : str(inkex.Style({'stroke':'#ff0000','stroke-width'  : '1','fill':'none'})),
                'x'     : str(bbox.left - self.options.offset),
                'y'     : str(bbox.top - self.options.offset),
                'width' : str(bbox.width + 2 * self.options.offset),
                'height': str(bbox.height + 2 * self.options.offset),
            }
            etree.SubElement(self.svg.get_current_layer(), inkex.addNS('rect','svg'), attribs)
		    	
        if self.options.circle:			    	
            attribs = {
                'style': str(inkex.Style({'stroke':'#ff0000','stroke-width'  : '1','fill':'none'})),
                'cx'   : str(bbox.center_x),
                'cy'   : str(bbox.center_y),
                #'r'   : str(bbox.width / 2 + self.options.offset),
                'r'    : str(math.sqrt((bbox.width + 2 * self.options.offset)* (bbox.width + 2 * self.options.offset) + (bbox.height + 2 * self.options.offset) * (bbox.height + 2 * self.options.offset)) / 2),
            }
            etree.SubElement(self.svg.get_current_layer(), inkex.addNS('circle','svg'), attribs)
      
    def effect(self):
        if len(self.svg.selected) > 0:
            if self.options.split is False:
                for id, item in self.svg.selected.items():
                    self.drawBBox(item.bounding_box())
            else:
                inkex.utils.debug("")
                #self.drawBBox(self.svg.get_selected_bbox()) #works for InkScape (1:1.0+devel+202008292235+eff2292935) @ Linux and for Windows (but with deprecation)
                self.drawBBox(self.svg.selection.bounding_box()) #works for InkScape 1.1dev (9b1fc87, 2020-08-27)) @ Windows

        else:
            inkex.errormsg('Please select some objects first.')
            return

if __name__ == '__main__':
    DrawBBoxes().run()