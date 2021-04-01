# Script for balancing the coils of TypeA
# 10th Jul., 2020 by M. Nakano

import numpy as np
from datetime import datetime
import argparse, logging, sys, os
from ezca import Ezca
import time
import cdsutils
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Function to check the suspension condition
# def CheckSuspension(optic,logger):
#     # check oplev in range
#     warningflag = True
#     while not ezca['GRD-VIS_%s_STATE'%optic] == 'TWR_DAMPED':
#         if warningflag:
#             logger.debug('Guardian is not in TWR_DAMPED. Please request TWR_DAMPED')
#             warningflag = False

#     warningflag = True
#     while any([abs(ezca['VIS-%s_TM_OPLEV_%s_DIAGMON'%(optic,DoF)]) > 50 for DoF in ['YAW','PIT']]) or ezca['VIS-%s_TM_OPLEV_TILT_SUM_OUTPUT'%optic] < 3000:
#         if warningflag:
#             logger.debug('Oplev is out of range. Please bring it to center by using optic align.')
#             warningflag = False

#     logger.debug('Oplev value is (p,y) = (%f,%f)'%(ezca['VIS-%s_TM_OPLEV_PIT_DIAGMON'%(optic)],ezca['VIS-%s_TM_OPLEV_YAW_DIAGMON'%(optic)]))

def ShutdownLOCKIN(optic):
    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_CLKGAIN'%optic] = 0
    time.sleep(ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_TRAMP'%optic])

#Function for balance the coil
#def Balancing(optic,stage,coil,freq,oscAMP,sweeprange,logger,Np=10,avgDuration=10,settleDuration=5,oscTRAMP=10):
def Balancing(optic,stage,coil,freq,oscAMP,sweeprange,Np=10,avgDuration=10,settleDuration=5,oscTRAMP=10):    
    #logger.debug('--------------Start coil balancing of %s %s %s------------------'%(optic,stage,coil))
    ezca['VIS-{0}_{2}_DEMOD_PHASE'.format(optic,stage,'LKIN_P')] = 0
    ezca['VIS-{0}_{2}_OSC_SINGAIN'.format(optic,stage,'LKIN_P')] = 1
    ezca['VIS-{0}_{2}_OSC_COSGAIN'.format(optic,stage,'LKIN_P')] = 1    

    if freq == 'Default':
        freq = default_freq[stage][coil]

    ezca['VIS-{0}_{2}_OSC_FREQ'.format(optic,stage,'LKIN_P')] = freq
    ezca['VIS-{0}_{2}_OSC_TRAMP'.format(optic,stage,'LKIN_P')] = oscTRAMP

    I = ezca.get_LIGOFilter('VIS-{0}_{2}_DEMOD_I'.format(optic,stage,'LKIN_P'))
    Q = ezca.get_LIGOFilter('VIS-{0}_{2}_DEMOD_Q'.format(optic,stage,'LKIN_P'))
    #Q = ezca.get_LIGOFilter('VIS-ITMY_PAY_OLSERVO_LKIN_DEMOD_Q')
    I.only_on('INPUT','OUTPUT','DECIMATION')
    Q.only_on('INPUT','OUTPUT','DECIMATION')

    # logger.debug('Turn on the filter named %s in DEMOD_I filter bank'%I.Name00.get())
    I.turn_on('FM1')

    # logger.debug('Turn on the filter named %s in DEMOD_Q filter bank'%Q.Name00.get())
    Q.turn_on('FM1')
    
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

    exit()
    # input and output matrix setting
    actDoF = {'V3':'V','H2':'L','H3':'T'}
    readback = {'V3':'TMP','H2':'TMY','H3':'TMY'}
    OUTindx = {'BFL':1,'BFT':2,'BFY':3,'MNL':4,'MNT':5,'MNV':6,'MNR':7,'MNP':8,'MNY':9,'IML':10,'IMT':11,'IMV':12,'IMR':13,'IMP':14,'IMY':15,'TML':16,'TMP':17,'TMY':18}
    INindx = {'MNP':1,'MNY':2,'TML':3,'TMP':4,'TMY':5,'ISCL':6,'ISCP':7,'ISCY':8}

    for ii in range(18):
        ezca['VIS-%s_PAY_OLSERVO_PK2EUL_%d_25'%(optic,ii+1)] = 0
    for ii in range(8):
        ezca['VIS-%s_PAY_OLSERVO_OL2PK_25_%d'%(optic,ii+1)] = 0
    ezca['VIS-%s_PAY_OLSERVO_PK2EUL_%d_25'%(optic,OUTindx[stage+actDoF[coil]])] = 1
    ezca['VIS-%s_PAY_OLSERVO_OL2PK_25_%d'%(optic,INindx[readback[coil]])] = 1

    # turn on excitation.
    logger.debug('Turn on excitation at %f Hz with ramptime of %d.'%(freq,oscTRAMP))
    if oscAMP == 'Default':
        oscAMP = default_amp[stage][coil]
    ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_CLKGAIN'%optic] = oscAMP
    logger.debug('Ramping to %f...'%oscAMP)
    time.sleep(oscTRAMP)

    # prepare the measurement
    logger.debug('Sweeprange of COILOUTF gain is [%f, %f]'%(min(sweeprange),max(sweeprange)))
    logger.debug('The number of sweep point is %d'%(Np))
    sweepstep = (max(sweeprange)-min(sweeprange))/((Np-1)*1.)
    gg = np.arange(min(sweeprange),max(sweeprange),sweepstep)#sweepgain list
    gg = np.append(gg,max(sweeprange))
    print(gg)
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
        CheckSuspension(optic,logger)
        
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
        'MN':{'V3':5,'H2':5,'H3':6},
        'IM':{'V3':5,'H2':5,'H3':6},
    }

    default_amp = {
        'MN':{'V3':3000,'H2':3000,'H3':3000},
        'IM':{'V3':3000,'H2':500,'H3':500},
    }
    
    ## Parse arguments and define constants
    parser=argparse.ArgumentParser(description=
                                   '''Balance the coils with COILOUTF gains of TypeA
                                   e.g. balanceCOILOUTF.py ITMY
                                   balanceCOILOUTF.py ITMY -f 0.3 -a 1000 -d 10 -r 10''',
                                   formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('OPTIC',help='Optic you want to balance the coils (e.g. SRM)')
    parser.add_argument('-s',dest='STAGE',default='ALL',help='Stage to be balanced (e.g. MN)[default=ALL]')
    parser.add_argument('-c',dest='COIL',default='ALL',help='Coil to be balanced (e.g. V3)[default=ALL]')
    parser.add_argument('-f',dest='FREQ',default='Default',help='Modulation frequency [default=5Hz]')
    parser.add_argument('-a',dest='AMP',default='Default',help='Modulation amplitude [default=5000cnts]')
    parser.add_argument('-d',dest='DURATION',type=float,default=10,help='Duration of each measurement [default=10sec]')
    parser.add_argument('--st',dest='SETTLETIME',type=float,default=5,help='Settle time after changing OUTF gain [default=5sec]')
    parser.add_argument('-t',dest='TEST',default=0,help='0 for real run, 1 for test run which does not update COILOUTF [default=0]')
    parser.add_argument('--sr',dest='SWEEPRANGE',type=list,default=[0.9,1.1],help='Range for OUTF gain sweeping [default=[0.9,1.1]]')
    parser.add_argument('-n',dest='NPOINTS',type=int,default=10,help='Number of point [default=10]')
    args = parser.parse_args()
    optic = args.OPTIC
    freq = args.FREQ
    if args.STAGE == 'ALL':
        stages = ['MN','IM']
    else:
        if not args.STAGE in ['IM','MN']:
            print('Invalid stage. {0}'.format(args.STAGE))
        stages = [args.STAGE,]

    if args.COIL == 'ALL':
        coils = ['V3','H2','H3']
    else:
        if not args.COIL in ['V3','H2','H3']:
            print('Invalid coil. {0}'.format(args.COIL))
        coils = [args.COIL,]
    oscAMP = (args.AMP)
    sweeprange = (args.SWEEPRANGE)
    Npoints = (args.NPOINTS)
    duration = args.DURATION
    SettleDuration = args.SETTLETIME

    # ##### Define logger
    # dt_now = datetime.now()
    # year = dt_now.year
    # month = dt_now.month
    # day = dt_now.day
    # hour = dt_now.hour
    # minute = dt_now.minute

    # log_dir = '/users/Commissioning/scripts/diagonalization/log/'
    # date_str = '%d%s%s_%s%s'%(year,str(month).zfill(2),str(day).zfill(2),str(hour).zfill(2),str(minute).zfill(2))
    # log_file = log_dir + 'archives/balanceCOILOUTF_%s_'%optic + date_str + '.log'
    
    # logger=logging.getLogger('flogger')
    # logger.setLevel(logging.DEBUG)
    # handler=logging.StreamHandler()
    # logger.addHandler(handler)
    # handler=logging.FileHandler(filename=log_file)
    # logger.addHandler(handler)

    # open ndscope
    #os.system('ndscope -s K1:VIS-%s_TM_OPLEV_PIT_DIAGMON K1:VIS-%s_TM_OPLEV_YAW_DIAGMON K1:VIS-%s_PAY_OLSERVO_LKIN_DEMOD_I_OUTPUT K1:VIS-%s_PAY_OLSERVO_LKIN_DEMOD_Q_OUTPUT &'%(optic,optic,optic,optic))

    # result dict

    try:
        for stage in stages:
            for coil in coils:
                # balancing
                print(optic,stage,coil,freq,oscAMP,sweeprange)
                gg,avgI,avgQ,stdI,stdQ = Balancing(optic,stage,coil,freq,
                                                   oscAMP,sweeprange,#logger,
                                                   Np=Npoints,avgDuration=duration,
                                                   settleDuration=SettleDuration)
                exit()
                # fititing
                pI = np.polyfit(gg,avgI,1)
                pQ = np.polyfit(gg,avgQ,1)

                logger.debug('fitresult with a*gain + b:')
                logger.debug('-I (a,b) = (%f,%f)'%(pI[0],pI[1]))
                logger.debug('-Q (a,b) = (%f,%f)'%(pQ[0],pQ[1]))

                logger.debug('balance')
                # plot results
                plt.scatter(gg,avgI)
                plt.scatter(gg,avgQ,color='red')
                plt.plot(gg,np.polyval(pI,gg))
                plt.plot(gg,np.polyval(pQ,gg))
                #plt.plot(gg,fitfunc(paramQ[0],paramQ[1],np.array(gg)))
                plt.savefig(log_dir+'archives/balanceCOIULOUTF_%s_'%optic + date_str +'_%s_%s'%(stage,coil)+'.png')
                plt.savefig(log_dir+'balanceCOULOUTF_%s_%s_%s_latest'%(optic,stage,coil)+'.png')
                

        os.system('cp %s %s'%(log_file,(log_dir+'balanceCOILOUTF_%s_latest.log'%optic)))
        ShutdownLOCKIN(optic)
    except KeyboardInterrupt:
        ## Shut down LOCKIN
        logger.debug('Keyboard Interruption detected! Shutting down...')
        ShutdownLOCKIN(optic)
        
    
