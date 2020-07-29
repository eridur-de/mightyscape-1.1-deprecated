#!/usr/bin/env python3
import sys
import math
import inkex
import simpletransform
from lxml import etree

class clonesPerspectiveEffect(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument('--num', type = int, default = 5, help = 'Drag out center of rotation before calling')
        self.arg_parser.add_argument('--ratio', type = float, default = 0.9, help = 'Ratio of size of nearest neighbor to first.  Must be < 1')

    def effect(self):
        svg = self.document.getroot()
        num = int( self.options.num )
        ratio = float( self.options.ratio)

        if 1 != len(self.svg.selected) :
            inkex.errormsg("Select exactly 1 thing. Group if necessary")
            sys.exit(1)
        id = self.svg.selected[0].get('id')
        sel = self.svg.selected[id]
        dic = sel.attrib
	
        try :
            tx = dic[inkex.addNS('transform-center-x','inkscape') ]
        except KeyError :
            tx = '0.'
        try :
            ty = dic[inkex.addNS('transform-center-y','inkscape') ]
        except KeyError : 
            ty = '0.'

        if float(tx) == 0. and float(ty) == 0. :
            inkex.errormsg("Center of rotation at center of object")
            sys.exit(1)
  
        for node in sel:
            width =  node.bounding_box().right - node.bounding_box().left
            height = node.bounding_box().bottom - node.bounding_box().top
            cx = float(node.bounding_box().left) + 0.5 * width  #Find center of selected object
            cy = float(node.bounding_box().top) + 0.5 * height #Find center of selected object

        tx = float(tx)
        ty = float(ty)
        crat = 1.0
        otx = tx
        oty = ty

        parent = sel.getparent()
        j = parent.index(sel)
        for i in range(num) :
            crat *= ratio
            tx *= ratio
            ty *= ratio
            att = {
                "id" : self.svg.get_unique_id("clone" + id),
                inkex.addNS('href','xlink') : "#" + id,
                inkex.addNS('transform-center-x','inkscape') : str(tx),
                inkex.addNS('transform-center-y','inkscape') : str(ty),
#            "x" : "0",
#            "y" : "0",
                'transform' : ("matrix(%f,0,0,%f,%f,%f)" %
                               (crat, crat,(1. - crat)*(cx + otx),
                                (1. - crat)*(cy - oty))),
#WHY Inkscape and SVG run +y in OPPOSITE directions is BEYOND me.
                "width" :  "100%",
                "height" : "100%",
                }
            parent.insert(j, etree.Element('use', att) )

# Create effect instance and apply it.
clonesPerspectiveEffect().run()