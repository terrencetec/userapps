###########
# Misalign
###########
MISALIGN_OFFSET = -1300
MISALIGN_TRAMP = 10
MISALIGN_CHAN = 'VIS-SRM_IM_TEST_Y'
'''
[TODO]
Remove after complete GRD_VIS,
'''
from TYPEB import INIT, SAFE, TRIPPED, MASTERSWITCH_OFF, NEUTRAL, DISENGAGING_IP_CONTROL, MASTERSWITCH_ON, ENGAGING_IP_CONTROL, IP_CONTROL_ENGAGED, DISENGAGING_IP_CONTROL, DISENGAGING_GAS_CONTROL, ENGAGING_GAS_CONTROL, PAY_TRIPPED, nominal



###########
# Threshold
###########
THRED_DISTANCE_SET2CURRENT = 500 # If the setpoint and current angle is far from each other by this threshold, guardian will not engage DC loop.


###########
# FB Config.
###########
'''
The following dicts describe the filter configuration. Each dict needs to have the following keys:

keys
----
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
        3. Engage first component of bst_FM. Wait for ramping
            4. Engage second component of bst_FM
                ...

    If integrator is False:
        1. Turn input, output, and init FM on. Clear history.
        2. Change gain to 1. Wait for ramping
        3. Engage first component of bst_FM. Wait for ramping
            4. Engage second component of bst_FM
                ...
'''


# K1:VIS-$(OPTIC)_IM_DAMP_$(DOF)
IM_LOCALDAMP = {
    'ramptime':3,
    'integrator':False,
    'init_FM':{
        'LEN':['FM6','FM7'],
        'TRANS':['FM6','FM7'],
        'VERT':['FM6','FM7','FM8'],
        'ROLL':['FM6','FM7'],
        'PIT':['FM6','FM7','FM9'],
        'YAW':['FM6','FM7'],
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
    
# K1:VIS-$(OPTIC)_TM_DAMP_$(DOF)
TM_OLDAMP = {
    'ramptime':0,
    'integrator':False,
    'init_FM':{'LEN':['FM1','FM2','FM9'],'PIT':['FM1'],'YAW':['FM1']},
    'bst_FM':{'LEN':[],'PIT':[],'YAW':[]},
}

# K1:VIS-$(OPTIC)_IM_OLDAMP_$(DOF)
IM_OLDAMP = {
    'ramptime':0,
    'integrator':True,
    'init_FM':{'PIT':['FM10'],'YAW':['FM1','FM2','FM10']},
    'bst_FM':{'PIT':[],'YAW':[]}
}

# K1:VIS-$(OPTIC)_TM_OPLEV_SERVO_$(DOF)
OLSERVO = {
    'ramptime':3,
    'integrator':False,
    'init_FM':{'LEN':[],'PIT':['FM1','FM2','FM3','FM9'],'YAW':['FM1','FM2','FM9']},
    'bst_FM':{'LEN':[],'PIT':[['FM1',],['FM8',]],'YAW':[['FM2',],['FM8',],['FM3','FM4']]},
}


'''
[TODO]
After complete the new guardian code, import everyghing from GRD_VIS
'''
from GRD_VIS import ENGAGE_TM_OLDAMP, ENGAGE_IM_OLDAMP, ENGAGE_OLSERVO, DISABLE_TM_OLDAMP, DISABLE_IM_OLDAMP, DISABLE_OLSERVO, ENGAGE_IM_LOCALDAMP, PAY_LOCALDAMPED, TWR_DAMPED, ALIGNED, DISABLE_IM_LOCALDAMP, edges, TRANSIT_TO_OBS, OBSERVATION, BACK_TO_ALIGNED, MISALIGNING, MISALIGNED, REALIGNING
