#!/usr/bin/env python3

"""
Extension for InkScape 1.0
Features
 - filters the current selection or the whole document for fill or stroke style. Each style will be put onto it's own layer. This way you can devide elements by their colors.
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 19.08.2020
Last patch: 19.08.2020
License: GNU GPL v3
"""

import inkex
import re
from lxml import etree

class LayerGroup(inkex.Effect):

    def findLayer(self, layerName):
        svg_layers = self.document.xpath('//svg:g[@inkscape:groupmode="layer"]', namespaces=inkex.NSS)
        for layer in svg_layers:
            #inkex.utils.debug(str(layer.get('inkscape:label')) + " == " + layerName)
            if layer.get('inkscape:label') == layerName:
                return layer
        return None

    def createLayer(self, layerNodeList, layerName):
        svg = self.document.xpath('//svg:svg',namespaces=inkex.NSS)[0]
        for layer in layerNodeList:
            #inkex.utils.debug(str(layer[0].get('inkscape:label')) + " == " + layerName)
            if layer[0].get('inkscape:label') == layerName:
                return layer[0] #already exists. Do not create duplicate
        layer = etree.SubElement(svg, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), '%s' % layerName)
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        return layer
        
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--separateby", default = "stroke", help = "Separate by")

    def effect(self):
   
        layer_name = None
        layerNodeList = [] #list with layer and node 
        selected = [] #list of items to parse
        
        if len(self.svg.selected) == 0:
            for element in self.document.getroot().iter("*"):
                selected.append(element)
        else:
            selected = self.svg.selected.values()
            
        for element in selected:
            style = element.get('style')
            fill = element.get('fill') #if no style attribute or fill is set as extra attribute
            stroke = element.get('stroke') #if no style attribute or stroke is set as extra attribute
            if fill is not None or stroke is not None:
                style = 'fill:'+ fill + ';stroke:' + stroke + ";"
                
            if style:
                if self.options.separateby == "stroke":
                    stroke = re.search('stroke:(.*?)(;|$)', style)
                    if stroke is not None:
                        stroke = stroke[0][8:-1]
                        layer_name = "stroke-" + stroke
                elif self.options.separateby == "fill":        
                    fill = re.search('fill:(.*?)(;|$)', style)
                    if fill is not None:
                        fill = fill[0][6:-1]
                        layer_name = "fill-" + fill

                if layer_name is not None:
                    currentLayer = self.findLayer(layer_name)    
                    
                    if currentLayer is None: #layer does not exist, so create a new one
                        layerNodeList.append([self.createLayer(layerNodeList, layer_name), element])
                    else:
                        layerNodeList.append([currentLayer, element]) #layer is existent. append items to this later
                                
        for layerNode in layerNodeList:
            layerNode[0].append(layerNode[1])
                
LayerGroup().run()