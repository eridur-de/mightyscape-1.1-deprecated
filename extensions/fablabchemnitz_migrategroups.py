#!/usr/bin/env python3

"""
Extension for InkScape 1.0

This extension parses the selection and will put all elements into one single group. If you have a cluster with lots of groups and elements you will clean up this way (one top level group, all elements below it). If you select a single element or a set of elements you just wrap it like using CTRL + G (like making a usual group). You can also use this extension to filter out unwanted SVG elements at all.
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 13.08.2020
Last Patch: 23.08.2020
License: GNU GPL v3
"""

import inkex
from lxml import etree

class MigrateGroups(inkex.Effect):

    allElements = []
    allGroups = []
    allNonMigrates = []
    
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--allitems", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--droponly", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--showdroplist", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--circle", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--clipPath", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--defs", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--ellipse", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--image", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--line", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--path", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--polyline", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--polygon", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--rect", type=inkex.Boolean, default=True)
        #self.arg_parser.add_argument("--sodipodi", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--svg", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--text", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--tspan", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--lineargradient", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--radialgradient", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--meshgradient", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--meshrow", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--meshpatch", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--metadata", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--script", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--stop", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--use", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--flowRoot", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--flowRegion", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--flowPara", type=inkex.Boolean, default=True)
    
    def effect(self):
        namespace = []
        namespace.append("{http://www.w3.org/2000/svg}circle")         if self.options.circle         else ""
        namespace.append("{http://www.w3.org/2000/svg}clipPath")       if self.options.clipPath       else ""
        namespace.append("{http://www.w3.org/2000/svg}defs")           if self.options.defs           else ""     
        namespace.append("{http://www.w3.org/2000/svg}ellipse")        if self.options.ellipse        else ""
        namespace.append("{http://www.w3.org/2000/svg}image")          if self.options.image          else ""
        namespace.append("{http://www.w3.org/2000/svg}line")           if self.options.line           else ""
        namespace.append("{http://www.w3.org/2000/svg}polygon")        if self.options.polygon        else ""
        namespace.append("{http://www.w3.org/2000/svg}path")           if self.options.path           else ""
        namespace.append("{http://www.w3.org/2000/svg}polyline")       if self.options.polyline       else ""
        namespace.append("{http://www.w3.org/2000/svg}rect")           if self.options.rect           else ""
        #namespace.append("{http://www.w3.org/2000/svg}sodipodi")       if self.options.sodipodi       else "" #do not do this. it will crash InkScape
        #namespace.append("{http://www.w3.org/2000/svg}svg")            if self.options.svg            else ""
        namespace.append("{http://www.w3.org/2000/svg}text")           if self.options.text           else ""
        namespace.append("{http://www.w3.org/2000/svg}tspan")          if self.options.tspan          else ""
        namespace.append("{http://www.w3.org/2000/svg}lineargradient") if self.options.lineargradient else ""
        namespace.append("{http://www.w3.org/2000/svg}radialgradient") if self.options.radialgradient else ""
        namespace.append("{http://www.w3.org/2000/svg}meshgradient")   if self.options.meshgradient   else ""
        namespace.append("{http://www.w3.org/2000/svg}meshrow")        if self.options.meshrow        else ""
        namespace.append("{http://www.w3.org/2000/svg}meshpatch")      if self.options.meshpatch      else ""
        namespace.append("{http://www.w3.org/2000/svg}script")         if self.options.script         else ""
        namespace.append("{http://www.w3.org/2000/svg}metadata")       if self.options.metadata       else ""
        namespace.append("{http://www.w3.org/2000/svg}stop")           if self.options.stop           else ""
        namespace.append("{http://www.w3.org/2000/svg}use")            if self.options.use            else ""
        namespace.append("{http://www.w3.org/2000/svg}flowRoot")       if self.options.flowRoot       else ""
        namespace.append("{http://www.w3.org/2000/svg}flowRegion")     if self.options.flowRegion     else ""
        namespace.append("{http://www.w3.org/2000/svg}flowPara")       if self.options.flowPara       else ""
        
        #check if we have selected elements or if we should parse the whole document instead
        selected = [] #list of elements to parse
        if len(self.svg.selected) == 0:
            for element in self.document.getroot().iter(tag=etree.Element):
                if element != self.document.getroot():
                    selected.append(element)
        else:
            selected = self.svg.selected
      
        def parseNodes(self, element):
        
            if self.options.allitems:
                if element not in self.allElements:
                    if element.tag != inkex.addNS('g','svg') and element.tag != inkex.addNS('svg','svg') and element.tag != inkex.addNS('namedview','sodipodi'):
                        self.allElements.append(element)
            else: 
                if element.tag in namespace:
                    if element not in self.allElements:
                        self.allElements.append(element)
                else:
                    if element.tag != inkex.addNS('g','svg') and element.tag != inkex.addNS('svg','svg') and element.tag != inkex.addNS('namedview','sodipodi'):
                        if element not in self.allNonMigrates:
                            self.allNonMigrates.append(element)
  
            if element.tag == inkex.addNS('g','svg') or element.tag == inkex.addNS('svg','svg'):
                if element not in self.allGroups:
                    self.allGroups.append(element)
                groups = element.getchildren()
                if groups is not None:
                    for group in groups:
                        parseNodes(self, group)
                        if group not in self.allGroups:
                            self.allGroups.append(group)
    
        #get all elements from the selection. Remove all groups from the selection and form a new single group of it. We also handle svg:svg because it behaves like a group container too
        for element in selected:
            parseNodes(self, element)
                
        if len(self.allElements) > 0:
            #copy all element into the new group
            newGroup = self.document.getroot().add(inkex.Group()) #make a new group at root level

            for oldElement in self.allElements:
                #oldElementId = oldElement.get('id')
                newElement = oldElement.copy()
                #newElement.set('id', oldElementId)
                newGroup.add(newElement)
            if self.options.droponly:
                if oldElement.getparent() is not None:
                    oldElement.getparent().remove(oldElement)
   
        if self.options.droponly == False:
            #now remove all the obsolete groups
            if len(self.allGroups) > 0:        
                for group in self.allGroups:
                    #if group.getparent() is not None:
                    group.getparent().remove(group)
              
        #remove the selected, now empty group (if it's the case) - this applies not if there is no user selection at all so some dangling group(s) might be left over
        if len(self.svg.selected) > 0 and len(self.allElements) > 0: 
            if self.svg.selected[0].tag == inkex.addNS('g','svg') or self.svg.selected[0].tag == inkex.addNS('svg','svg'):
                if self.svg.selected[0].getparent() is not None:
                    self.svg.selected[0].getparent().remove(self.svg.selected[0])
               
        if self.options.showdroplist:
            self.msg(str(len(self.allNonMigrates)) + " elements were removed during nodes while migration:")
            for i in self.allNonMigrates:
                if i.get('id') is not None:
                    self.msg(i.tag.replace("{http://www.w3.org/2000/svg}","svg:") + " id:" + i.get('id'))            
                    
MigrateGroups().run()