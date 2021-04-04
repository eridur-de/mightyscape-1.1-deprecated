#!/usr/bin/env python3

# suppress some nasty warnings we don't want. Note that this is really generic. For developing purposes re-enable this to see errors/deprecations
import logging
for key in logging.Logger.manager.loggerDict:
    print(key)
logging.getLogger().setLevel(logging.CRITICAL)
#for name, logger in logging.root.manager.loggerDict.items():
#    logger.disabled=True
#import warnings
#warnings.filterwarnings("ignore", category=DeprecationWarning)
#warnings.filterwarnings('always', category=DeprecationWarning)
#with warnings.catch_warnings():
#    warnings.simplefilter("ignore", category=DeprecationWarning)
#def noop(*args, **kargs): pass
#warnings.warn = noop
#logging.captureWarnings(True)

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

from shapely.geometry import LineString, Point

"""
Extension for InkScape 1.X
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 02.04.2021
Last patch: 03.04.2021
License: GNU GPL v3

Used (tested) version of vpype: commit id https://github.com/abey79/vpype/commit/0b0dc8dd7e32998dbef639f9db578c3bff02690b (29.03.2021)
Used (tested) version of vpype occult: commit id https://github.com/LoicGoulefert/occult/commit/2d04ca57d69078755c340066c226fd6cd927d41e (04.02.2021)

CLI / API docs:
- https://vpype.readthedocs.io/en/stable/api/vpype_cli.html#module-vpype_cli
- https://vpype.readthedocs.io/en/stable/api/vpype.html#module-vpype

vpype commands could be performed differently: 
 - 1. Work with current selection (line-wise): we could get the selected nodes/groups and check if those nodes are paths. If yes we could convert them to polylines and put it into vpype using doc.add(LineCollection, Layer)
 - 2. We could execute vpype on the complete document only (svg file handling, possible as one layer or multiple layers)
      working line of code (example:) doc = vpype.read_multilayer_svg(self.options.input_file, quantization=0.1, crop=False, simplify=False, parallel=False)

Todo's
- allow to change pen width / opacity in vpype viewer: https://github.com/abey79/vpype/issues/243
- command chain is really slow on Windows (takes ~5 times longer than Linux)
- add some debugging options to remove deprecation warnings of vpype/vpype_viewer
- allow to select other units than mm for tolerance, trimming, ... At the moment vpype uses millimeters regardless of the document units/display units in namedview
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
 
        # Plugin Occult
        self.arg_parser.add_argument("--plugin_occult", type=inkex.Boolean, default=False)
        self.arg_parser.add_argument("--plugin_occult_tolerance", type=float, default=0.01, help="Max distance between start and end point to consider a path closed (default 0.01 mm)")
 
        # General Settings
        self.arg_parser.add_argument("--flattenbezier", type=inkex.Boolean, default=False, help="Flatten bezier curves to polylines")        
        self.arg_parser.add_argument("--flatness", type=float, default=0.1, help="Minimum flatness = 0.1. The smaller the value the more fine segments you will get.")    
        self.arg_parser.add_argument("--apply_transformations", type=inkex.Boolean, default=False, help="Run 'Apply Transformations' extension before running vpype. Helps avoiding geometry shifting")
        self.arg_parser.add_argument("--output_show", type=inkex.Boolean, default=False, help="This will open a new matplotlib window showing modified SVG data")
        self.arg_parser.add_argument("--output_stats", type=inkex.Boolean, default=False, help="Show output statistics before/after conversion")
        self.arg_parser.add_argument("--output_trajectories", type=inkex.Boolean, default=False, help="Add paths for the travel trajectories")
        self.arg_parser.add_argument("--keep_selection", type=inkex.Boolean, default=False, help="If false, selected paths will be removed")
        self.arg_parser.add_argument("--strokes_to_paths", type=inkex.Boolean, default=True, help="Recommended option. Performs 'Path' > 'Stroke to Path' (CTRL + ALT + C) to convert vpype converted lines back to regular path objects")
 
    def effect(self):  
        lc = vpype.LineCollection() # create a new array of LineStrings consisting of Points. We convert selected paths to polylines and grab their points
        nodesToConvert = [] # we make an array of all collected nodes to get the boundingbox of that array. We need it to place the vpype converted stuff to the correct XY coordinates
        
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
                nodesToConvert.append(node)
                if self.options.flattenbezier is True:
                    flatten(node)
                d = node.get('d')
                p = CubicSuperPath(d)
                points = []
                for subpath in p:
                    for csp in subpath:
                        points.append(Point(csp[1][0], csp[1][1]))
                lc.append(LineString(points))        
            children = node.getchildren()
            if children is not None: 
                for child in children:
                    convertPath(child)

        # inkex.utils.debug(str(applyTransformAvailable)) #check if ApplyTransform Extension is available. If yes we use it
        if self.options.apply_transformations is True and applyTransformAvailable is True:
            applytransform.ApplyTransform().recursiveFuseTransform(self.document.getroot())

        # getting the bounding box of the current selection. We use to calculate the offset XY from top-left corner of the canvas. This helps us placing back the elements
        input_bbox = None
        if len(self.svg.selected) == 0:
            convertPath(self.document.getroot())
            for element in nodesToConvert:
                input_bbox += element.bounding_box()      
        else:
            for id, item in self.svg.selected.items():
                convertPath(item)
            input_bbox = inkex.elements._selected.ElementList.bounding_box(self.svg.selected) # get BoundingBox for selection
            
        # inkex.utils.debug(input_bbox)
            
        # lc.as_mls() #cast LineString array to MultiLineString

        if len(lc) == 0:
            inkex.errormsg('Selection appears to be empty or does not contain any valid svg:path nodes. Try to cast your objects to paths using CTRL + SHIFT + C or strokes to paths using CTRL + ALT+ C')
            return

        doc = vpype.Document(page_size=(input_bbox.width + input_bbox.left, input_bbox.height + input_bbox.top)) #create new vpype document
        
        # we add the lineCollection (converted selection) to the vpype document
        doc.add(lc, layer_id=None)
        #doc.translate(input_bbox.left, input_bbox.top) #wrong units?

        tooling_length_before = doc.length()
        traveling_length_before = doc.pen_up_length()
        
        # build and execute the conversion command
        # the following code block is not intended to sum up the commands to build a series (pipe) of commands!
        ##########################################
        
        # Line Sort
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
            if self.options.filter_closed is True:
                command += " --closed"
            if self.options.filter_not_closed is True:
                command += " --not-closed"
            if self.options.filter_closed is False and self.options.filter_not_closed is False and self.options.filter_min_length_enabled is False and self.options.filter_max_length_enabled is False:
                inkex.errormsg('No filters to apply. Please select at least one filter.')
                return

        # Plugin Occult
        if self.options.plugin_occult is True:     
            command = "occult --tolerance " + str(self.options.plugin_occult_tolerance)

        # inkex.utils.debug(command)
        doc = execute(command, doc)

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
        # there are missing options to set pen_width and pen_opacity. This is anchored in "Engine" class
        if self.options.output_show:
            vpype_viewer.show(doc, view_mode=ViewMode.PREVIEW, show_pen_up=self.options.output_trajectories, show_points=False, argv=None) # https://vpype.readthedocs.io/en/stable/api/vpype_viewer.ViewMode.html
          
        # save the vpype document to new svg file and close it afterwards
        output_file = self.options.input_file + ".vpype.svg"
        output_fileIO = open(output_file, "w", encoding="utf-8")
        vpype.write_svg(output_fileIO, doc, page_size=None, center=False, source_string='', layer_label_format='%d', show_pen_up=self.options.output_trajectories, color_mode='layer')       
        output_fileIO.close()
        
        # convert vpype polylines/lines/polygons to regular paths again. We need to use "--with-gui" to respond to "WARNING: ignoring verb FileSave - GUI required for this verb."
        if self.options.strokes_to_paths is True:
            cli_output = inkscape(output_file, "--with-gui", actions="EditSelectAllInAllLayers;EditUnlinkClone;ObjectToPath;FileSave;FileQuit")
            if len(cli_output) > 0:
                self.debug(_("Inkscape returned the following output when trying to run the vpype object to path back-conversion:"))
                self.debug(cli_output)
        
        # new parse the SVG file and insert it as new group into the current document tree
        # vpype_svg = etree.parse(output_file).getroot().xpath("//svg:g", namespaces=inkex.NSS)
        
        # the label id is the number of layer_id=None (will start with 1)
        lines = etree.parse(output_file).getroot().xpath("//svg:g[@inkscape:label='1']",namespaces=inkex.NSS) 
        vpypeLinesGroup = self.document.getroot().add(inkex.Group())
        vpypeLinesGroup.set('style', 'stroke:#000000;stroke-width:1px;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1;fill:none')       
        for item in lines:
            for child in item.getchildren(): 
                vpypeLinesGroup.append(child)
        # get the output's bounding box size (which might be other size than previous input bounding box, e.g. when using trim feature)
        # output_bbox = vpypeLinesGroup.bounding_box()
        
        # when using the trim function the bounding box of the original elements will not match the vpype'd ones. So we need to do some calculation for exact placement
        #translation = 'translate(' + str(input_bbox.left + self.options.trim_x_margin) + ',' + str(input_bbox.top + self.options.trim_y_margin) + ')' # we use the same translation for trajectory lines
        #vpypeLinesGroup.attrib['transform'] = translation # disabled because we use PageSize with vpype now
        vpypeLinesGroupId = self.svg.get_unique_id('vpypetools-lines-')
        vpypeLinesGroup.set('id', vpypeLinesGroupId)
    
        # inkex.utils.debug(self.svg.selection.first()) # get the first selected element. Chould be None
        self.svg.selection.set(vpypeLinesGroupId)
        # inkex.utils.debug(self.svg.selection.first()) # get the first selected element again to check if changing selection has worked
    
        if self.options.output_trajectories is True:
            trajectories = etree.parse(output_file).getroot().xpath("//svg:g[@id='pen_up_trajectories']",namespaces=inkex.NSS)
            vpypeTrajectoriesGroup = self.document.getroot().add(inkex.Group())
            vpypeTrajectoriesGroup.set('style', 'stroke:#0000ff;stroke-width:1px;stroke-miterlimit:4;stroke-dasharray:none;stroke-opacity:1;fill:none')       
            for item in trajectories:
                for child in item.getchildren(): 
                    vpypeTrajectoriesGroup.append(child)
            #vpypeTrajectoriesGroup.attrib['transform'] = translation # disabled because we use PageSize with vpype now
            vpypeTrajectoriesId = self.svg.get_unique_id('vpypetools-trajectories-')
            vpypeTrajectoriesGroup.set('id', vpypeTrajectoriesId)
            self.svg.selection.add(vpypeTrajectoriesId) # we also add trajectories to selection to remove translations in following step
          
        # we apply transformations also for new group to remove the "translate()" again # disabled because we use PageSize with vpype now
        #if self.options.apply_transformations and applyTransformAvailable:
        #    for node in self.svg.selection:
        #        applytransform.ApplyTransform().recursiveFuseTransform(node) 

        # Delete the temporary file again because we do not need it anymore
        if os.path.exists(output_file):
            os.remove(output_file)
            
        # Remove selection objects to do a real replace with new objects from vpype document
        if self.options.keep_selection is False:
            for node in nodesToConvert:
                node.getparent().remove(node)
    
if __name__ == '__main__':
    vpypetools().run()