from guardian import GuardState
import vislib
import kagralib
###########
# Misalign
###########
#MISALIGN_OFFSET = -7500
#MISALIGN_OFFSET = 14000
NOMINAL_BF_OFS = -30000
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
        'VERT':['FM1','FM2','FM3'],
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
    'init_FM':{'LEN':['FM1','FM2','FM9'],'PIT':[],'YAW':[]},
    'bst_FM':{'LEN':[],'PIT':[],'YAW':[]},
    }

#K1:VIS-PRM_IM_OLDAMP
IM_OLDAMP = {
    'gain':1,
    'ramptime':1,
    'integrator':False,
    'init_FM':{'LEN':['FM1','FM2'],'PIT':['FM1','FM2','FM3'],'YAW':['FM1','FM2','FM3','FM9']},
    'bst_FM':{'LEN':['FM3'],'PIT':[],'YAW':[]},
    'DC_FM':{'LEN':[],'PIT':[['FM1',],['FM10',]],'YAW':[['FM1',],['FM10',]]},
}

#K1:VIS-PRM_TM_OPLEV_SERVO
OLSERVO = {
    'gain':1,
    'ramptime':3,
    'integrator':False,
    'init_FM':{'LEN':[],'PIT':['FM1','FM2','FM9'],'YAW':['FM1','FM2','FM9']},
    'bst_FM':{'LEN':[],'PIT':[],'YAW':[]},
    'DC_FM':{'LEN':[],'PIT':[['FM1',],['FM3','FM4','FM8']],'YAW':[['FM1',],['FM8',]]},
}


from TypeBp import INIT, SAFE, TRIPPED, nominal
from GRD_VIS import ENGAGE_GAS_LOCALDAMP, ENGAGE_BF_LOCALDAMP, TWR_DAMPED, DISABLE_BF_LOCALDAMP, DISABLE_GAS_LOCALDAMP, ENGAGE_IM_LOCALDAMP, PAY_LOCALDAMPED,  ENGAGE_TM_OLDAMP, ENGAGE_IM_OLDAMP, ENGAGE_OLSERVO, ALIGNED, DISABLE_OLSERVO, DISABLE_IM_OLDAMP, DISABLE_TM_OLDAMP, PAY_LOCALDAMPED, TRANSIT_TO_OBS, OBSERVATION, BACK_TO_ALIGNED, TWR_IDLE, DISABLE_IM_LOCALDAMP, edges, MISALIGNING, MISALIGNED, REALIGNING, check_WD, check_TWWD, OLDAMPED, ENGAGE_IM_OLDC, DISABLE_IM_OLDC, ENGAGE_OLSERVO_DC, DISABLE_OLSERVO_DC,TRANSIT_TO_LOCKACQ, LOCK_ACQUISITION, BACK_TO_LOCKACQ


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
        #[FIXME] check PSD position
        return True
    
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
        self.BF_OFFSET = 70000

    @check_TWWD
    @check_WD
    def run(self):
        if not self.timer['waiting']:
            return

        if bool(ezca['PSL-BEAM_SHUTTER_STATE']):
            if self.timer['warning']:
                kagralib.speak_aloud('PSL shutter is open. Please close it to misalign PRM')
                notify('PSL shutter is open. Please close it to misalign PRM')
                self.timer['warning'] = 30
            return 

        if self.counter == 0:
            for key in self.OPAL:
                self.OPAL[key].turn_off('OFFSET')
                self.IM_TEST[key].turn_on('OFFSET')
                self.IM_TEST[key].ramp_gain(1,0,False)
                self.IM_TEST[key].ramp_offset(self.IM_OFFSET[key],3,False)
            self.counter += 1
            self.timer['waiting'] = 1

        elif self.counter == 1:
            self.BF_TEST.turn_on('OFFSET')
            self.BF_TEST.ramp_gain(1,0,False)
            self.BF_TEST.ramp_offset(self.BF_OFFSET,10,False)
            self.timer['warning'] = 120
            self.counter += 1

            
        elif self.counter == 2 and not self.BF_TEST.is_offset_ramping():
            #[FIXME] engage PSD loop or add state ENGAGE_PSD_LOOP state
            if self.timer['warning']:
                kagralib.speak_aloud('PRM is not misaligned propery yet. Please check PRM status.')
                self.timer['warning'] = 120
            return self.is_PSD_centered()

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
            self.counter += 1
            self.timer['waiting'] = 1

        elif self.counter == 1:
            self.BF_TEST.turn_on('OFFSET')
            self.BF_TEST.ramp_offset(self.BF_OFFSET,10,False)
            self.timer['warning'] = 120
            self.counter += 1

            
        elif self.counter == 2 and not self.BF_TEST.is_offset_ramping():
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
