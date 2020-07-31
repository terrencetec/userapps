# Script for balancing the coils of TypeA TM
# 16th July 2020, by K. Tanaka
# in reference of /users/Commissioning/scripts/diagonalization/balanceCOILOUTF_TypeA.py by Nakano-san

import numpy as np
from datetime import datetime
import argparse, logging, sys, os
from ezca import Ezca
import time
import cdsutils
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Function to check the suspension condition
def CheckSuspension(optic):
    # check oplev in range
    warningflag = True
    while not ezca['GRD-VIS_%s_STATE'%optic] == 'TWR_DAMPED':
        if warningflag:
            #logger.debug('Guardian is not in TWR_DAMPED. Please request TWR_DAMPED')
            warningflag = False

    warningflag = True
    while any([abs(ezca['VIS-%s_TM_OPLEV_%s_DIAGMON'%(optic,DoF)]) > 50 for DoF in ['YAW','PIT']]) or ezca['VIS-%s_TM_OPLEV_TILT_SUM_OUTPUT'%optic] < 3000:
        if warningflag:
            #logger.debug('Oplev is out of range. Please bring it to center by using optic align.')
            warningflag = False

    #logger.debug('Oplev value is (p,y) = (%f,%f)'%(ezca['VIS-%s_TM_OPLEV_PIT_DIAGMON'%(optic)],ezca['VIS-%s_TM_OPLEV_YAW_DIAGMON'%(optic)]))

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
# On the other hand, When put positve offset in H2 or H3 coil, TM should move in the negative direction of pitch or yaw.

def Signcoiloutgain(optic,offTRAMP=10,settleDuration=5,avgDuration=10):
    #logger.debug('--------------Start coil checkin the of %s TM coils------------------'%(optic))
    # Put the same value in GAIN channels of all TM_COILOUTF filters
    default_gain = 0.5
    for ii in range(4):
        ezca['VIS-%s_TM_COILOUTF_H%d_GAIN'%(optic,ii+1)] = default_gain
        #logger.debug('Put %f in %s_TM_COILOUTF_H%d_GAIN'%(default_gain, optic, ii+1))
        
    # fetch the oplev values before putting offset
    
    data_before = cdsutils.getdata(['K1:VIS-%s_TM_OPLEV_PIT_DIAG_DQ'%optic, 'K1:VIS-%s_TM_OPLEV_YAW_DIAG_DQ'%optic], duration = avgDuration)
    pit_before = np.mean(data_before[0].data)
    yaw_before = np.mean(data_before[1].data)
    
    #logger.debug('Oplev value before putting offset:(pitch, yaw) = (%f, %f)'%(pit_before,yaw_before))
    
    # put the offset in each coils and fetch the oplev value in this time one by one
    default_offset = 10000
    coil_gain = {} # The void dict to put the gains of TM coils 
    for ii in range(4):
        #logger.debug('Put %d cnts as offset in %s TM H%d coil, ramp time = %d'%(default_offset, optic, ii+1, offTRAMP))
        coil_offset = ezca.get_LIGOFilter('VIS-%s_TM_COILOUTF_H%d'%(optic,ii+1))
        coil_offset.turn_on('OFFSET')
        coil_offset.ramp_offset(default_offset, ramp_time = offTRAMP, wait=True)
        time.sleep(settleDuration)

        # fetch the oplev values after putting offset
        data_after = cdsutils.getdata(['K1:VIS-%s_TM_OPLEV_PIT_DIAG_DQ'%optic, 'K1:VIS-%s_TM_OPLEV_YAW_DIAG_DQ'%optic], duration = avgDuration)
        pit_after = np.mean(data_after[0].data)
        yaw_after = np.mean(data_after[1].data)
        
        #logger.debug('Oplev value after putting offset in H%d : (pitch, yaw) = (%f, %f)'%(ii+1,pit_after,yaw_after))

        #logger.debug('Turn off the offset of %s TM H%d coil, ramp time = %d'%(optic, ii+1, offTRAMP))
        coil_offset.ramp_offset(0, ramp_time = offTRAMP, wait=True)
        coil_offset.turn_off('OFFSET')
        time.sleep(settleDuration)
        
        compare_pitch = pit_after - pit_before
        compare_yaw   = yaw_after - yaw_before


        # in case of H1
        if ii == 0:
            if compare_pitch < 0:
                #logger.debug('The sign of H%d coil is negative(-)'%(ii+1))
                coil_gain["H%d"%(ii+1)] = default_gain*(-1.0)
                
            else:
                #logger.debug('The sign of H%d coil is positive(+)'%(ii+1))
                coil_gain["H%d"%(ii+1)] = default_gain
                
        # in case of H2
        elif ii == 1:
            if compare_pitch > 0:
                #logger.debug('The sign of H%d coil is negative(-)'%(ii+1))
                coil_gain["H%d"%(ii+1)] = default_gain*(-1.0)
                
            else:
                #logger.debug('The sign of H%d coil is positive(+)'%(ii+1))
                coil_gain["H%d"%(ii+1)] = default_gain
                
        # in case of H3
        elif ii == 2:
            if compare_yaw > 0:
                #logger.debug('The sign of H%d coil is negative(-)'%(ii+1))
                coil_gain["H%d"%(ii+1)] = default_gain*(-1.0)
                
            else:
                #logger.debug('The sign of H%d coil is positive(+)'%(ii+1))
                coil_gain["H%d"%(ii+1)] = default_gain
                
        # in case of H4
        else:
            if compare_yaw < 0:
                #logger.debug('The sign of H%d coil is negative(-)'%(ii+1))
                coil_gain["H%d"%(ii+1)] = default_gain*(-1.0)
                
            else:
                #logger.debug('The sign of H%d coil is negative(+)'%(ii+1))
                coil_gain["H%d"%(ii+1)] = default_gain*(-1.0)
                
        print coil_gain
        ezca['VIS-%s_TM_COILOUTF_H%d_GAIN'%(optic,ii+1)] = coil_gain["H%d"%(ii+1)]
        

    return coil_gain
        
#Function for balance the coil
def Balancing(optic,coil,freq,oscAMP,coil_gain,sweeprange,logger,Np=10,avgDuration=10,settleDuration=5,oscTRAMP=10):
    #logger.debug('--------------Start coil balancing of %s TM %s------------------'%(optic,coil))
    ezca['VIS-%s_PAY_OLSERVO_LKIN_DEMOD_PHASE'%optic] = 0
    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_SINGAIN'%optic] = 1
    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_COSGAIN'%optic] = 1
    if freq == 'Default':
        freq = default_freq[coil]

    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_FREQ'%optic] = freq
    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_TRAMP'%optic] = oscTRAMP
    I = ezca.get_LIGOFilter('VIS-%s_PAY_OLSERVO_LKIN_DEMOD_I'%optic)
    Q = ezca.get_LIGOFilter('VIS-%s_PAY_OLSERVO_LKIN_DEMOD_Q'%optic)
    I.only_on('INPUT','OUTPUT','DECIMATION')
    Q.only_on('INPUT','OUTPUT','DECIMATION')

    #logger.debug('Turn on the filter named %s in DEMOD_I filter bank'%I.Name00.get())
    I.turn_on('FM1')

    #logger.debug('Turn on the filter named %s in DEMOD_Q filter bank'%Q.Name00.get())
    Q.turn_on('FM1')
    
    # if there is a proper comb filter in I and Q FB, engage it
    for ii in range(10):
        
        exec('FMnameI = I.Name%s.get()'%str(ii).zfill(2))
        exec('FMnameQ = Q.Name%s.get()'%str(ii).zfill(2))

        if ('comb' in FMnameI) and (str(freq) in FMnameI):
            I.turn_on('FM%d'%(ii+1))
            #logger.debug('Turn on the filter named %s in DEMOD_I filter bank'%FMnameI)
        if ('comb' in FMnameQ) and (str(freq) in FMnameQ):
            #logger.debug('Turn on the filter named %s in DEMOD_Q filter bank'%FMnameQ)
            Q.turn_on('FM%d'%(ii+1))


    # input and output matrix setting
    actDoF = {'H2':'L','H4':'L'}
    readback = {'H2':'TMP','H4':'TMY'}
    OUTindx = {'BFL':1,'BFT':2,'BFY':3,'MNL':4,'MNT':5,'MNV':6,'MNR':7,'MNP':8,'MNY':9,'IML':10,'IMT':11,'IMV':12,'IMR':13,'IMP':14,'IMY':15,'TML':16,'TMP':17,'TMY':18}
    INindx = {'MNP':1,'MNY':2,'TML':3,'TMP':4,'TMY':5,'ISCL':6,'ISCP':7,'ISCY':8}

    for ii in range(18):
        ezca['VIS-%s_PAY_OLSERVO_PK2EUL_%d_25'%(optic,ii+1)] = 0
    for ii in range(8):
        ezca['VIS-%s_PAY_OLSERVO_OL2PK_25_%d'%(optic,ii+1)] = 0
    ezca['VIS-%s_PAY_OLSERVO_PK2EUL_16_25'%(optic)] = 1
    ezca['VIS-%s_PAY_OLSERVO_OL2PK_25_%d'%(optic,INindx[readback[coil]])] = 1

    # EULER to SENS matrix setting
    if coil == 'H2':
        ezca['VIS-%s_TM_EUL2COIL_1_1'%(optic)] = 1
        ezca['VIS-%s_TM_EUL2COIL_2_1'%(optic)] = 1
        ezca['VIS-%s_TM_EUL2COIL_3_1'%(optic)] = 0
        ezca['VIS-%s_TM_EUL2COIL_4_1'%(optic)] = 0
        #logger.debug('Turn off the output to H3 and H4')
    else:
        ezca['VIS-%s_TM_EUL2COIL_1_1'%(optic)] = 0
        ezca['VIS-%s_TM_EUL2COIL_2_1'%(optic)] = 0
        ezca['VIS-%s_TM_EUL2COIL_3_1'%(optic)] = 1
        ezca['VIS-%s_TM_EUL2COIL_4_1'%(optic)] = 1
        #logger.debug('Turn off the output to H3 and H4')

    # turn on excitation.
    #logger.debug('Turn on excitation at %f Hz with ramptime of %d.'%(freq,oscTRAMP))
    if oscAMP == 'Default':
        oscAMP = default_amp[coil]
    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_CLKGAIN'%optic] = oscAMP
    #logger.debug('Ramping to %f...'%oscAMP)
    time.sleep(oscTRAMP)

    # prepare the measurement
    # decide sweep range
    if coil_gain[coil] < 0:
        sw_range = [max(sweeprange)*(-1.0),min(sweeprange)*(-1.0)]
    else:
        sw_range = sweeprange
            
    #logger.debug('Sweeprange of %s COILOUTF gain is [%f, %f]'%(coil, min(sw_range),max(sw_range)))
    #logger.debug('The number of sweep point is %d'%(Np))
    sweepstep = (max(sw_range)-min(sw_range))/((Np-1)*1.)
    gg = np.arange(min(sw_range),max(sw_range),sweepstep) # sweepgain list
    gg = np.append(gg,max(sw_range))
    print gg
    avgI = [] # Void list to put output of I filter
    avgQ = [] # Void list to put output of Q filter
    stdI = [] # Void list to put standard diviation of output of I filter
    stdQ = [] # Void list to put standard diviation of output of Q filter

    OUTF = ezca.get_LIGOFilter('VIS-%s_TM_COILOUTF_%s'%(optic,coil))
    ii = 0
    for gain in gg:
        ii += 1
        # change gain with ramptime of 5 sec. Wait for the ramping.
        #logger.debug('---------------Measurement #%d / %d of TM %s----------------'%(ii,Np,coil))
        #logger.debug('COILOUTF gain is ramping to %f'%gain)
        OUTF.ramp_gain(gain,ramp_time=5,wait=True)

        # Check suspension condition
        CheckSuspension(optic,logger)
        
        # wait for a while.
        #logger.debug('Waiting for %d seconds'%settleDuration)
        time.sleep(settleDuration)
        
        # fetch the data
        d = cdsutils.getdata(['K1:'+I.filter_name+'_OUT','K1:'+Q.filter_name+'_OUT'],duration=avgDuration)
        avgI.append(np.mean(d[0].data))
        avgQ.append(np.mean(d[1].data))
        stdI.append(np.std(d[0].data))
        stdQ.append(np.std(d[1].data))
        #logger.debug('Result: (I, Q) = (%f, %f)'%(avgI[-1],avgQ[-1]))
        #logger.debug('Std: (I, Q) = (%f, %f)'%(stdI[-1],stdQ[-1]))
    return gg, avgI, avgQ, stdI, stdQ
        

if __name__ == '__main__':
    ezca = Ezca()

    # define default frequencies for each optics
    default_freq = {'H2':5,'H4':5}

    default_amp = {'H2':5000,'H4':5000}
    
    ## Parse arguments and define constants
    parser=argparse.ArgumentParser(description=
'''Balance the coils with COILOUTF gains of TypeA
e.g. balanceCOILOUTF.py ITMY
     balanceCOILOUTF.py ITMY -f 0.3 -a 1000 -d 10 -r 10 --sr 0.1 1.0''',formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('OPTIC',help='Optic you want to balance the coils (e.g. ITMY)')
    #parser.add_argument('-s',dest='STAGE',default='ALL',help='Stage to be balanced (e.g. MN)[default=ALL]')
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
    
    if args.COIL == 'ALL':
        coils = ['H2','H4']
    else:
        if not args.COIL in ['H2','H4']:
            print 'Invalid coil.'
        coils = [args.COIL,]
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
    
    #logger=logging.getLogger('flogger')
    #logger.setLevel(logging.DEBUG)
    handler=logging.StreamHandler()
    #logger.addHandler(handler)
    handler=logging.FileHandler(filename=log_file)
    #logger.addHandler(handler)

    ## open ndscope
    #os.system('ndscope -s K1:VIS-%s_TM_OPLEV_PIT_DIAGMON K1:VIS-%s_TM_OPLEV_YAW_DIAGMON K1:VIS-%s_PAY_OLSERVO_LKIN_DEMOD_I_OUTPUT K1:VIS-%s_PAY_OLSERVO_LKIN_DEMOD_Q_OUTPUT &'%(optic,optic,optic,optic))

    ## result dict

    coil_gain = Signcoiloutgain(optic)

    try:
        for coil in coils:
            gg,avgI,avgQ,stdI,stdQ = Balancing(optic,coil,freq,oscAMP,coil_gain,sweeprange,Np=Npoints,avgDuration=duration,settleDuration=SettleDuration)

            ## fitting
            pI = np.polyfit(gg,avgI,1)
            pQ = np.polyfit(gg,avgQ,1)
            pGAIN = float(pI[1])/float(pI[0])*(-1) # final gain of the balanced coil 

            #logger.debug('fitresult with a*gain + b:')
            #logger.debug('-I (a,b) = (%f,%f)'%(pI[0],pI[1]))
            #logger.debug('-Q (a,b) = (%f,%f)'%(pQ[0],pQ[1]))
            #logger.debug('%s GAIN = %f'%(coil,pGAIN))

            #logger.debug('put %f in VIS-%s_TM_COILOUTF_%s_GAIN'%(pGAIN, optic, coil))
            ezca['VIS-%s_TM_COILOUTF_%s_GAIN'%(optic, coil)] = pGAIN
            
            ## plot results
            plt.close()
            plt.scatter(gg,avgI,label="I")
            plt.scatter(gg,avgQ,color='red',label="Q")
            plt.plot(gg,np.polyval(pI,gg))
            plt.plot(gg,np.polyval(pQ,gg))
            plt.grid()
            
            #plt.plot(gg,fitfunc(paramQ[0],paramQ[1],np.array(gg)))
            plt.xlabel('%s_TM_COILOUTF_%s_GAIN'%(optic,coil))
            plt.ylabel('Amplitude of demodulated signal')
            plt.legend()
            plt.savefig(log_dir+'archives/balanceCOILOUTF_%s_'%optic + date_str +'_TM_%s'%(coil)+'.png')
            plt.savefig(log_dir+'balanceCOILOUTF_%s_TM_%s_latest'%(optic,coil)+'.png')
                

        os.system('cp %s %s'%(log_file,(log_dir+'balanceCOILOUTF_%s_latest.log'%optic)))
        ShutdownLOCKIN(optic)
    except KeyboardInterrupt:
        ## Shut down LOCKIN
        logger.debug('Keyboard Interruption detected! Shutting down...')
        ShutdownLOCKIN(optic)
        
