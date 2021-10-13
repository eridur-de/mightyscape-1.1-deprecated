# MightyScape for Inkscape 1.0+

In short: A maintained extension collection for Inkscape 1.0+, working on Windows and Linux. There are **223 extension folders** with **388 .inx files** inside. We also take part at https://inkscape.org/gallery/=extension/ (with single extension uploads).

# About MightyScape

Looking to get more productive we started using some more special Inkscape extensions. We love Inkscape. And we love things like 3d printing, laser cutting, vinyl cutting, pen plotting, maths, physics, geometry, patterns, 2D drawings, 3D CAD , embroidery and more stuff. All this you can do with Inkscape! We recognized that there is no good source to pull extensions in a quick and clean way. Each developer puts his own code on his hidden/unknown repository and often without enough documentation or visible results for common understanding. Many plugins are completely unknown that way, and a lot of extensions are forked x times or are unmaintained. So many of them do not work with recent Inkscape or were never tested with newer versions so far.

# What and why?

This is a one-to-bundle-them-all collection of hundreds of additional functions to Inkscape (extensions) for the new Python 3 based version 1.X including documentation, made  for makers and artists. All plugins where sorted into custom categories  (to avoid overloading the standard extension menu of Inkscape). You can find most of them in sub menu "FabLab Chemnitz". We renamed and cleaned a lot of *.inx files and *.py files. We applied some function renamings, id changes (for preferences.xml clean-keeping), spelling fixes, formattings and parameter corrections.

It took years to search and find all them on the web (so much different possible sources where to find!), to read, to comment (report issues), to fix problems, to test, to document and to provide them online. Many extensions were nearly lost in translation.

At least this repo will help to bring alife some good things and will show hidden gold. It meshes things together in a fresh and bundled way - with ease of use and minimum installation stress. A lot of code is not at the optimum. A mass of bugs has to be fixed and different tools should be improved in usage generally. This package will show errors more quickly. So hopefully a lot of new code fixes is result from this package. Maybe some people help to make all the stuff compatible with Inkscape 1.0 and newer.

# Credits / Help to develop

   * This is not a repository to steal the work of others. The credits go to each developer, maintainer, commiter, issue reporter and so on.
   * All plugins are open source licensed and are fully compatible to be legally inside this repository. This plugin is a fully non-commercial project too
   * All plugins were taken from each git repo's master branch (if git/svn available). There might exist some development branches, fork branches or issue comments which might resolve some issues or enhance functionality of provided plugins. To check for recent github forks use https://techgaun.github.io
   * A lot of plugins were fixed by ourselves in countless hours
   * If you find bugs or have ideas please push them directly to the corresponding root repository of the developer or put it to https://github.com/vmario89/mightyscape-1.X/issues
   * Credits for creation of this big package: Mario Voigt / FabLab Chemnitz

# Used software for development

   * Gitea and Github for hosting this
   * GitEye and SourceTree git frontends for commiting
   * LiClipse and NotePad++ for code
   * regular Python installation (both Linux and Windows)

# Requirements / Tested environment

   * tested with Inkscape
       * Windows portable Version (Inkscape 1.2-dev (25cba68, 2021-05-16)) @ Windows 10
       * Linux dev trunk (https://inkscape.org/de/release/inkscape-master/gnulinux/ubuntu/ppa/dl/) @ Ubuntu 20 LTS
   * tested using Python 3.8.5 64 Bit and 3.9.4 64 Bit
   * some extensions require custom Python installation/modules. See documentation at our FabLab Chemnitz Wiki (see below).
   * some extensions require additional commands, packages or other installers (see documentation too).
   * the structure of this repo is intended the following way: all extensions which require exactly one *.py and one *.inx file are kept on the top level /mightyscape-1.X/extensions/fablabchemnitz. So just copy them to your Inkscape's extension directory. All extension which require additional libraries have their own sub directory. You will find redundancies in this repo like node.exe (NodeJS). We did it this way to give easy possibilty to only pick the extensions you want (instead creating ~200 repositories).

# Remaining ToDos

  * clean code
  * make more precise documentation with more examples
  * check out command line handling of extension. This was totally ignored yet

# Installation, documentation and examples

MightyScape does not work with any releases or feature branches. Just use "git clone" to get the recent commit from master branch.

Please see at https://y.stadtfabrikanten.org/mightyscape-overview for installation tips like required python modules, file locations and other adjustments.

# Donate

<img src="./extensions/fablabchemnitz/000_about_fablabchemnitz.svg">

We are the Stadtfabrikanten, running the FabLab Chemnitz since 2016. A FabLab is an open workshop that gives people access to machines and digital tools like 3D printers, laser cutters and CNC milling machines.

You like our work and want to support us? You can donate to our non-profit organization by different ways:
https://y.stadtfabrikanten.org/donate

**Thanks for using our extension and helping us!**

# Locations

This repo has two remotes:
* https://gitea.fablabchemnitz.de/FabLab_Chemnitz/mightyscape-1.X (root repo origin)
* https://github.com/vmario89/mightyscape-1.X (repo for collaboration. You can create your issues here. Active since May 2021)
