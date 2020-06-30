'''
vislib is the library of the utility function for VIS guardain.
[TODO] VISfunctions.py needs to be marged.
Function
--------
get_Type(optic)
make_DOFList(DOF)
DiagChan(optic,DOF)
DCSetChan(optic,DOF)
DitherINF(optic,DOF,stage='TM')
init_DitherINF(optic, DOF='Both', stage='TM')
ISCINF(optic,DOF)
init_ISCINF(optic, DOF='Both', stage='TM', engaged_FM=[])
Lock(optic,DOF,stage='TM')
init_Lock(optic, DOF='Both', stage='TM', engaged_FM=[], gain=1)
update_DCsetpoint(optic, DOF='Both')
OpticAlign(optic,DOF,LigoFilter=False)
init_OpticAlign(optic, DOF='Both', ramptime=RampTimeOpticAlignDC)
'''
import kagralib
from visparams import *
import cdsutils
import time
##########################
# valuables
##########################
IE = ['I','E']
XY = ['X','Y']
DOFs = ['PIT','YAW']
TypeA = 'TypeA'
TypeB = 'TypeB'
TypeBp = 'TypeBp'
TypeC = 'TypeC'

TypeList = {
    'TypeA':['%sTM%s'%(ie,xy) for ie in IE for xy in XY],
    'TypeB':['BS'] + ['SR%s'%s for s in ['2','3','M']],
    'TypeBp':['PR%s'%s for s in ['2','3','M']],
    'TypeC':['IMMT1','IMMT2','OMMT1','OMMT2','OSTM'] + ['MC%s'%s for s in ['E','I','O']],
}

##########################
#utility functions
##########################
def get_Type(optic):
    for key in TypeList.keys():
        if optic in TypeList[key]:
            return key

def initialize_VISFB(optic, chanFunc, DOFs, stages, gain, ramptime, engaged_FM=[], disable_input=False, clear_history=True, hold_offset=False):
    '''initialize_VISFB(optic, chanFunc, **kwargs):
    function to initialize FB
    
    Arguments
    ---------
    optic: string
    chanFunc: function
        function of FB to initialize, e.g. ISCINF. chanFunc needs to take optic,  DOF, and stage as argument.
    DOFs: list of string
        DOF which the channel has. e.g. ['LEN','PIT','YAW'], ['YAW','PIT'], ['LEN','TRANS','VERT','YAW','ROLL','PIT']
    stages: list of string
        stage list. e.g. ['IM','TM']
    
    following arguments is for kagralib.init_FB. see init_FB
    gain: float
    ramptime: float
    engaged_FM: list of string
    disable_input: bool
    clear_history: bool
    '''
    for DOF in DOFs:
        for stage in stages:
            kagralib.init_FB(chanFunc(optic=optic, DOF=DOF, stage=stage),
                             engaged_FM = engaged_FM,
                             gain = gain,
                             ramptime = ramptime,
                             disable_input = disable_input,
                             clear_history = clear_history,
                             hold_offset = hold_offset,
            )

def stop_OUTPUT(optic, chanFunc, DOFs, stages, ramptime, TRIPPED=False):
    '''stop_OUTPUT(optic, chanFunc, DOFs, stages):
    stop outputs of the VIS channel rappidly. 
    
    Arguments
    ---------
    optic: string
    chanFunc: function
        function of FB to initialize, e.g. ISCINF. chanFunc needs to take optic,  DOF, and stage as argument.
    DOFs: list of string
        DOF which the channel has. e.g. ['LEN','PIT','YAW'], ['YAW','PIT'], ['LEN','TRANS','VERT','YAW','ROLL','PIT']
    stages: list of string
        stage list. e.g. ['IM','TM']
    TRIPPED: bool
        If it's true, turn off the output immediately

    Return
    ------
    flag: bool
        If all filter are turned off.
    '''
    ramp_time = [ramptime, 0][TRIPPED]
    flag = True
    for DOF in DOFs:
        for stage in stages:
            FB = chanFunc(optic=optic, DOF=DOF, stage=stage)
            if TRIPPED:
                FB.ramp_gain(0, 0, False)
                FB.all_off()
                FB.RSET.put(2)
            else:
                if not FB.GAIN.get()==0 or FB.is_gain_ramping():
                    FB.ramp_gain(0, ramp_time, False)
                    flag &= False
                else:
                    FB.all_off()
                    FB.RSET.put(2)
    return flag
            

            
##########################
# Chanel managers
##########################
## Channel
def DiagChan(optic,DOF):
    '''DiagChan(optic,DOF)
    function to get channal name of diagonalized oplev value

    Arguments
    ---------
    optic: string
    DOF: string 
       Chose from PIT,YAW,LEN
     
    Return
    ------
    channel: string
    '''
    if optic in TypeList[TypeC]:
        return 'VIS-%s_TM_OPLEV_%s_OUT16'%(optic,DOF)
    else:
        return 'VIS-%s_TM_OPLEV_%s_DIAGMON'%(optic,DOF)

## FB
'''These function return a LIGOFilter object. All of them have arguments as follows:
optic: stpring
    optic name
DOF: string
    DOF. Chose from 'LEN','PIT','YAW','TRANS','VERT','ROLL'
stage: string
    stage. Chose from 'MN', 'IM', 'TM'
'''

def OLSet(optic,DOF,stage=None,string=False):
    StageList = {
        'TypeA':'TM',
        'TypeB':'IM',
        'TypeBp':'TM',
        'TypeC':'TM'
        }
    Type = get_Type(optic)
    if string:
        return 'VIS-%s_%s_OLSET_%s'%(optic,StageList[Type],DOF[0])
    else:
        return ezca.get_LIGOFilter('VIS-%s_%s_OLSET_%s'%(optic,StageList[Type],DOF[0]))

    
def DitherINF(optic,DOF,stage='TM'):
    '''DitherINF(optic,DOF,stage='TM')

    Arguments
    --------
    optic: string
    DOF: string 
       Chose from PIT,YAW
    stage: string
       Chose from TM(all), IM(TypeB,TypeA), MN(TypeA)
     
    Return
    ------
    channel: LIGOFilter
    '''
    return ezca.get_LIGOFilter('VIS-%s_%s_DITHER_%s'%(optic,stage,DOF[0]))


def init_DitherINF(optic, stage, DOF = ['PIT','YAW']):
    if isinstance(DOF,str):
        DOF = [DOF,]
    for DoF in DOF:
        FB = DitherINF(optic, DoF, stage)
        kagralib.init_FB(FB, engaged_FM = ['FM1'], gain=1)
    return True

def ISCINF(optic,DOF,stage=None):
    Type = get_Type(optic)
    stage = {'TypeA':'','TypeB':'','TypeBp':'TM_','TypeC':'TM_'}
    return ezca.get_LIGOFilter('VIS-%s_%sISCINF_%s'%(optic,stage[Type],DOF[0]))

def init_ISCINF(optic, DoFs=['PIT','YAW']):
    for DoF in DoFs:
        FB = ISCINF(optic, DoF, stage=None)
        kagralib.init_FB(FB, gain=1)
        
def Lock(optic,DOF,stage='TM'):
    return ezca.get_LIGOFilter('VIS-%s_%s_LOCK_%s'%(optic,stage,DOF[0]))

def init_Lock(optic, stage, DoFs=['PIT','YAW'],gain=0):
    for DoF in DoFs:
        FB = DitherINF(optic, DoF, stage=None)
        kagralib.init_FB(FB, gain=gain)

def OpticAlign(optic,DOF,stage=None):
    Type = get_Type(optic)
    stagelist = {
        'TypeA':'MN',
        'TypeB':'IM',
        'TypeBp':'IM',
        'TypeC':'TM',
        }
    return ezca.get_LIGOFilter('VIS-%s_%s_OPTICALIGN_%s'%(optic,stagelist[Type],DOF[0]))


def OLDamp(optic,DOF,stage='TM'):
    Type = get_Type(optic)
    if stage == 'TM':
        return ezca.get_LIGOFilter('VIS-%s_%s_DAMP_%s'%(optic,stage,DOF[0]))
    
    else:
        if Type == 'TypeBp':
            return ezca.get_LIGOFilter('VIS-%s_%s_OLDAMP_%s'%(optic,stage,DOF[0]))
        elif Type == 'TypeB':
            return ezca.get_LIGOFilter('VIS-%s_%s_OLDCCTRL_%s'%(optic,stage,DOF[0]))
        elif Type == 'TypeA':
            return ezca.get_LIGOFilter('VIS-%s_%s_TMOLDAMP_%s'%(optic,stage,DOF[0]))
        
    

def OLServo(optic, DOF, stage=None):
    if get_Type(optic) == 'TypeA':
        return ezca.get_LIGOFilter('VIS-%s_TM_SERVO_%s'%(optic,DOF[0]))
    else:
        return ezca.get_LIGOFilter('VIS-%s_TM_OPLEV_SERVO_%s'%(optic,DOF))

def MNOLDamp(optic,DOF,stage=None):
    return ezca.get_LIGOFilter('VIS-%s_MN_MNOLDAMP_%s'%(optic,DOF[0]))

def LocalDamp(optic, DOF, stage):
    if get_Type(optic) == 'TypeA':
        return ezca.get_LIGOFilter('VIS-%s_%s_PSDAMP_%s'%(optic,stage,DOF[0]))
    else:
        return ezca.get_LIGOFilter('VIS-%s_%s_DAMP_%s'%(optic,stage,DOF[0]))

def GASDamp(optic, DOF, stage=None):
    '''
    DOF is stage in this function.
    Example
    -------
    GASDamp('PR3','BF')
    '''
    return ezca.get_LIGOFilter('VIS-%s_%s_DAMP_GAS'%(optic,DOF))

def IPDamp(optic, DOF, stage=None):
    return ezca.get_LIGOFilter('VIS-%s_IP_DAMP_%s'%(optic, DOF[0]))
                               
##########################
# WD managers
##########################

WDList = {
    'TypeC':['TM',],
    'TypeB':['TM','IMV','IMH',],
    'TypeBtower':['GAS','IP'],
    'TypeBp':['TM','IM1','IM2','GAS','BFH','BFV'],
    'TypeBptower':[],
    'TypeAtower':['BFH','BFV','GAS','PI'],
    'TypeA':['TM','IMB','IMH','MNIMV','MNH']
    }

def is_WD_tripped(optic, payload=True):
    '''is_WD_tripped(optic, payload)
    function to check analog WD
    
    Arguments
    ---------
    optic: string
    payload: bool
    if it's false, it check the WD of the tower part.

    Example
    -------
    is_WD_tripped('IMMT')
    '''
    Type = get_Type(optic)

    if not payload:
        Type += 'tower'
    WDs = WDList[Type]


    ######################################
    # Needs to be removed.
    if optic.lower() in ['bs','srm']:
        WDs = []
    elif optic.lower() in ['itmx','itmy','etmx','etmy','pr3','prm']:
        WDs = []

    ######################################


    # reference for check WD. from 16 bit to 19 bit are for the WD readback
    ref = 0
    for ii in range(16,20):
        ref += 2**ii
    return any([(int(ezca['VIS-%s_BIO_%s_MON'%(optic,BIO)]) & ref) for BIO in WDs])

DGWDList = {
    'TypeC':['TM',],
    'TypeBptower':[],
    'TypeBp':['TM','IM','BF','SF'],
    'TypeBtower':['BF','F1','F0','IP'],
    'TypeB':['TM','IM'],
    'TypeAtower':['BF','F3','F2','F1','F0','IP'],
    'TypeA':['TM','IM','MN'],
    }

def is_DGWD_tripped(optic, payload=True):
    '''is_DGWD_tripped(optic, payload)
    function to check digital WD
    
    Arguments
    ---------
    optic: string
    payload: bool
    if it's false, it check the WD of the tower part.

    Example
    -------
    is_WD_tripped('IMMT')
    '''
    Type = get_Type(optic)
    if not payload:
        Type += 'tower'

    return any([ezca['VIS-%s_%s_WDMON_STATE'%(optic,WD)] == 2 for WD in DGWDList[Type]])

##########################
# Oplev managers

##########################
def update_DCsetpoint(optic, DOF='Both'):
    '''update_DCsetpoint(optic)
    Function to update DC setpoint. DC setpoint is set to oplev value
    
    Argument
    --------
    optic: string
    DOF: string chosen in ['PIT','YAW','Both']

    Example
    -------
    update_DCsetpoint('ETMX')
    '''
    if get_Type(optic) == 'TypeC':
        return None
    DOFs = make_DOFList(DOF)
    for dof in DOFs:
        ezca[DCSetChan(optic,dof)] = ezca[DiagChan(optic,dof)]
    
def is_OL_lost(optic):
    '''is_OL_lost(optic)
    Function to check OL is lost

    Argument
    --------
    optic: string

    Example
    -------
    is_OL_lost('BS')
    '''
    status=False
    # for dof in ['PIT', 'YAW']:
    #     status |= abs(ezca['VIS-' + optic + '_TM_OPLEV_' + dof + '_DIAGMON'] - ezca['VIS-' + optic + '_GOOD_OPLEV_' + dof]) > OLGoodRange[dof]
    return status


def is_OL_insane(optic):
    '''is_OL_insane(optic)
    Function to check OLRMS

    Argument
    --------
    optic: string

    Example
    -------
    is_OL_insane('BS')
    '''
    status=False
    # for dof in ['L', 'P', 'Y']:
    #     status |= ezca['VIS-' + optic + '_TM_OPLEV_BLRMS_' + dof + '_300M_1'] > OLRMSThreshold[optic][dof]
    return status

##########################
# BOCOMB managers
##########################
# List for the BP comb
InSensList = ['MNP','MNY','TML','TMP','TMY']
#OutStageList = ['BFY','MNL','MNT','MNV','MNR','MNP','MNY','IML','IMT','IMV','IMR','IMP','IMY','TML','TMP','TMY']
OutStageList = ['BFL','BFT','BFY','MNL','MNT','MNV','MNR','MNP','MNY','IML','IMT','IMV','IMR','IMP','IMY','TML','TMP','TMY']

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
    #ezca['VIS-' + optic + '_PAY_OLSERVO_DAMP_P{:0>2}'.format(DOFNUM) + '_RSET'] = 2
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

def offload2OPAL(self, optic, gain, functype='run'):
    sustype = get_Type(optic)
    if functype == 'main':
        if sustype == 'TypeA':
            self.channel = {DoF:OpticAlign(optic, DoF) for DoF in ['PIT','YAW']}
            self.channel['MNOL'] = MNOLDamp(optic, 'YAW')
            self.readback = {
                'PIT':OLDamp(optic, 'PIT', 'MN'),
                'YAW':MNOLDamp(optic, 'YAW', 'MN'),
                'MNOL':OLDamp(optic, 'YAW', 'MN'),
            }

        else:
            self.channel = {DoF:OpticAlign(optic, DoF) for DoF in ['PIT','YAW']}
            self.readback = {DoF:OLDamp(optic, DoF, 'IM') for DoF in ['PIT','YAW']}
        for DoF in ['PIT','YAW']:
            if not self.channel[DoF].GAIN.get():
                self.channel[DoF].ramp_offset(0,0,False)
                time.sleep(0.3)
                self.channel[DoF].ramp_gain(1,0,False)    

        self.servo = {
            DoF:cdsutils.Servo(
                ezca, self.channel[DoF].OFFSET.channel,
                readback=self.readback[DoF].OUT16.channel,gain=gain[DoF],ugf=0.01
            )
            for DoF in self.channel.keys()
        }

    else:
        for DoF in self.servo.keys():
            self.channel[DoF].TRAMP.put(10)
            if not self.channel[DoF].is_offset_ramping():

                self.servo[DoF].step()
        
    
