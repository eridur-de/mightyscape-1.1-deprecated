#!/usr/bin/env python3
"""
Pixel2SVG - Convert the pixels of bitmap images to SVG rects

Idea and original implementation as standalone script:
Copyright (C) 2011 Florian Berger <fberger@florian-berger.de>
Homepage: <http://florian-berger.de/en/software/pixel2svg>

Rewritten as Inkscape extension:
Copyright (C) 2012 ~suv <suv-sf@users.sourceforge.net>

'getFilePath()' is based on code from 'extractimages.py':
Copyright (C) 2005 Aaron Spike, aaron@ekips.org

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""

import os
import sys
import base64
from io import StringIO, BytesIO
import urllib.parse
import urllib.request
import inkex
from PIL import Image
from lxml import etree

inkex.localization.localize

DEBUG = False


#   int r = ( hexcolor >> 16 ) & 0xFF;
#   int g = ( hexcolor >> 8 ) & 0xFF;
#   int b = hexcolor & 0xFF;
#   int hexcolor = (r << 16) + (g << 8) + b;

def hex_to_int_color(v):
    if (v[0] == '#'):
        v = v[1:]
    assert(len(v) == 6)
    return int(v[:2], 16), int(v[2:4], 16), int(v[4:6], 16)


class Pixel2SVG(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        # pixel2svg options
        self.arg_parser.add_argument("-s", "--squaresize", type=int, default="5", help="Width and height of vector squares in pixels")
        self.arg_parser.add_argument("--transparency", type=inkex.Boolean, default=True, help="Convert transparency to 'fill-opacity'")
        self.arg_parser.add_argument("--overlap", type=inkex.Boolean, default=False, help="Overlap vector squares by 1px")
        self.arg_parser.add_argument("--offset_image", type=inkex.Boolean, default=True, help="Offset traced image")
        self.arg_parser.add_argument("--delete_image", type=inkex.Boolean, default=False, help="Delete bitmap image")
        self.arg_parser.add_argument("--maxsize", type=int, default="256", help="Max. image size (width or height)")
        self.arg_parser.add_argument("--verbose", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--color_mode", default="all", help="Which colors to trace.")
        self.arg_parser.add_argument("--color", default="FFFFFF", help="Special color")
        self.arg_parser.add_argument("--tab")

    def getImagePath(self, node, xlink):
        """
        Find image file, return path
        """
        absref = node.get(inkex.addNS('absref', 'sodipodi'))
        url = urlparse(xlink)
        href = urllib.request.url2pathname

        path = ''
        #path selection strategy:
        # 1. href if absolute
        # 2. realpath-ified href
        # 3. absref, only if the above does not point to a file
        if href is not None:
            path = os.path.realpath(href)
        if (not os.path.isfile(path)):
            if absref is not None:
                path = absref

        try:
            path = unicode(path, "utf-8")
        except TypeError:
            path = path

        if (not os.path.isfile(path)):
            inkex.errormsg(_(
                "No xlink:href or sodipodi:absref attributes found, " +
                "or they do not point to an existing file! Unable to find image file."))
            if path:
                inkex.errormsg(_("Sorry we could not locate %s") % str(path))
            return False

        if (os.path.isfile(path)):
            return path

    def getImageData(self, xlink):
        """
        Read, decode and return data of embedded image
        """
        comma = xlink.find(',')
        data = ''

        if comma > 0:
            data = base64.decodebytes(xlink[comma:].encode('UTF-8'))
        else:
            inkex.errormsg(_("Failed to read embedded image data."))

        return data

    def getImage(self, node):
        image_element=self.svg.find('.//{http://www.w3.org/2000/svg}image')
        image_string=image_element.get('{http://www.w3.org/1999/xlink}href')
        #find comma position
        i=0
        while i<40:
            if image_string[i]==',':
                break
            i=i+1
        return Image.open(BytesIO(base64.b64decode(image_string[i+1:len(image_string)])))

    def drawFilledRect(self, parent, svgpx):
        """
        Draw rect based on ((x, y), (width,height), ((r,g,b),a)), add to parent
        """
        style = {}
        pos = svgpx[0]
        dim = svgpx[1]
        rgb = svgpx[2][0]
        alpha = svgpx[2][1]

        style['stroke'] = 'none'

        if len(rgb) == 3:
            # fill: rgb tuple
            style['fill'] = '#%02x%02x%02x' % (rgb[0], rgb[1], rgb[2])
        elif len(rgb) == 1:
            # fill: color name, or 'none'
            style['fill'] = rgb[0]
        else:
            # fill: 'Unset' (no fill defined)
            pass

        if alpha < 255:
            # only write 'fill-opacity' for non-default value
            style['fill-opacity'] = '%s' % round(alpha/255.0, 8)

        rect_attribs = {'x': str(pos[0]),
                        'y': str(pos[1]),
                        'width': str(dim[0]),
                        'height': str(dim[1]),
                        'style': str(inkex.Style(style)), }

        rect = etree.SubElement(parent, inkex.addNS('rect', 'svg'), rect_attribs)

        return rect

    def vectorizeImage(self, node):
        """
        Parse RGBA values of linked bitmap image, create a group and
        draw the rectangles (SVG pixels) inside the new group
        """
        image = self.getImage(node)

        if image:
            # init, set limit (default: 256)
            pixel2svg_max = self.options.maxsize

            if self.options.verbose:
                inkex.debug("ID: %s" % node.get('id'))
                inkex.debug("Image size:\t%dx%d" % image.size)
                inkex.debug("Image format:\t%s" % image.format)
                inkex.debug("Image mode:\t%s" % image.mode)
                inkex.debug("Image info:\t%s" % image.info)

                if (image.mode == 'P' and 'transparency' in image.info):
                    inkex.debug(
                        "Note: paletted image with an alpha channel is handled badly with " +
                        "current PIL:\n" +
                        "<http://stackoverflow.com/questions/12462548/pil-image-mode-p-rgba>")
                elif not image.mode in ('RGBA', 'LA'):
                    inkex.debug("No alpha channel or transparency found")

            image = image.convert("RGBA")
            (width, height) = image.size

            if width <= pixel2svg_max and height <= pixel2svg_max:

                # color trace modes
                trace_color = []
                if self.options.color:
                    trace_color = hex_to_int_color(self.options.color)

                # get RGBA data
                rgba_values = list(image.getdata())

                # create group
                nodeParent = node.getparent()
                nodeIndex = nodeParent.index(node)
                pixel2svg_group = etree.Element(inkex.addNS('g', 'svg'))
                pixel2svg_group.set('id', "%s_pixel2svg" % node.get('id'))
                nodeParent.insert(nodeIndex+1, pixel2svg_group)

                # move group beside original image
                if self.options.offset_image:
                    pixel2svg_offset = width
                else:
                    pixel2svg_offset = 0.0
                pixel2svg_translate = ('translate(%s, %s)' %
                                       (float(node.get('x') or 0.0) + pixel2svg_offset,
                                        node.get('y') or 0.0))
                pixel2svg_group.set('transform', pixel2svg_translate)

                # draw bbox rectangle at the bottom of group
                pixel2svg_bbox_fill = ('none', )
                pixel2svg_bbox_alpha = 255
                pixel2svg_bbox = ((0, 0),
                                  (width * self.options.squaresize,
                                   height * self.options.squaresize),
                                  (pixel2svg_bbox_fill, pixel2svg_bbox_alpha))
                self.drawFilledRect(pixel2svg_group, pixel2svg_bbox)

                # reverse list (performance), pop last one instead of first
                rgba_values.reverse()
                # loop through pixels (per row)
                rowcount = 0
                while rowcount < height:
                    colcount = 0
                    while colcount < width:
                        rgba_tuple = rgba_values.pop()
                        # Omit transparent pixels
                        if rgba_tuple[3] > 0:
                            # color options
                            do_trace = True
                            if (self.options.color_mode != "all"):
                                if (trace_color == rgba_tuple[:3]):
                                    # colors match
                                    if (self.options.color_mode == "other"):
                                        do_trace = False
                                else:
                                    # colors don't match
                                    if (self.options.color_mode == "this"):
                                        do_trace = False
                            if do_trace:
                                # position
                                svgpx_x = colcount * self.options.squaresize
                                svgpx_y = rowcount * self.options.squaresize
                                # dimension + overlap
                                svgpx_size = self.options.squaresize + self.options.overlap
                                # get color, ignore alpha
                                svgpx_rgb = rgba_tuple[:3]
                                svgpx_a = 255
                                # transparency
                                if self.options.transparency:
                                    svgpx_a = rgba_tuple[3]
                                svgpx = ((svgpx_x, svgpx_y),
                                         (svgpx_size, svgpx_size),
                                         (svgpx_rgb, svgpx_a)
                                         )
                                # draw square in group
                                self.drawFilledRect(pixel2svg_group, svgpx)
                        colcount = colcount + 1
                    rowcount = rowcount + 1

                # all done
                if DEBUG:
                    inkex.debug("All rects drawn.")

                if self.options.delete_image:
                    nodeParent.remove(node)

            else:
                # bail out with larger images
                inkex.errormsg(_(
                    "Bailing out: this extension is not intended for large images.\n" +
                    "The current limit is %spx for either dimension of the bitmap image."
                    % pixel2svg_max))
                sys.exit(0)

            # clean-up?
            if DEBUG:
                inkex.debug("Done.")

        else:
            inkex.errormsg(_("Bailing out: No supported image file or data found"))
            sys.exit(1)

    def effect(self):
        """
        Pixel2SVG - Convert the pixels of bitmap images to SVG rects
        """
        found_image = False
        if (self.options.ids):
            for node in self.svg.selected.values():
                if node.tag == inkex.addNS('image', 'svg'):
                    found_image = True
                    self.vectorizeImage(node)

        if not found_image:
            inkex.errormsg(_("Please select one or more bitmap image(s) for Pixel2SVG"))
            sys.exit(0)

if __name__ == '__main__':
    Pixel2SVG().run()