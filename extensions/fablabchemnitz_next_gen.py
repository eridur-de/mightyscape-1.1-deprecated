#!/usr/bin/env python
# coding=utf-8
#
# NextGenerator - an Inkscape extension to export images with automatically replaced values
# Copyright (C) 2008  Aurélio A. Heckert (original Generator extension in Bash)
#               2019  Maren Hachmann (Python rewrite, update for Inkscape 1.0)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# Version 0.9
"""
An Inkscape extension to automatically replace values (text, attribute values)
in an SVG file and to then export the result to various file formats.

This is useful e.g. for generating images for name badges and other similar items.
"""

from __future__ import unicode_literals

import os
import csv
import json
import time #for debugging purposes
import inkex
from inkex.command import inkscape


class NextGenerator(inkex.base.TempDirMixin, inkex.base.InkscapeExtension):
    """Generate image files by replacing variables in the current file"""

    def add_arguments(self, pars):
        pars.add_argument("-c", "--csv_file", type=str, dest="csv_file", help="path to a CSV file")
        pars.add_argument("-e", "--extra-vars", help="additional variables to replace and the corresponding columns, in JSON format")
        pars.add_argument("-f", "--format", help="file format to export to: png, pdf, svg, ps, eps")
        pars.add_argument("-d", "--dpi", type=int, default="300", help="dpi value for exported raster images")
        pars.add_argument("-o", "--output_folder", help="path to output folder")
        pars.add_argument("-p", "--file_pattern", help="pattern for the output file")
        pars.add_argument("-t", "--tab", type=str, default="any", help="not needed at all")
        pars.add_argument("-i", "--id", type=str, default="", help="not needed at all")

    def effect(self):

        # load the attributes that should be replaced in addition to textual values
        if self.options.extra_vars == None:
            self.options.extra_vars = '{}'

        extra_vars = json.loads(self.options.extra_vars)


        # load the CSV file
        # spaces around commas will be stripped
        csv.register_dialect('generator', 'excel', skipinitialspace=True)

        with open(self.options.csv_file, newline='', encoding='utf-8') as csvfile:

            data = csv.DictReader(csvfile, dialect='generator')

            for row in data:
                export_base_name = self.options.file_pattern
                self.new_doc = self.document
                for i, (key, value) in enumerate(row.items()):
                    search_string = "%VAR_" + key + "%"
                    # replace any occurrances of %VAR_my_variable_name% in the SVG file source code
                    self.new_doc = self.new_doc.replace(search_string, value)
                    # build the file name, still without file extension
                    export_base_name = export_base_name.replace(search_string, value)
                for key, svg_cont in extra_vars.items():
                    if key in row.keys():
                        # replace any attributes and other SVG content by the values from the CSV file
                        self.new_doc = self.new_doc.replace(svg_cont, row[key])
                    else:
                        inkex.errormsg(_("The replacements in the generated images may be incomplete. Please check your entry '{key}' in the field for the non-text values.").format(key=key))
                if self.export(export_base_name) != True:
                    return

    def export(self, export_base_name):

        export_file_name = '{0}.{1}'.format(export_base_name, self.options.format)

        if os.path.exists(self.options.output_folder):
            export_file_path = os.path.join(self.options.output_folder, export_file_name)
        else:
            inkex.errormsg(_("The selected output folder does not exist."))
            return False


        if self.options.format == 'svg':
            # would use this, but it cannot overwrite, nor handle strings for writing...:
            # write_svg(self.new_doc, export_file_path)
            with open(export_file_path, 'w') as f:
                f.write(self.new_doc)
        else:

            actions = {
                'png' : 'export-dpi:{dpi};export-filename:{file_name};export-do;FileClose'.\
                        format(dpi=self.options.dpi, file_name=export_file_path),
                'pdf' : 'export-dpi:{dpi};export-pdf-version:1.5;export-text-to-path;export-filename:{file_name};export-do;FileClose'.\
                        format(dpi=self.options.dpi, file_name=export_file_path),
                'ps'  : 'export-dpi:{dpi};export-text-to-path;export-filename:{file_name};export-do;FileClose'.\
                        format(dpi=self.options.dpi, file_name=export_file_path),
                'eps' : 'export-dpi:{dpi};export-text-to-path;export-filename:{file_name};export-do;FileClose'.\
                        format(dpi=self.options.dpi, file_name=export_file_path),
                }

            # create a temporary svg file from our string
            temp_svg_name = '{0}.{1}'.format(export_base_name, 'svg')
            temp_svg_path = os.path.join(self.tempdir, temp_svg_name)
            #inkex.utils.debug("temp_svg_path=" + temp_svg_path)
            with open(temp_svg_path, 'w') as f:
                 f.write(self.new_doc)
                 #inkex.utils.debug("self.new_doc=" + self.new_doc)
            # let Inkscape do the exporting
            # self.debug(actions[self.options.format])
            cli_output = inkscape(temp_svg_path, actions=actions[self.options.format])

            if len(cli_output) > 0:
                self.debug(_("Inkscape returned the following output when trying to run the file export; the file export may still have worked:"))
                self.debug(cli_output)
                return False
            return True

    def load(self, stream):
        return str(stream.read(), 'utf-8')

    def save(self, stream):
        # must be implemented, but isn't needed.
        pass

if __name__ == '__main__':
    NextGenerator().run()