#!/usr/bin/env python
# coding=utf-8
#
# Copyright (C) 2021 roberta bennett repeatingshadow@protonmail.com
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
Create svg path animation from frames.

Place each frame of the animation in a layer named 'frame'.
Each of these layers should have the same number of paths,
and each path should have the same number of points as the corresponding
path in other layers.

The animation is applied to the paths in the first layer in the sequence, so the
properties of that layer are used. 

Animations with different numbers of frames can be put into different sequences, 
named 'sequence', using sub-groups:

Layers:
 not_animated_layer1
 sequence
  frame
   path1a
   path2a
  frame
   path1b
   path2b
  frame
   path1c
   path2c
  frame
   path1d
   path2d
 sequence
  frame
  frame
  frame 


use layer named exactly 'frame' and groups named exactly 'sequence',
not, eg, frame1 frame2 frame3 !

"""

import inkex

class AnimateElement(inkex.BaseElement):
    """animation Elements do not have a visible representation on the canvas"""
    tag_name = 'animate'
    @classmethod
    def new(cls, **attrs):
        return super().new( **attrs)
        
        
class AnimationExtension(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--begin_str", default="0", help="begin string: eg 0;an2.end;an3.begin")
        pars.add_argument("--repeat_str",  default="indefinite", help="indefinite or an integer")
        pars.add_argument("--dur_str",  default="7.9", help="duration in seconds. Do not decorate with units")
                       

    def effect(self):
        sequences = self.svg.findall("svg:g[@inkscape:label='sequence']")
        if len(sequences) == 0:
            raise inkex.AbortExtension("layer named sequence does not exist.")
        for sequence in sequences:
            frames = sequence.findall("svg:g[@inkscape:label='frame']")
            if len(frames) == 0:
                 raise inkex.AbortExtension("layer named frame does not exist.")
            frame0paths = frames[0].findall('svg:path')
            Dlists = [p.get_path() for p in frame0paths]
            for frame in frames[1:]:
                paths = frame.findall("svg:path")
                for i,p in enumerate(paths):
                    Dlists[i] += ";\n"+p.get_path()
            for i,dl in enumerate(Dlists):    
                animel = AnimateElement(
                	attributeName="d",
                	attributeType="XML",
                	begin=self.options.begin_str,
                	dur=self.options.dur_str,
                	repeatCount=self.options.repeat_str,
                	values=dl)
                frame0paths[i].append(animel)

if __name__ == '__main__':
    AnimationExtension().run()
    
    
