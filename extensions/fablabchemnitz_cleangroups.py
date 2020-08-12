#!/usr/bin/env python3

import inkex

class CleanGroups(inkex.Effect):
       
    def __init__(self):
        inkex.Effect.__init__(self)

    def effect(self):
        groups = self.document.xpath('//svg:g',namespaces=inkex.NSS)
        for group in groups:
            if len(group.getchildren()) == 0:
                group.getparent().remove(group)
    
CleanGroups().run()