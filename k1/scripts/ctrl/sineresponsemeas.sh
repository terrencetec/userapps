#!/bin/sh
cd /users/sekiguchi/apps

STAGE="TM"

EXCDOF="L"



tdssine 5 100 K1:VIS-TEST_AUX5_EXC 12 > srm.log &

VAR=(`tdsdmd 5 10 5 K1:VIS-TEST_AUX5_IN1 K1:VIS-TEST_AUX5_OUT`)
echo ${VAR[@]}
echo ${VAR[2]}
echo ${VAR[9]}

