# -*- coding: utf-8 -*-
from copy import deepcopy
from pathlib import Path
import logging
import math
import os

import inkex
import inkex.command
from lxml import etree
from scour.scour import scourString


logger = logging.getLogger(__name__)


GROUP_ID = 'export_selection_transform'


class ExportObject(inkex.EffectExtension):
	def add_arguments(self, pars):
		pars.add_argument("--wrap_transform", type=inkex.Boolean, default=False, help="Wrap final document in transform")
		pars.add_argument("--export_dir", default="~/inkscape_export/",	help="Location to save exported documents")

	def effect(self):
		if not self.svg.selected:
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
			template.attrib['width'] = f'{width}'
			template.attrib['height'] = f'{height}'

			if filename is None:
				filename = elem.attrib.get('id', None)
				if filename:
					filename = filename.replace(os.sep, '_') + '.svg'
		if not filename:
			filename = 'element.svg'

		template.append(group)

		if not self.options.wrap_transform:
			self.load(inkex.command.inkscape_command(template.tostring(), select=GROUP_ID, verbs=['SelectionUnGroup']))
			template = self.svg
			for child in template.getchildren():
				if child.tag == '{http://www.w3.org/2000/svg}metadata':
					template.remove(child)

		self.save_document(template, export_dir / filename)

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