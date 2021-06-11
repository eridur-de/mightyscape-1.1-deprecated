#!/bin/bash
echo "Validating inx files with xmllint. Only errors are printed to console"
for folder in */ ; do xmllint --noout --relaxng ./inkscape.extension.rng $folder*.inx > /dev/null 2>> 000_xmllint.out; done; grep -v "validates\|warning: failed to load external entity" 000_xmllint.out; rm 000_xmllint.out


echo "Count of inx files:"
find ./ -type f -name "*.inx" | wc -l


echo "Count of extension folders:"
ls -d */ | wc -l


echo "Removing unrequired pyc cache files"
find . -type d -name "__pycache__" -exec rm -rf {} \;


echo "Building Inkscape gallery extension zip files"
TARGETDIR="../000_Inkscape_Gallery"
mkdir -p $TARGETDIR > /dev/null

#list of extensions which are uploaded at Inkscape gallery by us at the moment
for EXTENSION in                            \
	"animate_order"                         \
	"cleanup_styles"                        \
	"contour_scanner_and_trimmer"           \
	"convert_to_polylines"                  \
	"create_links"                          \
	"dxf2papercraft"                        \
	"dxf_dwg_importer"                      \
	"imagetracerjs"                         \
	"inventory_sticker"                     \
	"move_path_node"                        \
	"remove_empty_groups"                   \
    "offset_paths"                          \
	"papercraft_unfold"                     \
	"paperfold"                             \
	"primitive"                             \
	"slic3r_stl_input"                      \
	"split_and_break_bezier_at_t"           \
	"styles_to_layers"                      \
	"ungrouper_and_element_migrator_filter" \
	"unwind_paths"                          \
	"vpypetools"
do
	EXTRA=""
	if [[ $EXTENSION == "styles_to_layers" ]] || [[  $EXTENSION == "ungrouper_and_element_migrator_filter" ]]; then
		EXTRA="${EXTRA} apply_transformations/"
	elif [[ $EXTENSION == "styles_to_layers" ]] || [[  $EXTENSION == "ungrouper_and_element_migrator_filter" ]]; then
		EXTRA="${EXTRA} remove_empty_groups/"
	fi
    ZIPFILE=$TARGETDIR/$EXTENSION.zip
	rm $ZIPFILE > /dev/null
	zip -r  $ZIPFILE $EXTENSION/ 000_about_fablabchemnitz.svg $EXTRA
done
