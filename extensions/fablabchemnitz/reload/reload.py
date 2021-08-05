#!/usr/bin/env python3

import inkex
from lxml import etree

class Reload(inkex.EffectExtension):

    def effect(self):
        currentDoc = self.document_path()
        if currentDoc == "":
            self.msg("Your document is not saved as a permanent file yet. Cannot reload.")
            exit(1)
        stream = open(self.document_path(), 'r')
        p = etree.XMLParser(huge_tree=True)
        doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True))
        stream.close()
        root = self.document.getroot()
        kept = [] #required. if we delete them directly without adding new defs or namedview, inkscape will crash
        for node in self.document.xpath('//*', namespaces=inkex.NSS):
            if node.TAG not in ('svg', 'defs', 'namedview'):
                node.delete()
            elif node.TAG in ('defs', 'namedview'): #except 'svg'
                kept.append(node)
        
        children = doc.getroot().getchildren()
        for child in children:
           root.append(child)
        for k in kept:
            k.delete()
    
if __name__ == '__main__':
    Reload().run()