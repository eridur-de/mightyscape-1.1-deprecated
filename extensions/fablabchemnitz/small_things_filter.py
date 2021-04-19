#!/usr/bin/env python3

import inkex
from inkex.bezier import csplength, csparea

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

        for element in self.document.xpath("//svg:path", namespaces=inkex.NSS):
            try:
                csp = element.path.transform(element.composed_transform()).to_superpath()

                if self.options.measure == "area":
                    area = -csparea(csp) #is returned as negative value. we need to invert with -
                    if area < (self.options.threshold * (unit_factor * unit_factor)):
                        element.delete()
                        
                elif self.options.measure == "length":
                    slengths, stotal = csplength(csp) #get segment lengths and total length of path in document's internal unit
                    if stotal < (self.options.threshold * unit_factor):
                        element.delete()
            except Exception as e:
                pass

if __name__ == '__main__':
    SmallThingsFilter().run()