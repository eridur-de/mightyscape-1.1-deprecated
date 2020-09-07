#!/usr/bin/env python3

"""
Extension for InkScape 1.0

This extension parses the selection and will put all elements into one single group. If you have a cluster with lots of groups and elements you will clean up this way (one top level group, all elements below it). If you select a single element or a set of elements you just wrap it like using CTRL + G (like making a usual group). You can also use this extension to filter out unwanted SVG elements at all.
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 13.08.2020
Last Patch: 31.08.2020
License: GNU GPL v3
"""

import inkex
from lxml import etree

class MigrateGroups(inkex.Effect):

    allElements = [] #list of all (sub)elements to process within selection
    allGroups = [] #list of all groups (svg:g and svg:svg items) to delete for cleanup (for ungrouping)
    allDrops = [] #list of all other elements except svg:g and svg:svg to drop while migrating (for filtering)
    
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--ignorecustomselection", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--operationmode", default=False)
        self.arg_parser.add_argument("--parsechildren", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--cleanup", type=inkex.Boolean, default = True, help = "Decimal tolerance")
        self.arg_parser.add_argument("--showdroplist", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--shownewgroupname", type=inkex.Boolean, default=False)

        #self.arg_parser.add_argument("--sodipodi",      type=inkex.Boolean, default=True)
        #self.arg_parser.add_argument("--svg",           type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--circle",         type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--clipPath",       type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--defs",           type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--ellipse",        type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--image",          type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--line",           type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--path",           type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--polyline",       type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--polygon",        type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--rect",           type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--text",           type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--tspan",          type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--linearGradient", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--radialGradient", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--meshGradient",   type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--meshRow",        type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--meshPatch",      type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--metadata",       type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--script",         type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--symbol",         type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--stop",           type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--use",            type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--flowRoot",       type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--flowRegion",     type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--flowPara",       type=inkex.Boolean, default=True)
    
    def effect(self):
        namespace = [] #a list of selected types we are going to process for filtering (dropping items)
        #namespace.append("{http://www.w3.org/2000/svg}sodipodi")       if self.options.sodipodi       else "" #do not do this. it will crash InkScape
        #namespace.append("{http://www.w3.org/2000/svg}svg")            if self.options.svg            else "" #we handle svg:svg the same type like svg:g
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
        namespace.append("{http://www.w3.org/2000/svg}text")           if self.options.text           else ""
        namespace.append("{http://www.w3.org/2000/svg}tspan")          if self.options.tspan          else ""
        namespace.append("{http://www.w3.org/2000/svg}linearGradient") if self.options.linearGradient else ""
        namespace.append("{http://www.w3.org/2000/svg}radialGradient") if self.options.radialGradient else ""
        namespace.append("{http://www.w3.org/2000/svg}meshGradient")   if self.options.meshGradient   else ""
        namespace.append("{http://www.w3.org/2000/svg}meshRow")        if self.options.meshRow        else ""
        namespace.append("{http://www.w3.org/2000/svg}meshPatch")      if self.options.meshPatch      else ""
        namespace.append("{http://www.w3.org/2000/svg}script")         if self.options.script         else ""
        namespace.append("{http://www.w3.org/2000/svg}symbol")         if self.options.symbol         else ""
        namespace.append("{http://www.w3.org/2000/svg}metadata")       if self.options.metadata       else ""
        namespace.append("{http://www.w3.org/2000/svg}stop")           if self.options.stop           else ""
        namespace.append("{http://www.w3.org/2000/svg}use")            if self.options.use            else ""
        namespace.append("{http://www.w3.org/2000/svg}flowRoot")       if self.options.flowRoot       else ""
        namespace.append("{http://www.w3.org/2000/svg}flowRegion")     if self.options.flowRegion     else ""
        namespace.append("{http://www.w3.org/2000/svg}flowPara")       if self.options.flowPara       else ""
        #inkex.utils.debug(namespace)

        #in case the user made a manual selection instead of whole document parsing, we need to collect all required elements first
        def parseChildren(element):
            if element not in selected:
                selected.append(element)
            if self.options.parsechildren == True:   
                children = element.getchildren()
                if children is not None:
                    for child in children:
                        if child not in selected:
                            selected.append(child)
                        parseChildren(child) #go deeper and deeper

        #check the element for it's type and put it into the according list (either re-group or delete or just nothing)
        def parseElement(self, element):
            #if we only want to ungroup (flatten) the elements we just collect all elements in a list and put them in a new single group later
            if self.options.operationmode == "ungroup_only": 
                if element not in self.allElements:
                    if element.tag != inkex.addNS('g','svg') and element.tag != inkex.addNS('svg','svg') and element.tag != inkex.addNS('namedview','sodipodi'):
                        self.allElements.append(element)
            #if we dont want to ungroup but filter out elements, or ungroup and filter, we need to divide the elements with respect to the namespace (user selection)
            elif self.options.operationmode == "filter_only" or self.options.operationmode == "ungroup_and_filter":
                #inkex.utils.debug(element.tag)
                if element.tag in namespace: #if the element is in namespace and no group type we will regroup the item. so we will not remove it
                    if element not in self.allElements:
                        self.allElements.append(element)
                else: #we add all remaining items (except svg:g and svg:svg) into the list for deletion
                    #inkex.utils.debug(element.tag)
                    if element.tag != inkex.addNS('g','svg') and element.tag != inkex.addNS('svg','svg') and element.tag != inkex.addNS('namedview','sodipodi'):
                        if element not in self.allDrops:
                            self.allDrops.append(element)
            #finally the groups we want to get rid off are put into a another list. They will be deleted (depending on the mode) after parsing the element tree
            if self.options.operationmode == "ungroup_only" or self.options.operationmode == "ungroup_and_filter":
                if element.tag == inkex.addNS('g','svg') or element.tag == inkex.addNS('svg','svg'):
                    if element not in self.allGroups:
                        self.allGroups.append(element)

        #check if we have selected elements or if we should parse the whole document instead
        selected = [] #total list of elements to parse
        if len(self.svg.selected) == 0:
            for element in self.document.getroot().iter(tag=etree.Element):
                if element != self.document.getroot():
                    selected.append(element)
        else:
            for id, element in self.svg.selected.items():
                parseChildren(element)
                
        #get all elements from the selection.
        for element in selected:
            parseElement(self, element)
           
        #some debugging block
        #check output
        #inkex.utils.debug("--- Selected items (with or without children) ---")
        #inkex.utils.debug(selected)
        #inkex.utils.debug("--- All elements (except groups)---")
        #inkex.utils.debug(len(self.allElements))
        #inkex.utils.debug(self.allElements)
        #inkex.utils.debug("--- All groups ---")
        #inkex.utils.debug(len(self.allGroups))
        #inkex.utils.debug(self.allGroups)
        #inkex.utils.debug("--- All dropouts ---")
        #inkex.utils.debug(len(self.allDrops))
        #inkex.utils.debug(self.allDrops)
            
        # show a list with items to delete. For ungroup mode it does not apply because we are not going to remove anything
        if self.options.operationmode == "filter_only" or self.options.operationmode == "ungroup_and_filter":
            if self.options.showdroplist:
                self.msg(str(len(self.allDrops)) + " elements were removed during nodes while migration:")
                for i in self.allDrops:
                    if i.get('id') is not None:
                        self.msg(i.tag.replace("{http://www.w3.org/2000/svg}","svg:") + " id:" + i.get('id'))

        # remove all groups from the selection and form a new single group of it by copying with old IDs.
        if self.options.operationmode == "ungroup_only" or self.options.operationmode == "ungroup_and_filter":
            if len(self.allElements) > 0:
                newGroup = self.document.getroot().add(inkex.Group()) #make a new group at root level
                newGroup.set('id', self.svg.get_unique_id('migrate-')) #generate some known ID with the prefix 'migrate-'
                if self.options.shownewgroupname == True:
                        inkex.utils.debug("The migrated elements are now in group with ID " + str(newGroup.get('id')))
                index = 0
                for element in self.allElements: #we have a list of elements which does not cotain any other elements like svg:g or svg:svg 
                    newGroup.insert(index, element) #we do not copy any elements. we just rearrange them by moving to another place (group index)
                    index += 1 #we must count up the index or we would overwrite each previous element
   
       # remove the stuff from drop list list. this has to be done before we drop the groups where they are located in
        if self.options.operationmode == "filter_only" or self.options.operationmode == "ungroup_and_filter":
            if len(self.allDrops) > 0:
                for dropElement in self.allDrops:
                    if dropElement.getparent() is not None:
                        dropElement.getparent().remove(dropElement)
              
        # remove all the obsolete groups which are left over from ungrouping (flattening)
        if self.options.operationmode == "ungroup_only" or self.options.operationmode == "ungroup_and_filter":
            if len(self.allGroups) > 0:        
                for group in self.allGroups:
                    if group.getparent() is not None:
                        group.getparent().remove(group)
   
        # finally removed dangling empty groups using external extension (if installed)
        if self.options.cleanup == True:
            try:
                import cleangroups
                cleangroups.CleanGroups.effect(self)
            except:
                inkex.utils.debug("Calling 'Remove Empty Groups' extension failed. Maybe the extension is not installed. You can download it from official InkScape Gallery.")
         
if __name__ == '__main__':
    MigrateGroups().run()