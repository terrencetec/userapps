###########
# Ramp time
###########
RampTimeISCINF = 0
RampTimeDither = 0
RampTimeLock = 1
RampTimeOpticAlign = 1

##########
# Guardian
##########
FreezeState = {
    'TypeBp':'DISABLE_OLDCCTRL',
    'TypeB':'OL_DCCTRL_FLOAT',
    'TypeA':'FREEZE'
    }
OLCTRLFreeze = {
    'TypeBp':'IM',
    'TypeB':'IM',
    'TypeA':'MN'
    }
OLRMSThreshold = {
    'PR2': {'L': 1000, 'P': 1000, 'Y': 1000},
    'PR3': {'L': 1000, 'P': 1000, 'Y': 1000},
    'PRM': {'L': 1000, 'P': 1000, 'Y': 1000},
    'BS':  {'L': 1000, 'P': 1000, 'Y': 1000},
    'SR2': {'L': 1000, 'P': 1000, 'Y': 1000},
    'SR3': {'L': 1000, 'P': 1000, 'Y': 1000},
    'SRM': {'L': 1000, 'P': 1000, 'Y': 1000},
    'ITMX':{'L': 1000, 'P': 1000, 'Y': 1000},
    'ITMY':{'L': 1000, 'P': 1000, 'Y': 1000},
    'ETMX':{'L': 1000, 'P': 1000, 'Y': 1000},
    'ETMY':{'L': 1000, 'P': 1000, 'Y': 1000}
    }
OLGoodRange = {
    'PIT': 10000,
    'YAW': 10000
    }
