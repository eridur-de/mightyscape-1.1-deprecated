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
from datetime import datetime

class AboutUpgradeMightyScape(inkex.EffectExtension):

    def add_arguments(self, pars):
        pars.add_argument("--tab")
        pars.add_argument("--stash_untracked", type=inkex.Boolean, default=False, help="Stash untracked files and continue to upgrade")

    def effect(self):
        warnings.simplefilter('ignore', ResourceWarning) #suppress "enable tracemalloc to get the object allocation traceback"

        try:
            import git
            from git import Repo #requires GitPython lib
        except:
            inkex.utils.debug("Error. GitPython was not installed but is required to run the upgrade process!")
            return

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
        
        inkex.utils.debug("Locally there are {} extension folders with {} .inx files!".format(totalFolders, totalInx))

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
            try:
                latestRemoteCommit = git.cmd.Git().ls_remote("https://gitea.fablabchemnitz.de/FabLab_Chemnitz/mightyscape-1.X.git", heads=True).replace('refs/heads/master','').strip()
                localCommit = str(repo.head.commit)
                #ref_logs = repo.head.reference.log()
                
                #commits = list(repo.iter_commits("master", max_count=5))
                commits = list(repo.iter_commits("master"))
                self.msg("Local commit id is: " + localCommit[:7])
                self.msg("Latest remote commit is: " + latestRemoteCommit[:7])
                self.msg("There are {} remote commits at the moment.".format(len(commits)))
                #self.msg("There are {} remote ref logs at the moment.".format(len(ref_logs)))
                commitList = []
                for commit in commits:
                    commitList.append(commit)
                #commitList.reverse()
                #show last 10 entries
                self.msg("*"*40)
                self.msg("Latest 10 commits are:")
                for i in range(0, 10):
                    self.msg("{} | {} : {}".format(
                        datetime.utcfromtimestamp(commitList[i].committed_date).strftime('%Y-%m-%d %H:%M:%S'),
                        commitList[i].name_rev[:7],
                        commitList[i].message.strip())
                        )   
                    #self.msg(" - {}: {}".format(commitList[i].newhexsha[:7], commitList[i].message))   
                self.msg("*"*40)
    
                if localCommit != latestRemoteCommit:
                    ssh_executable = 'git'
                    with repo.git.custom_environment(GIT_SSH=ssh_executable):
                        origin.fetch()
                          
                        fetch_info = origin.pull() #finally pull new data               
                        for info in fetch_info: #should return only one line in total
                            inkex.utils.debug("Updated %s to commit id %s" % (info.ref, str(info.commit)[:7])) 
                        
                        inkex.utils.debug("Please restart Inkscape to let the changes take effect.")  
    
                else:
                    inkex.utils.debug("Nothing to do! MightyScape is already up to date!")  
                    exit(0)  
                       
            except git.exc.GitCommandError:
                self.msg("Error receiving latest remote commit from git. Are you offline? Cannot continue!")
                return
            
        else:
            inkex.utils.debug("No \".git\" directory found. Seems your MightyScape was not installed with git clone. Please see documentation on how to do that.")  
            exit(1)

if __name__ == '__main__':
    AboutUpgradeMightyScape().run()