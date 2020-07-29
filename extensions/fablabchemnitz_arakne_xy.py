#!/usr/bin/env python3
'''
shapes.py

Copyright (C) 2015 Paco Garcia, www.arakne.es

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
# standard library
import locale, os, sys, tempfile, webbrowser, math 
import inkex, simplestyle, simpletransform

def info(s, newLine="\n"):
    sys.stderr.write(s.encode("UTF-8") + newLine)

def tern(condition,val1,val2):
    return val1 if condition else val2

class XY:
    """A class for creating Inkscape SVG Effects"""
    def __init__(self, *args, **kwargs):
        self.co=[0.0,0.0]
        lArgs=len(args)
        if lArgs>0:
            if lArgs==1:
                if type(args[0]==XY):
                    self.co=args[0].co
                else:
                    self.co=[args[0],args[0]]
            if lArgs>1:
                self.co=[args[0],args[1]]
    def __add__(self,xy):
        co=[self.co[0] + xy.co[0],self.co[1] + xy.co[1]]
        self.co = co
        return self
    def __sub__(self,xy):
        self.co=[self.co[0] - xy.co[0], self.co[1] - xy.co[1]]
        return self
    def __eq__(self,xy):
        return (self.co[0] == xy.x and self.co[1] == xy.y)

    def sub(self,xy):
        #self.co=[self.co[0] - xy.co[0],self.co[1] - xy.co[1]]
        self.__sub__(xy)
        return self
    def mul(self,xy):
        if type(xy)==XY:
            co=[self.co[0] * xy.co[0],self.co[1] * xy.co[1]]
        else:
            co=[self.co[0] * xy,self.co[1] * xy]
        self.co = co
        return self
    def div(self,xy):
        if type(xy)==XY:
            co=[self.co[0] / xy.co[0],self.co[1] / xy.co[1]]
        else:
            co=[self.co[0] / xy, self.co[1] / xy]
        self.co = co
        return self
    def vlength(self):
        return math.sqrt((self.co[0]*self.co[0])+(self.co[1]*self.co[1]))
		
    def rot(self,ang):
        x,y,sa,ca= (self.co[0], self.co[1], math.sin(ang), math.cos(ang))
        self.co=[ca * x  - sa * y, sa * x + ca * y]
        return self

    def Rot(self,p,r):
        self.co=[math.cos(r)*p,math.sin(r)*p]
        return self

    def rotate(self,rot,cX=0.0,cY=0.0):
        px = cX + (self.x-cX) * math.cos(rot) - (self.y-cY)*math.sin(rot)
        py = cY + (self.x-cX) * math.sin(rot) + (self.y-cY)*math.cos(rot)
        self.co = [px,py]
        return self
    def rotateD(self,rot,cX=0.0,cY=0.0):
        self.rotate(math.radians(rot),cX,cY)
        return self
    def VDist(self,V2):
        tmp = XY(self.co[0],self.co[1])
        tmp = tmp.sub(V2)
        return tmp.vlength()
    def st(self):
        return str(self.co[0])+','+str(self.co[1])
    @property
    def x(self):
        return self.co[0]
    @property
    def y(self):
        return self.co[1]
    def hipo(self,xy):
        return math.sqrt( math.pow(self.x-xy.x,2) + math.pow(self.y-xy.y,2) )
    def angBetween2Lines(self,p1,p2): # pC punto comun
        return math.atan2(self.y - p1.y, self.x - p1.x) - math.atan2(self.y - p2.y, self.x - p2.x)
    def getAngle(self,b):
        return math.atan2(b.y - self.y, b.x - self.x)
    def getAngleD(self,b):
        return math.degrees(math.atan2(b.y - self.y, b.x - self.x))   

# ________________________________________________________________
# ________________________________________________________________
# ________________________________________________________________
class bezpnt(object):
	def __init__(self,pfixed=None,pprev=None,pnext=None):
		if isinstance(pfixed, list):
			self.fixed = XY(pfixed[0],pfixed[1])
		else:
			self.fixed = pfixed
		if isinstance(pprev, list):
			self.prev = XY(pprev[0],pprev[1])
		else:
			self.prev = pprev
		if isinstance(pnext, list):
			self.next = XY(pnext[0],pnext[1])
		else:
			self.next = pnext
		return

	def translate(self,x,y):
		self.fixed + XY(x,y)
		if self.prev!=None:self.prev + XY(x,y)
		if self.next!=None:self.next + XY(x,y)
		return self
	def scale(self,x=1.0,y=1.0):
		self.fixed.scale(x,y)
		if self.prev!=None:self.prev.scale(x,y)
		if self.next!=None:self.next.scale(x,y)
		return self
	def rotate(self,rot,cX=0.0,cY=0.0):
		self.fixed.rotate(rot,cX,cY)
		if self.prev!=None:self.prev.rotate(rot,cX,cY)
		if self.next!=None:self.next.rotate(rot,cX,cY)
		return self
	def skew(self,rotx,roty,cX=0.0,cY=0.0):
		self.fixed.skew(rotx,roty,cX,cY)
		if self.prev!=None:self.prev.skew(rotx,roty,cX,cY)
		if self.next!=None:self.next.skew(rotx,roty,cX,cY)
		return self
	def copy(self,bez2):
		try:
			self.fixed=XY().copy(bez2.fixed)
			self.prev = None if bez2.prev == None else XY().copy(bez2.prev)
			self.next = None if bez2.next == None else XY().copy(bez2.next)
		except Exception as e:
			gimp.message(str(e))
		return self
	def arrXY(self):
		pts=[]
		if self.prev == None:
			pts+=self.fixed.arrXY(1)
		else:
			pts+=self.prev.arrXY(1)
		pts+=self.fixed.arrXY(1)
		if self.next==None:
			pts+=self.fixed.arrXY(1)
		else:
			pts+=self.next.arrXY(1)
		return pts
	def Prev(self):
		p = self.prev
		if p==None: p=self.fixed
		return p
	def Next(self):
		p = self.next
		if p==None: p=self.fixed
		return p
	def Fixed(self):
		return self.fixed
	def flip(self):
		p=self.prev
		n=self.next
		self.prev=n
		self.next=p

def createSmallArcBez(r, a1, a2,rot):
	a = (a2 - a1) * 0.5
	p4 = XY(r * math.cos(a), r * math.sin(a))
	p1 = XY(p4.x, -p4.y)
	k = 0.5522847498
	f = k * math.tan(a)
	p2 = XY(p1.x + f * p4.y, p1.y + f * p4.x)
	p3 = XY(p2.x,-p2.y)
	ar = a + a1
	P1 = XY(r * math.cos(a1), r * math.sin(a1)).rotate(rot)
	P2 = XY(p2.x, p2.y).rotate(ar).rotate(rot)
	P3 = XY(p3.x, p3.y).rotate(ar).rotate(rot)
	P4 = XY(r * math.cos(a2),r * math.sin(a2)).rotate(rot)
	B1=bezpnt(P1,None,P2)
	B2=bezpnt(P4,P3)
	return [B1,B2]

def createArcBez(rad, sAng, eAng):
	EPSILON = 0.0000000001
	bezs =[]
	if eAng < sAng:
		eAng += 360.0
	sAng = math.radians(sAng)
	eAng = math.radians(eAng)
	rot = sAng
	sAng = math.radians(0)
	eAng = eAng - rot
	pi2 = math.pi * 2
	sAng, eAng = (sAng % pi2, eAng % pi2)
	pi_2 = math.pi * 0.5
	sign = 1 if (sAng < eAng) else -1
	a1 = sAng
	totAng = min(math.pi * 2, abs(eAng - sAng))
	while (totAng > EPSILON):
		a2 = a1 + sign * min(totAng, pi_2)
		bezs.extend(createSmallArcBez(rad, a1, a2,rot))
		totAng = totAng - abs(a2 - a1)
		a1 = a2
	return bezs

def bezs2XYList(arc1,transform = None):
    pnts=[]
    bezs=[]
    for aa in arc1:
        if aa.prev != None: 
            bezs.append(XY(aa.prev))
        bezs.append(XY(aa.fixed))
        if aa.next!=None:
            bezs.append(XY(aa.next))
    for i in range(len(bezs)):
        v = bezs[i]
        if transform:
            v = v + transform
        if i == 0:
            pnts.append(v)
        else:
            v2=pnts[-1]
            if (v2.x != v.x or v2.y != v.y):
                pnts.append(XY(v))
    a=len(pnts)
    return pnts

def XYList(lst, rot = 0.0, add = None):
    verts=[]
    for nn in range(len(lst)):
        v = lst[nn]
        if rot != 0.0: v = v.rotate(rot)
        if add: v = v + add
        verts.append([v.x,v.y])
    return verts

def XYListSt(lst, rot = 0.0, add = None):
    D2 = ""
    for nn in range(len(lst)):
        v = lst[nn]
        if rot != 0.0: v = v.rotate(rot)
        if add: v = v + add
        D2 += "%s%s " % (tern(nn==1,"C",""), v.st())
    return D2

# circle by quadrants, A: 0>90, B: 90>180, C: 180>270, D: 270>360
def circQ(p,r,abcd="ABCD",inverse=0,xtra=None):
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
    if inverse==1: pA.reverse()
    listA = XYList(pA)
    if xtra:
        for n in xtra:
            listA[n].extend(xtra[n])
    return listA

def circleInCircle(c1,r1,c2,r2):
    d = c1.hipo(c2)
    return tern((r1 > (d + r2)),True,False)