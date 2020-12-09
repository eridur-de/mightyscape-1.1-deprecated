#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) 2020 Ellen Wasboe, ellen@wasbo.net
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
"""
Remove duplicate nodes or join nodes with distance less than specified.
Optionally join start node with end node of each subpath if distance less than specified.
"""

import inkex
from inkex import bezier, PathElement, CubicSuperPath

class removeDuplicateNodes(inkex.EffectExtension):

	def add_arguments(self, pars):
		pars.add_argument("--minlength", default="0")
		pars.add_argument("--minUse", type=inkex.Boolean, default=False)
		pars.add_argument("--maxdist", default="0")
		pars.add_argument("--joinEnd", type=inkex.Boolean, default=False)
		
	"""Remove duplicate nodes"""
	def effect(self):
		for id, elem in self.svg.selected.items():
			minlength=float(self.options.minlength)
			maxdist=float(self.options.maxdist)
			if self.options.minUse == False:
				minlength=0
			if self.options.joinEnd == False:
				maxdist=-1
						
			#register which subpaths are closed
			dList=str(elem.path).upper().split(' M')
			closed=[""]
			l=0
			for sub in dList:			
				if dList[l].find("Z") > -1:
					closed.append(" Z ")
				else:
					closed.append("")
				l+=1
			closed.pop(0)
			
			new = []
			s=0
			for sub in elem.path.to_superpath():
				new.append([sub[0]])
				i = 1
				while i <= len(sub) - 1:
					length = bezier.cspseglength(new[-1][-1], sub[i]) #curve length			
					if length >= minlength:
						new[-1].append(sub[i])
					else:
						#average last node xy with this node xy and set this further node to last
						new[-1][-1][1][0]= 0.5*(new[-1][-1][1][0]+sub[i][1][0])
						new[-1][-1][1][1]= 0.5*(new[-1][-1][1][1]+sub[i][1][1])
						new[-1][-1][-1]=sub[i][-1] 
					i += 1
					
				if maxdist > -1:
					#calculate distance between first and last node
					#if <= maxdist set closed[i] to "Z "
					last=new[-1][-1]
					length = bezier.cspseglength(new[-1][-1], sub[0])
					if length <= maxdist:
						newStartEnd=[0.5*(new[-1][-1][-1][0]+new[0][0][0][0]),0.5*(new[-1][-1][-1][1]+new[0][0][0][1])]
						new[0][0][0]=newStartEnd
						new[0][0][1]=newStartEnd
						new[-1][-1][1]=newStartEnd
						new[-1][-1][2]=newStartEnd
						closed[s]=" Z "
				s+=1
					
			elem.path = CubicSuperPath(new).to_path(curves_only=True)
			
			#reset z to the originally closed paths (z lost in cubicsuperpath)
			temppath=str(elem.path.to_absolute()).split('M ')
			temppath.pop(0)
			newPath=''
			l=0
			for sub in temppath:
				newPath=newPath+'M '+temppath[l]+closed[l]
				l+=1
			elem.path=newPath
				
if __name__ == '__main__':
    removeDuplicateNodes().run()

