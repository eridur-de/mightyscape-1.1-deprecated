#!/usr/bin/env python3
#
# License: GPL2
# Copyright Mark "Klowner" Riedesel
# https://github.com/Klowner/inkscape-applytransforms
#
import copy
import math
from lxml import etree
import inkex
from inkex.paths import CubicSuperPath, Path
from inkex.transforms import Transform
from inkex.styles import Style

NULL_TRANSFORM = Transform([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


class ApplyTransform(inkex.EffectExtension):
    def __init__(self):
        super(ApplyTransform, self).__init__()

    def effect(self):
        if self.svg.selected:
            for id, shape in self.svg.selected.items():
                self.recursiveFuseTransform(shape)
        else:
            self.recursiveFuseTransform(self.document.getroot())

    @staticmethod
    def objectToPath(node):
        if node.tag == inkex.addNS('g', 'svg'):
            return node

        if node.tag == inkex.addNS('path', 'svg') or node.tag == 'path':
            for attName in node.attrib.keys():
                if ("sodipodi" in attName) or ("inkscape" in attName):
                    del node.attrib[attName]
            return node

        return node

    def scaleStrokeWidth(self, node, transf):
        if 'style' in node.attrib:
            style = node.attrib.get('style')
            style = dict(Style.parse_str(style))
            update = False

            if 'stroke-width' in style:
                try:
                    stroke_width = float(style.get('stroke-width').strip().replace("px", ""))
                    stroke_width *= math.sqrt(abs(transf.a * transf.d))
                    style['stroke-width'] = str(stroke_width)
                    update = True
                except AttributeError:
                    pass

            if update:
                node.attrib['style'] = Style(style).to_str()

    def recursiveFuseTransform(self, node, transf=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]):

        transf = Transform(transf) * Transform(node.get("transform", None)) #a, b, c, d = linear transformations / e, f = translations

        if 'transform' in node.attrib:
            del node.attrib['transform']

        node = ApplyTransform.objectToPath(node)

        if transf == NULL_TRANSFORM:
            # Don't do anything if there is effectively no transform applied
            # reduces alerts for unsupported nodes
            pass
        elif 'd' in node.attrib:
            d = node.get('d')
            p = CubicSuperPath(d)
            p = Path(p).to_absolute().transform(transf, True)
            node.set('d', str(Path(CubicSuperPath(p).to_path())))

            self.scaleStrokeWidth(node, transf)

        elif node.tag in [inkex.addNS('polygon', 'svg'),
                          inkex.addNS('polyline', 'svg')]:
            points = node.get('points')
            points = points.strip().split(' ')
            for k, p in enumerate(points):
                if ',' in p:
                    p = p.split(',')
                    p = [float(p[0]), float(p[1])]
                    p = transf.apply_to_point(p)
                    p = [str(p[0]), str(p[1])]
                    p = ','.join(p)
                    points[k] = p
            points = ' '.join(points)
            node.set('points', points)

            self.scaleStrokeWidth(node, transf)

        elif node.tag in [inkex.addNS("ellipse", "svg"), inkex.addNS("circle", "svg")]:

            def isequal(a, b):
                return abs(a - b) <= transf.absolute_tolerance

            if node.TAG == "ellipse":
                rx = float(node.get("rx"))
                ry = float(node.get("ry"))
            else:
                rx = float(node.get("r"))
                ry = rx

            cx = float(node.get("cx"))
            cy = float(node.get("cy"))
            sqxy1 = (cx - rx, cy - ry)
            sqxy2 = (cx + rx, cy - ry)
            sqxy3 = (cx + rx, cy + ry)
            newxy1 = transf.apply_to_point(sqxy1)
            newxy2 = transf.apply_to_point(sqxy2)
            newxy3 = transf.apply_to_point(sqxy3)

            node.set("cx", (newxy1[0] + newxy3[0]) / 2)
            node.set("cy", (newxy1[1] + newxy3[1]) / 2)
            edgex = math.sqrt(
                abs(newxy1[0] - newxy2[0]) ** 2 + abs(newxy1[1] - newxy2[1]) ** 2
            )
            edgey = math.sqrt(
                abs(newxy2[0] - newxy3[0]) ** 2 + abs(newxy2[1] - newxy3[1]) ** 2
            )

            if not isequal(edgex, edgey) and (
                node.TAG == "circle"
                or not isequal(newxy2[0], newxy3[0])
                or not isequal(newxy1[1], newxy2[1])
            ):
                inkex.utils.errormsg(
                    "Warning: Shape %s (%s) is approximate only, try Object to path first for better results"
                    % (node.TAG, node.get("id"))
                )

            if node.TAG == "ellipse":
                node.set("rx", edgex / 2)
                node.set("ry", edgey / 2)
            else:
                node.set("r", edgex / 2)

        elif node.tag == inkex.addNS("use", "svg"):    
            href = None
            old_href_key = '{http://www.w3.org/1999/xlink}href'
            new_href_key = 'href'
            if node.attrib.has_key(old_href_key) is True: # {http://www.w3.org/1999/xlink}href (which gets displayed as 'xlink:href') attribute is deprecated. the newer attribute is just 'href'
                href = node.attrib.get(old_href_key)
                #node.attrib.pop(old_href_key)
            if node.attrib.has_key(new_href_key) is True:
                href = node.attrib.get(new_href_key) #we might overwrite the previous deprecated xlink:href but it's okay
                #node.attrib.pop(new_href_key)

            #get the linked object from href attribute
            linkedObject = self.document.getroot().xpath("//*[@id = '%s']" % href.lstrip('#')) #we must remove hashtag symbol
            linkedObjectCopy = copy.copy(linkedObject[0])
            objectType = linkedObject[0].tag
            
            if objectType == inkex.addNS("image", "svg"):
                mask = None #image might have an alpha channel
                new_mask_id = self.svg.get_unique_id("mask")
                newMask = None
                if node.attrib.has_key('mask') is True:
                    mask = node.attrib.get('mask')
                    #node.attrib.pop('mask')

                #get the linked mask from mask attribute. We remove the old and create a new
                if mask is not None:
                    linkedMask = self.document.getroot().xpath("//*[@id = '%s']" % mask.lstrip('url(#').rstrip(')')) #we must remove hashtag symbol
                    linkedMask[0].getparent().remove(linkedMask[0])
                    maskAttributes = {'id': new_mask_id}
                    newMask = etree.SubElement(self.document.getroot(), inkex.addNS('mask', 'svg'), maskAttributes)
            
                width = float(linkedObjectCopy.get('width')) * transf.a
                height = float(linkedObjectCopy.get('height')) * transf.d
                linkedObjectCopy.set('width', '{:1.6f}'.format(width))
                linkedObjectCopy.set('height', '{:1.6f}'.format(height))
                linkedObjectCopy.set('x', '{:1.6f}'.format(transf.e))
                linkedObjectCopy.set('y', '{:1.6f}'.format(transf.f))
                if newMask is not None:
                    linkedObjectCopy.set('mask', 'url(#' + new_mask_id + ')')
                    maskRectAttributes = {'x': '{:1.6f}'.format(transf.e), 'y': '{:1.6f}'.format(transf.f), 'width': '{:1.6f}'.format(width), 'height': '{:1.6f}'.format(height), 'style':'fill:#ffffff;'}
                    maskRect = etree.SubElement(newMask, inkex.addNS('rect', 'svg'), maskRectAttributes)
            else:
                self.recursiveFuseTransform(linkedObjectCopy, transf)

            self.document.getroot().append(linkedObjectCopy) #for each svg:use we append a copy to the document root
            node.getparent().remove(node) #then we remove the use object

        elif node.tag in [inkex.addNS('rect', 'svg'),
                          inkex.addNS('text', 'svg'),
                          inkex.addNS('image', 'svg')]:
            inkex.utils.errormsg(
                "Shape %s (%s) not yet supported, try Object to path first"
                % (node.TAG, node.get("id"))
            )

        else:
            # e.g. <g style="...">
            self.scaleStrokeWidth(node, transf)

        for child in node.getchildren():
            self.recursiveFuseTransform(child, transf)

if __name__ == '__main__':
    ApplyTransform().run()