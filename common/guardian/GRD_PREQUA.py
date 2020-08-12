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
        LPfreq = {'IP':10,'BF':10,'MN':100,'IM':100,'TM':100} # frequency of BLP
        senstype = {'IP':'LVDT','BF':'LVDT','MN':'PS','IM':'PS'} 

        for stage in ['IP','BF','MN','IM','TM']:
            for sensor in ['H1','H2','H3','V1','V2','V3']:
                kagralib.foton_comb(self.QUA_FBs,'%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),0,freq=60,Q=100,amplitude=-100,force=True)
                kagralib.foton_butter(self.QUA_FBs,'%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),1,freq=LPfreq[stage],order=3,force=True)
                kagralib.foton_comb(self.MODAL_FBs,'%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),0,freq=60,Q=100,amplitude=-100,force=True)
                kagralib.foton_butter(self.MODAL_FBs,'%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),1,freq=LPfreq[stage],order=3,force=True)

                if stage in ['MN','IM']:
                    kagralib.foton_zpk(self.QUA_FBs,'%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),2,z=[12.3,],p=[0.46,],k=1,name='de-white',force=True)
                    kagralib.foton_zpk(self.MODAL_FBs,'%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),2,z=[12.3,],p=[0.46,],k=1,name='de-white',force=True)

                ezca.switch('VIS-%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),'FM1','FM2','FM3','ON')
                ezca.switch('MOD-%s_DIAG_SENSIN_%s_%s'%(OPTIC,stage,sensor),'FM1','FM2','FM3','ON')
                if not stage == 'TM' and not (stage == 'IP' and sensor in ['V1','V2','V3']):
                    ezca['VIS-%s_DIAG_SENSIN_%s_%s_GAIN'%(OPTIC,stage,sensor)] = np.sign(ezca['VIS-%s_%s_%sINF_%s_GAIN'%(OPTIC,stage,senstype[stage],sensor)])
                    ezca['MOD-%s_DIAG_SENSIN_%s_%s_GAIN'%(OPTIC,stage,sensor)] = np.sign(ezca['VIS-%s_%s_%sINF_%s_GAIN'%(OPTIC,stage,senstype[stage],sensor)])

                                                        


        self.QUA_FBs.write()
        self.MODAL_FBs.write()
        
        # Initialize SEN2EUL if mtrx_lock is false
        DIAG_SEN2EUL = {model:{stage:cdsutils.CDSMatrix(
            '%s-%s_DIAG_SEN2EUL_%s'%(model,OPTIC,stage),
            cols={ii+1: ii+1 for ii in range(6)},
            rows={ii+1: ii+1 for ii in range(6)},
        ) for stage in ['IP','BF','MN','IM','TM']} for model in ['VIS','MOD']
                        }
        if not ezca['VIS-%s_MTRX_LOCK'%OPTIC]:
            for model in ['VIS','MOD']:
                DIAG_SEN2EUL[model]['IP'].put_matrix(
                    np.matrix([[0,0,0,2./3.,-1./3.,-1./3.],
                               [0,0,0,0,-1./np.sqrt(3),1./np.sqrt(3)],
                               [0,0,0,0,0,0],
                               [0,0,0,0,0,0],
                               [0,0,0,0,0,0],
                               [0,0,0,1./np.sqrt(3),1./np.sqrt(3),1./np.sqrt(3)]]
                          ))

            
                DIAG_SEN2EUL[model]['BF'].put_matrix(
                    np.matrix([[0,0,0,2./3.,-1./3.,-1./3.],
                               [0,0,0,0,-1./np.sqrt(3),1./np.sqrt(3)],
                               [1./3.,1./3.,1./3.,0,0,0],
                               [-0.9157,-0.9157,1.83150,0,0,0],
                               [-1.5861,1.5861,0,0,0,0],
                               [0,0,0,0.8170,0.8170,0.8170]]
                          ))

                for stage in ['IM','MN']:
                    DIAG_SEN2EUL[model][stage].put_matrix(
                        np.matrix([[0,0,0,1./2.,1./2.,0],
                                   [0,0,0,-1./2.,1./2.,1],
                                   [-1./2.,0,-1./2.,0,0,0],
                                   [1./2.,-1,1./2.,0,0,0],
                                   [1./2.,0,-1./2.,0,0,0],
                                   [0,0,0,1./2.,-1./2.,0]]
                              ))
                
                

                DIAG_SEN2EUL[model]['TM'].put_matrix(
                    np.matrix([[0,0,0,0,1,0],
                               [0,0,0,0,0,0],
                               [0,0,0,0,0,0],
                               [0,0,0,0,0,0],
                               [1,0,0,0,0,0],
                               [0,0,0,1,0,0],]
                          ))
                

                # Initialize DECPL
        
                DIAG_DECPL = {model:{stage:cdsutils.CDSMatrix(            
                    '%s-%s_DIAG_DECPL_%s'%(model,OPTIC,stage),
                    cols={ii+1: ii+1 for ii in range(6)},
                    rows={ii+1: ii+1 for ii in range(6)},
                ) for stage in ['IP','BF','MN','IM','TM']} for model in ['VIS','MOD']
                          }
                

                for model in ['VIS','MOD']:
                    for stage in ['IP','BF','MN','IM','TM']:
                        DIAG_DECPL[model][stage].put_matrix(np.matrix(np.identity(6)))
                        
                    for key in sysmod.initDECPL.keys():
                        DIAG_DECPL[model][key].put_matrix(np.matrix(sysmod.initDECPL[key]))
                
        # initialize CAL
        for model in ['VIS','MOD']:
            ezca['%s-%s_DIAG_CAL_TM_PIT_GAIN'%(model,OPTIC)] = ezca['VIS-%s_TM_OPLEV_TILT_PIT_GAIN'%OPTIC]
            ezca['%s-%s_DIAG_CAL_TM_YAW_GAIN'%(model,OPTIC)] = ezca['VIS-%s_TM_OPLEV_TILT_YAW_GAIN'%OPTIC]
            ezca['%s-%s_DIAG_CAL_TM_LEN_GAIN'%(model,OPTIC)] = ezca['VIS-%s_TM_OPLEV_LEN_YAW_GAIN'%OPTIC]
            
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
        darkchans = ['K1:%s-%s_DIAG_SENSIN_%s_%s_INMON'%(model,OPTIC,stage,sensor) for model in ['MOD','VIS']for stage in ['IP','BF','MN','IM'] for sensor in ['V1','V2','V3','H1','H2','H3']]
        _data = cdsutils.getdata(darkchans,10)
        dark = {darkchans[ii]:np.average(_data[ii].data) for ii in range(len(darkchans))}
        for stage in ['IP','BF','MN','IM']:
            for sensor in ['V1','V2','V3','H1','H2','H3']:
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
        
        for stage in ['IP','BF','MN','IM','TM']:
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
                kagralib.foton_zpk(self.MODAL_FBs,'%s_DAMP_%s_%s'%(OPTIC,stage,DoF),1,z=[0,],p=[40],k=1,force=True)
                ezca['MOD-%s_DAMP_%s_%s_GAIN'%(OPTIC,stage,DoF)] = 0
                ezca.switch('MOD-%s_DAMP_%s_%s'%(OPTIC,stage,DoF),'FM1','FM2','ON')
        # OLDC initialization
        for DoF in ['PIT','YAW']:
            ezca['MOD-%s_OLDC_SETPOINT_%s_TRAMP'%(OPTIC,DoF)] = 0.5
            ezca.switch('MOD-%s_OLDC_SETPOINT_%s'%(OPTIC,DoF),'OFFSET','ON')
            
            kagralib.foton_zpk(self.MODAL_FBs,'%s_OLDC_MN_%s'%(OPTIC,DoF),9,z=[],p=[0,],k=1,force=True)
            kagralib.foton_gain(self.MODAL_FBs,'%s_OLDC_MN_%s'%(OPTIC,DoF),0,0.01,name='0.01Hz',force=True)
            kagralib.foton_gain(self.MODAL_FBs,'%s_OLDC_MN_%s'%(OPTIC,DoF),1,0.1,name='0.1Hz',force=True)
            kagralib.foton_gain(self.MODAL_FBs,'%s_OLDC_MN_%s'%(OPTIC,DoF),8,-1,force=True)

            ezca.switch('MOD-%s_OLDC_MN_%s'%(OPTIC,DoF),'FM1','FM10','ON','INPUT','OFF')

            kagralib.foton_zpk(self.MODAL_FBs,'%s_OLDC_BF_%s'%(OPTIC,DoF),9,z=[],p=[0,],k=1,force=True)
            kagralib.foton_gain(self.MODAL_FBs,'%s_OLDC_BF_%s'%(OPTIC,DoF),0,0.001,'1mHz',force=True)

            ezca.switch('MOD-%s_OLDC_MN_%s'%(OPTIC,DoF),'FM1','FM9','FM10','ON','INPUT','OFF')
            ezca.switch('MOD-%s_OLDC_BF_%s'%(OPTIC,DoF),'FM1','FM10','ON','INPUT','OFF')
            

        # IPDC initialization
        for DoF in ['LEN','TRA','YAW']:
            ezca['MOD-%s_IPDC_SETPOINT_%s_TRAMP'%(OPTIC,DoF)] = 0.5
            ezca.switch('MOD-%s_IPDC_SETPOINT_%s'%(OPTIC,DoF),'OFFSET','ON')
            
            kagralib.foton_zpk(self.MODAL_FBs,'%s_IPDC_%s'%(OPTIC,DoF),9,z=[],p=[0,],k=1,force=True)
            kagralib.foton_gain(self.MODAL_FBs,'%s_IPDC_%s'%(OPTIC,DoF),0,0.001,name='1mHz',force=True)
            kagralib.foton_gain(self.MODAL_FBs,'%s_IPDC_%s'%(OPTIC,DoF),1,0.01,name='10mHz',force=True)
            kagralib.foton_gain(self.MODAL_FBs,'%s_IPDC_%s'%(OPTIC,DoF),8,-1,force=True)

            ezca.switch('MOD-%s_IPDC_%s'%(OPTIC,DoF),'FM1','FM0','FM10','ON','INPUT','OFF')

            
        self.MODAL_FBs.write()
        self.TOWER_FBs.write()
        self.PAYLOAD_FBs.write()

        # Output matrices initialization

        if not ezca['VIS-%s_MTRX_LOCK'%OPTIC]:
            DECPL = {stage:cdsutils.CDSMatrix(            
                'MOD-%s_DRIVEDECPL_%s'%(OPTIC,stage),
                cols={ii+1: ii+1 for ii in range(6)},
                rows={ii+1: ii+1 for ii in range(6)},
            ) for stage in ['IP','BF','MN','IM','TM']}

            for stage in DECPL.keys():
                DECPL[stage].put_matrix(
                    np.identity(6)
                )
                
            MOD_EUL2COIL = {stage:cdsutils.CDSMatrix(            
                'MOD-%s_EUL2COIL_%s'%(OPTIC,stage),
                cols={ii+1: ii+1 for ii in range(6)},
                rows={ii+1: ii+1 for ii in range(6)},
            ) for stage in ['IP','BF','MN','IM','TM']}
                
            MOD_EUL2COIL['IP'].put_matrix(
                np.matrix([[0,0,0,0,0,0,],
                           [0,0,0,0,0,0,],
                           [0,0,0,0,0,0,],
                           [2./3.,0,0,0,0,1/np.sqrt(3)],
                           [-1./3.,-1./np.sqrt(3),0,0,0,1./np.sqrt(3)],
                           [-1./3.,1/np.sqrt(3),0,0,0,1./np.sqrt(3)]]
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
                MOD_EUL2COIL[stage].put_matrix(
                    np.matrix([[0,0,0.5,-0.5,-0.5,0],
                               [0,0,0,1,0,0],
                               [0,0,0.5,-0.5,0.5,0],
                               [-0.5,0.5,0,0,0,-0.5],
                               [-0.5,-0.5,0,0,0,0.5],
                               [0,-1,0,0,0,0]]
                          ))
            
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
        for dcuid in [sysmod.MONDCUID,sysmod.MODALDCUID,sysmod.PDCUID,sysmod.TDCUID]:
            if int(ezca['FEC-%d_STATE_WORD'%dcuid]) & 0b10000000000:
                ezca['FEC-%d_LOAD_NEW_COEFF'%dcuid] = 1



        
    def run(self):
        if any([int(ezca['FEC-%d_STATE_WORD'%dcuid]) & 0b10000000000 for dcuid in [sysmod.MONDCUID,sysmod.MODALDCUID,sysmod.PDCUID,sysmod.TDCUID]]):
            notify('Waiting to load coefficients!')
        else:
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
            for stage in ['IP','BF','MN','IM','TM']:
                for DoF in DoFList:
                    # channel name 
                    QUAname = 'VIS-%s_%s_QUA%s'%(OPTIC,stage,DoF)
                    
                    # reset SIG filter
                    ezca[QUAname+'_PLL_DEMOD_SIG_RSET'] = 2
                    ezca[QUAname+'_PLL_DEMOD_SIG_RMS_RSET'] = 2
                    ezca[QUAname+'_PLL_DEMOD_AMP_RSET'] = 2                    
                    ezca[QUAname+'_PLL_DEMOD_I_RSET'] = 2
                    ezca[QUAname+'_PLL_DEMOD_Q_RSET'] = 2
                    
            for stage in ['IP','BF','MN','IM','TM']:
                for param in ['AMP','REF_PHASE','FREQ','Q_VAL','DECAY_TIME']:
                    for ii in range(6):
                        ezca['VIS-%s_%s_DOF_SEL_%s_1_%d'%(OPTIC,stage,param,ii+1)] = (DoFList[ii] == self.modeDoF)
            for param in ['REF_PHASE','FREQ','Q_VAL','DECAY_TIME']:
                for ii in range(5):
                    ezca['VIS-%s_STAGE_SEL_%s_1_%d'%(OPTIC,param,ii+1)] = (['IP','BF','MN','IM','TM'][ii] == self.modeStage)
            self.counter += 1
                
        elif self.counter == 2:
            if int(ezca['FEC-%d_STATE_WORD'%sysmod.MONDCUID]) & 0b10000000000:
                notify('Waiting to load coefficients!')
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
            DoFindex = {'LEN':1,'TRA':2,'VER':3,'ROL':4,'PIT':5,'YAW':6}
            for ii in range(6):
                ezca['VIS-%s_PAY_OLSERVO_PK2EUL_%d_26'%(OPTIC,4+ii)] = ezca['MOD-%s_DRIVEDECPL_MN_%d_%d'%(OPTIC,ii+1,DoFindex[self.modeDoF])]
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

            for stage in ['IP','BF','MN','IM','TM']:
                for DoF in DoFList:
                    self.logger.debug('- %s %s'%(stage,DoF))
                    self.logger.debug('Coupling coefficient: %f'%(ezca[self.prefix[3:]+'%s_CP_COEF_%s'%(stage,DoF)]))
                    self.logger.debug('Relative phase: %f'%(np.mod(ezca[self.prefix[3:]+'%s_REL_PHASE_%s'%(stage,DoF)],-360)))                    
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
                        ax.append(fig.add_subplot(3,6,ii+1))
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
                    ax.append(fig.add_subplot(3,6,ii+1))
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
            ezca['VIS-%s_FREE_MODE_LIST_NO%d_PRE_FREQ'%(OPTIC,self.modeindex)] = ezca['VIS-%s_FREE_MODE_LIST_NO%d_FREQ'%(OPTIC,self.modeindex)]
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

def make_strresult(data, DoFList):
    strresult = '('
    for DoF in DoFList:
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
        for DoF2 in DoFList:
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
        
        # disable DC path
        if self.mycounter == 0:
            for DoF in ['PIT','YAW']:
                OLDC = ezca.get_LIGOFilter('MOD-%s_OLDC_MN_%s'%(OPTIC,DoF))
                OLDC.turn_off('INPUT')

            for DoF in ['LEN','TRA','YAW']:
                IPDC = ezca.get_LIGOFilter('MOD-%s_IPDC_%s'%(OPTIC,DoF))
                IPDC.turn_off('INPUT')
                TRAMP = IPDC.OUTPUT.get()/30
                IPDC.ramp_gain(0,TRAMP,False)
                if self.timer['my_waiting']:
                    self.timer['my_waiting'] = TRAMP
            self.mycounter += 1

        elif self.mycounter == 1:
            # clear history
            for DoF in ['LEN','TRA','YAW']:
                IPDC = ezca.get_LIGOFilter('MOD-%s_IPDC_%s'%(OPTIC,DoF))
                IPDC.RSET.put(2)
                IPDC.ramp_gain(1,0,False)

            self.timer['my_waiting'] = self.settletime['IP']
            self.mycounter += 1

        elif self.mycounter == 2:
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
         ('EXCITE_RESONANCE','RECORD_MEASUREMENT'),
         ('RECORD_MEASUREMENT','EXCITE_RESONANCE'),
         ('STANDBY','SENSOR_DIAGONALIZATION'),
         ('SENSOR_DIAGONALIZATION','ACT_DIAG_TOWER'),
         ('ACT_DIAG_TOWER','ACT_DIAG_PAY'),
         ('ACT_DIAG_PAY','SENSOR_CALIBRATION'),
         ('SENSOR_CALIBRATION','STANDBY')
]
