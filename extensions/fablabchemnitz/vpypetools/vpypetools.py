#!/usr/bin/env python3

import logging
logger = logging.getLogger()
logger.setLevel(level=logging.ERROR) #we set this to error before importing vpype to ignore the nasty output "WARNING:root:!!! `vpype.Length` is deprecated, use `vpype.LengthType` instead."

import sys
import os
from lxml import etree

import inkex
from inkex import transforms, bezier
from inkex.paths import CubicSuperPath
from inkex.command import inkscape

import vpype
import vpype_viewer
from vpype_viewer import ViewMode
from vpype_cli import execute

logger = logging.getLogger()
logger.setLevel(level=logging.WARNING) #after importing vpype we enabled logging again

import warnings # we import this to suppress moderngl warnings from vpype_viewer

from shapely.geometry import LineString, Point

"""
Extension for InkScape 1.X
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 02.04.2021
Last patch: 08.04.2021
License: GNU GPL v3

This piece of spaghetti-code, called "vpypetools", is a wrapper to pass (pipe) line elements from InkScape selection (or complete canvas) to vpype. 
It allows to run basic commands on the geometry. The converted lines are getting pushed back into InkScape. 
vpypetools allows to enable some important adjusters and debugging settings to get the best out of it.

vpypetools is based on 
 - Aaron Spike's "Flatten Bezier" extension, licensed by GPL v2
 - Mark Riedesel's "Apply Transform" extension (https://github.com/Klowner/inkscape-applytransforms), licensed by GPL v2
 - a lot of other extensions to rip off the required code pieces ;-)
 - used (tested) version of vpype: commit id https://github.com/abey79/vpype/commit/0b0dc8dd7e32998dbef639f9db578c3bff02690b (29.03.2021)
 - used (tested) version of vpype occult: commit id https://github.com/LoicGoulefert/occult/commit/2d04ca57d69078755c340066c226fd6cd927d41e (04.02.2021)

CLI / API docs:
- https://vpype.readthedocs.io/en/stable/api/vpype_cli.html#module-vpype_cli
- https://vpype.readthedocs.io/en/stable/api/vpype.html#module-vpype

Todo's
- allow to change pen width / opacity in vpype viewer: https://github.com/abey79/vpype/issues/243
- command chain is really slow on Windows (takes ~5 times longer than Linux). Find ways to speed up
"""

class vpypetools (inkex.EffectExtension):

    def __init__(self):
        inkex.Effect.__init__(self)
        
        # Line Sorting
        self.arg_parser.add_argument("--linesort", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--linesort_no_flip", type=inkex.Boolean, default=False, help="Disable reversing stroke direction for optimization")
        
        # Line Merging
        self.arg_parser.add_argument("--linemerge", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--linemerge_tolerance", type=float, default=0.500, help="Maximum distance between two line endings that should be merged (default 0.500 mm)")
        self.arg_parser.add_argument("--linemerge_no_flip", type=inkex.Boolean, default=False, help="Disable reversing stroke direction for merging")
  
        # Trimming
        self.arg_parser.add_argument("--trim", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--trim_x_margin", type=float, default=0.000, help="trim margin - x direction (mm)") # keep default at 0.000 to keep clean bbox
        self.arg_parser.add_argument("--trim_y_margin", type=float, default=0.000, help="trim margin - y direction (mm)") # keep default at 0.000 to keep clean bbox
    
        # Relooping
        self.arg_parser.add_argument("--reloop", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--reloop_tolerance", type=float, default=0.500, help="Controls how close the path beginning and end must be to consider it closed (default 0.500 mm)")
 
        # Multipass
        self.arg_parser.add_argument("--multipass", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--multipass_count", type=int, default=2, help="How many passes for each line (default 2)")
 
        # Filter
        self.arg_parser.add_argument("--filter", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--filter_tolerance", type=float, default=0.050, help="Tolerance used to determined if a line is closed or not (default 0.050 mm)")
        self.arg_parser.add_argument("--filter_closed", type=inkex.Boolean, default=False, help="Keep closed lines")
        self.arg_parser.add_argument("--filter_not_closed", type=inkex.Boolean, default=False, help="Keep open lines")
        self.arg_parser.add_argument("--filter_min_length_enabled", type=inkex.Boolean, default=False, help="filter by min length")
        self.arg_parser.add_argument("--filter_min_length", type=float, default=0.000, help="Keep lines whose length isn't shorter than value")
        self.arg_parser.add_argument("--filter_max_length_enabled", type=inkex.Boolean, default=False, help="filter by max length") 
        self.arg_parser.add_argument("--filter_max_length", type=float, default=0.000, help="Keep lines whose length isn't greater than value") 
 
        # Split All
        self.arg_parser.add_argument("--splitall", type=inkex.Boolean, default=False)
 
        # Plugin Occult
        self.arg_parser.add_argument("--plugin_occult", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--plugin_occult_tolerance", type=float, default=0.01, help="Max distance between start and end point to consider a path closed (default 0.01 mm)")

        # Free Mode
        self.arg_parser.add_argument("--tab")
        self.arg_parser.add_argument("--freemode", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--freemode_cmd1", default="")
        self.arg_parser.add_argument("--freemode_cmd1_enabled", type=inkex.Boolean, default=True)
        self.arg_parser.add_argument("--freemode_cmd2", default="")
        self.arg_parser.add_argument("--freemode_cmd2_enabled", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--freemode_cmd3", default="")
        self.arg_parser.add_argument("--freemode_cmd3_enabled", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--freemode_cmd4", default="")
        self.arg_parser.add_argument("--freemode_cmd4_enabled", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--freemode_cmd5", default="")
        self.arg_parser.add_argument("--freemode_cmd5_enabled", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--freemode_show_cmd", type=inkex.Boolean, default=False)
 
        # General Settings
        self.arg_parser.add_argument("--input_handling", default="paths", help="Input handling")
        self.arg_parser.add_argument("--flattenbezier", type=inkex.Boolean, default=False, help="Flatten bezier curves to polylines")
        self.arg_parser.add_argument("--flatness", type=float, default=0.1, help="Minimum flatness = 0.1. The smaller the value the more fine segments you will get (quantization).")
        self.arg_parser.add_argument("--decimals", type=int, default=3, help="Accuracy for imported lines' coordinates into vpype. Does not work for 'Multilayer/document'")
        self.arg_parser.add_argument("--simplify", type=inkex.Boolean, default=False, help="Reduces significantly the number of segments used to approximate the curve while still guaranteeing an accurate conversion, but may increase the execution time. Does not work for 'Singlelayer/paths'")
        self.arg_parser.add_argument("--parallel", type=inkex.Boolean, default=False, help="Enables multiprocessing for the SVG conversion. This is recommended ONLY when using 'Simplify geometry' on large SVG files with many curved elements. Does not work for 'Singlelayer/paths'")
        self.arg_parser.add_argument("--apply_transformations", type=inkex.Boolean, default=False, help="Run 'Apply Transformations' extension before running vpype. Helps avoiding geometry shifting")
        self.arg_parser.add_argument("--output_show", type=inkex.Boolean, default=False, help="This will open a new matplotlib window showing modified SVG data")
        self.arg_parser.add_argument("--output_stats", type=inkex.Boolean, default=False, help="Show output statistics before/after conversion")
        self.arg_parser.add_argument("--output_trajectories", type=inkex.Boolean, default=False, help="Add paths for the travel trajectories")
        self.arg_parser.add_argument("--keep_objects", type=inkex.Boolean, default=False, help="If false, selected paths will be removed")
        self.arg_parser.add_argument("--strokes_to_paths", type=inkex.Boolean, default=True, help="Recommended option. Performs 'Path' > 'Stroke to Path' (CTRL + ALT + C) to convert vpype converted lines back to regular path objects")
        self.arg_parser.add_argument("--use_style_of_first_element", type=inkex.Boolean, default=True, help="If enabled the first element in selection is scanned and we apply it's style to all imported vpype lines (but not for trajectories). Does not work for 'Multilayer/document'")
        self.arg_parser.add_argument("--lines_stroke_width", type=float, default=1.0, help="Stroke width of tooling lines (px). Gets overwritten if 'Use style of first selected element' is enabled")
        self.arg_parser.add_argument("--trajectories_stroke_width", type=float, default=1.0, help="Stroke width of trajectory lines (px). Gets overwritten if 'Use style of first selected element' is enabled")
 
    def effect(self):  
        lc = vpype.LineCollection() # create a new array of LineStrings consisting of Points. We convert selected paths to polylines and grab their points
        nodesToWork = [] # we make an array of all collected nodes to get the boundingbox of that array. We need it to place the vpype converted stuff to the correct XY coordinates
          
        applyTransformAvailable = False
        
        # at first we apply external extension
        try:
            sys.path.append("..") # add parent directory to path to allow importing applytransform (vpype extension is encapsulated in sub directory)
            import applytransform
            applyTransformAvailable = True
        except Exception as e:
            # inkex.utils.debug(e)
            inkex.utils.debug("Calling 'Apply Transformations' extension failed. Maybe the extension is not installed. You can download it from official InkScape Gallery. Skipping this step")

        def flatten(node):
            path = node.path.to_superpath()
            bezier.cspsubdiv(path, self.options.flatness)
            newpath = []
            for subpath in path:
                first = True
                for csp in subpath:
                    cmd = 'L'
                    if first:
                        cmd = 'M'
                    first = False
                    newpath.append([cmd, [csp[1][0], csp[1][1]]])
            node.path = newpath

        def convertPath(node):
            if node.tag == inkex.addNS('path','svg'):
                nodesToWork.append(node)
                if self.options.flattenbezier is True:
                    flatten(node)
                d = node.get('d')
                p = CubicSuperPath(d)
                points = []
                for subpath in p:
                    for csp in subpath:
                        points.append(Point(round(csp[1][0], self.options.decimals), round(csp[1][1], self.options.decimals)))
                lc.append(LineString(points))        
            children = node.getchildren()
            if children is not None: 
                for child in children:
                    convertPath(child)

        doc = None #create a vpype document
        
        '''
        if 'paths' we process paths only. Objects like rectangles or strokes like polygon have to be converted before accessing them
        if 'layers' we can process all layers in the complete document
        '''
        if self.options.input_handling == "paths":
            # getting the bounding box of the current selection. We use to calculate the offset XY from top-left corner of the canvas. This helps us placing back the elements
            input_bbox = None
            if self.options.apply_transformations is True and applyTransformAvailable is True:
                '''
                we need to apply transfoms to the complete document even if there are only some single paths selected. 
                If we apply it to selected nodes only the parent groups still might contain transforms. 
                This messes with the coordinates and creates hardly controllable behaviour
                '''
                applytransform.ApplyTransform().recursiveFuseTransform(self.document.getroot())
            if len(self.svg.selected) == 0:
                convertPath(self.document.getroot())
                for element in nodesToWork:
                    input_bbox += element.bounding_box()      
            else:
                for id, item in self.svg.selected.items():
                    convertPath(item)
                #input_bbox = inkex.elements._selected.ElementList.bounding_box(self.svg.selected) # get BoundingBox for selection
                input_bbox = self.svg.selection.bounding_box() # get BoundingBox for selection
            if len(lc) == 0:
                inkex.errormsg('Selection appears to be empty or does not contain any valid svg:path nodes. Try to cast your objects to paths using CTRL + SHIFT + C or strokes to paths using CTRL + ALT+ C')
                return  
            # find the first object in selection which has a style attribute (skips groups and other things which have no style)
            firstElementStyle = None
            for node in nodesToWork:
                if node.attrib.has_key('style'):
                    firstElementStyle = node.get('style')
            doc = vpype.Document(page_size=(input_bbox.width + input_bbox.left, input_bbox.height + input_bbox.top)) #create new vpype document     
            doc.add(lc, layer_id=None) # we add the lineCollection (converted selection) to the vpype document
            
        elif self.options.input_handling == "layers":
            doc = vpype.read_multilayer_svg(self.options.input_file, quantization = self.options.flatness, crop = False, simplify = self.options.simplify, parallel = self.options.parallel, default_width = self.document.getroot().get('width'), default_height = self.document.getroot().get('height'))

            for node in self.document.getroot().xpath("//svg:g", namespaces=inkex.NSS): #all groups/layers
                nodesToWork.append(node)

        tooling_length_before = doc.length()
        traveling_length_before = doc.pen_up_length()
        
        # build and execute the conversion command
        # the following code block is not intended to sum up the commands to build a series (pipe) of commands!
        ##########################################
        
        # Line Sorting
        if self.options.linesort is True:
            command = "linesort "
            if self.options.linesort_no_flip is True:
                command += " --no-flip"

        # Line Merging
        if self.options.linemerge is True:     
            command = "linemerge --tolerance " + str(self.options.linemerge_tolerance)
            if self.options.linemerge_no_flip is True:
                command += " --no-flip"
 
        # Trimming
        if self.options.trim is True:     
            command = "trim " + str(self.options.trim_x_margin) + " " + str(self.options.trim_y_margin)
 
        # Relooping
        if self.options.reloop is True:     
            command = "reloop --tolerance " + str(self.options.reloop_tolerance)
 
        # Multipass
        if self.options.multipass is True:     
            command = "multipass --count " + str(self.options.multipass_count)
 
        # Filter
        if self.options.filter is True:     
            command = "filter --tolerance " + str(self.options.filter_tolerance)
            if self.options.filter_min_length_enabled is True:
                command += " --min-length " + str(self.options.filter_min_length)
            if self.options.filter_max_length_enabled is True:
                command += " --max-length " + str(self.options.filter_max_length)
            if self.options.filter_closed is True and self.options.filter_not_closed is False:
                command += " --closed"
            if self.options.filter_not_closed is True and self.options.filter_closed is False:
                command += " --not-closed"
            if self.options.filter_closed is False and \
                self.options.filter_not_closed is False and \
                self.options.filter_min_length_enabled is False and \
                self.options.filter_max_length_enabled is False:
                inkex.errormsg('No filters to apply. Please select at least one filter.')
                return

        # Plugin Occult
        if self.options.plugin_occult is True:     
            command = "occult --tolerance " + str(self.options.plugin_occult_tolerance)

        # Split All
        if self.options.splitall is True:     
            command = " splitall"

        # Free Mode
        if self.options.freemode is True:
            command = ""
            if self.options.freemode_cmd1_enabled is True:
                command += " " + self.options.freemode_cmd1.strip()
            if self.options.freemode_cmd2_enabled is True:
                command += " " + self.options.freemode_cmd2.strip()
            if self.options.freemode_cmd3_enabled is True:
                command += " " + self.options.freemode_cmd3.strip()
            if self.options.freemode_cmd4_enabled is True:
                command += " " + self.options.freemode_cmd4.strip()
            if self.options.freemode_cmd5_enabled is True:
                command += " " + self.options.freemode_cmd5.strip()
            if self.options.freemode_cmd1_enabled is False and \
                self.options.freemode_cmd2_enabled is False and \
                self.options.freemode_cmd3_enabled is False and \
                self.options.freemode_cmd4_enabled is False and \
                self.options.freemode_cmd5_enabled is False:
                inkex.utils.debug("Warning: empty vpype pipeline. With this you are just getting read-write layerset/lineset.")
            else:
                if self.options.freemode_show_cmd is True:
                    inkex.utils.debug("Your command pipe will be the following:")
                    inkex.utils.debug(command)

        # inkex.utils.debug(command)
        try:
            doc = execute(command, doc)
        except Exception as e:
            inkex.utils.debug("Error in vpype:" + str(e))
            return

        ##########################################
        
        tooling_length_after = doc.length()
        traveling_length_after = doc.pen_up_length()        
        if tooling_length_before > 0:
            tooling_length_saving = (1.0 - tooling_length_after / tooling_length_before) * 100.0
        else:
            tooling_length_saving = 0.0            
        if traveling_length_before > 0:
            traveling_length_saving = (1.0 - traveling_length_after / traveling_length_before) * 100.0
        else:
            traveling_length_saving = 0.0  
        if self.options.output_stats is True:
            inkex.utils.debug('Total tooling length before vpype conversion: '   + str('{:0.2f}'.format(tooling_length_before))   + ' mm')
            inkex.utils.debug('Total traveling length before vpype conversion: ' + str('{:0.2f}'.format(traveling_length_before)) + ' mm')
            inkex.utils.debug('Total tooling length after vpype conversion: '    + str('{:0.2f}'.format(tooling_length_after))    + ' mm')
            inkex.utils.debug('Total traveling length after vpype conversion: '  + str('{:0.2f}'.format(traveling_length_after))  + ' mm')
            inkex.utils.debug('Total tooling length optimized: '   + str('{:0.2f}'.format(tooling_length_saving))   + ' %')
            inkex.utils.debug('Total traveling length optimized: ' + str('{:0.2f}'.format(traveling_length_saving)) + ' %')
         
        if tooling_length_after == 0:
            inkex.errormsg('No lines left after vpype conversion. Conversion result is empty. Cannot continue')
            return
         
        # show the vpype document visually
        if self.options.output_show:
            warnings.filterwarnings("ignore") # workaround to suppress annoying DeprecationWarning
            # vpype_viewer.show(doc, view_mode=ViewMode.PREVIEW, show_pen_up=self.options.output_trajectories, show_points=False, pen_width=0.1, pen_opacity=1.0, argv=None)
            vpype_viewer.show(doc, view_mode=ViewMode.PREVIEW, show_pen_up=self.options.output_trajectories, show_points=False, argv=None) # https://vpype.readthedocs.io/en/stable/api/vpype_viewer.ViewMode.html
            warnings.filterwarnings("default") # reset warning filter
            exit(0) #we leave the code loop because we only want to preview. We don't want to import the geometry
          
        # save the vpype document to new svg file and close it afterwards
        output_file = self.options.input_file + ".vpype.svg"
        output_fileIO = open(output_file, "w", encoding="utf-8")
        # vpype.write_svg(output_fileIO, doc, page_size=None, center=False, source_string='', layer_label_format='%d', show_pen_up=self.options.output_trajectories, color_mode='layer', no_basic_shapes = True)       
        vpype.write_svg(output_fileIO, doc, page_size=None, center=False, source_string='', layer_label_format='%d', show_pen_up=self.options.output_trajectories, color_mode='layer')       
        #vpype.write_svg(output_fileIO, doc, page_size=(self.svg.unittouu(self.document.getroot().get('width')), self.svg.unittouu(self.document.getroot().get('height'))), center=False, source_string='', layer_label_format='%d', show_pen_up=self.options.output_trajectories, color_mode='layer')       
        output_fileIO.close()
        
        # convert vpype polylines/lines/polygons to regular paths again. We need to use "--with-gui" to respond to "WARNING: ignoring verb FileSave - GUI required for this verb."
        if self.options.strokes_to_paths is True:
            cli_output = inkscape(output_file, "--with-gui", actions="EditSelectAllInAllLayers;EditUnlinkClone;ObjectToPath;FileSave;FileQuit")
            if len(cli_output) > 0:
                self.debug(_("Inkscape returned the following output when trying to run the vpype object to path back-conversion:"))
                self.debug(cli_output)
               
        # parse the SVG file
        try:
            stream = open(output_file, 'r')
        except FileNotFoundError as e:
            inkex.utils.debug("There was no SVG output generated by vpype. Cannot continue")
            exit(1)
        p = etree.XMLParser(huge_tree=True)
        import_doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True))
        stream.close()
          
        # handle pen_up trajectories (travel lines)
        trajectoriesLayer = import_doc.getroot().xpath("//svg:g[@id='pen_up_trajectories']", namespaces=inkex.NSS)
        if self.options.output_trajectories is True:
            if len(trajectoriesLayer) > 0:
                trajectoriesLayer[0].set('style', 'stroke:#0000ff;stroke-width:{:0.2f}px;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1;fill:none'.format(self.options.trajectories_stroke_width))
                trajectoriesLayer[0].attrib.pop('stroke') # remove unneccesary stroke attribute
                trajectoriesLayer[0].attrib.pop('fill') # remove unneccesary fill attribute
        else:
            if len(trajectoriesLayer) > 0:
                trajectoriesLayer[0].getparent().remove(trajectoriesLayer[0])
   
        lineLayers = import_doc.getroot().xpath("//svg:g[not(@id='pen_up_trajectories')]", namespaces=inkex.NSS) #all layer except the pen_up trajectories layer
        if self.options.use_style_of_first_element is True and self.options.input_handling == "paths" and firstElementStyle is not None:
            for lineLayer in lineLayers:
                lineLayer.set('style', firstElementStyle)
                lineLayer.attrib.pop('stroke') # remove unneccesary stroke attribute
                lineLayer.attrib.pop('fill') # remove unneccesary fill attribute

        else:
            for lineLayer in lineLayers:          
                if lineLayer.attrib.has_key('stroke'):
                    color = lineLayer.get('stroke')
                    lineLayer.set('style', 'stroke:' + color + ';stroke-width:{:0.2f}px;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1;fill:none'.format(self.options.lines_stroke_width))
                    lineLayer.attrib.pop('stroke') # remove unneccesary stroke attribute
                    lineLayer.attrib.pop('fill') # remove unneccesary fill attribute

        import_viewBox = import_doc.getroot().get('viewBox').split(" ")
        self_viewBox = self.document.getroot().get('viewBox').split(" ")
        scaleX = self.svg.unittouu(self_viewBox[2]) / self.svg.unittouu(import_viewBox[2])
        scaleY = self.svg.unittouu(self_viewBox[3]) / self.svg.unittouu(import_viewBox[3])

        for element in import_doc.getroot().iter("{http://www.w3.org/2000/svg}g"):
            self.document.getroot().append(element)
            if self.options.input_handling == "layers":
                element.set('transform', 'scale(' + str(scaleX) + ',' + str(scaleY) + ')') #imported groups need to be transformed. Or they have wrong size. Reason: different viewBox sizes/units in namedview definitions
                if self.options.apply_transformations is True and applyTransformAvailable is True: #we apply the transforms directly after adding them
                    applytransform.ApplyTransform().recursiveFuseTransform(element) 

        # Delete the temporary file again because we do not need it anymore
        if os.path.exists(output_file):
            os.remove(output_file)
            
        # Remove selection objects to do a real replace with new objects from vpype document
        if self.options.keep_objects is False:
            for node in nodesToWork:
                node.getparent().remove(node)
    
if __name__ == '__main__':
    vpypetools().run()