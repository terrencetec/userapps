#!/usr/bin/env python3
#! coding:utf-8
import os
import sys
import time
import subprocess
from datetime import datetime
import threading
from epics import caget, caput, cainfo

picodriverDict = {
    "MCE"      :"10.68.150.22",
    "MCI"      :"10.68.150.3",
    "MCO"      :"10.68.150.4",
    "STM1"     :"10.68.150.5",
    "STM2"     :"10.68.150.6",
    "POM1"     :"10.68.150.7",
    "IMMT1"    :"10.68.150.14",
    "IMMT2"    :"10.68.150.13",
    "PR2_BF"   :"10.68.150.12",
    "PR2_IM"   :"10.68.150.15",
    "PR3_BF"   :"10.68.150.10",
    "PR3_IM"   :"10.68.150.11",
    "PRM_BF"   :"10.68.150.8",
    "PRM_IM"   :"10.68.150.9",
    "BS_IM"    :"10.68.150.16",
    "BS_BF"    :"10.68.150.17",
    "ETMX"      :"10.68.150.20",
    "ETMY"      :"10.68.150.21",
    "ITMX"      :"10.68.150.18",
    "ITMY"      :"10.68.150.19",
    "SR2_IM"   :"10.68.150.24",
    "SR2_BF"   :"10.68.150.25",
    "SR3_IM"   :"10.68.150.26",
    "SR3_BF"   :"10.68.150.27",
    "SRM_IM"   :"10.68.150.32",
    "SRM_BF"   :"10.68.150.23",
#    "TEST"   :"10.68.150.22",    
    "POP_POM"   :"10.68.150.31",
    "POS_POM"   :"10.68.150.34",
    "PCAL_EX1"   :"10.68.150.35",
    "PCAL_EX2"   :"10.68.150.36",
    "PCAL_EY1"   :"10.68.150.37",
    "PCAL_EY2"   :"10.68.150.38",
    "OMMT1"   :"10.68.150.71",
    "OMMT2"   :"10.68.150.72",
    "OSTM"   :"10.68.150.73",
    "AS_WFS"   :"10.68.150.74",
    "REFL_WFS" :"10.68.150.75",
    "TEST" :"10.68.150.28",
}
stepperdriverDict = {
    "PR2_GAS"   :["10.68.150.40",'K1:VIS-PR2_BO_ENCODE_STEP_GAS_SW'],
    "PR0_GAS"   :["10.68.150.41",'K1:VIS-PR0_BO_ENCODE_STEP_GAS_SW'],
    "ITMX_GAS"  :["10.68.150.43",'K1:VIS-ITMX_BO_ENCODE_STEP_GAS_SW'],
    "ITMX_IP"   :["10.68.150.44",'K1:VIS-ITMX_BO_ENCODE_STEP_IP_SW'],
    "ETMX_GAS"  :["10.68.150.45",'K1:VIS-ETMX_BO_ENCODE_STEP_GAS_SW'],
    "ETMX_IP"   :["10.68.150.46",'K1:VIS-ETMX_BO_ENCODE_STEP_IP_SW'],
    "ITMY_GAS"  :["10.68.150.47",'K1:VIS-ITMY_BO_ENCODE_STEP_GAS_SW'],
    "ITMY_IP"   :["10.68.150.48",'K1:VIS-ITMY_BO_ENCODE_STEP_IP_SW'],
    "ETMY_GAS"  :["10.68.150.49",'K1:VIS-ETMY_BO_ENCODE_STEP_GAS_SW'],
    "ETMY_IP"   :["10.68.150.50",'K1:VIS-ETMY_BO_ENCODE_STEP_IP_SW'],
    "BS_GAS"    :["10.68.150.51",'K1:VIS-BS_BIO_ENCODE_STEP_GAS_SW'],
    "BS_IP"     :["10.68.150.52",'K1:VIS-BS_BIO_ENCODE_STEP_IP_SW'],
    "SR2_GAS"   :["10.68.150.53",'K1:VIS-SR2_BIO_ENCODE_STEP_GAS_SW'],
    "SR2_IP"    :["10.68.150.54",'K1:VIS-SR2_BIO_ENCODE_STEP_IP_SW'],
    "SR3_GAS"   :["10.68.150.55",'K1:VIS-SR3_BIO_ENCODE_STEP_GAS_SW'],
    "SR3_IP"    :["10.68.150.56",'K1:VIS-SR3_BIO_ENCODE_STEP_IP_SW'],
    "SRM_GAS"   :["10.68.150.57",'K1:VIS-SRM_BIO_ENCODE_STEP_GAS_SW'],
    "SRM_IP"    :["10.68.150.58",'K1:VIS-SRM_BIO_ENCODE_STEP_IP_SW'],
    # for Testing.
#    "TEST_GAS"  :"10.68.150.63",
#    "TESTSR_IP" :"10.68.150.63"
}

#os.system("clear")
before_status = {}
display_out = ""

def ping_test(prefix,stage,ipaddr,bioonoff):
    global display_out
    print(stage,bioonoff)
    d = datetime.now()
    result = subprocess.Popen(['ping','-c 1','-w 5',ipaddr], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    out, error = result.communicate()
    #print('out:',out)
    #print('error:',error)

    read_flag = False
    for line_str in out.decode().splitlines():
        if  'statistics' in line_str:
            read_flag = True
            continue
        if read_flag == True:
            read_flag = False
            datas = line_str.split(',')
            transmit_packet = 0
            recive_packet = 0
            packet_loss = 0
            #print(datas)
            for data in datas:
                if 'packets transmitted' in data:
                    count = data.strip().split(' ')
                    transmit_packet = int(count[0])
                elif 'received' in data:
                    count = data.strip().split(' ')
                    recive_packet = int(count[0])
                elif 'packet loss' in data:
                    count = data.strip().split('%')
                    packet_loss = float(count[0])

            status = True if packet_loss == 0 else False
            check_flag = False
            if stage in before_status:
                if  before_status[stage] != status:
                    check_flag = True
            before_status[stage] =status
            if packet_loss == 0:
                result_str = d.strftime('%Y-%m-%d %H:%M:%S') + ', ' + stage + ', OK, ' + str(transmit_packet) + ', ' + str(recive_packet) + ', ' + str(check_flag) 
            else:
                result_str = d.strftime('%Y-%m-%d %H:%M:%S') + ', ' + stage + ', NG, ' + str(transmit_packet) + ', ' + str(recive_packet) + ', ' + str(check_flag)
            if bioonoff != '':
                result_str = result_str + ', ' + bioonoff
            logfile = '/kagra/Dropbox/Subsystems/VIS/Scripts/PingTest/LogFiles/Motors/'+prefix+stage+'.log'
            #print(result_str)
            with open(logfile,'a') as f:
                f.write(result_str +'\n')


            # All Result
            if 'Off' in bioonoff:
                if packet_loss == 0:
                    result_str = d.strftime('%Y-%m-%d %H:%M:%S') + ', ' + stage + ', ' + bioonoff + ', NG, '
                else:
                    result_str = d.strftime('%Y-%m-%d %H:%M:%S') + ', ' + stage + ', ' + bioonoff + ', OK, '
            elif 'On' in bioonoff:
                if packet_loss == 100:
                    result_str = d.strftime('%Y-%m-%d %H:%M:%S') + ', ' + stage + ', ' + bioonoff + ', NG '
                else:
                    result_str = d.strftime('%Y-%m-%d %H:%M:%S') + ', ' + stage + ', ' + bioonoff + ', OK, '
            else:
                if packet_loss == 0:
                    result_str = d.strftime('%Y-%m-%d %H:%M:%S') + ', ' + stage + ', OK '
                else:
                    result_str = d.strftime('%Y-%m-%d %H:%M:%S') + ', ' + stage + ', NG, '

            logfile = '/kagra/Dropbox/Subsystems/VIS/Scripts/PingTest/LogFiles/Motors/ping_motors.log'
            with open(logfile,'a') as f:
                f.write(result_str +'\n')
            display_out += result_str + '\n'
                
global_count = 0

def thread_ping_pico(prefix,stage,ipaddr):
    count = 0    
    while True:
        if count == global_count:
            if count > 0:
                ping_test(prefix,stage,ipaddr,'')


            count = count + 1

def thread_ping_step(prefix,stage,ipaddr,bio):
    count = 0    
    while True:
        if count == global_count:
            if count > 0:
                #print(bio,prefix,stage,ipaddr)
                #before = caget(bio)
                #caput(bio,0)
                time.sleep(1.0)
                ping_test(prefix,stage,ipaddr,'Bio:Off')
                #caput(bio,1)
                time.sleep(1.0)
                ping_test(prefix,stage,ipaddr,'Bio:On')
                #caput(bio,before)


            count = count + 1

def ping_step(prefix,stage,ipaddr,bio):

    flg = True
    while flg:
        before = caget(bio)
        if before != None:
            flg = False
        else:
            print('Retry caget')
    
    #print(bio,prefix,stage,ipaddr,before)

    caput(bio,0)
    time.sleep(1.0)
    ping_test(prefix,stage,ipaddr,'Bio:Off')

    caput(bio,1)
    time.sleep(5.0)
    ping_test(prefix,stage,ipaddr,'Bio:On')
    caput(bio,before)


def main():

    for stage, ipaddr in picodriverDict.items():
        thread = threading.Thread(target=thread_ping_pico, args=('PICO_', stage, ipaddr) )
        thread.setDaemon(True)
        thread.start()


#    for stage, data in stepperdriverDict.items():
#        ipaddr = data[0]
#        bio = data[1]
#        thread_ping_test('STEP_',stage,ipaddr,bio)
#        thread = threading.Thread(target=thread_ping_step, args=('STEP_', stage, ipaddr, bio) )
#        thread.start()


if __name__ == "__main__":

    print('-- init --')
    main()
#    time.sleep(120)


    print('-- starting --')
    global_count = global_count + 1

    for stage, data in stepperdriverDict.items():
        ipaddr = data[0]
        bio = data[1]
        ping_step('STEP_',stage,ipaddr,bio)
    
    print('-- Completed --')
    print(display_out)
    sys.exit()
