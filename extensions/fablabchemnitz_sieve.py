#!/usr/bin/env python3

import inkex
import svgpathtools

def isclosedac(p):
    return abs(p.start-p.end) < 1e-6


class Sieve(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument('--unit')
        self.arg_parser.add_argument('--area', type=float, help='Remove paths with an area smaller than this value')
		
    def effect(self):
        namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
        doc_units = namedView.get(inkex.addNS('document-units', 'inkscape'))
        #inkex.utils.debug("document unit is " + doc_units)
        self.options.area = self.svg.unittouu(str(self.options.area) + doc_units)
        unit_factor = 1.0 / self.svg.uutounit(1.0,self.options.unit)
        #inkex.utils.debug("unit_factor is " + str(unit_factor))
		
        if self.options.area == 0:
            return

        for path in self.document.xpath("//svg:path", namespaces=inkex.NSS):
            try:
                parsed_path = svgpathtools.parse_path(path.attrib["d"])
                
                if not isclosedac(parsed_path):
                    continue
                
                area = parsed_path.area()
                #inkex.utils.debug(area) #print calculated area with document units
                #inkex.utils.debug(str(self.options.area * (unit_factor * unit_factor))) #print threshold area with selected units
                if area < (self.options.area * (unit_factor * unit_factor)):
                    path.getparent().remove(path)
            except:
                pass

if __name__ == '__main__':
    Sieve().run()