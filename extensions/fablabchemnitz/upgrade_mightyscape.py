#!/usr/bin/env python3

"""
Upgrade MightyScape from Inkscape Extension Dialog. Made for end users

Extension for InkScape 1.X
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 14.05.2021
Last patch: 14.05.2021
License: GNU GPL v3
"""

import inkex
import os
from git import Repo

class Upgrade(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--stash_untracked", type=inkex.Boolean, default=False, help="Stash untracked files and continue to upgrade")

    def effect(self):
        #get the directory of mightyscape
        extension_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../', '../') #go up to dir /home/<user>/.config/inkscape/extensions/mightyscape-1.X/

        repo = Repo(os.path.join(extension_dir, ".git"))
        
        #check if it is a non-empty git repository
        if repo.bare is False:
            
            if repo.is_dirty(untracked_files=True) is False:        
                if len(repo.untracked_files) > 0:
                    if self.options.stash_untracked is True:
                        repo.git.stash('save')
                    else:
                        inkex.utils.debug("There are some untracked files in your MightyScape directory. Still trying to pull recent files from git...")
                        
                origin = repo.remotes.origin
                fetch_info = origin.fetch()
    
                for info in fetch_info:
                    inkex.utils.debug("Updated %s to %s" % (info.ref, info.commit))
                
                #finally pull new data    
                origin.pull()
            else:
                inkex.utils.debug("MightyScape is up to date!")  
                exit(0)     

        else:
            inkex.utils.debug("No \".git\" directory found. Seems your MightyScape was not installed with git clone. Please see documentation on how to do that.")  
            exit(1)

if __name__ == '__main__':
    Upgrade().run()