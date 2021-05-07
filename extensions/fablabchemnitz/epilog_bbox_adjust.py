#!/usr/bin/env python3

'''
Extension for InkScape 1.0
Features
- This tool is a helper to adjust the document border including an offset value, which is added. 
Sending vector data to Epilog Dashboard often results in trimmed paths. This leads to wrong geometry where the laser misses to cut them.
So we add a default (small) amount of 1.0 doc units to expand the document's canvas

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 21.04.2021
Last patch: 21.04.2021
License: GNU GPL v3
'''

import inkex
from inkex import Transform

class BBoxAdjust(inkex.EffectExtension):

    def effect(self):
        offset = 1.0 #in documents' units

        # create a new bounding box and get the bbox size of all elements of the document (we cannot use the page's bbox)
        bbox = inkex.BoundingBox()
        for element in self.svg.root.getchildren():
            if isinstance (element, inkex.ShapeElement):
                bbox += element.bounding_box()

        # adjust the viewBox to the bbox size and add the desired offset
        # note from 07.05.2021: seems if the following order is viewBox/width/height, or width/height/viewBox, the units are not respected. So me mess around a little bit
        self.document.getroot().attrib['width'] = f'{bbox.width + offset * 2}' + self.svg.unit
        self.document.getroot().attrib['viewBox'] = f'{-offset} {-offset} {bbox.width + offset * 2} {bbox.height + offset * 2}'
        self.document.getroot().attrib['height'] = f'{bbox.height + offset * 2}' + self.svg.unit

        # translate all elements to fit the adjusted viewBox
        mat = Transform("translate(%f, %f)" % (-bbox.left,-bbox.top)).matrix
        for element in self.svg.root.getchildren():
            if isinstance (element, inkex.ShapeElement):
                element.transform = Transform(mat) * element.transform

if __name__ == '__main__':
    BBoxAdjust().run()