#! /usr/bin/env python3

import numpy as np
from math import pi, sin, cos

import inkex

from Path import Path
from Pattern import Pattern

class SupportRing(Pattern):

    def __init__(self):
        Pattern.__init__(self)  # Must be called in order to parse common options

        # save all custom parameters defined on .inx file
        self.add_argument('--sides', type=int, default=3)
        self.add_argument('--radius_external', type=float, default=10.0)
        self.add_argument('--radius_ratio', type=float, default=0.5)
        self.add_argument('--radius_type', default='polygonal')
        self.add_argument('--radius_draw', type=inkex.Boolean, default=True)
        self.add_argument('--connector_length', type=float, default=3.0)
        self.add_argument('--connector_thickness', type=float, default=3.0)
        self.add_argument('--head_length', type=float, default=1.0)
        self.add_argument('--head_thickness', type=float, default=1.0)
        self.add_argument('--pattern', default='support ring')

    def generate_path_tree(self):
        """ Specialized path generation for your origami pattern
        """
        # retrieve conversion factor for selected unit
        unit_factor = self.calc_unit_factor()

        # retrieve saved parameters, and apply unit factor where needed
        radius_external = self.options.radius_external * unit_factor
        radius_type = self.options.radius_type
        radius_ratio = self.options.radius_ratio
        radius_internal = radius_external * radius_ratio
        dradius = radius_external-radius_internal
        sides = self.options.sides
        connector_length = self.options.connector_length * unit_factor
        connector_thickness = self.options.connector_thickness * unit_factor
        head_length = self.options.head_length * unit_factor
        head_thickness = self.options.head_thickness * unit_factor

        angle = pi / sides
        length_external = 2 * radius_external * sin(angle)
        length_internal = length_external * radius_ratio

        external_points = [(-length_external/2, 0),
                           (-connector_thickness / 2, 0),
                           (-connector_thickness / 2, -connector_length),
                           (-connector_thickness / 2 - head_thickness / 2, -connector_length),
                           (-connector_thickness / 2, -connector_length - head_length),
                           (0, -connector_length - head_length),
                           (+connector_thickness / 2, -connector_length - head_length),
                           (+connector_thickness / 2 + head_thickness / 2, -connector_length),
                           (+connector_thickness / 2, -connector_length),
                           (+connector_thickness / 2, 0),
                           (length_external/2, 0)]
        internal_points = [(0, 0), (length_internal, 0)]

        external_lines_0 = Path(external_points, 'm') + (length_external / 2, 0)
        external_lines = [external_lines_0]

        for i in range(sides-1):
            x, y = external_lines[-1].points[-1]
            external_lines.append(external_lines_0*(1, 2*(i+1)*angle) + (x, y))

        self.path_tree = [external_lines]

        if self.options.radius_draw == True:
            if radius_type == 'polygonal':
                internal_lines_0 = Path(internal_points, 'm')
                internal_lines = [internal_lines_0]
                for i in range(sides - 1):
                    x, y = internal_lines[-1].points[-1]
                    internal_lines.append(internal_lines_0*(1, 2*(i+1)*angle) + (x, y))
                internal_lines = Path.list_add(internal_lines, ((length_external - length_internal) / 2, dradius * cos(angle)))
            elif radius_type == 'circular':
                internal_lines = Path((length_external / 2, radius_internal + dradius/2), radius=radius_internal, style = 'm')

            self.path_tree.append(internal_lines)

if __name__ == '__main__':
    SupportRing().run()