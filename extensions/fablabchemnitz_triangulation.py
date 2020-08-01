#!/usr/bin/env python3
'''
Copyright (C) 2014 Nicola Romano', romano.nicola@gmail.com

version 0.1
    0.1: first working version

------------------------------------------------------------------------
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
------------------------------------------------------------------------

'''

import inkex
import urllib.parse
import urllib.request
import os
import random
from PIL import Image
from lxml import etree
from inkex import Transform
import numpy as np
from scipy.spatial import Delaunay
from scipy.cluster.vq import kmeans2
import cv2

class Triangulation(inkex.Effect):
    def __init__(self):
        # Call base class construtor.
        inkex.Effect.__init__(self)
        # Option parser:
        # -n, --num_points
        # -m, --edge_thresh_min
        # -M, --edge_thresh_max
        # -c, --add_corners
        # -g, --gradient_fill
        # -b, --tab
        self.arg_parser.add_argument("-n", "--num_points", type=int, default=100, help="Number of points to be sampled")
        self.arg_parser.add_argument("-m", "--edge_thresh_min", type=int, default=200, help="Minimum threshold for edge detection")
        self.arg_parser.add_argument("-M", "--edge_thresh_max", type=int, default=255, help="Maximum threshold for edge detection")
        self.arg_parser.add_argument("-c", "--add_corners", type=inkex.Boolean, default=0, help="Use corners for triangulation?")
        self.arg_parser.add_argument("-g", "--gradient_fill", type=inkex.Boolean, default=0, help="Fill triangles with gradient?")
        self.arg_parser.add_argument("-b", "--tab", default='', help="The tab of the interface")

    def draw_SVG_path(self, points, closed, style, parent):
        pathdesc = "M "
        for p in points:
            pathdesc = pathdesc + str(p[0]) + "," + str(p[1]) + " "
        if closed == 1:
            pathdesc = pathdesc + "Z"    
        path = etree.SubElement(parent, inkex.addNS('path','svg'), {'style' : str(inkex.Style(style)), 'd' : pathdesc})
        return path
		
    def effect(self):
			
        # Check we have something selected
        if len(self.svg.selected) == 0:
            inkex.errormsg("Please select an image.")
            exit()
        else:
            # Check it is an image
            for id, obj in self.svg.selected.items():
                if obj.tag[len(obj.tag)-5:] != "image":
                    inkex.errormsg("The selected object (" + id + ") is not an image, skipping.")
                    continue
                else:
                    (self.path, errcode) = self.checkImagePath(obj) # This also ensures the file exists
                    if errcode==1:
                        inkex.errormsg("Embedded images are not (yet?) supported, please use a linked image. Skipping.")
                        continue
                    elif errcode==2:
                        inkex.errormsg("The image points to a file, which seems to be missing: "+self.path+". Skipping.")
                        continue

                    grpname = 'img_triangles'
                    # Make sure that the id/name is unique
                    index = 0
                    while (str(self.svg.get_ids()) in grpname):
                        grpname = 'axis' + str(index)
                        index = index + 1

                    grp_name = grpname
                    grp_attribs = {inkex.addNS('label','inkscape'):grp_name}
                    # The group to put everything in
                    grp = etree.SubElement(self.svg.get_current_layer(), 'g', grp_attribs)

                    # Find image size and position in Inkscape
                    try:
                        self.img_x_pos = float(obj.get("x"))
                        self.img_y_pos = float(obj.get("y"))
                    except:
                        self.img_x_pos = 0
                        self.img_y_pos = 0
                    self.img_width = float(obj.get("width"))
                    self.img_height = float(obj.get("height"))
                    im = Image.open(self.path)
                    # IMPORTANT! 
                    # The numpy array is accessed as im.data[row,column], that is data[y_coord, x_coord]
                    # Be careful not to pass coordinates as (x,y): rather use (y,x)!
                    im.data = np.asarray(im)
                    # The RGB components of all the pixels in the image
                    self.red, self.green, self.blue = im.data[:,:,0], im.data[:,:,1], im.data[:,:,2]

                    # Find real image size
                    (self.img_real_width, self.img_real_height) = im.size
        
                    self.doTriangulation(grp)

    # Check file exists and returns its path
    def checkImagePath(self, obj):
        xlink = obj.get(inkex.addNS('href','xlink'))
        if xlink[:5] == 'data:': # Embedded image
            return (None, 1)
        
        # Code shamelessly copied from the Embed image extension :)
        if xlink is None or xlink[:5] != 'data:':
            absref = obj.get(inkex.addNS('absref','sodipodi'))
            url = urllib.parse.urlparse(xlink)
            href = urllib.request.url2pathname(url.path)

        path=''
        #path selection strategy:
        # 1. href if absolute
        # 2. realpath-ified href
        # 3. absref, only if the above does not point to a file
        if (href != None):
            path = os.path.realpath(href)
        if (not os.path.isfile(path)):
            if (absref != None):
                path=absref
        if (not os.path.isfile(path)):
            return (path, 2)
        
        return (path, 0)
    
    # Converts image coordinates to screen coordinates
    def imgToScreen(self, x, y):
        newx = x / (self.img_real_width/self.img_width) + self.img_x_pos
        newy = y / (self.img_real_height/self.img_height) + self.img_y_pos
        return (newx, newy)

    def createLinearGradient(self, x1, y1, x2, y2, color1, color2, gradID):
        attribs = {
            'x1' : str(x1),
            'y1' : str(y1),
            'x2' : str(x2),
            'y2' : str(y2),
            'id' : gradID,
            'gradientUnits' : "userSpaceOnUse",
            '{'+inkex.NSS[u'xlink']+'}href': "#"+gradID
            }
            
        svgdefs = self.document.getroot().find(inkex.addNS('defs', 'svg'))
        gradient = etree.SubElement(svgdefs, inkex.addNS('linearGradient','svg'), attribs)

        attribs = {
                'offset' : "0%",
                'style' : "stop-color:"+color1+"; stop-opacity:1"
                }
        stop1 = etree.SubElement(gradient, inkex.addNS('stop','svg'), attribs)
        attribs = {
                'offset' : "100%",
                'style' : "stop-color:"+color2+"; stop-opacity:1"
                }
        stop2 = etree.SubElement(gradient, inkex.addNS('stop','svg'), attribs)
        return gradient
    
    def doTriangulation (self, grp):
        #inkex.utils.debug(self.path)
        # Read image with OpenCV
        imcv = cv2.imread(self.path)
        # Convert to grayscale
        gray = cv2.cvtColor(imcv,cv2.COLOR_RGB2GRAY)
        gray = np.float32(gray)
        # Find edges
        edges = cv2.Canny(imcv, self.options.edge_thresh_min, self.options.edge_thresh_max, 100)
        # Find coordinates of the edges
        coords = [(float(x),float(y)) for y, row in enumerate(edges) for x, col in enumerate(row) if col>0]
        #pt = random.sample(coords, self.options.num_points)
        pt, idx = kmeans2(np.array(coords), self.options.num_points, minit="points")

        if self.options.add_corners:
            # Add the four corners
            corners = [(0, 0), 
                (self.img_real_width-1, 0),
                (0, self.img_real_height-1),
                (self.img_real_width-1, self.img_real_height-1)]
        
            pt = np.vstack((pt, corners))

        # Perform Delaunay triangulation
        tri = Delaunay(pt)
        tri_coord = [(pt[t[0]], pt[t[1]], pt[t[2]]) for t in tri.simplices]
        tri_colors = [(
                     (self.red[int(t[0][1]),int(t[0][0])], self.green[int(t[0][1]),int(t[0][0])], self.blue[int(t[0][1]),int(t[0][0])]),
                     (self.red[int(t[1][1]),int(t[1][0])], self.green[int(t[1][1]),int(t[1][0])], self.blue[int(t[1][1]),int(t[1][0])]),
                     (self.red[int(t[2][1]),int(t[2][0])], self.green[int(t[2][1]),int(t[2][0])], self.blue[int(t[2][1]),int(t[2][0])])
                     )
                     for t in tri_coord]
        
        for i, c in enumerate(tri_coord):
            # Convert to screen coordinates
            v0 = self.imgToScreen(c[0][0], c[0][1])
            v1 = self.imgToScreen(c[1][0], c[1][1])
            v2 = self.imgToScreen(c[2][0], c[2][1])
            col = tri_colors[i]
            fill = ""
            
            if self.options.gradient_fill:
                color1 = "rgb("+str(col[0][0])+","+str(col[0][1])+","+str(col[0][2])+")"
                color2 = "rgb("+str(0.5*col[1][0]+0.5*col[2][0])+","+ \
                        str(0.5*col[1][1]+0.5*col[2][1])+","+ \
                        str(0.5*col[1][2]+0.5*col[2][2])+")"
                gradID = 'linearGradient'
                # Make sure that the id is inique
                index = 0
                while (str(self.svg.get_ids()) in gradID):
                    gradID = 'linearGradient' + str(index)
                    index = index + 1
            
                #self.doc_ids[gradID]=1
            
                gradient = self.createLinearGradient(v0[0], v0[1], 
                        0.5*(v1[0]+v2[0]), 0.5*(v1[1]+v2[1]), 
                        color1, color2, gradID)
                fill = "url(#"+gradient.get("id")+")"
            else:
                fill = "rgb("+str(col[0][0])+","+str(col[0][1])+","+str(col[0][2])+")"
                
            tri_style = {
                'stroke-width' : '1px',
                'stroke-linecap' : 'round',
                'stroke-opacity' : '1',
                'fill' : fill,
                'fill-opacity' : '1',
                'stroke' : fill
                }
            
            self.draw_SVG_path([v0, v1, v2], 1, tri_style, grp)

Triangulation().run()