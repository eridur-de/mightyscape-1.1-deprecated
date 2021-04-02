#!/usr/bin/env python3

import inkex

"""
Extension for InkScape 1.0

This extension is totally minimal. It will just clean the whole document from groups without content (dangling groups). That usually happens if you have a group but remove it's paths for example. The group will possibly stay in the XML tree. This also applies for layers because layers are just special types of groups. This effect applies to the whole document ONLY!
 
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 19.08.2020
Last Patch: 01.04.2021
License: GNU GPL v3
"""

class CleanGroups(inkex.EffectExtension):
     
    def __init__(self):
        inkex.Effect.__init__(self)

    def effect(self):
        while True: 
            groups = self.document.xpath('//svg:g',namespaces=inkex.NSS)
            oldLen = len(groups)
            #leave the loop if there are no groups at all
            if len(groups) == 0:
                break
            #loop trough groups. we have minimum of one to check for emptyness
            for group in groups:
                if len(group.getchildren()) == 0 and group.getparent() is not None:
                    group.getparent().remove(group) #deletes the deepest empty group
                    continue #we found minimum of one element to delete. so we should run another cycle to check if the parent of this group is empty after deletion
            newLen = len(self.document.xpath('//svg:g',namespaces=inkex.NSS))
            if newLen == oldLen: #found no more empty groups. Leaving the loop
                break
            
if __name__ == '__main__':            
    CleanGroups().run()