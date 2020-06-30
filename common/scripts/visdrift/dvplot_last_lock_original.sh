#!/usr/bin/env bash

source /ligo/cdscfg/stdsetup.sh

export PYTHONPATH=/home/joseph.betzwieser/pydv:${PYTHONPATH}
/opt/rtcds/userapps/release/sys/common/scripts/dvplot_last_lock.py $*

sleep 100

