###########
# Misalign
###########
MISALIGN_OFFSET = -7500
MISALIGN_TRAMP = 10
MISALIGN_CHAN = 'VIS-PRM_IM_TEST_Y'

###########
# Threshold
###########
THRED_DISTANCE_SET2CURRENT = 300 # If the setpoint and current angle is far from each other by this threshold, guardian will not engage DC loop.

###########
# Offload gain
###########
offload_gain = {
    'PIT':-1,
    'YAW':-1,
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
    FM list which engaged before the filter will be engaged. keys need to be a DoF which the filter has, e.g. 'PIT','YAW','LEN' for K1:VIS-BS_TM_DAMP, 'SF','BF' for K1:VIS-PR3_$(DOF)_DAMP_GAS. Each key value needs to be a list of FM to be engaged, e.g. ['FM1','FM2'].
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

# K1:VIS-PR3_$(DOF)_DAMP_GAS
GAS_LOCALDAMP = {
    'ramptime':1,
    'integrator':True,
    'init_FM':{
        'SF':['FM1','FM2','FM8','FM9'],
        'BF':['FM1','FM8','FM9'],
        },
    'bst_FM':{
        'SF':[['FM1',],],
        'BF':[['FM1',],]
        }
    }

# K1:VIS-PR3_BF_DAMP
BF_LOCALDAMP = {
    'ramptime':3,
    'integrator':False,
    'init_FM':{
        'LEN':['FM1','FM2','FM4','FM6'],
        'TRANS':['FM1','FM2','FM4','FM7'],
        'VERT':['FM1','FM2','FM4','FM7'],
        'ROLL':['FM1','FM2','FM4','FM7'],
        'PIT':['FM1','FM2','FM4','FM7'],
        'YAW':['FM1','FM2','FM4','FM7'],
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

# K1:VIS-PR3_IM_DAMP
IM_LOCALDAMP = {
    'ramptime':3,
    'integrator':False,
    'init_FM':{
        'LEN':['FM1','FM2','FM3','FM9'],
        'TRANS':['FM1','FM2','FM3','FM9'],
        #'VERT':['FM2','FM5','FM6'],
        'ROLL':['FM1','FM2','FM3','FM4','FM9'],
        'PIT':['FM2','FM3','FM4','FM5','FM6','FM9'],
        'YAW':['FM1','FM2','FM3','FM4','FM9'],
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

#K1:VIS-PR3_TM_DAMP
TM_OLDAMP = {
    'gain':1,
    'ramptime':1,
    'integrator':False,
    'init_FM':{'LEN':['FM1','FM2','FM9'],'PIT':[],'YAW':[]},
    'bst_FM':{'LEN':[],'PIT':[],'YAW':[]},
    'DC_FM':{'LEN':[],'PIT':[],'YAW':[]},
}


#K1:VIS-PR3_IM_OLDAMP
IM_OLDAMP = {
    'gain':1,
    'ramptime':0,
    'integrator':False,
    'init_FM':{'LEN':['FM1','FM2'],'PIT':['FM1','FM2','FM3'],'YAW':['FM1','FM2','FM3']},
    'bst_FM':{'LEN':[],'PIT':[],'YAW':[]},
    'DC_FM':{'LEN':[],'PIT':[['FM1',],['FM10']],'YAW':[['FM1'],['FM10']]},
}

#K1:VIS-PR3_TM_OPLEV_SERVO
OLSERVO = {
    'gain':1,
    'ramptime':3,
    'integrator':False,
    'init_FM':{'LEN':[],'PIT':['FM1','FM2','FM4','FM7','FM9'],'YAW':['FM1','FM2','FM7']},
    'bst_FM':{'LEN':[],'PIT':[],'YAW':[]},
    'DC_FM':{'LEN':[],'PIT':[['FM1'],['FM3','FM8',]],'YAW':[['FM1'],['FM8']]},
}


from TypeBp import INIT, SAFE, TRIPPED, nominal
from GRD_VIS import ENGAGE_GAS_LOCALDAMP, ENGAGE_BF_LOCALDAMP, TWR_DAMPED, DISABLE_BF_LOCALDAMP, DISABLE_GAS_LOCALDAMP, ENGAGE_IM_LOCALDAMP, PAY_LOCALDAMPED,  ENGAGE_TM_OLDAMP, ENGAGE_IM_OLDAMP, ENGAGE_OLSERVO, ALIGNED, DISABLE_OLSERVO, DISABLE_IM_OLDAMP, DISABLE_TM_OLDAMP, PAY_LOCALDAMPED, TRANSIT_TO_OBS, OBSERVATION, BACK_TO_ALIGNED, TWR_IDLE, DISABLE_IM_LOCALDAMP, edges, MISALIGNING, MISALIGNED, REALIGNING, check_WD, check_TWWD, OLDAMPED, ENGAGE_IM_OLDC, DISABLE_IM_OLDC, ENGAGE_OLSERVO_DC, DISABLE_OLSERVO_DC, TRANSIT_TO_LOCKACQ, LOCK_ACQUISITION, BACK_TO_LOCKACQ
