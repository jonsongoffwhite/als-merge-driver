#!/bin/bash
mkdir mergetemp
gzip -cd $1 > .merge/mergetemp/base.xml
gzip -cd $2 > .merge/mergetemp/ours.xml
gzip -cd $3 > .merge/mergetemp/theirs.xml

python3 .merge/merge.py .merge/mergetemp/base.xml .merge/mergetemp/ours.xml .merge/mergetemp/theirs.xml .merge/mergetemp/merged.xml
gzip -c .merge/mergetemp/merged.xml > $4

rm -r .merge/mergetemp
