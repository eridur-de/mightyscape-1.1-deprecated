#!/usr/bin/env python3

import inkex
import svgpathtools

def isclosedac(p):
    return abs(p.start-p.end) < 1e-6


class Sieve(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument('--unit')
        self.arg_parser.add_argument('--threshold', type=float, help='Remove paths with an threshold smaller than this value')
        self.arg_parser.add_argument('--measure', default="length")
		
    def effect(self):
        namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
        doc_units = namedView.get(inkex.addNS('document-units', 'inkscape'))
        #inkex.utils.debug("document unit is " + doc_units)
        self.options.threshold = self.svg.unittouu(str(self.options.threshold) + doc_units)
        unit_factor = 1.0 / self.svg.uutounit(1.0,self.options.unit)
        #inkex.utils.debug("unit_factor is " + str(unit_factor))
		
        if self.options.threshold == 0:
            return

        for path in self.document.xpath("//svg:path", namespaces=inkex.NSS):
            try:
                parsed_path = svgpathtools.parse_path(path.attrib["d"])
                
                #if not isclosedac(parsed_path):
                #    continue
                
                if self.options.measure == "area":      
                    calc = parsed_path.area()
                    #inkex.utils.debug(calc) #print calculated area with document units
                    #inkex.utils.debug(str(self.options.threshold * (unit_factor * unit_factor))) #print threshold area with selected units
                    if calc < (self.options.threshold * (unit_factor * unit_factor)):
                        path.getparent().remove(path)
                else: #length
                    calc = parsed_path.length()
                    #inkex.utils.debug(calc) #print calculated area with document units
                    #inkex.utils.debug(str(self.options.threshold * (unit_factor * unit_factor))) #print threshold area with selected units
                    if calc < (self.options.threshold * unit_factor):
                        path.getparent().remove(path)
            except:
                pass

if __name__ == '__main__':
    Sieve().run()