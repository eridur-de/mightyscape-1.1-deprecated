#!/usr/bin/env python3

# Purge short lines
# This script is designed to be used to clean up/simplify 2D vector exports from
# SketchUp. It ignores everything but paths between exactly 2 points.

import inkex
import math
debug = False

class EnerothPurgeShortEdges(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument('-w', '--length', action = 'store',
            type = float, dest = 'length', default = 10.0)
    
    def effect(self):
        length = self.options.length
        svg = self.document.getroot()
    
        if len(self.svg.selected)==0:
             self.iterate_node(self.document.getroot())
        else:
            for id, node in self.svg.selected.items():
                self.iterate_node(node)
    
    def iterate_node(self, node):
        self.do_node(node)
        for child in node:
            self.iterate_node(child)
    
    def do_node(self, node):
        if node.attrib.has_key('d'):
            points = []
    
            instruction = None
            prev_coords = [0,0]
    
            words = node.get('d').split(' ')
            for i, word in enumerate(words):
                if len(word) == 1:
                    instruction = word
                    # inkex.utils.debug(word)		  
                else:
    	        # Sometimes there is the case that "coords" returns only an array like [-1.29] (only one coordinate) instead of XY coordinates. Reason is the type "map"
                    coords = list(map(lambda c: float(c), word.split(',')))
                    # inkex.utils.debug(coords)
                    if instruction.lower() == instruction:
                        # inkex.utils.debug("coords len=" + str(len(coords)) + "prev_coords len=" + str(len(prev_coords)))
                        try:
                            coords[0] += prev_coords[0]
                            coords[1] += prev_coords[1]
                            # if len(coords) == 2:
                            # coords[1] += prev_coords[1]
                            prev_coords = coords
                            # Assume all coordinates are points of straight lines (instructor being M, m, L or l)
                            # inkex.utils.debug("X=" + str(coords[0]) + "Y=" + str(coords[1]))  
                            points.append(coords)
                            # inkex.utils.debug("pointsCount=" + str(len(points))) 
                            if len(points) == 2:
                                length = math.sqrt((points[0][0]-points[1][0])**2 + (points[0][1]-points[1][1])**2)
                                # inkex.utils.debug("length=" + str(length))		         
                            if debug:
                                inkex.utils.debug(length)
                            if length < self.options.length:
                            # inkex.utils.debug("delete")
                                node.getparent().remove(node)
                        except:
                            pass #ignore errors in case of vertical lines or horizonal lines
EnerothPurgeShortEdges().run()