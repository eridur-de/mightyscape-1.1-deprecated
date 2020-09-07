#!/usr/bin/env python3

"""
Extension for InkScape 1.0
Features
 - filters the current selection or the whole document for fill or stroke style. Each style will be put onto it's own layer. This way you can devide elements by their colors.
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 19.08.2020
Last patch: 29.08.2020
License: GNU GPL v3
"""
import inkex
import re
from lxml import etree
import math
from operator import itemgetter
from inkex.colors import Color

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
        self.arg_parser.add_argument("--parsecolors",default = "hexval", help = "Sort colors by")
        self.arg_parser.add_argument("--subdividethreshold", type=int, default = 1, help = "Threshold for splitting into sub layers")
        self.arg_parser.add_argument("--decimals", type=int, default = 1, help = "Decimal tolerance")
        self.arg_parser.add_argument("--cleanup", type=inkex.Boolean, default = True, help = "Decimal tolerance")

    def effect(self):
    
        def colorsort(stroke_value): #this function applies to stroke or fill (hex colors)
            if self.options.parsecolors == "hexval":
                return float(int(stroke_value[1:], 16))
            elif self.options.parsecolors == "hue":
                return float(Color(stroke_value).to_hsl()[0])
            elif self.options.parsecolors == "saturation":
                return float(Color(stroke_value).to_hsl()[1])
            elif self.options.parsecolors == "luminance":
                return float(Color(stroke_value).to_hsl()[2])
            return None
            
        layer_name = None
        layerNodeList = [] #list with layer, neutral_value, element and self.options.separateby type
        selected = [] #list of items to parse
        
        if len(self.svg.selected) == 0:
            for element in self.document.getroot().iter("*"):
                selected.append(element)
        else:
            selected = self.svg.selected.values()

        for element in selected:
            style = element.get('style')
            
            #if no style attributes or stroke/fill are set as extra attribute
            stroke         = element.get('stroke')
            stroke_width   = element.get('stroke-width')
            stroke_opacity = element.get('stroke-opacity')
            fill           = element.get('fill')
            fill_opacity   = element.get('fill-opacity')
            
            # possible values for fill are #HEXCOLOR (like #000000), color name (like purple, black, red) or gradients (URLs)

            neutral_value = None #we will use this value to slice the filter result into sub layers (threshold)
           
            if fill is not None:
                style = 'fill:'+ fill + ";"
            if stroke is not None:    
                style = style + 'stroke:' + stroke + ";"
                
            if style and element.tag != inkex.addNS('stop','svg'): #we don't want to destroy elements with gradients (they contain svg:stop elements which have a style too)
                if self.options.separateby == "stroke":
                    stroke = re.search('stroke:(.*?)(;|$)', style)
                    if stroke is not None:
                        stroke = stroke[0]
                        stroke_value = stroke.split("stroke:")[1].split(";")[0]
                        if stroke_value != "none": 
                            stroke_converted = str(Color(stroke_value).to_rgb()) #the color can be hex code or clear name. we handle both the same
                            neutral_value = colorsort(stroke_converted)
                            layer_name = "stroke-" + self.options.parsecolors + "-" + stroke_converted
                    else:
                        layer_name = "stroke-" + self.options.parsecolors + "-none"
                elif self.options.separateby == "stroke_width":        
                    stroke_width = re.search('stroke-width:(.*?)(;|$)', style)
                    if stroke_width is not None:
                        stroke_width = stroke_width[0]
                        neutral_value = self.svg.unittouu(stroke_width.split("stroke-width:")[1].split(";")[0])
                        layer_name = stroke_width
                    else:
                        layer_name = "stroke-width-none"
                elif self.options.separateby == "stroke_opacity":        
                    stroke_opacity = re.search('stroke-opacity:(.*?)(;|$)', style)
                    if stroke_opacity is not None:
                        stroke_opacity = stroke_opacity[0]
                        neutral_value = float(stroke_opacity.split("stroke-opacity:")[1].split(";")[0])
                        layer_name = stroke_opacity
                    else:
                        layer_name = "stroke-opacity-none"
                elif self.options.separateby == "fill":        
                    fill = re.search('fill:(.*?)(;|$)', style)
                    if fill is not None:
                        fill = fill[0]
                        fill_value = fill.split("fill:")[1].split(";")[0]
                        #check if the fill color is a real color or a gradient. if it's a gradient we skip the element
                        if fill_value != "none" and "url" not in fill_value:
                            fill_converted = str(Color(fill_value).to_rgb()) #the color can be hex code or clear name. we handle both the same
                            neutral_value = colorsort(fill_converted)
                            layer_name = "fill-" + self.options.parsecolors + "-" + fill_converted 
                        elif "url" in fill_value: #okay we found a gradient. we put it to some group
                            layer_name = "fill-" + self.options.parsecolors + "-gradient"
                    else:
                        layer_name = "fill-" + self.options.parsecolors + "-none"
                elif self.options.separateby == "fill_opacity":               
                    fill_opacity = re.search('fill-opacity:(.*?)(;|$)', style)
                    if fill_opacity is not None:
                        fill_opacity = fill_opacity[0]
                        neutral_value = float(fill_opacity.split("fill-opacity:")[1].split(";")[0])
                        layer_name = fill_opacity
                    else:
                        layer_name = "fill-opacity-none"
                else:
                    inkex.utils.debug("No proper option selected.")
                    exit(1)
                    
                if neutral_value is not None: #apply decimals filter
                    neutral_value = float(round(neutral_value, self.options.decimals))
                
                if layer_name is not None:
                    layer_name = layer_name.split(";")[0] #cut off existing semicolons to avoid duplicated layers with/without semicolon
                    currentLayer = self.findLayer(layer_name) 
                    if currentLayer is None: #layer does not exist, so create a new one
                        layerNodeList.append([self.createLayer(layerNodeList, layer_name), neutral_value, element, self.options.separateby])
                    else:
                        layerNodeList.append([currentLayer, neutral_value, element, self.options.separateby]) #layer is existent. append items to this later

        contentlength = 0 #some counter to track if there layers inside or if it is just a list with empty children
        for layerNode in layerNodeList:
            layerNode[0].append(layerNode[2]) #append element to created layer           
            if layerNode[1] is not None: contentlength += 1 #for each found layer we increment +1
          
        # Additionally if threshold was defined re-arrange the previously created layers by putting them into sub layers        
        if self.options.subdividethreshold > 1 and contentlength > 0: #check if there if we need to subdivide and if there items we could rearrange into sub layers
            
            #disabled sorting because it can return NoneType values which will kill the algorithm
            #layerNodeList.sort(key=itemgetter(1)) #sort by neutral values from min to max to put them with ease into parent layers
            
            topLevelLayerNodeList = [] #list with new layers and sub layers (mapping)
            minmax_range = []
            for layerNode in layerNodeList:
                if layerNode[1] is not None: 
                   if layerNode[1] not in minmax_range: 
                       minmax_range.append(layerNode[1]) #get neutral_value
      
            if len(minmax_range) >= 3: #if there are less than 3 distinct values a sub-layering will make no sense
                #adjust the subdividethreshold if there are less layers than division threshold value dictates
                if len(minmax_range) - 1 < self.options.subdividethreshold:
                    self.options.subdividethreshold = len(minmax_range)-1
                #calculate the sub layer slices (sub ranges)
                minval = min(minmax_range)
                maxval = max(minmax_range)
                sliceinterval = (maxval - minval) / self.options.subdividethreshold
        
                #inkex.utils.debug("neutral values (sorted) = " + str(minmax_range))
                #inkex.utils.debug("min neutral_value = " + str(minval))
                #inkex.utils.debug("max neutral_value = " + str(maxval))
                #inkex.utils.debug("slice value (divide step size) = " + str(sliceinterval))
                #inkex.utils.debug("subdivides (parent layers) = " + str(self.options.subdividethreshold))
             
                for layerNode in layerNodeList:
                    for x in range(0, self.options.subdividethreshold): #loop through the sorted neutral_values and determine to which layer they should belong

                        if layerNode[1] is None:
                            layer_name = str(layerNode[3]) + "#parent:unfilterable"
                            currentLayer = self.findLayer(layer_name)
                            if currentLayer is None: #layer does not exist, so create a new one
                                topLevelLayerNodeList.append([self.createLayer(topLevelLayerNodeList, layer_name), layerNode[0]])
                            else:
                                topLevelLayerNodeList.append([currentLayer, layerNode[0]]) #layer is existent. append items to this later
                            break
                        else:
                            layer_name = str(layerNode[3]) + "#parent" + str(x+1)
                            currentLayer = self.findLayer(layer_name)    
                            #value example for arranging:
                            #min neutral_value = 0.07
                            #max neutral_value = 2.50
                            #slice value = 0.81
                            #subdivides = 3
                            #
                            #that finally should generate:
                            #    layer #1: (from 0.07) to (0.07 + 0.81 = 0.88)
                            #    layer #2: (from 0.88) to (0.88 + 0.81 = 1.69)
                            #    layer #3: (from 1.69) to (1.69 + 0.81 = 2.50)
                            #
                            #now check layerNode[1] (neutral_value) and sort it into the correct layer  
                            if (layerNode[1] >= minval + sliceinterval * x) and (layerNode[1] <= minval + sliceinterval + sliceinterval * x):
                                if currentLayer is None: #layer does not exist, so create a new one
                                    topLevelLayerNodeList.append([self.createLayer(topLevelLayerNodeList, layer_name), layerNode[0]])
                                else:
                                    topLevelLayerNodeList.append([currentLayer, layerNode[0]]) #layer is existent. append items to this later
                                break
                            
                #finally append the sublayers to the slices
                #for layer in topLevelLayerNodeList:
                    #inkex.utils.debug(layer[0].get('inkscape:label'))
                    #inkex.utils.debug(layer[1])
                for newLayerNode in topLevelLayerNodeList:            
                    newLayerNode[0].append(newLayerNode[1]) #append newlayer to layer     
        
        if self.options.cleanup == True:
            try:
                import cleangroups
                cleangroups.CleanGroups.effect(self)
            except:
                inkex.utils.debug("Calling 'Remove Empty Groups' extension failed. Maybe the extension is not installed. You can download it from official InkScape Gallery.")
            
if __name__ == '__main__':
    LayerGroup().run()