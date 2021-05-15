#!/usr/bin/env python3

"""
Based on 
- https://github.com/TimeTravel-0/ofsplot

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Last Patch: 22.04.2021
License: GNU GPL v3

"""

import inkex
import math
from inkex.paths import CubicSuperPath
import re
import pyclipper

class OffsetPaths(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--tab')
        pars.add_argument('--unit')
        pars.add_argument("--offset_count", type=int, default=1, help="Number of offset paths")
        pars.add_argument("--offset", type=float, default=1.000, help="Offset amount")
        pars.add_argument("--init_offset", type=float, default=0.000, help="Initial Offset Amount")
        pars.add_argument("--copy_org", type=inkex.Boolean, default=True, help="copy original path")
        pars.add_argument("--offset_increase", type=float, default=0.000, help="Offset increase between iterations")
        pars.add_argument("--jointype", default="2", help="Join type")
        pars.add_argument("--endtype", default="3", help="End type")
        pars.add_argument("--miterlimit", type=float, default=3.0, help="Miter limit")
        pars.add_argument("--clipperscale", type=int, default=1024, help="Scaling factor. Should be a multiplicator of 2, like 2^4=16 or 2^10=1024. The higher the scale factor the higher the quality.")
        
    def effect(self):
        unit_factor = 1.0 / self.svg.uutounit(1.0, self.options.unit)
        paths = self.svg.selection.filter(inkex.PathElement).values()
        count = sum(1 for path in paths)
        paths = self.svg.selection.filter(inkex.PathElement).values() #we need to call this twice because the sum function consumes the generator
        if count == 0:
            inkex.errormsg("No paths selected.")
            exit()
        for path in paths:
            if path.tag == inkex.addNS('path','svg'):
                p = CubicSuperPath(path.get('d'))

                scale_factor = self.options.clipperscale # 2 ** 32 = 1024 - see also https://github.com/fonttools/pyclipper/wiki/Deprecating-SCALING_FACTOR

                pco = pyclipper.PyclipperOffset(self.options.miterlimit)
                
                JT = None
                if self.options.jointype == "0":
                    JT = pyclipper.JT_SQUARE
                elif self.options.jointype == "1":
                    JT = pyclipper.JT_ROUND
                elif self.options.jointype == "2":
                    JT = pyclipper.JT_MITER
                    
                ET = None
                if self.options.endtype == "0":
                    ET = pyclipper.ET_CLOSEDPOLYGON
                elif self.options.endtype == "1":
                    ET = pyclipper.ET_CLOSEDLINE
                elif self.options.endtype == "2":
                    ET = pyclipper.ET_OPENBUTT
                elif self.options.endtype == "3":
                    ET = pyclipper.ET_OPENSQUARE
                elif self.options.endtype == "4":                 
                    ET = pyclipper.ET_OPENROUND
                
                new = []

                # load in initial paths
                for sub in p:
                    sub_simple = []
                    for item in sub:
                        itemx = [float(z) * scale_factor for z in item[1]]
                        sub_simple.append(itemx)
                    pco.AddPath(sub_simple, JT, ET)

                # calculate offset paths for different offset amounts
                offset_list = []
                offset_list.append(self.options.init_offset * unit_factor)
                for i in range(0, self.options.offset_count):
                    ofs_increase = +math.pow(float(i) * self.options.offset_increase * unit_factor, 2)
                    if self.options.offset_increase < 0:
                        ofs_increase = -ofs_increase
                    offset_list.append(offset_list[0] + float(i) * self.options.offset * unit_factor + ofs_increase * unit_factor)

                solutions = []
                for offset in offset_list:
                    solution = pco.Execute(offset * scale_factor)
                    solutions.append(solution)
                    if len(solution)<=0:
                        continue # no more loops to go, will provide no results.

                # re-arrange solutions to fit expected format & add to array
                for solution in solutions:
                    for sol in solution:
                        solx = [[float(s[0]) / scale_factor, float(s[1]) / scale_factor] for s in sol]
                        sol_p = [[a, a, a] for a in solx]
                        sol_p.append(sol_p[0][:])
                        new.append(sol_p)

                # add old, just to keep (make optional!)
                if self.options.copy_org:
                    for sub in p:
                        new.append(sub)

                path.set('d', CubicSuperPath(new))

if __name__ == '__main__':
    OffsetPaths().run()