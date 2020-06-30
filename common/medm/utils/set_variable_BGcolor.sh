#!/bin/bash
#*****************************
# Author: K. Okutomi
# Last modified: 2019-09-25
#*****************************

function check(){
    if [ "${1}" = "" ]; then
	echo "Usage: $0 filename"
	exit 1
    fi
}

check ${1} && sed -i '87s/000000/$(BGCOLOR)/g' ${1}
