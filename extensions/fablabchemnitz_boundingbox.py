#!/usr/bin/env python3

import inkex
from lxml import etree

class DrawBBoxes(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument('--offset', type=float, default=0.0, help='Offset from object (all directions)')

    def effect(self):
        if len(self.svg.selected) > 0:
            bboxes = [(id, node, node.bounding_box()) for id, node in self.svg.selected.items()]
            for id, node, bbox in bboxes:
                attribs = {
                    'style'     : str(inkex.Style({'stroke':'#ff0000','stroke-width'  : '1','fill':'none'})),
                    'x'         : str(bbox.left - self.options.offset),
                    'y'         : str(bbox.top - self.options.offset),
                    'width'     : str(bbox.width + 2 * self.options.offset),
                    'height'    : str(bbox.height + 2 * self.options.offset),
                }
                etree.SubElement(self.svg.get_current_layer(), inkex.addNS('rect','svg'), attribs )

DrawBBoxes().run()