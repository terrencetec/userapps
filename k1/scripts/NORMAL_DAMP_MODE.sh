#!/bin/bash
# Changes matrix elements in the IP_DAMPMODE cdsMultMatrix block
# to enable normal damping mode. Takes an optic name as command line argument.

caput K1:VIS-$1_IP_DAMPMODE_SETTING_1_1 1
caput K1:VIS-$1_IP_DAMPMODE_SETTING_2_2 1
caput K1:VIS-$1_IP_DAMPMODE_SETTING_3_3 1
caput K1:VIS-$1_IP_DAMPMODE_SETTING_1_4 0
caput K1:VIS-$1_IP_DAMPMODE_SETTING_2_5 0
caput K1:VIS-$1_IP_DAMPMODE_SETTING_3_6 0
caput K1:VIS-$1_IP_DAMPMODE_LOAD_MATRIX 1

