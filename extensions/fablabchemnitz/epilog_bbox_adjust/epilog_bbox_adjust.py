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
Last patch: 27.05.2021
License: GNU GPL v3

#known bugs:
- viewbox/width/height do not correctly apply if documents only contain an object (not a path). After converting it to path it works. Seems to be a bbox problem
- note from 07.05.2021: seems if the following order is viewBox/width/height, or width/height/viewBox, the units are not respected. So me mess around a little bit

#Todo
- add some way to handle translations properly

'''

import math
import inkex
from inkex import Transform

class BBoxAdjust(inkex.EffectExtension):

    def getElementChildren(self, element, elements = None):
        if elements == None:
            elements = []
        if element.tag != inkex.addNS('g','svg'):
                elements.append(element)
        for child in element.getchildren():
            self.getElementChildren(child, elements)
        return elements

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--offset", type=float, default="1.0", help="XY Offset (mm) from top left corner")
        pars.add_argument("--removal", default="none", help="Remove all elements outside the bounding box or selection")
        pars.add_argument("--use_machine_size", type=inkex.Boolean, default=False, help="Use machine size")
        pars.add_argument("--machine_size", default="812x508", help="Machine/Size")
        pars.add_argument("--debug", type=inkex.Boolean, default=False, help="Debug output")

    def effect(self):
        offset = self.options.offset
        #units = self.svg.unit
        units = "mm" #force millimeters

        # create a new bounding box and get the bbox size of all elements of the document (we cannot use the page's bbox)
        bbox = inkex.BoundingBox()
        if len(self.svg.selected) > 0:
            bbox = self.svg.selection.bounding_box()
            #for element in self.svg.selected.values():
            #    bbox += element.bounding_box()
        else:
            #for element in self.svg.root.getchildren():
            for element in self.document.getroot().iter("*"):
                if isinstance (element, inkex.ShapeElement):
                    bbox += element.bounding_box()

        if abs(bbox.width) == math.inf or abs(bbox.height) == math.inf:
            inkex.utils.debug("Error calculating bounding box! Impossible to continue!")
            return

    # adjust the viewBox to the bbox size and add the desired offset
        if self.options.use_machine_size is True:
            machineWidth = float(self.options.machine_size.split('x')[0])
            machineHeight = float(self.options.machine_size.split('x')[1])
            width = f'{machineWidth}' + units
            height = f'{machineHeight}' + units
            viewBoxXmin = -offset
            viewBoxYmin = -offset
            viewBoxXmax = machineWidth
            viewBoxYmax = machineHeight
        else:
            width = f'{bbox.width + offset * 2}' + units
            height = f'{bbox.height + offset * 2}' + units
            viewBoxXmin = -offset
            viewBoxYmin = -offset
            viewBoxXmax = bbox.width + offset * 2
            viewBoxYmax = bbox.height + offset * 2
        self.document.getroot().attrib['width'] = width
        self.document.getroot().attrib['viewBox'] = f'{viewBoxXmin} {viewBoxYmin} {viewBoxXmax} {viewBoxYmax}'
        self.document.getroot().attrib['height'] = height
        
        # translate all elements to fit the adjusted viewBox
        mat = Transform("translate(%f, %f)" % (-bbox.left,-bbox.top))
        for element in self.document.getroot().iter("*"):
            if isinstance (element, inkex.ShapeElement) and element.tag != inkex.addNS('g', 'svg'):
                element.transform = Transform(mat) * element.transform
                #element.transform = Transform(element.composed_transform().add_matrix(mat)) * element.transform

        if self.options.removal == "outside_canvas":
            for element in self.document.getroot().iter("*"):
                if isinstance (element, inkex.ShapeElement) and element.tag != inkex.addNS('g', 'svg'):
                    ebbox = element.bounding_box()
                    #self.msg("{} | bbox: left = {:0.3f} right = {:0.3f} top = {:0.3f} bottom = {:0.3f}".format(element.get('id'), ebbox.left, ebbox.right, ebbox.top, ebbox.bottom))
                    #check if the element's bbox is inside the view canvas. If not: delete it!
                    if ebbox.right  < viewBoxXmin or \
                       ebbox.left   > viewBoxXmax or \
                       ebbox.top    < viewBoxYmin or \
                       ebbox.bottom > viewBoxYmax:
                        if self.options.debug is True:
                            self.msg("Removing {} {}".format(element.get('id'), ebbox))
                        element.delete()

        elif self.options.removal == "outside_selection":
            if len(self.svg.selected) == 0:
                inkex.utils.debug("Your selection is empty but you have chosen the option to remove all elements outside selection!")
                return
            
            allElements = []
            for selected in self.svg.selection:
                allElements = self.getElementChildren(selected, allElements)
            
            for element in self.document.getroot().iter("*"):
                if element not in allElements and isinstance (element, inkex.ShapeElement) and element.tag != inkex.addNS('g', 'svg'):
                    if self.options.debug is True:
                        self.msg("Removing {}".format(element.get('id')))
                    element.delete()

if __name__ == '__main__':
    BBoxAdjust().run()