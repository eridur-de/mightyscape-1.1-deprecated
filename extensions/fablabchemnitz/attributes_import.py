#!/usr/bin/env python3

import inkex

class AttribImport(inkex.EffectExtension):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--data", default="", help="data file")

    def effect(self):
        with open(self.options.data, 'r') as f:
            lines = f.read().splitlines()
            for line in lines:
                #split on , max 2+1 = 3 items
                parts = line.split(",", 2)
                if len(parts) >= 3:
                    id = parts[0]
                    attribute = parts[1]
                    value = parts[2]
                    try:
                        node = self.svg.getElementById(id)
                        if node is not None:
                            try: 
                                node.set(attribute, value)
                            except AttributeError:
                                inkex.utils.debug("Unknown Attribute")
                    except AttributeError:
                        inkex.utils.debug("element with id '" + id + "' not found in current selection.")
                        
if __name__ == '__main__':
    AttribImport().run()