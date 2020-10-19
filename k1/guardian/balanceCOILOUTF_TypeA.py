# Script for balancing the coils of MN, IM, TM stages on TypeA
# 17th July 2020, by K. Tanaka
# in reference of /users/Commissioning/scripts/diagonalization/balanceCOILOUTF_TypeA.py by Nakano-san

import numpy as np
from datetime import datetime
import argparse, logging, sys, os
from ezca import Ezca
import foton
import kagralib
import time
import cdsutils
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Function to check the suspension condition
def CheckSuspension(optic,logger):
    # check oplev in range
    warningflag = True
    while not ezca['GRD-VIS_%s_STATE'%optic] == 'TWR_DAMPED':
        if warningflag:
            logger.debug('Guardian is not in TWR_DAMPED. Please request TWR_DAMPED')
            warningflag = False

    warningflag = True
    while any([abs(ezca['VIS-%s_TM_OPLEV_%s_DIAGMON'%(optic,DoF)]) > 50 for DoF in ['YAW','PIT']]) or ezca['VIS-%s_TM_OPLEV_TILT_SUM_OUTPUT'%optic] < 3000:
        if warningflag:
            logger.debug('Oplev is out of range. Please bring it to center by using optic align.')
            warningflag = False

    logger.debug('Oplev value is (p,y) = (%f,%f)'%(ezca['VIS-%s_TM_OPLEV_PIT_DIAGMON'%(optic)],ezca['VIS-%s_TM_OPLEV_YAW_DIAGMON'%(optic)]))

def ShutdownLOCKIN(optic):
    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_CLKGAIN'%optic] = 0
    time.sleep(ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_TRAMP'%optic])
    ezca['VIS-%s_TM_EUL2COIL_1_1'%(optic)] = 1
    ezca['VIS-%s_TM_EUL2COIL_2_1'%(optic)] = 1
    ezca['VIS-%s_TM_EUL2COIL_3_1'%(optic)] = 1
    ezca['VIS-%s_TM_EUL2COIL_4_1'%(optic)] = 1


## Function to check the sign of TM coil output gain
# check the sign of coil output value by comparing the Oplev values before and after DC offset
# When put positve offset in H1 or H4 coil, TM should move in the positive direction of pitch or yaw, considering the location of each coils.
# On the other hand, When put positve offset in H2 or H3 coil, TM should move in the negative direction of pitch or yaw
def SIGN_TM_COILOUT(optic,logger,offTRAMP=10,settleDuration=5,avgDuration=5):
    #return
    logger.debug('--------------Start coil check the sign of %s TM coils------------------'%(optic))
    # Put the same value in GAIN channels of all COILOUTF filters
    default_gain = 0.5
    for ii in ['H1','H2','H3','H4']:
        ezca['VIS-%s_TM_COILOUTF_%s_GAIN'%(optic,ii)] = default_gain
        logger.debug('Put %f in %s_TM_COILOUTF_%s_GAIN'%(default_gain, optic, ii))

    # fetch the oplev values before putting offset
    data_before = cdsutils.getdata(['K1:VIS-%s_TM_OPLEV_PIT_DIAG_DQ'%optic, 'K1:VIS-%s_TM_OPLEV_YAW_DIAG_DQ'%optic], duration = avgDuration)
    pit_before = np.mean(data_before[0].data)
    yaw_before = np.mean(data_before[1].data)

    logger.debug('Oplev value before putting offset:(pitch, yaw) = (%f, %f)'%(pit_before,yaw_before))

    # put the offset in each coils and fetch the oplev value in this time one by one
    default_offset = 20000
    coil_gain = {} # The void dict to put the gains of TM coils
    for ii in ['H1','H2','H3','H4']:
        logger.debug('Put %d cnts as offset in %s TM %s coil, ramp time = %d'%(default_offset, optic, ii, offTRAMP))
        ezca['VIS-%s_TM_COILOUTF_%s_OFFSET'%(optic, ii)] = 0
        coil_offset = ezca.get_LIGOFilter('VIS-%s_TM_COILOUTF_%s'%(optic,ii))
        coil_offset.turn_on('OFFSET')
        coil_offset.ramp_offset(default_offset, ramp_time = offTRAMP, wait=True)
        time.sleep(settleDuration)

        # fetch the oplev values after putting offset
        data_after = cdsutils.getdata(['K1:VIS-%s_TM_OPLEV_PIT_DIAG_DQ'%optic, 'K1:VIS-%s_TM_OPLEV_YAW_DIAG_DQ'%optic], duration = avgDuration)
        pit_after = np.mean(data_after[0].data)
        yaw_after = np.mean(data_after[1].data)

        logger.debug('Oplev value after putting offset in %s : (pitch, yaw) = (%f, %f)'%(ii,pit_after,yaw_after))

        logger.debug('Turn off the offset of %s TM %s coil, ramp time = %d'%(optic, ii, offTRAMP))
        coil_offset.ramp_offset(0, ramp_time = offTRAMP, wait=True)
        coil_offset.turn_off('OFFSET')
        time.sleep(settleDuration)

        compare_pitch = pit_after - pit_before
        compare_yaw   = yaw_after - yaw_before


        # in case of H1
        if ii == 'H1':
            if compare_pitch < 0:
                logger.debug('The sign of %s coil is negative(-)'%(ii))
                coil_gain["%s"%(ii)] = default_gain*(-1.0)

            else:
                logger.debug('The sign of %s coil is positive(+)'%(ii))
                coil_gain["%s"%(ii)] = default_gain

        # in case of H2
        elif ii == 'H2':
            if compare_pitch > 0:
                logger.debug('The sign of %s coil is negative(-)'%(ii))
                coil_gain["%s"%(ii)] = default_gain*(-1.0)

            else:
                logger.debug('The sign of %s coil is positive(+)'%(ii))
                coil_gain["%s"%(ii)] = default_gain

        # in case of H3
        elif ii == 'H3':
            if compare_yaw > 0:
                logger.debug('The sign of %s coil is negative(-)'%(ii))
                coil_gain["%s"%(ii)] = default_gain*(-1.0)

            else:
                logger.debug('The sign of %s coil is positive(+)'%(ii))
                coil_gain["%s"%(ii)] = default_gain

        # in case of H4
        else:
            if compare_yaw < 0:
                logger.debug('The sign of %s coil is negative(-)'%(ii))
                coil_gain["%s"%(ii)] = default_gain*(-1.0)

            else:
                logger.debug('The sign of %s coil is negative(+)'%(ii))
                coil_gain["%s"%(ii)] = default_gain

        ezca['VIS-%s_TM_COILOUTF_%s_GAIN'%(optic,ii)] = coil_gain[ii]
    return coil_gain

def SIGN_MNIM_COILOUT(optic,stage,logger,offTRAMP=10.0,settleDuration=5,avgDuration=5.0):
    logger.debug('--------------Start coil check the sign of %s %s coils------------------'%(optic,stage))


    #return
    #  Turn off OPTIC ALIGN
    if stage=='MN':
        for dof in ['P','Y']:
            if not ezca['VIS-%s_MN_OPTICALIGN_%s_OFFSET'%(optic,dof)] == 0:
                optic_align_offset = ezca.get_LIGOFilter('VIS-%s_MN_OPTICALIGN_%s'%(optic,dof))
                optic_align_offset.ramp_offset(0, ramp_time = 30, wait=True)
                time.sleep(settleDuration)

    # Put the same value in GAIN channels of all COILOUTF filters
    default_gain = 1.0
    for ii in ['V1','V3','V2','H1','H2','H3']:
        ezca['VIS-%s_%s_COILOUTF_%s_GAIN'%(optic,stage,ii)] = default_gain
        logger.debug('Put %f in %s_%s_COILOUTF_%s_GAIN'%(default_gain, optic, stage,ii))

    # fetch the TM oplev values before putting offset
    data_before = cdsutils.getdata(['K1:VIS-%s_TM_OPLEV_PIT_DIAG_DQ'%optic, 'K1:VIS-%s_TM_OPLEV_YAW_DIAG_DQ'%optic, 'K1:VIS-%s_%s_PSDAMP_R_IN1_DQ'%(optic,stage)], duration = avgDuration)
    pit_before = np.mean(data_before[0].data)
    yaw_before = np.mean(data_before[1].data)
    roll_before = np.mean(data_before[2].data)

    logger.debug('%s sensor value before putting offset:(pitch,yaw,roll) = (%f,%f,%f)'%(stage,pit_before,yaw_before,roll_before))

    # put the offset in each coils and fetch the oplev value in this time one by one
    default_offset = [{'H':50,'V': 150},{'H':5000,'V':10000}][stage=='IM']
    coil_gain = {} # The void dict to put the gains of MN coils
    for ii in ['V1','V2','V3','H1','H2','H3']:
        logger.debug('Put %d cnts as offset in %s %s %s coil, ramp time = %d'%(default_offset[ii[0]], optic, stage, ii, offTRAMP))
        ezca['VIS-%s_%s_COILOUTF_%s_OFFSET'%(optic, stage, ii)] = 0
        coil_offset = ezca.get_LIGOFilter('VIS-%s_%s_COILOUTF_%s'%(optic, stage, ii))
        coil_offset.turn_on('OFFSET')
        coil_offset.ramp_offset(default_offset[ii[0]], ramp_time = offTRAMP, wait=True)
        time.sleep(settleDuration)

        # fetch the TM oplev values after putting offset
        data_after = cdsutils.getdata(['K1:VIS-%s_TM_OPLEV_PIT_DIAG_DQ'%optic, 'K1:VIS-%s_TM_OPLEV_YAW_DIAG_DQ'%optic, 'K1:VIS-%s_%s_PSDAMP_R_IN1_DQ'%(optic,stage)], duration = avgDuration)
        pit_after = np.mean(data_after[0].data)
        yaw_after = np.mean(data_after[1].data)
        roll_after = np.mean(data_after[2].data)

        logger.debug('%s sensor value after putting offset in %s : (pitch,yaw,roll) = (%f,%f,%f)'%(stage,ii,pit_after,yaw_after,roll_after))

        logger.debug('Turn off the offset of %s %s %s coil, ramp time = %d'%(optic, stage, ii, offTRAMP))
        coil_offset.ramp_offset(0, ramp_time = offTRAMP, wait=True)
        coil_offset.turn_off('OFFSET')
        time.sleep(settleDuration)

        compare_pitch = pit_after - pit_before
        compare_yaw   = yaw_after - yaw_before
        #compare_trans = trans_after - trans_before
        compare_roll  = roll_after - roll_before

        # in case of V1
        if ii == 'V1':
            if compare_pitch > 0:
                logger.debug('The sign of %s coil is negative(-)'%(ii))
                coil_gain["%s"%(ii)] = default_gain*(-1.0)

            else:
                logger.debug('The sign of %s coil is positive(+)'%(ii))
                coil_gain["%s"%(ii)] = default_gain

        # in case of V2
        if ii == 'V2':
            if compare_roll > 0:
                logger.debug('The sign of %s coil is negative(-)'%(ii))
                coil_gain["%s"%(ii)] = default_gain*(-1.0)

            else:
                logger.debug('The sign of %s coil is positive(+)'%(ii))
                coil_gain["%s"%(ii)] = default_gain

        # in case of V3
        elif ii == 'V3':
            if compare_pitch < 0:
                logger.debug('The sign of %s coil is negative(-)'%(ii))
                coil_gain["%s"%(ii)] = default_gain*(-1.0)

            else:
                logger.debug('The sign of %s coil is positive(+)'%(ii))
                coil_gain["%s"%(ii)] = default_gain

        # in case of H1
        if ii == 'H1':
            if compare_yaw > 0:
                logger.debug('The sign of %s coil is negative(-)'%(ii))
                coil_gain["%s"%(ii)] = default_gain*(-1.0)

            else:
                logger.debug('The sign of %s coil is positive(+)'%(ii))
                coil_gain["%s"%(ii)] = default_gain

        # in case of H2
        elif ii == 'H2':
            if compare_yaw < 0:
                logger.debug('The sign of %s coil is negative(-)'%(ii))
                coil_gain["%s"%(ii)] = default_gain*(-1.0)

            else:
                logger.debug('The sign of %s coil is positive(+)'%(ii))
                coil_gain["%s"%(ii)] = default_gain

        # in case of H3
        elif ii == 'H3':
            if compare_yaw > 0:
                logger.debug('The sign of %s coil is negative(-)'%(ii))
                coil_gain["%s"%(ii)] = default_gain*(-1.0)

            else:
                logger.debug('The sign of %s coil is positive(+)'%(ii))
                coil_gain["%s"%(ii)] = default_gain

        ezca['VIS-%s_%s_COILOUTF_%s_GAIN'%(optic,stage,ii)] = coil_gain[ii]
        time.sleep(settleDuration)
    return coil_gain


#Function for balance the coil
def Balancing(optic,stage,coil,freq,oscAMP,coil_gain,sweeprange,logger,Np=10,avgDuration=10,settleDuration=30,oscTRAMP=10):
    logger.debug('--------------Start coil balancing of %s %s %s------------------'%(optic,stage,coil))
    ezca['VIS-%s_PAY_OLSERVO_LKIN_DEMOD_PHASE'%optic] = 0
    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_SINGAIN'%optic] = 1
    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_COSGAIN'%optic] = 1
    if freq == 'Default':
        freq = default_freq[stage][coil]

    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_FREQ'%optic] = freq
    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_TRAMP'%optic] = oscTRAMP
    I = ezca.get_LIGOFilter('VIS-%s_PAY_OLSERVO_LKIN_DEMOD_I'%optic)
    Q = ezca.get_LIGOFilter('VIS-%s_PAY_OLSERVO_LKIN_DEMOD_Q'%optic)
    I.only_on('INPUT','OUTPUT','DECIMATION')
    Q.only_on('INPUT','OUTPUT','DECIMATION')



    logger.debug('Turn on the filter named %s in DEMOD_I filter bank'%I.Name00.get())
    logger.debug('Turn on the filter named %s in DEMOD_I filter bank'%I.Name01.get())
    I.turn_on('FM1','FM2')

    logger.debug('Turn on the filter named %s in DEMOD_Q filter bank'%Q.Name00.get())
    logger.debug('Turn on the filter named %s in DEMOD_Q filter bank'%Q.Name01.get())
    Q.turn_on('FM1','FM2')
    '''
    # if there is a proper comb filter in I and Q FB, engage it
    for ii in range(10):

        exec('FMnameI = I.Name%s.get()'%str(ii).zfill(2))
        exec('FMnameQ = Q.Name%s.get()'%str(ii).zfill(2))

        if ('comb' in FMnameI) and (str(freq) in FMnameI):
            I.turn_on('FM%d'%(ii+1))
            logger.debug('Turn on the filter named %s in DEMOD_I filter bank'%FMnameI)
        if ('comb' in FMnameQ) and (str(freq) in FMnameQ):
            logger.debug('Turn on the filter named %s in DEMOD_Q filter bank'%FMnameQ)
            Q.turn_on('FM%d'%(ii+1))



    #  Turn off OPTIC ALIGN before starting MN coil balance
    for dof in ['P','Y']:
        optic_align_offset = ezca.get_LIGOFilter('VIS-%s_MN_OPTICALIGN_%s_OFFSET'%(optic,dof))
        #optic_align_offset.turn_on('OFFSET')
        optic_align_offset.ramp_offset(offset = 0, ramp_time = 30, wait=True)
        time.sleep(settleDuration)
    '''
    # if there is a proper notch filter in I and Q , engage it
    fotonfile = '/opt/rtcds/kamioka/k1/chans/K1VIS%sP.txt'%optic
    FB = foton.FilterFile(fotonfile)

    notchI = kagralib.foton_notch(FB, '%s_PAY_OLSERVO_LKIN_DEMOD_I'%optic,1,freq = freq,force=True)
    notchQ = kagralib.foton_notch(FB, '%s_PAY_OLSERVO_LKIN_DEMOD_Q'%optic,1,freq = freq,force=True)
    FB.write()
    ezca['VIS-%s_PAY_OLSERVO_LKIN_DEMOD_I_RSET'%optic] = 1
    ezca['VIS-%s_PAY_OLSERVO_LKIN_DEMOD_Q_RSET'%optic] = 1



    # input and output matrix setting
    actDoF = {'V3':'V','H2':'L','H3':'T','H4':'L'}
    if stage in ['MN','IM']:
        readback = {'V3':'TMP','H2':'TMY','H3':'TMY'}
    else:
        readback = {'H2':'TMP','H4':'TMY'}
    OUTindx = {'BFL':1,'BFT':2,'BFY':3,'MNL':4,'MNT':5,'MNV':6,'MNR':7,'MNP':8,'MNY':9,'IML':10,'IMT':11,'IMV':12,'IMR':13,'IMP':14,'IMY':15,'TML':16,'TMP':17,'TMY':18}
    INindx = {'MNP':1,'MNY':2,'TML':3,'TMP':4,'TMY':5,'ISCL':6,'ISCP':7,'ISCY':8}

    for ii in range(18):
        ezca['VIS-%s_PAY_OLSERVO_PK2EUL_%d_25'%(optic,ii+1)] = 0
    for ii in range(8):
        ezca['VIS-%s_PAY_OLSERVO_OL2PK_25_%d'%(optic,ii+1)] = 0
    ezca['VIS-%s_PAY_OLSERVO_PK2EUL_%d_25'%(optic,OUTindx[stage+actDoF[coil]])] = 1
    ezca['VIS-%s_PAY_OLSERVO_OL2PK_25_%d'%(optic,INindx[readback[coil]])] = 1

    # EULER to SENS matrix setting for TM stage
    if stage == 'TM':
        if coil == 'H2':
            ezca['VIS-%s_TM_EUL2COIL_1_1'%(optic)] = 1
            ezca['VIS-%s_TM_EUL2COIL_2_1'%(optic)] = 1
            ezca['VIS-%s_TM_EUL2COIL_3_1'%(optic)] = 0
            ezca['VIS-%s_TM_EUL2COIL_4_1'%(optic)] = 0
            logger.debug('Turn off the output to H3 and H4 of TM')
        else:
            ezca['VIS-%s_TM_EUL2COIL_1_1'%(optic)] = 0
            ezca['VIS-%s_TM_EUL2COIL_2_1'%(optic)] = 0
            ezca['VIS-%s_TM_EUL2COIL_3_1'%(optic)] = 1
            ezca['VIS-%s_TM_EUL2COIL_4_1'%(optic)] = 1
            logger.debug('Turn off the output to H1 and H2 of TM')

    # turn on excitation.
    logger.debug('Turn on excitation at %f Hz with ramptime of %d.'%(freq,oscTRAMP))
    if oscAMP == 'Default':
        oscAMP = default_amp[coil]
    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_CLKGAIN'%optic] = oscAMP
    logger.debug('Ramping to %f...'%oscAMP)
    time.sleep(oscTRAMP)

    # prepare the measurement
    # decide sweep range
    if coil_gain[coil] < 0:
        sw_range = [max(sweeprange)*(-1.0),min(sweeprange)*(-1.0)]
    else:
        sw_range = sweeprange

    logger.debug('Sweeprange of %s COILOUTF gain is [%f, %f]'%(coil, min(sw_range),max(sw_range)))
    logger.debug('The number of sweep point is %d'%(Np))
    sweepstep = (max(sw_range)-min(sw_range))/((Np-1)*1.)
    gg = np.arange(min(sw_range),max(sw_range),sweepstep) # sweepgain list
    gg = np.append(gg,max(sw_range))

    avgI = [] # Void list to put output of I filter
    avgQ = [] # Void list to put output of Q filter
    stdI = [] # Void list to put standard diviation of output of I filter
    stdQ = [] # Void list to put standard diviation of output of Q filter

    OUTF = ezca.get_LIGOFilter('VIS-%s_%s_COILOUTF_%s'%(optic,stage,coil))
    ii = 0
    for gain in gg:
        ii += 1
        # change gain with ramptime of 5 sec. Wait for the ramping.
        logger.debug('---------------Measurement #%d / %d of %s %s----------------'%(ii,Np,stage,coil))
        logger.debug('COILOUTF gain is ramping to %f'%gain)
        OUTF.ramp_gain(gain,ramp_time=5,wait=True)

        # Check suspension condition
        #CheckSuspension(optic,logger)

        # wait for a while.
        logger.debug('Waiting for %d seconds'%settleDuration)
        time.sleep(settleDuration)

        # fetch the data
        d = cdsutils.getdata(['K1:'+I.filter_name+'_OUT','K1:'+Q.filter_name+'_OUT'],duration=avgDuration)
        avgI.append(np.mean(d[0].data))
        avgQ.append(np.mean(d[1].data))
        stdI.append(np.std(d[0].data))
        stdQ.append(np.std(d[1].data))
        logger.debug('Result: (I, Q) = (%f, %f)'%(avgI[-1],avgQ[-1]))
        logger.debug('Std: (I, Q) = (%f, %f)'%(stdI[-1],stdQ[-1]))
    return gg, avgI, avgQ, stdI, stdQ


if __name__ == '__main__':
    ezca = Ezca()

    # define default frequencies for each optics
    default_freq = {
        'MN':{'V3':5,'H2':4.2,'H3':4.2},
        'IM':{'V3':5,'H2':5,'H3':6},
        'TM':{'H2':5,'H4':5}
    }

    default_amp = {
        'MN':{'V3':3000,'H2':10000,'H3':10000},
        'IM':{'V3':20000,'H2':20000,'H3':20000},
        'TM':{'H2':5000,'H4':5000}
    }

    ## Parse arguments and define constants
    parser=argparse.ArgumentParser(description=
'''Balance the coils with COILOUTF gains of TypeA
e.g. balanceCOILOUTF.py ITMY
     balanceCOILOUTF.py ITMY -f 0.3 -a 1000 -d 10 -r 10 --sr 0.1 1.0''',formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('OPTIC',help='Optic you want to balance the coils (e.g. ITMY)')
    parser.add_argument('-s',dest='STAGE',default='ALL',help='Stage to be balanced (e.g. MN)[default=ALL]')
    parser.add_argument('-c',dest='COIL',default='ALL',help='Coil to be balanced (e.g. V3)[default=ALL]')
    parser.add_argument('-f',dest='FREQ',default='Default',help='Modulation frequency [default=5Hz]')
    parser.add_argument('-a',dest='AMP',default='Default',help='Modulation amplitude [default=5000cnts]')
    parser.add_argument('-d',dest='DURATION',type=float,default=10,help='Duration of each measurement [default=10sec]')
    parser.add_argument('--st',dest='SETTLETIME',type=float,default=5,help='Settle time after changing OUTF gain [default=5sec]')
    parser.add_argument('-t',dest='TEST',default=0,help='0 for real run, 1 for test run which does not update COILOUTF [default=0]')
    parser.add_argument('--sr',dest='SWEEPRANGE',nargs='+',type=float,default=[0.1,1.0],help='Range for OUTF gain sweeping [default=[0.1,1.0]]')
    parser.add_argument('-n',dest='NPOINTS',type=int,default=10,help='Number of point [default=10]')
    args=parser.parse_args()
    optic = args.OPTIC
    freq = args.FREQ

    if args.STAGE == 'ALL':
        stages = [
            # 'MN',
            'IM',
            'TM']
    else:
        if not args.STAGE in ['IM','MN','TM']:
            print('Invalid Stage.')
        stages = [args.STAGE,]

    if args.COIL == 'ALL':
        coils = {
            # 'MN':['V3','H2','H3'],
            'IM':['V3','H2','H3'],
            'TM':['H2','H4']
            }
    else:
        if not args.COIL in ['V3','H2','H3','H4']:
            print('Invalid coil.')
        elif args.COIL in ['V3','H3']:
            stages = ['MN','IM']
            coils = {
                'MN':[args.COIL,],
                'IM':[args.COIL,]
            }
        elif args.COIL == 'H4':
            stages = ['TM']
            coils = {'TM':['H4']}
        else:
            coils = {
            'MN':['H2'],
            'IM':['H2'],
            'TM':['H2']
            }

    oscAMP = (args.AMP)
    sweeprange = (args.SWEEPRANGE)
    Npoints = (args.NPOINTS)
    duration = args.DURATION
    SettleDuration = args.SETTLETIME


    ##### Define logger
    dt_now = datetime.now()
    year = dt_now.year
    month = dt_now.month
    day = dt_now.day
    hour = dt_now.hour
    minute = dt_now.minute

    log_dir = '/users/Commissioning/scripts/diagonalization/log/'
    date_str = '%d%s%s_%s%s'%(year,str(month).zfill(2),str(day).zfill(2),str(hour).zfill(2),str(minute).zfill(2))
    log_file = log_dir + 'archives/balanceCOILOUTF_%s_'%optic + date_str + '.log'

    logger=logging.getLogger('flogger')
    logger.setLevel(logging.DEBUG)
    handler=logging.StreamHandler()
    logger.addHandler(handler)
    handler=logging.FileHandler(filename=log_file)
    logger.addHandler(handler)

    ## open ndscope
    #os.system('ndscope -s K1:VIS-%s_TM_OPLEV_PIT_DIAGMON K1:VIS-%s_TM_OPLEV_YAW_DIAGMON K1:VIS-%s_PAY_OLSERVO_LKIN_DEMOD_I_OUTPUT K1:VIS-%s_PAY_OLSERVO_LKIN_DEMOD_Q_OUTPUT &'%(optic,optic,optic,optic))

    ## result dict

    coil_gain = Signcoiloutgain(optic,logger)

    try:
        for stage in stages:
            for coil in coils[stage]:
                gg,avgI,avgQ,stdI,stdQ = Balancing(optic,stage,coil,freq,oscAMP,coil_gain,sweeprange,logger,Np=Npoints,avgDuration=duration,settleDuration=SettleDuration)

                ## fitting
                pI = np.polyfit(gg,avgI,1)
                pQ = np.polyfit(gg,avgQ,1)
                pGAIN = float(pI[1])/float(pI[0])*(-1) # final gain of the balanced coil

                logger.debug('fitresult with a*gain + b:')
                logger.debug('-I (a,b) = (%f,%f)'%(pI[0],pI[1]))
                logger.debug('-Q (a,b) = (%f,%f)'%(pQ[0],pQ[1]))
                logger.debug('%s GAIN = %f'%(coil,pGAIN))
                logger.debug('balance')
                logger.debug('put %f in VIS-%s_%s_COILOUTF_%s_GAIN'%(pGAIN, optic, stage, coil))
                ezca['VIS-%s_%s_COILOUTF_%s_GAIN'%(optic, stage, coil)] = pGAIN

                ## plot results
                plt.close()
                plt.scatter(gg,avgI,label="I")
                plt.scatter(gg,avgQ,color='red',label="Q")
                plt.plot(gg,np.polyval(pI,gg))
                plt.plot(gg,np.polyval(pQ,gg))
                plt.grid()

                #plt.plot(gg,fitfunc(paramQ[0],paramQ[1],np.array(gg)))
                plt.xlabel('%s_%s_COILOUTF_%s_GAIN'%(optic, stage, coil))
                plt.ylabel('Amplitude of demodulated signal')
                plt.legend()
                plt.savefig(log_dir+'archives/balanceCOILOUTF_%s_'%optic + date_str +'_%s_%s'%(stage, coil)+'.png')
                plt.savefig(log_dir+'balanceCOILOUTF_%s_%s_%s_latest'%(optic, stage, coil)+'.png')


        os.system('cp %s %s'%(log_file,(log_dir+'balanceCOILOUTF_%s_latest.log'%optic)))
        ShutdownLOCKIN(optic)
    except KeyboardInterrupt:
        ## Shut down LOCKIN
        logger.debug('Keyboard Interruption detected! Shutting down...')
        ShutdownLOCKIN(optic)
