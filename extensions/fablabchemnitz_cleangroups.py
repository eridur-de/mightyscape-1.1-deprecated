#!/usr/bin/env python3

import inkex

class CleanGroups(inkex.Effect):
       
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
CleanGroups().run()