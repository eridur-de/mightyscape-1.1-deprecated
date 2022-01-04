#!/usr/bin/env python3

import inkex
from inkex import Transform
from lxml import etree

class NormalizeDrawingScale(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--remove_viewbox', type=inkex.Boolean, default=True)
    
    def effect(self):
        namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
        doc_units = namedView.get(inkex.addNS('document-units', 'inkscape'))        
        docScale = self.svg.scale
        docWidth = self.svg.uutounit(self.svg.width, doc_units)
        docHeight = self.svg.uutounit(self.svg.height, doc_units)
        vxMin, vyMin, vxMax, vyMax = self.svg.get_viewbox()
        vxTotal = vxMax - vxMin
        vScaleX = self.svg.unittouu(str(vxTotal / self.svg.width) + doc_units)
        if round(vScaleX, 5) != 1.0 or self.options.remove_viewbox is True:
            
            #set scale to 100% (we adjust viewBox)
            if self.options.remove_viewbox is False:
                self.svg.set('viewBox', '0 0 {} {}'.format(docWidth, docHeight))
            else:
                self.svg.pop('viewBox')
                self.document.getroot().set('inkscape:document-units', 'px')
                self.svg.set('width', docWidth)
                self.svg.set('height', docHeight)

                namedView.attrib[inkex.addNS('document-units', 'inkscape')] = 'px'
            translation_matrix = [[1/vScaleX, 0.0, 0.0], [0.0, 1/vScaleX, 0.0]]

            #select each top layer and apply the transformation to scale
            processed = []
            for element in self.document.getroot().iter(tag=etree.Element):
                if element != self.document.getroot():
                    if element.tag == inkex.addNS('g','svg'):
                        parent = element.getparent()
                        if parent.get('inkscape:groupmode') != 'layer' and element.get('inkscape:groupmode') == 'layer':
                            element.transform = Transform(translation_matrix) * element.composed_transform()
                            processed.append(element)

            #do the same for all elements which lay on first level and which are not a layer
            for element in self.document.getroot().getchildren():
                if isinstance(element, inkex.ShapeElement) and element not in processed:
                    element.transform = Transform(translation_matrix) * element.composed_transform()

        else:
            inkex.utils.debug("Nothing to do. Scale is already 100%")
   
                             
if __name__ == '__main__':
    NormalizeDrawingScale().run()