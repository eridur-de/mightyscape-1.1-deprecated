#!/usr/bin/env python3
'''
Copyright (C) 2010 David Turner <novalis@novalis.org>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin St Fifth Floor, Boston, MA 02139
'''
import inkex
from inkex import paths
from collections import defaultdict

class FixedRadiusSearch():
    def __init__(self, r=0.1):
        self.r = r
        self.seen = defaultdict(list)

    def round(self, f):
        return int(round(f/self.r))
        
    def bin(self, p):
        return (self.round(p[0]), self.round(p[1]))

    def test(self, p, q):
        return abs(self.round(p[0] - q[0])) <= 1 and abs(self.round(p[1] - q[1])) <= 1

    def search(self, p):
        b = self.bin(p)
        for i in range(b[0]-1, b[0]+2):
            for j in range(b[1]-1, b[1]+2):
                for q in self.seen[(i, j)]:
                    if self.test(p, q):
                        return q
        return None

    def add(self, p):
        self.seen[self.bin(p)].append(p)

    def get_or_add(self, p):
        result = self.search(p)
        if result == None:
            self.add(p)
            return p
        return result

class RemoveRedundant(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)

    def effect(self):
        seenSegments = set()
        coordsCache = FixedRadiusSearch()

        for id, node in self.svg.selected.items():
            if node.tag == inkex.addNS('path','svg'):
                d = node.get('d')
                path = paths.CubicSuperPath(d).to_path().to_arrays()
                newPath = []
                start = prev = None
                pathclosed = True
                for command, coords in path:
                    newCoords = []
                    for x, y in zip(*[iter(coords)]*2):
                        newCoords.extend(list(coordsCache.get_or_add((x, y))))
                    coords = newCoords
                    tcoords = tuple(coords)

                    if command == 'M':
                        newPath.append([command, coords])
                        start = prev = tcoords
                        pathclosed = True
                    elif command == 'L':
                        if ('L', prev, tcoords) in seenSegments or \
                           ('L', tcoords, prev) in seenSegments:
                            newPath.append(['M', coords])
                            pathclosed = False
                        else:
                            newPath.append([command, coords])
                            seenSegments.add(('L', prev, tcoords))
                        prev = tcoords
                    elif command == 'Z':
                        if ('L', prev, start) in seenSegments or \
                           ('L', start, prev) in seenSegments:
                            newPath.append(['M', start])
                        else:
                            if pathclosed:
                                newPath.append([command, coords])
                            else:
                                newPath.append(['L', start])
                            seenSegments.add(('L', prev, start))
                        prev = start
                    elif command == 'C':
                        if ('C', prev, tcoords) in seenSegments or \
                           ('C', tcoords[4:], (tcoords[2:4], tcoords[0:2], prev)) in seenSegments:
                            newPath.append(['M', coords[4:]])
                        else:
                            newPath.append(['C', coords])
                            seenSegments.add(('C', prev, tcoords))
                        prev = tcoords[4:]                        
                    else:
                        newPath.append([command, coords])
                while len(newPath) and newPath[-1][0] == 'M':
                    newPath = newPath[:-1]
                node.set('d',str(paths.Path(newPath)))

RemoveRedundant().run()