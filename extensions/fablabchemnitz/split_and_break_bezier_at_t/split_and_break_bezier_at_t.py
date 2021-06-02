#!/usr/bin/env python3

import copy
import inkex
from inkex import bezier, CubicSuperPath, PathElement, Path
from inkex.bezier import csplength

class SplitAndBreakBezierAtT(inkex.EffectExtension):

    def breakContours(self, element, breakelements = None):
        ''' this does the same as "CTRL + SHIFT + K" '''
        if breakelements == None:
            breakelements = []
        if element.tag == inkex.addNS('path','svg'):
            parent = element.getparent()
            idx = parent.index(element)
            idSuffix = 0    
            raw = element.path.to_arrays()
            subPaths, prev = [], 0
            for i in range(len(raw)): #breaks compound paths into sub paths
                if raw[i][0] == 'M' and i != 0:
                    subPaths.append(raw[prev:i])
                    prev = i
            subPaths.append(raw[prev:])
            for subpath in subPaths:
                replacedelement = copy.copy(element)
                oldId = replacedelement.get('id')
                csp = CubicSuperPath(subpath)
                if len(subpath) > 1 and csp[0][0] != csp[0][1]: #avoids pointy paths like M "31.4794 57.6024 Z"
                    replacedelement.set('d', csp)
                    replacedelement.set('id', oldId + str(idSuffix))
                    parent.insert(idx, replacedelement)
                    idSuffix += 1
                    breakelements.append(replacedelement)
            parent.remove(element)
        for child in element.getchildren():
            self.breakContours(child, breakelements)
        return breakelements

    def add_arguments(self, pars):
        pars.add_argument('--split_select', default="t")
        pars.add_argument('--unit', default="mm")
        pars.add_argument('--target_length', type=float, default=0.5)
        pars.add_argument('--target_t', type=float, default=0.5)

    def effect(self):   
        breakApartElements = None
        for element in self.svg.selection.filter(PathElement):
            breakApartElements = self.breakContours(element, breakApartElements)

        if breakApartElements is not None:
            for element in breakApartElements:
                csp = element.path.to_superpath()
                slengths, totalLength = csplength(csp)
                if totalLength == 0:
                    inkex.utils.debug("{} is invalid: zero length (path d='{}'). Skipping ...".format(element.get('id'), element.path))
                    continue
                if self.options.split_select == "t":
                    length_at_target_t = self.options.target_t * totalLength
                elif self.options.split_select == "length":
                    length_at_target_t = self.svg.unittouu(str(self.options.target_length) + self.options.unit)
                    if length_at_target_t > totalLength:
                        inkex.utils.debug("Entered length is larger than length of {}. Skipping ...".format(element.get('id')))
                        continue
                    self.options.target_t = length_at_target_t / totalLength #override

                new = []
                lengthSum = 0
                segOfTOccurence = None   
                for seg in csp:        
                    new.append([seg[0][:]])      
                    for i in range(1,len(seg)):
                        segLength = bezier.cspseglength(new[-1][-1], seg[i])
                        lengthSum += segLength
                        current_t = lengthSum / totalLength
                        #insert a new breaking node in case we are at the desired t parameter
                        if current_t >= self.options.target_t:
                            if segOfTOccurence is None:
                                segOfTOccurence = i
                                t_dist = 1 - ((lengthSum - length_at_target_t) / segLength)
                                result = bezier.cspbezsplitatlength(new[-1][-1], seg[i], t_dist)
                                better_result = [[list(el) for el in elements] for elements in result]
                                new[-1][-1], nxt, seg[i] = better_result
                                new[-1].append(nxt[:])
                        new[-1].append(seg[i])                
                newpath = CubicSuperPath(new).to_path(curves_only=True).to_arrays()
                #insert the splitting at the occurence (we add "m 0,0") to break the path
                newpath.insert(segOfTOccurence + 1, ['m', [0, 0]])
                element.path = Path(newpath)
                breakAparts = self.breakContours(element)
                
                #print the breaking point coordinate
                #for step, (x, y) in enumerate(breakAparts[1].path.end_points):
                #    self.msg("x={},y={}".format(x, y))
                #    break
        else:
            inkex.utils.debug("Selection seems to be empty!")
            return
if __name__ == '__main__':
    SplitAndBreakBezierAtT().run()