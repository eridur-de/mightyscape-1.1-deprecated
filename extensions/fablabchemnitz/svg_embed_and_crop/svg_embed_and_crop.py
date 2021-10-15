import inkex
import subprocess
import os
from lxml import etree
from inkex import command

class EmbedAndCrop(inkex.EffectExtension):

	def effect(self):
		cp = os.path.dirname(os.path.abspath(__file__)) + "/svg_embed_and_crop/*"
		output_file = self.options.input_file + ".cropped"
		command.call('java', '-cp', cp, 'edu.emory.cellbio.svg.EmbedAndCropInkscapeEntry', self.options.input_file, "-o", output_file)
		if not os.path.exists(output_file):
			raise inkex.AbortExtension("Plugin canceled")
		stream = open(output_file, 'r')
		p = etree.XMLParser(huge_tree=True)
		doc = etree.parse(stream, parser=etree.XMLParser(huge_tree=True))
		stream.close()
		root = self.document.getroot()
		kept = [] #required. if we delete them directly without adding new defs or namedview, inkscape will crash
		for node in self.document.xpath('//*', namespaces=inkex.NSS):
			if node.TAG not in ('svg', 'defs', 'namedview'):
				node.delete()
			elif node.TAG in ('defs', 'namedview'): #except 'svg'
				kept.append(node)
		
		children = doc.getroot().getchildren()
		for child in children:
		   root.append(child)
		for k in kept:
			k.delete()

if __name__ == '__main__':
	EmbedAndCrop().run()