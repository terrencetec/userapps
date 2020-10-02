from guardian import GuardState
import kagralib
import vislib

###########
# Misalign
###########
#MISALIGN_OFFSET = -7500
#MISALIGN_OFFSET = 14000
NOMINAL_BF_OFS = 0
TRAMP_BF_OFS = 10

MISALIGN_OFFSET = -2000
MISALIGN_OFFSET_FOR_PRFPMI = -2000
MISALIGN_TRAMP = 10
MISALIGN_TRAMP_FOR_PRFPMI = 1
MISALIGN_CHAN = 'VIS-PRM_BF_TEST_Y'

###########
# Threshold
###########
THRED_DISTANCE_SET2CURRENT = 300 # If the setpoint and current angle is far from each other by this threshold, guardian will not engage DC loop.

###########
# Offload gain
###########
offload_gain = {
    'PIT':-0.1,
    'YAW':-0.1,
    }

###########
# FB Config.
###########
'''
The following dicts describe the filter configuration. Each dict needs to have the following keys:

keys
----
'chan
'ramptime': float
    ramptime to be set into each filter

'integraotr': bool
    If the filter has integrator, put True.

'init_FM': dict
    FM list which engaged before the filter will be engaged. keys need to be a DoF which the filter has, e.g. 'PIT','YAW','LEN' for K1:VIS-BS_TM_DAMP, 'SF','BF' for K1:VIS-PRM_$(DOF)_DAMP_GAS. Each key value needs to be a list of FM to be engaged, e.g. ['FM1','FM2'].
    The detail of procedure to engage FB is written later.

'bst_FM': dict
    This keyvalue describe the procedure how to engage the FMs after FB is engaged.
    e.g.: [['FM1','FM2'],['FM3']] -> press FM1, FM2 first and then engage FM3 after FM1 and FM2 is engaged.

note
----
- How FMs are engaged
    If integrator is True:
        (0. If gain is 0, change gain to 1 with input off. Wait for ramping)
        1. Turn init_FM on
        2. Engage input. 
        3. Toggle first component of bst_FM. Wait for ramping
            4. Toggle second component of bst_FM
                ...

    If integrator is False:
        1. Turn input, output, and init FM on. Clear history.
        2. Change gain to 1. Wait for ramping
        3. Toggle first component of bst_FM. Wait for ramping
            4. Toggle second component of bst_FM
                ...
'''

# K1:VIS-PRM_$(DOF)_DAMP_GAS
GAS_LOCALDAMP = {
    'ramptime':1,
    'integrator':True,
    'init_FM':{
        'SF':['FM2','FM4','FM5','FM6'],
        'BF':['FM2','FM9'],
        },
    'bst_FM':{
        'SF':[[],],
        'BF':[[],]
        }
    }

# K1:VIS-PRM_BF_DAMP
BF_LOCALDAMP = {
    'ramptime':3,
    'integrator':False,
    'init_FM':{
        'LEN':['FM1','FM2','FM4'],
        'TRANS':['FM1','FM2','FM4'],
        'VERT':['FM1','FM2','FM4'],
        'ROLL':['FM1','FM2','FM4','FM5'],
        'PIT':['FM1','FM2','FM4','FM5'],
        'YAW':['FM1','FM2','FM4','FM5'],
    },
    'bst_FM':{
        'LEN':[],
        'TRANS':[],
        'VERT':[],
        'ROLL':[],
        'PIT':[],
        'YAW':[],
    },
    }

# K1:VIS-PRM_IM_DAMP
IM_LOCALDAMP = {
    'ramptime':3,
    'integrator':False,
    'init_FM':{
        'LEN':['FM1','FM2','FM3'],
        'TRANS':['FM1','FM2','FM3'],
        'VERT':['FM1','FM2','FM3','FM4','FM5','FM6'],
        'ROLL':['FM1','FM2','FM3','FM4'],
        'PIT':['FM1','FM2','FM3'],
        'YAW':['FM1','FM2','FM3','FM4'],
    },
    'bst_FM':{
        'LEN':[],
        'TRANS':[],
        'VERT':[],
        'ROLL':[],
        'PIT':[],
        'YAW':[],
    },
    }

#K1:VIS-PRM_TM_DAMP
TM_OLDAMP = {
    'gain':1,
    'ramptime':0,
    'integrator':False,
    'init_FM':{'LEN':[],'PIT':[],'YAW':[]},
    'bst_FM':{'LEN':[],'PIT':[],'YAW':[]},
    }

#K1:VIS-PRM_IM_OLDAMP
IM_OLDAMP = {
    'gain':1,
    'ramptime':1,
    'integrator':False,
    'init_FM':{'PIT':['FM1','FM2','FM3'],'YAW':['FM1','FM2','FM3','FM4','FM8']},
    'bst_FM':{'PIT':[],'YAW':[]},
    'DC_FM':{'LEN':[],'PIT':[['FM1',],['FM10',]],'YAW':[['FM1',],['FM9',]]},
}

#K1:VIS-PRM_TM_OPLEV_SERVO
OLSERVO = {
    'gain':1,
    'ramptime':3,
    'integrator':False,
    'init_FM':{'LEN':['FM1','FM2','FM9'],'PIT':['FM1','FM2','FM9'],'YAW':['FM1','FM2','FM9']},
    'bst_FM':{'LEN':[],'PIT':[],'YAW':[]},
    'DC_FM':{'LEN':[],'PIT':[['FM1',],['FM3','FM4','FM8']],'YAW':[['FM1',],['FM8',]]},
}


from TypeBp import INIT, SAFE, TRIPPED, nominal
from GRD_OLD import ENGAGE_GAS_LOCALDAMP, ENGAGE_BF_LOCALDAMP, TWR_DAMPED, DISABLE_BF_LOCALDAMP, DISABLE_GAS_LOCALDAMP, ENGAGE_IM_LOCALDAMP, PAY_LOCALDAMPED,  ENGAGE_TM_OLDAMP, ENGAGE_IM_OLDAMP, ENGAGE_OLSERVO, ALIGNED, DISABLE_OLSERVO, DISABLE_IM_OLDAMP, DISABLE_TM_OLDAMP, PAY_LOCALDAMPED, TRANSIT_TO_OBS, OBSERVATION, BACK_TO_ALIGNED, TWR_IDLE, DISABLE_IM_LOCALDAMP, edges, MISALIGNING, MISALIGNED, REALIGNING, check_WD, check_TWWD, OLDAMPED, ENGAGE_IM_OLDC, DISABLE_IM_OLDC, ENGAGE_OLSERVO_DC, DISABLE_OLSERVO_DC,TRANSIT_TO_LOCKACQ, LOCK_ACQUISITION, BACK_TO_LOCKACQ, ENGAGE_BF_OLDAMP, DISABLE_BF_OLDAMP



#########################
# class
#########################
class MISALIGNING_FOR_PRFPMI(GuardState):
    index = 99
    request = False

    @check_TWWD
    @check_WD
    def main(self):
        self.ofschan = ezca.get_LIGOFilter(MISALIGN_CHAN)
        self.ofschan.turn_on('OFFSET')
        init_ofs = self.ofschan.OFFSET.get()
        self.ofschan.ramp_offset(init_ofs + MISALIGN_OFFSET_FOR_PRFPMI, MISALIGN_TRAMP_FOR_PRFPMI, False)
        self.ofschan.ramp_gain(1, MISALIGN_TRAMP_FOR_PRFPMI, False)

    @check_TWWD
    @check_WD
    def run(self):
        return not self.ofschan.is_offset_ramping()
    

class MISALIGNED_FOR_PRFPMI(GuardState):
    index = 97
    request = True

    @check_TWWD
    @check_WD
    def run(self):
        return True

#Overwrite misalign state in VIS_GRD.py
class MISALIGNING(GuardState):
    index = 101
    request = False

    def is_PSD_centered(self):
        pit = ezca['VIS-PRM_TM_PSD_PIT_OUTPUT']
        yaw = ezca['VIS-PRM_TM_PSD_YAW_OUTPUT']
        if abs(pit)<0.1 and abs(yaw)<0.1:            
            return True
        else:
            return False
    
    @check_TWWD
    @check_WD
    def main(self):
        self.timer['waiting'] = 0
        self.timer['warning'] = 0
        self.counter = 0
        self.OPAL = {DoF:vislib.OpticAlign('PRM',DoF) for DoF in ['PIT','YAW']}
        self.IM_TEST = {DoF:ezca.get_LIGOFilter('VIS-PRM_IM_TEST_%s'%DoF[0]) for DoF in ['PIT','YAW']}
        self.BF_TEST = ezca.get_LIGOFilter('VIS-PRM_BF_TEST_Y')
        self.timer['checking'] = 0

    @check_TWWD
    @check_WD
    def run(self):
        if not self.timer['waiting']:
            return

        if bool(ezca['PSL-BEAM_SHUTTER_STATE']) and self.counter < 3:
            if self.timer['warning']:
                kagralib.speak_aloud('PSL shutter is open. Please close it to misalign PRM')
                notify('PSL shutter is open. Please close it to misalign PRM')
                self.timer['warning'] = 30
            return 

        if self.counter == 0:
            for key in self.OPAL:
                self.OPAL[key].turn_off('OFFSET')
                self.IM_TEST[key].TRAMP.put(3)
                self.IM_TEST[key].turn_on('OFFSET')
                self.IM_TEST[key].ramp_gain(1,0,False)
            self.counter += 1
            self.timer['waiting'] = 1

        elif self.counter == 1:
            self.BF_TEST.TRAMP.put(3)
            self.BF_TEST.turn_on('OFFSET')
            self.BF_TEST.ramp_gain(1,0,False)
            self.timer['warning'] = 120
            self.counter += 1
            
        elif self.counter == 2 and not self.BF_TEST.is_offset_ramping():
            # engage PSD loop in IM_PIT and BF_YAW
            filt = ezca.get_LIGOFilter('VIS-PRM_BF_PSD_Y')
            filt.switch('FM3','FM7','FM8','FM9','ON')
            filt.ramp_gain(1,ramp_time=5,wait=True)            
            filt = ezca.get_LIGOFilter('VIS-PRM_IM_PSD_P')
            filt.switch('FM3','FM7','FM8','FM9','ON')
            filt.ramp_gain(1,ramp_time=5,wait=True)
                            
            if self.is_PSD_centered() and self.timer['checking']:
                self.timer['checking'] = 10
                self.counter += 1
                
        elif self.counter==3:
            if self.timer['checking']:
                if self.is_PSD_centered():
                    return True
            if self.timer['warning']:
                kagralib.speak_aloud('PRM is not misaligned propery yet. Please check PRM status.')
                self.timer['warning'] = 120                
                    

#[FIXME]
'''
class ENGAGE_PSD_LOOP(engage_damping):
    index = 106
    request = False
    #[FIXME]
    pass
'''

class REALIGNING(GuardState):
    index = 103
    request = False

    def is_oplev_inrange(self):
        #[FIXME] check oplev position
        #inrange = all([ (abs(ezca[vislib.DiagChan('PRM',DoF)]) < 400) for DoF in ['PIT','YAW']])
        #oksum = ezca['VIS-PRM_TM_OPLEV_TILT_SUM_OUTPUT'] > 3000
        #return (inrange and oksum)
        return all([ (abs(ezca[vislib.DiagChan('PRM',DoF)]) < 400) for DoF in ['PIT','YAW']]) and ezca['VIS-PRM_TM_OPLEV_TILT_SUM_OUTPUT'] > 3000
    
    @check_TWWD
    @check_WD
    def main(self):
        self.timer['waiting'] = 0
        self.timer['warning'] = 0
        self.counter = 0
        self.OPAL = {DoF:vislib.OpticAlign('PRM',DoF) for DoF in ['PIT','YAW']}
        self.IM_TEST = {DoF:ezca.get_LIGOFilter('VIS-PRM_IM_TEST_%s'%DoF[0]) for DoF in ['PIT','YAW']}
        self.IM_OFFSET = {'PIT':-1500,'YAW':-3000}
        self.BF_TEST = ezca.get_LIGOFilter('VIS-PRM_BF_TEST_Y')
        self.BF_OFFSET = NOMINAL_BF_OFS

    @check_TWWD
    @check_WD
    def run(self):
        if not self.timer['waiting']:
            return

        if bool(ezca['PSL-BEAM_SHUTTER_STATE']):
            if self.timer['warning']:
                kagralib.speak_aloud('PSL shutter is open. Please close it to realign PRM')
                notify('PSL shutter is open. Please close it to realign PRM')

                self.timer['warning'] = 30
            return 

        if self.counter == 0:
            for key in self.OPAL:
                self.OPAL[key].turn_on('OFFSET')
                self.IM_TEST[key].turn_off('OFFSET')
            self.IM_TEST['PIT'].ramp_offset(self.IM_TEST['PIT'].OFFSET.get()+ezca['VIS-PRM_IM_PSD_P_OUTPUT'],1,False)
            self.counter += 1
            self.timer['waiting'] = 1

        elif self.counter == 1:
            self.BF_TEST.turn_off('OFFSET')
            self.BF_TEST.ramp_offset(self.BF_TEST.OFFSET.get() + ezca['VIS-PRM_BF_PSD_Y_OUTPUT'],1,False)
            self.timer['warning'] = 120
            self.counter += 1
            
        elif self.counter == 2 and not self.BF_TEST.is_offset_ramping():
            # diable PSD loop in IM_PIT and BF_YAW
            filt = ezca.get_LIGOFilter('VIS-PRM_BF_PSD_Y')
            filt.switch('FM3','FM4','FM7','FM8','FM9','OFF')
            filt.ramp_gain(0,ramp_time=5,wait=True)
            filt = ezca.get_LIGOFilter('VIS-PRM_IM_PSD_P')
            filt.switch('FM3','FM4','FM7','FM8','FM9','OFF')
            filt.ramp_gain(0,ramp_time=5,wait=True)
            
            if self.timer['warning']:
                kagralib.speak_aloud('PRM is not realigned propery yet. Please check PRM status.')
                self.timer['warning'] = 120
                
            return self.is_oplev_inrange()
#[FIXME]
'''
class DISABLE_PSD_LOOP(disable_damping):
    index = 107
    request = False

    pass
'''
        
    

class REALIGNING_FOR_PRFPMI(GuardState):
    index = 98
    request = False

    @check_TWWD
    @check_WD
    def main(self):
        self.ofschan = ezca.get_LIGOFilter(MISALIGN_CHAN)
        init_ofs = self.ofschan.OFFSET.get()
        log(init_ofs)
        self.ofschan.ramp_offset(init_ofs - MISALIGN_OFFSET_FOR_PRFPMI, MISALIGN_TRAMP_FOR_PRFPMI, False)

    @check_TWWD
    @check_WD
    def run(self):
        return not self.ofschan.is_offset_ramping()

edges += (
    ('PAY_LOCALDAMPED','MISALIGNING_FOR_PRFPMI'),
    ('MISALIGNING_FOR_PRFPMI','MISALIGNED_FOR_PRFPMI'),
    ('MISALIGNED_FOR_PRFPMI','REALIGNING_FOR_PRFPMI'),
    ('REALIGNING_FOR_PRFPMI','PAY_LOCALDAMPED'),
    )
