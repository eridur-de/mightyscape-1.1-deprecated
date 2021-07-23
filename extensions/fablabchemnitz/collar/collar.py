#!/usr/bin/env python3
#
# Copyright (C) [2021] [Joseph Zakar], [observing@gmail.com]
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
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
"""
Given a set of parameters for two polygons, this program generates paper
models of (1) the two polygons; (2) a collar (divided into segments if desired)
represented by a strip with tabs and score lines; and (3) wrapper(s) for
covering the tabbed strip(s).
"""

import inkex
from inkex import Color
import math
import copy

class pathStruct(object):
    
    
    def __init__(self):
        self.id="path0000"
        self.path=[]
        self.enclosed=False
        
        
    def __str__(self):
        return self.path
    
class pnPoint(object):
   # This class came from https://github.com/JoJocoder/PNPOLY
   
   
    def __init__(self,p):
        self.p=p
        
        
    def __str__(self):
        return self.p
    
    
 

    def InPolygon(self,polygon,BoundCheck=False):
        inside=False
        if BoundCheck:
            minX=polygon[0][0]
            maxX=polygon[0][0]
            minY=polygon[0][1]
            maxY=polygon[0][1]
            for p in polygon:
                minX=min(p[0],minX)
                maxX=max(p[0],maxX)
                minY=min(p[1],minY)
                maxY=max(p[1],maxY)
            if self.p[0]<minX or self.p[0]>maxX or self.p[1]<minY or self.p[1]>maxY:
                return False
        j=len(polygon)-1
        for i in range(len(polygon)):
            if ((polygon[i][1]>self.p[1])!=(polygon[j][1]>self.p[1]) and (self.p[0]<(polygon[j][0]-polygon[i][0])*(self.p[1]-polygon[i][1])/( polygon[j][1] - polygon[i][1] ) + polygon[i][0])):
                    inside =not inside
            j=i
        return inside


class Collar(inkex.EffectExtension):
    
    
    def add_arguments(self, pars):
        pars.add_argument("--usermenu")
        pars.add_argument("--unit", default="in",help="Dimensional units")
        pars.add_argument("--polysides", type=int, default=6,help="Number of Polygon Sides")
        pars.add_argument("--poly1size", type=float, default=5.0, help="Size of Polygon 1 in dimensional units")
        pars.add_argument("--poly2size", type=float, default=3.0, help="Size of Polygon 2 in dimensional units")
        pars.add_argument("--collarheight", type=float, default=2.0, help="Height of collar in dimensional units")
        pars.add_argument("--collarparts", type=int, default=1,help="Number of parts to divide collar into")
        pars.add_argument("--dashlength", type=float, default=0.1, help="Length of dashline in dimensional units (zero for solid line)")
        pars.add_argument("--tabangle", type=float, default=45.0, help="Angle of tab edges in degrees")
        pars.add_argument("--tabheight", type=float, default=0.4, help="Height of tab in dimensional units")
        pars.add_argument("--generate_decorative_wrapper", type=inkex.Boolean, default=False, help="Generate decorative wrapper")
        pars.add_argument("--cosmetic_dash_style", type=inkex.Boolean, default=False, help="Cosmetic dash lines")
        pars.add_argument("--color_solid", type=Color, default='4278190335', help="Solid line color")
        pars.add_argument("--color_dash", type=Color, default='65535', help="Solid line dash")


    #draw SVG line segment(s) between the given (raw) points
    def drawline(self, dstr, name, parent, sstr=None):
        line_style   = {'stroke':self.options.color_solid,'stroke-width':'0.25','fill':'#eeeeee'}
        if sstr == None:
            stylestr = str(inkex.Style(line_style))
        else:
            stylestr = sstr
        el = parent.add(inkex.PathElement())
        el.path = dstr
        el.style = stylestr
        el.label = name
        
    def makepoly(self, toplength, numpoly):
      r = toplength/(2*math.sin(math.pi/numpoly))
      pstr = ''
      for ppoint in range(0,numpoly):
         xn = r*math.cos(2*math.pi*ppoint/numpoly)
         yn = r*math.sin(2*math.pi*ppoint/numpoly)
         if ppoint == 0:
            pstr = 'M '
         else:
            pstr += ' L '
         pstr += str(xn) + ',' + str(yn)
      pstr = pstr + ' Z'
      return pstr

    # Thanks to Gabriel Eng for his python implementation of https://en.wikipedia.org/wiki/Line%E2%80%93line_intersection
    def findIntersection(self, x1,y1,x2,y2,x3,y3,x4,y4):
        px= ( (x1*y2-y1*x2)*(x3-x4)-(x1-x2)*(x3*y4-y3*x4) ) / ( (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4) ) 
        py= ( (x1*y2-y1*x2)*(y3-y4)-(y1-y2)*(x3*y4-y3*x4) ) / ( (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4) )
        return px, py

    def insidePath(self, path, p):
        point = pnPoint((p.x, p.y))
        pverts = []
        for pnum in path:
            pverts.append((pnum.x, pnum.y))
        isInside = point.InPolygon(pverts, True)
        return isInside # True if point p is inside path

    def makescore(self, pt1, pt2, dashlength):
        # Draws a dashed line of dashlength between two points
        # Dash = dashlength (in inches) space followed by dashlength mark
        # if dashlength is zero, we want a solid line
        apt1 = inkex.paths.Line(0.0,0.0)
        apt2 = inkex.paths.Line(0.0,0.0)
        ddash = ''
        if math.isclose(dashlength, 0.0):
            #inkex.utils.debug("Draw solid dashline")
            ddash = ' M '+str(pt1.x)+','+str(pt1.y)+' L '+str(pt2.x)+','+str(pt2.y)
        else:
            if math.isclose(pt1.y, pt2.y):
                #inkex.utils.debug("Draw horizontal dashline")
                if pt1.x < pt2.x:
                    xcushion = pt2.x - dashlength
                    xpt = pt1.x
                    ypt = pt1.y
                else:
                    xcushion = pt1.x - dashlength
                    xpt = pt2.x
                    ypt = pt2.y
                ddash = ''
                done = False
                while not(done):
                    if (xpt + dashlength*2) <= xcushion:
                        xpt = xpt + dashlength
                        ddash = ddash + ' M ' + str(xpt) + ',' + str(ypt)
                        xpt = xpt + dashlength
                        ddash = ddash + ' L ' + str(xpt) + ',' + str(ypt)
                    else:
                        done = True
            elif math.isclose(pt1.x, pt2.x):
                #inkex.utils.debug("Draw vertical dashline")
                if pt1.y < pt2.y:
                    ycushion = pt2.y - dashlength
                    xpt = pt1.x
                    ypt = pt1.y
                else:
                    ycushion = pt1.y - dashlength
                    xpt = pt2.x
                    ypt = pt2.y
                ddash = ''
                done = False
                while not(done):
                    if(ypt + dashlength*2) <= ycushion:
                        ypt = ypt + dashlength         
                        ddash = ddash + ' M ' + str(xpt) + ',' + str(ypt)
                        ypt = ypt + dashlength
                        ddash = ddash + ' L ' + str(xpt) + ',' + str(ypt)
                    else:
                        done = True
            else:
                #inkex.utils.debug("Draw sloping dashline")
                if pt1.y > pt2.y:
                    apt1.x = pt1.x
                    apt1.y = pt1.y
                    apt2.x = pt2.x
                    apt2.y = pt2.y
                else:
                    apt1.x = pt2.x
                    apt1.y = pt2.y
                    apt2.x = pt1.x
                    apt2.y = pt1.y
                m = (apt1.y-apt2.y)/(apt1.x-apt2.x)
                theta = math.atan(m)
                msign = (m>0) - (m<0)
                ycushion = apt2.y + dashlength*math.sin(theta)
                xcushion = apt2.x + msign*dashlength*math.cos(theta)
                ddash = ''
                xpt = apt1.x
                ypt = apt1.y
                done = False
                while not(done):
                    nypt = ypt - dashlength*2*math.sin(theta)
                    nxpt = xpt - msign*dashlength*2*math.cos(theta)
                    if (nypt >= ycushion) and (((m<0) and (nxpt <= xcushion)) or ((m>0) and (nxpt >= xcushion))):
                        # move to end of space / beginning of mark
                        xpt = xpt - msign*dashlength*math.cos(theta)
                        ypt = ypt - msign*dashlength*math.sin(theta)
                        ddash = ddash + ' M ' + str(xpt) + ',' + str(ypt)
                        # draw the mark
                        xpt = xpt - msign*dashlength*math.cos(theta)
                        ypt = ypt - msign*dashlength*math.sin(theta)
                        ddash = ddash + ' L ' + str(xpt) + ',' + str(ypt)
                    else:
                        done = True
        return ddash

    def detectIntersect(self, x1, y1, x2, y2, x3, y3, x4, y4):
        td = (x1-x2)*(y3-y4)-(y1-y2)*(x3-x4)
        if td == 0:
            # These line segments are parallel
            return False
        t = ((x1-x3)*(y3-y4)-(y1-y3)*(x3-x4))/td
        if (0.0 <= t) and (t <= 1.0):
            return True
        else:
            return False

    def makeTab(self, tpath, pt1, pt2, tabht, taba):
        # tpath - the pathstructure containing pt1 and pt2
        # pt1, pt2 - the two points where the tab will be inserted
        # tabht - the height of the tab
        # taba - the angle of the tab sides
        # returns the two tab points in order of closest to pt1
        tpt1 = inkex.paths.Line(0.0,0.0)
        tpt2 = inkex.paths.Line(0.0,0.0)
        currTabHt = tabht
        currTabAngle = taba
        testAngle = 1.0
        testHt = currTabHt * 0.001
        adjustTab = 0
        tabDone = False
        while not tabDone:
            # Let's find out the orientation of the tab
            if math.isclose(pt1.x, pt2.x):
                # It's vertical. Let's try the right side
                if pt1.y < pt2.y:
                    tpt1.x = pt1.x + testHt
                    tpt2.x = pt2.x + testHt
                    tpt1.y = pt1.y + testHt/math.tan(math.radians(testAngle))
                    tpt2.y = pt2.y - testHt/math.tan(math.radians(testAngle))
                    pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                    pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1.x = pt1.x - currTabHt
                        tpt2.x = pt2.x - currTabHt
                    else:
                        tpt1.x = pt1.x + currTabHt
                        tpt2.x = pt2.x + currTabHt
                    tpt1.y = pt1.y + currTabHt/math.tan(math.radians(currTabAngle))
                    tpt2.y = pt2.y - currTabHt/math.tan(math.radians(currTabAngle))
                else: # pt2.y < pt1.y
                    tpt1.x = pt1.x + testHt
                    tpt2.x = pt2.x + testHt
                    tpt1.y = pt1.y - testHt/math.tan(math.radians(testAngle))
                    tpt2.y = pt2.y + testHt/math.tan(math.radians(testAngle))
                    pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                    pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1.x = pt1.x - currTabHt
                        tpt2.x = pt2.x - currTabHt
                    else:
                        tpt1.x = pt1.x + currTabHt
                        tpt2.x = pt2.x + currTabHt
                    tpt1.y = pt1.y - currTabHt/math.tan(math.radians(currTabAngle))
                    tpt2.y = pt2.y + currTabHt/math.tan(math.radians(currTabAngle))
            elif math.isclose(pt1.y, pt2.y):
                # It's horizontal. Let's try the top
                if pt1.x < pt2.x:
                    tpt1.y = pt1.y - testHt
                    tpt2.y = pt2.y - testHt
                    tpt1.x = pt1.x + testHt/math.tan(math.radians(testAngle))
                    tpt2.x = pt2.x - testHt/math.tan(math.radians(testAngle))
                    pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                    pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1.y = pt1.y + currTabHt
                        tpt2.y = pt2.y + currTabHt
                    else:
                        tpt1.y = pt1.y - currTabHt
                        tpt2.y = pt2.y - currTabHt
                    tpt1.x = pt1.x + currTabHt/math.tan(math.radians(currTabAngle))
                    tpt2.x = pt2.x - currTabHt/math.tan(math.radians(currTabAngle))
                else: # pt2.x < pt1.x
                    tpt1.y = pt1.y - testHt
                    tpt2.y = pt2.y - testHt
                    tpt1.x = pt1.x - testHt/math.tan(math.radians(testAngle))
                    tpt2.x = pt2.x + testHt/math.tan(math.radians(testAngle))
                    pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                    pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                    if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                       (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                        tpt1.y = pt1.y + currTabHt
                        tpt2.y = pt2.y + currTabHt
                    else:
                        tpt1.y = pt1.y - currTabHt
                        tpt2.y = pt2.y - currTabHt
                    tpt1.x = pt1.x - currTabHt/math.tan(math.radians(currTabAngle))
                    tpt2.x = pt2.x + currTabHt/math.tan(math.radians(currTabAngle))

            else: # the orientation is neither horizontal nor vertical
                # Let's get the slope of the line between the points
                # Because Inkscape's origin is in the upper-left corner,
                # a positive slope (/) will yield a negative value
                slope = (pt2.y - pt1.y)/(pt2.x - pt1.x)
                # Let's get the angle to the horizontal
                theta = math.degrees(math.atan(slope))
                # Let's construct a horizontal tab
                seglength = math.sqrt((pt1.x-pt2.x)**2 +(pt1.y-pt2.y)**2)
                if slope < 0.0:
                    if pt1.x < pt2.x:
                        tpt1.y = pt1.y - testHt
                        tpt2.y = pt2.y - testHt
                        tpt1.x = pt1.x + testHt/math.tan(math.radians(testAngle))
                        tpt2.x = pt2.x - testHt/math.tan(math.radians(testAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                        pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                        pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1.y = pt1.y + currTabHt
                            tpt2.y = pt2.y + currTabHt
                        else:
                            tpt1.y = pt1.y - currTabHt
                            tpt2.y = pt2.y - currTabHt
                        tpt1.x = pt1.x + currTabHt/math.tan(math.radians(currTabAngle))
                        tpt2.x = pt2.x - currTabHt/math.tan(math.radians(currTabAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                    else: # pt1.x > pt2.x
                        tpt1.y = pt1.y - testHt
                        tpt2.y = pt2.y - testHt
                        tpt1.x = pt1.x - testHt/math.tan(math.radians(testAngle))
                        tpt2.x = pt2.x + testHt/math.tan(math.radians(testAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                        pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                        pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1.y = pt1.y + currTabHt
                            tpt2.y = pt2.y + currTabHt
                        else:
                            tpt1.y = pt1.y - currTabHt
                            tpt2.y = pt2.y - currTabHt
                        tpt1.x = pt1.x - currTabHt/math.tan(math.radians(currTabAngle))
                        tpt2.x = pt2.x + currTabHt/math.tan(math.radians(currTabAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                else: # slope > 0.0
                    if pt1.x < pt2.x:
                        tpt1.y = pt1.y - testHt
                        tpt2.y = pt2.y - testHt
                        tpt1.x = pt1.x + testHt/math.tan(math.radians(testAngle))
                        tpt2.x = pt2.x - testHt/math.tan(math.radians(testAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                        pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                        pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1.y = pt1.y + currTabHt
                            tpt2.y = pt2.y + currTabHt
                        else:
                            tpt1.y = pt1.y - currTabHt
                            tpt2.y = pt2.y - currTabHt
                        tpt1.x = pt1.x + currTabHt/math.tan(math.radians(currTabAngle))
                        tpt2.x = pt2.x - currTabHt/math.tan(math.radians(currTabAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                    else: # pt1.x > pt2.x
                        tpt1.y = pt1.y - testHt
                        tpt2.y = pt2.y - testHt
                        tpt1.x = pt1.x - testHt/math.tan(math.radians(testAngle))
                        tpt2.x = pt2.x + testHt/math.tan(math.radians(testAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
                        pnpt1 = inkex.paths.Move(tpt1.x, tpt1.y)
                        pnpt2 = inkex.paths.Move(tpt2.x, tpt2.y)
                        if ((not tpath.enclosed) and (self.insidePath(tpath.path, pnpt1) or self.insidePath(tpath.path, pnpt2))) or \
                           (tpath.enclosed and ((not self.insidePath(tpath.path, pnpt1)) and (not self.insidePath(tpath.path, pnpt2)))):
                            tpt1.y = pt1.y + currTabHt
                            tpt2.y = pt2.y + currTabHt
                        else:
                            tpt1.y = pt1.y - currTabHt
                            tpt2.y = pt2.y - currTabHt
                        tpt1.x = pt1.x - currTabHt/math.tan(math.radians(currTabAngle))
                        tpt2.x = pt2.x + currTabHt/math.tan(math.radians(currTabAngle))
                        tl1 = [('M', [pt1.x,pt1.y])]
                        tl1 += [('L', [tpt1.x, tpt1.y])]
                        ele1 = inkex.Path(tl1)
                        tl2 = [('M', [pt1.x,pt1.y])]
                        tl2 += [('L', [tpt2.x, tpt2.y])]
                        ele2 = inkex.Path(tl2)
                        thetal1 = ele1.rotate(theta, [pt1.x,pt1.y])
                        thetal2 = ele2.rotate(theta, [pt2.x,pt2.y])
                        tpt1.x = thetal1[1].x
                        tpt1.y = thetal1[1].y
                        tpt2.x = thetal2[1].x
                        tpt2.y = thetal2[1].y
            # Check to see if any tabs intersect each other
            if self.detectIntersect(pt1.x, pt1.y, tpt1.x, tpt1.y, pt2.x, pt2.y, tpt2.x, tpt2.y):
                # Found an intersection.
                if adjustTab == 0:
                    # Try increasing the tab angle in one-degree increments
                    currTabAngle = currTabAngle + 1.0
                    if currTabAngle > 88.0: # We're not increasing the tab angle above 89 degrees
                        adjustTab = 1
                        currTabAngle = taba
                if adjustTab == 1:
                    # So, try reducing the tab height in 20% increments instead
                    currTabHt = currTabHt - tabht*0.2 # Could this lead to a zero tab_height?
                    if currTabHt <= 0.0:
                        # Give up
                        currTabHt = tabht
                        adjustTab = 2
                if adjustTab == 2:
                    tabDone = True # Just show the failure
            else:
                tabDone = True
            
        return tpt1,tpt2

    def effect(self):
        layer = self.svg.get_current_layer()
        scale = self.svg.unittouu('1'+self.options.unit)
        polysides = int(self.options.polysides)
        poly1size = float(self.options.poly1size) * scale
        poly2size = float(self.options.poly2size) * scale
        collarht = float(self.options.collarheight) * scale
        partcnt = int(self.options.collarparts)
        tab_angle = float(self.options.tabangle)
        tab_height = float(self.options.tabheight) * scale
        dashlength = float(self.options.dashlength) * scale
        polylarge = max(poly1size, poly2size) # Larger of the two polygons
        polysmall = min(poly1size, poly2size) # Smaller of the two polygons
        polysmallR = polysmall/2
        polysmallr = polysmallR*math.cos(math.pi/polysides)
        polysmalltabht = tab_height
        if polysmallr < polysmalltabht:
             polysmalltabht = polysmallr
        wpaths = []
        done = 0
        # We go through this loop twice
        # First time for the wrapper / decorative strip
        # Second time for the model, scorelines, and the lids
        while done < 2:
          w1 = (polylarge)*(math.sin(math.pi/polysides))
          w2 = (polysmall)*(math.sin(math.pi/polysides))
          if done == 0:
             # First time through, init the storage areas
             pieces = []
             nodes = []
             nd = []
             for i in range(4):
                nd.append(inkex.paths.Line(0.0,0.0))
          else:
             # Second time through, empty the storage areas
             i = 0
             while i < polysides:
                j = 0
                while j < 4:
                   del pieces[i][0]
                   j = j + 1
                i = i + 1
             i = 0
             while len(pieces) > 0:
                del pieces[0]
                i = i + 1
             i = 0
             while i < 4:
                del nodes[0]
                i = i + 1
          for pn in range(polysides):
             nodes.clear()
             #what we need here is to skip the rotatation and just move the x and y if there is no difference between the polygon sizes.
             #Added by Sue to handle equal polygons
             if poly1size == poly2size:
                nd[0].x =  pn * w1
                nd[0].y = collarht
                nd[1].x = nd[0].x + w1  
                nd[1].y = nd[0].y
                nd[2].x = nd[1].x
                nd[2].y = nd[0].y - collarht   
                nd[3].x = nd[0].x  
                nd[3].y = nd[2].y 
             else:
                if pn == 0:
                   nd[3].x = -w2/2
                   nd[3].y = (polysmall/2)*math.cos(math.pi/polysides)
                   nd[0].x = -w1/2
                   nd[0].y = (polylarge/2)*math.cos(math.pi/polysides)
                   vlen = math.sqrt(collarht**2 + (nd[0].y-nd[3].y)**2)
                   nd[0].y = nd[0].y + (vlen-(nd[0].y-nd[3].y))
                   nd[2].x = w2/2
                   nd[2].y = nd[3].y
                   nd[1].x = w1/2
                   nd[1].y = nd[0].y
                   ox,oy = self.findIntersection(nd[0].x,nd[0].y,nd[3].x,nd[3].y,nd[1].x,nd[1].y,nd[2].x,nd[2].y)
                   Q2 = math.degrees(math.atan((nd[0].y - oy)/(w1/2 - ox)))
                   Q1 = 90 - Q2
                else:
                   dl = ''
                   for j in range(4):
                        if j == 0:
                           dl += 'M '
                        else:
                           dl += ' L '
                        dl += str(nd[j].x) + ',' + str(nd[j].y)
                   dl += ' Z'
                   p1 = inkex.paths.Path(path_d=dl)
                   p2 = p1.rotate(-2*Q1, (ox,oy))
                   for j in range(4):
                      nd[j].x = p2[j].x
                      nd[j].y = p2[j].y
             for i in range(4):
                nodes.append(copy.deepcopy(nd[i]))
             pieces.append(copy.deepcopy(nodes))
          dscores = []
          if done == 0:
             wpath = pathStruct() # We'll need this for makeTab
             wpath.id = "c1"
             for pc in range(partcnt):
                dwrap = '' # Create the wrapper
                dscores.clear()
                sidecnt = math.ceil(polysides/partcnt)
                if pc == partcnt - 1:
                   # Last time through creates the remainder of the pieces
                   sidecnt = polysides - math.ceil(polysides/partcnt)*pc
                startpc = pc*math.ceil(polysides/partcnt)
                endpc = startpc + sidecnt
                for pn in range(startpc, endpc):
                   # First half
                   if(pn == startpc):
                      ppt0 = inkex.paths.Move(pieces[pn][0].x,pieces[pn][0].y)
                      dwrap +='M '+str(ppt0.x)+','+str(ppt0.y)
                      # We're also creating wpath for later use in creating the model
                      wpath.path.append(ppt0)
                   ppt1 = inkex.paths.Line(pieces[pn][1].x,pieces[pn][1].y)
                   dwrap +=' L '+str(ppt1.x)+','+str(ppt1.y)
                   wpath.path.append(ppt1)
                   if pn < endpc - 1:
                      # Put scorelines across the collar
                      ppt2 = inkex.paths.Line(pieces[pn][2].x,pieces[pn][2].y)
                      spaths = self.makescore(ppt1, ppt2,dashlength)
                      dscores.append(spaths)
                for pn in range(endpc-1, startpc-1, -1):
                   # Second half
                   if(pn == (endpc-1)):
                      ppt2 = inkex.paths.Line(pieces[pn][2].x,pieces[pn][2].y)
                      dwrap +=' L '+str(pieces[pn][2].x)+','+str(pieces[pn][2].y)
                      wpath.path.append(inkex.paths.Line(pieces[pn][2].x,pieces[pn][2].y))
                   ppt3 = inkex.paths.Line(pieces[pn][3].x,pieces[pn][3].y)
                   dwrap +=' L '+str(ppt3.x)+','+str(ppt3.y)
                   wpath.path.append(inkex.paths.Line(pieces[pn][3].x,pieces[pn][3].y))
                dwrap +=' Z' # Close off the wrapper's path
                wpath.path.append(ppt0)
                if math.isclose(dashlength, 0.0):
                   # lump together all the score lines
                   dscore = ''
                   for dndx in range(len(dscores)):
                      if dndx == 0:
                         dscore = dscores[dndx][1:]
                      else:
                         dscore += dscores[dndx]
                   group = inkex.elements._groups.Group()
                   group.label = 'group'+str(pc)+'ws'
                   if self.options.generate_decorative_wrapper is True:
                       self.drawline(dwrap,'wrapper'+str(pc),group,sstr="fill:#ffdddd;stroke:{};stroke-width:0.25".format(self.options.color_solid)) # Output the wrapper
                       self.drawline(dscore,'score'+str(pc)+'w',group,sstr="fill:#ffdddd;stroke:{};stroke-width:0.25".format(self.options.color_dash)) # Output the scorelines separately
                   layer.append(group)
                else:
                   # lump together all the score lines with the model
                   for dndx in dscores:
                      dwrap = dwrap + dndx
                   self.drawline(dwrap,'wrapper'+str(pc),layer,sstr="fill:#ffdddd;stroke:{};stroke-width:0.25".format(self.options.color_solid)) # Output the wrapper
                wpaths.append(copy.deepcopy(wpath))
                wpath.path.clear()
             done = 1
          else:
             # Create the model
             for pc in range(partcnt):
                dprop = ''
                dscores.clear()
                sidecnt = math.ceil(polysides/partcnt)
                if pc == partcnt - 1:
                   sidecnt = polysides - math.ceil(polysides/partcnt)*pc
                startpc = pc*math.ceil(polysides/partcnt)
                endpc = startpc + sidecnt
                for pn in range(startpc, endpc):
                   # First half
                   if pn == startpc:
                      dprop = 'M '+str(pieces[pn][0].x)+','+str(pieces[pn][0].y)
                   cpt1 = inkex.paths.Move(pieces[pn][0].x, pieces[pn][0].y)
                   cpt2 = inkex.paths.Move(pieces[pn][1].x, pieces[pn][1].y)
                   tabpt1, tabpt2 = self.makeTab(wpaths[pc], cpt1, cpt2, tab_height, tab_angle)
                   dprop +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
                   dprop +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
                   dprop += ' L '+str(pieces[pn][1].x)+','+str(pieces[pn][1].y)
                   # As long as we're here, create a scoreline along the tab...
                   spaths = self.makescore(pieces[pn][0], pieces[pn][1],dashlength)
                   dscores.append(spaths)
                   # ...and across the collar
                   spaths = self.makescore(pieces[pn][1], pieces[pn][2],dashlength)
                   dscores.append(spaths)
                for pn in range(endpc-1, startpc-1, -1):
                   # Second half
                   if(pn == (endpc-1)):
                      # Since we're starting on the last piece, put a tab on the end of it, too
                      cpt1 = inkex.paths.Move(pieces[pn][1].x, pieces[pn][1].y)
                      cpt2 = inkex.paths.Move(pieces[pn][2].x, pieces[pn][2].y)
                      tabpt1, tabpt2 = self.makeTab(wpaths[pc], cpt1, cpt2, tab_height, tab_angle)
                      dprop +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
                      dprop +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
                      # Create a scoreline along the tab
                      #spaths = self.makescore(pieces[pn][1], pieces[pn][2],dashlength)
                      #dscores.append(spaths)
                   dprop +=' L '+str(pieces[pn][2].x)+','+str(pieces[pn][2].y)
                   cpt1 = inkex.paths.Move(pieces[pn][2].x, pieces[pn][2].y)
                   cpt2 = inkex.paths.Move(pieces[pn][3].x, pieces[pn][3].y)
                   tabpt1, tabpt2 = self.makeTab(wpaths[pc], cpt1, cpt2, polysmalltabht, tab_angle)
                   dprop +=' L '+str(tabpt1.x)+','+str(tabpt1.y)
                   dprop +=' L '+str(tabpt2.x)+','+str(tabpt2.y)
                   dprop += ' L '+str(pieces[pn][3].x)+','+str(pieces[pn][3].y)
                   # Create a scoreline along the tab
                   spaths = self.makescore(pieces[pn][2], pieces[pn][3],dashlength)
                   dscores.append(spaths)
                dprop += ' Z' # Close off the model's path
                # lump together all the score lines
                dscore = ''
                for dndx in range(len(dscores)):
                   if dndx == 0:
                      dscore = dscores[dndx][1:]
                   else:
                      dscore += dscores[dndx]
                group = inkex.elements._groups.Group()
                group.label = 'group'+str(pc)+'ms'
                self.drawline(dprop,'model'+str(pc),group,sstr='stroke:{};stroke-width:0.25;fill:#eeeeee'.format(self.options.color_solid)) # Output the model
                
                #self.drawline(dprop,'model'+str(pc),group,sstr=None) # Output the model
                #self.drawline(dscore,'score'+str(pc)+'m',group,sstr=None) # Output the scorelines separately
                
                
                if dscore != '':
                  dscore_style = 'stroke:{};stroke-width:0.25;fill:#eeeeee'.format(self.options.color_dash)
                  if self.options.cosmetic_dash_style is True:
                    dscore_style += ';stroke-dasharray:{}'.format(3, 3)
                  self.drawline(dscore,'score'+str(pc),group,dscore_style) # Output the scorelines separately
                
                layer.append(group)
    
             # At this point, we can generate the top and bottom polygons
             # r = sidelength/(2*sin(PI/numpoly))
             self.drawline(self.makepoly(w1, polysides),'biglid',layer,sstr=None) # Output the bigger polygon
             sp = self.makepoly(w2, polysides)
             self.drawline(sp,'smalllid',layer,sstr=None) # Output the smaller polygon
             done = 2

if __name__ == '__main__':
    Collar().run()
