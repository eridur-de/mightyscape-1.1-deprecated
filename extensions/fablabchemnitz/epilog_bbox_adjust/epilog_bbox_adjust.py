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
Last patch: 23.05.2021
License: GNU GPL v3

#known bugs:
- viewbox/width/height do not correctly apply if documents only contain an object (not a path). After converting it to path it works. Seems to be a bbox problem
- note from 07.05.2021: seems if the following order is viewBox/width/height, or width/height/viewBox, the units are not respected. So me mess around a little bit
'''

import math
import inkex
from inkex import Transform

class BBoxAdjust(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--offset", type=float, default="1.0", help="XY Offset (mm) from top left corner")
        pars.add_argument("--use_machine_size", type=inkex.Boolean, default=False, help="Use machine size")
        pars.add_argument("--machine_size", default="812x508", help="Machine/Size")

    def effect(self):
        offset = self.options.offset
        #units = self.svg.unit
        units = "mm" #force millimeters

        # create a new bounding box and get the bbox size of all elements of the document (we cannot use the page's bbox)
        bbox = inkex.BoundingBox()
        for element in self.svg.root.getchildren():
            if isinstance (element, inkex.ShapeElement):
                bbox += element.bounding_box()

        if abs(bbox.width) == math.inf or abs(bbox.height) == math.inf:
            inkex.utils.debug("Error calculating bounding box!")
            return

    # adjust the viewBox to the bbox size and add the desired offset
        if self.options.use_machine_size is True:
            machineHeight = float(self.options.machine_size.split('x')[0])
            machineWidth = float(self.options.machine_size.split('x')[1])
            self.document.getroot().attrib['width'] = f'{machineHeight}' + units
            self.document.getroot().attrib['viewBox'] = f'{-offset} {-offset} {machineHeight} {machineWidth}'     
            self.document.getroot().attrib['height'] = f'{machineWidth}' + units
        else:
            self.document.getroot().attrib['width'] = f'{bbox.width + offset * 2}' + units
            self.document.getroot().attrib['viewBox'] = f'{-offset} {-offset} {bbox.width + offset * 2} {bbox.height + offset * 2}'
            self.document.getroot().attrib['height'] = f'{bbox.height + offset * 2}' + units
        # translate all elements to fit the adjusted viewBox
        mat = Transform("translate(%f, %f)" % (-bbox.left,-bbox.top)).matrix
        for element in self.svg.root.getchildren():
            if isinstance (element, inkex.ShapeElement):
                element.transform = Transform(mat) * element.transform

if __name__ == '__main__':
    BBoxAdjust().run()