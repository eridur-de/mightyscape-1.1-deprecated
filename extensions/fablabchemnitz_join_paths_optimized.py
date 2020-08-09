#!/usr/bin/env python3

'''
Inkscape extension to join the selected paths. With the optimized option selected, 
the next path to be joined is the one, which has one of its end nodes closest to the ending
node of the earlier path.

Copyright (C) 2019  Shrinivas Kulkarni

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
'''

import inkex
from inkex.paths import CubicSuperPath
import copy

def floatCmpWithMargin(float1, float2, margin):
    return abs(float1 - float2) < margin 
    
def vectCmpWithMargin(vect1, vect2, margin):
    return all(floatCmpWithMargin(vect2[i], vect1[i], margin) for i in range(0, len(vect1)))

def getPartsFromCubicSuper(cspath):
    parts = []
    for subpath in cspath:
        part = []
        prevBezPt = None            
        for i, bezierPt in enumerate(subpath):
            if(prevBezPt != None):
                seg = [prevBezPt[1], prevBezPt[2], bezierPt[0], bezierPt[1]]
                part.append(seg)
            prevBezPt = bezierPt
        parts.append(part)
    return parts
        
def getCubicSuperFromParts(parts):
    cbsuper = []
    for part in parts:
        subpath = []
        lastPt = None
        pt = None
        for seg in part:
            if(pt == None):
                ptLeft = seg[0]
                pt = seg[0]
            ptRight = seg[1]
            subpath.append([ptLeft, pt, ptRight])
            ptLeft = seg[2]
            pt = seg[3]
        subpath.append([ptLeft, pt, pt])
        cbsuper.append(subpath)
    return cbsuper
    
def getArrangedIds(pathMap, startPathId):
    nextPathId = startPathId
    orderPathIds = [nextPathId]
    
    #Arrange in order
    while(len(orderPathIds) < len(pathMap)):
        minDist = 9e+100 #A large float
        closestId = None        
        np = pathMap[nextPathId]
        npPts = [np[-1][-1][-1]]
        if(len(orderPathIds) == 1):#compare both the ends for the first path
            npPts.append(np[0][0][0])
        
        for key in pathMap:
            if(key in orderPathIds):
                continue
            parts = pathMap[key] 
            start = parts[0][0][0]
            end = parts[-1][-1][-1]
            
            for i, npPt in enumerate(npPts):
                dist = abs(start[0] - npPt[0]) + abs(start[1] - npPt[1])
                if(dist < minDist):
                    minDist = dist
                    closestId = key
                dist = abs(end[0] - npPt[0]) + abs(end[1] - npPt[1])
                if(dist < minDist):
                    minDist = dist
                    pathMap[key] = [[[pts for pts in reversed(seg)] for seg in \
                        reversed(part)] for part in reversed(parts)]
                    closestId = key
                    
                #If start point of the first path is closer reverse its direction    
                if(i > 0 and closestId == key):
                    pathMap[nextPathId] = [[[pts for pts in reversed(seg)] for seg in \
                        reversed(part)] for part in reversed(np)]
                    
        orderPathIds.append(closestId)
        nextPathId = closestId
    return orderPathIds
    
class JoinPathsOptimEffect(inkex.Effect):

    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--optimized", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--tab", default="sampling", help="Tab") 
          
    def effect(self):
        selections = self.svg.selected        
        pathNodes = self.document.xpath('//svg:path',namespaces=inkex.NSS)

        paths = {p.get('id'): getPartsFromCubicSuper(CubicSuperPath(p.get('d'))) for p in  pathNodes }
            
        #paths.keys() Order disturbed
        pathIds = [p.get('id') for p in pathNodes]
        
        if(len(paths) > 1):
            if(self.options.optimized):
                startPathId = pathIds[0]
                pathIds = getArrangedIds(paths, startPathId)
                
            newParts = []
            firstElem = None
            for key in pathIds:
                parts = paths[key]
                # ~ parts = getPartsFromCubicSuper(cspath)
                start = parts[0][0][0]
                try:
                    elem = self.svg.selected[key]
			
                    if(len(newParts) == 0):
                        newParts += parts[:]
                        firstElem = elem
                    else:
                        if(vectCmpWithMargin(start, newParts[-1][-1][-1], margin = .01)):
                            newParts[-1] += parts[0]
                        else:
                            newSeg = [newParts[-1][-1][-1], newParts[-1][-1][-1], start, start]
                            newParts[-1].append(newSeg)                    
                            newParts[-1] += parts[0]
                        
                        if(len(parts) > 1):
                            newParts += parts[1:]
                    
                    parent = elem.getparent()
                    idx = parent.index(elem)
                    parent.remove(elem)
                except:
                    pass #elem might come from group item - in this case we need to ignore it
					
            newElem = copy.copy(firstElem)
            oldId = firstElem.get('id')
            newElem.set('d', CubicSuperPath(getCubicSuperFromParts(newParts)))
            newElem.set('id', oldId + '_joined')
            parent.insert(idx, newElem)

JoinPathsOptimEffect().run()