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
            for i in range(len(raw)): # Breaks compound paths into simple paths
                if raw[i][0] == 'M' and i != 0:
                    subPaths.append(raw[prev:i])
                    prev = i
            subPaths.append(raw[prev:])
            for subpath in subPaths:
                replacedelement = copy.copy(element)
                oldId = replacedelement.get('id')
                replacedelement.set('d', CubicSuperPath(subpath))
                replacedelement.set('id', oldId + str(idSuffix).zfill(5))
                parent.insert(idx, replacedelement)
                idSuffix += 1
                breakelements.append(replacedelement)
            parent.remove(element)
        for child in element.getchildren():
            self.breakContours(child, breakelements)
        return breakelements

    def add_arguments(self, pars):
        pars.add_argument('--target_t', type=float, default=0.5)

    def effect(self):   
        breakApartElements = None
        for element in self.svg.selection.filter(PathElement):
            breakApartElements = self.breakContours(element, breakApartElements)
        for element in breakApartElements:
            csp = element.path.to_superpath()
            slengths, totalLength = csplength(csp)
            length_at_target_t = self.options.target_t * totalLength
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
            breakApartElements = self.breakContours(element)
            
            #print the breaking point coordinate
            #for step, (x, y) in enumerate(breakApartElements[1].path.end_points):
            #    self.msg("x={},y={}".format(x, y))
            #    break
if __name__ == '__main__':
    SplitAndBreakBezierAtT().run()