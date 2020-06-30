#!/bin/bash
#******************************************#
#     File Name: analog_wd_reset.sh
#        Author: Takahiro Yamamoto
# Last Modified: 2019/11/20 01:30:27
#******************************************#

MASTER=/opt/rtcds/kamioka/k1/target/fb/master

function reset(){
    caput $1 1
    sleep 0.5
    caput $1 0
}

for mdl in `grep '.ini$' ${MASTER} | grep -v '^#'`
do
    for ch in `grep _WD_ ${mdl} | grep _BIO_ | tr -d '[' | tr -d ']'`
    do
	reset $ch &
    done
done
wait 
sleep 2
