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

# List for the BP comb
InSensList = ['MNP','MNY','TML','TMP','TMY']
#OutStageList = ['BFY','MNL','MNT','MNV','MNR','MNP','MNY','IML','IMT','IMV','IMR','IMP','IMY','TML','TMP','TMY']
OutStageList = ['BFL','BFT','BFY','MNL','MNT','MNV','MNR','MNP','MNY','IML','IMT','IMV','IMR','IMP','IMY','TML','TMP','TMY']

def modelName(optic):
    return ifo+'vis'+optic

def req_file_path(optic):
    return os.path.join('/opt/rtcds',site,ifo,'target',modelName(optic),modelName(optic)+'epics')

def snap_file_path(optic):
#    return os.path.join(userapps, 'vis', ifo, 'burtfiles') 
    return os.path.join(userapps, 'vis', ifo, 'guardian') # FIXME temporary only

###################################################
# utility functions

# ------- Made by T. Ushiba 2019/8/20 -------#
# when going out of CALM DOWN state
def is_oplev_noisy(optic):
    if (ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_Y_300M_1'] > 30 or ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_Y_1_3'] > 15 or ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_Y_3_10'] > 1.05 or ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_P_300M_1'] > 30 or ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_P_1_3'] > 7.5 or ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_P_3_10'] > 0.6):
        return True
    else:
        return False
#--------------------------------------------#
# when entering CALM DOWN state
def is_oplev_noisy2(optic):
    if (ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_Y_300M_1'] > 45 or ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_Y_1_3'] > 24 or ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_Y_3_10'] > 2.1 or ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_P_300M_1'] > 45 or ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_P_1_3'] > 12 or ezca['VIS-'+optic+'_TM_OPLEV_TILT_BLRMS_P_3_10'] > 0.9):
        return True
    else:
        return False



#-------Mod by A. Shoda-------#
def is_twr_tripped(optic,BIO):
    WD_state = False or (ezca['VIS-'+optic+'_TWR_SHUTDOWN_STATE'] != 0)
    
    AnalogWD_state = False
    for name in BIO:
        AnalogWD_state = AnalogWD_state or ( (int(ezca['VIS-'+optic+'_BIO_'+name+'_MON']) & 983040) != 0 ) # check if 

    DACKILL_state = (ezca['VIS-'+optic+'_TWR_DACKILL_STATE'] != 1)
    
    if WD_state or AnalogWD_state or DACKILL_state:
        return True
    
    else:
        return False

def is_pay_tripped(optic,BIO):
    # Works only the TWR is controlled state.
    GRDstate = ezca['GRD-VIS_'+optic+'_STATE_N']

    WD_state = False or (ezca['VIS-'+optic+'_SHUTDOWN_STATE'] != 0)
    
    AnalogWD_state = False
    for name in BIO:
        AnalogWD_state = AnalogWD_state or ( (int(ezca['VIS-'+optic+'_BIO_'+name+'_MON']) & 983040) != 0 ) # check if 

    DACKILL_state = (ezca['VIS-'+optic+'_PAY_DACKILL_STATE'] != 1)
    
    #if (WD_state or AnalogWD_state or DACKILL_state) and (GRDstate >= 55):
    if (WD_state or AnalogWD_state or DACKILL_state):
        return True
    
    else:
        return False

#-----------------------------#

def is_oplev_inrange(optic):
    if (abs(ezca['K1:VIS-'+optic+'_TM_OPLEV_TILT_YAW_OUTPUT'])-abs(ezca['K1:VIS-'+optic+'_TM_OPLEV_TILT_YAW_GAIN'])*0.9 < 0) or \
       (abs(ezca['K1:VIS-'+optic+'_TM_OPLEV_TILT_PIT_OUTPUT'])-abs(ezca['K1:VIS-'+optic+'_TM_OPLEV_TILT_PIT_GAIN'])*0.9 < 0):
        return True
    else:
        return False

def optic_misaligned(optic):
    return (abs(ezca['VIS-'+optic+'_BF_PAYOL_OFS_Y_OUTPUT'])>70)


def tm_lock_off(GuardState,optic):
    for DOF in ['L', 'P', 'Y']:
        ezca['VIS-'+optic+'_TM_LOCK_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_TM_LOCK_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_TM_LOCK_%s_GAIN'%DOF] = 0

def im_lock_off(GuardState,optic):
    for DOF in ['L', 'P', 'Y']:
        ezca['VIS-'+optic+'_IM_LOCK_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_IM_LOCK_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_IM_LOCK_%s_GAIN'%DOF] = 0

def mn_lock_off(GuardState,optic):
    for DOF in ['L', 'P', 'Y']:
        ezca['VIS-'+optic+'_MN_LOCK_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_MN_LOCK_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_MN_LOCK_%s_GAIN'%DOF] = 0

def tm_dither_off(GuardState,optic):
    for DOF in ['P', 'Y']:
        ezca['VIS-'+optic+'_TM_DITHER_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_TM_DITHER_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_TM_DITHER_%s_GAIN'%DOF] = 0

def im_dither_off(GuardState,optic):
    for DOF in ['P', 'Y']:
        ezca['VIS-'+optic+'_IM_DITHER_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_IM_DITHER_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_IM_DITHER_%s_GAIN'%DOF] = 0

def mn_dither_off(GuardState,optic):
    for DOF in ['P', 'Y']:
        ezca['VIS-'+optic+'_MN_DITHER_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_MN_DITHER_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_MN_DITHER_%s_GAIN'%DOF] = 0

def tm_damp_off(GuardState,optic):
    for DOF in ['L', 'P', 'Y']:
        ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = 0
    #wait(GuardState,5)
        
    
def im_damp_off(GuardState,optic):
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_IM_PSDAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_IM_PSDAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_IM_PSDAMP_%s_GAIN'%DOF] = 0
    #wait(GuardState,5)

def im_oldamp_off(GuardState,optic):
    for DOF in ['L','P','Y']:
        ezca['VIS-'+optic+'_IM_TMOLDAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_IM_TMOLDAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_IM_TMOLDAMP_%s_GAIN'%DOF] = 0
#    #wait(GuardState,5)

def mn_damp_off(GuardState,optic):
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_MN_PSDAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_MN_PSDAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_MN_PSDAMP_%s_GAIN'%DOF] = 0
    #wait(GuardState,5)

def mn_oldamp_off(GuardState,optic):
    if optic == 'ETMY':
        ezca.switch('VIS-'+optic+'_MN_MNOLDAMP_Y','FM9','OFF')
    for DOF in ['P','Y']:
        ezca['VIS-'+optic+'_MN_MNOLDAMP_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_MN_MNOLDAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_MN_MNOLDAMP_%s_GAIN'%DOF] = 0
    #wait(GuardState,5])

def mn_oldcctrl_off(GuardState,optic):
    for DOF in ['P','Y']:
        ezca['VIS-'+optic+'_MN_OLDCCTRL_%s_TRAMP'%DOF] = 5.0
        ezca.switch('VIS-'+optic+'_MN_OLDCCTRL_%s'%DOF, 'INPUT', 'OFF')
        if ezca['VIS-'+optic+'_MN_OLDCCTRL_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_MN_OLDCCTRL_%s_GAIN'%DOF] = 0
        ezca['VIS-'+optic+'_MN_OLDCCTRL_%s_RSET'%DOF] = 2
    
    ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_TRAMP'] = 5.0
    ezca.switch('VIS-'+optic+'_BF_PAYOL_DCCTRL_Y', 'INPUT', 'OFF')
    if ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_GAIN'] != 0.0:
            ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_GAIN'] = 0
    ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_RSET'] = 2
    ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_GAIN'] = 1
    #wait(GuardState,5])


def bf_damp_off(GuardState,optic,rampt):
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = rampt
        if ezca['VIS-'+optic+'_BF_DAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_BF_DAMP_%s_GAIN'%DOF] = 0
    #wait(GuardState,60)

def gas_damp_off(GuardState,optic,rampt):
    for DOF in ['BF','F3','F2','F1','F0']:
        ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = rampt
        if ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = 0
    #wait(GuardState,5)

def ip_damp_off(GuardState,optic,rampt):
    for DOF in ['L','T','Y']:
        ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF] = rampt
        if ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = 0
    #wait(GuardState,60)

def ip_blend_off(GuardSate,optic,rampt):
    for DOF in ['L','T','Y']:
        ezca['VIS-'+optic+'_IP_BLEND_ACC%s_TRAMP'%DOF] = rampt
        if ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = 0
    #wait(GuardState,10)

def ip_tidal_off(GuardState,optic,rampt):
    ezca['VIS-'+optic+'_IP_TIDAL_L_TRAMP'] = rampt
    if ezca['VIS-'+optic+'_IP_TIDAL_L_GAIN'] != 0.0:
        ezca['VIS-'+optic+'_IP_TIDAL_L_GAIN'] = 0


def oa_off(GuardState,optic):
    for DOF in ['P','Y']:
        ezca['VIS-'+optic+'_MN_OPTICALIGN_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_MN_OPTICALIGN_%s_OFFSET'%DOF] = 0


# Added on 2019 Aug. 13th ----------------------- #
def ip_sc_off(GuardState,optic):
    for DOF in ['L','T']:
        ezca['VIS-'+optic+'_IP_SENSCORR_%s_TRAMP'%DOF] = 5.0
        if ezca['VIS-'+optic+'_IP_SENSCORR_%s_GAIN'%DOF] != 0.0:
            ezca['VIS-'+optic+'_IP_SENSCORR_%s_GAIN'%DOF] = 0
# ----------------------------------------------- #


def test_pay_off(GuardState,optic):
    for DOF in ['L', 'P', 'Y']:
        ezca['VIS-'+optic+'_TM_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_TM_TEST_%s_GAIN'%DOF] = 0
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_IM_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_IM_TEST_%s_GAIN'%DOF] = 0
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_MN_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_MN_TEST_%s_GAIN'%DOF] = 0
    #wait(GuardState,ezca['VIS-'+optic+'_MN_TEST_Y_TRAMP'])

def test_twr_off(GuardState, optic):
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_BF_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_BF_TEST_%s_GAIN'%DOF] = 0
    for DOF in ['BF','F3','F2','F1','F0']:
        ezca['VIS-'+optic+'_%s_TEST_GAS_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_%s_TEST_GAS_GAIN'%DOF] = 0
    for DOF in ['L','T','Y']:
        ezca['VIS-'+optic+'_IP_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_IP_TEST_%s_GAIN'%DOF] = 0
    #wait(GuardState,ezca['VIS-'+optic+'_IP_TEST_Y_TRAMP'])

def wait(GuardState,t):
    GuardState.timer['waiting'] = t
    while not (GuardState.timer['waiting']):
        log('waiting')
    return True

def clear_PAYINPUT_MTRX(optic):
    for row in range(24):
        for col in range(5):
            ezca['VIS-' + optic + '_PAY_OLSERVO_OL2PK_' + str(row+1) + '_' + str(col+1)] = 0

            
def clear_PAYOUTPUT_MTRX(optic):
    for row in range(18):
        for col in range(24):
            ezca['VIS-' + optic + '_PAY_OLSERVO_PK2EUL_' + str(row+1) + '_' + str(col+1)] = 0

def config_BPCOMB(optic, DOFNUM, InputSensor, OutputStage, onSW, TRAMP = 5, LIMIT = 15000):
    SWbit1 = 1 * 2**2 + 0 * 2**3 # INPUT on, offset off
    SWbit2 = 1 * 2**(24-16) +  1 * 2**(25-16) +  1 * 2**(26-16) # LIMIT on, DECIMATION on, OUTPUT on

    for ii in range(6):
        if ii+1 in onSW:
            SWbit1 = SWbit1 + 1 * 2**(ii * 2 + 4)

    for ii in range(6,10):
        if ii+1 in onSW:
            SWbit2 = SWbit2 + 1 * 2**((ii-6)*2)

    ezca['VIS-' + optic + '_PAY_OLSERVO_OL2PK_' + str(DOFNUM) + '_' + str(InSensList.index(InputSensor) + 1)] = 1
    ezca['VIS-' + optic + '_PAY_OLSERVO_PK2EUL_' + str(OutStageList.index(OutputStage)+1) + '_' + str(DOFNUM)] = 1
    #ezca['VIS-' + optic + '_PAY_OLSERVO_DAMP_P{:0>2}'.format(DOFNUM) + '_SW1S'] = SWbit1
    #ezca['VIS-' + optic + '_PAY_OLSERVO_DAMP_P{:0>2}'.format(DOFNUM) + '_SW2S'] = SWbit2    
    ezca['VIS-' + optic + '_PAY_OLSERVO_DAMP_P{:0>2}'.format(DOFNUM) + '_TRAMP'] = TRAMP
    ezca['VIS-' + optic + '_PAY_OLSERVO_DAMP_P{:0>2}'.format(DOFNUM) + '_LIMIT'] = LIMIT
    ezca['VIS-' + optic + '_PAY_OLSERVO_DAMP_P{:0>2}'.format(DOFNUM) + '_RSET'] = 2
    ezca['VIS-' + optic + '_PAY_OLSERVO_DAMP_P{:0>2}'.format(DOFNUM) + '_GAIN'] = 1

def config_BPCOMB_from_description(optic, DOFNUM, onSW, TRAMP = 5, LIMIT = 20000):
    description = ezca['VIS-' + optic + '_PAY_OLSERVO_DAMP_P{:0>2}'.format(DOFNUM) + '_STRING']
    usable = description[:6] == 'USABLE'
    inputSens = description[7:10]
    outputStage = description[11:14]
    if usable and (inputSens in InSensList) and (outputStage in OutStageList):
        config_BPCOMB(optic, DOFNUM, inputSens, outputStage, onSW, TRAMP, LIMIT)
            
def disable_BPCOMB(optic):
    for ii in range(24):
        ezca['VIS-' + optic + '_PAY_OLSERVO_DAMP_P{:0>2}'.format(ii+1) + '_GAIN'] = 0



def all_off(GuardState,optic):
    pay_off(GuardState, optic)
    test_twr_off(GuardState,optic)
    log('Turning tower damping off')
    bf_damp_off(GuardState,optic,60.0)
    gas_damp_off(GuardState,optic,10.0)
    ip_damp_off(GuardState,optic,60.0)
    ip_blend_off(GuardState,optic,10.0)
    ip_tidal_off(GuardState,optic,60.0)
    ip_sc_off(GuardState,optic)
    wait(GuardState,60)
    
def pay_off(GuardState, optic, oaOffFlag=True):
    log('Turning TM oplev damping off')
    tm_damp_off(GuardState,optic)
    log('Turning IM OLDAMP off')
    im_oldamp_off(GuardState,optic)
    log('Turning MN OLDAMP off')
    mn_oldamp_off(GuardState,optic)
    if oaOffFlag:
        log('Turning Optic Align offset off')
        oa_off(GuardState,optic)
    else:
        for DOF in ['P', 'Y']:
            ezca['VIS-'+optic+'_MN_OPTICALIGN_%s_OFFSET'%DOF] = 0
    log('Turning payload test filter off')
    test_pay_off(GuardState,optic)
    log('Turning payload damping off')
    im_damp_off(GuardState,optic)
    mn_damp_off(GuardState,optic)
    mn_oldcctrl_off(GuardState,optic)
    disable_BPCOMB(optic)
    tm_lock_off(GuardState,optic)
    im_lock_off(GuardState,optic)
    mn_lock_off(GuardState,optic)
    tm_dither_off(GuardState,optic)
    im_dither_off(GuardState,optic)
    mn_dither_off(GuardState,optic)
    wait(GuardState,5)


def all_off_quick(GuardState,optic):
    pay_off(GuardState,optic)
    log('Turning tower damping off')
    rampT_p = ezca['VIS-'+optic+'_SHUTDOWN_RAMPT']
    rampT_t = ezca['VIS-'+optic+'_TWR_SHUTDOWN_RAMPT']
    rampT = max(rampT_p,rampT_t)
    bf_damp_off(GuardState,optic,rampT)
    gas_damp_off(GuardState,optic,rampT)
    ip_damp_off(GuardState,optic,rampT)
    ip_blend_off(GuardState,optic,rampT)
    ip_sc_off(GuardState,optic)
    ip_tidal_off(GuardState,optic,rampT)
    test_twr_off(GuardState, optic)
    wait(GuardState,rampT)
    

