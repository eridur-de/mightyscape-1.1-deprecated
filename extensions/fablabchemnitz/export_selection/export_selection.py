#!/usr/bin/env python3

from copy import deepcopy
from pathlib import Path
import logging
import math
import os
import sys
import subprocess
from subprocess import Popen, PIPE
import warnings
import inkex
import inkex.command
from inkex.command import inkscape, inkscape_command

from lxml import etree
from scour.scour import scourString

'''
ToDo: work with temporary SVG file in temp dir instead handling deletion stuff at the end / valide that the file exists when spawning new instance
'''

logger = logging.getLogger(__name__)

DETACHED_PROCESS = 0x00000008
GROUP_ID = 'export_selection_transform'

class ExportObject(inkex.EffectExtension):
    
    def add_arguments(self, pars):
        pars.add_argument("--wrap_transform", type=inkex.Boolean, default=False, help="Wrap final document in transform")
        pars.add_argument("--border_offset", type=float, default=1.000, help="Add border offset around selection")
        pars.add_argument("--export_dir", default="~/inkscape_export/",    help="Location to save exported documents")
        pars.add_argument("--opendir", type=inkex.Boolean, default=False, help="Open containing output directory after export")
        pars.add_argument("--dxf_exporter_path", default="/usr/share/inkscape/extensions/dxf_outlines.py", help="Location of dxf_outlines.py")
        pars.add_argument("--export_svg", type=inkex.Boolean, default=False, help="Create a svg file")
        pars.add_argument("--export_dxf", type=inkex.Boolean, default=False, help="Create a dxf file")
        pars.add_argument("--export_pdf", type=inkex.Boolean, default=False, help="Create a pdf file")
        pars.add_argument("--newwindow", type=inkex.Boolean, default=False, help="Open file in new Inkscape window")      

    def openExplorer(self, dir):
        if os.name == 'nt':
            Popen(["explorer", dir], close_fds=True, creationflags=DETACHED_PROCESS).wait()
        else:
            Popen(["xdg-open", dir], close_fds=True, start_new_session=True).wait()

    def spawnIndependentInkscape(self, file): #function to spawn non-blocking inkscape instance. the inkscape command is available because it is added to ENVIRONMENT when Inkscape main instance is started
        warnings.simplefilter('ignore', ResourceWarning) #suppress "enable tracemalloc to get the object allocation traceback"
        if os.name == 'nt':
            Popen(["inkscape", file], close_fds=True, creationflags=DETACHED_PROCESS)
        else:
            subprocess.Popen(["inkscape", file], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        warnings.simplefilter("default", ResourceWarning)

    def effect(self):
        
        svg_export = self.options.export_svg
        
        if self.options.export_svg is False and \
            self.options.export_dxf is False and \
            self.options.export_pdf is False and \
            self.options.newwindow is False:
            inkex.utils.debug("You must select at least one option to continue!")
            return
        else:
            self.options.export_svg = True #required for all other options!
        
        if not self.svg.selected:
            inkex.errormsg("Selection is empty. Please select some objects first!")
            return

        #preflight check for DXF input dir
        if not os.path.exists(self.options.dxf_exporter_path):
            inkex.utils.debug("Location of dxf_outlines.py does not exist. Please select a proper file and try again.")
            exit(1)
            
        export_dir = Path(self.absolute_href(self.options.export_dir))
        os.makedirs(export_dir, exist_ok=True)

        offset = self.options.border_offset

        bbox = inkex.BoundingBox()

        for elem in self.svg.selected.values():
            transform = inkex.Transform()
            parent = elem.getparent()
            if parent is not None and isinstance(parent, inkex.ShapeElement):
                transform = parent.composed_transform()
            try:
                bbox += elem.bounding_box(transform)
            except Exception:
                logger.exception("Bounding box not computed")
                logger.info("Skipping bounding box")
                transform = elem.composed_transform()
                x1, y1 = transform.apply_to_point([0, 0])
                x2, y2 = transform.apply_to_point([1, 1])
                bbox += inkex.BoundingBox((x1, x2), (y1, y2))

        template = self.create_document()
        svg_filename = None

        group = etree.SubElement(template, '{http://www.w3.org/2000/svg}g')
        group.attrib['id'] = GROUP_ID
        group.attrib['transform'] = str(inkex.Transform(((1, 0, -bbox.left), (0, 1, -bbox.top))))

        for elem in self.svg.selected.values():
            elem_copy = deepcopy(elem)
            elem_copy.attrib['transform'] = str(elem.composed_transform())
            elem_copy.attrib['style'] = str(elem.composed_style())            
            group.append(elem_copy)

            template.attrib['viewBox'] = f'{-offset} {-offset} {bbox.width + offset * 2} {bbox.height + offset * 2}'
            template.attrib['width'] = f'{bbox.width + offset * 2}' + self.svg.unit
            template.attrib['height'] = f'{bbox.height + offset * 2}' + self.svg.unit

            if svg_filename is None:
                filename_base = elem.attrib.get('id', None).replace(os.sep, '_')
                if filename_base:
                    svg_filename = filename_base + '.svg'
        if not filename_base: #should never be the case. Inkscape might crash if the id attribute is empty or not existent due to invalid SVG
            filename_base = self.svg.get_unique_id("selection")
            svg_filename = filename_base + '.svg'

        template.append(group)

        if not self.options.wrap_transform:
            self.load(inkscape_command(template.tostring(), select=GROUP_ID, verbs=['SelectionUnGroup']))
            template = self.svg
            for child in template.getchildren():
                if child.tag == '{http://www.w3.org/2000/svg}metadata':
                    template.remove(child)

        if self.options.export_svg is True:
            self.save_document(template, export_dir / svg_filename)
        
        if self.options.opendir is True:
            self.openExplorer(export_dir)
            
        if self.options.newwindow is True:
            #inkscape(os.path.join(export_dir, svg_filename)) #blocking cmd
            self.spawnIndependentInkscape(os.path.join(export_dir, svg_filename)) #non-blocking
            
        if self.options.export_dxf is True:
            #ensure that python command is available #we pass 25.4/96 which stands for unit mm. See inkex.units.UNITS and dxf_outlines.inx
            cmd = [
                sys.executable, #the path of the python interpreter which is used for this script 
                self.options.dxf_exporter_path, 
                '--output=' + os.path.join(export_dir, filename_base + '.dxf'), 
                r'--units=25.4/96', 
                os.path.join(export_dir, svg_filename)
                ]
            proc = Popen(cmd, shell=False, stdout=PIPE, stderr=PIPE)
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                inkex.utils.debug("%d %s %s" % (proc.returncode, stdout, stderr))
            
        if self.options.export_pdf is True:    
            cli_output = inkscape(os.path.join(export_dir, svg_filename), actions='export-pdf-version:1.5;export-text-to-path;export-filename:{file_name};export-do;FileClose'.format(file_name=os.path.join(export_dir, filename_base + '.pdf')))
            if len(cli_output) > 0:
                self.msg("Inkscape returned the following output when trying to run the file export; the file export may still have worked:")
                self.msg(cli_output)
                
        if svg_export is False and self.options.newwindow is False: #we need the SVG file in case we open in new window because we spawn a new instance
            os.remove(os.path.join(export_dir, svg_filename)) #remove SVG if not enabled to export. Might delete existing SVG accidently!
      
    def create_document(self):
        document = self.svg.copy()
        for child in document.getchildren():
            if child.tag == '{http://www.w3.org/2000/svg}defs':
                continue
            document.remove(child)
        return document

    def save_document(self, document, filename):
        with open(filename, 'wb') as fp:
            document = document.tostring()
            fp.write(scourString(document).encode('utf8'))


if __name__ == '__main__':
    ExportObject().run()