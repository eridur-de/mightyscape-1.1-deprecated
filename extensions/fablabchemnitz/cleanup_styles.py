#!/usr/bin/env python3
'''
Copyright (C) 2013 Matthew Dockrey  (gfish @ cyphertext.net)

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

Based on 
- coloreffect.py by Jos Hirth and Aaron C. Spike
- cleanup.py (https://github.com/attoparsec/inkscape-extensions) by attoparsec

Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Last Patch: 12.04.2021
License: GNU GPL v3

Notes: 
 - This extension does not check if attributes contain duplicates properties like "opacity:1;fill:#393834;fill-opacity:1;opacity:1;fill:#393834;fill-opacity:1". We assume the SVG syntax is correct
'''

import inkex
import re

class Cleanup(inkex.EffectExtension):

    groups = []
    
    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--mode", default="Lines", help="Join paths with lines or polygons")
        pars.add_argument("--dedicated_style_attributes", default="ignore", help="Handling of dedicated style attributes")
        pars.add_argument("--stroke_width_override", type=inkex.Boolean, default=False, help="Override stroke width")
        pars.add_argument("--stroke_width", type=float, default=0.100, help="Stroke width")
        pars.add_argument("--stroke_width_units", default="mm", help="Stroke width unit")
        pars.add_argument("--stroke_opacity_override", type=inkex.Boolean, default=False, help="Override stroke opacity")
        pars.add_argument("--stroke_opacity", type=float, default="100.0", help="Stroke opacity (%)")
        pars.add_argument("--reset_stroke_attributes", type=inkex.Boolean, help="Remove stroke style attributes 'stroke-dasharray', 'stroke-dashoffset', 'stroke-linejoin', 'stroke-linecap', 'stroke-miterlimit'")
        pars.add_argument("--reset_fill_attributes", type=inkex.Boolean, help="Sets 'fill:none;fill-opacity:1;' to style attribute")
        pars.add_argument("--apply_hairlines", type=inkex.Boolean, help="Adds 'vector-effect:non-scaling-stroke;' and '-inkscape-stroke:hairline;' Hint: stroke-width is kept in background. All hairlines still have a valued width.")
        pars.add_argument("--apply_black_strokes", type=inkex.Boolean, help="Adds 'stroke:#000000;' to style attribute")
        pars.add_argument("--remove_group_styles", type=inkex.Boolean, help="Remove styles from groups")
        
    def effect(self):
        if len(self.svg.selected) == 0:
            self.getAttribs(self.document.getroot())
        else:
            for element in self.svg.selected.values():
                self.getAttribs(element)
        #finally remove the styles from collected groups (if enabled)
        if self.options.remove_group_styles is True:
            for group in self.groups:
                if group.attrib.has_key('style') is True:
                    group.attrib.pop('style')

    def getAttribs(self, node):
        self.changeStyle(node)
        for child in node:
            self.getAttribs(child)

    #stroke and fill styles can be included in style attribute or they can exist separately (can occure in older SVG files). We do not parse other attributes than style
    def changeStyle(self, node):
    
        #we check/modify the style of all shapes (not groups)
        if isinstance(node, inkex.ShapeElement) and not isinstance(node, inkex.Group):
            # the final styles applied to this element (with influence from top level elements like groups)
            composed_style = node.composed_style()
            composedStyleAttributes = str(composed_style).split(';') #array
            composedStyleAttributesDict = {}
            if len(composed_style) > 0: #Style "composed_style" might contain just empty '' string which will lead to failing dict update
                for composedStyleAttribute in composedStyleAttributes:
                    composedStyleAttributesDict.update({'{}'.format(composedStyleAttribute.split(':')[0]): composedStyleAttribute.split(':')[1]})
           
            #three options to handle dedicated attributes (attributes not in the "style" attribute, but separate):
            # - just delete all dedicated properties
            # - merge dedicated properties, and prefer them over those from composed style
            # - merge dedicated properties, but prefer properties from composed style
            dedicatedStyleAttributesDict = {}
            popDict = []
            popDict.extend(['stroke', 'stroke-opacity', 'stroke-width', 'stroke-dasharray', 'stroke-dashoffset', 'stroke-linecap', 'stroke-linejoin', 'stroke-miterlimit', 'fill', 'fill-opacity'])
            for popItem in popDict:
                if node.attrib.has_key(str(popItem)):
                    dedicatedStyleAttributesDict.update({'{}'.format(popItem): node.get(popItem)})
                    node.attrib.pop(popItem)
 
            #inkex.utils.debug("composedStyleAttributesDict = " + str(composedStyleAttributesDict))
            #inkex.utils.debug("dedicatedStyleAttributesDict = " + str(dedicatedStyleAttributesDict))
 
            if self.options.dedicated_style_attributes == 'prefer_dedicated':
                composedStyleAttributesDict.update(dedicatedStyleAttributesDict)
                node.set('style', composedStyleAttributesDict)
            elif self.options.dedicated_style_attributes == 'prefer_composed':
                dedicatedStyleAttributesDict.update(composedStyleAttributesDict)
                node.set('style', dedicatedStyleAttributesDict)
            elif self.options.dedicated_style_attributes == 'ignore':
                pass

            # now parse the style with possibly merged dedicated attributes modded style attribute (dedicatedStyleAttributes)
            if node.attrib.has_key('style') is False:
                node.set('style', 'stroke:#000000;') #we add basic stroke color black. We cannot set to empty value or just ";" because it will not update properly
            style = node.get('style')
            
            #add missing style attributes if required
            if style.endswith(';') is False:
                style += ';'
            if re.search('(;|^)stroke:(.*?)(;|$)', style) is None: #if "stroke" is None, add one. We need to distinguish because there's also attribute "-inkscape-stroke" that's why we check starting with ^ or ;
                style += 'stroke:none;'
            if self.options.stroke_width_override is True and "stroke-width:" not in style:
                style += 'stroke-width:{:1.4f};'.format(self.svg.unittouu(str(self.options.stroke_width) + self.options.stroke_width_units))
            if self.options.stroke_opacity_override is True and "stroke-opacity:" not in style:
                style += 'stroke-opacity:{:1.1f};'.format(self.options.stroke_opacity / 100)

            if self.options.apply_hairlines is True:
                if "vector-effect:non-scaling-stroke" not in style:
                    style += 'vector-effect:non-scaling-stroke;'
                if "-inkscape-stroke:hairline" not in style:
                    style += '-inkscape-stroke:hairline;'
               
            if re.search('fill:(.*?)(;|$)', style) is None: #if "fill" is None, add one.
                style += 'fill:none;'
                                   
            #then parse the content and check what we need to adjust   
            declarations = style.split(';')
            for i, decl in enumerate(declarations):
                parts = decl.split(':', 2)
                if len(parts) == 2:
                    (prop, val) = parts
                    prop = prop.strip().lower()
                    if prop == 'stroke-width' and self.options.stroke_width_override is True:
                        new_val = self.svg.unittouu(str(self.options.stroke_width) + self.options.stroke_width_units)
                        declarations[i] = prop + ':{:1.4f}'.format(new_val)
                    if prop == 'stroke-opacity' and self.options.stroke_opacity_override is True:
                        new_val = self.options.stroke_opacity / 100
                        declarations[i] = prop + ':{:1.1f}'.format(new_val)
                    if self.options.reset_stroke_attributes is True:
                        if prop == 'stroke-dasharray':
                            declarations[i] = ''
                        if prop == 'stroke-dashoffset':
                            declarations[i] = ''
                        if prop == 'stroke-linejoin':
                            declarations[i] = ''
                        if prop == 'stroke-linecap':
                            declarations[i] = ''
                        if prop == 'stroke-miterlimit':
                            declarations[i] = ''
                    if self.options.apply_black_strokes is True:
                        if prop == 'stroke':
                            if val == 'none':
                                new_val = '#000000'
                                declarations[i] = prop + ':' + new_val
                    if self.options.reset_fill_attributes is True:
                        if prop == 'fill':
                                new_val = 'none'
                                declarations[i] = prop + ':' + new_val
                        if prop == 'fill-opacity':
                                new_val = '1'
                                declarations[i] = prop + ':' + new_val
                    if self.options.apply_hairlines is False:
                        if prop == '-inkscape-stroke':
                            if val == 'hairline':
                                del declarations[i]
                        if prop == 'vector-effect':
                            if val == 'non-scaling-stroke':
                                del declarations[i]
            node.set('style', ';'.join(declarations))
            
        # if element is group we add it to collection to remove it's style after parsing all selected items
        elif isinstance(node, inkex.ShapeElement) and isinstance(node, inkex.Group):
            self.groups.append(node)

if __name__ == '__main__':
    Cleanup().run()