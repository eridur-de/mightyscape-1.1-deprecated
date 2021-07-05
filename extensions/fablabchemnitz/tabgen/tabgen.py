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
Given a closed path of straight lines, this program generates a paper model containing
tabs and score lines for each straight edge.
"""

import inkex
from inkex import Path
from lxml import etree
import math
import copy
import inspect

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

class Tabgen(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--usermenu")
        pars.add_argument("--tabangle", type=float, default=45.0, help="Angle of tab edges in degrees")
        pars.add_argument("--tabheight", type=float, default=0.4, help="Height of tab in dimensional units")
        pars.add_argument("--dashlength", type=float, default=0.25, help="Length of dashline in dimentional units (zero for solid line)")
        pars.add_argument("--tabsets", default="both", help="Tab placement on polygons with cutouts")
        pars.add_argument("--unit", default="in", help="Dimensional units of selected paths")
        pars.add_argument("--print_debug", type=inkex.Boolean, default=True, help="Print debug info")
        pars.add_argument("--keep_original", type=inkex.Boolean, default=False, help="Keep original elements")

    #draw SVG line segment(s) between the given (raw) points
    def drawline(self, dstr, name, parent, sstr=None):
        line_style   = {'stroke':'#000000','stroke-width':'1','fill':'none'}
        if sstr == None:
            stylestr = str(inkex.Style(line_style))
        else:
            stylestr = sstr
        el = parent.add(inkex.PathElement())
        el.path = dstr
        el.style = sstr
        el.label = name

    def pathInsidePath(self, path, testpath):
        enclosed = True
        for tp in testpath:
            # If any point in the testpath is outside the path, it's not enclosed
            if self.insidePath(path, tp) == False:
                enclosed = False
                return enclosed # True if testpath is fully enclosed in path
        return enclosed
        
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
        testHt = currTabHt * 0.01
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
        scale = self.svg.unittouu('1'+self.options.unit)
        layer = self.svg.get_current_layer()
        tab_angle = float(self.options.tabangle)
        tab_height = float(self.options.tabheight) * scale
        dashlength = float(self.options.dashlength) * scale
        tabsets = self.options.tabsets
        npaths = []
        savid = ''
        elems = []
        pc = 0
        for selem in self.svg.selection.filter(inkex.PathElement):
            elems.append(selem)
        if len(elems) == 0:
            raise inkex.AbortExtension("Nothing selected")
        for elem in elems:
            npaths.clear()
            escale = 1.0
            #inkex.utils.debug(elem.attrib)
            if 'transform' in elem.attrib:
                transforms = elem.attrib['transform'].split()
                for tf in transforms:
                    if tf.startswith('scale'):
                        escale = float(tf.split('(')[1].split(')')[0])
            last_letter = 'Z'
            savid = elem.get_id()
            idmod = 0
            elementPath = Path(elem.path.to_absolute().transform(elem.getparent().composed_transform()))
            
            for ptoken in elementPath: # For each point in the path
                ptx2 = None
                pty2 = None
                if ptoken.letter == 'M': # Starting point
                    # Hold this point in case we receive a Z
                    ptx1 = mx = ptoken.x * escale
                    pty1 = my = ptoken.y * escale
                    '''
                    Assign a structure to the new path. We assume that there is
                    only one path and, therefore, it isn't enclosed by a
                    sub-path. However, we'll suffix the ID, if we find a
                    sub-path.
                    '''
                    npath = pathStruct()
                    npath.enclosed = False
                    if idmod > 0:
                        npath.id = elem.get_id()+"-"+str(idmod)
                    else:
                        npath.id = elem.get_id()
                    idmod += 1
                    npath.path.append(inkex.paths.Move(ptx1,pty1))
                else:
                    if last_letter != 'M':
                        ptx1 = ptx2
                        pty1 = pty2
                    if ptoken.letter == 'L':
                        ptx2 = ptoken.x * escale
                        pty2 = ptoken.y * escale
                    elif ptoken.letter == 'H':
                        ptx2 = ptoken.x * escale
                        pty2 = pty1
                    elif ptoken.letter == 'V':
                        ptx2 = ptx1
                        pty2 = ptoken.y * escale
                    elif ptoken.letter == 'Z':
                        ptx2 = mx
                        pty2 = my
                    else:
                        raise inkex.AbortExtension("Unrecognized path command {0}".format(ptoken.letter))
                    npath.path.append(inkex.paths.Line(ptx2,pty2))
                    if ptoken.letter == 'Z':
                        npaths.append(npath)
                    else:
                        if self.options.print_debug is True:
                            self.msg("Warning! Path {} is not closed. Skipping ...".format(elem.get('id')))
                last_letter = ptoken.letter
            # check for cutouts
            if idmod > 1:
                for apath in npaths: # We test these paths to see if they are fully enclosed
                    for bpath in npaths: # by these paths
                        if apath.id != bpath.id:
                            if self.pathInsidePath(bpath.path, apath.path):
                                apath.enclosed = True
            # add tabs to current path(s)
            if 'style' in elem.attrib:
                sstr = elem.attrib['style']
                if not math.isclose(escale, 1.0):
                    lsstr = sstr.split(';')
                    for stoken in range(len(lsstr)):
                        if lsstr[stoken].startswith('stroke-width'):
                            swt = lsstr[stoken].split(':')[1]
                            swf = str(float(swt)*escale)
                            lsstr[stoken] = lsstr[stoken].replace(swt, swf)
                        if lsstr[stoken].startswith('stroke-miterlimit'):
                            swt = lsstr[stoken].split(':')[1]
                            swf = str(float(swt)*escale)
                            lsstr[stoken] = lsstr[stoken].replace(swt, swf)
                    sstr = ";".join(lsstr)
            else:
                sstr = None
            dsub = '' # Used for building sub-paths
            dprop = '' # Used for building the main path
            dscore = '' # Used for building dashlines
            for apath in npaths:
                mpath = [apath.path[0]] # init output path with first point of input path
                for ptn in range(len(apath.path)-1):
                    if (tabsets == 'both') or (((tabsets == 'inside') and (apath.enclosed)) or ((tabsets == 'outside') and (not apath.enclosed))):
                        tabpt1, tabpt2 = self.makeTab(apath, apath.path[ptn], apath.path[ptn+1], tab_height, tab_angle)
                        mpath.append(tabpt1)
                        mpath.append(tabpt2)
                        dscore = dscore + self.makescore(apath.path[ptn], apath.path[ptn+1],dashlength)
                    mpath.append(apath.path[ptn+1])
                if apath.id == elem.get_id():
                    for nodes in range(len(mpath)):
                        if nodes == 0:
                            dprop = 'M ' # This is the main path, which should appear first
                        else:
                            dprop = dprop + ' L '
                        dprop = dprop + str(mpath[nodes].x) + ',' + str(mpath[nodes].y)
                    ## and close the path
                    dprop = dprop + ' Z'
                else:
                    for nodes in range(len(mpath)):
                        if nodes == 0:
                            dsub = dsub + ' M ' # This is a sub-path, which should follow the main path
                        else:
                            dsub = dsub + ' L '
                        dsub = dsub + str(mpath[nodes].x) + ',' + str(mpath[nodes].y)
                    ## and close the path
                    dsub = dsub + ' Z'
            dprop = dprop + dsub # combine all the paths
            if math.isclose(dashlength, 0.0):
                # lump together all the score lines
                group = inkex.elements._groups.Group()
                group.label = 'group'+str(pc)+'ms'
                self.drawline(dprop,'model'+str(pc),group,sstr) # Output the model
                if dscore != '':
                    self.drawline(dscore,'score'+str(pc),group,sstr) # Output the scorelines separately
                layer.append(group)
            else:
                dprop = dprop + dscore
                self.drawline(dprop,savid+'ms',layer,sstr)
            pc += 1
         
            if self.options.keep_original is False:
                elem.delete()  

if __name__ == '__main__':
    Tabgen().run()
