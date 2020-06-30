###########
# Misalign
###########
MISALIGN_OFFSET = 250
MISALIGN_TRAMP = 30
MISALIGN_CHAN = 'VIS-ETMX_BF_PAYOL_OFS_Y'

###########
# Threshold
###########
THRED_DISTANCE_SET2CURRENT = 300 # If the setpoint and current angle is far from each other by this threshold, guardian will not engage DC loop.

###########
# Offload gain
###########
offload_gain = {
    'PIT':-0.01,
    'YAW':-0.1,
    'MNOL':-1,
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


#K1:VIS-ETMX_MN_PSDAMP
MN_LOCALDAMP = {
    'ramptime':3,
    'integrator':False,
    'init_FM':{'LEN':['FM1','FM4','FM5','FM8','FM9'],
               'TRANS':['FM1','FM5','FM6','FM7','FM8'],},
    'bst_FM':{'LEN':[['FM2','FM3']],'TRANS':[],'YAW':[]},
}

#K1:VIS-ETMX_MN_MNOLDAMP
MN_MNOLDAMP = {
    'ramptime':2,
    'integrator':False,
    'init_FM':{'PIT':[],'YAW':['FM1','FM2','FM6','FM8']},
    'bst_FM':{'PIT':[],'YAW':['FM4']},
    'DC_FM':{'PIT':[],'YAW':[['FM1'],['FM9']]}
}

#K1:VIS-ETMX_MN_TMOLDAMP
MN_OLDAMP = {
    'ramptime':2,
    'integrator':False,
    'init_FM':{#'LEN':['FM1','FM2','FM3','FM9'],
               'PIT':['FM1','FM2'],
               'YAW':['FM1','FM2','FM3','FM5']},
    'bst_FM':{'LEN':[],'PIT':[],'YAW':[]},
    'DC_FM':{'LEN':[],'PIT':[['FM9'],['FM1'],['FM2']],'YAW':[['FM9'],['FM1']]}
}

#K1:VIS-ETMX_IM_TMOLDAMP
IM_OLDAMP = {
    'ramptime':3,
    'integrator':False,
    'init_FM':{'PIT':['FM1','FM2','FM3','FM4','FM9'],'YAW':[]},
    'bst_FM':{'PIT':[],'YAW':[]},
    'DC_FM':{'PIT':[['FM1'],['FM8']]}
}

#K1:VIS-ETMX_TM_DAMP
TM_OLDAMP = {
    'ramptime':2,
    'integrator':False,
    'init_FM':{
        #'LEN':['FM1','FM2','FM8'],
        #'PIT':['FM1','FM2','FM9']
    },
    'bst_FM':{'LEN':[],'PIT':[]},
    'DC_FM':{'LEN':[],'PIT':[]},
}

OLSERVO = {
    'ramptime':0,
    'integrator':False,
    'init_FM':{'LEN':[],'PIT':[],'YAW':[]},
    'bst_FM':{'LEN':[],'PIT':[[],[]],'YAW':[]},
    'DC_FM':{}
    }

from TYPEA import *
from GRD_VIS import ENGAGE_TM_OLDAMP, ENGAGE_IM_OLDAMP, ENGAGE_MN_OLDAMP, ENGAGE_MN_MNOLDAMP, DISABLE_TM_OLDAMP, DISABLE_IM_OLDAMP, DISABLE_MN_OLDAMP, DISABLE_MN_MNOLDAMP, ENGAGE_MN_LOCALDAMP, DISABLE_MN_LOCALDAMP, PAY_LOCALDAMPED, edges, ALIGNED, TRANSIT_TO_OBS, OBSERVATION, BACK_TO_ALIGNED, MISALIGNING, MISALIGNED, REALIGNING, ENGAGE_BPCOMB, DISABLE_BPCOMB, ENGAGE_OLSERVO, OLDAMPED, ENGAGE_MN_MNOLDC, DISABLE_MN_MNOLDC, DISABLE_IM_OLDC, DISABLE_MN_OLDC, ENGAGE_IM_OLDC, ENGAGE_MN_OLDC, TRANSIT_TO_LOCKACQ, LOCK_ACQUISITION, BACK_TO_LOCKACQ, REMOVE_ISCSIG

#from GRD_VIS import ENGAGE_TM_OLDAMP, ENGAGE_IM_OLDAMP, ENGAGE_MN_OLDAMP, ENGAGE_MN_MNOLDAMP, DISABLE_TM_OLDAMP, DISABLE_IM_OLDAMP, DISABLE_MN_OLDAMP, DISABLE_MN_MNOLDAMP, ENGAGE_MN_LOCALDAMP, DISABLE_MN_LOCALDAMP, PAY_LOCALDAMPED,edges, ALIGNED, TRANSIT_TO_OBS, OBSERVATION, BACK_TO_ALIGNED, MISALIGNING, MISALIGNED, REALIGNING, ENGAGE_BPCOMB, DISABLE_BPCOMB, CHECK_TM_ANGLE, ENGAGE_OLSERVO, DISABLE_OLSERVO
