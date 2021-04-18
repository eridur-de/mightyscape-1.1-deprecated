#!/usr/bin/env python
'''
shapes_1.py

Copyright (C) 2015 - 2020 Paco Garcia, www.arakne.es

2017_07_30: added crossed corners
			copy class of original object if exists
2017_08_09: rombus moved to From corners tab
2017_08_17: join circles not need boolen operations now
			join circles added Oval
2017_08_25: fixed error in objects without style
			
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
import locale, os, sys, tempfile, webbrowser, math, simplepath
from lxml import etree

try:
	from subprocess import Popen, PIPE
	bsubprocess = True
except:
	bsubprocess = False

import inkex
from inkex.transforms import BoundingBox

from arakne_xy import *

defStyle = [['stroke-width','0.5'],['fill','#f0ff00'],['stroke','#ff0000']]

locale.setlocale(locale.LC_ALL, '')

# ####################################################3

def calcCircle(pt1, pt2, pt3):
	D_a = XY(pt2)-pt1
	D_b = XY(pt3)-pt2
	m_C = XY()
	Min = 0.000000001

	m_dRadius= 0

	if (abs(D_a.x) <= Min and abs(D_b.y) <= Min):
		m_C= XY(0.5*(pt2.x + pt3.x), 0.5*(pt1.y + pt2.y))
		m_dRadius= vlength(m_C,pt1)		# calc. radius

	aSlope = D_a.y / D_a.x

	if D_b.x == 0:
		bSlope = D_b.y
	else:
		bSlope = D_b.y / D_b.x
	if (abs(aSlope-bSlope) <= Min): # checking if given points are colinear.
		return [-1,-1,-1]
	# calc center
	m_Cx= (aSlope * bSlope * (pt1.y - pt3.y) + bSlope * ( pt1.x + pt2.x ) - aSlope * ( pt2.x + pt3.x ) )/( 2 * ( bSlope - aSlope) )
	m_Cy = -1*(m_Cx - (pt1.x + pt2.x) / 2 ) / aSlope +  (pt1.y + pt2.y)/2
	v1 = XY(m_Cx,m_Cy).VDist(pt2)
	return {'c':XY(m_Cx,m_Cy),'r':v1}

# ####################################################3

class Shapes(inkex.Effect):
	def addOpt(self, name, Type=str, Default=""):
		self.arg_parser.add_argument("--" + name, action="store", type=Type, dest=name, default=Default, help="")

	def __init__(self):
		inkex.Effect.__init__(self)
		#sOP = self.OptionParser
		sOP = self.arg_parser
		for n in ["tab","chamfertype","midtype","objid","tab_from_bb"] : self.addOpt(n)
		for n in ["size","midsize","incdec","spikesep","spikeheight","joinradius","objsize","reducey"] : self.addOpt(n, float, 0.0)
		for n in ["arrowWidth","fntsize"] : self.addOpt(n, float, 10.0)
		for n in ["tritype", "spikestype","spikesdir","spikesdirt","spikesdirr","spikesdirb","spikesdirl","unit"] : self.addOpt(n)
		self.addOpt("spikesize", float, "2.0")
		self.addOpt("arrowtype")
		self.addOpt("headWidth",float,"20.0")
		self.addOpt("headHeight",float,"40.0")
		for n in ["squareselection", "trihside","trivside","copyfill", "fromCornersInv", "deleteorigin"] : self.addOpt(n, inkex.Boolean, "false")
		sOP.add_argument("--joincirctype", action="store", type=str, dest="joincirctype", default="", help="" )

		# para from nodes
		for n in ["obj","posh","posv"] : self.addOpt(n)
		sOP.add_argument("--maxdecimals", action="store", type=int, dest="maxdecimals", default="6", help="" )

		for n in ["ordery", "rotpath"] : self.addOpt(n, inkex.Boolean, "false")

	def getU(self, val):
		return self.svg.unittouu(str(val)+self.options.unit)

	def addEle(self, ele, parent, props):
		#elem = inkex.etree.SubElement(parent, ele)
		elem = etree.SubElement(parent, ele)
		for n in props: elem.set(n,props[n])
		return elem

	def chStyles(self,node,sty):
		style = dict(inkex.Style.parse_str(node.get('style')))
		for m in list(style):
			sys.stderr.write(m)
		for n in sty:
			if n[0] in style: style.pop(n[0], None)
			if n[1]!="": style[n[0]]=n[1]
		node.set('style',inkex.Style(style))

	# def unit2uu(self, val):	
		# if hasattr(self,"unittouu") is True:
			# return self.svg.unittouu(val)
		# else:
			# return inkex.unittouu(val)

	# def u2uu(self,value):
		# if hasattr(inkex, 'unittouu'):
			# v = inkex.unittouu(value)
		# else:
			# v = self.unittouu(value)
		# return v

	def limits(self, node):
		s = node.bounding_box()
		incdec = self.getU(self.options.incdec)
		l,r,t,b,an,al = (s.left-incdec, s.right+incdec, s.top-incdec, s.bottom+incdec, s.width+incdec*2, s.height+incdec*2)
		return (l,r,t,b,an,al)

	def copyProp(self, orig, dest, prop):
		if orig.get(prop):
			dest.set(prop, orig.get(prop))

	def estilo(self, nn, orig, style=defStyle):
		if self.options.copyfill:
			self.copyProp(orig, nn, 'style')
			self.copyProp(orig, nn, 'class')
		else:
			self.chStyles(nn,style)

	def circleABCD(self,p,r,abcd="ABCD",inverse=False,xtra=None):
		aa = r * 0.551915024494
		parts={
			'A':[XY(0,-r),XY(aa,-r), XY(r, -aa),XY(r,0)],
			'B':[XY(r,0), XY(r, aa), XY(aa,  r),XY(0,r)],
			'C':[XY(0,r), XY(-aa,r), XY(-r, aa),XY(-r,0)],
			'D':[XY(-r,0),XY(-r,-aa),XY(-aa,-r),XY(0,-r)]}
		pA = [XY(p)+N for N in parts[abcd[0]]]
		for aa in abcd[1:]:
			pA = pA + [XY(p)+N for N in parts[aa][1:]]
		if inverse==True: pA.reverse()
		listA = XYList(pA)
		if xtra:
			for n in xtra:
				listA[n].extend(xtra[n])
		return listA

	# def getMed(self, id):
		# #query inkscape about the bounding box of obj
		# q = {'width':0,'height':0}
		# file = self.args[-1]
		# scale = self.unittouu('1px') # convert to document units
		# for query in q.keys():
			# ss = 'inkscape --query-%s --query-id=%s "%s"' % (query,id,file)
			# if bsubprocess:
				# info('bsubprocess')
				# p = Popen(ss, shell=True, stdout=PIPE, stderr=PIPE)
				# rc = p.wait()
				# aaa = p.stdout.read()
				# q[query] = aaa
				# err = p.stderr.read()
			# else:
				# f,err = os.popen3(ss)[1:]
				# q[query] = scale * float(f.read())
				# f.close()
				# err.close()
		# return q

	def pillows(self, type, a, node, l, t, r, b, cX, cY):
		pts = []
		if type=="pillowrect":   cnrs=[XY(l,t), XY(r,t), XY(r,b), XY(l,b)]
		if type=="pillowrombus": cnrs=[XY(l,t+cY), XY(l+cX,t), XY(r,t+cY), XY(r-cX,b)]
		aa = a
		for n in range(0,len(cnrs)-1):
			pts.append(cnrs[n])
			pts.append(XY(cnrs[n]).atMid(cnrs[n+1]) + XY(0,aa).rot(cnrs[n].getAngle(cnrs[n+1])))
		n=len(cnrs)-1
		pts.append(cnrs[n])

		pM = XY(cnrs[n]).atMid(cnrs[0]) + XY(0,aa).rot(cnrs[n].getAngle(cnrs[0]))
		pts.append(pM)

		s = ''

		for n in range(0,int(len(pts)/2)-1):
			nnA = calcCircle(pts[n*2], pts[n*2+1], pts[n*2 + 2])
			s = s + ' ' + setArc(nnA['c'].x, nnA['c'].y, nnA['r'], nnA['c'].getAngle(pts[n*2+2]), nnA['c'].getAngle(pts[n*2]), 1 if n==0 else 0)
		n = len(pts)
		nnA = calcCircle(pts[n-2], pts[n-1], pts[0])
		s = s + ' ' + setArc(nnA['c'].x, nnA['c'].y, nnA['r'], nnA['c'].getAngle(pts[0]), nnA['c'].getAngle(pts[n-2]), 0)
		shp = addChild(node.getparent(), 'path',{'d': s+" Z"})
		self.estilo(shp,node)

	def draw(self, node, sh='rombus'):
		if (node.tag == inkex.addNS('text','svg')):
			return
		sO = self.options
		l, r, t, b, an, al = self.limits(node)
		sqSel = sO.squareselection
		tInv = sO.fromCornersInv
		copyfill = sO.copyfill
		deleteorigin = sO.deleteorigin

		side = min(al,an)
		if sqSel:
			incx=(an-side)/2.0
			l,r,an =(l+incx,r-incx,side)
			incy=(al-side)/2.0
			t +=incy
			b -=incy
			al = side
		cX, cY = (an/2.0,al/2.0)
		sub_bb = sO.tab_from_bb
		pp = node.getparent()
		varBez = 0.551915024494

		a = self.getU(sO.size) if sub_bb=="chamfer" else self.getU(sO.midsize)

		a_2, a2 = (a / 2.0,a * 2.0)
		dS = "m %sz"
		pnts = [[l+cX,t],[cX,cY],[-cX,cY],[-cX,-cY]]
		aa = a * varBez
		chtype = sO.chamfertype
		midtype = sO.midtype
		
		an2, al2 = ((an-a)/2.0,(al-a)/2.0)
		tritype = sO.tritype
		if sh == 'bbox':
			if midtype=="rombus" and a>0: pnts=[[l+cX - a_2,t],[a,0],[an2,al2],[0,a],[-an2,al2],[-a,0],[-an2,-al2],[0,-a]]
			if (sub_bb=='mid'):
				if midtype=="chamfer":
					if tInv==False:
						pnts=[[l+a,t],[an - a2,0],[a,a],[0,al-a2],[-a,a],[-(an - a2),0],[-a,-a],[0,-(al-a2)]]
					else:
						pnts=[[l,t],[a,0],[-a,a],[an-a,0," z m"],[a,0],[0,a],[a,al," z m"],[0,-a],[-a,a],[-an+a,0," z m"],[-a,-a],[0,a]]
				if midtype=="cross":
					pnts=[[l+an2,t],[a,0],[0,al2],[an2,0],[0,a],[-an2,0],[0,al2],[-a,0],[0,-al2],[-an2,0],[0,-a],[an2,0]]
				if midtype=="starcenter":
					pnts=[[l+cX,t],[a_2,al2], [an2,a_2], [-an2,a_2],[-a_2,al2],[-a_2,-al2],[-an2,-a_2],[an2,-a_2]]

				if midtype=="pillowrombus":
					self.pillows(midtype, a, node, l, t, r, b, cX, cY)
					pnts  = []
					if deleteorigin: node.delete()

			if (sub_bb=='chamfer'):
				if chtype=="chamfer":
					if tInv==False:
						pnts=[[l+a,t],[an - a2,0],[a,a],[0,al-a2],[-a,a],[-(an - a2),0],[-a,-a],[0,-(al-a2)]]
					else:
						pnts=[[l,t],[a,0],[-a,a],[an-a,0," z m"],[a,0],[0,a],[a,al," z m"],[0,-a],[-a,a],[-an+a,0," z m"],[-a,-a],[0,a]]
				if chtype=="round":
					if tInv==False:
						pnts = circQ(XY(l,t),a,"B",0,{1:"C"}) + circQ(XY(l,b),a,"A",0,{0:"L",1:"C"}) + circQ(XY(r,b),a,"D",0,{0:"L",1:"C"}) + circQ(XY(r,t),a,"C",0,{0:"L",1:"C"})
					else:
						pnts=[[l,t],[a,0],[0,aa,"c "],[-aa,a],[-a,a],[an-a,0,"z m "],[a,0],[0,a],[-aa,0," c"],[-a,-aa],[-a,-a],
							[a,al-a,"z m "],[0,a],[-a,0],[0,-aa,"c "],[aa,-a],[a,-a],[-an,0,"z m "],[0,a],[a,0],[0,-aa,"c "],[-aa,-a],[-a,-a]]
				if chtype=="roundinv":
					pnts=[[l,t],[a,0],[0,aa,"c "],[-aa,a],[-a,a],[an-a,0,"z m "],[a,0],[0,a],[-aa,0," c"],[-a,-aa],[-a,-a],
						[a,al-a,"z m "],[0,a],[-a,0],[0,-aa,"c "],[aa,-a],[a,-a],[-an,0,"z m "],[0,a],[a,0],[0,-aa,"c "],[-aa,-a],[-a,-a]]
				if chtype=="rect":
					pnts=[[l+a,t],[an - a2,0],[0,a],[a,0],[0,al-a2],[-a,0],[0,a],[-(an-a2),0],[0,-a],[-a,0],[0,-(al-a2)],[a,0]]
				if chtype=="starcorners":
					pnts=[[l,t],[cX,al2],[cX,-al2],[-an2,cY],[an2,cY],[-cX,-al2],[-cX,al2],[an2,-cY]]
				if chtype=="crosscornersquad":
					pnts=[[l-a,t],[0,-a],[a,0],[0,al+a*2],[-a,0],[0,-a],[an+a*2,0],[0,a],[-a,0],[0,-al-a*2],[a,0],[0,a]]
				if chtype=="crosscornerstri":
					pnts=[[l-a,t], [a,-a], [0,al+a*2], [-a,-a], [an+a*2,0], [-a,a], [0,-al-a*2],[a,a]]
				if chtype=="crosscornersround":
					dS = "M %sZ"
					aa2 = a_2 * varBez
					p1 = circQ(XY(r + a_2, t - a_2),a_2,"DAB",1)
					p2 = circQ(XY(r + a_2, b + a_2),a_2,"ABC",1)
					p3 = circQ(XY(l - a_2, b + a_2),a_2,"BCD",1)
					p4 = circQ(XY(l - a_2, t - a_2),a_2,"CDA",1)
					pnts = p1 + [[r,t],[r,b+a_2-aa2]] + p2 + [[r+a_2-aa2,b],[l-a_2+aa2,b]] + p3 + [[l,b+a_2-aa],[l,t-a_2+aa]] + p4
					pnts[1].append(" C")

				if chtype=="pillowrect":
					pts = []
					self.pillows(chtype, a, node, l, t, r, b, cX, cY)
					pnts  = []
					dS = "M %sZ"
					if deleteorigin: node.delete()
				if chtype == "spiralrect":
					An, Al = (an, al)
					pnts = [[l,t], [An,0], [0,Al], [-An,0], [0,-Al+a]]
					An = An - a
					Al = Al - a*2
					tot = min(An//a,Al//a) // 2 + 1

					for n in range(0,int(tot)):
						pnts.append([An,0])
						An = An-a
						if Al>a:
							pnts.append([0,Al])
							Al=Al-a
						else:
							break
						if An>a:
							pnts.extend([[-An,0]])
							An = An-a
						else:
							break
						if Al>0:
							pnts.extend([[0, -Al]])
							Al=Al-a
						else:
							break

					#   ________________
					#   ______________  |
					#  |  __________  | |
					#  | |____________| |
					#  |________________|

					defStyle = [['stroke-width','2.5'],['fill','none'],['stroke','#ff0000']]
					dS = "m %s"

			if (sub_bb=='spikes'): pnts = self.triSpikes(sO, an, al, l, t)

			if sub_bb=='arrow':
				pnts = self.drawArrow(sO, an, al, l, t)
				if sO.arrowtype=="arrowstick":
					dS = "m %s"

			if sub_bb=='triangles':
				trihside, trivside=(sO.trihside, sO.trivside)
				if tritype=="isosceles": pnts=[[l+cX,t],[cX,al],[-an,0]]
				if tritype=="equi":
					sqrt3 = 1.7320508075
					height = sqrt3/2 * side
					tcx, tcy = ((an - side)/2.0, (al - height)/2.0)
					pnts=[[cX+l,t+tcy],[an/2.0-tcx,height],[-side,0]]
				if tritype=="rect":
					x1 = l + tern(not trivside and trihside,an,0)
					x2 = tern(not trivside and trihside,0,an)
					x3 = tern(trivside and trihside,0,-an)
					pnts=[[x1,t], [x2,tern(not trivside,al,0)], [x3,tern(not trivside,0,al)]]
				# #######################################
				if tritype=="circi" or tritype=="circe" or tritype=="trii":
					# get verts
					pnts = []
					if node.get('d'):
						p = node.path.to_superpath().to_path().to_arrays()
						vs=[]
						for cmd, params in p:
							if cmd != 'Z' and cmd != 'z':
								vs.append(XY(params[-2],params[-1]))
						if len(vs)>2:
							if tritype == "trii":
								p1 = XY(vs[0]) + (XY(vs[1])-vs[0]).div(2)
								p2 = XY(vs[1]) + (XY(vs[2])-vs[1]).div(2)
								p3 = XY(vs[2]) + (XY(vs[0])-vs[2]).div(2)
								pnts = [p3.co,(p1-p3).co,((p2-p1)-p3).co]
							if tritype == "circi" or tritype == "circe":
								if tritype == "circi":
									rad, px, py = circleInscribedInTri(vs[0], vs[1], vs[2])
								if tritype == "circe":
									rad, px, py = TriInscribedInCircle(vs[0], vs[1], vs[2])
								nn = svgCircle(node.getparent(), rad, px, py)
								self.estilo(nn,node)
								pnts=[]
								if deleteorigin: node.delete()
		if sh=='nodes':
			# get verts
			obj, posh, posv, objS, oY =(sO.obj, int(sO.posh), int(sO.posv), sO.objsize, sO.ordery)
			reducey = sO.reducey
			o2 = objS/2
			pnts = []
			orderY = []
			if node.get('d'):
				p = node.path.to_arrays()
				vs = []
				minY, maxY, prevX, prevY = (100000.0, -100000.0, 0, 0)
				for cmd, params in p:
					if cmd != 'Z' and cmd != 'z':
						posY = prevY
						posX = prevX
						posY = params[-1]
						if cmd in ['h','H']:
							posY = prevY
							posX = params[-1]
						elif cmd not in ['v','V','h','H']:
							posX = params[-2]
						vs.append(XY(posX, posY))
						prevX, prevY, minY, maxY = (posX, posY, min(posY, minY), max(posY, maxY))
				objs = []
				dist = maxY - minY
				grp = addChild(node.getparent(), 'g',{})
				self.copyProp(node, grp, 'transform')
				self.estilo(grp,node)

				if obj == "obj":
					oi = sO.objid
					este = self.svg.getElementById('%s' % oi)
					if este == None:
						obj='c'
					else:
						l1, r1, t1, b1, an1, al1 = self.limits(este)
						w2, h2 = (an1/2 , al1/2)
				for n in range(0,len(vs)):
					if obj == "number":
						nn = self.addTxt(grp, str(vs[n].x), str(vs[n].y), str(n))
					if obj=="obj":
						if este != None:
							reduce = (100 - (reducey * ((maxY - vs[n].y) / dist)))/100
							px = str(vs[n].x / reduce - l1 - w2 + w2 * posh)
							py = str(vs[n].y / reduce - t1 - h2 + h2 * posv)
							nn = addChild(grp,'use',{inkex.addNS('href',"xlink"):"#"+oi,'x':px,'y':py, "transform":"scale(%f)" % (reduce)})
						else:
							obj='c'
					reduce = (o2 / 100 * reducey) * (maxY - vs[n].y) / dist
					O2 = o2 - reduce
					if obj=="c":
						pxy = vs[n] + XY(posh, posv).mul(O2)
						nn = svgCircle(grp, O2, pxy.x, pxy.y)
					if obj=="s":
						pxy = vs[n] - XY(O2) + XY(O2 * posh, O2 * posv)
						nn = addChild(grp,'rect',{'height':str(O2*2), 'width':str(O2*2), 'x':str(pxy.x), 'y':str(pxy.y)})
					if obj=="number":
						nn = self.addTxt(grp, str(vs[n].x), str(vs[n].y), str(n))
					if obj=="coords":
						maxDec=sO.maxdecimals
						nn = self.addTxt(grp, str(vs[n].x), str(vs[n].y), str(round(vs[n].x, maxDec)) + "," + str(round(vs[n].y, maxDec)))
					orderY.append([vs[n].y,nn])
					#self.estilo(nn,node)
				if sO.ordery:
					def myFunc(e):
						return e[0]
					orderY.sort(key=myFunc)
					for item in orderY:
						grp.append( item[1])
			if deleteorigin: node.delete()
			# ##############################3

		d = ""
		if len(pnts)>0:
			for n in pnts:
				ss = "" if len(n)<3 else n[2]
				d += "%s%s,%s " % (ss, str(n[0]),str(n[1]))
			nn = self.addEle('path',pp, {'d':dS % (d)})
			self.estilo(nn,node)
			if deleteorigin: node.delete()

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
		new.set('style','text-align:center; vertical-align:bottom; font-size:%s; fill-opacity:1.0; stroke:none; font-weight:normal; font-style:normal; fill:#000000' % self.options.fntsize)
		new.set('dy', str(dy))
		new.text = str(text)
		return new2

	def circsCone(self, sels, sh='rombus'):
		sO = self.options
		copyfill = sO.copyfill
		deleteorigin = sO.deleteorigin
		joincirctype = sO.joincirctype
		r2 = sO.joinradius
		cssEmpty = [['stroke-width','0.5'],['fill','none'],['stroke','#ff0000']]

		strEmpty = 'stroke-width:0.02; fill:none; stroke:#000000; stroke-dasharray:0.5,0.2; stroke-dashoffset:0;'

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
					#D2 = math.sqrt((dist*dist) - (rDif*rDif)) / dist
					D2 = triCat(dist, rDif) / dist
					P1 = XY(Axis).mul(rA / dist)
					P2 = XY(-dist,0) + XY(Axis).mul(rB / dist)
					r = P1.VDist(P2)
					Rot1 = XY(P2.x,rB * D2).getAngleD(XY(P2.x + r, rA * D2))
					aBez=createArcBez(rA,-90 -Rot1, -270 + Rot1)
					curva1a = bezs2XYList(aBez)
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
						a = ( pow2(dist) - pow2(rB+r2) + pow2(rA+r2))/(dist*2)
					else:
						r2 = dist - rA - rB
						rad1 = dist - rB
						rad2 = dist - rA
						a = (pow2(dist-rB) - pow2(dist-rA) + pow2(dist))/(dist*2);   
					# alineamos las esferas en Y

					rt = math.atan2(PtB.y - PtA.y, PtB.x - PtA.x)
					# # distancia del centro 1 a la interseccion de los circulos
					x = (dist * dist - rad2 * rad2 + rad1 * rad1) / (dist*2)
					if (rad1 * rad1 - x * x) > 0 :
						#catB = math.sqrt(rad1 * rad1 - x * x)
						catB = triCat(rad1, x)

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
					a = ( pow2(dist) - pow2(rB+r2) + pow2(rA+r2))/(dist*2)

					rt = math.atan2(PtB.y - PtA.y, PtB.x - PtA.x)
					D = dist #XY(PtA).sub(PtB).vlength() # distancia entre los centros
					# distancia del centro 1 a la interseccion de los circulos
					x = (D*D - rad2 * rad2 + rad1 * rad1) / (D*2)
					# catB = math.sqrt(rad1 * rad1 - x * x)
					catB = triCat(rad1, x)

					rotAB=XY(PtB).getAngle(PtA)
					rot1 = math.degrees(XY(0,0).getAngle(XY(-x,-catB))) + 180.0
					curva1 = bezs2XYList(createArcBez(rA, -rot1, rot1))
					curva1.reverse()
					#rot2 = math.degrees(XY(-dist,0).getAngle(XY(-x,-catB))) +180.0
					rot2 = XY(-dist,0).getAngleD(XY(-x,-catB)) +180.0
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
				if deleteorigin: node.delete()

	def drawArrow(self, sO, an, al, l, t):
		arrowType = sO.arrowtype
		headH, headW, arrowW = (self.getU(sO.headHeight), self.getU(sO.headWidth), self.getU(sO.arrowWidth))
		hw2=headW/2.0
		cX = an/2.0
		if arrowType=="arrowfilled":
			pnts=[[l+cX,t],[hw2,headH],[-(headW-arrowW)/2.0,0],[0,al-headH],[-arrowW,0],[0,-(al-headH)],[-(headW-arrowW)/2.0,0]]
		else:
			#dS = "m %s"
			pnts=[[l+cX,t],[0,al],[-hw2,-al+headH,"m "],[hw2,-headH],[hw2,headH]]
		return pnts

	def triSpikes(self, sO, an, al, l, t):
		spktype, spikesdir, sh, ssep = (sO.spikestype, sO.spikesdir, sO.spikeheight, self.getU(sO.spikesep))
		ss = self.getU(sO.spikesize)
		anX, anY = (int( (an + ssep) / (ss * 2 + ssep)), int( (al+ssep) / (ss * 2 + ssep)))
		iniX, iniY = (((an+ssep) - (anX * (ss * 2 + ssep))) / 2.0, ((al+ssep) - (anY * (ss * 2 + ssep))) / 2.0)
		if spktype=="trirect" or spktype=="squ":
			anX, anY = ( int((an + ssep) / (ss + ssep)), int((al + ssep) / (ss + ssep)) )
			iniX, iniY = (((an + ssep) - (anX * (ss + ssep))) / 2.0, ((al + ssep) - (anY * (ss + ssep))) / 2.0)
		dir = 1
		pnts = [[l,t],[iniX,0]]

		if spikesdir=='ins': dir = -1.0
		#if spktype=="tri" or spktype=="trirect" or spktype=="squ":
		if spktype in ["tri", "trirect", "squ"]:
			sDir = sO.spikesdirt # --------------------------------TOP---------------------
			if sDir=='pre': sDir = spikesdir
			if sDir=='non':
				pnts = [[l,t],[an,0]]
			else :
				dirT = 1
				if sDir=='ins': dirT = -1.0
				for n in range(anX):
					if sDir=='alt' : dirT = 1 if n % 2 == 1 else -1
					if spktype=="tri":     pnts.extend([[ss,-sh*dirT],[ss,sh*dirT]])
					if spktype=="trirect": pnts.extend([[0,-sh*dirT],[ss,sh*dirT]])
					if spktype=="squ":     pnts.extend([[0,-sh*dirT],[ss,0],[0,sh*dirT]])
					if ssep != 0 and n < (anX-1): pnts.append([ssep,0])
				pnts.append([iniX,0])
			sDir = sO.spikesdirr # ---------------------------------RIGHT-------------------
			if sDir == 'pre' : sDir = spikesdir
			if sDir == 'non' : 
				pnts.append([0,al])
			else : 
				pnts.append([0,iniY])
				dirR = -1.0 if sDir=='ins' else 1.0
				for n in range(anY):
					if sDir == 'alt' : dirR = 1 if n % 2 == 1 else -1  
					if spktype=="tri":     pnts.extend([[sh*dirR,ss],[-sh * dirR,ss]])
					if spktype=="trirect": pnts.extend([[sh*dirR,0],[-sh * dirR,ss]])
					if spktype=="squ":     pnts.extend([[sh*dirR,0],[0,ss],[-sh * dirR,0]])
					if ssep != 0 and n < (anY-1): pnts.append([0, ssep])
				pnts.append([0,iniY])
			sDir = sO.spikesdirb # -------------------------------BOTTOM--------------------
			if sDir == 'pre' : sDir = spikesdir
			if sDir == 'non' :
				pnts.append([-an,0])
			else : 
				pnts.append([-iniX,0])
				dirB = -1.0 if sDir=='ins' else 1.0
				for n in range(anX):
					if sDir == 'alt' : dirB = 1 if n % 2 == 1 else -1  
					if spktype=="tri":     pnts.extend([[-ss,sh*dirB],[-ss,-sh*dirB]])
					if spktype=="trirect": pnts.extend([[0,sh*dirB],[-ss,-sh*dirB]])
					if spktype=="squ":     pnts.extend([[0,sh*dirB],[-ss,0],[0,-sh*dirB]])
					if ssep != 0 and n < (anX-1): pnts.append([-ssep,0])
				pnts.append([-iniX,0])
			sDir = sO.spikesdirl # --------------------------------------LEFT---------------
			if sDir == 'pre' : sDir = spikesdir
			if sDir != 'non' :
				pnts.append([0,-iniY])
				dirL = -1.0 if sDir=='ins' else 1.0
				#sDir = sO.spikesdir
				for n in range(anY):
					if sDir == 'alt' : dirL = 1 if n % 2 == 1 else -1
					#pnts.extend([[-sh*dirL,-ss],[sh*dirL,-ss]])
					if spktype=="tri":     pnts.extend([[-sh*dirL,-ss],[sh*dirL,-ss]])
					if spktype=="trirect": pnts.extend([[-sh*dirL,0],  [sh*dirL,-ss]])
					if spktype=="squ":     pnts.extend([[-sh*dirL,0],  [0,-ss],[sh * dirL,0]])
					if ssep != 0 and n < (anY-1): pnts.append([0, -ssep])
		###########################################
		varBez = 0.551915024494
		if spktype in ["rnd", "wav"]:
			dif, difh, dBez, dBezh = (ss-(ss*varBez), sh-(sh*varBez), ss*varBez, sh*varBez)
			sDir = sO.spikesdirt # --------------------------------TOP---------------------
			if sDir=='pre': sDir = spikesdir
			if sDir=='non':
				pnts = [[l,t],[an,0],[0,iniY]]
			else :
				dirT = -1.0 if sDir=='ins' else 1.0
				for n in range(anX):
					if sDir=='alt' : dirT = 1 if n % 2 == 1 else -1
					if spktype == "rnd": pnts.extend([[0,-dBezh*dirT," c"],[dif,-sh*dirT],[ss,-sh*dirT],[dBez,0],      [ss,difh*dirT],[ss,sh*dirT]]) #fijo
					if spktype == "wav": pnts.extend([[0,-dBezh*dirT," c"],[dif,-sh*dirT],[ss,-sh*dirT],[0,dBezh*dirT],[dBez,sh*dirT],[ss,sh*dirT]]) #fijo
					if ssep!=0 and n < (anX-1): pnts.append([ssep,0,' l'])
				pnts.extend([[iniX,0,' l'],[0,iniY]])
			sDir = sO.spikesdirr # ---------------------------------RIGHT-------------------
			if sDir == 'pre' : sDir = spikesdir
			if sDir == 'non' : 
				pnts.extend([[0,al - iniY],[-iniX,0]])
			else : 
				dirR = -1.0 if sDir=='ins' else 1.0
				for n in range(anY):
					if sDir == 'alt' : dirR = 1 if n % 2 == 1 else -1  
					if spktype == "rnd": pnts.extend([[dBezh*dirR,0," c"],[sh*dirR,dif],[sh*dirR,ss], [0,dBez]       ,[-difh*dirR,ss], [-sh*dirR,ss]]) #fijo
					if spktype == "wav": pnts.extend([[dBezh*dirR,0," c"],[sh*dirR,dif],[sh*dirR,ss], [-dBezh*dirR,0],[-sh*dirR,dBez], [-sh*dirR,ss]]) #fijo
					if ssep!=0 and n < (anY-1): pnts.append([0, ssep,' l'])
				pnts.extend([[0,iniY,' l'],[-iniX,0]])
			sDir = sO.spikesdirb # -------------------------------BOTTOM--------------------
			if sDir == 'pre' : sDir = spikesdir
			if sDir == 'non' :
				pnts.extend([[-an + iniX,0],[0,-iniY]])
			else : 
				dirB = -1.0 if sDir=='ins' else 1.0
				for n in range(anX):
					if sDir == 'alt' : dirB = 1 if n % 2 == 1 else -1  
					if spktype == "rnd": pnts.extend([[0,dBezh*dirB," c"],[-dif,sh*dirB],[-ss,sh*dirB],[-dBez,0],[-ss,-difh * dirB],[-ss,-sh * dirB]]) #fijo
					if spktype == "wav": pnts.extend([[0,dBezh*dirB," c"],[-dif,sh*dirB],[-ss,sh*dirB],[0,-dBezh*dirB],[-dif, -sh*dirB],[-ss,-sh * dirB]]) #fijo
					if ssep!=0 and n < (anX-1): pnts.append([-ssep,0,' l'])
				pnts.extend([[-iniX,0,' l'],[0,-iniY]])
			sDir = sO.spikesdirl # --------------------------------------LEFT---------------
			if sDir == 'pre' : sDir = spikesdir
			if sDir != 'non' :
				dirL = -1.0 if sDir=='ins' else 1.0
				for n in range(anY):
					if sDir == 'alt' : dirL = 1 if n % 2 == 1 else -1
					if spktype=="rnd": pnts.extend([[-dBezh*dirL,0," c"],[-sh*dirL,-dif],[-sh*dirL,-ss],[0,-dBez],[difh * dirL,-ss],[sh * dirL,-ss]]) #fijo
					if spktype=="wav": pnts.extend([[-dBezh*dirL,0," c"],[-sh*dirL,-dif],[-sh*dirL,-ss],[dBezh*dirL,0],[sh*dirL,-dBez],[sh * dirL,-ss]]) #fijo
					if ssep!=0 and n < (anY-1): pnts.append([0, -ssep,' l'])
		return pnts # 805

	def draw_shapes(self):
		sels = []
		for id, node in self.svg.selected.items(): sels.append(node)
		tab = str(self.options.tab)
		if tab != 'extra':
			for node in sels:
				self.draw(node, tab)
		else:
			Type = str(self.options.joincirctype)
			if len(sels)<2:
				inkex.errormsg('Select at least two objects')
			else:
				self.circsCone(sels, Type)

	def loc_str(self, str):
		return locale.format("%.f", float(str), 0)

	def effect(self):
		slices = self.draw_shapes()

if __name__ == "__main__":
	Shapes().run()