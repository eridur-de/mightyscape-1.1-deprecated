#!/usr/bin/env python3

import inkex
from lxml import etree

class DrawBBoxes(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)

    def effect(self):
        if len(self.svg.selected) > 0:
            bboxes = [(id, node, node.bounding_box()) for id, node in self.svg.selected.items()]
            for id, node, bbox in bboxes:
                attribs = {
                    'style'     : str(inkex.Style({'stroke':'#ff0000','stroke-width'  : '1','fill':'none'})),
                    'x'         : str(bbox.left),
                    'y'         : str(bbox.top),
                    'width'     : str(bbox.width),
                    'height'    : str(bbox.height),
                }
                etree.SubElement(self.svg.get_current_layer(), inkex.addNS('rect','svg'), attribs )

DrawBBoxes().run()