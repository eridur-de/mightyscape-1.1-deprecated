#!/usr/bin/env python3

import inkex
import math
from lxml import etree

class DrawBBoxes(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument('--offset', type=float, default=0.0, help='Offset from object (all directions)')
        self.arg_parser.add_argument('--box', type=inkex.Boolean, default=0.0, help='Draw boxes')
        self.arg_parser.add_argument('--circle', type=inkex.Boolean, default=0.0, help='Draw circles')
		
    def effect(self):
        if len(self.svg.selected) > 0:
            bboxes = [(id, node, node.bounding_box()) for id, node in self.svg.selected.items()]
			
            if self.options.box:
                for id, node, bbox in bboxes:
                    attribs = {
                        'style' : str(inkex.Style({'stroke':'#ff0000','stroke-width'  : '1','fill':'none'})),
                        'x'     : str(bbox.left - self.options.offset),
                        'y'     : str(bbox.top - self.options.offset),
                        'width' : str(bbox.width + 2 * self.options.offset),
                        'height': str(bbox.height + 2 * self.options.offset),
                    }
                    etree.SubElement(self.svg.get_current_layer(), inkex.addNS('rect','svg'), attribs )
			    	
            if self.options.circle:			    	
                for id, node, bbox in bboxes:
                    attribs = {
                        'style': str(inkex.Style({'stroke':'#ff0000','stroke-width'  : '1','fill':'none'})),
                        'cx'   : str(bbox.center_x),
                        'cy'   : str(bbox.center_y),
                        #'r'   : str(bbox.width / 2 + self.options.offset),
                        'r'    : str(math.sqrt((bbox.width + 2 * self.options.offset)* (bbox.width + 2 * self.options.offset) + (bbox.height + 2 * self.options.offset) * (bbox.height + 2 * self.options.offset)) / 2),
                    }
                    etree.SubElement(self.svg.get_current_layer(), inkex.addNS('circle','svg'), attribs )
DrawBBoxes().run()