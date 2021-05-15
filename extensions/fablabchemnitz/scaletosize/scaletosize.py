#!/usr/bin/env python3

# Author: Mario Voigt / FabLab Chemnitz
# Mail: mario.voigt@stadtfabrikanten.org
# Date: 04.08.2020
# License: GNU GPL v3

import inkex
from inkex.paths import CubicSuperPath, Path
from inkex import Transform
from lxml import etree
from inkex.styles import Style

# This extension can scale any object or path on X, Y or both axes. This addon is kind of obsolete because you can do the same from transforms menu

class ScaleToSize(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--unit')
        pars.add_argument("--expected_size", type=float, default=1.0, help="The expected size of the object")
        pars.add_argument("--scale_type", default="Horizontal", help="Scale type (Uniform, Horizontal, Vertical)")
        pars.add_argument("--description")

    def effect(self):
        unit_factor = 1.0 / self.svg.uutounit(1.0,self.options.unit)
        for id, node in self.svg.selected.items():
		
            #get recent XY coordinates (top left corner of the bounding box)
            bbox = node.bounding_box()
            new_horiz_scale = self.options.expected_size * unit_factor / bbox.width
            new_vert_scale = self.options.expected_size * unit_factor / bbox.height
			
            if self.options.scale_type == "Horizontal":
                translation_matrix = [[new_horiz_scale, 0.0, 0.0], [0.0, 1.0, 0.0]]
            elif self.options.scale_type == "Vertical":
                translation_matrix = [[1.0, 0.0, 0.0], [0.0, new_vert_scale, 0.0]]
            else: #Uniform
                translation_matrix = [[new_horiz_scale, 0.0, 0.0], [0.0, new_vert_scale, 0.0]]			
            node.transform = Transform(translation_matrix) * node.transform
			
            # now that the node moved we need to get the nodes XY coordinates again to fix them
            bbox_new = node.bounding_box()

            #inkex.utils.debug(cx)
            #inkex.utils.debug(cy)
            #inkex.utils.debug(cx_new)
            #inkex.utils.debug(cy_new)
		
            # We remove the transformation attribute from SVG XML tree in case it's regular path. In case the node is an object like arc,circle, ellipse or star we have the attribute "sodipodi:type". Then we do not play with it's path because the size transformation will not apply (this code block is ugly)
            if node.get ('sodipodi:type') is None and 'd' in node.attrib:
                #inkex.utils.debug("it's a path!")
                d = node.get('d')
                p = CubicSuperPath(d)
                transf = Transform(node.get("transform", None))
                if 'transform' in node.attrib:
                    del node.attrib['transform']
                p = Path(p).to_absolute().transform(transf, True)
                node.set('d', Path(CubicSuperPath(p).to_path()))
            #else:
                #inkex.utils.debug("it's an object!")
		
            #we perform second translation to reset the center of the path				
            translation_matrix = [[1.0, 0.0, bbox.left - bbox_new.left + (bbox.width - bbox_new.width)/2], [0.0, 1.0, bbox.top - bbox_new.top + (bbox.height - bbox_new.height)/2]]			
            node.transform = Transform(translation_matrix) * node.transform	
		
if __name__ == '__main__':
    ScaleToSize().run()