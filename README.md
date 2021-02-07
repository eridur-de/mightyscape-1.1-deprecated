# MightyScape for InkScape 1.0 / 1.1dev

Looking to get more productive i started using some more special InkScape extensions. I love InkScape. And i love things like 3d printing, laser cutting, vinyl cutting, pen plotting, maths, physics, geometry, patterns, 2D drawings, 3D CAD and so on. I am also interested to learn embroidery and more stuff. All this you can do with InkScape! After years i recognized that there is no good source to pull extensions in a quick and clean way. Each developer puts his own code on his hidden/unknown repository and often without enough documentation or visible results for understanding. Many plugins are completely unknown and a lot of extensions are forked x times or are unmaintained. So many of them do not work with recent InkScape or were never tested with newer versions so far.

# What and why?

This is a one-to-bundle-them-all collection of hundreds of additional functions to InkScape (extensions) for the new Python 3 based version 1.X including documentation. All plugins where sorted into custom categories  (to avoid overloading the standard extension menu of InkScape). You can find most of them in sub menu "FabLab Chemnitz". I renamed and cleaned a lot of *.inx files and *.py files. I applied some function renamings, id changes (for preferences.xml clean-keeping), spelling fixes, formattings and parameter corrections.

I stopped counting the extensions. It took many weeks to search and find all them on the web (so much different possible sources where to find!), to read, to comment (report issues), to fix problems, to test, to document and to provide them online. Many extensions were lost in translation / really really hidden.

At least this repo will help to bring alife some good things from the past and will show hidden gold. It meshes things together in a fresh and bundled way - with ease of use and minimum installation stress. A lot of code is not at the optimum. A mass of bugs has to be fixed and different tools should be improved in usage generally. This package will show errors more quickly. So hopefully a lot of new code fixes is result from this package. Maybe some people help to make all the stuff compatible with InkScape 1.0 and newer.

I think this package is ideal for makers who are travelling around and/or using a lot of different machines at different locations.

# Credits / Help to develop

   * This is not a repository to steal the work of others. The credits go to each developer, maintainer, commiter, issue reporter and so on.
   * All plugins are open source licensed and are fully compatible to be legally inside this repository. This plugin is a fully non-commercial project too
   * All plugins were taken from each git repo's master branch (if git/svn available). There might exist some development branches, fork branches or issue comments which might resolve some issues or enhance functionality of provided plugins. I did not find them all maybe. To check for recent github forks i use https://techgaun.github.io
   * A lot of plugins were fixed by myself in countless hours
   * If you find bugs or have ideas please push them directly to the corresponding root repository of the developer like i did
   * Credits for creation of this big package: me (Mario Voigt)

# Requirements / Tested environment

   * tested with InkScape
       * Windows portable Version (1.1dev 2020-07-27) @ Windows 10
       * Linux dev trunk (https://inkscape.org/de/release/inkscape-master/gnulinux/ubuntu/ppa/dl/) @ Ubuntu 20 LTS
   * tested using Python 3.8.5 64 Bit
   * some extensions require custom Python installation/modules. So i provide a description on how to do this (see documentation at our FabLab Chemnitz Wiki (see below)).
   * some extensions require additional commands, packages or other installers (see documentation too).
   * the structure of this repo is intended the following way: all extensions which require exactly one *.py and one *.inx file are kept on the top level /mightyscape-1.X/extensions/fablabchemnitz. So just copy them to your InkScape's extension directory. All extension which require additional libraries have their own sub directory. You will find redundancies in this repo like node.exe (NodeJS). I did it this way to give easy possibilty to only pick the extensions you want (i dont want to make about 200 repositories).

# Remaining ToDos

  * clean code
  * make more precise documentation with more examples
  * remove deprecation warnings
  * check out command line handling of extension. This was totally ignored yet

# Documentation and examples
Please see at https://fablabchemnitz.de/pages/viewpage.action?pageId=73040380
