#!/usr/bin/env python3

"""
Upgrade MightyScape from Inkscape Extension Dialog. Made for end users

Extension for InkScape 1.X
Author: Mario Voigt / FabLab Chemnitz
Mail: mario.voigt@stadtfabrikanten.org
Date: 14.05.2021
Last patch: 23.06.2021
License: GNU GPL v3

ToDo
    - enable stash option
    - add while loop to list all remoteCommits by jumping from parent to parent
    - add option to create/init .git repo from zip downloaded MightyScape version (to enable upgrader) if no .git dir was found
"""

import inkex
import os
import warnings
from datetime import datetime
try:
    import git
    from git import Repo #requires GitPython lib
except:
    inkex.utils.debug("Error. GitPython was not installed but is required to run the upgrade process!")
    exit(1)

class AboutUpgradeMightyScape(inkex.EffectExtension):

    def update(self, local_repo, remote):
        try:
            localCommit = local_repo.head.commit
            remote_repo = git.remote.Remote(local_repo, 'origin')
            remoteCommit = remote_repo.fetch()[0].commit
            self.msg("Latest remote commit is: " + str(remoteCommit)[:7])

            if localCommit.hexsha != remoteCommit.hexsha:
                ssh_executable = 'git'
                with local_repo.git.custom_environment(GIT_SSH=ssh_executable):
                    origin = local_repo.remotes.origin
                    origin.fetch()
                      
                    fetch_info = origin.pull() #finally pull new data               
                    for info in fetch_info: #should return only one line in total
                        inkex.utils.debug("Updated %s to commit id %s" % (info.ref, str(info.commit)[:7])) 
                    
                    inkex.utils.debug("Please restart Inkscape to let the changes take effect.")  

            else:
                inkex.utils.debug("Nothing to do! MightyScape is already up to date!")  
                   
        except git.exc.GitCommandError as e:
            self.msg("Error: ")
            self.msg(e)
            return False
        return True

   
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
        
        inkex.utils.debug("Locally there are {} extension folders with {} .inx files!\n".format(totalFolders, totalInx))

        gitDir = os.path.join(main_dir, ".git")
        if not os.path.exists(gitDir):
            self.msg("MightyScape .git directory was not found. It seems you installed MightyScape the traditional way (by downloading and extracting from archive). Please install MightyScape using the git clone method if you want to use the upgrade function. More details can be found in the official README.")
            exit(1)
            #Possible option: turn the zip installation into a .git one by cloning over the recent extension dir. could be added as ugprader option.
        
        local_repo = Repo(gitDir)
        #check if it is a non-empty git repository
        if local_repo.bare is False:
            if local_repo.is_dirty(untracked_files=True) is False:        
                if len(local_repo.untracked_files) > 0:
                    if self.options.stash_untracked is True:
                        local_repo.git.stash('save')
                    else:
                        inkex.utils.debug("There are some untracked files in your MightyScape directory. Still trying to pull recent files from git...")
              
            remotes = []
            remotes.append("https://gitea.fablabchemnitz.de/FabLab_Chemnitz/mightyscape-1.X.git") #main
            remotes.append("https://github.com/vmario89/mightyscape-1.X.git") #copy/second remote
            
            localLatestCommit = local_repo.head.commit
            localCommits = list(local_repo.iter_commits("master", max_count=10, skip=0))
            self.msg("Local commit id is: " + str(localLatestCommit)[:7])
            self.msg("There are {} local commits at the moment.".format(len(localCommits)))
            localCommitList = []
            for localCommit in localCommits:
                localCommitList.append(localCommit)
            #localCommitList.reverse()
            self.msg("*"*40)
            self.msg("Latest local commits are:")
            for i in range(0, 10):
                self.msg("{} | {} : {}".format(
                    datetime.utcfromtimestamp(localCommitList[i].committed_date).strftime('%Y-%m-%d %H:%M:%S'),
                    localCommitList[i].name_rev[:7],
                    localCommitList[i].message.strip())
                    )   
                #self.msg(" - {}: {}".format(localCommitList[i].newhexsha[:7], localCommitList[i].message))   
            self.msg("*"*40)
            
            #finally run the update
            success = self.update(local_repo, remotes[0])
            if success is False: #try the second remote if first failed
                self.msg("Error receiving latest remote commit from main git remote {}. Trying second remote ...".format(remotes[0]))
                success = self.update(local_repo, remotes[1])
            if success is False: #if still false:
                self.msg("Error receiving latest remote commit from second git remote {}.\nAre you offline? Cannot continue!".format(remotes[0]))
                exit(1)
        
        else:
            inkex.utils.debug("No \".git\" directory found. Seems your MightyScape was not installed with git clone. Please see documentation on how to do that.")  
            exit(1)

if __name__ == '__main__':
    AboutUpgradeMightyScape().run()