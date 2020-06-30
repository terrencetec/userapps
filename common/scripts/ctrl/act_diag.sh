#!/bin/sh
# actuator diagonalzation
# $1=frequency, $2=amplitude, $3=cycle, $4=avarage


# CHANGE DIRECTORY
cd /users/sekiguchi/apps

# INITIAL SETTING
# select stage from TM, IM and F0
STAGE=TM
# DoF
ALLDOF=(L P Y)
# excitation frequency
EXCFREQ=${1:-0.1}
# excitation amplitude
EXCAMP=${2:-50}
# cycle number
EXCCYC=${3:-10}
# agerage
EXCAVG=${4:-5}
# excitation time
EXCTIME=`echo "scale=2; $EXCCYC / $EXCFREQ * $EXCAVG + 1" | bc`
# observation channel
for OBSDOF in ${ALLDOF[@]}
do
    OBSCH+=("K1:VIS-PROTO_${STAGE}_SERVOF_${OBSDOF}_IN1")
done

# WRITE SETUP TO FILE
DATED=(`date`)
echo "Start time: "${DATED[@]} > diag_setup_${STAGE}.dat
echo "Exc freq: "${EXCFREQ} >> diag_setup_${STAGE}.dat
echo "Exc amp: "${EXCAMP} >> diag_setup_${STAGE}.dat
echo "Cycle: "${EXCCYC} >> diag_setup_${STAGE}.dat
echo "Avg:"${EXCAVG} >> diag_setup_${STAGE}.dat

# RESET FILES
: > diag_amplitude_${STAGE}.dat
: > diag_coherence_${STAGE}.dat
: > diag_phase_${STAGE}.dat

# EXCITATION START
for EXCDOF in ${ALLDOF[@]}
do
    EXCCH=K1:VIS-PROTO_${STAGE}_TEST_${EXCDOF}_EXC
    OBSCH1=($EXCCH ${OBSCH[@]})
    tdssine ${EXCFREQ} ${EXCAMP} ${EXCCH} ${EXCTIME} &
    RAWDATA=(`tdsdmd ${EXCFREQ} ${EXCCYC} ${EXCAVG} ${OBSCH1[@]}`)
    DATA=()
    COHR=()
    PHSE=()
    for (( dum = 0;  dum <= ${#ALLDOF[@]} ; dum++ ))
    do
     	dum2=`echo "scale=0; $dum * 7 + 1" | bc`
	dum3=`echo "scale=0; $dum * 7 + 0" | bc`
	dum4=`echo "scale=0; $dum * 7 + 2" | bc`
	DATA+=(${RAWDATA[$dum2]})
	COHR+=(${RAWDATA[$dum3]})
	PHSE+=(${RAWDATA[$dum4]})
    done
    echo 'EXC CHANNEL: '$EXCDOF
    echo 'AMPLITUDE: '${DATA[@]}
    echo 'COHERENCE: '${COHR[@]}
    echo 'PHASE: '${PHSE[@]}
    echo ${DATA[@]} >> diag_amplitude_${STAGE}.dat
    echo ${COHR[@]} >> diag_coherence_${STAGE}.dat
    echo ${PHSE[@]} >> diag_phase_${STAGE}.dat
    sleep 3
done

# VAR=(`tdsdmd 5 10 5 K1:VIS-TEST_AUX5_IN1 K1:VIS-TEST_AUX5_OUT`)
# echo ${VAR[@]}
# echo ${VAR[2]}
# echo ${VAR[9]}

