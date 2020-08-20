#!/usr/bin/env python3

"""
Extension for InkScape 1.0

This extension parses the selection and will put all paths into one single group. If you have a cluster with lots of groups and paths you will clean up this way (one top level group, all paths below it). If you select a single path or a set of paths you just wrap it like using CTRL + G (like making a usual group)
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 13.08.2020
License: GNU GPL v3
"""

import inkex

class MigrateGroups(inkex.Effect):

    allPaths = []
    allGroups = []
    allNonMigrates = []
    
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--rect", type=inkex.Boolean, default=True, help="rect")
        self.arg_parser.add_argument("--circle", type=inkex.Boolean, default=True, help="circle")
        self.arg_parser.add_argument("--ellipse", type=inkex.Boolean, default=True, help="ellipse")
        self.arg_parser.add_argument("--line", type=inkex.Boolean, default=True, help="line")
        self.arg_parser.add_argument("--polyline", type=inkex.Boolean, default=True, help="polyline")
        self.arg_parser.add_argument("--polygon", type=inkex.Boolean, default=True, help="polygon")
        self.arg_parser.add_argument("--path", type=inkex.Boolean, default=True, help="path")
        self.arg_parser.add_argument("--image", type=inkex.Boolean, default=True, help="image")
        self.arg_parser.add_argument("--text", type=inkex.Boolean, default=True, help="text")
        self.arg_parser.add_argument("--tspan", type=inkex.Boolean, default=True, help="tspan")
    
    def effect(self):
    
        namespace = []
        namespace.append("{http://www.w3.org/2000/svg}rect")     if self.options.rect else ""
        namespace.append("{http://www.w3.org/2000/svg}circle")   if self.options.circle else ""
        namespace.append("{http://www.w3.org/2000/svg}ellipse")  if self.options.ellipse else ""
        namespace.append("{http://www.w3.org/2000/svg}line")     if self.options.line else ""
        namespace.append("{http://www.w3.org/2000/svg}polyline") if self.options.polyline else ""
        namespace.append("{http://www.w3.org/2000/svg}polygon")  if self.options.polygon else ""
        namespace.append("{http://www.w3.org/2000/svg}path")     if self.options.path else ""
        namespace.append("{http://www.w3.org/2000/svg}image")    if self.options.image else ""
        namespace.append("{http://www.w3.org/2000/svg}text")     if self.options.text else ""
        namespace.append("{http://www.w3.org/2000/svg}tspan")    if self.options.tspan else ""
    
        #get all paths and groups from selection. Remove all groups from the selection and form a new single group of it
        def parseNodes(self, node):
            if node.tag in namespace:
                if node not in self.allPaths:
                    self.allPaths.append(node)
            else:
                if node.tag != inkex.addNS('g','svg'):
                    self.allNonMigrates.append(node)
            if node.tag == inkex.addNS('g','svg'):
                if node not in self.allGroups:
                    self.allGroups.append(node)
                groups = node.getchildren()
                if groups is not None:
                    for group in groups:
                        parseNodes(self, group)
                        if group not in self.allGroups:
                            self.allGroups.append(group)
    
        for id, item in self.svg.selected.items():
            parseNodes(self, item)
         
        if len(self.allPaths) > 0:
            #make a new group at root level - TODO: respect the position where the first selected object is in XML tree and put it there instead (or make this optional)
            newGroup = self.document.getroot().add(inkex.Group())

            #copy all paths into the new group
            for path in self.allPaths:
                newGroup.add(path.copy())
            
                #then remove all the old stuff
                path.getparent().remove(path)
   
        #now remove all the obsolete groups
        if len(self.allGroups) > 0:        
            for group in self.allGroups:
                if group.getparent() is not None:
                    group.getparent().remove(group)
          
        #remove the selected, now empty group (if it's the case)
        if len(self.svg.selected) > 0 and len(self.allPaths) > 0: 
            if self.svg.selected[0].tag == inkex.addNS('g','svg'):
                if self.svg.selected[0].getparent() is not None:
                    self.svg.selected[0].getparent().remove(self.svg.selected[0])

        if len(self.allNonMigrates) > 0:
            self.msg("You are going to remove " + str(len(self.allNonMigrates)) + " nodes while migrating:")
            for i in self.allNonMigrates:
                self.msg(i.get('id'))            
                    
        #TODO: make newGroup selected now. How ?
MigrateGroups().run()