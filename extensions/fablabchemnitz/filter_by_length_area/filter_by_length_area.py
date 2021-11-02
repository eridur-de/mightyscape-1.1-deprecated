#!/usr/bin/env python3

'''
Extension for InkScape 1.0
Features
- Filter paths which are smaller/bigger than a given length or area

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 03.08.2020
Last patch: 21.10.2021
License: GNU GPL v3
'''

import inkex
from inkex.bezier import csplength, csparea

class FilterByLengthArea(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--debug', type=inkex.Boolean, default=False)
        pars.add_argument('--unit')
        pars.add_argument('--min_filter_enable', type=inkex.Boolean, default=True, help='Enable filtering min.')
        pars.add_argument('--min_threshold', type=float, default=0.000, help='Remove paths with an threshold smaller than this value')
        pars.add_argument('--max_filter_enable', type=inkex.Boolean, default=False, help='Enable filtering max.')
        pars.add_argument('--max_threshold', type=float, default=10000000.000, help='Remove paths with an threshold bigger than this value')
        pars.add_argument('--min_nodes', type=int, default=0, help='Min. nodes/<interval>')
        pars.add_argument('--max_nodes', type=int, default=10000000, help='Max. nodes/<interval>')
        pars.add_argument('--nodes_interval', type=float, default=10000000.000, help='Interval')
        pars.add_argument('--measure', default="length")
		
    def effect(self):
        so = self.options
        if so.min_filter_enable is False and so.max_filter_enable is False:
            inkex.utils.debug("You need to enabled at least one filter rule!")
            return
        
        so.min_threshold = self.svg.unittouu(str(so.min_threshold) + self.svg.unit)
        so.max_threshold = self.svg.unittouu(str(so.max_threshold) + self.svg.unit)
        unit_factor = 1.0 / self.svg.uutounit(1.0, so.unit)
        if so.min_threshold == 0 or so.max_threshold == 0:
            inkex.utils.debug("One or both tresholds are zero. Please adjust.")
            return
        
        if len(self.svg.selected) > 0:
            elements = self.svg.selection.filter(inkex.PathElement).values()
        else:
            elements = self.document.xpath("//svg:path", namespaces=inkex.NSS)

        for element in elements:
            try:
                csp = element.path.transform(element.composed_transform()).to_superpath()

                if so.measure == "area":
                    area = -csparea(csp) #is returned as negative value. we need to invert with
                    if so.debug is True: 
                        inkex.utils.debug("id={}, area={:0.3f}{}^2".format(element.get('id'), area, so.unit))
                    if so.min_filter_enable is True and area < (so.min_threshold * (unit_factor * unit_factor)):
                        element.delete()
                    if so.max_filter_enable is True and area >= (so.max_threshold * (unit_factor * unit_factor)):
                        element.delete()
                        
                elif so.measure == "length":
                    slengths, stotal = csplength(csp) #get segment lengths and total length of path in document's internal unit
                    if so.debug is True: 
                        inkex.utils.debug("id={}, length={:0.3f}{}".format(element.get('id'), self.svg.uutounit(str(stotal), so.unit), so.unit))
                    if so.min_filter_enable is True and stotal < (so.min_threshold * unit_factor):
                        element.delete()
                    if self.options.max_filter_enable is True and stotal >= (so.max_threshold * unit_factor):
                        element.delete()
                   
                elif so.measure == "nodes":
                    slengths, stotal = csplength(csp) #get segment lengths and total length of path in document's internal unit
                    nodes = len(element.path)
                    if so.debug is True: 
                        inkex.utils.debug("id={}, length={:0.3f}{}, nodes={}".format(element.get('id'), self.svg.uutounit(str(stotal), so.unit), so.unit, nodes))
                    if so.min_filter_enable is True and nodes / stotal < so.min_nodes / self.svg.unittouu(str(so.nodes_interval) + so.unit):
                        element.delete()
                    if so.max_filter_enable is True and nodes / stotal < so.max_nodes / self.svg.unittouu(str(so.nodes_interval) + so.unit):
                        element.delete() 
     
            except Exception as e:
                #self.msg(e)
                pass

if __name__ == '__main__':
    FilterByLengthArea().run()