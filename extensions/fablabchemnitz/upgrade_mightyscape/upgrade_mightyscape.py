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
import warnings
from git import Repo #requires GitPython lib

class Upgrade(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--stash_untracked", type=inkex.Boolean, default=False, help="Stash untracked files and continue to upgrade")

    def effect(self):
        warnings.simplefilter('ignore', ResourceWarning) #suppress "enable tracemalloc to get the object allocation traceback"

        #get the directory of mightyscape
        extension_dir = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../')) #go up to main dir /home/<user>/.config/inkscape/extensions/mightyscape-1.X/
        main_dir = os.path.abspath(os.path.join(extension_dir, '../../')) #go up to main dir /home/<user>/.config/inkscape/extensions/mightyscape-1.X/

        #create some statistics
        totalFolders = 0
        for root, folders, files in os.walk(extension_dir):
            totalFolders += len(folders)                        
            break #prevent descending into subfolders
        
        totalInx = 0
        for root, folders, files in os.walk(extension_dir):
            for file in files:    
                if file.endswith('.inx'):
                    totalInx += 1
        
        inkex.utils.debug("There are {} extension folders with {} .inx files!".format(totalFolders, totalInx))

        repo = Repo(os.path.join(main_dir, ".git"))
        
        #check if it is a non-empty git repository
        if repo.bare is False:
            
            if repo.is_dirty(untracked_files=True) is False:        
                if len(repo.untracked_files) > 0:
                    if self.options.stash_untracked is True:
                        repo.git.stash('save')
                    else:
                        inkex.utils.debug("There are some untracked files in your MightyScape directory. Still trying to pull recent files from git...")
                        
                origin = repo.remotes.origin
                
                ssh_executable = 'git'
                with repo.git.custom_environment(GIT_SSH=ssh_executable):
                    origin.fetch()
                    
                    #hcommit = repo.head.commit
                    #hcommit.diff()   
                    fetch_info = origin.pull() #finally pull new data               
                    for info in fetch_info:
                        inkex.utils.debug("Updated %s to commit id %s" % (info.ref, str(info.commit)[:7]))
                    inkex.utils.debug("Please restart Inkscape to let the changes take effect.")  

            else:
                inkex.utils.debug("Nothing to do! MightyScape is already up to date!")  
                exit(0)     

        else:
            inkex.utils.debug("No \".git\" directory found. Seems your MightyScape was not installed with git clone. Please see documentation on how to do that.")  
            exit(1)

if __name__ == '__main__':
    Upgrade().run()