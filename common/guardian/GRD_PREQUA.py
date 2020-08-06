from guardian import GuardState
from guardian import GuardStateDecorator
import cdsutils
import gpstime

import kagralib
import vislib
import time
import foton

import numpy as np
import importlib

sysmod = importlib.import_module(SYSTEM)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import logging


__,OPTIC = SYSTEM.split('_') # This instruction retrieves the name of the Guardian node running the code e.i. the suspension name: SYSTEM='VIS_BS'.
optic = OPTIC.lower()
sustype = vislib.get_Type(OPTIC)
chans = '/opt/rtcds/kamioka/k1/chans/'
DoFList = ['LEN','TRA','VER','ROL','PIT','YAW']



##################################################
# initialization values
state = 'STANDBY' # For determining where the guardian state is.

# initial REQUEST state
request = 'STANDBY'

# NOMINAL state, which determines when node is OK
nominal = 'STANDBY'

##################################################
# State Decorator
class check_mod_freq(GuardStateDecorator):
    def pre_exec(self):
        modeindex = ezca['QUA-%s_MODE_INDEX'%OPTIC]

        try:
            if not ezca['VIS-%s_PREQUA_DEMOD_FREQ'%(OPTIC)] == ezca['VIS-%s_FREE_MODE_LIST_NO%d_PRE_FREQ'%(OPTIC,modeindex)]:
                log('Measurement mode index has been changed. Initialize PReQua')
                return 'INIT_PREQUA'

        except:
            log('Measurement mode index has been changed. Initialize PReQua')
            return 'INIT_PREQUA'



##################################################
# State Definitions
class INIT(GuardState):
    index = 0
    request = True
    def main(self):
        return True

class STANDBY(GuardState):
    index = 1
    request = True
    def main(self):
        return True



class INIT_DIAG(GuardState):
    index = 10
    request = True

             
    def main(self):
        
        self.TOWER_FBs = foton.FilterFile(chans+'K1VIS%sT.txt'%(OPTIC.upper()))
        self.PAYLOAD_FBs = foton.FilterFile(chans+'K1VIS%sP.txt'%(OPTIC.upper()))
        self.QUA_FBs = foton.FilterFile(chans+'K1VIS%sMON.txt'%(OPTIC.upper()))
        self.MODAL = foton.FilterFile(chans+'K1MODAL%s.txt'%(OPTIC.upper()))
        

        '''
        # Initialize INF for each sensor
        # IP
        stage = 'IP'


        for sensor in ['H1','H2','H3']:
            log('copy IP %s INF'%sensor)
            kagralib.copy_FB('VIS',self.TOWER_FBs,'%s_IP_LVDTINF_%s'%(OPTIC,sensor),self.QUA_FBs,'%s_IP_DIAG_INF_%s'%(OPTIC,sensor))

        # BF
        stage = 'BF'
        for sensor in ['V1','V2','V3','H1','H2','H3']:
            log('copy BF %s INF'%sensor)
            kagralib.copy_FB('VIS',self.TOWER_FBs,'%s_BF_LVDTINF_%s'%(OPTIC,sensor),self.QUA_FBs,'%s_BF_DIAG_INF_%s'%(OPTIC,sensor))
        '''
        # MN, IM
        for stage in ['MN','IM']:
            for sensor in ['V1','V2','V3','H1','H2','H3']:
                kagralib.foton_comb(self.QUA_FBs,'%s_%s_DIAG_INF_%s'%(OPTIC,stage,sensor),0,freq=60,Q=100,amplitude=-100,force=True)
                kagralib.foton_butter(self.QUA_FBs,'%s_%s_DIAG_INF_%s'%(OPTIC,stage,sensor),1,freq=100,order=3,force=True)
                kagralib.foton_zpk(self.QUA_FBs,'%s_%s_DIAG_INF_%s'%(OPTIC,stage,sensor),2,z=[12.3,],p=[0.46,],k=1,name='de-white',force=True)

                ezca.switch('VIS-%s_%s_DIAG_INF_%s'%(OPTIC,stage,sensor),'FM1','FM2','FM3','ON')

        self.QUA_FBs.write()
        '''
        # TM
        stage = 'TM'
        for oplev in ['LEN','TILT']:
            for dof in ['PIT','YAW','SUM']:
                kagralib.copy_FB('VIS',self.PAYLOAD_FBs,'%s_%s_OPLEV_%s_%s'%(OPTIC,stage,oplev,dof),self.QUA_FBs,'%s_%s_DIAG_OPLEV_%s_%s'%(OPTIC,stage,oplev,dof))
            for ii in range(4):
                log('copy %s %s SEG%d INF'%(stage,oplev,ii+1))
                kagralib.copy_FB('VIS',self.PAYLOAD_FBs,'%s_%s_OPLEV_%s_SEG%d'%(OPTIC,stage,oplev,ii+1),self.QUA_FBs,'%s_%s_DIAG_OPLEV_%s_SEG%d'%(OPTIC,stage,oplev,ii+1))
        '''

        log('zero offset')
        darkchans = ['K1:VIS-%s_%s_DIAG_INF_%s_INMON'%(OPTIC,stage,sensor) for stage in ['IP','BF','MN','IM'] for sensor in ['V1','V2','V3','H1','H2','H3']]
        _data = cdsutils.getdata(darkchans,10)
        dark = {darkchans[ii]:np.average(_data[ii].data) for ii in range(len(darkchans))}
        for stage in ['IP','BF','MN','IM']:
            for sensor in ['V1','V2','V3','H1','H2','H3']:
                ezca['VIS-%s_%s_DIAG_INF_%s_OFFSET'%(OPTIC,stage,sensor)] = -dark['K1:VIS-%s_%s_DIAG_INF_%s_INMON'%(OPTIC,stage,sensor)]
                ezca.switch('VIS-%s_%s_DIAG_INF_%s'%(OPTIC,stage,sensor),'OFFSET','ON')
        # Initialize COILOUTF
        coildict = {'IP':['H1','H2','H3'],
                    'BF':['V1','V2','V3','H1','H2','H3'],
                    'MN':['V1','V2','V3','H1','H2','H3'],
                    'IM':['V1','V2','V3','H1','H2','H3'],
                    'TM':['H1','H2','H3','H4'],
                    }

        
        for stage in ['IP','BF','MN','IM','TM']:
            for coil in coildict[stage]:
                if stage in ['IP','BF']:
                    FBs = self.TOWER_FBs
                else:
                    FBs = self.PAYLOAD_FBs
                kagralib.foton_comb(FBs,'MOD_%s_%s_COILOUTF_%s'%(OPTIC,stage,coil),0,freq=128,Q=10,amplitude=-100,harmonics=4,force=True)
                kagralib.foton_ELP(FBs,'MOD_%s_%s_COILOUTF_%s'%(OPTIC,stage,coil),1,freq=128,force=True)
                ezca.switch('MOD-%s_%s_COILOUTF_%s'%(OPTIC,stage,coil),'FM1','FM2','ON',)
        self.TOWER_FBs.write()
        self.PAYLOAD_FBs.write()
                
        # Initialize SEN2EUL matrix
        sensors = ['V1','V2','V3','H1','H2','H3']
        OL_sensors = ['TILT_PIT','TILT_YAW','LEN_PIT','LEN_YAW']
        OL_DoFs = ['PIT','YAW','SUM']
        DoFs = DoFList
        DIAG_SEN2EUL = {stage:cdsutils.CDSMatrix(
            'VIS-%s_%s_DIAG_SEN2EUL'%(OPTIC,stage),
            cols={ii+1: sensors[ii] for ii in range(6)},
            rows={ii+1: DoFs[ii] for ii in range(6)},
        ) for stage in ['IP','BF','MN','IM']}
        MOD_EUL2COIL = {stage:cdsutils.CDSMatrix(
            'MOD-%s_%s_EUL2COIL'%(OPTIC,stage),
            cols={ii+1: sensors[ii] for ii in range(6)},
            rows={ii+1: DoFs[ii] for ii in range(6)},
        ) for stage in ['IP','BF','MN','IM']}
        DIAG_SEN2EUL_OL = cdsutils.CDSMatrix(
            'VIS-%s_TM_DIAG_SEN2EUL'%(OPTIC),
            cols={ii+1: sensors[ii] for ii in range(4)},
            rows={ii+1: DoFs[ii] for ii in range(6)},
        )
        MOD_EUL2COIL_TM = cdsutils.CDSMatrix(
            'MOD-%s_TM_EUL2COIL'%(OPTIC),
            cols={ii+1: DoFs[ii] for ii in range(6)},
            rows={ii+1: sensors[ii] for ii in range(4)},
        )
        DECPL = {stage:cdsutils.CDSMatrix(
            'VIS-%s_%s_DIAG_DECPL'%(OPTIC,stage),
            cols={ii+1: DoFs[ii] for ii in range(6)},
            rows={ii+1: DoFs[ii] for ii in range(6)},
        ) for stage in ['IP','BF','MN','IM','TM']}

        DRIVEDECPL = {stage:cdsutils.CDSMatrix(
            'MOD-%s_%s_DRIVEDECPL'%(OPTIC,stage),
            cols={ii+1: DoFs[ii] for ii in range(6)},
            rows={ii+1: DoFs[ii] for ii in range(6)},
        ) for stage in ['IP','BF','MN','IM','TM']}
        
        OL2EUL = {oplev:cdsutils.CDSMatrix(
            'VIS-%s_TM_DIAG_OPLEV_%s_MTRX'%(OPTIC,oplev),
            cols={ii+1: 'SEG%d'%(ii+1) for ii in range(4)},
            rows={ii+1: OL_DoFs[ii] for ii in range(3)},
        ) for oplev in ['TILT','LEN']}
        # IP
        DIAG_SEN2EUL['IP'].put_matrix(
            np.matrix([[0,0,0,2./3.,-1./3.,-1./3.],
             [0,0,0,0,-1./np.sqrt(3),1./np.sqrt(3)],
             [0,0,0,0,0,0],
             [0,0,0,0,0,0],
             [0,0,0,0,0,0],
             [0,0,0,1./np.sqrt(3),1./np.sqrt(3),1./np.sqrt(3)]]
            ))
        MOD_EUL2COIL['IP'].put_matrix(
            np.matrix([[0,0,0,0,0,0,],
                       [0,0,0,0,0,0,],
                       [0,0,0,0,0,0,],
                       [2./3.,0,0,0,0,1/np.sqrt(3)],
                       [-1./3.,-1./np.sqrt(3),0,0,0,1./np.sqrt(3)],
                       [-1./3.,1/np.sqrt(3),0,0,0,1./np.sqrt(3)]]
            ))

        DIAG_SEN2EUL['BF'].put_matrix(
            np.matrix([[0,0,0,2./3.,-1./3.,-1./3.],
             [0,0,0,0,-1./np.sqrt(3),1./np.sqrt(3)],
             [1./3.,1./3.,1./3.,0,0,0],
             [-0.9157,-0.9157,1.83150,0,0,0],
             [-1.5861,1.5861,0,0,0,0],
             [0,0,0,0.8170,0.8170,0.8170]]
            ))

        MOD_EUL2COIL['BF'].put_matrix(
            np.matrix([[0,0,1,-0.182,-0.3152,0],
                       [0,0,1,-0.182,0.3152,0],
                       [0,0,1,0.364,0,0],
                       [1,0,0,0,0,0.408],
                       [-0.5,-0.866,0,0,0,0.408],
                       [-0.5,0.866,0,0,0,0.408]]
            ))

        for stage in ['IM','MN']:
            DIAG_SEN2EUL[stage].put_matrix(
                np.matrix([[0,0,0,1./2.,1./2.,0],
                           [0,0,0,-1./2.,1./2.,1],
                           [-1./2.,0,-1./2.,0,0,0],
                           [1./2.,-1,1./2.,0,0,0],
                           [1./2.,0,-1./2.,0,0,0],
                           [0,0,0,1./2.,-1./2.,0]]
                      ))
        for stage in ['IM','MN']:
            MOD_EUL2COIL[stage].put_matrix(
                np.matrix([[0,0,0.5,-0.5,-0.5,0],
                           [0,0,0,1,0,0],
                           [0,0,0.5,-0.5,0.5,0],
                           [-0.5,0.5,0,0,0,-0.5],
                           [-0.5,-0.5,0,0,0,0.5],
                           [0,-1,0,0,0,0]]
                      ))
        DIAG_SEN2EUL_OL.put_matrix(
            np.matrix([[0,0,0,1],
                       [0,0,0,0],
                       [0,0,0,0],
                       [0,0,0,0],
                       [1,0,0,0],
                       [0,1,0,0]]
            ))

        MOD_EUL2COIL_TM.put_matrix(
            np.matrix([[1,0,0,0,1,0],
                       [1,0,0,0,-1,0],
                       [1,0,0,0,0,-1],
                       [1,0,0,0,0,1]],
            ))


        for stage in DECPL.keys():
            DECPL[stage].put_matrix(
                np.identity(6)
                )
            DRIVEDECPL[stage].put_matrix(
                np.identity(6)
                )
        for oplev in OL2EUL.keys():
            OL2EUL[oplev].put_matrix(
                np.matrix(
                    [[-1,-1,1,1],
                     [1,-1,-1,1],
                     [1,1,1,1]],
                    )
                )
        if int(ezca['FEC-%d_STATE_WORD'%sysmod.DCUID]) & 0b10000000000:
            ezca['FEC-%d_LOAD_NEW_COEFF'%sysmod.DCUID] = 1

        
    def run(self):
        if int(ezca['FEC-%d_STATE_WORD'%sysmod.DCUID]) & 0b10000000000:
            notify('Waiting to load coefficiency!')
        else:
            return True
    

class INIT_PREQUA(GuardState):
    index = 50
    request = True
    goto = True

    def main(self):
        self.FB_load = False
        self.modeindex = 0
        self.counter = 0
        self.timer['waiting'] = 0
        self.FBs = foton.FilterFile(chans+'K1VIS%sMON.txt'%OPTIC)

    def run(self):
        if not self.modeindex == ezca['QUA-%s_MODE_INDEX'%OPTIC]:
            self.modeindex = ezca['QUA-%s_MODE_INDEX'%OPTIC]
            self.counter = 0
            
        if self.modeindex < 1 or self.modeindex > 30:
            notify('Invalid mode index. Please check QUA_%s_MODE_INDEX'%OPTIC)
            return

        self.modeDoF = ezca['VIS-%s_FREE_MODE_LIST_NO%d_DOF'%(OPTIC,self.modeindex)]
        self.modeStage = ezca['VIS-%s_FREE_MODE_LIST_NO%d_PLL_SENS'%(OPTIC,self.modeindex)]
        _degenerate = ezca['VIS-%s_FREE_MODE_LIST_NO%d_DEGEN_MODE'%(OPTIC,self.modeindex)].split(',')
        self.degenerate = []
        for modestr in _degenerate:
            try:
                self.degenerate.append(int(modestr))
            except:
                pass
        
        if not self.modeDoF in DoFList:
            notify('start PReQua initialization')
            notify('Mode DoF is not defined propery. Please define it at VIS-%s_FREE_MODE_LIST_NO%d_DOF'%(OPTIC,self.modeindex))
            self.counter = 0
            return
        
        if not self.modeStage in ['IP','BF','MN','IM','TM']:
            notify('Mode refelence stage is not defined propery. Please define it at VIS-%s_FREE_MODE_LIST_NO%d_PLL_SENS'%(OPTIC,self.modeindex))
            self.counter = 0
            return

        if not self.timer['waiting']:
            return

        if self.counter == 0:

            # reset stop watch
            ezca['VIS-%s_PREQUA_DEMOD_SW'%OPTIC] = 0
            time.sleep(0.1)
            ezca['VIS-%s_PREQUA_DEMOD_SW'%OPTIC] = 1
            
            self.pre_freq = ezca['VIS-%s_FREE_MODE_LIST_NO%d_PRE_FREQ'%(OPTIC,self.modeindex)]
            self.pre_Q = ezca['VIS-%s_FREE_MODE_LIST_NO%d_PRE_Q'%(OPTIC,self.modeindex)]
            if self.pre_freq == 0 or self.pre_Q == 0:
                notify('Invalid predicted frequency and Q. Please check VIS-%s_FREE_MODE_LIST_NO%d_PRE_FREQ'%(OPTIC,self.modeindex))
                return

            ezca['VIS-%s_PREQUA_DEMOD_FREQ'%(OPTIC)] = self.pre_freq
            
            self.pre_tau = self.pre_Q/self.pre_freq/np.pi

            edit_chans = []
            for stage in ['IP','BF','MN','IM','TM']:
                for DoF in DoFList:
                    # channel name 
                    QUAname = 'VIS-%s_%s_QUA%s'%(OPTIC,stage,DoF)
                    fotonQUAname = QUAname[4:]


                    
                    ezca[QUAname+'_CALC_DECAY_DT'] = 30 * 1./self.pre_freq

                    # edit foton file
                    # SIG (bandpass)
                    kagralib.foton_butter(self.FBs,
                                          fotonQUAname+'_PLL_DEMOD_SIG',
                                          Type='BandPass',
                                          index=0,
                                          order=2,
                                          freq=self.pre_freq-self.pre_freq/(self.pre_Q*1.),
                                          freq2=self.pre_freq+self.pre_freq/(self.pre_Q*1.),
                                          force=True)
                    edit_chans.append(QUAname+'_PLL_DEMOD_SIG')
                    
                    _notchdesign = ''
                    if len(self.degenerate) > 0:
                        for mode in self.degenerate:
                            notchfreq = ezca['VIS-%s_FREE_MODE_LIST_NO%d_PRE_FREQ'%(OPTIC,mode)]
                            if notchfreq > 0:
                                _notchdesign += kagralib.foton_notch(self.FBs,
                                                     fotonQUAname+'_PLL_DEMOD_SIG',
                                                     index=1,
                                                     Q=100,
                                                     attenuation=100,
                                                     freq=notchfreq,
                                                     force=True)

                        kagralib.foton_design(self.FBs,
                                              fotonQUAname+'_PLL_DEMOD_SIG',
                                              1,
                                              _notchdesign,
                                              'notch',
                                              force=True)

                            
                    # SIG RMS (lowpass)
                    kagralib.foton_butter(self.FBs,
                                          fotonQUAname+'_PLL_DEMOD_SIG_RMS',
                                          Type='LowPass',
                                          index=0,
                                          order=2,
                                          freq=self.pre_freq/10,
                                          force=True)
                    edit_chans.append(QUAname+'_PLL_DEMOD_SIG_RMS')
        
                    # IQ (lowpass+notch)
                    for phase in ['I','Q','AMP']:
                        kagralib.foton_butter(self.FBs,
                                              fotonQUAname+'_PLL_DEMOD_%s'%phase,
                                              index=0,
                                              order=2,
                                              freq=self.pre_freq,
                                              force=True)
                        
                        kagralib.foton_comb(self.FBs,
                                            fotonQUAname+'_PLL_DEMOD_%s'%phase,
                                            index=1,
                                            freq=self.pre_freq,
                                            amplitude=-100,
                                            force=True)
                        edit_chans.append(QUAname+'_PLL_DEMOD_%s'%phase)
            
                    # PLL servo
                    kagralib.foton_gain(self.FBs,
                                        fotonQUAname+'_PLL_SERVO',
                                        index=0,
                                        gain=30*(self.pre_freq/3),
                                        force=True)
                    
                    kagralib.foton_zpk(self.FBs,
                                       fotonQUAname+'_PLL_SERVO',
                                       index=9,
                                       p=[0,],
                                       force=True)
                    kagralib.foton_zpk(self.FBs,
                                       fotonQUAname+'_PLL_SERVO',
                                       index=8,
                                       p=[0,],
                                       z=[0.01,],
                                       k=0.01,
                                       force=True)
                    edit_chans.append(QUAname+'_PLL_SERVO')
                    
                    if self.FB_load:
                        # config each FB
                        PLL_servo = ezca.get_LIGOFilter(QUAname+'_PLL_SERVO')
                        PLL_servo.only_on('OUTPUT','FM1','FM9','FM10','DECIMATION')
                        PLL_servo.ramp_gain(1,0,False)
                        
                        DEMOD_I = ezca.get_LIGOFilter(QUAname+'_PLL_DEMOD_I')
                        DEMOD_I.only_on('OUTPUT','FM1','FM2','DECIMATION','INPUT')
                        DEMOD_I.ramp_gain(1,0,False)
                        
                        DEMOD_Q = ezca.get_LIGOFilter(QUAname+'_PLL_DEMOD_Q')
                        DEMOD_Q.only_on('OUTPUT','FM2','DECIMATION','INPUT')
                        DEMOD_Q.ramp_gain(1,0,False)
                        
                        DEMOD_AMP = ezca.get_LIGOFilter(QUAname+'_PLL_DEMOD_AMP')
                        DEMOD_AMP.only_on('OUTPUT','FM1','FM2','DECIMATION','INPUT')
                        DEMOD_AMP.ramp_gain(1,0,False)
                        
                        DEMOD_SIG = ezca.get_LIGOFilter(QUAname+'_PLL_DEMOD_SIG')
                        DEMOD_SIG.only_on('OUTPUT','FM1','FM2','DECIMATION','INPUT')
                        DEMOD_SIG.ramp_gain(1,0,False)
                        
                        DEMOD_SIG_RMS = ezca.get_LIGOFilter(QUAname+'_PLL_DEMOD_SIG_RMS')
                        DEMOD_SIG_RMS.only_on('OUTPUT','FM1','FM2','DECIMATION','INPUT')
                        DEMOD_SIG_RMS.ramp_gain(np.sqrt(2),0,False)


                    ezca[QUAname+'_PLL_OSC_AMP'] = 1
                    self.FBs.write()
                    
            time.sleep(1)
            if int(ezca['FEC-%d_STATE_WORD'%sysmod.DCUID]) & 0b10000000000:
                ezca['FEC-%d_LOAD_NEW_COEFF'%sysmod.DCUID] = 1                    
            self.counter += 1

        elif self.counter == 1:
            for stage in ['IP','BF','MN','IM','TM']:
                for param in ['AMP','REF_PHASE','FREQ','Q_VAL','DECAY_TIME']:
                    for ii in range(6):
                        ezca['VIS-%s_%s_DOF_SEL_%s_1_%d'%(OPTIC,stage,param,ii+1)] = (DoFList[ii] == self.modeDoF)
            for param in ['REF_PHASE','FREQ','Q_VAL','DECAY_TIME']:
                for ii in range(5):
                    ezca['VIS-%s_STAGE_SEL_%s_1_%d'%(OPTIC,param,ii+1)] = (['IP','BF','MN','IM','TM'][ii] == self.modeStage)
            self.counter += 1
                
        elif self.counter == 2:
            if int(ezca['FEC-%d_STATE_WORD'%sysmod.DCUID]) & 0b10000000000:
                notify('Waiting to load coefficiencies!')
            else:
                self.counter += 1
                
        elif self.counter == 3:
            return True

class CLOSE_PLL(GuardState):
    index = 80
    request = True

    def is_PLL_locked(self):
        return True

    @check_mod_freq
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    @check_mod_freq
    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            for stage in ['IP','BF','MN','IM','TM']:
                for DoF in DoFList:
                    ezca.switch('VIS-%s_%s_QUA%s_PLL_SERVO'%(OPTIC,stage,DoF),'INPUT','OFF')
                    ezca['VIS-%s_%s_QUA%s_PLL_SERVO_RSET'%(OPTIC,stage,DoF)] = 2
                    time.sleep(.1)
                    ezca.switch('VIS-%s_%s_QUA%s_PLL_SERVO'%(OPTIC,stage,DoF),'INPUT','ON')

            self.timer['waiting'] = 2
            self.counter += 1

        elif self.counter == 1:
            return self.is_PLL_locked()
        

class EXCITE_RESONANCE(GuardState):
    index = 100
    request = True

    def is_EXC_enough(self):
        # Check SIG_RMS and compare with threshold. Then, how we can set good threshold?
        return True
    
    @check_mod_freq
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

        self.modeindex = ezca['QUA-%s_MODE_INDEX'%OPTIC]

        self.QUAEXC = ezca.get_LIGOFilter('VIS-ITMY_QUAEXC')


    @check_mod_freq
    def run(self):
        if not self.timer['waiting']:
            return
        
        self.modeDoF = ezca['VIS-%s_FREE_MODE_LIST_NO%d_DOF'%(OPTIC,self.modeindex)]
        
        if not self.modeDoF in DoFList:
            notify('Mode DoF is not defined propery. Please define it at VIS-%s_FREE_MODE_LIST_NO%d_DOF'%(OPTIC,self.modeindex))
            self.counter = 0
            return
            
        
        if self.counter == 0:
            for ii in range(6):
                ezca['VIS-%s_PAY_OLSERVO_PK2EUL_%d_26'%(OPTIC,4+ii)] = (self.modeDoF == DoFList[ii])
            self.counter += 2
            return

        
            self.QUAEXC.turn_on('INPUT','OUTPUT')
            self.QUAEXC.ramp_gain(1,2,False)
            self.timer['waiting'] = 10

        elif self.counter == 1:

            if self.is_EXC_enough():
                self.counter += 1
                self.QUAEXC.ramp_gain(0,2,False)
                self.timer['waiting'] = 2
            else:
                self.QUAEXC.ramp_gain(self.QUAEXC.GAIN.get()*3,2,False)
                self.timer['waiting'] = 10
                
        elif self.counter == 2:
            return True

class RECORD_MEASUREMENT(GuardState):
    index = 150
    request = True

    def mkdir(self,dirname):
        log(os.path.exists(dirname))
        if not os.path.exists(dirname):
            os.mkdir(dirname)

    #@check_mod_freq
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

        self.modeindex = ezca['QUA-%s_MODE_INDEX'%OPTIC]
        self.duration = 10./ezca['VIS-%s_PREQUA_DEMOD_FREQ'%OPTIC]

        # readback channel and record channel
        state = 'FREE'
        self.prefix = 'K1:VIS-%s_%s_MODE_LIST_NO%d_'%(OPTIC,state,self.modeindex)
        self.short_prefix = 'K1:VIS-%s_'%OPTIC
        self.chandict = {}
        self.freqchandict = {}
        for param in ['FREQ','Q_VAL','DECAY_TIME']:
            self.chandict[self.short_prefix+'PREQUA_%s_OUT_DQ'%param] = self.prefix+param
        
        for stage in ['IP','BF','MN','IM','TM']:
            for param in ['CP_COEF','REL_PHASE']:
                self.chandict[self.short_prefix+'%s_%s_OUT_DQ'%(param,stage)] = self.prefix+'%s_%s'%(param,stage)
                for DoF in DoFList:
                    self.chandict[self.short_prefix+'%s_%s_%s_OUTPUT'%(stage,param,DoF)] = self.prefix+'%s_%s_%s'%(stage,param,DoF)

        for stage in ['IP','BF','MN','IM','TM']:
            for DoF in DoFList:
                self.freqchandict[self.short_prefix+'%s_QUA%s_FREQ_OUTPUT'%(stage,DoF)] = '%s_%s'%(stage,DoF) #These are just identifier.

        _t = time.localtime()
        keys = ['YEAR','MON','DAY','HOUR','MIN','SEC']
        self.time = {
            keys[ii]:_t[ii] for ii in range(len(keys))
            }

        for key in ['YEAR','MON','DAY']:
            ezca[self.prefix[3:]+'MEAS_DATE_' + key] = self.time[key]

        # for plot
        self.figdir = '/users/Measurements/VIS/ITMY/PREQUA/mode%d/'%int(self.modeindex)
        self.figdir_archive = '/users/Measurements/VIS/ITMY/PREQUA/mode%d/archive/'%int(self.modeindex)

        self.mkdir(self.figdir)
        self.mkdir(self.figdir+'medm')
        self.mkdir(self.figdir_archive)

        self.fileprefix = '%s%s%s%s%s_'%(str(self.time['YEAR']),
                                         str(self.time['MON']).zfill(2),
                                         str(self.time['DAY']).zfill(2),
                                         str(self.time['HOUR']).zfill(2),
                                         str(self.time['MIN']).zfill(2))

        #initialize logger
        log_file = self.figdir_archive + self.fileprefix + 'measurement.log'
        
        self.logger=logging.getLogger('flogger')
        self.logger.setLevel(logging.DEBUG)
        handler=logging.StreamHandler()
        self.logger.addHandler(handler)
        handler=logging.FileHandler(filename=log_file)
        self.logger.addHandler(handler)


    #@check_mod_freq
    def run(self):
        if not self.timer['waiting']:
            return

        self.modeDoF = ezca['VIS-%s_FREE_MODE_LIST_NO%d_DOF'%(OPTIC,self.modeindex)]
        self.modeStage = ezca['VIS-%s_FREE_MODE_LIST_NO%d_PLL_SENS'%(OPTIC,self.modeindex)]

        
        if not self.modeDoF in DoFList:
            notify('Mode DoF is not defined propery. Please define it at VIS-%s_FREE_MODE_LIST_NO%d_DOF'%(OPTIC,self.modeindex))
            self.counter = 0
            return
        if not self.modeStage in ['IP','BF','MN','IM','TM']:
            notify('Mode refelence stage is not defined propery. Please define it at VIS-%s_FREE_MODE_LIST_NO%d_PLL_SENS'%(OPTIC,self.modeindex))
            self.counter = 0
            return

        if self.counter == 0:
            notify('start recording')

            # log date
            _keys = self.chandict.keys() + self.freqchandict.keys()
            _time = time.localtime()
            self.logger.debug('OPTIC: %s.'%OPTIC)                        
            self.logger.debug('Mode number: %d.'%self.modeindex)            
            self.logger.debug('start recording at %s/%s/%s %s:%s:%s.'%(str(_time[0]),str(_time[1]).zfill(2),str(_time[2]).zfill(2),str(_time[3]).zfill(2),str(_time[4]).zfill(2),str(_time[5]).zfill(2)))

            # measure and perse result
            _data = cdsutils.getdata(_keys,self.duration,)
            self.data = {
                _keys[ii]: _data[ii].data for ii in range(len(_keys))
                }
            self.tt = {
                _keys[ii]: 1/_data[ii].sample_rate * np.array(range(len(_data[ii].data))) for ii in range(len(_keys))
                }
            
            _time = time.localtime()
            self.logger.debug('finish recording at %s/%s/%s %s:%s:%s.'%(str(_time[0]),str(_time[1]).zfill(2),str(_time[2]).zfill(2),str(_time[3]).zfill(2),str(_time[4]).zfill(2),str(_time[5]).zfill(2)))
            self.counter += 1

        elif self.counter == 1:
            # put measurement record to EPICS channel
            for key in self.chandict.keys():
                ezca[self.chandict[key][3:]] = np.average(self.data[key])
            
            # wrap relative phase            
            for stage in ['IP','BF','MN','IM','TM']:
                ezca[self.prefix[3:]+'REL_PHASE_%s'%(stage)] = np.mod(ezca[self.prefix[3:]+'REL_PHASE_%s'%(stage)],-360)
                for DoF in DoFList:
                    ezca[self.prefix[3:]+'%s_REL_PHASE_%s'%(stage,DoF)] = np.mod(ezca[self.prefix[3:]+'%s_REL_PHASE_%s'%(stage,DoF)],-360)

            # log and check data quality
            #20200805 Akutsu added the following block
            #For evaluating the demod freqs of each DoF of each stage
            #And judge whether the stage's dof can be usable or not.
            self.freq_id_dict={}
            for key in self.freqchandict.keys():
                self.freq_id_dict[self.freqchandict[key]]={'mean': np.mean(self.data[key]),
                                                           'std': np.std(self.data[key]),
                                                           'bool': True}
            #Argorithm1: using mean of means.
            _mean_list =  [self.freq_id_dict[k]['mean'] for k in self.freq_id_dict]
            #_norm_std_list =  self.freq_id_dict[k]['std']/self.freq_id_dict[k]['mean'] for k in self.freq_id_dict]
            _mean_list_mean = np.mean(_mean_list)
            _mean_list_std = np.std(_mean_list)
            self.logger.debug('Resonant frequency:%f'%ezca['VIS-%s_FREE_MODE_LIST_NO%d_FREQ'%(OPTIC,self.modeindex)])
            self.logger.debug('Mean of resonant frequency of all QUADOF:%f'%_mean_list_mean)
            self.logger.debug('Std of resonant frequency of all QUADOF:%f'%_mean_list_std)
            for key in  self.freq_id_dict:
                qq1 =  self.freq_id_dict[key]
                if (qq1['mean'] > _mean_list_mean + _mean_list_std*3.) or (qq1['mean'] < _mean_list_mean - _mean_list_std*3. ):
                    qq1['bool'] = False
            #Argorithm2
            # Any nicer way to distinguish extraordinary values??

            for stage in ['IP','BF','MN','IM','TM']:
                for DoF in DoFList:
                    self.logger.debug('- %s %s'%(stage,DoF))
                    self.logger.debug('Coupling coefficient: %f'%(ezca[self.prefix[3:]+'CP_COEF_%s'%(stage)]))
                    self.logger.debug('Relative phase: %f'%(np.mod(ezca[self.prefix[3:]+'REL_PHASE_%s'%(stage)],-360)))                    
                    if not self.freq_id_dict['%s_%s'%(stage,DoF)]['bool']:
                        qq1 = ezca[self.prefix[3:]+'%s_CP_COEF_%s'%(stage,DoF)]
                        self.logger.debug('---------------------warning---------------------------')
                        self.logger.debug('%d Hz is out of the 3-sigma region of the distribtion of the means'%(qq1))
                        self.logger.debug('Put 0 as coupling coefficient and relative phase')
                        ezca[self.prefix[3:]+'%s_CP_COEF_%s'%(stage,DoF)] = 0.
                        ezca[self.prefix[3:]+'%s_REL_PHASE_%s'%(stage,DoF)] = 0.

                        


                
                    
            self.counter +=1
        
        elif self.counter == 2:
            # make plot
            fig = plt.figure()
            #for param in ['FREQ','Q_VAL','DECAY_TIME']:
            _keyfreq = self.short_prefix+'PREQUA_%s_OUT_DQ'%'FREQ'
            _keyQ = self.short_prefix+'PREQUA_%s_OUT_DQ'%'Q_VAL'
            ax1 = fig.add_subplot(2,1,1)
            ax1.plot(self.tt[_keyfreq],self.data[_keyfreq])
            ax1.set_ylabel('Frequency [Hz]')

            
            ax2 = fig.add_subplot(2,1,2)
            ax2.plot(self.tt[_keyQ],self.data[_keyQ])
            ax2.set_xlabel('time [sec]')
            ax2.set_ylabel('Q Value')

            fig.tight_layout()
            fig.savefig(self.figdir + 'MODE_PARAMS.png')
            fig.savefig(self.figdir_archive + self.fileprefix +  'MODE_PARAMS.png')
            
            os.system('convert %s %s'%(self.figdir + 'MODE_PARAMS.png',self.figdir + 'medm/MODE_PARAMS.gif'))

            # coupling coefficiency and relative phase
            plt.rcParams['font.size'] = 6

            for param in ['CP_COEF','REL_PHASE']:
                fig = plt.figure()
                ii = 0
                ax = []
                for stage in ['MN','IM','TM']:
                    for DoF in DoFList:
                        ax.append(fig.add_subplot(5,6,ii+1))
                        label = self.short_prefix+'%s_%s_%s_OUTPUT'%(stage,param,DoF)
                        ax[-1].plot(self.tt[label], self.data[label])
                        ax[-1].set_title('%s %s'%(stage,DoF),fontsize=6)

                        #remove xtick except for bottom line
                        if ii < 12:
                            ax[-1].tick_params(axis='x',          
                                               which='both',
                                               bottom=False,
                                               top=False,
                                               labelbottom=False)                        
                        ii += 1

                fig.suptitle("%s"%param)
                fig.savefig(self.figdir + '%s.png'%param)
                fig.savefig(self.figdir_archive + self.fileprefix + '%s.png'%param)

            # frequency in each QUADOF
            fig = plt.figure()
            ii = 0
            ax = []
            for stage in ['MN','IM','TM']:
                for DoF in DoFList:
                    ax.append(fig.add_subplot(5,6,ii+1))
                    label = self.short_prefix+'%s_QUA%s_FREQ_OUTPUT'%(stage,DoF)
                    ax[-1].plot(self.tt[label], self.data[label])
                    #remove xtick except for bottom line
                    if ii < 12:
                        ax[-1].tick_params(axis='x',          
                                           which='both',
                                           bottom=False,
                                           top=False,
                                           labelbottom=False)
                    ax[-1].set_title('%s %s'%(stage,DoF),fontsize=6)
                    ii += 1

            fig.suptitle("QUADOF frequencies")
            fig.savefig(self.figdir + 'QUADOF_frequencies.png')
            fig.savefig(self.figdir_archive + self.fileprefix + 'QUADOF_frequencies.png')
            os.system('cp %s %s/measurement.log'%(self.figdir_archive + self.fileprefix + 'measurement.log',self.figdir))

            self.counter += 1
            
        elif self.counter == 3:
            return True
                
class UPDATE_MODFREQ(GuardState):
    index = 200
    request = True

    def main(self):
        self.modeindex = ezca['QUA-%s_MODE_INDEX'%OPTIC]
        ezca['VIS-%s_FREE_MODE_LIST_NO%d_PRE_FREQ'%(OPTIC,self.modeindex)] = ezca['VIS-%s_FREE_MODE_LIST_NO%d_FREQ'%(OPTIC,self.modeindex)]

    def run(self):
        return True



class INIT_MODALDAMP(GuardState):
    index = 210
    request = True

    def main(self):
        self.state = 'FREE'
        self.DoFlist = {'TM':['LEN','PIT','YAW'],
                        'MN':['LEN','TRA','VER','ROL','PIT','YAW'],
                        'IM':['LEN','TRA','VER','ROL','PIT','YAW'],
                        'IP':['LEN','TRA','YAW'],
                        'BF':['LEN','TRA','VER','ROL','PIT','YAW'],
                    }
        self.modeindex = ezca['QUA-%s_MODE_INDEX'%OPTIC]
        self.prefix = 'MOD-%s_MODE%d_'%(OPTIC, self.modeindex)
        
        self.freq = ezca['VIS-%s_%s_MODE_LIST_NO%d_FREQ'%(OPTIC,self.state,self.modeindex)]
        self.Q = max(10,ezca['VIS-%s_%s_MODE_LIST_NO%d_Q_VAL'%(OPTIC,self.state,self.modeindex)])
        
        self.modeDoF = ezca['VIS-%s_FREE_MODE_LIST_NO%d_DOF'%(OPTIC,self.modeindex)]
        self.modestage = ezca['VIS-%s_FREE_MODE_LIST_NO%d_PLL_SENS'%(OPTIC,self.modeindex)]
        
        _degenerate = ezca['VIS-%s_FREE_MODE_LIST_NO%d_DEGEN_MODE'%(OPTIC,self.modeindex)].split(',')
        self.degenerate = []
        for modestr in _degenerate:
            try:
                self.degenerate.append(int(modestr))
            except:
                pass

        self.counter = 0
        self.timer['waiting'] = 0

    def run(self):
        if 'self' in ezca['VIS-%s_FREE_MODE_LIST_NO%d_USER_DESCRIPTION'%(OPTIC,self.modeindex)]:
            kagralib.speak_aloud('This filter is self designed. I don\'t change anyhing.')
            return True

        
        if not self.timer['waiting']:
            return
        
        if self.freq == 0:
            log( 'Measurement has not been done yet. Please ask PReQua to measure resonant frequency')
            return True

        if self.counter == 1:
            ezca['MOD-%s_MODE%d_ACT_FREQ'%(OPTIC, self.modeindex)] = self.freq
            ezca['MOD-%s_MODE%d_SENS_FREQ'%(OPTIC, self.modeindex)] = self.freq


            ii = 1
            for stage in ['IP','BF','MN','IM','TM']:
                for DoF in self.DoFlist[stage]:
                    if DoF == self.modeDoF:
                        ezca[self.prefix + 'ACT_PHASE_SHIFT_DEG_%d_1'%(ii)] = - ezca['VIS-%s_%s_MODE_LIST_NO%d_REL_PHASE_%s'%(OPTIC,self.state,self.modeindex,stage)]
                        ezca[self.prefix + 'ACT_VECTOR_%d_1'%(ii)] =  ezca['VIS-%s_%s_MODE_LIST_NO%d_CP_COEF_%s'%(OPTIC,self.state,self.modeindex,stage)] / sysmod.ACTRATIO[self.modeDoF][stage]
                    else:
                        ezca[self.prefix + 'ACT_PHASE_SHIFT_DEG_%d_1'%(ii)] = 0
                        ezca[self.prefix + 'ACT_VECTOR_%d_1'%(ii)] = 0
                    ii += 1
            ii = 1
            for stage in ['IP','BF','MN','IM','TM']:
                for DoF in DoFList:
                    if DoF == self.modeDoF and stage == self.modestage:
                        ezca[self.prefix + 'SENS_VECTOR_1_%d'%(ii)] = 1
                    else:
                        ezca[self.prefix + 'SENS_VECTOR_1_%d'%(ii)] = 0
                    ii += 1

            self.counter += 1

        elif self.counter == 0:
            SERVO = ezca.get_LIGOFilter(self.prefix+'SERVO')
            SERVO.ramp_gain(0,2,False)
            SERVO.turn_on('INPUT','OUTPUT','FM1','FM2','FM10')
            
            FBs = foton.FilterFile(chans+'K1MODAL%s.txt'%OPTIC)
            kagralib.foton_butter(FBs,'%s_MODE%d_SERVO'%(OPTIC, self.modeindex),Type='BandPass',index=1,order=3,freq=self.freq-self.freq/(self.Q/30),freq2=self.freq+self.freq/(self.Q/30),force=True)
            kagralib.foton_zpk(FBs,'%s_MODE%d_SERVO'%(OPTIC, self.modeindex),index=0,z=[0,],p=[self.freq*10],k=-1)

            _notchdesign = ''
            if len(self.degenerate) > 0:
                for mode in self.degenerate:
                    notchfreq = ezca['VIS-%s_FREE_MODE_LIST_NO%d_PRE_FREQ'%(OPTIC,mode)]
                    if notchfreq > 0:
                        _notchdesign += kagralib.foton_notch(FBs,
                                                            '%s_MODE%d_SERVO'%(OPTIC, self.modeindex),
                                                            index=2,
                                                            Q=100,
                                                            attenuation=100,
                                                            freq=notchfreq,
                                                            force=True)
                kagralib.foton_design(FBs,
                                      '%s_MODE%d_SERVO'%(OPTIC, self.modeindex),
                                      2,
                                      _notchdesign,
                                      'notch',
                                      force=True)

            FBs.write()
            ezca[self.prefix+'SERVO_RSET'] = 1
            self.counter += 1



        elif self.counter == 2:
            return True

class SENSOR_DIAGONALIZATION(GuardState):
    index = 250
    request = True

    def calc_major_axis(self,A,B,theta):
        # calc major axis of elliptic described as x = A*cos(t), y = B*cos(t+theta)
        # 2020/08/02 by MN
        # calculate t which X = x**2 + y**2 got maximum.
        # dX/dt =  a*sin(2t)+b*cos(2t) = sqt(a**2+b**2)*sin(2t+alpha) = 0,
        # where a, b and alpha is drived as below.
        # major axis can be derived as x = A*cos(-alpha/2), y = B*cos(-alpha/2+theta)
    
        a = (A**2+B**2*np.cos(2*theta))
        b = B**2*np.sin(2*theta)
        alpha = np.arcsin(b/np.sqrt(a**2+b**2))
        
        x = A*np.cos(-alpha/2)
        y = B*np.cos(-alpha/2+theta)
        
        return x,y

    def calc_SENSDIAG_matrix(self,stage):
        _t_sensing_matrix = np.identity(len(DoFList))
        ii = 0
        for motion_DoF in DoFList:
            _sensing_vector = []
            _A = ezca['VIS-%s_SENDIAG_%s_%s_CP_COEF_%s'%(OPTIC,motion_DoF,stage,motion_DoF)]
            _theta_a = ezca['VIS-%s_SENDIAG_%s_%s_REL_PHASE_%s'%(OPTIC,motion_DoF,stage,motion_DoF)]
            if _A == 0:
                log('skip this DoF')
                
            else:
                for sensor_DoF in DoFList:
                    _B = ezca['VIS-%s_SENDIAG_%s_%s_CP_COEF_%s'%(OPTIC,motion_DoF,stage,sensor_DoF)]
                    _theta_b = ezca['VIS-%s_SENDIAG_%s_%s_REL_PHASE_%s'%(OPTIC,motion_DoF,stage,sensor_DoF)]

                    _theta = (_theta_a - _theta_b)/180*np.pi
                    
                    _AA,_BB = self.calc_major_axis(_A,_B,_theta)
                    _sensing_vector.append(_BB/_AA)
                    if abs(_sensing_vector[-1]) < 1e-3:
                        _sensing_vector[-1] = 0

                _t_sensing_matrix[ii] = _sensing_vector
                
            ii += 1
        sensing_matrix = np.transpose(_t_sensing_matrix)
        _diag_matrix = np.linalg.inv(sensing_matrix)
        
        for ii in range(len(_diag_matrix)):
            _diag_matrix[ii] = _diag_matrix[ii]/np.sqrt(np.sum(_diag_matrix[ii]**2))
        return _diag_matrix


    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    def run(self):
        if self.counter == 0:
            DECPL = {stage:cdsutils.CDSMatrix(
                'VIS-%s_%s_DIAG_DECPL'%(OPTIC,stage),
                cols={ii+1: ii+1 for ii in range(6)},
                rows={ii+1: ii+1 for ii in range(6)},                
            ) for stage in ['IP','BF','MN','IM','TM']}
            
            for stage in ['MN','IM','TM']:
                DECPL[stage].put_matrix(DECPL[stage].get_matrix() * self.calc_SENSDIAG_matrix(stage))
            self.counter += 1

        else:
            return True
                

            
        
    
##################################################
# EDGES
##################################################

edges = [('INIT','STANDBY'),
         ('STANDBY','INIT_DIAG'),
         ('STANDBY','INIT_PREQUA'),
         ('INIT_PREQUA','CLOSE_PLL'),
         ('CLOSE_PLL','EXCITE_RESONANCE'),
         ('EXCITE_RESONANCE','INIT_MODALDAMP'),
         ('INIT_MODALDAMP','STANDBY'),
         ('EXCITE_RESONANCE','RECORD_MEASUREMENT'),
         ('RECORD_MEASUREMENT','UPDATE_MODFREQ'),
         ('UPDATE_MODFREQ','EXCITE_RESONANCE'),
]
