#!/usr/bin/env python3

import inkex
from inkex import TextElement, TextPath, Tspan
from inkex.bezier import csparea, cspcofm, csplength
from inkex.colors import Color

class IdsToText(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument('--fontsize', type = int, default = '10', help = 'Font Size')
        self.arg_parser.add_argument('--color', type=Color, default = 255, help = 'Color')
        self.arg_parser.add_argument('--font', default = 'Roboto', help = 'Font Family')
        self.arg_parser.add_argument('--fontweight', default = 'bold', help = 'Font Weight')
        self.arg_parser.add_argument('--replaced', default = '', help = 'Text to replace')
        self.arg_parser.add_argument('--replacewith', default = '', help = 'Replace with this text')
        self.arg_parser.add_argument('--angle', type = float, dest = 'angle', default = 0, help = 'Rotation angle')
        self.arg_parser.add_argument('--capitals', type = inkex.Boolean, default = False, help = 'Capitalize')

    def effect(self):
        if len(self.svg.selected) == 0:
            inkex.errormsg("Please select some paths first.")
            exit()

        for id, node in self.svg.selected.items():
            id = node.get('id')
            self.group = node.getparent().add(TextElement())
            csp = node.path.transform(node.composed_transform()).to_superpath()
            bbox = node.bounding_box()
            tx, ty = bbox.center
            anchor = 'middle'

            node = self.group
            new = node.add(Tspan())
            new.set('sodipodi:role', 'line')
            s = {'text-align': 'center', 'vertical-align': 'bottom',
                'text-anchor': 'middle', 'font-size': str(self.options.fontsize) + 'px',
                'font-weight': self.options.fontweight, 'font-style': 'normal', 'font-family': self.options.font, 'fill': str(self.options.color)}
            new.set('style', str(inkex.Style(s)))
            new.set('dy', '0')

            if self.options.capitals:
                id = id.upper()

            new.text = id.replace(self.options.replaced, self.options.replacewith)
            node.set('x', str(tx))
            node.set('y', str(ty))
            node.set('transform', 'rotate(%s, %s, %s)' % (-int(self.options.angle), tx, ty))            

if __name__ == '__main__':
    IdsToText().run()