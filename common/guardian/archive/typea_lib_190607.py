from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import os, time, subprocess

##################################################
# initialization values

# initial REQUEST state
request = 'ALIGNED'

# NOMINAL state, which determines when node is OK
nominal = 'ALIGNED'

##################################################

##################################################
# Tool for taking safe snapshot
userapps = '/opt/rtcds/userapps/release/'
IFO = os.getenv('IFO')
ifo = IFO.lower()
SITE = os.getenv('SITE')
site = SITE.lower()
dorw = 2
verbose=False

def modelName(optic):
    return ifo+'vis'+optic

def req_file_path(optic):
    return os.path.join('/opt/rtcds',site,ifo,'target',modelName(optic),modelName(optic)+'epics')

def snap_file_path(optic):
#    return os.path.join(userapps, 'vis', ifo, 'burtfiles') 
    return os.path.join(userapps, 'vis', ifo, 'guardian') # FIXME temporary only

###################################################
# utility functions

def is_tripped(optic):
    if (ezca['VIS-'+optic+'_TM_WDMON_STATE'] != 1) or \
	(ezca['VIS-'+optic+'_IM_WDMON_STATE'] != 1) or \
	(ezca['VIS-'+optic+'_MN_WDMON_STATE'] != 1) or \
	(ezca['VIS-'+optic+'_IM_WDMON_STATE'] != 1) or \
	(ezca['VIS-'+optic+'_BF_WDMON_STATE'] != 1) or \
	(ezca['VIS-'+optic+'_F3_WDMON_STATE'] != 1) or \
	(ezca['VIS-'+optic+'_F2_WDMON_STATE'] != 1) or \
	(ezca['VIS-'+optic+'_F1_WDMON_STATE'] != 1) or \
	(ezca['VIS-'+optic+'_F0_WDMON_STATE'] != 1) or \
	(ezca['VIS-'+optic+'_IP_WDMON_STATE'] != 1): # if WatchDog is triped
        return True
    else:
        return False

def is_oplev_inrange(optic):
    if (abs(ezca['K1:VIS-'+optic+'_TM_OPLEV_TILT_YAW_OUTPUT'])-abs(ezca['K1:VIS-'+optic+'_TM_OPLEV_TILT_YAW_GAIN'])*0.9 < 0) or \
       (abs(ezca['K1:VIS-'+optic+'_TM_OPLEV_TILT_PIT_OUTPUT'])-abs(ezca['K1:VIS-'+optic+'_TM_OPLEV_TILT_PIT_GAIN'])*0.9 < 0):
        return True
    else:
        return False


def tm_damp_off(GuardState,optic):
    for DOF in ['L', 'P', 'Y']:
        ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = 0
            wait(GuardState,ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF])
        
    
def im_damp_off(GuardState,optic):
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_IM_DAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_IM_DAMP_%s_GAIN'%DOF] = 0
            wait(GuardState,ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF])

def im_oldamp_off(GuardState,optic):
    for DOF in ['L','P','Y']:
        ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = 0
            wait(GuardState,ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF])

def mn_damp_off(GuardState,optic):
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_MN_DAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_MN_DAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_MN_DAMP_%s_GAIN'%DOF] = 0
            wait(GuardState,ezca['VIS-'+optic+'_MN_DAMP_%s_TRAMP'%DOF])

def mn_oldamp_off(GuardState,optic):
    for DOF in ['P','Y']:
        ezca['VIS-'+optic+'_MN_OLDAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_MN_OLDAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_MN_OLDAMP_%s_GAIN'%DOF] = 0
            wait(GuardState,ezca['VIS-'+optic+'_MN_OLDAMP_%s_TRAMP'%DOF])

def mn_mnoldamp_off(GuardState,optic):
    for DOF in ['P','Y']:
        ezca['VIS-'+optic+'_MN_OLDAMP1_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_MN_OLDAMP1_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_GAIN'%DOF] = 0
            wait(GuardState,ezca['VIS-'+optic+'_MN_OLDAMP1_%s_TRAMP'%DOF])

def bf_oldamp_off(GuardState,optic):
    for DOF in ['L','P','Y']:
        ezca['VIS-'+optic+'_BF_OLDAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_BF_OLDAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_BF_OLDAMP_%s_GAIN'%DOF] = 0
            wait(GuardState,ezca['VIS-'+optic+'_BF_OLDAMP_%s_TRAMP'%DOF])

def bf_damp_off(GuardState,optic):
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_BF_DAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_BF_DAMP_%s_GAIN'%DOF] = 0
            wait(GuardState,ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF])

def gas_damp_off(GuardState,optic):
    for DOF in ['BF','F3','F2','F1','F0']:
        ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = 0
            wait(GuardState,ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF])

def ip_damp_off(GuardState,optic):
    for DOF in ['L','T','Y']:
        ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = 0
            wait(GuardState,ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF])

def oa_off(GuardState,optic):
    for DOF in ['P','Y']:
        ezca['VIS-'+optic+'_MN_OPTICALIGN_%s_TRAMP'%DOF] = 5.0
        ezca.switch('VIS-'+optic+'_MN_OPTICALIGN_%s'%DOF,'OFFSET','OFF')
    wait(GuardState,ezca['VIS-'+optic+'_MN_OPTICALIGN_Y_TRAMP'])

def test_off(GuardState,optic):
    for DOF in ['L', 'P', 'Y']:
        ezca['VIS-'+optic+'_TM_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_TM_TEST_%s_GAIN'%DOF] = 0
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_IM_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_IM_TEST_%s_GAIN'%DOF] = 0
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_MN_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_MN_TEST_%s_GAIN'%DOF] = 0
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_BF_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_BF_TEST_%s_GAIN'%DOF] = 0
    for DOF in ['BF','F3','F2','F1','F0']:
        ezca['VIS-'+optic+'_%s_TEST_GAS_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_%s_TEST_GAS_GAIN'%DOF] = 0
    for DOF in ['L','T','Y']:
        ezca['VIS-'+optic+'_IP_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_IP_TEST_%s_GAIN'%DOF] = 0
    wait(GuardState,ezca['VIS-'+optic+'_IP_TEST_L_TRAMP'])

def wait(GuardState,t):
    GuardState.timer['waiting'] = t
    while not (GuardState.timer['waiting']):
        log('waiting')
    return True

def all_off(GuardState,optic):
    log('Turning TM oplev damping off')
    tm_damp_off(GuardState,optic)
    im_oldamp_off(GuardState,optic)
    mn_oldamp_off(GuardState,optic)
    bf_oldamp_off(GuardState,optic)
    log('Turning MN oplev damping off')
    mn_mnoldamp_off(GuardState,optic)
    log('Turning all test filter off')
    test_off(GuardState,optic)
    log('Turning Optic Align offset off')
    oa_off(GuardState,optic)
    log('Turning other damping off')
    im_damp_off(GuardState,optic)
    mn_damp_off(GuardState,optic)
    bf_damp_off(GuardState,optic)
    gas_damp_off(GuardState,optic)
    ip_damp_off(GuardState,optic)
    

            
