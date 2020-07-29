#!/usr/bin/env python3
'''
shapes.py

Copyright (C) 2015-2017 Paco Garcia, www.arakne.es

2017_07_30: added crossed corners
            copy class of original object if exists
2017_08_09: rombus moved to From corners tab
2017_08_17: join circles not need boolen operations now
            join circles added Oval
2017_08_25: fixed error in objects without style
            in oval sets the minimal radius necessary

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
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307 USA

-----------------------

'''
import locale
import os
import sys
import tempfile
import webbrowser
import math
from subprocess import Popen, PIPE
import inkex
from fablabchemnitz_arakne_xy import *
from lxml import etree

defStyle = [['stroke-width','0.5'],['fill','#f0ff00'],['stroke','#ff0000']]

locale.setlocale(locale.LC_ALL, '')

class Shapes(inkex.Effect):

    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--tab")
        self.arg_parser.add_argument("--chamfertype")
        self.arg_parser.add_argument("--size", type=float, default="20")
        self.arg_parser.add_argument("--incdec", type=float, default="0")
        self.arg_parser.add_argument("--tritype", default="")
        self.arg_parser.add_argument("--spikestype")
        self.arg_parser.add_argument("--spikesdir")
        self.arg_parser.add_argument("--unit")
        self.arg_parser.add_argument("--spikesize", type=float, default="2.0")
        self.arg_parser.add_argument("--spikesep", type=float, default="0.0")
        self.arg_parser.add_argument("--arrowtype",  default="")
        self.arg_parser.add_argument("--headWidth", type=float, default="20.0")
        self.arg_parser.add_argument("--headHeight", type=float, default="40.0")
        self.arg_parser.add_argument("--arrowWidth", type=float, default="10.0")
        self.arg_parser.add_argument("--squareselection", type=inkex.Boolean, default="false")
        self.arg_parser.add_argument("--trihside", type=inkex.Boolean, default="false")
        self.arg_parser.add_argument("--trivside", type=inkex.Boolean, default="false")
        self.arg_parser.add_argument("--copyfill", type=inkex.Boolean, default="false")
        self.arg_parser.add_argument("--deleteorigin", type=inkex.Boolean, default="false")
        self.arg_parser.add_argument("--joincirctype",  default="")
        self.arg_parser.add_argument("--joinradius", type=float, default="0.0")

    def addEle(self, ele, parent, props):
        elem = etree.SubElement(parent, ele)
        for n in props: elem.set(n,props[n])
        return elem

    def chStyles(self,node,sty):
        style = inkex.Style.parse_str(node.get('style'))
        for n in sty:
            if str(style) in n[0]: style.pop(n[0], None)
            #if n[1]!="": style[n[0]]=n[1]
        node.set('style',str(inkex.Style(style)))

    def unit2uu(self, val):    
        if hasattr(self,"unittouu") is True:
            return self.unittouu(val)
        else:
            return inkex.unittouu(val)

    def limits(self, node):
        s = node.bounding_box()
        l,r,t,b = (s.left,s.right,s.top,s.bottom)
        an,al = (r - l, b - t)
        incdec = self.svg.unittouu(self.options.incdec)
        l, t, r, b, an, al = (l - incdec, t - incdec, r + incdec, b + incdec, an + incdec*2, al + incdec*2)
        return (l,r,t,b,an,al)
 
    def estilo(self, nn, orig, style=defStyle):
        if self.options.copyfill:
            if orig.get('style'):
                nn.set("style", orig.get('style'))
                if orig.get('class'):
                     nn.set("class", orig.get('class'))
        else:
            self.chStyles(nn,style)

    def circleABCD(self,p,r,abcd="ABCD",inverse=False,xtra=None):
        aa = r * 0.551915024494
        parts={
            'A':[XY(0,-r),XY(aa,-r), XY(r, -aa),XY(r,0)],
            'B':[XY(r,0), XY(r, aa), XY(aa,  r),XY(0,r)],
            'C':[XY(0,r), XY(-aa,r), XY(-r, aa),XY(-r,0)],
            'D':[XY(-r,0),XY(-r,-aa),XY(-aa,-r),XY(0,-r)]}
        #pA = parts[abcd[0]]
        pA = [XY(p)+N for N in parts[abcd[0]]]
        for aa in abcd[1:]:
            pA = pA + [XY(p)+N for N in parts[aa][1:]]
        if inverse==True: pA.reverse()
        listA = XYList(pA)
        if xtra:
            for n in xtra:
                listA[n].extend(xtra[n])
        return listA

    def draw(self, node, sh='"rombus"'):
        #inkex.errormsg(sh)
        sO = self.options
        l, r, t, b, an, al = self.limits(node)
        sqSel = sO.squareselection
        copyfill = sO.copyfill
        deleteorigin=sO.deleteorigin

        side = min(al,an)
        if sqSel:
            incx=(an-side)/2.0
            l,r,an =(l+incx,r-incx,side)
            incy=(al-side)/2.0
            t +=incy
            b -=incy
            al = side
        cX, cY = (an/2.0,al/2.0)

        pp = node.getparent()
        varBez = 0.551915024494
        a = self.svg.unittouu(sO.size)
        a_2, a2 = (a / 2.0,a * 2.0)
        dS = "m %sz"
        pnts = [[l+cX,t],[cX,cY],[-cX,cY],[-cX,-cY]]
        aa = a * varBez
        chtype=sO.chamfertype
        tritype=sO.tritype
        if sh=='"chamfer"':
            an2, al2 = ((an-a)/2.0,(al-a)/2.0)
            if chtype=="rombus" and a>0:
                pnts=[[l+cX - a_2,t],[a,0],[an2,al2],[0,a],[-an2,al2],[-a,0],[-an2,-al2],[0,-a]]
            if chtype=="chamfer":
                pnts=[[l+a,t],[an - a2,0],[a,a],[0,al-a2],[-a,a],[-(an - a2),0],[-a,-a],[0,-(al-a2)]]
            if chtype=="chamferinv":
                pnts=[[l,t],[a,0],[-a,a],[an-a,0," z m"],[a,0],[0,a],[a,al," z m"],[0,-a],[-a,a],[-an+a,0," z m"],[-a,-a],[0,a]]
            if chtype=="round":
                pnts = circQ(XY(l,t),a,"B",0,{1:"C"}) + circQ(XY(l,b),a,"A",0,{0:"L",1:"C"}) + circQ(XY(r,b),a,"D",0,{0:"L",1:"C"}) + circQ(XY(r,t),a,"C",0,{0:"L",1:"C"})
            if chtype=="roundinv":
                pnts=[[l,t],[a,0],[0,aa,"c "],[-aa,a],[-a,a],[an-a,0,"z m "],[a,0],[0,a],[-aa,0," c"],[-a,-aa],[-a,-a],
                    [a,al-a,"z m "],[0,a],[-a,0],[0,-aa,"c "],[aa,-a],[a,-a],[-an,0,"z m "],[0,a],[a,0],[0,-aa,"c "],[-aa,-a],[-a,-a]]
            if chtype=="rect":
                pnts=[[l+a,t],[an - a2,0],[0,a],[a,0],[0,al-a2],[-a,0],[0,a],[-(an-a2),0],[0,-a],[-a,0],[0,-(al-a2)],[a,0]]
            if chtype=="cross":
                pnts=[[l+an2,t],[a,0],[0,al2],[an2,0],[0,a],[-an2,0],[0,al2],[-a,0],[0,-al2],[-an2,0],[0,-a],[an2,0]]
            if chtype=="starcorners":
                pnts=[[l,t],[cX,al2],[cX,-al2],[-an2,cY],[an2,cY],[-cX,-al2],[-cX,al2],[an2,-cY]]
            if chtype=="starcenter":
                pnts=[[l+cX,t],[a_2,al2], [an2,a_2], [-an2,a_2],[-a_2,al2],[-a_2,-al2],[-an2,-a_2],[an2,-a_2]]
            if chtype=="crosscornersquad":
                pnts=[[l-a,t],[0,-a],[a,0],[0,al+a*2],[-a,0],[0,-a],[an+a*2,0],[0,a],[-a,0],[0,-al-a*2],[a,0],[0,a]]
            if chtype=="crosscornerstri":
                pnts=[[l-a,t],[a,-a],[0,al+a*2],[-a,-a],[an+a*2,0],[-a,a],      [0,-al-a*2],[a,a]]
            if chtype=="crosscornersround":
                dS = "M %sZ"
                aa2 = a_2 * varBez
                p1 = circQ(XY(r + a_2, t - a_2),a_2,"DAB",1)
                p2 = circQ(XY(r + a_2, b + a_2),a_2,"ABC",1)
                p3 = circQ(XY(l - a_2, b + a_2),a_2,"BCD",1)
                p4 = circQ(XY(l - a_2, t - a_2),a_2,"CDA",1)
                pnts = p1 + [[r,t],[r,b+a_2-aa2]] + p2 + [[r+a_2-aa2,b],[l-a_2+aa2,b]] + p3 + [[l,b+a_2-aa],[l,t-a_2+aa]] + p4
                pnts[1].append(" C")

        if sh=='"triangles"':
            trihside, trivside=(sO.trihside, sO.trivside)
            if tritype=="isosceles": pnts=[[l+cX,t],[cX,al],[-an,0]]
            if tritype=="equi":
                sqrt3 = 1.7320508075
                height = sqrt3/2*side
                tcx, tcy = ((an - side)/2.0, (al - height)/2.0)
                pnts=[[cX+l,t+tcy],[an/2.0-tcx,height],[-side,0]]
            if tritype=="rect":
                x1 = l + tern(not trivside and trihside,an,0)
                x2 = tern(not trivside and trihside,0,an)
                x3 = tern(trivside and trihside,0,-an)
                pnts=[[x1,t],[x2,tern(not trivside,al,0)],[x3,tern(not trivside,0,al)]]
        if sh=='"spikes"':
            spikestype = sO.spikestype
            spikesdir = sO.spikesdir
            ssep = self.svg.unittouu(sO.spikesep)
            ss = self.svg.unittouu(sO.spikesize)
            anX, anY = (int( (an+ssep) / (ss * 2 + ssep)), int( (al+ssep) / (ss * 2 + ssep)))
            iniX, iniY = (((an+ssep) - (anX * (ss * 2 + ssep))) / 2.0, ((al+ssep) - (anY * (ss * 2 + ssep))) / 2.0)
            dir = 1
            pnts = [[l,t],[iniX,0]]
            if spikesdir=='ins': dir = -1.0
            if spikestype=="tri":
                for n in range(anX):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1            
                    pnts.extend([[ss,-ss*dir],[ss,ss*dir]])
                    if ssep>0 and n < (anX-1): pnts.append([ssep,0])
                pnts.extend([[iniX,0],[0,iniY]])
                for n in range(anY):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[ss * dir,ss],[-ss * dir,ss]])
                    if ssep>0 and n < (anY-1): pnts.append([0, ssep])
                pnts.extend([[0,iniY],[-iniX,0]])
                for n in range(anX):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[-ss,ss*dir],[-ss,-ss*dir]])
                    if ssep>0 and n < (anX-1): pnts.append([-ssep,0])
                pnts.extend([[-iniX,0],[0,-iniY]])
                for n in range(anY):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[-ss*dir,-ss],[ss*dir,-ss]])
                    if ssep>0 and n < (anY-1): pnts.append([0, -ssep])
            if spikestype=="trirect":
                anX, anY = ( int((an + ssep) / (ss + ssep)), int((al + ssep) / (ss + ssep)) )
                iniX, iniY = (((an + ssep) - (anX * (ss + ssep))) / 2.0, ((al + ssep) - (anY * (ss + ssep))) / 2.0)
                pnts = [[l,t],[iniX,0]]
                for n in range(anX):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1                
                    pnts.extend([[0,-ss*dir],[ss,ss*dir]])
                    if ssep>0 and n < (anX-1): pnts.append([ssep,0])
                pnts.extend([[iniX,0],[0,iniY]])
                for n in range(anY):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[ss * dir,0],[-ss * dir,ss]])
                    if ssep>0 and n < (anY-1): pnts.append([0, ssep])
                pnts.extend([[0,iniY],[-iniX,0]])
                for n in range(anX):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[0,ss*dir],[-ss,-ss*dir]])
                    if ssep>0 and n < (anX-1): pnts.append([-ssep,0])
                pnts.extend([[-iniX,0],[0,-iniY]])
                for n in range(anY):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[-ss*dir,0],[ss*dir,-ss]])
                    if ssep>0 and n < (anY-1): pnts.append([0, -ssep])
            if spikestype=="squ":
                anX, anY = ( int((an + ssep) / (ss + ssep)), int((al + ssep) / (ss + ssep)) )
                iniX, iniY = (((an + ssep) - (anX * (ss + ssep))) / 2.0, ((al + ssep) - (anY * (ss + ssep))) / 2.0)
                pnts = [[l,t],[iniX,0]]
                for n in range(anX):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[0,-ss * dir], [ss,0], [0,ss * dir]])
                    if ssep>0 and n < (anX-1): pnts.append([ssep,0])
                pnts.extend([[iniX,0],[0,iniY]])
                for n in range(anY):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[ss * dir,0],[0,ss],[-ss * dir,0]])
                    if ssep>0 and n < (anY-1): pnts.append([0,ssep])
                pnts.extend([[0,iniY],[-iniX,0]])
                for n in range(anX):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[0,ss * dir],[-ss,0],[0,-ss * dir]])
                    if ssep>0 and n < (anX-1): pnts.append([-ssep,0])
                pnts.extend([[-iniX,0],[0,-iniY]])
                for n in range(anY):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[-ss * dir,0],[0,-ss],[ss * dir,0]])
                    if ssep>0 and n < (anY-1): pnts.append([0,-ssep])

            if spikestype=="rnd":
                dif = ss - (ss*varBez)
                dBez = ss*varBez
                for n in range(anX):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1   
                    pnts.extend([[0,-dBez * dir," c"],[dif,-ss * dir],[ss,-ss * dir],#fijo
                        [dBez,0],[ss,dif * dir],[ss,ss * dir]]) #fijo
                    if ssep>0 and n < (anX-1): pnts.append([ssep,0,' l'])
                pnts.extend([[iniX,0," l"],[0,iniY]])
                for n in range(anY):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[dBez * dir,0," c"],[ss * dir,dif],[ss * dir,ss],#fijo
                        [0,dBez],[-dif * dir,ss],[-ss * dir,ss]]) #fijo
                    if ssep>0 and n < (anY-1): pnts.append([0,ssep,' l'])
                pnts.extend([[0,iniY,' l'],[-iniX,0]])
                for n in range(anX):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[0,dBez * dir," c"],[-dif,ss * dir],[-ss,ss * dir],#fijo
                        [-dBez,0],[-ss,-dif * dir],[-ss,-ss * dir]]) #fijo
                    if ssep>0 and n < (anX-1): pnts.append([-ssep,0,' l'])
                pnts.extend([[-iniX,0,' l'],[0,-iniY]])
                for n in range(anY):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[-dBez * dir,0," c"],[-ss * dir,-dif],[-ss * dir,-ss],#fijo
                        [0,-dBez],[dif * dir,-ss],[ss * dir,-ss]]) #fijo
                    if ssep>0 and n < (anY-1): pnts.append([0,-ssep,' l'])

            if spikestype=="wav":
                dif = ss - (ss*varBez)
                dBez = ss*varBez
                for n in range(anX):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[0,-dBez * dir," c"],[dif,-ss * dir],[ss,-ss * dir],#fijo
                        [0,dBez*dir],[dBez,ss*dir],[ss,ss * dir]]) #fijo
                    if ssep>0 and n < (anX-1): pnts.append([ssep,0,' l'])
                pnts.extend([[iniX,0," l"],[0,iniY]])
                for n in range(anY):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[dBez * dir,0," c"],[ss * dir,dif],[ss * dir,ss],#fijo
                        [-dBez*dir,0],[-ss*dir,dBez],[-ss * dir,ss]]) #fijo
                    if ssep>0 and n < (anY-1): pnts.append([0,ssep,' l'])
                pnts.extend([[0,iniY,' l'],[-iniX,0]])
                for n in range(anX):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[0,dBez * dir," c"],[-dif,ss * dir],[-ss,ss * dir],#fijo
                        [0,-dBez*dir],   [-dif, -ss*dir],[-ss,-ss * dir]]) #fijo
                    if ssep>0 and n < (anX-1): pnts.append([-ssep,0,' l'])

                pnts.extend([[-iniX,0,' l'],[0,-iniY]])
                for n in range(anY):
                    if spikesdir == 'alt' : dir = 1 if n % 2 == 1 else -1  
                    pnts.extend([[-dBez * dir,0," c"],[-ss * dir,-dif],[-ss * dir,-ss],#fijo
                        [dBez*dir,0],[ss*dir,-dBez],[ss * dir,-ss]]) #fijo
                    if ssep>0 and n < (anY-1): pnts.append([0,-ssep,' l'])
        if sh=='"arrow"':
            arrowType=sO.arrowtype
            headH, headW, arrowW = (self.svg.unittouu(sO.headHeight), self.svg.unittouu(sO.headWidth), self.svg.unittouu(sO.arrowWidth))
            hw2=headW/2.0
            if arrowType=="arrowfilled":
                pnts=[[l+cX,t],[hw2,headH],[-(headW-arrowW)/2.0,0],[0,al-headH],[-arrowW,0],[0,-(al-headH)],[-(headW-arrowW)/2.0,0]]
            else:
                dS = "m %s"
                pnts=[[l+cX,t],[0,al],[-hw2,-al+headH,"m "],[hw2,-headH],[hw2,headH]]
        d = ""
        for n in pnts:
            ss = "" if len(n)<3 else n[2]
            d += "%s%s,%s " % (ss, str(n[0]),str(n[1]))
        nn = self.addEle('path',pp, {'d':dS % (d)})
        self.estilo(nn,node)

        if deleteorigin: node.getparent().remove(node)

    def makeRel(self,arr):
        b = arr[:]
        for n in range(1,len(arr)):
            s = b[n]
            for i in range(0,n):
                s = s - arr[i]
            b[n] = s
        return b

    def circle(self,p,r):
        varBez = 0.551915024494
        dS = "m %s"
        aa = r * varBez
        d=""
        pnts=[[p.x - r,p.y],[0,aa,"c "],[r - aa,r],[r,r],[aa,0,"c "],[r,-r+aa],[r,-r],[0,-aa,"c "],[-r+aa,-r],[-r,-r],[-aa,0,"c "],[-r,r-aa],[-r,  r]]
        for n in pnts:
            ss = "" if len(n)<3 else n[2]
            d += "%s%s,%s " % (ss, str(n[0]),str(n[1]))
        return d

    def addTxt(self, node, x, y, text, dy = 0):
        new2 = self.addEle(inkex.addNS('text','svg'), node,{'x':str(x),'y':str(y)})
        new = etree.SubElement(new2, inkex.addNS('tspan','svg'), {inkex.addNS('role','sodipodi'): 'line'})
        new.set('style','text-align:center; vertical-align:bottom; font-size:10; fill-opacity:1.0;stroke:none; font-weight:normal; font-style:normal; fill:#000000')
        new.set('dy', str(dy))
        new.text = str(text)

    def circsCone(self, sels, sh='"rombus"'):
        sO = self.options
        copyfill = sO.copyfill
        deleteorigin = sO.deleteorigin
        joincirctype = sO.joincirctype
        r2 = sO.joinradius

        for nodos in range(len(sels)-1):
            node = sels[nodos]
            node2 = sels[nodos+1]
            lA, rA, tA, bA, anA, alA = self.limits(node)
            lB, rB, tB, bB, anB, alB = self.limits(node2)
            rA, cY = (anA/2.0,alA/2.0)
            rB, cY2 = (anB/2.0,alB/2.0)

            PtA = XY(lA + rA, tA + cY)
            PtB = XY(lB + rB, tB + cY2)
            if (circleInCircle(PtA,rA,PtB,rB) or circleInCircle(PtB,rB,PtA,rA)):
                pass
            else:
                pp = node.getparent()
                rotAB = XY(PtB).getAngle(PtA)
                dist = PtA.hipo(PtB)
                if joincirctype=='trapecio':
                    # alineamos las esferas en Y
                    rDif = rA - rB
                    Axis = XY(-rDif,0)
                    D2 = math.sqrt((dist*dist) - (rDif*rDif)) / dist
                    P1 = XY(Axis).mul(rA / dist)
                    P2 = XY(-dist,0) + XY(Axis).mul(rB / dist)
                    r = P1.VDist(P2)
                    Rot1 = XY(P2.x,rB * D2).getAngleD(XY(P2.x + r, rA * D2))
                    curva1a = bezs2XYList(createArcBez(rA,-90 -Rot1, -270 + Rot1))
                    d = XYListSt(curva1a, rotAB, PtA)
                    pnts2 = bezs2XYList(createArcBez(rB, 90 + Rot1, 270 - Rot1),XY(-dist,0))
                    d2 = XYListSt(pnts2, rotAB, PtA)
                    nn = self.addEle('path',pp, {'d':"M%s L%sZ" % (d,d2)})
                    self.estilo(nn,node)    
                # ################## B L O B ##############
                if joincirctype=='blob':
                    if ((r2==0) and (dist<(rA+rB))):
                        r2 = dist - rB
                    if (r2 > 0):
                        rad1 = rA + r2
                        rad2 = rB + r2
                        a = (math.pow(dist,2) - math.pow(rB+r2,2) + math.pow(rA+r2,2))/(dist*2)
                    else:
                        r2 = dist - rA - rB
                        rad1 = dist - rB
                        rad2 = dist - rA
                        a = (math.pow(dist-rB,2) - math.pow(dist-rA,2) + math.pow(dist,2))/(dist*2);   
                    # alineamos las esferas en Y

                    rt = math.atan2(PtB.y - PtA.y, PtB.x - PtA.x)
                    # # distancia del centro 1 a la interseccion de los circulos
                    x = (dist * dist - rad2 * rad2 + rad1 * rad1) / (dist*2)
                    if (rad1 * rad1 - x * x) > 0 :
                        catB = math.sqrt(rad1 * rad1 - x * x)

                        rt = math.degrees(XY(0,0).getAngle(XY(-x, -catB)))
                        rt2 = math.degrees(XY(0,0).getAngle(XY(-(dist - x), -catB)))

                        curva1 = bezs2XYList(createArcBez(rA, rt, -rt))
                        curva1.reverse()
                        curva2 = bezs2XYList(createArcBez(r2, -180 + rt, -rt2),XY(-x, -catB))
                        curva3 = bezs2XYList(createArcBez(rB, rt2+180,180-rt2),XY(-dist, 0))
                        curva3.reverse()
                        curva4 = bezs2XYList(createArcBez(r2,  rt2,  180 - rt),XY(-x, catB))

                        curva1= curva1+curva2[1:]+curva3[1:]+curva4[1:]
                        sCurva1 = XYListSt(curva1, rotAB, PtA)

                        nn = self.addEle('path',pp,{'d':"M %s" % (sCurva1)})
                        self.estilo(nn,node)
# ################################################
# ################## O V A L #####################
# ################################################
                if joincirctype=='oval':
                    minR2 = dist + min(rA,rB)
                    if r2 < minR2:
                        r2 = minR2
                        info('Changed radius to '+str(minR2))
                    rad1 = r2 - rA
                    rad2 = r2 - rB
                    a = (math.pow(dist,2) - math.pow(rB+r2,2) + math.pow(rA+r2,2))/(dist*2)

                    rt = math.atan2(PtB.y - PtA.y, PtB.x - PtA.x)
                    D = dist #XY(PtA).sub(PtB).vlength() # distancia entre los centros
                    # distancia del centro 1 a la interseccion de los circulos
                    x = (D*D - rad2 * rad2 + rad1 * rad1) / (D*2)
                    catB = math.sqrt(rad1 * rad1 - x * x)

                    rotAB=XY(PtB).getAngle(PtA)
                    rot1 = math.degrees(XY(0,0).getAngle(XY(-x,-catB))) + 180.0                
                    curva1 = bezs2XYList(createArcBez(rA, -rot1, rot1))
                    curva1.reverse()
                    rot2 = math.degrees(XY(-dist,0).getAngle(XY(-x,-catB))) +180.0                
                    curva2 = bezs2XYList(createArcBez(r2, -rot2,-rot1),XY(-x,catB))
                    curva2.reverse()
                    curva3 = bezs2XYList(createArcBez(rB, rot2,-rot2),XY(-dist,0))
                    curva3.reverse()
                    curva4 = bezs2XYList(createArcBez(r2,  rot1,rot2),XY(-x,-catB))
                    curva4.reverse()
                    curva1= curva1+curva2[1:]+curva3[1:]+curva4[1:] #+curva3[1:]+curva4[1:]
                    sCurva1 = XYListSt(curva1, rotAB, PtA)
                    # curva1
                    nn = self.addEle('path',pp,{'d':"M %sZ" % (sCurva1),'style':'stroke-width:0.02;fill:#cc0000;stroke:#000000;'})
                    self.estilo(nn,node)
                if deleteorigin: node.getparent().remove(node)        

    def draw_shapes(self):
        tab = str(self.options.tab)
        sels = []
        for id, node in self.svg.selected.items():
            sels.append(node)
        if tab != '"extra"':
            for id, node in self.svg.selected.items():
                self.draw(node, tab)
        else:
            if len(sels)<2:
                inkex.errormsg('Select at least two objects')
            else:
                self.circsCone(sels, tab)

    def loc_str(self, str):
        return locale.format("%.f", float(str), 0)

    def effect(self):
        slices = self.draw_shapes()

if __name__ == "__main__":
    Shapes().run()