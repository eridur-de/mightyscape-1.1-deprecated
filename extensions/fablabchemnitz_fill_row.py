#!/usr/bin/env python3

import sys
from inkex import Effect as InkscapeEffect
from inkex import etree, addNS
from copy import deepcopy
from inkex.paths import Path
from inkex.transforms import Transform
from lxml import etree

class FillRow(InkscapeEffect):
    def __init__(self):
        InkscapeEffect.__init__(self)
        self.arg_parser.add_argument("--gap_x", type=int, default="10")
        self.arg_parser.add_argument("--gap_y",type=int, default="10")
		
    def effect(self):
        if len(self.svg.selected) > 0:
            self.total_height = 0
            for id, node in self.svg.selected.items():
                self.fill_row(node)

    def fill_row(self, node):
        #max_line_width = self.svg.unittouu('450mm')
        #x_start = self.svg.unittouu('3mm')
        #y_start = self.svg.unittouu('1600mm') - self.svg.unittouu('3mm')
        #gap_x = gap_y = self.svg.unittouu('10mm')
		
        svg = self.document.getroot()
        x_start  = 0
        y_start  = self.svg.unittouu(svg.attrib['height'])
        max_line_width = self.svg.unittouu(svg.get('width'))
	
        total_width = 0
        total_height = self.total_height

        group = etree.SubElement(self.svg.get_current_layer(), addNS('g','svg'))

        bbox = node.bounding_box()
        x = bbox.left
        y = bbox.top
        node_width = self.options.gap_x + bbox.width

        while total_width + node_width < max_line_width:
            node_copy = deepcopy(node)
            group.append(node_copy)

            x_dest = x_start + total_width
            y_dest = y_start - (total_height + bbox.height)

            # translation logic
            if node_copy.tag == addNS('path','svg'):
                x_delta = x_dest - x
                y_delta = y_dest - y

                path = Path(node_copy.attrib['d'])
                path.translate(x_delta, y_delta, True)
                node_copy.attrib['d'] = str(Path(path))
            elif node_copy.tag == addNS('g','svg'):
                x_delta = x_dest - x
                y_delta = y_dest - y

                translation_matrix = [[1.0, 0.0, x_delta], [0.0, 1.0, y_delta]]
                Transform(translation_matrix) * node_copy.transform 
            else:
                node_copy.attrib['x'] = str(x_dest)
                node_copy.attrib['y'] = str(y_dest)

            total_width += node_width

        self.total_height += group.bounding_box().height + self.options.gap_y

FillRow().run()