#!/usr/bin/env python3

import inkex
import svgpathtools

def isclosedac(p):
    return abs(p.start-p.end) < 1e-6


class SmallThingsFilter(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--unit')
        pars.add_argument('--threshold', type=float, help='Remove paths with an threshold smaller than this value')
        pars.add_argument('--measure', default="length")
		
    def effect(self):
        self.options.threshold = self.svg.unittouu(str(self.options.threshold) + self.svg.unit)
        unit_factor = 1.0 / self.svg.uutounit(1.0,self.options.unit)
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
    SmallThingsFilter().run()