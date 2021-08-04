#!/usr/bin/env python3
'''
An extension to generate SVG files from plt files (Niklas Roy/Kai Hyyppä from Vektorkollektor)

Made by FabLab Chemnitz / Stadtfabrikanten e.V. - Developer: Mario Voigt (year 2021)

Vektorkollektor Team: Kati Hyyppa [http://katihyyppa.com] & Niklas Roy [https://niklasroy.com] 
http://vektorkollektor.com
'''

import urllib.request
from lxml import etree
import inkex
from inkex import PathElement, Path
import re
from ast import literal_eval

class Vektorkollektor(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--vk_url", default="http://www.vektorkollektor.com/vektordaten/vektorkollektor.js")
        pars.add_argument("--vk_id", type=int, default=1)

    def effect(self):
        # Download the recent vektorkollektor data file and parse it
        handler = urllib.request.HTTPBasicAuthHandler()
        opener = urllib.request.build_opener(handler)
   
        try:
            xP = [] #x-coordinate
            yP = [] #y-coordinate
            cP = [] #draw
            fN = [] #original vektorkollektor .PLT file number
            
            vkData = opener.open(self.options.vk_url).read().decode("utf-8")
            urllib.request.install_opener(opener)
            for match in re.compile(r"""^var xP = .*;""", re.MULTILINE).finditer(vkData):
                xP = literal_eval(match.group(0).split("var xP = ")[1].split(";")[0])
            for match in re.compile(r"""^var yP = .*;""", re.MULTILINE).finditer(vkData):
                yP = literal_eval(match.group(0).split("var yP = ")[1].split(";")[0])
            for match in re.compile(r"""^var cP = .*;""", re.MULTILINE).finditer(vkData):
                cP = literal_eval(match.group(0).split("var cP = ")[1].split(";")[0])
            for match in re.compile(r"""^var fN = .*;""", re.MULTILINE).finditer(vkData):
                fN = literal_eval(match.group(0).split("var fN = ")[1].split(";")[0])

            vkGroup = self.document.getroot().add(inkex.Group(id="vektorkollektor-{}".format(self.options.vk_id))) 
            for move in range(0, len(fN)):
                begin = None
                end = None
                if fN[move] == self.options.vk_id:
                    if cP[move] == 0: #pen up (reset)
                        begin = None
                        end = None
                        #self.msg("xP={}, yP={}, pen up".format(xP[move], yP[move]))
                    if cP[move] == 1:#pen down
                        begin = [xP[move-1], yP[move-1]]
                        end = [xP[move], yP[move]]
                        #self.msg("xP={}, yP={}, pen down".format(xP[move], yP[move]))
                    if begin is not None and end is not None:
                        newLine = PathElement(id="vkLine-{}".format(move))
                        newLine.path = Path("M {},{} L {},{}".format(begin[0], begin[1], end[0], end[1]))
                        newLine.style = "fill:none;stroke:#000000;stroke-width:1;stroke-linecap:round"
                        vkGroup.append(newLine)
                           
        except Exception as e:
            inkex.errormsg(e)

if __name__ == "__main__":
    Vektorkollektor().run()
