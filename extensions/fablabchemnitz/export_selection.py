#!/usr/bin/env python3

from copy import deepcopy
from pathlib import Path
import logging
import math
import os
import subprocess
from subprocess import Popen, PIPE

import inkex
import inkex.command
from inkex.command import inkscape, inkscape_command

from lxml import etree
from scour.scour import scourString


logger = logging.getLogger(__name__)


GROUP_ID = 'export_selection_transform'


class ExportObject(inkex.EffectExtension):
	
	def add_arguments(self, pars):
		pars.add_argument("--wrap_transform", type=inkex.Boolean, default=False, help="Wrap final document in transform")
		pars.add_argument("--export_dir", default="~/inkscape_export/",	help="Location to save exported documents")
		pars.add_argument("--opendir", type=inkex.Boolean, default=False, help="Open containing output directory after export")
		pars.add_argument("--dxf_exporter_path", default="/usr/share/inkscape/extensions/dxf_outlines.py", help="Location of dxf_outlines.py")
		pars.add_argument("--export_dxf", type=inkex.Boolean, default=False, help="Create a dxf file")
		pars.add_argument("--newwindow", type=inkex.Boolean, default=False, help="Open file in new Inkscape window")
		

	def openExplorer(self, dir):
		DETACHED_PROCESS = 0x00000008
		if os.name == 'nt':
			Popen(["explorer", dir], close_fds=True, creationflags=DETACHED_PROCESS).wait()
		else:
			Popen(["xdg-open", dir], close_fds=True, start_new_session=True).wait()

	def effect(self):
		if not self.svg.selected:
			inkex.errormsg("Selection is empty. Please select some objects first!")
			return

		export_dir = Path(self.absolute_href(self.options.export_dir))
		os.makedirs(export_dir, exist_ok=True)

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
		filename = None

		group = etree.SubElement(template, '{http://www.w3.org/2000/svg}g')
		group.attrib['id'] = GROUP_ID
		group.attrib['transform'] = str(inkex.Transform(((1, 0, -bbox.left), (0, 1, -bbox.top))))

		for elem in self.svg.selected.values():

			elem_copy = deepcopy(elem)
			elem_copy.attrib['transform'] = str(elem.composed_transform())
			group.append(elem_copy)

			width = math.ceil(bbox.width)
			height = math.ceil(bbox.height)
			template.attrib['viewBox'] = f'0 0 {width} {height}'
			template.attrib['width'] = f'{width}' + self.svg.unit
			template.attrib['height'] = f'{height}' + self.svg.unit

			if filename is None:
				filename = elem.attrib.get('id', None)
				if filename:
					filename = filename.replace(os.sep, '_') + '.svg'
		if not filename:
			filename = 'element.svg'

		template.append(group)

		if not self.options.wrap_transform:
			self.load(inkscape_command(template.tostring(), select=GROUP_ID, verbs=['SelectionUnGroup']))
			template = self.svg
			for child in template.getchildren():
				if child.tag == '{http://www.w3.org/2000/svg}metadata':
					template.remove(child)

		self.save_document(template, export_dir / filename)
		
		if self.options.opendir is True:
			self.openExplorer(export_dir)
			
		if self.options.newwindow is True:
			inkscape(os.path.join(export_dir, filename))
			
		if self.options.export_dxf is True:
			#ensure that python3 command is available #we pass 25.4/96 which stands for unit mm. See inkex.units.UNITS and dxf_outlines.inx
			cmd = ['python3', self.options.dxf_exporter_path, '--output=' + os.path.join(export_dir, filename + '.dxf'), r'--units=25.4/96', os.path.join(export_dir, filename)]
			proc = Popen(cmd, shell=False, stdout=PIPE, stderr=PIPE)
			stdout, stderr = proc.communicate()
			#inkex.utils.debug("%d %s %s" % (proc.returncode, stdout, stderr))
				   
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