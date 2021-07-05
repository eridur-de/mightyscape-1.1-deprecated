#!/usr/bin/env python3
"""
table.py
Table support for Inkscape

Copyright (C) 2011 Cosmin Popescu, cosminadrianpopescu@gmail.com

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
"""

import sys, os, optparse
sys.path.append(os.path.dirname(sys.argv[0]))

class install():
    OptionParser = optparse.OptionParser(usage="usage: %prog [options] SVGfile")
    
    def __init__(self):
        opts = [('-i', '--input', 'string', 'input', '/tmp/i',
                 'The input file'),
                 ('-o', '--output', 'string', 'output', '/tmp/o',
                 'The output file'),
                ]
        for o in opts:
            self.OptionParser.add_option(o[0], o[1], action="store", type=o[2],
                                         dest=o[3], default=o[4], help=o[5])
        self.getoptions()

    def getoptions(self,args=sys.argv[1:]):
        """Collect command line arguments"""
        self.options, self.args = self.OptionParser.parse_args(args)
        
    def do_install(self):
        f = open(self.options.input, 'r')
        content = f.read()
        f.close()

        f = open(self.options.output, 'r')
        _c = f.read()
        f.close()

        _c = _c.replace('</keys>', content + '\n</keys>')

        f = open(self.options.output, 'w')
        f.write(_c)
        f.close()

if __name__ == '__main__':   #pragma: no cover
    e = install()
    e.do_install()
