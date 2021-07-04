#!/usr/bin/python3
#-*- coding: utf-8 -*-

# Simple Inkscape Version 0.1

# The purpose of this Inkscape extension is to provide a easy method to change the interface. 
# The needed .xml and .ui files are provided in the zip file. 
# These filese are moved into the .config/inkscape-simpleinkscape folder on first run.
# There are two option: default and simple.

# This program has been released under the Gnu Public Licence version 2. It is free for everyone to use, copy and change.
# A copy of the GPLv2 licence has added to this program.

import inkex
import shutil
import os
import platform
import subprocess

#profiles = ['default', 'simple', 'lasercutter']
profiles = ['default', 'simple']
#folders  = ['extensions','icons', 'keys', 'palettes', 'templates', 'ui']
folders  = ['ui']

def log (msg =''):  
    inkex.errormsg(msg)
    
def debug (msg=''):
    inkex.errormsg("DEBUG : " + msg)
    pass

class simpleinkscape(inkex.Effect):

    def __init__(self):
        inkex.Effect.__init__(self)
        self.arg_parser.add_argument("--interfaceVersion", type=str)
    
    def effect(self):
        log ('\n***   Simple Inkscape   ***\n')

        # Determine the platform, only continue on linux or windows
        platfrm = platform.system()
        if platfrm == 'Linux':     sep = '/'
        elif platfrm == 'Windows': sep = "\\"
        else: 
            log ('\nError!\n\nThis extension works only on Linux and Windows.\nOther OSes have not been tested and will not work.\n\nExiting.')
            exit()

        interfaceVersion = str(self.options.interfaceVersion).lower()
        log ('Inkscape interface will be switched to : ' + interfaceVersion + '\n')
        
        # Set all folder paths and names
        userfolder = subprocess.run(['inkscape', '--user-data-directory'], capture_output=True, text=True).stdout[0:-1]+sep
        profilefolder = userfolder[:-1] + '-simpleinkscape' + sep        
               
        # Create ProfileFolder and copy profiles from extensions folder on first run.
        if not os.path.isdir (profilefolder): 
            log ('profile folder not existing. Creating it ...')
            os.mkdir(profilefolder)
            
        extension_dir = os.path.abspath(os.path.join(os.path.abspath(os.path.dirname(__file__)))) #go up to main dir /home/<user>/.config/inkscape/extensions/mightyscape-1.X/
        simpleinkscapefolder = extension_dir + sep + 'inkscape-simpleinkscape' + sep
        
        if os.path.isdir(simpleinkscapefolder):
            shutil.copytree(simpleinkscapefolder, profilefolder, dirs_exist_ok=True)

        # Check if profile for chosen interface version exists.
        if os.path.isdir (profilefolder + interfaceVersion) == False:
            log ('Error!\n\nThe chosen profile folder does not exist in ' + profilefolder)
            log ('User interface has not been changed.\n\nExiting.')
            exit()
            
        # Go through list of folders and if they exist in the profile: replace contents
        log ('Installing folders:')
        for folder in folders:
            # Folder exists inside profile?
            if os.path.isdir (profilefolder + interfaceVersion + sep + folder):
                # Delete folder from userfolder and replace by the one in profile
                shutil.rmtree(userfolder + folder, ignore_errors=True)
                os.mkdir(userfolder + folder)
                log ('    ' + userfolder + folder + sep)
                shutil.copytree( profilefolder + interfaceVersion + sep + folder + sep, userfolder+folder+sep, dirs_exist_ok=True)

        log('\nSucces!\n\nThe Inkscape interface has been set to ' + interfaceVersion)
        log('The changes will become visible after restarting inkscape')
        log('\n***   End   ***')
        exit()


if __name__ == "__main__":
    myExt = simpleinkscape()
    myExt.run()

