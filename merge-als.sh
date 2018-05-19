#!/bin/bash
mkdir mergetemp
gzip -cd $1 > mergetemp/base.xml
gzip -cd $2 > mergetemp/ours.xml
gzip -cd $3 > mergetemp/theirs.xml

python3 merge.py mergetemp/base.xml mergetemp/ours.xml mergetemp/theirs.xml mergetemp/merged.xml
gzip -c mergetemp/merged.xml > $4

rm -r mergetemp
