#!/usr/bin/env python3

import inkex
import sys

class AttribEditor(inkex.Effect):
	def __init__(self):
		inkex.Effect.__init__(self)
		self.arg_parser.add_argument("-a", "--attributeName", help="attribute name to set")
		self.arg_parser.add_argument("-v", "--attributeValue", help="attribute value to set")
		self.arg_parser.add_argument("-m", "--mode", default="set", help="mode of operation")

	def effect(self):
		if not self.options.attributeName:   # if attributeName is not given
			self.OptionParser.error("Attribute name not given")

		elements = self.svg.selected.values()
		for el in elements:
			currentAtt = el.attrib.get(self.options.attributeName)
			if currentAtt is None:
				currentAtt = ""

			if self.options.mode == "set":
				el.attrib[self.options.attributeName] = self.options.attributeValue
			elif self.options.mode == "append":
				el.attrib[self.options.attributeName] = currentAtt + self.options.attributeValue
			elif self.options.mode == "prefix":
				el.attrib[self.options.attributeName] = self.options.attributeValue + currentAtt
			elif self.options.mode == "subtract":
				el.attrib[self.options.attributeName] = currentAtt.replace(self.options.attributeValue, "")
			elif self.options.mode == "remove":
				if self.options.attributeName in el.attrib:
					del el.attrib[self.options.attributeName]
			else:
				inkex.errormsg(_("Invalid mode: " + self.options.mode))

if __name__ == "__main__":
	AttribEditor().run()