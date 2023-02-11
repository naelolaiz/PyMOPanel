#!/bin/bash
convert ${1} -coalesce tmp.gif
convert tmp.gif -resize 192x64 resized_${1}
rm tmp.gif
