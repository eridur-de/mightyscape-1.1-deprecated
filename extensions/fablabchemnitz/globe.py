#!/usr/bin/env python3
'''
Globe rendering extension for Inkscape
Copyright (C) 2009 Gerrit Karius

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


About the Globe rendering extension:



'''
from __future__ import division
import inkex
from math import *
from lxml import etree

#TODO: put the globe in the center of the view canvas

def draw_ellipse_rotated(cx,cy,rx,ry, width, fill, name, parent, rotationAngle):
    a = cos(rotationAngle)
    b = sin(rotationAngle)
    c = -sin(rotationAngle)
    d = cos(rotationAngle)
    e = -(a*cx + c*cy) + cx
    f = -(b*cx + d*cy) + cy
    style = { 'stroke': '#000000', 'stroke-width':str(width), 'fill':fill}
    if rx == 0:
        x1 = cx 
        x2 = cx
        y1 = cy - ry
        y2 = cy + ry
        circle_attribs = {'style':str(inkex.Style(style)),
                          inkex.addNS('label','inkscape'):name,
                          'd':'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2),
                          'transform':'matrix('+str(a)+','+str(b)+','+str(c)+','+str(d)+','+str(e)+','+str(f)+')'}
    elif ry == 0: 
        x1 = cx - rx 
        x2 = cx + rx
        y1 = cy
        y2 = cy
        circle_attribs = {'style':str(inkex.Style(style)),
                          inkex.addNS('label','inkscape'):name,
                          'd':'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2),
                          'transform':'matrix('+str(a)+','+str(b)+','+str(c)+','+str(d)+','+str(e)+','+str(f)+')'}                           
    else:
        circle_attribs = {'style':str(inkex.Style(style)),
                          inkex.addNS('label','inkscape'):name,
                          inkex.addNS('cx','sodipodi'):str(cx),
                          inkex.addNS('cy','sodipodi'):str(cy),
                          inkex.addNS('rx','sodipodi'):str(rx),
                          inkex.addNS('ry','sodipodi'):str(ry),
                          inkex.addNS('type','sodipodi'):'arc',
                          'transform':'matrix('+str(a)+','+str(b)+','+str(c)+','+str(d)+','+str(e)+','+str(f)+')'}
    etree.SubElement(parent, inkex.addNS('path','svg'), circle_attribs)

def draw_ellipse_segment_rotated(cx,cy,rx,ry, width, fill, name, parent, rotationAngle, segmentAngleStart, segmentAngleEnd):
    a = cos(rotationAngle)
    b = sin(rotationAngle)
    c = -sin(rotationAngle)
    d = cos(rotationAngle)
    e = -(a*cx + c*cy) + cx
    f = -(b*cx + d*cy) + cy
    style = { 'stroke': '#000000', 'stroke-width':str(width), 'fill':fill}
    if rx == 0:
        x1 = cx 
        x2 = cx
        y1 = cy - ry
        y2 = cy + ry
        circle_attribs = {'style':str(inkex.Style(style)),
                          inkex.addNS('label','inkscape'):name,
                          'd':'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2),
                          'transform':'matrix('+str(a)+','+str(b)+','+str(c)+','+str(d)+','+str(e)+','+str(f)+')'}
    elif ry == 0: 
        x1 = cx - rx 
        x2 = cx + rx
        y1 = cy
        y2 = cy
        circle_attribs = {'style':str(inkex.Style(style)),
                          inkex.addNS('label','inkscape'):name,
                          'd':'M '+str(x1)+','+str(y1)+' L '+str(x2)+','+str(y2),
                          'transform':'matrix('+str(a)+','+str(b)+','+str(c)+','+str(d)+','+str(e)+','+str(f)+')'}     
    else:  
        circle_attribs = {'style':str(inkex.Style(style)),
                          inkex.addNS('label','inkscape'):name,
                          inkex.addNS('cx','sodipodi'):str(cx),
                          inkex.addNS('cy','sodipodi'):str(cy),
                          inkex.addNS('rx','sodipodi'):str(rx),
                          inkex.addNS('ry','sodipodi'):str(ry),
                          inkex.addNS('start','sodipodi'):str(segmentAngleStart),
                          inkex.addNS('end','sodipodi'):str(segmentAngleEnd),
                          inkex.addNS('open','sodipodi'):'true',
                          inkex.addNS('type','sodipodi'):'arc',
                          'transform':'matrix('+str(a)+','+str(b)+','+str(c)+','+str(d)+','+str(e)+','+str(f)+')'}
    etree.SubElement(parent, inkex.addNS('path','svg'), circle_attribs)


class Globe(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--longitudeLineCount", type=int, default=15, help="Number of longitude lines")
        pars.add_argument("--latitudeLineCount", type=int, default=15, help="Number of latitude lines")
        pars.add_argument("--rotationXDegrees", type=float, default=45, help="Rotation around X axis (degrees)")
        pars.add_argument("--rotationYDegrees", type=float, default=-45, help="Rotation around Y axis (degrees)")
        pars.add_argument("--isSeeThrough", type=inkex.Boolean, default=False, help="Is the globe see-through")
        
    def effect(self):

        name = 'globe'

        # globe fill and stroke style
        fill = 'none'
        width = 1

        #input parameters - globe center and radius
        cyb = 500.0
        cxb = 500.0 
        rb  = 100.0 

        longitudeRotationAngleDegrees = float(self.options.rotationYDegrees)
        tiltForwardAngleDegrees       = float(self.options.rotationXDegrees)

        # inputs range fixing
        # tiltForwardAngle is adjusted to vary from 0 <= angle < pi
        if tiltForwardAngleDegrees >= 180.0:
            tiltForwardAngleDegrees -= 180.0
        elif tiltForwardAngleDegrees < 180.0:
            tiltForwardAngleDegrees += 180.0 

        if self.options.longitudeLineCount > 0:
            angleSpacingLongitudeLinesDegrees = 180.0 / float(self.options.longitudeLineCount);
            # longitudeAngle is wrapped to vary from 0 <= angle < angleSpacingLongitudeLines.
            while longitudeRotationAngleDegrees < 0:
                longitudeRotationAngleDegrees += angleSpacingLongitudeLinesDegrees
            while longitudeRotationAngleDegrees >= angleSpacingLongitudeLinesDegrees:
                longitudeRotationAngleDegrees -= angleSpacingLongitudeLinesDegrees                   

        # units conversion from degrees to radians
        tiltForwardAngle = tiltForwardAngleDegrees * pi / 180.0;
        initialAngleLongitudeLines = longitudeRotationAngleDegrees * pi / 180.0

        # derived parameters
        rxb = rb
        ryb = rb

        #
        # start drawing
        #

        # create the group to put the globe in
        group_attribs = {inkex.addNS('label','inkscape'):name}
        parent = etree.SubElement(self.svg.get_current_layer(), 'g', group_attribs)
		
        # draw the outside border
        draw_ellipse_rotated(cxb,cyb,rxb,ryb, width, fill, 'border', parent, 0)

        # draw the longitude lines
        # elipse #0 corresponds to ring on the front (visible only as a straight vertical line)
        # elipse #n-1 corresponds to the ring that is almost 180 degrees away
        # elipse #n/2 corresponds to ring around the side (overlaps with globe boundary) (only if n is even)
        if self.options.longitudeLineCount > 0:
            angleSpacingLongitudeLines = pi / float(self.options.longitudeLineCount);
            yOfPole = ryb * cos(tiltForwardAngle)
            for i in range(0, self.options.longitudeLineCount):
                lineName = 'longitude' + str(i)
                # longitudeAngle is always from 0 to pi.
                # rotation angle is always from 0 to pi.
                # rx is never negative.
                longitudeAngle = ((float(i)) * angleSpacingLongitudeLines) + initialAngleLongitudeLines
                if tiltForwardAngleDegrees == 0 or tiltForwardAngleDegrees == 180.0:
                    if longitudeAngle < pi/2:
                        rotationAngle = 0.0
                    else:
                        rotationAngle = pi
                    rx = rxb * sin(longitudeAngle)

                    arcStart = pi/2
                    arcEnd = -pi/2

                else:
                    rotationAngle = acos(cos(longitudeAngle) / sqrt(1 - pow(sin(longitudeAngle)*cos(tiltForwardAngle), 2)))
                    rx = rxb  * sin(longitudeAngle) * cos(tiltForwardAngle)
                    if rx < 0:
                        rx = -rx
                        arcStart = -pi/2
                        arcEnd = pi/2
                    else:
                        arcStart = pi/2
                        arcEnd = -pi/2
                ry = ryb
                cx = cxb
                cy = cyb
                if self.options.isSeeThrough:
                    draw_ellipse_rotated(cx,cy,rx,ry, width, fill, lineName, parent, rotationAngle)
                else:
                    draw_ellipse_segment_rotated(cx,cy,rx,ry, width, fill, lineName, parent, rotationAngle, arcStart, arcEnd)

        # draw the latitude lines
        # elipse #0 corresponds to ring closest to north pole.
        # elipse #n-1 corresponds to ring closest to south pole.
        # equator is ring #(n-1)/2 (only if n is odd). 
        if self.options.latitudeLineCount > 0:
            angleSpacingLatitudeLines  = pi / (1.0 + float(self.options.latitudeLineCount));
            yOfPole = ryb * cos(tiltForwardAngle)
            for i in range(0, self.options.latitudeLineCount):
                lineName = 'latitude' + str(i)
                # angleOfCurrentLatitudeLine is always from 0 to pi.
                # tiltForwardAngle is always from 0 to pi.
                # ry is never negative.                
                angleOfCurrentLatitudeLine = float(i + 1) * angleSpacingLatitudeLines
                rx = rxb * sin(angleOfCurrentLatitudeLine)
                ry = rx * sin(tiltForwardAngle)
                cx = cxb
                cy = cyb - yOfPole*cos(angleOfCurrentLatitudeLine)
                if self.options.isSeeThrough:
                    #inkex.utils.debug(cx)
                    #inkex.utils.debug(cy)
                    #inkex.utils.debug(rx)
                    #inkex.utils.debug(ry)
                    #inkex.utils.debug(width)
                    #inkex.utils.debug(fill)
                    #inkex.utils.debug(lineName)
                    #inkex.utils.debug(parent)
                    draw_ellipse_rotated(cx,cy,rx,ry, width, fill, lineName, parent, 0)
                else:
                    if tiltForwardAngle > pi/2:
                        # tilt away from viewaer
                        if rxb * cos(angleOfCurrentLatitudeLine) / cos(tiltForwardAngle) > rxb:
                            # elipse is not visible
                            pass
                        else:
                            if rxb * cos(angleOfCurrentLatitudeLine) / cos(tiltForwardAngle) < -rxb:
                                # elipse is all visible
                                segmentAngle = pi
                            else:
                                # elipse is only partially visible
                                segmentAngle = acos(max(-1,min(1, -tan(tiltForwardAngle) / tan(angleOfCurrentLatitudeLine))))
                            draw_ellipse_segment_rotated(cx,cy,rx,ry, width, fill, lineName, parent, 0, pi/2+segmentAngle, pi/2-segmentAngle)
                    else:
                        # tilt towards viewer
                        if rxb * cos(angleOfCurrentLatitudeLine) / cos(tiltForwardAngle) < -rxb:
                            # elipse is not visible
                            pass
                        else:
                            if rxb * cos(angleOfCurrentLatitudeLine) / cos(tiltForwardAngle) > rxb:
                                # elipse is all visible
                                segmentAngle = pi
                            else:
                                # elipse is only partially visible
                                segmentAngle = acos(max(-1,min(1, tan(tiltForwardAngle) / tan(angleOfCurrentLatitudeLine))))
                            draw_ellipse_segment_rotated(cx,cy,rx,ry, width, fill, lineName, parent, 0, -pi/2+segmentAngle, -pi/2-segmentAngle)			
if __name__ == '__main__':
    Globe().run()