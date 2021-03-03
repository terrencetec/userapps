#!/bin/bash
'''
Replace $(macro) in the  yaml file with a strings.
'''
echo Launch NDSCOPE
if test $# -lt 2 ; then
    echo launch_ndscope file.yml optics=ITMX vacoptics=X_IXA
    exit
fi

yamlfile=$1
tempfile=$(mktemp file-XXX.yml)
trap 'rm -v "$tempfile"' EXIT

replace=

for arg in $@; do
    if [ `echo $arg | grep '.yml'` ] ; then
        echo Input file: $yamlfile
    else
        ARGS=(${arg//=/ })
        replace=$replace" -e s/\$(${ARGS[0]})/${ARGS[1]}/g"
    fi
done

cat $yamlfile | sed $replace > $tempfile
ndscope $tempfile 
