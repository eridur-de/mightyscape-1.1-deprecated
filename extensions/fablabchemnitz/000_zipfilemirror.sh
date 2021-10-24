#!/bin/bash
clear
   echo "Building extension zip files"
   TARGETDIR="../../../mightyscape-1.X-zipmirror"
   mkdir -p $TARGETDIR > /dev/null 2>&1

for EXTENSION in */; do
    EXTENSION="${EXTENSION%/}" #strip trailing slash
   	EXTRA=""
   	if [[ $EXTENSION == "styles_to_layers" ]] || [[  $EXTENSION == "ungrouper_and_element_migrator_filter" ]]; then
   		EXTRA="${EXTRA} apply_transformations/"
 		 	elif [[ $EXTENSION == "styles_to_layers" ]] || [[  $EXTENSION == "ungrouper_and_element_migrator_filter" ]]; then
 	  		EXTRA="${EXTRA} remove_empty_groups/"
 	  	fi
 	    ZIPFILE=$TARGETDIR/$EXTENSION.zip
   	zip -ru  $ZIPFILE $EXTENSION/ 000_about_fablabchemnitz.svg $EXTRA > /dev/null 2>&1
    echo "--> creating/updating $ZIPFILE"	
   	
   	
done
