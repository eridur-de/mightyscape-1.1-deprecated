#!/usr/bin/env python3
'''
(C) 2018 Juergen Weigert <juergen@fabmail.org>, distribute under GPLv2 or ask

This is an input extension for inkscape to read STL files.

Requires: (python-lxml | python3-lxml), slic3r
For optional(!) rotation support:
  Requires: (python-numpy-stl | python3-numpy-stl)
  If you get ImportError: cannot import name 'mesh'
  although an stl module is installed, then you have the wrong stl module.
  Try 'pip3 uninstall stl; pip3 install numpy-stl'

2018-12-22 jw, v0.1 Initial draught
                       v0.1 First working standalone tool.
2018-12-26 jw, v0.3 Mesh rotation support via numpy-stl. Fully optional.
                       v0.4 Works fine as an inkscape input extension under Linux.
2019-03-01 jw, v0.5 numbers and center option added.
2019-07-17 jw, v0.6 fixed ry rotation.

2021-05-14 - Mario Voigt: 
    - changed extension to support ply,off,obj,stl by using OpenMesh
    - moved extension to sub menu structure (allows preview)
    - added different options

#ToDos
 * Make it available through PrusaSlic3r
 * FIXME: should use svg_pathstats(path_d): to compute bounding boxes.
'''
import sys
import os
import re
import subprocess
from lxml import etree
from subprocess import Popen, PIPE
import inkex
from inkex import Color
import tempfile
import openmesh as om
import stl #numpy-stl lib
import numpy
import math

sys_platform = sys.platform.lower()
if sys_platform.startswith('win'):
  slic3r = 'slic3r-console.exe'
elif sys_platform.startswith('darwin'):
  slic3r = 'slic3r'
else:   # Linux
  slic3r = os.environ['HOME']+ '/Downloads/Slic3r-1.3.0-x86_64.AppImage'
  if not os.path.exists(slic3r):
    slic3r = 'slic3r'

class InputSTL(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument('--tab')

        pars.add_argument('--inputfile', help='STL input file to convert to SVG with the same name, but ".svg" suffix.')
        pars.add_argument('-l', '--layer_height', default=None, help='slic3r layer height, probably in mm. Default: per slic3r config')
        pars.add_argument('--rx', default=None, type=float, help='Rotate STL object around X-Axis before importing.')
        pars.add_argument('--ry', default=None, type=float, help='Rotate STL object around Y-Axis before importing.')
        pars.add_argument('--numbers', type=inkex.Boolean, default=False, help='Add layer numbers.')
        pars.add_argument('--center', type=inkex.Boolean, default=False, help='Add center marks.')
        pars.add_argument("--stroke_width", type=float, default=2.0, help="Stroke width (px)")
        pars.add_argument('--path_color', type=Color, default='879076607', help="Path color")
        pars.add_argument("--fill_color", type=Color, default='1943148287', help="Fill color")
        pars.add_argument("--use_fill_color", type=inkex.Boolean, default=False, help="Use fill color")
        pars.add_argument("--tone_down",  default="regular", help="Town down opacity for each layer")
      
        pars.add_argument('-s', '--slic3r-cmd', '--slic3r_cmd', default="slic3r", help="Command to invoke slic3r.")

    def effect(self):             
        args = self.options
        inputfile = args.inputfile    
        outputfilebase = os.path.splitext(os.path.basename(inputfile))[0]
        converted_inputfile = os.path.join(tempfile.gettempdir(), outputfilebase + ".stl")
        if not os.path.exists(inputfile):
                inkex.utils.debug("The input file does not exist.")
                exit(1) 
        om.write_mesh(converted_inputfile, om.read_trimesh(inputfile)) #read + convert     # might throw "[STLWriter] : Warning non-triangle data!"
        args.inputfile = converted_inputfile #overwrite

        # input-stl.inx advertises use of '$HOME' -- windows has HOMEPATH instead of HOME
        home = os.environ.get('HOME', os.environ.get('HOMEPATH', 'NO-HOME'))
        #args.slic3r_cmd = re.sub('^\$HOME(PATH)?', home, args.slic3r_cmd)
        
        if sys_platform.startswith('win'):
            # assert we run the commandline version of slic3r
            args.slic3r_cmd = re.sub('slic3r(\.exe)?$', 'slic3r-console.exe', args.slic3r_cmd, flags=re.I)
        

        tmp_inputfile = None
     
        if args.rx is not None and abs(args.rx) < 0.01: args.rx = None
        if args.ry is not None and abs(args.ry) < 0.01: args.ry = None
        
        if args.rx or args.ry:
            try:        
                mesh = stl.Mesh.from_file(inputfile)
                if args.rx: mesh.rotate([1.0, 0.0, 0.0], math.radians(float(args.rx)))
                if args.ry: mesh.rotate([0.0, 1.0, 0.0], math.radians(float(args.ry)))
                inputfile = tmp_inputfile = tempfile.gettempdir() + os.path.sep + 'ink-stl-' + str(os.getpid()) + '.stl'
                mesh.save(inputfile)
            except Exception as e:
                inkex.utils.debug("Rotate failed: " + str(e))
            
        svgfile = re.sub('\.stl', '.svg', args.inputfile, flags=re.IGNORECASE)
                        
        cmd = [args.slic3r_cmd, '--version']
        try:
            proc = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            hint="Maybe use --slic3r-cmd option?"
            inkex.utils.debug("{0}\nCommand failed: errno={1} {2}\n\n{3}".format(' '.join(cmd), e.errno, e.strerror, hint), file=sys.stderr)
            sys.exit(1)
        stdout, stderr = proc.communicate()
        
        # option --layer-height does not work. We use --scale instead...
        scale = 1/float(args.layer_height)
        cmd = [args.slic3r_cmd, '--no-gui']
        if args.layer_height is not None:
            cmd += ['--scale', str(scale), '--first-layer-height', '0.1mm']     # args.layer_height+'mm']
        cmd += ['--export-svg', '-o', svgfile, inputfile]
        
        magic = 10    # layer width seems to be 0.1mm ???
        
        def scale_points(pts, scale):
            """ str='276.422496,309.4 260.209984,309.4 260.209984,209.03 276.422496,209.03'
            """
            return re.sub('\d*\.\d*', lambda x: str(float(x.group(0))*scale*magic), pts)
        
        
        ## CAUTION: keep svg_pathstats() in sync with inkscape-centerlinetrace
        def svg_pathstats(path_d):
            """ calculate statistics from an svg path:
                    length (measuring bezier splines as straight lines through the handles).
                    points (all, including duplicates)
                    segments (number of not-connected!) path segments.
                    simple bounding box (ignoring curves of splines, but inclding handles.)
            """
            xmin = 1e99
            ymin = 1e99
            xmax = -1e99
            ymax = -1e99
            p_points = 0
            p_length = 0
            p_segments = 0
        
            path_d = path_d.lower()
            for p in path_d.split('m'):
        
                pp = re.sub('[cl,]', ' ', p)
                pp,closed = re.subn('z\s*$','',pp)
                xy = pp.split()
                if len(xy) < 2:
                    # inkex.utils.debug(len(pp))
                    # inkex.utils.debug("short path error")
                    continue
                x0 = float(xy[0])
                y0 = float(xy[1])
                if x0 > xmax: xmax = x0
                if x0 < xmin: xmin = x0
                if y0 > ymax: ymax = y0
                if y0 < ymin: ymin = y0
        
                p_points += 1
                x = xy[2::2]
                y = xy[3::2]
                if len(x):
                    p_segments += 1
                    if closed:
                        x.extend(x0)
                        y.extend(y0)
        
                for i in range(len(x)):
                    p_points += 1
                    dx = float(x[i]) - x0
                    dy = float(y[i]) - y0
                    p_length += math.sqrt( dx * dx + dy * dy )
                    x0,y0 = float(x[i]),float(y[i])
                    if x0 > xmax: xmax = x0
                    if x0 < xmin: xmin = x0
                    if y0 > ymax: ymax = y0
                    if y0 < ymin: ymin = y0
        
            return { 'points':p_points, 'segments':p_segments, 'length':p_length, 'bbox': (xmin,ymin, xmax, ymax) }
        
        
        def bbox_info(slic3r, file):
            cmd = [ slic3r, '--no-gui', '--info', file ]
            p = Popen(cmd, stdout=PIPE, stderr=PIPE)
            out, err = p.communicate()
            if len(err):
                raise ValueError(err)
        
            bb = {}
            for l in out.decode().split("\n"):
                m = re.match('((min|max)_[xyz])\s*=\s*(.*)', l)
                if m: bb[m.group(1)] = float(m.group(3))
            if (len(bb) != 6):
                raise ValueError("slic3r --info did not return 6 elements for bbox")
            return bb
        
        if args.center is not False:
            bb = bbox_info(args.slic3r_cmd, inputfile)
            # Ouch: bbox info gives us stl coordinates. slic3r translates them into svg px using 75dpi.
            cx = (-bb['min_x'] + bb['max_x']) * 0.5 * 1/scale * magic * 25.4 / 75
            cy = (-bb['min_y'] + bb['max_y']) * 0.5 * 1/scale * magic * 25.4 / 75  

        try:
            proc = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except OSError as e:
            raise OSError("{0}\nCommand failed: errno={1} {2}".format(' '.join(cmd), e.errno, e.strerror))
        stdout, stderr = proc.communicate()
        
        if tmp_inputfile and os.path.exists(tmp_inputfile):
            os.unlink(tmp_inputfile)
        
        if not b'Done.' in stdout:
            inkex.utils.debug("Command failed: {0}".format(' '.join(cmd)))
            inkex.utils.debug("OUT: " + str(stdout))
            inkex.utils.debug("ERR: " + str(stderr))
            sys.exit(1)
        
        # slic3r produces correct svg files, but with polygons instead of paths, and with undefined strokes.
        # When opened with inkscape, most lines are invisible and polygons cannot be edited.
        # To fix these issues, we postprocess the svg file:
        # * replace polygon nodes with corresponding path nodes.
        # * replace style attribute in polygon nodes with one that has a black stroke
        
        stream = open(svgfile, 'r')
        p = etree.XMLParser(huge_tree=True)
        doc = etree.parse(stream, parser=p)
        stream.close()
        
        ## To change the document units to mm, insert directly after the root node:
        # e.tag = '{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}namedview'
        # e.attrib['id'] = "base"
        # e.attrib['{http://www.inkscape.org/namespaces/inkscape}document-units'] = "mm"
        
        layercount = 0
        for e in doc.iterfind('//{*}g'):
            if e.attrib['{http://slic3r.org/namespaces/slic3r}z'] and e.attrib['id']:
                e.attrib['{http://www.inkscape.org/namespaces/inkscape}label'] = e.attrib['id'] + ' slic3r:z=' + e.attrib['{http://slic3r.org/namespaces/slic3r}z']
                del e.attrib['{http://slic3r.org/namespaces/slic3r}z']
                # for some fun with our inkscape-paths2openscad extension, add sibling to e:
                # <svg:desc id="descpoly60">Depth: 1mm\nOffset: 31mm</svg:desc>
                desc = etree.Element('{http://www.w3.org/2000/svg}desc')
                desc.attrib['id'] = 'descl'+str(layercount)
                desc.text = "Depth: %.2fmm\nRaise: %.2fmm\n" % (1/scale, layercount/scale)
                e.append(desc)
                layercount+=1
                if args.numbers is True:
                    num = etree.Element('{http://www.w3.org/2000/svg}text')
                    num.attrib['id'] = 'textnum'+str(layercount)
                    num.attrib['x'] = str(layercount*2)
                    num.attrib['y'] = str(layercount*4+10)
                    num.attrib['style'] = 'fill:#00FF00;fill-opacity:1;stroke:#00FF00;font-family:FreeSans;font-size:10pt;stroke-opacity:1;stroke-width:0.1'
                    num.text = "%d" % layercount
                    e.append(num)
                if args.center is True:
                    cc = etree.Element('{http://www.w3.org/2000/svg}path')
                    cc.attrib['id'] = 'ccross'+str(layercount)
                    cc.attrib['style'] = 'fill:none;fill-opacity:1;stroke:#0000FF;font-family:FreeSans;font-size:10pt;stroke-opacity:1;stroke-width:0.1'
                    cc.attrib['d'] = 'M %s,%s v 10 M %s,%s h 10 M %s,%s h 4' % (cx, cy-5,  cx-5, cy,  cx-2, cy+5)
                    e.append(cc)
       
        totalPolygoncount = 0
        for e in doc.iterfind('//{*}polygon'):
            totalPolygoncount += 1
            
        polygoncount = 0
        
        if args.use_fill_color is False:
            fill = "none"
        else:
            fill = args.fill_color
        
        for e in doc.iterfind('//{*}polygon'):
            polygoncount += 1
            if args.tone_down == "front_to_back":
                stroke_and_fill_opacity = polygoncount / totalPolygoncount
            elif args.tone_down == "back_to_front":
                stroke_and_fill_opacity = 1 - (polygoncount / totalPolygoncount)
            elif args.tone_down == "regular":
                stroke_and_fill_opacity = 1.0
            else:
                inkex.utils.debug("Error: unkown town down option")
                exit(1)
            # e.tag = '{http://www.w3.org/2000/svg}polygon'
            # e.attrib = {'{http://slic3r.org/namespaces/slic3r}type': 'contour', 'points': '276.422496,309.4 260.209984,309.4 260.209984,209.03 276.422496,209.03', 'style': 'fill: white'}
            e.tag = re.sub('polygon$', 'path', e.tag)
            e.attrib['id'] = 'polygon%d' % polygoncount
            e.attrib['{http://www.inkscape.org/namespaces/inkscape}connector-curvature'] = '0'
            e.attrib['style'] = 'fill:{};fill-opacity:{};stroke:{};stroke-opacity:{};stroke-width:{}'.format(fill, stroke_and_fill_opacity, args.path_color, stroke_and_fill_opacity, args.stroke_width)
            e.attrib['d'] = 'M ' + re.sub(' ', ' L ', scale_points(e.attrib['points'], 1/scale)) + ' Z'
            del e.attrib['points']
            if e.attrib.get('{http://slic3r.org/namespaces/slic3r}type') == 'contour':
                # remove contour, but keep all slic3r:type='hole', whatever it is worth later.
                del e.attrib['{http://slic3r.org/namespaces/slic3r}type']
        
        etree.cleanup_namespaces(doc.getroot(), top_nsmap={
            'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
            'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'})
    
        #inkex.utils.debug("{0}: {1} polygons in {2} layers converted to paths.".format(svgfile, polygoncount, layercount))

        stl_group = self.document.getroot().add(inkex.Group(id=self.svg.get_unique_id("slic3r-stl-input-"))) #make a new group at root level
        for element in doc.getroot().iter("{http://www.w3.org/2000/svg}g"):
            stl_group.append(element)

if __name__ == '__main__':
    InputSTL().run()