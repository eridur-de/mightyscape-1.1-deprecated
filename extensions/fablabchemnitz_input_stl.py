#!/usr/bin/env python3
# input-stl.py
# (C) 2018 Juergen Weigert <juergen@fabmail.org>, distribute under GPLv2 or ask
#
# This is an input extension for inkscape to read STL files.
#
# Requires: (python-lxml | python3-lxml), slic3r
# For optional(!) rotation support:
#   Requires: (python-numpy-stl | python3-numpy-stl)
#   If you get ImportError: cannot import name 'mesh'
#   although an stl module is installed, then you have the wrong stl module.
#   Try 'pip3 uninstall stl; pip3 install numpy-stl'
#
# 2018-12-22 jw, v0.1 Initial draught
#                v0.1 First working standalone tool.
# 2018-12-26 jw, v0.3 Mesh rotation support via numpy-stl. Fully optional.
#                v0.4 Works fine as an inkscape input extension under Linux.
# 2019-03-01 jw, v0.5 numbers and center option added.
# 2019-07-17 jw, v0.6 fixed ry rotation.
#
# FIXME: should use svg_pathstats(path_d): to compute bounding boxes.

from __future__ import print_function
import sys, os, re, argparse
import subprocess, tempfile
from lxml import etree
from subprocess import Popen, PIPE
_version = '0.6'

sys_platform = sys.platform.lower()
if sys_platform.startswith('win'):
  slic3r = 'slic3r-console.exe'
elif sys_platform.startswith('darwin'):
  slic3r = 'slic3r'
else:   # Linux
  slic3r = os.environ['HOME']+ '/Downloads/Slic3r-1.3.0-x86_64.AppImage'
  if not os.path.exists(slic3r):
    slic3r = 'slic3r'

parser = argparse.ArgumentParser(description='convert an STL file to a nice SVG for inkscape. The STL object is projected onto the X-Y plane.')
parser.add_argument('-l', '--layer_height', default=None, help='slic3r layer height, probably in mm. Default: per slic3r config')
parser.add_argument('--rx', default=None, type=float, help='Rotate STL object around X-Axis before importing.')
parser.add_argument('--ry', default=None, type=float, help='Rotate STL object around Y-Axis before importing.')
parser.add_argument('--numbers', default='false', help='Add layer numbers.')
parser.add_argument('--center', default='false', help='Add center marks.')
parser.add_argument('--stdout', '--tab', default=None, help=argparse.SUPPRESS)
parser.add_argument('-s', '--slic3r-cmd', '--slic3r_cmd', default=slic3r, help='Command to invoke slic3r. Default is "'+slic3r+'"')
parser.add_argument('-o', '--output', default=None, help='SVG output file name or "-" for stdout. Default: Name derived from STL input.') 
parser.add_argument('stlfile', help='STL input file to convert to SVG with the same name, but ".svg" suffix.')

args = parser.parse_args()

# input-stl.inx advertises use of '$HOME' -- windows has HOMEPATH instead of HOME
home = os.environ.get('HOME', os.environ.get('HOMEPATH', 'NO-HOME'))
#args.slic3r_cmd = re.sub('^\$HOME(PATH)?', home, args.slic3r_cmd)

if sys_platform.startswith('win'):
  # assert we run the commandline version of slic3r
  args.slic3r_cmd = re.sub('slic3r(\.exe)?$', 'slic3r-console.exe', args.slic3r_cmd, flags=re.I)

stlfile = args.stlfile
tmpstlfile = None

if args.rx is not None and abs(args.rx) < 0.01: args.rx = None
if args.ry is not None and abs(args.ry) < 0.01: args.ry = None

if args.rx or args.ry:
  try:
    import numpy, stl, math

    mesh = stl.Mesh.from_file(stlfile)
    if args.rx: mesh.rotate([1.0, 0.0, 0.0], math.radians(float(args.rx)))
    if args.ry: mesh.rotate([0.0, 1.0, 0.0], math.radians(float(args.ry)))
    stlfile = tmpstlfile = tempfile.gettempdir() + os.path.sep + 'ink-stl-' + str(os.getpid()) + '.stl'
    mesh.save(stlfile)
  except Exception as e:
    print("Rotate failed: " + str(e), file=sys.stderr)

if args.output == '-': args.stdout = True

if args.stdout:
  svgfile = tempfile.gettempdir() + os.path.sep + 'ink-stl-' + str(os.getpid()) + '.svg'
else:
  svgfile = re.sub('\.stl', '.svg', args.stlfile, flags=re.IGNORECASE)
  if args.output is not None: svgfile = args.output

cmd = [args.slic3r_cmd, '--version']
try:
  proc = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except OSError as e:
  if args.stdout:
    hint="Check your slic3r command setting in the second tab of the STL Input dialog."
  else:
    hint="Maybe use --slic3r-cmd option?"
  print("{0}\nCommand failed: errno={1} {2}\n\n{3}".format(' '.join(cmd), e.errno, e.strerror, hint), file=sys.stderr)
  sys.exit(1)
stdout, stderr = proc.communicate()

# option --layer-height does not work. We use --scale instead...
scale = 1/float(args.layer_height)
cmd = [args.slic3r_cmd, '--no-gui']
if args.layer_height is not None:
  cmd += ['--scale', str(scale), '--first-layer-height', '0.1mm']     # args.layer_height+'mm']
cmd += ['--export-svg', '-o', svgfile, stlfile]

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
      # print len(pp)
      # print "short path error"
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

if args.center != 'false':
  bb = bbox_info(args.slic3r_cmd, stlfile)
  # Ouch: bbox info gives us stl coordinates. slic3r translates them into svg px using 75dpi.
  cx = (-bb['min_x'] + bb['max_x']) * 0.5 * 1/scale * magic * 25.4 / 75
  cy = (-bb['min_y'] + bb['max_y']) * 0.5 * 1/scale * magic * 25.4 / 75
# print(cx, cy, file=sys.stderr)


try:
  if args.stdout:
    tty = open("/dev/tty", "w")
  else:
    tty = sys.stderr
except:
    tty = sys.stderr

try:
  proc = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
except OSError as e:
  raise OSError("{0}\nCommand failed: errno={1} {2}".format(' '.join(cmd), e.errno, e.strerror))
stdout, stderr = proc.communicate()

if tmpstlfile and os.path.exists(tmpstlfile):
  os.unlink(tmpstlfile)

if not b'Done.' in stdout:
  print("Command failed: {0}".format(' '.join(cmd)))
  print("OUT: " + str(stdout), file=sys.stderr)
  print("ERR: " + str(stderr), file=sys.stderr)
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

doc.getroot().addprevious(etree.Comment(' Imported with '+sys.argv[0]+' V'+_version+" by Juergen Weigert "))
doc.getroot().attrib['{http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd}docname'] = 'input-stl.svg'

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
    if args.numbers != 'false':
      num = etree.Element('{http://www.w3.org/2000/svg}text')
      num.attrib['id'] = 'textnum'+str(layercount)
      num.attrib['x'] = str(layercount*2)
      num.attrib['y'] = str(layercount*4+10)
      num.attrib['style'] = 'fill:#00FF00;fill-opacity:1;stroke:#00FF00;font-family:FreeSans;font-size:10pt;stroke-opacity:1;stroke-width:0.1'
      num.text = "%d" % layercount
      e.append(num)
    if args.center != 'false':
      cc = etree.Element('{http://www.w3.org/2000/svg}path')
      cc.attrib['id'] = 'ccross'+str(layercount)
      cc.attrib['style'] = 'fill:none;fill-opacity:1;stroke:#0000FF;font-family:FreeSans;font-size:10pt;stroke-opacity:1;stroke-width:0.1'
      cc.attrib['d'] = 'M %s,%s v 10 M %s,%s h 10 M %s,%s h 4' % (cx, cy-5,  cx-5, cy,  cx-2, cy+5)
      e.append(cc)



polygoncount = 0
for e in doc.iterfind('//{*}polygon'):
  # e.tag = '{http://www.w3.org/2000/svg}polygon'
  # e.attrib = {'{http://slic3r.org/namespaces/slic3r}type': 'contour', 'points': '276.422496,309.4 260.209984,309.4 260.209984,209.03 276.422496,209.03', 'style': 'fill: white'}
  e.tag = re.sub('polygon$', 'path', e.tag)
  polygoncount += 1
  e.attrib['id'] = 'polygon%d' % polygoncount
  e.attrib['{http://www.inkscape.org/namespaces/inkscape}connector-curvature'] = '0'
  e.attrib['style'] = 'fill:none;fill-opacity:1;stroke:#FF0000;stroke-opacity:1;stroke-width:0.1'
  e.attrib['d'] = 'M ' + re.sub(' ', ' L ', scale_points(e.attrib['points'], 1/scale)) + ' Z'
  del e.attrib['points']
  if e.attrib.get('{http://slic3r.org/namespaces/slic3r}type') == 'contour':
    # remove contour, but keep all slic3r:type='hole', whatever it is worth later.
    del e.attrib['{http://slic3r.org/namespaces/slic3r}type']

try:
  # Available in lxml since 3.5.0
  # Make an xmlns declaration in the svg header, and use the "inkscape:" prefix throughout the document.
  etree.cleanup_namespaces(doc.getroot(), top_nsmap={
    'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
    'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'})
except:
  pass

try:
  print("{0}: {1} polygons in {2} layers converted to paths.".format(svgfile, polygoncount, layercount), file=tty)
except:
  pass

if args.stdout:
  doc.write(sys.stdout.buffer)
else:
  doc.write(svgfile, pretty_print=True)