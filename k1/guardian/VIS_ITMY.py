from TYPEA import *




###########
# Misalign
###########
MISALIGN_OFFSET = 300
MISALIGN_TRAMP = 30
MISALIGN_CHAN = 'VIS-ITMY_BF_PAYOL_OFS_Y'

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


#K1:VIS-ITMY_MN_PSDAMP
MN_LOCALDAMP = {
    'ramptime':0.5,
    'integrator':False,
    'init_FM':{'LEN':['FM1','FM2','FM8','FM9'],
               'TRANS':['FM1','FM7'],
               'ROLL':['FM1','FM2','FM10'],
              #'PIT':['FM1','FM2','FM4'],
              #'YAW':['FM1','FM2','FM3','FM4']
           },
    'bst_FM':{'LEN':[],'ROLL':[],'TRANS':[],'PIT':[],'YAW':[]},
}

#K1:VIS-ITMY_MN_MNOLDAMP
MN_MNOLDAMP = {
    'ramptime':2,
    'integrator':False,
    'init_FM':{'PIT':[],'YAW':['FM1','FM2','FM5','FM7','FM8']},
    'bst_FM':{'PIT':[],'YAW':[]},
    'DC_FM':{'PIT':[],'YAW':[['FM1',],['FM9','FM6']]}
}

#K1:VIS-ITMY_MN_TMOLDAMP
MN_OLDAMP = {
    'ramptime':2,
    'integrator':False,
    'init_FM':{'LEN':['FM1','FM2','FM3','FM9'],
               'PIT':['FM1','FM2','FM3'],
               'YAW':['FM1','FM2','FM3','FM5']},
    'bst_FM':{'LEN':[],'PIT':[],'YAW':[]},
    'DC_FM':{'LEN':[],'PIT':[['FM9',],['FM1',]],'YAW':[['FM9',],['FM1',]]}
}

#K1:VIS-ITMY_IM_TMOLDAMP
IM_OLDAMP = {
    'ramptime':2,
    'integrator':False,
    'init_FM':{'PIT':['FM1','FM2','FM3','FM4','FM9'],'YAW':[]},
    'bst_FM':{'PIT':[],'YAW':[]},
    'DC_FM':{'PIT':[['FM1',],['FM8',],['FM6']]}
}

TM_OLDAMP = {
    'ramptime':2,
    'integrator':False,
    'init_FM':{},
    'bst_FM':{},
    'DC_FM':{},
}

OLSERVO = {
    'ramptime':0,
    'integrator':False,
    'init_FM':{'LEN':[],'PIT':[],'YAW':[]},
    'bst_FM':{'LEN':[],'PIT':[[],[]],'YAW':[]},
    'DC_FM':{}
    }

MN_COIL_BALANCE = {
    'coils':['V3','H2','H3'],
    'freq':{'V3':5,'H2':5,'H3':6},
    'oscAMP':{'V3':3000,'H2':3000,'H3':3000},
    'sweeprange':[0.9,1.1],
    'Npoints':10,
    'duration':10,
    'SettleDuration':5,
    'oscTRAMP':10
}

IM_COIL_BALANCE = {
    'coils':['V3','H2','H3'],
    'freq':{'V3':5,'H2':5,'H3':6},
    'oscAMP':{'V3':3000,'H2':500,'H3':500},
    'sweeprange':[0.9,1.1],
    'Npoints':10,
    'duration':10,
    'SettleDuration':5,
    'oscTRAMP':10
}

TM_COIL_BALANCE = {
    'coils':['H2','H4'],
    'freq':{'H2':5.0,'H4':5.0},
    'oscAMP':{'H2':5000.0,'H4':5000.0},
    'sweeprange':[0.1,1.0],
    'Npoints':10,
    'duration':10,
    'SettleDuration':5,
    'oscTRAMP':10
}



from TYPEA import *
from GRD_VIS import ENGAGE_TM_OLDAMP, ENGAGE_IM_OLDAMP, ENGAGE_MN_OLDAMP, ENGAGE_MN_MNOLDAMP, DISABLE_TM_OLDAMP, DISABLE_IM_OLDAMP, DISABLE_MN_OLDAMP, DISABLE_MN_MNOLDAMP, ENGAGE_MN_LOCALDAMP, DISABLE_MN_LOCALDAMP, PAY_LOCALDAMPED, edges, ALIGNED, TRANSIT_TO_OBS, OBSERVATION, BACK_TO_ALIGNED, MISALIGNING, MISALIGNED, REALIGNING, ENGAGE_BPCOMB, DISABLE_BPCOMB, ENGAGE_OLSERVO, OLDAMPED, ENGAGE_MN_MNOLDC, DISABLE_MN_MNOLDC, DISABLE_IM_OLDC, DISABLE_MN_OLDC, ENGAGE_IM_OLDC, ENGAGE_MN_OLDC, TRANSIT_TO_LOCKACQ, LOCK_ACQUISITION, BACK_TO_LOCKACQ, REMOVE_ISCSIG,INIT_MON,COIL_BALANCED,MN_COIL_BALANCING,IM_COIL_BALANCING,TM_COIL_BALANCING



#from GRD_VIS import ENGAGE_TM_OLDAMP, ENGAGE_IM_OLDAMP, ENGAGE_MN_OLDAMP, ENGAGE_MN_MNOLDAMP, DISABLE_TM_OLDAMP, DISABLE_IM_OLDAMP, DISABLE_MN_OLDAMP, DISABLE_MN_MNOLDAMP, ENGAGE_MN_LOCALDAMP, DISABLE_MN_LOCALDAMP, PAY_LOCALDAMPED, edges, ALIGNED, TRANSIT_TO_OBS, OBSERVATION, BACK_TO_ALIGNED, MISALIGNING, MISALIGNED, REALIGNING, ENGAGE_BPCOMB, DISABLE_BPCOMB, CHECK_TM_ANGLE, ENGAGE_OLSERVO, DISABLE_OLSERVO

edges.extend([('TWR_DAMPED','INIT_MON'),
              ('TWR_DAMPED','MN_COIL_BALANCING'),
              ('MN_COIL_BALANCING','IM_COIL_BALANCING'),
              ('IM_COIL_BALANCING','TM_COIL_BALANCING'),
              ('TM_COIL_BALANCING','COIL_BALANCED')
          ])
