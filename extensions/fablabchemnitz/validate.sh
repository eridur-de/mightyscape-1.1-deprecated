#!/bin/bash

echo "Validating inx files with xmllint. Only errors are printed to console"
for folder in */ ; do xmllint --noout --relaxng ./inkscape.extension.rng $folder*.inx > /dev/null 2>> 000_xmllint.out; done; grep -v "validates\|warning: failed to load external entity" 000_xmllint.out; rm 000_xmllint.out

echo "Count of inx files:"
find ./ -type f -name "*.inx" | wc -l

echo "Count of extension folders:"
ls -d */ | wc -l
