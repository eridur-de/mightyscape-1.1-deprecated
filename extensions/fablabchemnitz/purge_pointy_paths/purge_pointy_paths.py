#!/usr/bin/env python3

"""
This filter deletes paths which render as point only

More usesless and/or redundant filters for removing duplicate nodes and segments are provided by the following extension:
- https://stadtfabrikanten.org/display/IFM/Purge+Duplicate+Path+Segments
- https://stadtfabrikanten.org/display/IFM/Purge+Duplicate+Path+Nodes

Extension for InkScape 1.X
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 21.04.2021
Last patch: 21.04.2021
License: GNU GPL v3
"""

import inkex
from lxml import etree

class PurgeInvalidPaths(inkex.EffectExtension):

    def effect(self):
        if len(self.svg.selected) > 0:
            for element in self.svg.selected.values():
                if isinstance(element, inkex.PathElement):
                    p = element.path
                    commandsCoords = p.to_arrays()
                    # "m 45.250809,91.692739" - this path contains onyl one command - a single point
                    if len(commandsCoords) == 1:
                        element.delete()
                    # "m 45.250809,91.692739 z"  - this path contains two commands, but only one coordinate. 
                    # It's a single point, the path is closed by a Z command
                    elif len(commandsCoords) == 2 and commandsCoords[0][1] == commandsCoords[1][1]:
                        element.delete()
                    # "m 45.250809,91.692739 l 45.250809,91.692739" - this path contains two commands, 
                    # but the first and second coordinate are the same. It will render als point
                    elif len(commandsCoords) == 2 and commandsCoords[-1][0] == 'Z':
                        element.delete()
                    # "m 45.250809,91.692739 l 45.250809,91.692739 z" - this path contains three commands, 
                    # but the first and second coordinate are the same. It will render als point, the path is closed by a Z command
                    elif len(commandsCoords) == 3 and commandsCoords[0][1] == commandsCoords[1][1] and commandsCoords[2][1] == 'Z':
                        element.delete()
        else:
            inkex.errormsg('Please select some objects first.')
            return

if __name__ == '__main__':
    PurgeInvalidPaths().run()