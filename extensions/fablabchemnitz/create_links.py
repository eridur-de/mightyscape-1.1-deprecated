#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) 2005,2007 Aaron Spike, aaron@ekips.org
# Copyright (C) 2009 Alvin Penner, penner@vaxxine.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
This extension converts a path into a dashed line using 'stroke-dasharray'
It is a modification of the file addnodes.py
It is a modification of the file convert2dash.py
Extension to convert paths into dash-array line

ToDo:
- better handling of dasharray patterns (fix experimental stuff with multiplicator)
- dash offset does not behave the exspected way
- break apart before calculating
"""

import copy
import re

import inkex
from inkex import bezier, Path, CubicSuperPath, Group, PathElement
from inkex.bezier import csplength


class LinksCreator(inkex.EffectExtension):
    def __init__(self):
        super(LinksCreator, self).__init__()
        self.arg_parser.add_argument("--main_tabs")
        self.arg_parser.add_argument("--path_types", default="closed_paths", help="Apply for closed paths, open paths or both")
        self.arg_parser.add_argument("--unit", default="mm", help="Units")
        self.arg_parser.add_argument("--link_count", type=int, default=1, help="Link count")
        self.arg_parser.add_argument("--length_link", type=float, default=1.000, help="Link length")
        self.arg_parser.add_argument("--link_multiplicator", type=int, default=1, help="If set, we create a set of multiple gaps of same size next to the main gap")
        self.arg_parser.add_argument("--link_offset", type=float, default=0.000, help="Link offset (+/-). Does not properly work the intended way if link count is more than 1.")       
        self.arg_parser.add_argument("--length_filter", type=inkex.Boolean, default=False, help="Enable path length filtering")
        self.arg_parser.add_argument("--length_filter_value", type=float, default=0.000, help="Paths with length more than")
        self.arg_parser.add_argument("--custom_dasharray", type=inkex.Boolean, default=False, help="Enable custom dash pattern")
        self.arg_parser.add_argument("--custom_dasharray_value", default="", help="A list of separated lengths that specify the lengths of alternating dashes and gaps. Input only accepts numbers. It ignores percentages or other characters.")
        self.arg_parser.add_argument("--keep_selected", type=inkex.Boolean, default=False, help="Keep selected elements")
        self.arg_parser.add_argument("--breakapart", type=inkex.Boolean, default=False, help="Performs CTRL + SHIFT + K to break the new output path into it's parts")
        self.arg_parser.add_argument("--show_info", type=inkex.Boolean, default=False, help="Print some length and pattern information")
   
    def breakContours(self, node, breakNodes = None): #this does the same as "CTRL + SHIFT + K"
        if breakNodes == None:
            breakNodes = []
        parent = node.getparent()
        idx = parent.index(node)
        idSuffix = 0    
        raw = Path(node.get("d")).to_arrays()
        subPaths, prev = [], 0
        for i in range(len(raw)): # Breaks compound paths into simple paths
            if raw[i][0] == 'M' and i != 0:
                subPaths.append(raw[prev:i])
                prev = i
        subPaths.append(raw[prev:])  
        for subpath in subPaths:
            replacedNode = copy.copy(node)
            oldId = replacedNode.get('id')
            replacedNode.set('d', CubicSuperPath(subpath))
            replacedNode.set('id', oldId + str(idSuffix).zfill(5))
            parent.insert(idx, replacedNode)
            idSuffix += 1
            breakNodes.append(replacedNode)
        parent.remove(node)
        return breakNodes

    def effect(self):
        def createLinks(node):   
            nodeParent = node.getparent()

            pathIsClosed = False
            path = node.path.to_superpath()
            if path[-1][0] == 'Z' or path[0] == path[-1]:  #if first is last point the path is also closed. The "Z" command is not required
                pathIsClosed = True

            if self.options.path_types == 'open_paths' and pathIsClosed is True:
                return #skip this loop iteration
            elif self.options.path_types == 'closed_paths' and pathIsClosed is False:
                return #skip this loop iteration
            elif self.options.path_types == 'both':
                pass
                            
            if self.options.keep_selected is True:
                parent = node.getparent()
                idx = parent.index(node)
                copynode = copy.copy(node)
                parent.insert(idx, copynode)

            # we measure the length of the path to calculate the required dash configuration
            csp = node.path.transform(node.composed_transform()).to_superpath()
            slengths, stotal = csplength(csp) #get segment lengths and total length of path in document's internal unit
           
            if self.options.unit == "percent":
                length_link = (self.options.length_link / 100.0) * stotal
            else:
                length_link = self.svg.unittouu(str(self.options.length_link) + self.options.unit)
           
            if self.options.length_filter is True:
                if stotal < self.options.length_filter_value:
                    if self.options.show_info is True:
                        inkex.utils.debug("node " + node.get('id') + " is shorter than minimum allowed length of {:1.3f}. Path length is {:1.3f}".format(self.options.length_filter_value, stotal))
                    return #skip this loop iteration
            
            '''
            <dasharray>
                A list of comma and/or white space separated <length>s and <percentage>s that specify the lengths of alternating dashes and gaps.
                If an odd number of values is provided, then the list of values is repeated to yield an even number of values. Thus, 5,3,2 is equivalent to 5,3,2,5,3,2.

                If we want three gaps in a path with length of 168.71 mm and a gap length of 2 mm we set the stroke-dasharray to: 
                50.236 2.0 → because 3 * 50.236 mm + 3 * 2.0 mm  = 168.71 mm
                
                examples having a circle with a circumference of length = 100:
                - the array "20 5" will create 4 dashes with length = 20 and 4 gaps with length = 5 (20 + 5 + 20 + 5 + 20 + 5 + 20 + 5 = 100)
                - the array "5 20" will create 4 dashes with length = 5 and 4 gaps with length = 20 (5 + 20 + 5 + 20 + 5 + 20 + 5 + 20 = 100)
                - the array "5 15" will create 5 dashes with length = 5 and 5 gaps with length = 15 (5 + 15 + 5 + 15 + 5 + 15 + 5 + 15 + 5 + 15 = 100)
                - the array "5 14" will create 6 dashes with length = 5 and 5 gaps with length = 15 (5 + 14 + 5 + 14 + 5 + 14 + 5 + 14 + 5 + 14 + 5 = 100) - the first dash will connect to the last dash fluently
                in the examples above we always match the full length. But we do not always match it.
            '''

            dashes = []
            dashes.append((stotal - length_link * self.options.link_count) / self.options.link_count)
            dashes.append(length_link)
            
            for i in range(0, self.options.link_multiplicator):
                dashes.append(length_link) #stroke (=gap)
                dashes.append(length_link) #gap
                           
            if self.options.custom_dasharray is True:
                try:
                    floats = [float(dash) for dash in re.findall(r"[-+]?\d*\.\d+|\d+", self.options.custom_dasharray_value)]
                    if len(floats) > 0:
                        dashes = floats #overwrite previously calculated values with custom input
                    else:
                        raise ValueError
                except:
                    inkex.errormsg("Error in custom dasharray string (might be empty or does not contain any numbers). Using regular input instead ...")
                                   
            stroke_dasharray = ' '.join(format(dash, "1.3f") for dash in dashes)
            stroke_dashoffset = self.svg.unittouu(str(self.options.link_offset) + self.options.unit)

            if self.options.show_info is True:
                inkex.utils.debug("node " + node.get('id'))
                if self.options.unit == "percent":
                    inkex.utils.debug("total path length = {:1.3f} {}".format(stotal, self.svg.unit)) #show length, converted in selected unit
                else:
                    inkex.utils.debug("total path length = {:1.3f} {} ({:1.3f} {})".format(self.svg.uutounit(stotal, self.options.unit), self.options.unit, stotal, self.svg.unit)) #show length, converted in selected unit
                inkex.utils.debug("total gaps = {}".format(self.options.link_count))
                inkex.utils.debug("(calculated) gap length: {:1.3f} {}".format(length_link, self.options.unit))
                inkex.utils.debug("(calculated) dash/gap pattern: {} ({})".format(stroke_dasharray, self.svg.unit))
                inkex.utils.debug("(calculated) dash offset: {:1.3f} {}".format(self.svg.uutounit(stroke_dashoffset, self.options.unit), self.options.unit))
                inkex.utils.debug("--------------------------------------------------------------------------------------------------")

            # check if the node has a style attribute. If not we create a blank one with a black stroke and without fill
            style = None
            if node.attrib.has_key('style'):
                style = node.get('style')
                if style.endswith(';') is False:
                    style += ';'
                    
                # if has style attribute an dasharray and/or dashoffset are present we modify it accordingly
                declarations = style.split(';')  # parse the style content and check what we need to adjust
                for i, decl in enumerate(declarations):
                    parts = decl.split(':', 2)
                    if len(parts) == 2:
                        (prop, val) = parts
                        prop = prop.strip().lower()
                        if prop == 'stroke-dasharray': #comma separated list of one or more float values
                            declarations[i] = prop + ':{};'.format(stroke_dasharray)
                        if prop == 'stroke-dashoffset':
                            declarations[i] = prop + ':{};'.format(stroke_dashoffset)
                node.set('style', ';'.join(declarations)) #apply new style to node
                    
                #if has style attribute but the style attribute does not contain dasharray or dashoffset yet
                style = node.style
                if not 'stroke-dasharray' in style:
                    style = style + 'stroke-dasharray:{};'.format(stroke_dasharray)
                if not 'stroke-dashoffset' in style:
                    style = style + 'stroke-dashoffset:{};'.format(stroke_dashoffset)
                node.set('style', style)
            else:
                style = 'fill:none;stroke:#000000;stroke-width:1px;stroke-dasharray:{};stroke-dashoffset:{};'.format(stroke_dasharray, stroke_dashoffset)
                node.set('style', style)
                
            style = node.style #get the style again, but this time as style class    
                
            new = []
            for sub in node.path.to_superpath():
                idash = 0
                dash = dashes[0]
                length = float(stroke_dashoffset)
                while dash < length:
                    length = length - dash
                    idash = (idash + 1) % len(dashes)
                    dash = dashes[idash]
                new.append([sub[0][:]])
                i = 1
                while i < len(sub):
                    dash = dash - length
                    length = bezier.cspseglength(new[-1][-1], sub[i])
                    while dash < length:
                        new[-1][-1], nxt, sub[i] = \
                            bezier.cspbezsplitatlength(new[-1][-1], sub[i], dash/length)
                        if idash % 2:           # create a gap
                            new.append([nxt[:]])
                        else:                   # splice the curve
                            new[-1].append(nxt[:])
                        length = length - dash
                        idash = (idash + 1) % len(dashes)
                        dash = dashes[idash]
                    if idash % 2:
                        new.append([sub[i]])
                    else:
                        new[-1].append(sub[i])
                    i += 1
            style.pop('stroke-dasharray')
            node.pop('sodipodi:type')
            node.path = CubicSuperPath(new)
            node.style = style
            
            if self.options.breakapart is True:
                breakOutputNodes = self.breakContours(node)
                breakApartGroup = nodeParent.add(inkex.Group())
                for breakOutputNode in breakOutputNodes:
                    breakApartGroup.append(breakOutputNode)
                    #inkex.utils.debug(replacedNode.get('id'))
                    #self.svg.selection.set(replacedNode.get('id')) #update selection to split paths segments (does not work, so commented out)
                
        if len(self.svg.selected) > 0:
            for node in self.svg.selection.filter(PathElement).values():
                #at first we need to break down combined nodes to single path, otherwise dasharray cannot properly be applied
                breakInputNodes = self.breakContours(node)
                for breakInputNode in breakInputNodes:
                    createLinks(breakInputNode)

        else:
            inkex.errormsg('Please select some objects first.')
            return
        
if __name__ == '__main__':
    LinksCreator().run()