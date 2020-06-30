#!/bin/bash
today=$(date '+%m%d')
year=$(date '+%Y')
now=$(date '+%H%M')

if [ ! -d /users/VISsvn/Commissioning/$2/Measurements/${year} ]; then
    mkdir /users/VISsvn/Commissioning/$2/Measurements/${year}
fi
if [ ! -d /users/VISsvn/Commissioning/$2/Measurements/${year}/${today} ]; then
    mkdir /users/VISsvn/Commissioning/$2/Measurements/${year}/${today}
fi
if [ ! -d /users/VISsvn/Commissioning/$2/Measurements/${year}/${today}/temp ]; then
    mkdir /users/VISsvn/Commissioning/$2/Measurements/${year}/${today}/temp
fi
if [ ! -e /users/VISsvn/Commissioning/$2/Measurements/${year}/${today}/temp/$2_$1_${now}.xml ]; then
    cp /users/VISsvn/Commissioning/$2/Templates/$2_$1.xml /users/VISsvn/Commissioning/$2/Measurements/${year}/${today}/temp/$2_$1_${now}.xml
fi
cd /users/VISsvn/Commissioning/$2/Measurements/${year}/${today}
diaggui /users/VISsvn/Commissioning/$2/Measurements/${year}/${today}/temp/$2_$1_${now}.xml &


