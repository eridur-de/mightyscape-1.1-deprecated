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

    def __init__(self):
        inkex.Effect.__init__(self)
    
    def effect(self):
    
        #get all paths and groups from selection. Remove all groups from the selection and form a new single group of it
        def parseNodes(self, node):
            if node.tag == inkex.addNS('path','svg'):
                if node not in self.allPaths:
                    self.allPaths.append(node)
            if node.tag == inkex.addNS('g','svg'):
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
        if len(self.svg.selected) > 0:
            if self.svg.selected[0].tag == inkex.addNS('g','svg'):
                self.svg.selected[0].getparent().remove(self.svg.selected[0])

        #TODO: make newGroup selected now. How ?
MigrateGroups().run()