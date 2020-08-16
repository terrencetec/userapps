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

##################################################
# Filter configuation
##################################################
# frequency of BLP at SENSIN
SENSIN_LPfreq = {'IP':10,'BF':1,'MN':100,'IM':100,'TM':100} 

# gain for damping filter
DAMP_gain = {'IP':[3,3,0,0,0,1],'BF':[0,0,0,0,0,30],'MN':[0,0,0,0,0,0],'IM':[0,0,0,0,0,0],'TM':[0,0,0,0,0,0],'GAS':[1,1,1,1,1]}

# rolloff frequency for damping filter. Naively speaking, it should be around the highest resonance you want damp.
DAMP_ROLLOFFfreq = {'IP':[1,1,1,1,1,1],'BF':[0.1,0.1,0.1,0.1,0.1,0.1],'MN':[3,3,3,3,3,3],'IM':[3,3,3,3,3,3],'TM':[3,3,3,3,3,3],'GAS':[1,1,1,1,1,]}


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
        pass
        '''
        modeindex = ezca['QUA-%s_MODE_INDEX'%OPTIC]

        try:
            if not ezca['VIS-%s_PREQUA_DEMOD_FREQ'%(OPTIC)] == ezca['VIS-%s_FREE_MODE_LIST_NO%d_PRE_FREQ'%(OPTIC,modeindex)]:
                log('Measurement mode index has been changed. Initialize PReQua')
                return 'INIT_PREQUA'

        except:
            log('Measurement mode index has been changed. Initialize PReQua')
            return 'INIT_PREQUA'
        '''



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
    goto = True
    def main(self):
        return True



class INIT_SIGNAL_PROC(GuardState):
    index = 10
    request = True

             
    def main(self):
        
        self.TOWER_FBs = foton.FilterFile(chans+'K1VIS%sT.txt'%(OPTIC.upper()))
        self.PAYLOAD_FBs = foton.FilterFile(chans+'K1VIS%sP.txt'%(OPTIC.upper()))
        self.QUA_FBs = foton.FilterFile(chans+'K1VIS%sMON.txt'%(OPTIC.upper()))
        self.MODAL_FBs = foton.FilterFile(chans+'K1MODAL%s.txt'%(OPTIC.upper()))
        
        # Initialize OL_PROC
        OL_DoFs = ['PIT','YAW','SUM','CROSS']
        for oplev in ['TM_LEN','TM_TILT','MN_TILT']:
            stage, ol = oplev.split('_')

            kagralib.foton_butter(self.QUA_FBs,'%s_DIAG_OL_PROC_%s_SUM'%(OPTIC,oplev),0,freq = 1, force = True)
            ezca.switch('MOD-%s_DIAG_OL_PROC_%s_SUM'%(OPTIC,oplev),'FM1','ON')
            ezca.switch('VIS-%s_DIAG_OL_PROC_%s_SUM'%(OPTIC,oplev),'FM1','ON')
            for ii in range(4):
                kagralib.copy_FB('VIS',self.PAYLOAD_FBs,'%s_%s_OPLEV_%s_SEG%d'%(OPTIC,stage,ol,ii+1),'VIS',self.QUA_FBs,'%s_DIAG_OL_PROC_%s_SEG%d'%(OPTIC,oplev,ii+1))
                kagralib.copy_FB('VIS',self.PAYLOAD_FBs,'%s_%s_OPLEV_%s_SEG%d'%(OPTIC,stage,ol,ii+1),'MOD',self.MODAL_FBs,'%s_DIAG_OL_PROC_%s_SEG%d'%(OPTIC,oplev,ii+1))

            for model in ['VIS','MOD']:
                OL2EUL = cdsutils.CDSMatrix(
                    '%s-%s_DIAG_OL_PROC_%s_MTRX'%(model,OPTIC,oplev),
                    cols={ii+1: 'SEG%d'%(ii+1) for ii in range(4)},
                    rows={ii+1: OL_DoFs[ii] for ii in range(4)},
                )
                OL2EUL.put_matrix(np.matrix(
                    [[-1,-1,1,1],
                     [1,-1,-1,1],
                     [1,1,1,1],
                     [1,-1,1,-1]]
                ))
            
        # Initialize SENSIN for each sensor

        for stage in ['IP','BF','MN','IM','TM']:
            for sensor in ['H1','H2','H3','V1','V2','V3']:
                kagralib.foton_comb(self.QUA_FBs,'%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),0,freq=60,Q=100,amplitude=-100,force=True)
                kagralib.foton_butter(self.QUA_FBs,'%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),1,freq=SENSIN_LPfreq[stage],order=3,force=True)
                kagralib.foton_comb(self.MODAL_FBs,'%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),0,freq=60,Q=100,amplitude=-100,force=True)
                kagralib.foton_butter(self.MODAL_FBs,'%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),1,freq=SENSIN_LPfreq[stage],order=3,force=True)

                if stage in ['MN','IM']:
                    kagralib.foton_zpk(self.QUA_FBs,'%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),2,z=[12.3,],p=[0.46,],k=1,name='de-white',force=True)
                    kagralib.foton_zpk(self.MODAL_FBs,'%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),2,z=[12.3,],p=[0.46,],k=1,name='de-white',force=True)

                ezca.switch('VIS-%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),'FM1','FM2','FM3','ON')
                ezca.switch('MOD-%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),'FM1','FM2','FM3','ON')
                
        # GAS SENSIN
        for sensor in ['F0','F1','F2','F3','BF']:
            kagralib.foton_butter(self.QUA_FBs,'%s_DIAG_SENSIN_GAS_%s'%(OPTIC,sensor),1,freq=10,order=3,force=True)
            kagralib.foton_butter(self.MODAL_FBs,'%s_DIAG_SENSIN_GAS_%s'%(OPTIC,sensor),1,freq=10,order=3,force=True)
            kagralib.foton_comb(self.QUA_FBs,'%s_DIAG_SENSIN_GAS_%s'%(OPTIC,sensor),0,freq=28,harmonics=10,Q=100,amplitude=-100,force=True)
            kagralib.foton_comb(self.MODAL_FBs,'%s_DIAG_SENSIN_GAS_%s'%(OPTIC,sensor),0,freq=28,harmonics=10,Q=100,amplitude=-100,force=True)
            ezca.switch('VIS-%s_DIAG_SENSIN_GAS_%s'%(OPTIC,sensor),'FM1','FM2','FM3','ON')
            ezca.switch('MOD-%s_DIAG_SENSIN_GAS_%s'%(OPTIC,sensor),'FM1','FM2','FM3','ON')


        self.QUA_FBs.write()
        self.MODAL_FBs.write()

        for model in ['VIS','MOD']:        
            # Initialize SEN2EUL if mtrx_lock is false
            DIAG_SEN2EUL = {stage:cdsutils.CDSMatrix(
                '%s-%s_DIAG_SEN2EUL_%s'%(model,OPTIC,stage),
                cols={ii+1: ii+1 for ii in range(6)},
                rows={ii+1: ii+1 for ii in range(6)},
            ) for stage in ['IP','BF','MN','IM','TM']}

            if not ezca['VIS-%s_MTRX_LOCK_IP'%OPTIC]:
                DIAG_SEN2EUL['IP'].put_matrix(
                    np.matrix([[0,0,0,2./3.,-1./3.,-1./3.],
                               [0,0,0,0,-1./np.sqrt(3),1./np.sqrt(3)],
                               [0,0,0,0,0,0],
                               [0,0,0,0,0,0],
                               [0,0,0,0,0,0],
                               [0,0,0,1./np.sqrt(3),1./np.sqrt(3),1./np.sqrt(3)]]
                          ))
                
            if not ezca['VIS-%s_MTRX_LOCK_BF'%OPTIC]:
                DIAG_SEN2EUL['BF'].put_matrix(
                    np.matrix([[0,0,0,2./3.,-1./3.,-1./3.],
                               [0,0,0,0,-1./np.sqrt(3),1./np.sqrt(3)],
                               [1./3.,1./3.,1./3.,0,0,0],
                               [-0.9157,-0.9157,1.83150,0,0,0],
                               [-1.5861,1.5861,0,0,0,0],
                               [0,0,0,0.8170,0.8170,0.8170]]
                          ))
            

            for stage in ['IM','MN']:
                if not ezca['VIS-%s_MTRX_LOCK_%s'%(OPTIC,stage)]:                    
                    DIAG_SEN2EUL[stage].put_matrix(
                        np.matrix([[0,0,0,1./2.,1./2.,0],
                                   [0,0,0,-1./2.,1./2.,1],
                                   [-1./2.,0,-1./2.,0,0,0],
                                   [1./2.,-1,1./2.,0,0,0],
                                   [1./2.,0,-1./2.,0,0,0],
                                   [0,0,0,1./2.,-1./2.,0]]
                              ))
                
                
            if not ezca['VIS-%s_MTRX_LOCK_TM'%OPTIC]:
                DIAG_SEN2EUL['TM'].put_matrix(
                    np.matrix([[0,0,0,0,1,0],
                               [0,0,0,0,0,0],
                               [0,0,0,0,0,0],
                               [0,0,0,0,0,0],
                               [1,0,0,0,0,0],
                               [0,0,0,1,0,0],]
                          ))

            # Initialize GAS SEN2EUL if mtrx_lock is false
            DIAG_SEN2EUL_GAS = cdsutils.CDSMatrix(
                '%s-%s_DIAG_SEN2EUL_GAS'%(model,OPTIC),
                cols={ii+1: ii+1 for ii in range(5)},
                rows={ii+1: ii+1 for ii in range(5)},
            )
            
            if not ezca['VIS-%s_MTRX_LOCK_GAS'%OPTIC]:
                DIAG_SEN2EUL_GAS.put_matrix(np.matrix(np.identity(5)))

                

            # Initialize DECPL
            DIAG_DECPL = {stage:cdsutils.CDSMatrix(            
                '%s-%s_DIAG_DECPL_%s'%(model,OPTIC,stage),
                cols={ii+1: ii+1 for ii in range(6)},
                rows={ii+1: ii+1 for ii in range(6)},
            ) for stage in ['IP','BF','MN','IM','TM']}
            
            DIAG_DECPL_GAS = cdsutils.CDSMatrix(            
                '%s-%s_DIAG_DECPL_GAS'%(model,OPTIC),
                cols={ii+1: ii+1 for ii in range(5)},
                rows={ii+1: ii+1 for ii in range(5)},
            )

            for stage in ['IP','BF','MN','IM','TM']:
                if not ezca['VIS-%s_MTRX_LOCK_%s'%(OPTIC,stage)]:
                    DIAG_DECPL[stage].put_matrix(np.matrix(np.identity(6)))
            if not ezca['VIS-%s_MTRX_LOCK_GAS'%(OPTIC)]:
                DIAG_DECPL_GAS.put_matrix(np.matrix(np.identity(5)))

            
            for key in sysmod.initDECPL.keys():
                if not ezca['VIS-%s_MTRX_LOCK_%s'%(OPTIC,key)]:
                    DIAG_DECPL[key].put_matrix(np.matrix(sysmod.initDECPL[key]))
                
        if int(ezca['FEC-%d_STATE_WORD'%sysmod.MONDCUID]) & 0b10000000000:
            ezca['FEC-%d_LOAD_NEW_COEFF'%sysmod.MONDCUID] = 1
        if int(ezca['FEC-%d_STATE_WORD'%sysmod.MODALDCUID]) & 0b10000000000:
            ezca['FEC-%d_LOAD_NEW_COEFF'%sysmod.MODALDCUID] = 1


        
    def run(self):
        if (int(ezca['FEC-%d_STATE_WORD'%sysmod.MONDCUID]) & 0b10000000000 or int(ezca['FEC-%d_STATE_WORD'%sysmod.MODALDCUID]) & 0b10000000000):
            notify('Waiting to load coefficients!')
        else:
            return True
    
class ZERO_SENSOFS(GuardState):
    index = 15
    request = True
    goto = True

    def main(self):
        log('zero offset')
        darkchans = ['K1:%s-%s_DIAG_SENSIN_%s_%s_INMON'%(model,OPTIC,stage,sensor) for model in ['MOD','VIS']for stage in ['BF','MN','IM'] for sensor in ['V1','V2','V3','H1','H2','H3']]
        _data = cdsutils.getdata(darkchans,10)
        dark = {darkchans[ii]:np.average(_data[ii].data) for ii in range(len(darkchans))}
        for stage in ['BF','MN','IM']:
            for sensor in ['V1','V2','V3','H1','H2','H3']:
                for model in ['MOD','VIS']:
                    ezca['%s-%s_DIAG_SENSIN_%s_%s_OFFSET'%(model,OPTIC,stage,sensor)] = -dark['K1:%s-%s_DIAG_SENSIN_%s_%s_INMON'%(model,OPTIC,stage,sensor)]
                
                    ezca.switch('%s-%s_DIAG_SENSIN_%s_%s'%(model,OPTIC,stage,sensor),'OFFSET','ON')

    def run(self):
        return True

class ZERO_IP_SENSOFS(GuardState):
    index = 16
    request = True
    goto = True

    def main(self):
        log('zero offset')
        darkchans = ['K1:%s-%s_DIAG_SENSIN_%s_%s_INMON'%(model,OPTIC,stage,sensor) for model in ['MOD','VIS']for stage in ['IP'] for sensor in ['V1','V2','V3','H1','H2','H3']]
        _data = cdsutils.getdata(darkchans,10)
        dark = {darkchans[ii]:np.average(_data[ii].data) for ii in range(len(darkchans))}
        for stage in ['IP']:
            for sensor in ['V1','V2','V3','H1','H2','H3']:
                for model in ['MOD','VIS']:
                    ezca['%s-%s_DIAG_SENSIN_%s_%s_OFFSET'%(model,OPTIC,stage,sensor)] = -dark['K1:%s-%s_DIAG_SENSIN_%s_%s_INMON'%(model,OPTIC,stage,sensor)]
                
                    ezca.switch('%s-%s_DIAG_SENSIN_%s_%s'%(model,OPTIC,stage,sensor),'OFFSET','ON')

    def run(self):
        return True
    
class ZERO_GAS_SENSOFS(GuardState):
    index = 17
    request = True
    goto = True

    def main(self):
        log('zero offset')
        darkchans = ['K1:%s-%s_DIAG_SENSIN_%s_%s_INMON'%(model,OPTIC,stage,sensor) for model in ['MOD','VIS']for stage in ['GAS'] for sensor in ['F0','F1','F2','F3','BF']]
        _data = cdsutils.getdata(darkchans,10)
        dark = {darkchans[ii]:np.average(_data[ii].data) for ii in range(len(darkchans))}
        for stage in ['GAS']:
            for sensor in ['F0','F1','F2','F3','BF']:
                for model in ['MOD','VIS']:
                    ezca['%s-%s_DIAG_SENSIN_%s_%s_OFFSET'%(model,OPTIC,stage,sensor)] = -dark['K1:%s-%s_DIAG_SENSIN_%s_%s_INMON'%(model,OPTIC,stage,sensor)]
                
                    ezca.switch('%s-%s_DIAG_SENSIN_%s_%s'%(model,OPTIC,stage,sensor),'OFFSET','ON')

    def run(self):
        return True

class INIT_OUTPUT(GuardState):
    index = 20
    request = True
    goto = True

    def main(self):
        self.TOWER_FBs = foton.FilterFile(chans+'K1VIS%sT.txt'%(OPTIC.upper()))
        self.PAYLOAD_FBs = foton.FilterFile(chans+'K1VIS%sP.txt'%(OPTIC.upper()))
        self.QUA_FBs = foton.FilterFile(chans+'K1VIS%sMON.txt'%(OPTIC.upper()))
        self.MODAL_FBs = foton.FilterFile(chans+'K1MODAL%s.txt'%(OPTIC.upper()))
        
        
        self.timer['waiting'] = 0
        self.counter = 0

    def run(self):
        if not self.timer['waiting']:
            return

        if not ezca['GRD-NEW_%s_STATE'%OPTIC] == 'SAFE':
            kagralib.speak_aloud('Guardian need to be in safe state.')
            notify('Guardian need to be in safe state.')
            return

        if self.counter == 0:
            for stage in ['IP','BF','MN','IM','TM']:
                DoFindex = 0
                for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']:
                    if stage in ['IP','BF']:
                        FBs = self.TOWER_FBs
                    else:
                        FBs = self.PAYLOAD_FBs
                    
                    # Initialize anti-imaging filter                    
                    kagralib.foton_comb(FBs,'MOD_%s_AI_%s_%s'%(OPTIC,stage,DoF),0,freq=128,Q=10,amplitude=-100,harmonics=4,force=True)
                    kagralib.foton_ELP(FBs,'MOD_%s_AI_%s_%s'%(OPTIC,stage,DoF),1,freq=128,force=True)
                    ezca.switch('MOD-%s_AI_%s_%s'%(OPTIC,stage,DoF),'FM1','FM2','ON',)

                    # Initialize damping
                    kagralib.foton_gain(self.MODAL_FBs,'%s_DAMP_%s_%s'%(OPTIC,stage,DoF),0,-1)
                    kagralib.foton_zpk(self.MODAL_FBs,'%s_DAMP_%s_%s'%(OPTIC,stage,DoF),1,z=[0,],p=[DAMP_ROLLOFFfreq[stage][DoFindex],],k=DAMP_gain[stage][DoFindex],force=True)
                    ezca['MOD-%s_DAMP_%s_%s_GAIN'%(OPTIC,stage,DoF)] = 0
                    ezca.switch('MOD-%s_DAMP_%s_%s'%(OPTIC,stage,DoF),'FM1','FM2','ON')
                    DoFindex += 1

            DoFindex = 0
            for DoF in ['M%d'%ii for ii in range(1,6)]:
                stage = 'GAS'

                # Initialize anti-imaging filter for GAS                
                FBs = self.MODAL_FBs
                kagralib.foton_comb(FBs,'%s_AI_%s_%s'%(OPTIC,stage,DoF),0,freq=128,Q=10,amplitude=-100,harmonics=4,force=True)
                kagralib.foton_ELP(FBs,'%s_AI_%s_%s'%(OPTIC,stage,DoF),1,freq=128,force=True)
                ezca.switch('MOD-%s_AI_%s_%s'%(OPTIC,stage,DoF),'FM1','FM2','ON',)
                # Initialize damping
                kagralib.foton_gain(self.MODAL_FBs,'%s_DAMP_%s_%s'%(OPTIC,stage,DoF),0,-1)
                kagralib.foton_zpk(self.MODAL_FBs,'%s_DAMP_%s_%s'%(OPTIC,stage,DoF),1,z=[0,],p=[DAMP_ROLLOFFfreq[stage][DoFindex],],k=DAMP_gain[stage][DoFindex],force=True)
                ezca['MOD-%s_DAMP_%s_%s_GAIN'%(OPTIC,stage,DoF)] = 0
                ezca.switch('MOD-%s_DAMP_%s_%s'%(OPTIC,stage,DoF),'FM1','FM2','ON')
                DoFindex += 1


            self.counter += 1

        elif self.counter == 1:
            # OLDC initialization
            for DoF in ['PIT','YAW']:
                ezca['MOD-%s_OLDC_SETPOINT_%s_TRAMP'%(OPTIC,DoF)] = 0.5
                ezca.switch('MOD-%s_OLDC_SETPOINT_%s'%(OPTIC,DoF),'OFFSET','ON')
            
                kagralib.foton_zpk(self.MODAL_FBs,'%s_OLDC_MN_%s'%(OPTIC,DoF),9,z=[],p=[0,],k=1,force=True)
                kagralib.foton_gain(self.MODAL_FBs,'%s_OLDC_MN_%s'%(OPTIC,DoF),0,0.01,name='0.01Hz',force=True)
                kagralib.foton_gain(self.MODAL_FBs,'%s_OLDC_MN_%s'%(OPTIC,DoF),1,0.1,name='0.1Hz',force=True)
                kagralib.foton_gain(self.MODAL_FBs,'%s_OLDC_MN_%s'%(OPTIC,DoF),8,-1,force=True)
                
                kagralib.foton_zpk(self.MODAL_FBs,'%s_OLDC_BF_%s'%(OPTIC,DoF),9,z=[],p=[0,],k=1,force=True)
                kagralib.foton_gain(self.MODAL_FBs,'%s_OLDC_BF_%s'%(OPTIC,DoF),0,0.001,'1mHz',force=True)

                MN = ezca.get_LIGOFilter('MOD-%s_OLDC_MN_%s'%(OPTIC,DoF))
                BF = ezca.get_LIGOFilter('MOD-%s_OLDC_BF_%s'%(OPTIC,DoF))
                if MN.OUTPUT.get() or BF.OUTPUT.get():
                    kagralib.speak_aloud('There is output in M N or B F D C loop. please check it.')
                    return
                MN.turn_off('INPUT','OFFSET')
                MN.turn_on('FM1','FM9','FM10')
                MN.RSET.put(2)
                time.sleep(0.3)
                MN.ramp_gain(1,0,False)
                BF.turn_off('INPUT','OFFSET')
                BF.turn_on('FM1','FM10')
                BF.RSET.put(2)
                time.sleep(0.3)
                BF.ramp_gain(1,0,False)

            self.counter += 1

        elif self.counter == 2:

            # IPDC initialization
            for DoF in ['LEN','TRA','YAW']:
                ezca['MOD-%s_IPDC_SETPOINT_%s_TRAMP'%(OPTIC,DoF)] = 0.5
                ezca.switch('MOD-%s_IPDC_SETPOINT_%s'%(OPTIC,DoF),'OFFSET','ON')
            
                kagralib.foton_zpk(self.MODAL_FBs,'%s_IPDC_%s'%(OPTIC,DoF),9,z=[],p=[0,],k=1,force=True)
                kagralib.foton_gain(self.MODAL_FBs,'%s_IPDC_%s'%(OPTIC,DoF),0,0.001,name='1mHz',force=True)
                kagralib.foton_gain(self.MODAL_FBs,'%s_IPDC_%s'%(OPTIC,DoF),1,0.01,name='10mHz',force=True)
                kagralib.foton_gain(self.MODAL_FBs,'%s_IPDC_%s'%(OPTIC,DoF),8,-1,force=True)

                ezca.switch('MOD-%s_IPDC_%s'%(OPTIC,DoF),'FM2','FM9','FM10','ON','INPUT','OFF')
                if ezca['MOD-%s_IPDC_%s_OUTPUT'%(OPTIC,DoF)]:
                    kagralib.speak_aloud('There is output in I P D C loop. please check it.')
                    return
                ezca['MOD-%s_IPDC_%s_RSET'%(OPTIC,DoF)] = 2
                time.sleep(0.3)
                ezca['MOD-%s_IPDC_%s_GAIN'%(OPTIC,DoF)] = 1
            self.counter += 1

        elif self.counter == 3:
            # GASDC initialization
            for DoF in ['F0','F1','F2','F3','BF']:
                ezca['MOD-%s_GASDC_SETPOINT_%s_TRAMP'%(OPTIC,DoF)] = 0.5
                ezca.switch('MOD-%s_GASDC_SETPOINT_%s'%(OPTIC,DoF),'OFFSET','ON')
                kagralib.foton_zpk(self.MODAL_FBs,'%s_GASDC_%s'%(OPTIC,DoF),9,z=[],p=[0,],k=1,force=True)
                kagralib.foton_gain(self.MODAL_FBs,'%s_GASDC_%s'%(OPTIC,DoF),0,0.001,name='1mHz',force=True)
                kagralib.foton_gain(self.MODAL_FBs,'%s_GASDC_%s'%(OPTIC,DoF),1,0.01,name='10mHz',force=True)
                kagralib.foton_gain(self.MODAL_FBs,'%s_GASDC_%s'%(OPTIC,DoF),8,-1,force=True)
                
                ezca.switch('MOD-%s_GASDC_%s'%(OPTIC,DoF),'FM2','FM9','FM10','ON','INPUT','OFF')
                if ezca['MOD-%s_GASDC_%s_OUTPUT'%(OPTIC,DoF)]:
                    kagralib.speak_aloud('There is output in GAS D C loop. please check it.')
                    return
                ezca['MOD-%s_GASDC_%s_RSET'%(OPTIC,DoF)] = 2
                time.sleep(0.3)
                ezca['MOD-%s_GASDC_%s_GAIN'%(OPTIC,DoF)] = 1
            self.counter += 1

        elif self.counter == 4:
            self.MODAL_FBs.write()
            self.TOWER_FBs.write()
            self.PAYLOAD_FBs.write()

            # Output matrices initialization
            DECPL = {stage:cdsutils.CDSMatrix(            
                'MOD-%s_DRIVEDECPL_%s'%(OPTIC,stage),
                cols={ii+1: ii+1 for ii in range(6)},
                rows={ii+1: ii+1 for ii in range(6)},
            ) for stage in ['IP','BF','MN','IM','TM']}

            for stage in DECPL.keys():
                if not ezca['VIS-%s_MTRX_LOCK_%s'%(OPTIC,stage)]:
                    DECPL[stage].put_matrix(
                        np.identity(6)
                    )

            if not ezca['VIS-%s_MTRX_LOCK_%s'%(OPTIC,'GAS')]:
                MOD_DECPL_GAS = cdsutils.CDSMatrix(            
                    'MOD-%s_DRIVEDECPL_GAS'%(OPTIC,),
                    cols={ii+1: ii+1 for ii in range(5)},
                    rows={ii+1: ii+1 for ii in range(5)},
                )

                MOD_DECPL_GAS.put_matrix(np.matrix(np.identity(5)))
                
            MOD_EUL2COIL = {stage:cdsutils.CDSMatrix(            
                'MOD-%s_EUL2COIL_%s'%(OPTIC,stage),
                cols={ii+1: ii+1 for ii in range(6)},
                rows={ii+1: ii+1 for ii in range(6)},
            ) for stage in ['IP','BF','MN','IM','TM']}
            
            if not ezca['VIS-%s_MTRX_LOCK_IP'%OPTIC]:        
                MOD_EUL2COIL['IP'].put_matrix(
                    np.matrix([[0,0,0,0,0,0,],
                               [0,0,0,0,0,0,],
                               [0,0,0,0,0,0,],
                               [2./3.,0,0,0,0,1/np.sqrt(3)],
                               [-1./3.,-1./np.sqrt(3),0,0,0,1./np.sqrt(3)],
                               [-1./3.,1/np.sqrt(3),0,0,0,1./np.sqrt(3)]]
                          ))
            if not ezca['VIS-%s_MTRX_LOCK_BF'%OPTIC]:
                MOD_EUL2COIL['BF'].put_matrix(
                    np.matrix([[0,0,1,-0.182,-0.3152,0],
                               [0,0,1,-0.182,0.3152,0],
                               [0,0,1,0.364,0,0],
                               [1,0,0,0,0,0.408],
                               [-0.5,-0.866,0,0,0,0.408],
                               [-0.5,0.866,0,0,0,0.408]]
                          ))
                

            for stage in ['IM','MN']:
                if not ezca['VIS-%s_MTRX_LOCK_%s'%(OPTIC,stage)]:
                    MOD_EUL2COIL[stage].put_matrix(
                        np.matrix([[0,0,0.5,-0.5,-0.5,0],
                                   [0,0,0,1,0,0],
                                   [0,0,0.5,-0.5,0.5,0],
                                   [-0.5,0.5,0,0,0,-0.5],
                                   [-0.5,-0.5,0,0,0,0.5],
                                   [0,-1,0,0,0,0]]
                              ))
                
            if not ezca['VIS-%s_MTRX_LOCK_%s'%(OPTIC,'TM')]:
                MOD_EUL2COIL_TM = cdsutils.CDSMatrix(            
                    'MOD-%s_EUL2COIL_TM'%(OPTIC,),
                    cols={ii+1: ii+1 for ii in range(6)},
                    rows={ii+1: ii+1 for ii in range(4)},
                )
                
                MOD_EUL2COIL_TM.put_matrix(
                    np.matrix([[1,0,0,0,1,0],
                               [1,0,0,0,-1,0],
                               [1,0,0,0,0,-1],
                               [1,0,0,0,0,1]],
                          ))
            
            if not ezca['VIS-%s_MTRX_LOCK_%s'%(OPTIC,'GAS')]:
                MOD_EUL2COIL_GAS = cdsutils.CDSMatrix(            
                    'MOD-%s_EUL2COIL_GAS'%(OPTIC,),
                    cols={ii+1: ii+1 for ii in range(5)},
                    rows={ii+1: ii+1 for ii in range(5)},
                )

                
                MOD_EUL2COIL_GAS.put_matrix(np.matrix(np.identity(5)))
            
            for dcuid in [sysmod.MONDCUID,sysmod.MODALDCUID,sysmod.PDCUID,sysmod.TDCUID]:
                if int(ezca['FEC-%d_STATE_WORD'%dcuid]) & 0b10000000000:
                    ezca['FEC-%d_LOAD_NEW_COEFF'%dcuid] = 1

            self.counter += 1
            
        elif self.counter == 5:
            if any([int(ezca['FEC-%d_STATE_WORD'%dcuid]) & 0b10000000000 for dcuid in [sysmod.MONDCUID,sysmod.MODALDCUID,sysmod.PDCUID,sysmod.TDCUID]]):
                notify('Waiting to load coefficients!')
                return
                               
            self.counter += 1

        elif self.counter == 6:
            return True



# run function for PREQUA initialization
def QUArun(self,GAS=False):
    doflist = [['LEN','TRA','VER','ROL','PIT','YAW'],['M1','M2','M3','M4','M5']]   
    if not self.modeindex == ezca['QUA-%s_MODE_INDEX'%OPTIC]:
        self.modeindex = ezca['QUA-%s_MODE_INDEX'%OPTIC]
        self.counter = 0
        
    if self.modeindex < 1 or self.modeindex > [24,5][GAS]:
            notify('Invalid mode index. Please check QUA_%s_MODE_INDEX'%OPTIC)
            return

    if GAS:
        self.prefix = 'PRE-%s_MODE_GAS_NO%d_'%(OPTIC,self.modeindex)
    else:
        self.prefix = 'PRE-%s_MODE_NO%d_'%(OPTIC,self.modeindex)
        
    self.modeDoF = ezca[self.prefix + 'DOF']
    self.modeStage = ezca[self.prefix + 'STAGE']
    _degenerate = ezca[self.prefix + 'DEGEN_MODE'].split(',')
    self.degenerate = []
    for modestr in _degenerate:
        try:
            self.degenerate.append(int(modestr))
        except:
            pass
        
    if not self.modeDoF in doflist[GAS]:
        notify('start PReQua initialization')
        notify('Mode DoF is not defined propery. Please define it at PRE-%s_MODE_NO%d_DOF'%(OPTIC,self.modeindex))
        self.counter = 0
        return
        
    if not self.modeStage in ['IP','BF','MN','IM','TM','GAS']:
        notify('Mode refelence stage is not defined propery. Please define it at PRE-%s_MODE_NO%d_PLL_SENS'%(OPTIC,self.modeindex))
        self.counter = 0
        return

    if not self.timer['waiting']:
        return

    if self.counter == 0:

        # reset stop watch
        ezca['VIS-%s_PREQUA_DEMOD_SW'%OPTIC] = 0
        time.sleep(0.1)
        ezca['VIS-%s_PREQUA_DEMOD_SW'%OPTIC] = 1
            
        self.pre_freq = ezca[self.prefix + 'PRE_FREQ']
        self.pre_Q = ezca[self.prefix + 'PRE_Q']
        if self.pre_freq == 0 or self.pre_Q == 0:
            notify('Invalid predicted frequency and Q. Please check PRE-%s_MODE_NO%d_PRE_FREQ'%(OPTIC,self.modeindex))
            return

        ezca['VIS-%s_PREQUA_DEMOD_FREQ'%(OPTIC)] = self.pre_freq
            
        self.pre_tau = self.pre_Q/self.pre_freq/np.pi

        edit_chans = []
        for stage in ['IP','BF','MN','IM','TM','GAS']:

            for DoF in doflist[stage=='GAS']:
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
                        notchfreq = ezca[self.prefix + 'PRE_FREQ']
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
                else:
                    kagralib.foton_delete(self.FBs,
                                          fotonQUAname+'_PLL_DEMOD_SIG',
                                          1,
                                          force = True)
                            
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
        if int(ezca['FEC-%d_STATE_WORD'%sysmod.MONDCUID]) & 0b10000000000:
            ezca['FEC-%d_LOAD_NEW_COEFF'%sysmod.MONDCUID] = 1                    
        self.counter += 1

    elif self.counter == 1:
        for stage in ['IP','BF','MN','IM','TM','GAS']:
            for DoF in doflist[stage=='GAS']:
                # channel name 
                QUAname = 'VIS-%s_%s_QUA%s'%(OPTIC,stage,DoF)
                    
                # reset SIG filter
                ezca[QUAname+'_PLL_DEMOD_SIG_RSET'] = 2
                ezca[QUAname+'_PLL_DEMOD_SIG_RMS_RSET'] = 2
                ezca[QUAname+'_PLL_DEMOD_AMP_RSET'] = 2                    
                ezca[QUAname+'_PLL_DEMOD_I_RSET'] = 2
                ezca[QUAname+'_PLL_DEMOD_Q_RSET'] = 2

        if GAS:
            for param in ['AMP','REF_PHASE','FREQ','Q_VAL','DECAY_TIME']:
                for ii in range(5):
                    ezca['VIS-%s_GAS_DOF_SEL_%s_1_%d'%(OPTIC,param,ii+1)] = (doflist[True][ii] == self.modeDoF)
                for ii in range(6):
                    ezca['VIS-%s_TM_DOF_SEL_%s_1_%d'%(OPTIC,param,ii+1)] = (doflist[False][ii] == 'PIT')
        else:
            for stage in ['IP','BF','MN','IM','TM']:
                for param in ['AMP','REF_PHASE','FREQ','Q_VAL','DECAY_TIME']:
                    for ii in range(6):
                        ezca['VIS-%s_%s_DOF_SEL_%s_1_%d'%(OPTIC,stage,param,ii+1)] = (doflist[False][ii] == self.modeDoF)
        for param in ['REF_PHASE','FREQ','Q_VAL','DECAY_TIME']:
            for ii in range(6):
                ezca['VIS-%s_STAGE_SEL_%s_1_%d'%(OPTIC,param,ii+1)] = (['IP','BF','MN','IM','TM','GAS'][ii] == self.modeStage)
        self.counter += 1
                
    elif self.counter == 2:
        if int(ezca['FEC-%d_STATE_WORD'%sysmod.MONDCUID]) & 0b10000000000:
            notify('Waiting to load coefficients!')
        else:
            self.counter += 1
            
    elif self.counter == 3:
        return True

class INIT_PREQUA(GuardState):
    index = 50
    request = True

    def main(self):
        self.FB_load = (ezca['VIS-%s_TM_QUALEN_PLL_DEMOD_SIG_Name00'%OPTIC] == '')
        self.modeindex = 0
        self.counter = 0
        self.timer['waiting'] = 0
        self.FBs = foton.FilterFile(chans+'K1VIS%sMON.txt'%OPTIC)

    def run(self):
        return QUArun(self)

class INIT_PREQUA_GAS(GuardState):
    index = 52
    request = True

    def main(self):
        self.FB_load = (ezca['VIS-%s_GAS_QUAM1_PLL_DEMOD_SIG_Name00'%OPTIC] == '')
        self.modeindex = 0
        self.counter = 0
        self.timer['waiting'] = 0
        self.FBs = foton.FilterFile(chans+'K1VIS%sMON.txt'%OPTIC)

    def run(self):
        return QUArun(self,True)

    

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
                for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']:
                    ezca.switch('VIS-%s_%s_QUA%s_PLL_SERVO'%(OPTIC,stage,DoF),'INPUT','OFF')
                    ezca['VIS-%s_%s_QUA%s_PLL_SERVO_RSET'%(OPTIC,stage,DoF)] = 2
                    time.sleep(.1)
                    ezca.switch('VIS-%s_%s_QUA%s_PLL_SERVO'%(OPTIC,stage,DoF),'INPUT','ON')

            self.timer['waiting'] = 2
            self.counter += 1

        elif self.counter == 1:
            return self.is_PLL_locked()

class CLOSE_PLL_GAS(GuardState):
    index = 81
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

        doflist = [['LEN','TRA','VER','ROL','PIT','YAW'],['M1','M2','M3','M4','M5']]
        
        if self.counter == 0:
            for stage in ['TM','GAS']:
                for DoF in doflist[stage == 'GAS']:
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
        self.EXCDOF = (['IP_LEN','IP_TRA','IP_YAW'] +
        ['%s_%s'%(stage,DOF) for stage in ['BF','MN','IM'] for DOF in ['LEN','TRA','VER','ROL','PIT','YAW']] +
        ['TM_LEN','TM_PIT','TM_YAW'] +
        ['GAS_M%d'%ii for ii in range(1,6)])
        
        self.QUAEXC_SEL = cdsutils.CDSMatrix(            
                    'MOD-%s_QUAEXC_SEL'%(OPTIC,),
                    cols={ii+1: ii+1 for ii in range(1)},
                    rows={self.EXCDOF[ii]: ii+1 for ii in range(len(self.EXCDOF))},
                )

        self.counter = 0
        self.timer['waiting'] = 0

        self.modeindex = ezca['QUA-%s_MODE_INDEX'%OPTIC]

        self.QUAEXC = ezca.get_LIGOFilter('VIS-ITMY_QUAEXC')
        self.FBs = foton.FilterFile(chans+'K1VIS%sMON.txt'%OPTIC)


    @check_mod_freq
    def run(self):
        if not self.timer['waiting']:
            return
        
        self.modeDoF = ezca['PRE-%s_MODE_GAS_NO%d_DOF'%(OPTIC,self.modeindex)]
        self.Stage = ezca['PRE-%s_MODE_GAS_NO%d_STAGE'%(OPTIC,self.modeindex)]
        self.pre_freq = ezca['PRE-%s_MODE_GAS_NO%d_PRE_FREQ'%(OPTIC,self.modeindex)]

                    
        
        if self.counter == 0:
            self.QUAEXC.ramp_gain(0,2,False)
            self.timer['waiting'] = 2
            self.counter += 1

        elif self.counter == 1:
            log(self.QUAEXC_SEL)
            self.QUAEXC_SEL.put_matrix(np.matrix([[0,] for ii in range(len(self.EXCDOF))]))
            self.QUAEXC_SEL['%s_%s'%(self.Stage,self.modeDoF),1] = 1
            '''
            except:
                notify('Invalid DoF or stage!!')
                return
            '''
            kagralib.foton_butter(self.FBs,
                                  '%s_QUAEXC'%OPTIC,
                                  Type='BandPass',
                                  index=0,
                                  order=4,
                                  freq=self.pre_freq-self.pre_freq/20.,
                                  freq2=self.pre_freq+self.pre_freq/20.,
                                  force=True)
            self.FBs.write()
            time.sleep(0.5)
            self.QUAEXC.turn_on('OFFSET','FM1')
            self.QUAEXC.RSET.put(1)


            self.counter += 1
                
        elif self.counter == 2:
            return True



class EXCITE_RESONANCE_GAS(GuardState):
    index = 101
    request = True

    def is_EXC_enough(self):
        # Check SIG_RMS and compare with threshold. Then, how we can set good threshold?
        return True
    
    @check_mod_freq
    def main(self):
        self.EXCDOF = (['IP_LEN','IP_TRA','IP_YAW'] +
        ['%s_%s'%(stage,DOF) for stage in ['BF','MN','IM'] for DOF in ['LEN','TRA','VER','ROL','PIT','YAW']] +
        ['TM_LEN','TM_PIT','TM_YAW'] +
        ['GAS_M%d'%ii for ii in range(1,6)])
        
        self.QUAEXC_SEL = cdsutils.CDSMatrix(            
                    'MOD-%s_QUAEXC_SEL'%(OPTIC,),
                    cols={ii+1: ii+1 for ii in range(1)},
                    rows={self.EXCDOF[ii]: ii+1 for ii in range(len(self.EXCDOF))},
                )

        self.counter = 0
        self.timer['waiting'] = 0

        self.modeindex = ezca['QUA-%s_MODE_INDEX'%OPTIC]

        self.QUAEXC = ezca.get_LIGOFilter('VIS-ITMY_QUAEXC')
        self.FBs = foton.FilterFile(chans+'K1VIS%sMON.txt'%OPTIC)


    @check_mod_freq
    def run(self):
        if not self.timer['waiting']:
            return
        
        self.modeDoF = ezca['PRE-%s_MODE_GAS_NO%d_DOF'%(OPTIC,self.modeindex)]
        self.Stage = ezca['PRE-%s_MODE_GAS_NO%d_STAGE'%(OPTIC,self.modeindex)]
        self.pre_freq = ezca['PRE-%s_MODE_GAS_NO%d_PRE_FREQ'%(OPTIC,self.modeindex)]

                    
        
        if self.counter == 0:
            self.QUAEXC.ramp_gain(0,2,False)
            self.timer['waiting'] = 2
            self.counter += 1

        elif self.counter == 1:
            self.QUAEXC_SEL.put_matrix(np.matrix([[0,] for ii in range(len(self.EXCDOF))]))            
            self.QUAEXC_SEL['%s_%s'%(self.Stage,self.modeDoF),1] = 1
            '''
            except:
                notify('Invalid DoF or stage!!')
                return
            '''
            kagralib.foton_butter(self.FBs,
                                  '%s_QUAEXC'%OPTIC,
                                  Type='BandPass',
                                  index=0,
                                  order=4,
                                  freq=self.pre_freq-self.pre_freq/20.,
                                  freq2=self.pre_freq+self.pre_freq/20.,
                                  force=True)
            self.FBs.write()
            time.sleep(0.5)
            self.QUAEXC.turn_on('OFFSET','FM1')
            self.QUAEXC.RSET.put(1)


            self.counter += 1
                
        elif self.counter == 2:
            return True



########################################################################
# Function for Recording
    
class RECORD_MEASUREMENT(GuardState):
    index = 150
    request = True


    def plot_PARAMS(self):
        # plot frequency and Qval time series
        fig = plt.figure()
        ax1 = fig.add_subplot(2,1,1)
        ax1.plot(self.tt[self.param_chans['FREQ']],self.data[self.param_chans['FREQ']])
        ax1.set_ylabel('Frequency [Hz]')
        
        
        ax2 = fig.add_subplot(2,1,2)
        ax1.plot(self.tt[self.param_chans['Q_VAL']],self.data[self.param_chans['Q_VAL']])
        ax2.set_xlabel('time [sec]')
        ax2.set_ylabel('Q Value')
        
        fig.tight_layout()
        fig.savefig(self.figdir + 'MODE_PARAMS.png')
        fig.savefig(self.figdir_archive + self.fileprefix +  'MODE_PARAMS.png')
        plt.close(fig)
        
        os.system('convert %s %s'%(self.figdir + 'MODE_PARAMS.png',self.figdir + 'medm/MODE_PARAMS.gif'))
        
    def plot_SENSMAT(self,stagelist,filelabel):
        # plot sensing matrix component timeseries
        fig1 = plt.figure()
        fig2 = plt.figure()
        ii = 0
        ax = []
        for stage in stagelist:
            for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']:
                ax.append(fig1.add_subplot(len(stagelist),6,ii+1))
                ax[-1].plot(self.tt[self.sensvec_chans[stage][DoF]], self.data[self.sensvec_chans[stage][DoF]])
                ax[-1].set_title('%s %s'%(stage,DoF),fontsize=6)
            
                #remove xtick except for bottom line
                if ii < 6 * (len(stagelist) - 1):
                    ax[-1].tick_params(axis='x',          
                                       which='both',
                                       bottom=False,
                                       top=False,
                                       labelbottom=False)
                    
                ax.append(fig2.add_subplot(len(stagelist),6,ii+1))
                ax[-1].plot(self.tt[self.sensvec_phase_chans[stage][DoF]], self.data[self.sensvec_phase_chans[stage][DoF]])
                ax[-1].set_title('%s %s'%(stage,DoF),fontsize=6)

                #remove xtick except for bottom line
                if ii < 6 * (len(stagelist) - 1):
                    ax[-1].tick_params(axis='x',          
                                       which='both',
                                       bottom=False,
                                       top=False,
                                       labelbottom=False)                        
                ii += 1

        fig1.suptitle("Sensing matrix")
        fig1.savefig(self.figdir + 'SENSMAT_%s.png'%filelabel)
        fig1.savefig(self.figdir_archive + self.fileprefix + 'SENSMAT_%s.png'%filelabel)
        plt.close(fig1)
        
        fig2.suptitle("Sensing phase matrix")
        fig2.savefig(self.figdir + 'SENSMAT_PHASE_%s.png'%filelabel)
        fig2.savefig(self.figdir_archive + self.fileprefix + 'SENSMAT_PHASE_%s.png'%filelabel)
        plt.close(fig2)

    def plot_DOFfreq(self,stagelist,filelabel):
        # plot sensing matrix component timeseries
        fig1 = plt.figure()
        ii = 0
        ax = []
        for stage in stagelist:
            for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']:
                ax.append(fig1.add_subplot(len(stagelist),6,ii+1))
                ax[-1].plot(self.tt[self.freq_chans[stage][DoF]], self.data[self.freq_chans[stage][DoF]])
                ax[-1].set_title('%s %s'%(stage,DoF),fontsize=6)

                #remove xtick except for bottom line
                if ii < 6 * (len(stagelist) - 1):
                    ax[-1].tick_params(axis='x',          
                                       which='both',
                                       bottom=False,
                                       top=False,
                                       labelbottom=False)
                ii += 1

        fig1.suptitle("QUADOF Q values")
        fig1.savefig(self.figdir + 'QUADOF_Q_%s.png'%filelabel)
        fig1.savefig(self.figdir_archive + self.fileprefix + 'QUADOF_Q_%s.png'%filelabel)
        plt.close(fig1)

    def plot_DOFQ(self,stagelist,filelabel):
        # plot sensing matrix component timeseries
        fig1 = plt.figure()
        ii = 0
        ax = []
        for stage in stagelist:
            for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']:
                ax.append(fig1.add_subplot(len(stagelist),6,ii+1))
                ax[-1].plot(self.tt[self.freq_chans[stage][DoF]], self.data[self.freq_chans[stage][DoF]])
                ax[-1].set_title('%s %s'%(stage,DoF),fontsize=6)
                
                #remove xtick except for bottom line
                if ii < 6 * (len(stagelist) - 1):
                    ax[-1].tick_params(axis='x',          
                                       which='both',
                                       bottom=False,
                                       top=False,
                                       labelbottom=False)
                ii += 1

        fig1.suptitle("QUADOF frequencies")
        fig1.savefig(self.figdir + 'QUADOF_freq_%s.png'%filelabel)
        fig1.savefig(self.figdir_archive + self.fileprefix + 'QUADOF_freq_%s.png'%filelabel)
        plt.close(fig1)
        
    def check_config(self):
        if not self.modeDoF in ['LEN','TRA','VER','ROL','PIT','YAW']:
            notify('Mode DoF is not defined propery. Please define it at VIS-%s_FREE_MODE_LIST_NO%d_DOF'%(OPTIC,self.modeindex))
            self.counter = 0
            return False
    
        if not self.modeStage in ['IP','BF','MN','IM','TM']:
            notify('Mode refelence stage is not defined propery. Please define it at VIS-%s_FREE_MODE_LIST_NO%d_PLL_SENS'%(OPTIC,self.modeindex))
            self.counter = 0
            return False
        return True
    
    
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

        self.modeindex = ezca['QUA-%s_MODE_INDEX'%OPTIC]
        self.duration = 10./ezca['VIS-%s_PREQUA_DEMOD_FREQ'%OPTIC] # duration for average

        
        self.SENSMAT = cdsutils.CDSMatrix(            
            'PRE-%s_MODE_NO%d_SENSMAT_RATIO'%(OPTIC,self.modeindex),
            rows={['LEN','TRA','VER','ROL','PIT','YAW'][ii]:ii+1 for ii in range(6)},
            cols={['IP','BF','MN','IM','TM'][ii]:ii+1 for ii in range(5)},
        )
            
        self.SENSMAT_PHASE = cdsutils.CDSMatrix(            
            'PRE-%s_MODE_NO%d_SENSMAT_PHASE'%(OPTIC,self.modeindex),
            rows={['LEN','TRA','VER','ROL','PIT','YAW'][ii]:ii+1 for ii in range(6)},
            cols={['IP','BF','MN','IM','TM'][ii]:ii+1 for ii in range(5)},
        )

        self.MOTIONVEC = cdsutils.CDSMatrix(            
            'PRE-%s_MODE_NO%d_STAGE_MOTION_RATIO'%(OPTIC,self.modeindex),
            rows={['IP','BF','MN','IM','TM'][ii]:ii+1 for ii in range(5)},
            cols={ii+1:ii+1 for ii in range(1)},
        )
            
        self.MOTIONVEC_PHASE = cdsutils.CDSMatrix(            
            'PRE-%s_MODE_NO%d_STAGE_MOTION_PHASE'%(OPTIC,self.modeindex),
            rows={['IP','BF','MN','IM','TM'][ii]:ii+1 for ii in range(5)},
            cols={ii+1:ii+1 for ii in range(1)},
        )
        
        # difine readback channel
        # parameter channels for frequency, Q val, and decay time.
        self.param_chans = {param:'VIS-%s_PREQUA_%s_OUT_DQ'%(OPTIC,param) for param in ['FREQ','Q_VAL','DECAY_TIME']}

        # sensing vector channels for each stage
        self.sensvec_chans = {
            stage:{DoF:'VIS-%s_%s_CP_COEF_%s_OUTPUT'%(OPTIC,stage,DoF) for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']}
            for stage in ['IP','BF','MN','IM','TM']
        }

        self.sensvec_phase_chans = {
            stage:{DoF:'VIS-%s_%s_REL_PHASE_%s_OUTPUT'%(OPTIC,stage,DoF) for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']}
            for stage in ['IP','BF','MN','IM','TM']
        }

        # stage motion vector channels
        self.motvec_chans = {
            stage:'VIS-%s_CP_COEF_%s_OUT_DQ'%(OPTIC,stage)
            for stage in ['IP','BF','MN','IM','TM']
        }
        self.motvec_phase_chans = {
            stage:'VIS-%s_REL_PHASE_%s_OUT_DQ'%(OPTIC,stage)
            for stage in ['IP','BF','MN','IM','TM']
        }


        # QUADOF frequency channels
        self.freq_chans = {
            stage:{DoF:'VIS-%s_%s_QUA%s_FREQ_OUTPUT'%(OPTIC,stage,DoF) for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']}
            for stage in ['IP','BF','MN','IM','TM']
            }
        '''
        self.Q_chans = {
            stage:{DoF:'VIS-%s_%s_QUA%s_Q_VAL_OUTPUT'%(OPTIC,stage,DoF) for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']}
            for stage in ['IP','BF','MN','IM','TM']
            }
        '''
        #[FIXME] Sorry Akutsu-san...
        '''
        for stage in ['IP','BF','MN','IM','TM']:
            for DoF in doflist[stage=='GAS']:
                self.freqchandict[self.short_prefix+'%s_QUA%s_FREQ_OUTPUT'%(stage,DoF)] = '%s_%s'%(stage,DoF) #These are just identifier.
        '''

        _t = time.localtime()
        keys = ['YEAR','MON','DAY','HOUR','MIN','SEC']
        self.time = {
            keys[ii]:_t[ii] for ii in range(len(keys))
        }
        
    
        for key in ['YEAR','MON','DAY']:
            ezca['PRE-%s_MODE_NO%d_MEAS_DATE_'%(OPTIC,self.modeindex) + key] = self.time[key]

        # for plot
        self.figdir = '/users/Measurements/VIS/ITMY/PREQUA/mode%d/'%int(self.modeindex)
        self.figdir_archive = '/users/Measurements/VIS/ITMY/PREQUA/mode%d/archive/'%int(self.modeindex)

        kagralib.mkdir(self.figdir)
        kagralib.mkdir(self.figdir+'medm')
        kagralib.mkdir(self.figdir_archive)
    
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
        
        
        
    def run(self):
        if not self.timer['waiting']:
            return

        self.modeDoF = ezca['PRE-%s_MODE_NO%d_DOF'%(OPTIC,self.modeindex)]
        self.modeStage = ezca['PRE-%s_MODE_NO%d_STAGE'%(OPTIC,self.modeindex)]

        if not self.check_config():
            return
        

        if self.counter == 0:
            notify('start recording')
            # log date

            #[FIXEME] sorry Akutsu-san
            #_keys = self.chandict.keys() + self.freqchandict.keys()

            # get data
            # channel list
            _chans = []
            for param in self.param_chans.keys():
                _chans.append(self.param_chans[param])
                
            for stage in self.sensvec_chans.keys():
                for DoF in self.sensvec_chans[stage].keys():
                    _chans.append(self.sensvec_chans[stage][DoF])
                    _chans.append(self.sensvec_phase_chans[stage][DoF])
                                  
            for stage in self.motvec_chans.keys():
                _chans.append(self.motvec_chans[stage])
                _chans.append(self.motvec_phase_chans[stage])

            for stage in self.freq_chans.keys():
                for DoF in self.freq_chans[stage].keys():
                    _chans.append(self.freq_chans[stage][DoF])
            '''
            for stage in self.Q_chans.keys():
                for DoF in self.Q_chans[stage].keys():
                    _chans.append(self.Q_chans[stage][DoF])
            '''

            # record starting time
            _time = time.localtime()
            self.logger.debug('OPTIC: %s.'%OPTIC)                        
            self.logger.debug('Mode number: %d.'%self.modeindex)
            self.logger.debug('start recording at %s/%s/%s %s:%s:%s.'%(str(_time[0]).zfill(2),str(_time[1]).zfill(2),str(_time[2]).zfill(2),str(_time[3]).zfill(2),str(_time[4]).zfill(2),str(_time[5]).zfill(2)))

            # measure and perse result
            _data = cdsutils.getdata(_chans,self.duration,)
                                  
            self.data = {
                _chans[ii]: _data[ii].data for ii in range(len(_chans))
            }
            self.tt = {
                _chans[ii]: np.array(range(len(_data[ii].data))) / _data[ii].sample_rate for ii in range(len(_chans))
                }

            # record end time
            _time = time.localtime()
            self.logger.debug('finish recording at %s/%s/%s %s:%s:%s.'%(str(_time[0]).zfill(2),str(_time[1]).zfill(2),str(_time[2]).zfill(2),str(_time[3]).zfill(2),str(_time[4]).zfill(2),str(_time[5]).zfill(2)))
            self.counter += 1

        elif self.counter == 1:
            # put measurement record to EPICS channel
            # parameters
            prefix = 'PRE-%s_MODE_NO%d_'%(OPTIC,self.modeindex)

            for param in self.param_chans.keys():
                ezca[prefix+param] = np.average(self.data[self.param_chans[param]])

                
            for stage in self.sensvec_chans.keys():
                for DoF in self.sensvec_chans[stage].keys():
                    log(self.SENSMAT_PHASE)
                    self.SENSMAT[DoF,stage] = np.average(self.data[self.sensvec_chans[stage][DoF]])
                    self.SENSMAT_PHASE[DoF,stage] = np.mod(np.average(self.data[self.sensvec_phase_chans[stage][DoF]]),-360)

            for stage in self.motvec_chans.keys():
                self.MOTIONVEC[stage,1] = np.average(self.data[self.motvec_chans[stage]])
                self.MOTIONVEC_PHASE[stage,1] = np.mod(np.average(self.data[self.motvec_phase_chans[stage]]),-360)

            '''
            # log and check data quality
            #20200805 Akutsu added the following block
            #For evaluating the demod freqs of each DoF of each stage
            #And judge whether the stage's dof can be usable or not.
            self.freq_id_dict={}
            for key in self.freqchandict.keys():
                _key2 = self.freqchandict[key]
                self.freq_id_dict[_key2]={'mean': np.mean(self.data[key]),
                                          #'std': np.std(self.data[key]),
                                          'bool': True}
            #Argorithm1: using mean of means. _mean_list = [mean,weight]
            _mean_list = np.array([[self.freq_id_dict[k]['mean'], sysmod.AVGWEIGHT[k.split('_')[0]][k.split('_')[1]]] for k in self.freq_id_dict]).T
            _mean_list_mean = np.average(_mean_list[0], weights = _mean_list[1]) # Weighted mean of the means
            #_mean_list_std = np.std(_mean_list)
            # The following is, I believe, weighted standard dev.
            _mean_list_std = np.sqrt(np.average((_mean_list[0]-_mean_list_mean)**2., weights = _mean_list[1]))
            self.logger.debug('Resonant frequency:%f'%ezca['VIS-%s_FREE_MODE_LIST_NO%d_FREQ'%(OPTIC,self.modeindex)])
            self.logger.debug('(Weighted) Mean of resonant frequency of all QUADOF:%f'%_mean_list_mean)
            self.logger.debug('(Weighted) Std of resonant frequency of all QUADOF:%f'%_mean_list_std)
            for key in  self.freq_id_dict:
                qq1 =  self.freq_id_dict[key]
                if (qq1['mean'] > _mean_list_mean + _mean_list_std*3.) or (qq1['mean'] < _mean_list_mean - _mean_list_std*3. ):
                    qq1['bool'] = False
            #Argorithm2
            # Any nicer way to distinguish extraordinary values??
            '''
            
            for stage in self.sensvec_chans.keys():
                for DoF in self.sensvec_chans[stage].keys():
                    self.logger.debug('- %s %s'%(stage,DoF))
                    self.logger.debug('Coupling coefficient: %f'%self.SENSMAT[DoF,stage])
                    self.logger.debug('Relative phase: %f'%self.SENSMAT_PHASE[DoF,stage])
                    
                #[FIXME] sorry Akutsu-san
                '''
                if not self.freq_id_dict['%s_%s'%(stage,DoF)]['bool']:
                    qq1 = ezca[self.prefix[3:]+'%s_CP_COEF_%s'%(stage,DoF)]
                    self.logger.debug('---------------------warning---------------------------')
                    self.logger.debug('%d Hz is out of the 3-sigma region of the distribtion of the means'%(qq1))
                    self.logger.debug('Put 0 as coupling coefficient and relative phase')
                    ezca[self.prefix[3:]+'%s_CP_COEF_%s'%(stage,DoF)] = 0.
                    ezca[self.prefix[3:]+'%s_REL_PHASE_%s'%(stage,DoF)] = 0.
                '''
            self.counter +=1
        
        elif self.counter == 2:
            self.plot_PARAMS()
        
            # coupling coefficiency and relative phase
            plt.rcParams['font.size'] = 6
            self.plot_SENSMAT(['MN','IM','TM'],'PAYLOAD')
            self.plot_SENSMAT(['IP','BF'],'TOWER')
            self.plot_DOFfreq(['MN','IM','TM'],'PAYLOAD')
            self.plot_DOFfreq(['IP','BF'],'TOWER')
            self.plot_DOFQ(['MN','IM','TM'],'PAYLOAD')
            self.plot_DOFQ(['IP','BF'],'TOWER')


            # copy measurement log to archive
            os.system('cp %s %s/measurement.log'%(self.figdir_archive + self.fileprefix + 'measurement.log',self.figdir))

            # [FIXME] sorry Akutsu-san
            # Histogram of the mean of each freq chan
            # The first version of the histgoram-ing was added by Akutsu on 20200806
            '''
            fig = plt.figure()
            ax1 = fig.add_subplot(111)
            ax1.hist(_mean_list[0], bins=5)# Always hard to determine a proper bins; if using the Sturges' rule, bins=5 for 24 data points.
            fig.savefig('/users/akutsu/test0.png')# Change the path!!
            '''
            
            self.counter += 1
        elif self.counter == 3:
            ezca['PRE-%s_MODE_NO%d_PRE_FREQ'%(OPTIC,self.modeindex)] = ezca['PRE-%s_MODE_NO%d_FREQ'%(OPTIC,self.modeindex)]
            
            self.counter += 1
            
        elif self.counter == 4:
            return True


    
class RECORD_MEASUREMENT_GAS(GuardState):
    index = 151
    request = True
    
    def check_config(self):
        if not self.modeDoF in ['M1','M2','M3','M4','M5']:
            notify('Mode DoF is not defined propery. Please define it at VIS-%s_FREE_MODE_GAS_LIST_NO%d_DOF'%(OPTIC,self.modeindex))
            self.counter = 0
            return False
    
        if not self.modeStage in ['GAS',]:
            notify('Mode refelence stage is not defined propery. Please define it at VIS-%s_FREE_MODE_GAS_LIST_NO%d_PLL_SENS'%(OPTIC,self.modeindex))
            self.counter = 0
            return False
        return True
    
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

        self.modeindex = ezca['QUA-%s_MODE_INDEX'%OPTIC]
        self.duration = 10./ezca['VIS-%s_PREQUA_DEMOD_FREQ'%OPTIC] # duration for average

        '''
        self.SENSMAT = cdsutils.CDSMatrix(            
            'PRE-%s_MODE_GAS_NO%d_STAGE_MOTION_RATIO'%(OPTIC,self.modeindex),
            rows={['GAS','TM'][ii]:ii+1 for ii in range(5)},
            cols={ii+1:ii+1 for ii in range(1)},
        )
        '''
        self.SENSMAT_PHASE = cdsutils.CDSMatrix(            
            'PRE-%s_MODE_GAS_NO%d_STAGE_MOTION_PHASE'%(OPTIC,self.modeindex),
            rows={['GAS','TM'][ii]:ii+1 for ii in range(2)},
            cols={ii+1:ii+1 for ii in range(1)},
        )

        self.MOTIONVEC = cdsutils.CDSMatrix(            
            'PRE-%s_MODE_GAS_NO%d_STAGE_MOTION_RATIO'%(OPTIC,self.modeindex),
            rows={['M1','M2','M3','M4','M5'][ii]:ii+1 for ii in range(5)},
            cols={ii+1:ii+1 for ii in range(1)},
        )

        self.MOTIONVEC_PHASE = cdsutils.CDSMatrix(            
            'PRE-%s_MODE_GAS_NO%d_STAGE_MOTION_PHASE'%(OPTIC,self.modeindex),
            rows={['M1','M2','M3','M4','M5'][ii]:ii+1 for ii in range(5)},
            cols={ii+1:ii+1 for ii in range(1)},
        )
            
        
        # difine readback channel
        # parameter channels for frequency, Q val, and decay time.
        self.param_chans = {param:'VIS-%s_PREQUA_%s_OUT_DQ'%(OPTIC,param) for param in ['FREQ','Q_VAL','DECAY_TIME']}

        # sensing vector channels for each stage
        self.sensvec_phase_chans = {
            stage:'VIS-%s_REL_PHASE_%s_OUTPUT'%(OPTIC,stage)
            for stage in ['GAS','TM']
        }

        # stage motion vector channels
        self.motvec_chans = {
            stage:'VIS-%s_GAS_CP_COEF_%s_OUT_DQ'%(OPTIC,stage)
            for stage in ['M1','M2','M3','M4','M5']
        }
        self.motvec_phase_chans = {
            stage:'VIS-%s_GAS_REL_PHASE_%s_OUT_DQ'%(OPTIC,stage)
            for stage in ['M1','M2','M3','M4','M5']
        }


        # QUADOF frequency channels
        self.freq_chans = {
            'GAS':{DoF:'VIS-%s_%s_QUA%s_FREQ_OUTPUT'%(OPTIC,'GAS',DoF) for DoF in ['M1','M2','M3','M4','M5']},
            'TM':{DoF:'VIS-%s_%s_QUA%s_FREQ_OUTPUT'%(OPTIC,'GAS',DoF) for DoF in ['PIT','YAW']}
            }
        '''
        self.Q_chans = {
            stage:{DoF:'VIS-%s_%s_QUA%s_Q_VAL_OUTPUT'%(OPTIC,stage,DoF) for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']}
            for stage in ['IP','BF','MN','IM','TM']
            }
        '''
        #[FIXME] Sorry Akutsu-san...
        '''
        for stage in ['IP','BF','MN','IM','TM']:
            for DoF in doflist[stage=='GAS']:
                self.freqchandict[self.short_prefix+'%s_QUA%s_FREQ_OUTPUT'%(stage,DoF)] = '%s_%s'%(stage,DoF) #These are just identifier.
        '''

        _t = time.localtime()
        keys = ['YEAR','MON','DAY','HOUR','MIN','SEC']
        self.time = {
            keys[ii]:_t[ii] for ii in range(len(keys))
        }
        
    
        for key in ['YEAR','MON','DAY']:
            ezca['PRE-%s_MODE_GAS_NO%d_MEAS_DATE_'%(OPTIC,self.modeindex) + key] = self.time[key]

        # for plot
        self.figdir = '/users/Measurements/VIS/ITMY/PREQUA/GAS_mode%d/'%int(self.modeindex)
        self.figdir_archive = '/users/Measurements/VIS/ITMY/PREQUA/GAS_mode%d/archive/'%int(self.modeindex)

        kagralib.mkdir(self.figdir)
        kagralib.mkdir(self.figdir+'medm')
        kagralib.mkdir(self.figdir_archive)
    
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
        
        
        
    def run(self):
        if not self.timer['waiting']:
            return

        self.modeDoF = ezca['PRE-%s_MODE_GAS_NO%d_DOF'%(OPTIC,self.modeindex)]
        self.modeStage = ezca['PRE-%s_MODE_GAS_NO%d_STAGE'%(OPTIC,self.modeindex)]

        if not self.check_config():
            return
        

        if self.counter == 0:
            notify('start recording')
            # log date

            #[FIXEME] sorry Akutsu-san
            #_keys = self.chandict.keys() + self.freqchandict.keys()

            # get data
            # channel list
            _chans = []
            for param in self.param_chans.keys():
                _chans.append(self.param_chans[param])

            for stage in self.sensvec_phase_chans.keys():
                    #_chans.append(self.sensvec_chans[stage][DoF])
                    _chans.append(self.sensvec_phase_chans[stage])

            for stage in self.motvec_chans.keys():
                _chans.append(self.motvec_chans[stage])
                _chans.append(self.motvec_phase_chans[stage])
                '''
            for stage in self.freq_chans.keys():
                for DoF in self.freq_chans[stage].keys():
                    _chans.append(self.freq_chans[stage][DoF])

            for stage in self.Q_chans.keys():
                for DoF in self.Q_chans[stage].keys():
                    _chans.append(self.Q_chans[stage][DoF])
            '''

            # record starting time
            _time = time.localtime()
            self.logger.debug('OPTIC: %s.'%OPTIC)                        
            self.logger.debug('Mode number: %d.'%self.modeindex)
            self.logger.debug('start recording at %s/%s/%s %s:%s:%s.'%(str(_time[0]).zfill(2),str(_time[1]).zfill(2),str(_time[2]).zfill(2),str(_time[3]).zfill(2),str(_time[4]).zfill(2),str(_time[5]).zfill(2)))

            # measure and perse result
            log(_chans)
            _data = cdsutils.getdata(_chans,self.duration,)
                                  
            self.data = {
                _chans[ii]: _data[ii].data for ii in range(len(_chans))
            }
            self.tt = {
                _chans[ii]: np.array(range(len(_data[ii].data))) / _data[ii].sample_rate for ii in range(len(_chans))
                }

            # record end time
            _time = time.localtime()
            self.logger.debug('finish recording at %s/%s/%s %s:%s:%s.'%(str(_time[0]).zfill(2),str(_time[1]).zfill(2),str(_time[2]).zfill(2),str(_time[3]).zfill(2),str(_time[4]).zfill(2),str(_time[5]).zfill(2)))
            self.counter += 1

        elif self.counter == 1:
            # put measurement record to EPICS channel
            # parameters
            prefix = 'PRE-%s_MODE_GAS_NO%d_'%(OPTIC,self.modeindex)

            for param in self.param_chans.keys():
                ezca[prefix+param] = np.average(self.data[self.param_chans[param]])

                
            for stage in self.sensvec_phase_chans.keys():
                #self.SENSMAT[DoF,stage] = np.average(self.data[self.sensvec_chans[stage][DoF]])
                self.SENSMAT_PHASE[stage,1] = np.mod(np.average(self.data[self.sensvec_phase_chans[stage]]),-360)

            for stage in self.motvec_chans.keys():
                self.MOTIONVEC[stage,1] = np.average(self.data[self.motvec_chans[stage]])
                self.MOTIONVEC_PHASE[stage,1] = np.mod(np.average(self.data[self.motvec_phase_chans[stage]]),-360)

            '''
            # log and check data quality
            #20200805 Akutsu added the following block
            #For evaluating the demod freqs of each DoF of each stage
            #And judge whether the stage's dof can be usable or not.
            self.freq_id_dict={}
            for key in self.freqchandict.keys():
                _key2 = self.freqchandict[key]
                self.freq_id_dict[_key2]={'mean': np.mean(self.data[key]),
                                          #'std': np.std(self.data[key]),
                                          'bool': True}
            #Argorithm1: using mean of means. _mean_list = [mean,weight]
            _mean_list = np.array([[self.freq_id_dict[k]['mean'], sysmod.AVGWEIGHT[k.split('_')[0]][k.split('_')[1]]] for k in self.freq_id_dict]).T
            _mean_list_mean = np.average(_mean_list[0], weights = _mean_list[1]) # Weighted mean of the means
            #_mean_list_std = np.std(_mean_list)
            # The following is, I believe, weighted standard dev.
            _mean_list_std = np.sqrt(np.average((_mean_list[0]-_mean_list_mean)**2., weights = _mean_list[1]))
            self.logger.debug('Resonant frequency:%f'%ezca['VIS-%s_FREE_MODE_LIST_NO%d_FREQ'%(OPTIC,self.modeindex)])
            self.logger.debug('(Weighted) Mean of resonant frequency of all QUADOF:%f'%_mean_list_mean)
            self.logger.debug('(Weighted) Std of resonant frequency of all QUADOF:%f'%_mean_list_std)
            for key in  self.freq_id_dict:
                qq1 =  self.freq_id_dict[key]
                if (qq1['mean'] > _mean_list_mean + _mean_list_std*3.) or (qq1['mean'] < _mean_list_mean - _mean_list_std*3. ):
                    qq1['bool'] = False
            #Argorithm2
            # Any nicer way to distinguish extraordinary values??
            '''
            
            for stage in self.motvec_chans.keys():
                self.logger.debug('- %s'%(stage))
                self.logger.debug('Coupling coefficient: %f'%self.MOTIONVEC[stage,1])
                self.logger.debug('Relative phase: %f'%self.MOTIONVEC_PHASE[stage,1])
                    
                #[FIXME] sorry Akutsu-san
                '''
                if not self.freq_id_dict['%s_%s'%(stage,DoF)]['bool']:
                    qq1 = ezca[self.prefix[3:]+'%s_CP_COEF_%s'%(stage,DoF)]
                    self.logger.debug('---------------------warning---------------------------')
                    self.logger.debug('%d Hz is out of the 3-sigma region of the distribtion of the means'%(qq1))
                    self.logger.debug('Put 0 as coupling coefficient and relative phase')
                    ezca[self.prefix[3:]+'%s_CP_COEF_%s'%(stage,DoF)] = 0.
                    ezca[self.prefix[3:]+'%s_REL_PHASE_%s'%(stage,DoF)] = 0.
                '''
            self.counter +=1
        
        elif self.counter == 2:
            #self.plot_PARAMS()
        
            # coupling coefficiency and relative phase
            plt.rcParams['font.size'] = 6
            #self.plot_SENSMAT(['MN','IM','TM'],'PAYLOAD')
            #self.plot_SENSMAT(['IP','BF'],'TOWER')
            #self.plot_DOFfreq(['MN','IM','TM'],'PAYLOAD')
            #self.plot_DOFfreq(['IP','BF'],'TOWER')
            #self.plot_DOFQ(['MN','IM','TM'],'PAYLOAD')
            #self.plot_DOFQ(['IP','BF'],'TOWER')


            # copy measurement log to archive
            os.system('cp %s %s/measurement.log'%(self.figdir_archive + self.fileprefix + 'measurement.log',self.figdir))

            # [FIXME] sorry Akutsu-san
            # Histogram of the mean of each freq chan
            # The first version of the histgoram-ing was added by Akutsu on 20200806
            '''
            fig = plt.figure()
            ax1 = fig.add_subplot(111)
            ax1.hist(_mean_list[0], bins=5)# Always hard to determine a proper bins; if using the Sturges' rule, bins=5 for 24 data points.
            fig.savefig('/users/akutsu/test0.png')# Change the path!!
            '''
            
            self.counter += 1
        elif self.counter == 3:
            ezca['PRE-%s_MODE_GAS_NO%d_PRE_FREQ'%(OPTIC,self.modeindex)] = ezca['PRE-%s_MODE_GAS_NO%d_FREQ'%(OPTIC,self.modeindex)]
            
            self.counter += 1
            
        elif self.counter == 4:
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
                for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']:
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
        # where a, b and alpha is drived as in the script.
        # major axis can be derived as x = A*cos(-alpha/2), y = B*cos(-alpha/2+theta)
    
        a = (A**2+B**2*np.cos(2*theta))
        b = B**2*np.sin(2*theta)
        alpha = np.arcsin(b/np.sqrt(a**2+b**2))
        
        x = A*np.cos(-alpha/2)
        y = B*np.cos(-alpha/2+theta)
        
        return x,y

    def calc_SENSDIAG_matrix(self,stage):
        _t_sensing_matrix = np.identity(6)
        ii = 0
            
        for motion_DoF in ['LEN','TRA','VER','ROL','PIT','YAW']:
            if stage in ['IP','BF','TM']:
                SENDIAG = 'SENSDIAG_TOWER'
                if stage == 'TM' and motion_DoF == 'PIT':
                    log('hogehoge')
                    SENDIAG = 'SENSDIAG'
            else:
                SENDIAG = 'SENSDIAG'            
            _sensing_vector = []
            _A = ezca['VIS-%s_%s_%s_%s_CP_COEF_%s'%(OPTIC,SENDIAG,motion_DoF,stage,motion_DoF)]
            _theta_a = ezca['VIS-%s_%s_%s_%s_REL_PHASE_%s'%(OPTIC,SENDIAG,motion_DoF,stage,motion_DoF)]
            if _A == 0:
                log('skip this DoF')
                
            else:
                for sensor_DoF in ['LEN','TRA','VER','ROL','PIT','YAW']:
                    _B = ezca['VIS-%s_%s_%s_%s_CP_COEF_%s'%(OPTIC,SENDIAG,motion_DoF,stage,sensor_DoF)]
                    _theta_b = ezca['VIS-%s_%s_%s_%s_REL_PHASE_%s'%(OPTIC,SENDIAG,motion_DoF,stage,sensor_DoF)]

                    _theta = (_theta_a - _theta_b)/180*np.pi
                    
                    _AA,_BB = self.calc_major_axis(_A,_B,_theta)
                    _sensing_vector.append(_BB/_AA)
                    if abs(_sensing_vector[-1]) < 1e-3:
                        _sensing_vector[-1] = 0

                _t_sensing_matrix[ii] = _sensing_vector
                
            ii += 1
        sensing_matrix = np.transpose(_t_sensing_matrix)
        diag_matrix = np.linalg.inv(sensing_matrix)
        
        for ii in range(len(diag_matrix)):
            diag_matrix[ii] = diag_matrix[ii]/diag_matrix[ii][ii]
        return diag_matrix


    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0
        self.timer['speaking'] = 0

    def run(self):
        if ezca['VIS-%s_MTRX_LOCK'%OPTIC]:
            if self.timer['speaking']:
                kagralib.speak_aloud('Sensing and actuator matrices are locke. I cannot change it')
                self.timer['speaking'] = 300
            return True
        
        if self.counter == 0:
            for model in ['MOD','VIS']:
                DECPL = {stage:cdsutils.CDSMatrix(
                    '%s-%s_DIAG_DECPL_%s'%(model,OPTIC,stage),
                    cols={ii+1: ii+1 for ii in range(6)},
                    rows={ii+1: ii+1 for ii in range(6)},                
                ) for stage in ['IP','BF','MN','IM','TM']}
            
                for stage in ['BF','MN','IM','TM']:
                    if ezca['VIS-%s_MTRX_LOCK'%(OPTIC)]:
                        kagralib.speak_aloud('Decoupling Matrix is locked. I cannot change it')
                        self.counter += 1
                        return 
                    DECPL[stage].put_matrix(np.dot(self.calc_SENSDIAG_matrix(stage),DECPL[stage].get_matrix()),)
            self.counter += 1

        else:
            return True


class SENSOR_DIAGONALIZATION_GAS(GuardState):
    index = 251
    request = True

    def calc_major_axis(self,A,B,theta):
        # calc major axis of elliptic described as x = A*cos(t), y = B*cos(t+theta)
        # 2020/08/02 by MN
        # calculate t which X = x**2 + y**2 got maximum.
        # dX/dt =  a*sin(2t)+b*cos(2t) = sqt(a**2+b**2)*sin(2t+alpha) = 0,
        # where a, b and alpha is drived as in the script.
        # major axis can be derived as x = A*cos(-alpha/2), y = B*cos(-alpha/2+theta)
    
        a = (A**2+B**2*np.cos(2*theta))
        b = B**2*np.sin(2*theta)
        alpha = np.arcsin(b/np.sqrt(a**2+b**2))
        
        x = A*np.cos(-alpha/2)
        y = B*np.cos(-alpha/2+theta)
        
        return x,y

    def calc_SENSDIAG_matrix(self):
        _t_sensing_matrix = np.identity(5)
        ii = 0
            
        for ii in range(1,6):
            stage = 'GAS'
            _sensing_vector = []
            _A = ezca['PRE-%s_SENSDIAG_GAS_RATIO_%d_%d'%(OPTIC,ii,ii)]
            _theta_a = ezca['PRE-%s_SENSDIAG_GAS_PHASE_%d_%d'%(OPTIC,ii,ii)]
            
            if _A == 0:
                log('skip this DoF')
                
            else:
                for jj in range(1,6):
                    _B = ezca['PRE-%s_SENSDIAG_GAS_RATIO_%d_%d'%(OPTIC,jj,ii)]
                    _theta_b = ezca['PRE-%s_SENSDIAG_GAS_PHASE_%d_%d'%(OPTIC,jj,ii)]

                    _theta = (_theta_a - _theta_b)/180*np.pi
                    
                    _AA,_BB = self.calc_major_axis(_A,_B,_theta)
                    _sensing_vector.append(_BB/_AA)
                    if abs(_sensing_vector[-1]) < 1e-3:
                        _sensing_vector[-1] = 0

                _t_sensing_matrix[ii-1] = _sensing_vector
                
        sensing_matrix = np.transpose(_t_sensing_matrix)
        diag_matrix = np.linalg.inv(sensing_matrix)
        
        for ii in range(len(diag_matrix)):
            diag_matrix[ii] = diag_matrix[ii]/diag_matrix[ii][ii]
        return diag_matrix


    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0
        self.timer['speaking'] = 0

    def run(self):
        if ezca['VIS-%s_MTRX_LOCK_GAS'%OPTIC]:
            if self.timer['speaking']:
                kagralib.speak_aloud('Sensing and actuator matrices are locked. I cannot change it')
                self.timer['speaking'] = 300
            return True
        
        if self.counter == 0:
            for model in ['MOD','VIS']:
                DECPL = cdsutils.CDSMatrix(
                    '%s-%s_DIAG_DECPL_GAS'%(model,OPTIC),
                    cols={ii+1: ii+1 for ii in range(5)},
                    rows={ii+1: ii+1 for ii in range(5)},                
                )
            

                DECPL.put_matrix(np.dot(self.calc_SENSDIAG_matrix(),DECPL.get_matrix()),)
            self.counter += 1

        else:
            return True
                

class SENSOR_CALIBRATION(GuardState):
    # Calibrate PIT YAW sensors in MN, IM at DC with the reference of TM sensor.
    # Then, ROL is calibrated so that ROL and PIT has same order of values when same counts is input to the actuator.
    # Same for YAW v.s. LEN and YAW v.s. TRA
    index = 255
    request = True

    def get_data(self):
        _data = cdsutils.getdata(self.chans,self.avgduration)
        data = {self.chans[ii]: np.average(_data[ii].data) for ii in range(len(self.chans))}
        return data
        
    def main(self):
        self.ofs_dict = {
            'LEN':20000,
            'TRA':10000,
            'ROL':5000,
            'PIT':5000,
            'YAW':1000
        }
        self.DoFlist = ['LEN','TRA','ROL','PIT','YAW']
        self.stagelist = ['MN','IM']
        
        self.counter = 0
        self.timer['waiting'] = 0

        
        self.chans = ['K1:VIS-%s_%s_DIAG_%s_INMON'%(OPTIC,stage,DoF) for stage in ['MN','IM','TM'] for DoF in self.DoFlist]

        self.TRAMP = 15 #ramptime for offset
        self.avgduration = 10 # average duration for each data
        self.settletime = 5 # settle time after put/remove offset
        self.DoFindex = 0
        self.stageindex = 0
        self.dif = {stage:{} for stage in self.stagelist}
        
                                                                                                              
    def run(self):
        if not self.timer['waiting']:
            return

        # initialize INF
        if self.counter == 0:
            #engage length oplev
            ezca['VIS-%s_TM_DIAG_SEN2EUL_1_4'%OPTIC] = 1
            for stage in self.stagelist:
                for DoF in self.DoFlist:
                    INF = ezca.get_LIGOFilter('VIS-%s_%s_DIAG_%s'%(OPTIC,stage,DoF))
                    INF.ramp_gain(1,0,False)
                    INF.ramp_offset(0,0,False)

                    SUMOUT = ezca.get_LIGOFilter('VIS-%s_%s_SUMOUT_%s'%(OPTIC,stage,DoF[0]))
                    SUMOUT.ramp_gain(1,5,False)
                    SUMOUT.ramp_offset(0,5,False)
                    SUMOUT.turn_on('OFFSET')

                    if SUMOUT.is_offset_ramping() or SUMOUT.is_gain_ramping():
                        self.timer['waiting'] = 5
            self.counter += 1 

        # take reference value
        elif self.counter == 1:
            self.ref = self.get_data()
            self.counter += 1

        # put offset
        elif self.counter == 2:
            DoF = self.DoFlist[self.DoFindex]
            stage = 'MN'
            SUMOUT = ezca.get_LIGOFilter('VIS-%s_%s_SUMOUT_%s'%(OPTIC,stage,DoF[0]))
            SUMOUT.ramp_offset(self.ofs_dict[DoF],self.TRAMP)
            self.timer['waiting'] = self.TRAMP + self.settletime
            self.counter += 1

        # take average and remove offset
        elif self.counter == 3:
            DoF = self.DoFlist[self.DoFindex]
            stage = 'MN'
            _data = self.get_data()
            self.dif[DoF] = {key: _data[key] - self.ref[key] for key in _data.keys()}
            SUMOUT = ezca.get_LIGOFilter('VIS-%s_%s_SUMOUT_%s'%(OPTIC,stage,DoF[0]))
            SUMOUT.ramp_offset(0,self.TRAMP)
            self.timer['waiting'] = self.TRAMP + self.settletime
            self.counter += 1

        # if all DoF has been done, go next. Otherwise go back counter 2
        elif self.counter == 4:
            self.DoFindex += 1
            if self.DoFindex >= len(self.DoFlist):
                self.counter += 1
            else:
                self.counter = 2
                
        elif self.counter == 5:
            for stage in self.stagelist:
                # take ratio of PS diffrence to OL difference
                for DoF in ['PIT','YAW','LEN']:
                    OLkey = 'K1:VIS-%s_TM_DIAG_%s_INMON'%(OPTIC,DoF)
                    stagekey = 'K1:VIS-%s_%s_DIAG_%s_INMON'%(OPTIC,stage,DoF)
                    log('Difference when move in %s'%DoF)
                    log('OL: %f, %s: %f'%(self.dif[DoF][OLkey],stage,self.dif[DoF][stagekey]))
                    toOL = self.dif[DoF][OLkey]/self.dif[DoF][stagekey]
                    ezca['VIS-%s_%s_DIAG_%s_GAIN'%(OPTIC,stage,DoF)] = toOL

                for DoF in ['TRA']:
                    Lenkey = 'K1:VIS-%s_%s_DIAG_LEN_INMON'%(OPTIC,stage)
                    DoFkey = 'K1:VIS-%s_%s_DIAG_%s_INMON'%(OPTIC,stage,DoF)
                    
                    log('Difference when move in %s'%DoF)
                    log('%f'%(self.dif[DoF][OLkey]))
                    
                    toLen = (self.dif['LEN'][Lenkey]/self.ofs_dict['LEN'])/(self.dif[DoF][DoFkey]/self.ofs_dict[DoF])
                    ezca['VIS-%s_%s_DIAG_%s_GAIN'%(OPTIC,stage,DoF)] = ezca['VIS-%s_%s_DIAG_YAW_GAIN'%(OPTIC,stage)] * toLen

                for DoF in ['ROL']:
                    Pitkey = 'K1:VIS-%s_%s_DIAG_PIT_INMON'%(OPTIC,stage)
                    DoFkey = 'K1:VIS-%s_%s_DIAG_%s_INMON'%(OPTIC,stage,DoF)

                    log('Difference when move in %s'%DoF)
                    log('%f'%(self.dif[DoF][OLkey]))
                    
                    toPit = (self.dif['PIT'][Pitkey]/self.ofs_dict['PIT'])/(self.dif[DoF][DoFkey]/self.ofs_dict[DoF])
                    ezca['VIS-%s_%s_DIAG_%s_GAIN'%(OPTIC,stage,DoF)] = ezca['VIS-%s_%s_DIAG_PIT_GAIN'%(OPTIC,stage)] * toPit
            self.counter += 1
            ezca['VIS-%s_TM_DIAG_SEN2EUL_1_4'%OPTIC] = 0
        elif self.counter == 6:
            return True

    
    
# common functions for ACT_DIAG_TOWER, PAYLOAD
def getData(channels,avgtime):
    _data = cdsutils.getdata(channels,avgtime)
    data = {channels[ii]:np.average(_data[ii].data) for ii in range(len(channels))}
    std = {channels[ii]:np.std(_data[ii].data) for ii in range(len(channels))}
    return data,std

def make_strresult(data,doflist):
    strresult = '('
    for DoF in doflist:
        for key in data:
            if DoF in key:
                strresult += DoF + ':' + str(data[key]) + ','
    strresult = strresult[:-1] + ')'
    return strresult

# diagonalization of actuator to sensor basis.
def diag_main(self):
    self.DoFindex = {'LEN':1,'TRA':2,'VER':3,'ROL':4,'PIT':5,'YAW':6}
    self.currentstage = 0
    self.DoFlist = {
        'IP':['LEN','TRA','YAW'],
        'BF':['LEN','TRA','YAW'],
        'MN':['LEN','TRA','ROL','PIT','YAW'],
        'TM':['PIT','YAW'],
    }
    self.currentDoF = 0
    self.coillist = {
        'IP':{'V1':1,'V2':2,'V3':3,'H1':4,'H2':5,'H3':6},
        'BF':{'V1':1,'V2':2,'V3':3,'H1':4,'H2':5,'H3':6},
        'MN':{'V1':1,'V2':2,'V3':3,'H1':4,'H2':5,'H3':6},
        'IM':{'V1':1,'V2':2,'V3':3,'H1':4,'H2':5,'H3':6},
        'TM':{'H1':1,'H2':2,'H3':3,'H4':4},
    }
    
    # put offset so that the maximum input get this vlue
    self.maxoutput_dict = {'IP':1000,'BF':5000,'MN':10000}
    
    self.offset_dict = {}
    self.TRAMP = {'IP':30,'BF':30,'MN':15}
    self.avgtime = {'IP':40,'BF':40,'MN':15}
    self.settletime = {'IP':15,'BF':15,'MN':15}

        
    ##### Define logger
    _t = time.localtime()
    keys = ['YEAR','MON','DAY','HOUR','MIN','SEC']
    self.time = {
        keys[ii]:_t[ii] for ii in range(len(keys))
    }
    
    self.figdir = '/users/Measurements/VIS/ITMY/PREQUA/suspension_initialization'
    self.figdir_archive = '/users/Measurements/VIS/ITMY/PREQUA/suspension_initialization/archive/'
    
    kagralib.mkdir(self.figdir)
    kagralib.mkdir(self.figdir_archive)
    
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
    
    
    self.counter = 0
    self.timer['waiting'] = 0
    self.timer['speaking'] = 0
    
def diag_run(self):
    if ezca['VIS-%s_MTRX_LOCK'%OPTIC]:
        if self.timer['speaking']:
            kagralib.speak_aloud('Sensing and actuator matrices are locke. I cannot change it')
            self.timer['speaking'] = 300
        return True

        
    if not self.timer['waiting']:
        return
    
    if self.counter == 0:
        #initialize SUMOUT
        for stage in self.stagelist:
            self.offset_dict[stage] = {}
            for DoF in self.DoFlist[stage]:
                SUMOUT = ezca.get_LIGOFilter('MOD-%s_SUM_%s_%s'%(OPTIC,stage,DoF))
                SUMOUT.ramp_offset(0,self.TRAMP[stage],False)
                
                # make ofsdict so that maximum coil output got max output
                decpl = np.zeros((6,6))
                eul2coil = np.zeros((len(self.coillist[stage]),6))
                for ii in range(len(decpl)):
                    for jj in range(len(decpl[ii])):
                        decpl[ii,jj] = ezca['MOD-%s_DRIVEDECPL_%s_%d_%d'%(OPTIC,stage,ii+1,jj+1)]
                for ii in range(len(eul2coil)):
                    for jj in range(len(eul2coil[ii])):
                        eul2coil[ii,jj] = ezca['MOD-%s_EUL2COIL_%s_%d_%d'%(OPTIC,stage,ii+1,jj+1)]
                dof2coil = np.dot(eul2coil,decpl)
                _maximumoffset = []                                
                for coil in self.coillist[stage].keys():
                    if not (stage=='IP' and 'V' in coil):
                        _maximumoffset.append(abs(self.maxoutput_dict[stage]/
                                                  SUMOUT.GAIN.get()/
                                                  ezca['VIS-%s_%s_COILOUTF_%s_GAIN'%(OPTIC,stage,coil)]/
                                                  dof2coil[self.coillist[stage][coil]-1,self.DoFindex[DoF]-1]))
                            
                log('%s %s _maximumoffset=%s'%(stage,DoF,str(_maximumoffset)))
                self.offset_dict[stage][DoF] = min(_maximumoffset)

                # yaw offset is reduced since our yaw actuator is too strong due to the super low resonant frequency
                if DoF == 'YAW':
                    self.offset_dict[stage][DoF] /= 10.
                    
            if SUMOUT.is_offset_ramping() or SUMOUT.is_gain_ramping():
                self.timer['waiting'] = self.TRAMP[stage]
            
        self.counter += 1
            

    elif self.counter == 1:
        # take reference
        self.stage = self.stagelist[self.currentstage]
        
        if self.currentDoF == 0:
            #initialize _t_actmat
            self._t_actmat = np.identity(len(self.DoFlist[self.stage]))
                
            
        self.channels = ['K1:VIS-%s_DIAG_CAL_%s_%s_INMON'%(OPTIC,self.stage,DoF) for DoF in self.DoFlist[self.stage]]
        log(self.channels)
        self.DoF = self.DoFlist[self.stage][self.currentDoF]
        self.logger.debug('--------------- %s dif measurement ---------------------'%self.DoF)            

        # transpose of actuator matrix
            


        self.ref,rev_norm_factor = getData(self.channels,self.avgtime[self.stage])
        norm_factor = {key:1./rev_norm_factor[key] for key in rev_norm_factor.keys()}
        self.logger.debug('Reference position')
        strresult = make_strresult(self.ref,self.DoFlist[self.stage])
        self.logger.debug(strresult)
        
        self.counter += 1

    elif self.counter == 2:
        # put offset
        self.logger.debug('put offset of %f'%self.offset_dict[self.stage][self.DoF])
        self.SUMOUT = ezca.get_LIGOFilter('MOD-%s_SUM_%s_%s'%(OPTIC,self.stage,self.DoF))
        self.SUMOUT.turn_on('OFFSET')
        self.SUMOUT.ramp_offset(self.offset_dict[self.stage][self.DoF],self.TRAMP[self.stage],False)
        self.timer['waiting'] = self.TRAMP[self.stage] + self.settletime[self.stage]
        self.counter += 1

    elif self.counter == 3:
        # take difference from ref
        shift,_ = getData(self.channels,self.avgtime[self.stage])
        self.logger.debug('Shifted value from reference')
        strresult = make_strresult(shift,self.DoFlist[self.stage])
        self.logger.debug(strresult)
        
        dif = {key:(shift[key]-self.ref[key]) for key in self.ref.keys()}
        self.logger.debug('Difference from reference')
        strresult = make_strresult(dif,self.DoFlist[self.stage])
        self.logger.debug(strresult)
        

        _actvec = []
        for DoF2 in ['LEN','TRA','VER','ROL','PIT','YAW']:
            for key in dif.keys():
                if DoF2 in key:
                    _actvec.append(dif[key])

        actvec = np.array(_actvec) / (self.offset_dict[self.stage][self.DoF] * self.SUMOUT.GAIN.get())
        self._t_actmat[self.currentDoF] = actvec
        log(str(self._t_actmat))
        
        self.SUMOUT.ramp_offset(0,self.TRAMP[self.stage],False)
        self.timer['waiting'] = self.TRAMP[self.stage]+self.settletime[self.stage]
        self.currentDoF += 1
        if self.currentDoF >= len(self.DoFlist[self.stage]):
            self.counter += 1
        else:
            self.counter = 1

            
    elif self.counter == 4:
        actmat = np.transpose(self._t_actmat)
        norm_actmat = np.identity(len(actmat))
        for ii in range(len(actmat)):
            for jj in range(len(actmat)):
                norm_actmat[ii,jj] = actmat[ii,jj] / (actmat[ii,ii])
            
        _DRIVEDECPL = np.linalg.inv(norm_actmat)
    


        # put missing DoF
        missing_DoF = []
        for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']:
            if not DoF in self.DoFlist[self.stage]:
                missing_DoF.append(self.DoFindex[DoF]-1)

                    
        DRIVEDECPL = np.identity(len(self.DoFlist[self.stage])+len(missing_DoF))
    
        iii = 0
        for ii in range(len(self.DoFlist[self.stage])+len(missing_DoF)):
            jjj = 0
            if ii in missing_DoF:
                DRIVEDECPL[ii] = np.zeros((1,len(self.DoFlist[self.stage])+len(missing_DoF)))
            else:
                for jj in range(len(self.DoFlist[self.stage])+len(missing_DoF)):
                    if jj in missing_DoF:
                        DRIVEDECPL[ii,jj] = 0
                    else:
                        DRIVEDECPL[ii,jj] = _DRIVEDECPL[iii,jjj]
                        jjj += 1
                iii += 1
        current_DRIVEDECPL = np.identity(6)
            
        for ii in range(6):
            for jj in range(6):
                current_DRIVEDECPL[ii,jj] = ezca['MOD-%s_DRIVEDECPL_%s_%d_%d'%(OPTIC,self.stage,ii+1,jj+1)]
        _newDRIVEDECPL = np.dot(current_DRIVEDECPL,DRIVEDECPL)

        self.newDRIVEDECPL = np.matrix(np.identity(6))
        for ii in range(6):
            for jj in range(6):
                if not _newDRIVEDECPL[jj,jj] == 0:
                    self.newDRIVEDECPL[ii,jj] = _newDRIVEDECPL[ii,jj]/_newDRIVEDECPL[jj,jj]
                        

        self.logger.debug('New DRIVEDECPL:')
        self.logger.debug(self.newDRIVEDECPL)
        
        self.logger.debug('Differential DRIVEDECPL:')
        self.logger.debug(DRIVEDECPL)

    
        for ii in range(6):
            for jj in range(6):
                ezca['MOD-%s_DRIVEDECPL_%s_%d_%d'%(OPTIC,self.stage,ii+1,jj+1)] = self.newDRIVEDECPL[ii,jj]

        newactmat = np.dot(actmat, _DRIVEDECPL)
        self.logger.debug('New Actuator matrix:')
        self.logger.debug(newactmat)
        
        ii = 0
        for DoF in self.DoFlist[self.stage]:
            SUMOUT = ezca.get_LIGOFilter('MOD-%s_SUM_%s_%s'%(OPTIC,self.stage,DoF))
            SUMOUT.ramp_gain(1./newactmat[ii,ii],1,False)
            ii += 1

            
        kagralib.speak_aloud('%s %s Diagonalized and Calibrated!'%(self.stage[0],self.stage[1]))
        self.currentstage += 1
        self.currentDoF = 0
        if self.currentstage >= len(self.stagelist):
            self.counter += 1
        else:
            self.counter = 1

    elif self.counter == 5:
        return True

class ACT_DIAG_TOWER(GuardState):
    index = 300
    request = True
    
    def main(self):
        diag_main(self)
        self.stagelist = ['IP',]
        self.mycounter = 0
        self.timer['my_waiting'] =0
        
    def run(self):
        if not self.timer['my_waiting']:
            return
        
        # check Guardian status
        if not ezca['GRD-NEW_%s'%OPTIC] == 'FLOAT':
            if self.timer['speak']:
                kagralib.speak_aloud('Guardian must be in float state.')
                self.timer['speak'] = 300
            return

        return diag_run(self)

class ACT_DIAG_PAY(GuardState):
    index = 305
    request = True
    
    
    def main(self):
        diag_main(self)
        self.stagelist = ['MN',]
        self.mycounter = 0
        self.timer['my_waiting'] =0
        
    def run(self):
        if not self.timer['my_waiting']:
            return
        
        # disable DC path
        if self.mycounter == 0:
            for DoF in ['PIT','YAW']:
                OLDC_BF = ezca.get_LIGOFilter('MOD-%s_OLDC_BF_%s'%(OPTIC,DoF))
                OLDC_BF.turn_off('INPUT')
                OLDC_MN = ezca.get_LIGOFilter('MOD-%s_OLDC_MN_%s'%(OPTIC,DoF))
                OLDC_MN.turn_off('INPUT')
                TRAMP = OLDC_MN.OUTPUT.get()/10
                if self.timer['my_waiting']:
                    self.timer['my_waiting'] = TRAMP
                
            self.mycounter += 1

        elif self.mycounter == 1:
            # clear history
            for DoF in ['PIT','YAW']:
                OLDC_MN = ezca.get_LIGOFilter('MOD-%s_OLDC_MN_%s'%(OPTIC,DoF))
                OLDC_MN.RSET.put(2)
                OLDC_MN.ramp_gain(1,0,False)

            self.timer['my_waiting'] = self.settletime['MN']
            self.mycounter += 1

        elif self.mycounter == 2:
            return diag_run(self)
                
                    
                
class ACT_DIAG_GAS(GuardState):
    index = 310
    request = True
    
    # diagonalization of actuator to sensor basis.
    def main(self):
        self.DoFindex = {'M%d'%ii:ii for ii in range(1,6)}
        
        self.currentstage = 0
        self.DoFlist = {
            'GAS':[sysmod.workingGAS[ii-1] for ii in range(1,1+len(sysmod.workingGAS))],
        }
        self.currentDoF = 0
        self.coillist = {
            'GAS':{'F0':1,'F1':2,'F2':3,'F3':4,'BF':5}
        }
        
        # put offset so that the maximum input get this vlue
        self.maxoutput_dict = {'GAS': 1000}
        
        self.offset_dict = {}
        self.TRAMP = {'GAS':20}
        self.avgtime = {'GAS':15}
        self.settletime = {'GAS':30}
        
        
        ##### Define logger
        _t = time.localtime()
        keys = ['YEAR','MON','DAY','HOUR','MIN','SEC']
        self.time = {
            keys[ii]:_t[ii] for ii in range(len(keys))
        }
        
        self.figdir = '/users/Measurements/VIS/ITMY/PREQUA/suspension_initialization'
        self.figdir_archive = '/users/Measurements/VIS/ITMY/PREQUA/suspension_initialization/archive/'
        
        kagralib.mkdir(self.figdir)
        kagralib.mkdir(self.figdir_archive)
        
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
        
        
        self.counter = 0
        self.timer['waiting'] = 0
        self.timer['speaking'] = 0
    
    def run(self):
        # check Guardian status
        if not ezca['GRD-NEW_%s_STATE'%OPTIC] == 'FLOAT':
            if self.timer['speaking']:
                kagralib.speak_aloud('Guardian must be in float state.')
                self.timer['speaking'] = 300
            return

        if ezca['VIS-%s_MTRX_LOCK_GAS'%OPTIC]:
            if self.timer['speaking']:
                kagralib.speak_aloud('Sensing and actuator matrices are locke. I cannot change it')
                self.timer['speaking'] = 300
            return True

        
        if not self.timer['waiting']:
            return
    
        if self.counter == 0:
            #initialize SUMOUT
            stage = 'GAS'
            self.offset_dict[stage] = {}
            for DoF in self.DoFlist[stage]:
                SUMOUT = ezca.get_LIGOFilter('MOD-%s_SUM_%s_%s'%(OPTIC,stage,DoF))
                SUMOUT.ramp_offset(0,self.TRAMP[stage],False)
                
                # make ofsdict so that maximum coil output got max output
                decpl = np.zeros((5,5))
                eul2coil = np.zeros((len(self.coillist[stage]),5))
                for ii in range(len(decpl)):
                    for jj in range(len(decpl[ii])):
                        decpl[ii,jj] = ezca['MOD-%s_DRIVEDECPL_%s_%d_%d'%(OPTIC,stage,ii+1,jj+1)]
                for ii in range(len(eul2coil)):
                    for jj in range(len(eul2coil[ii])):
                        eul2coil[ii,jj] = ezca['MOD-%s_EUL2COIL_%s_%d_%d'%(OPTIC,stage,ii+1,jj+1)]
                dof2coil = np.dot(eul2coil,decpl)
                _maximumoffset = []                                
                for coil in self.coillist[stage].keys():
                    if not (stage=='IP' and 'V' in coil):
                        _maximumoffset.append(abs(self.maxoutput_dict[stage]/
                                                  SUMOUT.GAIN.get()/
                                                  ezca['VIS-%s_%s_COILOUTF_%s_GAIN'%(OPTIC,coil,stage)]/
                                                  dof2coil[self.coillist[stage][coil]-1,self.DoFindex[DoF]-1]))
                            
                log('%s %s _maximumoffset=%s'%(stage,DoF,str(_maximumoffset)))
                self.offset_dict[stage][DoF] = min(_maximumoffset)

                    
            if SUMOUT.is_offset_ramping() or SUMOUT.is_gain_ramping():
                self.timer['waiting'] = self.TRAMP[stage]
            else:
                self.counter += 1
            

        elif self.counter == 1:
            # take reference
            self.stage = 'GAS'
        
            if self.currentDoF == 0:
                #initialize _t_actmat
                self._t_actmat = np.identity(len(self.DoFlist[self.stage]))
                
            
                self.channels = ['K1:VIS-%s_DIAG_CAL_%s_%s_INMON'%(OPTIC,self.stage,DoF) for DoF in self.DoFlist[self.stage]]

            self.DoF = self.DoFlist[self.stage][self.currentDoF]
            self.logger.debug('--------------- %s dif measurement ---------------------'%self.DoF)            

            # transpose of actuator matrix
            


            self.ref,rev_norm_factor = getData(self.channels,self.avgtime[self.stage])
            norm_factor = {key:1./rev_norm_factor[key] for key in rev_norm_factor.keys()}
            self.logger.debug('Reference position')
            strresult = make_strresult(self.ref,self.DoFlist[self.stage])
            self.logger.debug(strresult)
        
            self.counter += 1

        elif self.counter == 2:
            # put offset
            self.logger.debug('put offset of %f'%self.offset_dict[self.stage][self.DoF])
            self.SUMOUT = ezca.get_LIGOFilter('MOD-%s_SUM_%s_%s'%(OPTIC,self.stage,self.DoF))
            self.SUMOUT.turn_on('OFFSET')
            self.SUMOUT.ramp_offset(self.offset_dict[self.stage][self.DoF],self.TRAMP[self.stage],False)
            self.timer['waiting'] = self.TRAMP[self.stage] + self.settletime[self.stage]
            self.counter += 1

        elif self.counter == 3:
            # take difference from ref
            shift,_ = getData(self.channels,self.avgtime[self.stage])
            self.logger.debug('Shifted value from reference')
            strresult = make_strresult(shift,self.DoFlist[self.stage])
            self.logger.debug(strresult)
            
            dif = {key:(shift[key]-self.ref[key]) for key in self.ref.keys()}
            self.logger.debug('Difference from reference')
            strresult = make_strresult(dif,self.DoFlist[self.stage])
            self.logger.debug(strresult)
                

            _actvec = []
            for DoF2 in ['M1','M2','M3','M4','M5']:
                for key in dif.keys():
                    if DoF2 in key:
                        _actvec.append(dif[key])

            actvec = np.array(_actvec) / (self.offset_dict[self.stage][self.DoF] * self.SUMOUT.GAIN.get())
            self._t_actmat[self.currentDoF] = actvec
            log(str(self._t_actmat))
            
            self.SUMOUT.ramp_offset(0,self.TRAMP[self.stage],False)
            self.timer['waiting'] = self.TRAMP[self.stage]+self.settletime[self.stage]
            self.currentDoF += 1
            if self.currentDoF >= len(self.DoFlist[self.stage]):
                self.counter += 1
            else:
                self.counter = 1

            
        elif self.counter == 4:
            actmat = np.transpose(self._t_actmat)
            norm_actmat = np.identity(len(actmat))
            for ii in range(len(actmat)):
                for jj in range(len(actmat)):
                    norm_actmat[ii,jj] = actmat[ii,jj] / (actmat[ii,ii])
                    
            _DRIVEDECPL = np.linalg.inv(norm_actmat)
                


            # put missing DoF
            missing_DoF = []
            for DoF in ['M1','M2','M3','M4','M5']:
                if not DoF in self.DoFlist[self.stage]:
                    missing_DoF.append(self.DoFindex[DoF]-1)
                    
                    
            DRIVEDECPL = np.identity(len(self.DoFlist[self.stage])+len(missing_DoF))
            
            iii = 0
            for ii in range(len(self.DoFlist[self.stage])+len(missing_DoF)):
                jjj = 0
                if ii in missing_DoF:
                    DRIVEDECPL[ii] = np.zeros((1,len(self.DoFlist[self.stage])+len(missing_DoF)))
                else:
                    for jj in range(len(self.DoFlist[self.stage])+len(missing_DoF)):
                        if jj in missing_DoF:
                            DRIVEDECPL[ii,jj] = 0
                        else:
                            DRIVEDECPL[ii,jj] = _DRIVEDECPL[iii,jjj]
                            jjj += 1
                    iii += 1
                        
            current_DRIVEDECPL = np.identity(5)
            for ii in range(5):
                for jj in range(5):
                    current_DRIVEDECPL[ii,jj] = ezca['MOD-%s_DRIVEDECPL_%s_%d_%d'%(OPTIC,self.stage,ii+1,jj+1)]
            _newDRIVEDECPL = np.dot(current_DRIVEDECPL,DRIVEDECPL)

            self.newDRIVEDECPL = np.matrix(np.identity(6))
            for ii in range(5):
                for jj in range(5):
                    if not _newDRIVEDECPL[jj,jj] == 0:
                        self.newDRIVEDECPL[ii,jj] = _newDRIVEDECPL[ii,jj]/_newDRIVEDECPL[jj,jj]
                        

            self.logger.debug('New DRIVEDECPL:')
            self.logger.debug(self.newDRIVEDECPL)
            
            self.logger.debug('Differential DRIVEDECPL:')
            self.logger.debug(DRIVEDECPL)
            
    
            for ii in range(5):
                for jj in range(5):
                    ezca['MOD-%s_DRIVEDECPL_%s_%d_%d'%(OPTIC,self.stage,ii+1,jj+1)] = self.newDRIVEDECPL[ii,jj]

            newactmat = np.dot(actmat, _DRIVEDECPL)
            self.logger.debug('New Actuator matrix:')
            self.logger.debug(newactmat)
            
            ii = 0
            for DoF in self.DoFlist[self.stage]:
                SUMOUT = ezca.get_LIGOFilter('MOD-%s_SUM_%s_%s'%(OPTIC,self.stage,DoF))
                SUMOUT.ramp_gain(1./newactmat[ii,ii],1,False)
                ii += 1

            
            kagralib.speak_aloud('%s %s Diagonalized and Calibrated!'%(self.stage[0],self.stage[1]))
            
            self.counter += 1

        elif self.counter == 5:
            return True
            
                
        
        
    
    

##################################################
# EDGES
##################################################

edges = [('INIT','STANDBY'),
         ('STANDBY','INIT_SIGNAL_PROC'),
         ('INIT_SIGNAL_PROC','ZERO_SENSOFS'),
         ('ZERO_SENSOFS','INIT_OUTPUT'),
         ('STANDBY','INIT_PREQUA'),
         ('INIT_PREQUA','CLOSE_PLL'),
         ('CLOSE_PLL','EXCITE_RESONANCE'),
         ('EXCITE_RESONANCE','STANDBY'),
         ('STANDBY','INIT_PREQUA_GAS'),
         ('INIT_PREQUA_GAS','CLOSE_PLL_GAS'),
         ('CLOSE_PLL_GAS','EXCITE_RESONANCE_GAS'),
         ('EXCITE_RESONANCE_GAS','STANDBY'),
         ('EXCITE_RESONANCE_GAS','RECORD_MEASUREMENT_GAS'),
         ('RECORD_MEASUREMENT_GAS','EXCITE_RESONANCE_GAS'),         
         ('EXCITE_RESONANCE','RECORD_MEASUREMENT'),
         ('RECORD_MEASUREMENT','EXCITE_RESONANCE'),
         ('STANDBY','SENSOR_DIAGONALIZATION'),
         ('SENSOR_DIAGONALIZATION','ACT_DIAG_TOWER'),
         ('ACT_DIAG_TOWER','ACT_DIAG_PAY'),
         ('ACT_DIAG_PAY','SENSOR_CALIBRATION'),
         ('SENSOR_CALIBRATION','STANDBY')
]
