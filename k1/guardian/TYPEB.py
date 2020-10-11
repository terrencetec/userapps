# Terrence email: astrotec@connect.hku.hk
import time
import math
from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import os
import VISfunction as vf
from burt import *
import vistoolstest as vistools
import sdflib
import cdslib
import sys

globaldir = dir()

__,OPTIC = SYSTEM.split('_') # This instruction retrieves the name of the Guardian node running the code e.i. the suspension name: SYSTEM='VIS_BS'. 
optic = OPTIC.lower() #2019-01-16 Terrence, 2019-04-11 MB; it changes to lower case the return value of OPTIC: BS --> bs
visObj = None
def checkvis():
    global visObj
    if visObj == None:
        visObj=vistools.Vis((SYSTEM,ezca))

userapps = '/opt/rtcds/userapps/release/'
path_to_snap = '/opt/rtcds/kamioka/k1/target/{modname}/{modname}epics/burt/'
IFO = os.getenv('IFO')
ifo = IFO.lower()
SITE = os.getenv('SITE')
site = SITE.lower()
dorw = 2
verbose=False

def modelName(OPTIC):
    return ifo+'vis'+OPTIC

##################################################
# initialization values
state = 'TOWER' # For determining where the guardian state is.
# initial REQUEST state
request = 'INIT'

# NOMINAL state, which determines when node is OK
nominal = 'ALIGNED'

##################################################
##################################################
# Define useful constants here

class timeConsts():
    IPSETRamp=30
    GASSETRamp=10
    OLSETRamp=10
    DCCTRLRamp=5
    DAMPRamp=5
    offRamp=5
    OLSERVORamp=0
    rampNotifyInterval=1

class buttons():
#     format:
#     buttonName=['Switch name (shown as channel name)','bit number']
    input=['SW1',2]
    offset=['SW1',3]
    output=['SW2',10]
    ramping=['SW2',12] #bit number is 12 if the filter is turned on by setting gain to 1, 13 if the filter is turned on by pressing offset. NOTE: INPUT/OUTPUT DOESN'T TRIGGER RAMP.
    clrHist=['RSET',1]
#

typeBtime=timeConsts()
setRampDict={
'IP':typeBtime.IPSETRamp,
'F0':typeBtime.GASSETRamp,
'F1':typeBtime.GASSETRamp,
'BF':typeBtime.GASSETRamp,
'align':typeBtime.OLSETRamp,
'misalign':typeBtime.OLSETRamp
}
typeBsw=buttons()
##################################################
WD = ['TM','IM','BF','F1','F0','IP']
TWR_WD = ['BF','F1','F0','IP']
PAY_WD = ['TM','IM']
BIO = ['TM','IMV','IMH','GAS','IP'] # full list #FIXME THIS ONE MAYBE NO USED
# Below is a list of BIO watchdogs that the guardian will check. Note that checking IMH is disabled in vistools.
# We confirmed that the TM coil driver watchdog is disabled, therefore we don't put it into the PAY_BIO list. Terrence  11-20-2019.
if OPTIC=='BS':
    TWR_BIO = ['BIO_GAS_MON','BIO_IP_MON']
    PAY_BIO = ['BIO_IMV_MON','BIO_IMH_MON']
else:
    TWR_BIO = ['BIO_GAS_MON','BIO_IP_MON']
    PAY_BIO = ['BIO_TM_MON','BIO_IMV_MON','BIO_IMH_MON']
#BIO = ['TM','IMV','GAS','IP'] # list with IMH removed to work around spurious WD output.
ochitsuke_sec = 20 # waiting time to stay at DAMPED in seconds
# Tool for taking safe snapshot
reqfile = vf.req_file_path(optic)+'/autoBurt.req'
snapfile = '/opt/rtcds/userapps/release/vis/k1/burtfiles/'+vf.modelName(optic)+'_guardian_safe.snap'
safeDir= userapps+'vis/'+ifo+'/burtfiles/'+ifo+'vis'+optic+'_safe.snap'
snapDir= userapps+'vis/'+ifo+'/burtfiles/'
alignSnap = snapDir+ifo+'vis'+optic+'p_align.snap'
misalignSnap= snapDir+ifo+'vis'+optic+'p_misalign.snap'
ipSnap= snapDir+ifo+'vis'+optic+'t_IP.snap'
gasSnap= snapDir+ifo+'vis'+optic+'t_GAS.snap'
setSnapDict={
'IP':ipSnap,
'F0':gasSnap,
'F1':gasSnap,
'BF':gasSnap,
'align':alignSnap,
'misalign':misalignSnap
}
##################################################
# functions
def is_tripped_BIO(BIO):
    return False
    AnalogWD_state = False
    for name in BIO:
        AnalogWD_state = AnalogWD_state or ( (int(ezca['VIS-'+OPTIC+'_BIO_'+name+'_MON']) & 983040) != 0 ) # check if any coil driver is tripped or not
    return AnalogWD_state

def is_tripped_SWD(OPTIC,WD):
    WD_state = False
    for name in WD:
        WD_state = WD_state or (ezca['VIS-'+OPTIC+'_'+name+'_WDMON_STATE'] != 1) # check if any user WD is tripped or not
    return WD_state

def is_tripped_IOP(OPTIC):
    return ezca['VIS-'+OPTIC+'_TWR_DACKILL_STATE'] != 1 or ezca['VIS-'+OPTIC+'_PAY_DACKILL_STATE'] != 1 # check if IOP WD is tripped

def is_tripped(OPTIC,WD,BIO):
    # list of WD channel names and BIO channel names to be specified
    return is_tripped_SWD(OPTIC,WD) or is_tripped_IOP(OPTIC) or is_tripped_BIO(BIO)

def valFromSnap(stage,block,dof,snapDir,valName):
    dict=readBurt(snapDir)
    val=dict['K1:VIS-'+OPTIC+'_'+stage+'_'+block+'_'+dof+'_'+valName]
    return(val)

def waitForRamp(stateObj,level,text,rampNotifyInterval=typeBtime.rampNotifyInterval):
    global visObj
    if level == '':
        level=[]
    else:
        level=[level]
    stateObj.timer[text]=rampNotifyInterval
    visObj.waitForRampingToKickIn(stateObj,0.3)
    while any(visObj.dcctrlRampingRead(levels=level)) or any(visObj.dampRampingRead(levels=level)) or any(visObj.setRampingRead(levels=level)) or any(visObj.olDcctrlRampingRead(levels=level)) or any(visObj.olSetRampingRead(levels=level)) or any(visObj.idampRampingRead(levels=level)) or any(visObj.alignRampingRead(levels=level)):
        if any([i in visObj.trippedWds() for i in TWR_WD]) or any([i in visObj.trippedBioWds() for i in TWR_BIO]):
            return 'TRIPPED'
        if any([i in visObj.trippedWds() for i in PAY_WD]) or any([i in visObj.trippedBioWds() for i in PAY_BIO]):
            if state == 'PAYLOAD':
                return 'PAY_TRIPPED'
            else:
                return 'TRIPPED'
        if stateObj.timer[text]:
            stateObj.timer[text]=rampNotifyInterval

def beginControlSequence(stateObj,level):
    notify('Engaging '+level+' control 1: everything to OFF/0')
    filterReset(level)#reset filters. (This means it turns the filters off.)
    enableControl(level)#enable controllers
    if waitForRamp(stateObj,level,'ramping_up_DAMP_(DCCTRL)',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'
    rampSetpoint(level)#ramp setpoints. (This is the function which reads the snapshop file via valFromSnap.)
    if waitForRamp(stateObj,level,'ramping_up_SET',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'
    
def filterReset(level):
    global visObj
    visObj.dcctrlInputSwitchWrite('OFF',levels=[level])
    visObj.dampInputSwitchWrite('OFF',levels=[level])
    visObj.idampInputSwitchWrite('OFF',levels=[level])
    visObj.dcctrlOutputSwitchWrite('OFF',levels=[level])
    visObj.dampOutputSwitchWrite('OFF',levels=[level])
    visObj.idampOutputSwitchWrite('OFF',levels=[level])
    visObj.dcctrlOffsetSwitchWrite('OFF',levels=[level])
    visObj.dampOffsetSwitchWrite('OFF',levels=[level])
    visObj.idampOffsetSwitchWrite('OFF',levels=[level])

def enableControl(level):
    global visObj
    notify('Engaging '+level+' control 2: copying current position to SET')
    if level not in ['IM','TM']:
        setpoints=visObj.witRead([level])
        visObj.setRampWrite(0,levels=[level])
        visObj.setGainWrite(1,levels=[level])
        visObj.setOffsetWrite(setpoints,levels=[level])
    notify('Engaging '+level+' control 3: ramping up (DCCTRL) and DAMP gains')
    visObj.dcctrlPressButton('CLEAR',levels=[level])
    visObj.dampPressButton('CLEAR',levels=[level])
    visObj.idampPressButton('CLEAR',levels=[level])
    visObj.dcctrlInputSwitchWrite('ON',levels=[level])
    visObj.dampInputSwitchWrite('ON',levels=[level])
    visObj.idampInputSwitchWrite('ON',levels=[level])
    visObj.dcctrlOutputSwitchWrite('ON',levels=[level])
    visObj.dampOutputSwitchWrite('ON',levels=[level])
    visObj.idampOutputSwitchWrite('ON',levels=[level])
    visObj.dcctrlRampWrite(typeBtime.DCCTRLRamp,levels=[level])
    visObj.dampRampWrite(typeBtime.DAMPRamp,levels=[level])
    visObj.idampRampWrite(typeBtime.DAMPRamp,levels=[level])
    visObj.dcctrlGainWrite(1,levels=[level])
    visObj.dampGainWrite(1,levels=[level])
    visObj.idampGainWrite(1,levels=[level])

def rampSetpoint(level):
    global visObj
    DOFs=visObj.setPvs(levels=[level])
    DOFs=[i.replace(level+'_SET_','') for i in DOFs]
    notify('Engaging '+level+' control 4: moving to snapshot SET point')
    if level not in ['IM','TM']:
        for DOF in DOFs:
            val=valFromSnap(level,'SET',DOF,setSnapDict[level],'OFFSET')
            notify('Read SET offset for '+level+' '+DOF+' from '+setSnapDict[level])
            visObj.setRampWrite(setRampDict[level],levels=[level])
            visObj.setOffsetWrite(val,levels=[level],chans=[DOF])

def disengageControlSequence(stateObj,level,ramptime=typeBtime.offRamp):
    global visObj
    visObj.dcctrlRampWrite(ramptime,levels=[level])
    visObj.dcctrlGainWrite(0,levels=[level])
    if waitForRamp(stateObj,level,'ramping_down_DCCTRL',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'
    visObj.dampRampWrite(ramptime,levels=[level])
    visObj.dampGainWrite(0,levels=[level])
    visObj.idampRampWrite(ramptime,levels=[level])
    visObj.idampGainWrite(0,levels=[level])
    if waitForRamp(stateObj,level,'ramping_down_DAMP',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'

### No ol control state now. Only aligning and misaligning.
#def olBeginControlSequence(stateObj,level):
#    global visObj
#    olFilterReset(level) #reset filters
#    olEnableControl(level) #enable controllers
#    if waitForRamp(stateObj,level,'ramping_up_OLDCCTRL',rampNotifyInterval=2.5) == 'TRIPPED':
#        return 'TRIPPED'

def olAlign(stateObj,level):
    global visObj
    olFilterReset(level) #reset filters
    olEnableControl(level) #enable controllers
    if waitForRamp(stateObj,level,'ramping_up_OLDCCTRL',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'
    olRampSetpoint(level) #ramp setpoints
    if waitForRamp(stateObj,level,'ramping_up_OLSET',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'

def olFilterReset(level):
    global visObj
    notify('Engaging '+level+' OL control 1: everything to OFF/0')
    visObj.olDcctrlInputSwitchWrite('OFF',levels=[level])
    visObj.olDcctrlOutputSwitchWrite('OFF',levels=[level])
    visObj.olDcctrlOffsetSwitchWrite('OFF',levels=[level])

def olEnableControl(level):
    global visObj
    notify('Engaging'+level+' OL control 2: copying current TM position to OLSET')
    setpoints=visObj.witRead(levels=['TM'],chans=['PIT','YAW'])
    visObj.olSetRampWrite(0,levels=[level])
    visObj.olSetGainWrite(1,levels=[level])
    visObj.olSetOffsetWrite(setpoints,levels=[level])
    notify('Engaging'+level+' OL control 3: ramping up OLDCCTRL gain')
    visObj.olDcctrlPressButton('CLEAR',levels=[level])
    visObj.olDcctrlInputSwitchWrite('ON',levels=[level])
    visObj.olDcctrlOutputSwitchWrite('ON',levels=[level])
    visObj.olDcctrlRampWrite(typeBtime.DCCTRLRamp,levels=[level])
    visObj.olDcctrlGainWrite(1,levels=[level])

def olRampSetpoint(level):
##############################################################################
#Method replaced by reading a reference channel instead of reading from burt.#
##############################################################################
#    global visObj
#    DOFs=visObj.olSetPvs(levels=[level])
#    DOFs=[i.replace(level+'_OLSET_','') for i in DOFs]
#    notify('Engaging'+level+' OL control 4: moving to snapshot SET point ('+align+'ing)')
#    for DOF in DOFs:
#        val=valFromSnap(level,'OLSET',DOF,setSnapDict[align],'OFFSET')
#        val=ezca['VIS-'+OPTIC+'_GOOD_OPLEV_']
#        notify('Read OLSET offset for '+level+' '+DOF+' from '+setSnapDict[align])
#        visObj.olSetRampWrite(setRampDict[align],levels=[level])
#        visObj.olSetOffsetWrite(val,levels=[level],chans=[DOF])
##############################################################################
    global visObj
    DOFs=['PIT','YAW']
    notify('Engaging'+level+' OL control 4: moving to snapshot SET point (Aligning)')
    visObj.olSetRampWrite(setRampDict['align'],levels=[level])
    for DOF in DOFs:
        refChan='VIS-'+OPTIC+'_GOOD_OPLEV_'+DOF
        val=ezca[refChan]
        notify('%.1f'%val)
        notify('Read OLSET offset for '+level+' '+DOF+' from K1:'+refChan)
#        try:
#            visObj.olSetOffsetWrite(val,levels=[level],chans=[DOF])
#        except:
        if DOF == 'PIT':
            _DOF = 'P'
        elif DOF == 'YAW':
            _DOF = 'Y'
        else:
            notify('Not PIT-P, YAW-Y conversion. Do nothing and expect vistools to fail silently')
        visObj.olSetOffsetWrite(val,levels=[level],chans=[_DOF])
def olDisengageControlSequence(stateObj,level,ramptime=typeBtime.offRamp):
    global visObj
    visObj.olDcctrlRampWrite(ramptime,levels=[level])
    visObj.olDcctrlGainWrite(0,levels=[level])
    if waitForRamp(stateObj,level,'ramping_down_OLDCCTRL',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'
    
def freezingOutputs(stateObj):
    global visObj
    notify('Freezing OLDCCTRL/DCCTRL outputs')
    visObj.olDcctrlInputSwitchWrite('OFF')
    visObj.dcctrlInputSwitchWrite('OFF')
    notify('Disengaging DAMP controls')
    visObj.dampRampWrite(typeBtime.offRamp)
    visObj.dampGainWrite(0)
    visObj.idampRampWrite(typeBtime.offRamp)
    visObj.idampGainWrite(0)
    if waitForRamp(stateObj,'','ramping_down_DAMP',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'

def unFreezingOutputs(stateObj):
    global visObj
    notify('engaging DAMP controls')
    visObj.dampRampWrite(typeBtime.DAMPRamp)
    visObj.dampGainWrite(1)
    visObj.idampRampWrite(typeBtime.DAMPRamp)
    visObj.idampGainWrite(1)
    if waitForRamp(stateObj,'','ramping_up_DAMP',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'
    notify('Unfreezing OLDCCTRL/DCCTRL outputs')
    visObj.dcctrlInputSwitchWrite('ON')
    visObj.olDcctrlInputSwitchWrite('ON')

#def resetSafe(stateObj): ## Graceful shutoff
#    global visObj
#    notify('Turning off all outputs Safely')
#    visObj.testRampWrite(typeBtime.offRamp)
#    visObj.alignRampWrite(typeBtime.offRamp)
#    visObj.alignGainWrite(0)
#    visObj.testGainWrite(0)
#    if waitForRamp(stateObj,'','ramping_down_TEST_OPTICALIGN',rampNotifyInterval=2.5) == 'TRIPPED':
#        return 'TRIPPED'
#    visObj.olDcctrlRampWrite(typeBtime.offRamp)
#    visObj.olDcctrlGainWrite(0)
#    if waitForRamp(stateObj,'','ramping_down_OLDCCTRL',rampNotifyInterval=2.5) == 'TRIPPED':
#        return 'TRIPPED'
#    visObj.dcctrlRampWrite(typeBtime.offRamp)
#    visObj.dampRampWrite(typeBtime.offRamp)    
#    visObj.idampRampWrite(typeBtime.offRamp)
#    for level in ['TM','IM','F0','F1','BF','IP']:
#        visObj.dcctrlGainWrite(0,levels=[level])
#        if waitForRamp(stateObj,'','ramping_down_'+level+'DCCTRL',rampNotifyInterval=2.5) == 'TRIPPED':
#            return 'TRIPPED'
#        visObj.dampGainWrite(0,levels=[level])
#        visObj.idampGainWrite(0,levels=[level])
#        if waitForRamp(stateObj,'','ramping_down_'+level+'DAMP',rampNotifyInterval=2.5) == 'TRIPPED':
#            return 'TRIPPED'
#    visObj.masterSwitchWrite('OFF')

def resetSafe(stateObj): ## NOT Graceful shutoff
    global visObj
    notify('Turning off all outputs Safely')
    visObj.testRampWrite(typeBtime.offRamp)
    visObj.alignRampWrite(typeBtime.offRamp)
    visObj.alignGainWrite(0)
    visObj.testGainWrite(0)
    visObj.olDcctrlRampWrite(typeBtime.offRamp)
    visObj.olDcctrlGainWrite(0)
    visObj.dcctrlRampWrite(typeBtime.offRamp)
    visObj.dampRampWrite(typeBtime.offRamp)    
    visObj.idampRampWrite(typeBtime.offRamp)
    visObj.dcctrlGainWrite(0)
    visObj.dampGainWrite(0)
    visObj.idampGainWrite(0)
    if waitForRamp(stateObj,'','ramping_down_all_outputs',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'
    visObj.masterSwitchWrite('OFF')

def resetPayloadSafe(stateObj): ## NOT Graceful shutoff
    global visObj
    notify('Turning off all outputs Safely')
    visObj.testRampWrite(typeBtime.offRamp,levels=['TM','IM'])
    visObj.alignRampWrite(typeBtime.offRamp,levels=['TM','IM'])
    visObj.alignGainWrite(0,levels=['TM','IM'])
    visObj.testGainWrite(0,levels=['TM','IM'])
    visObj.olDcctrlRampWrite(typeBtime.offRamp,levels=['TM','IM'])
    visObj.olDcctrlGainWrite(0,levels=['TM','IM'])
    visObj.dcctrlRampWrite(typeBtime.offRamp,levels=['TM','IM'])
    visObj.dampRampWrite(typeBtime.offRamp,levels=['TM','IM'])    
    visObj.idampRampWrite(typeBtime.offRamp,levels=['TM','IM'])
    visObj.dcctrlGainWrite(0,levels=['TM','IM'])
    visObj.dampGainWrite(0,levels=['TM','IM'])
    visObj.idampGainWrite(0,levels=['TM','IM'])
    if waitForRamp(stateObj,'','ramping_down_payload_outputs',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'


def olMisalign(stateObj,level):
    global visObj
    notify('Misaligning using OPTIC ALIGN OFFSET')
    visObj.dampRampWrite(typeBtime.offRamp,levels=['TM'])
    visObj.dampGainWrite(0,levels=['TM'])
    if waitForRamp(stateObj,'','ramping_down_TM_DAMP',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'
    visObj.alignRampWrite(typeBtime.OLSETRamp,levels=[level]) #ramp OPTICALIGN #FIXME Refine ramp time
    visObj.alignOffsetWrite(800,levels=[level]) #FIXME Hardcoded offset 800
    visObj.alignOffsetSwitchWrite('ON',levels=[level])
    visObj.alignGainWrite(1,levels=[level])
    if waitForRamp(stateObj,level,'ramping_up_OPTIC_ALIGN',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'

def disengageOlMisalign(stateObj,level):
    global visObj
    notify('Disengaging OPTIC ALIGN')
    visObj.alignRampWrite(typeBtime.OLSETRamp,levels=[level]) #ramp OPTICALIGN #FIXME Refine ramp time
#    visObj.alignOffsetWrite(0,levels=[level])
    visObj.alignOffsetSwitchWrite('OFF',levels=[level])
    visObj.alignGainWrite(0,levels=[level])
    if waitForRamp(stateObj,level,'ramping_up_OPTIC_ALIGN',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'
    visObj.dampRampWrite(typeBtime.DAMPRamp,levels=['TM'])
    visObj.dampGainWrite(1,levels=['TM'])
    if waitForRamp(stateObj,'','ramping_up_TM_DAMP',rampNotifyInterval=2.5) == 'TRIPPED':
        return 'TRIPPED'

def freezingOlDcctrl():
    global visObj
    notify('Freezing OL DCCTRL')
    visObj.olDcctrlInputSwitchWrite('OFF')
    return True

def unfreezingOlDcctrl():
    global visObj
    notify('Unfreezing OL DCCTRL')
    visObj.olDcctrlInputSwitchWrite('ON')
    return True

def checkSafe():
    global visObj
    notify('Checking if all outputs are off')
    if any(visObj.testGainRead()+visObj.alignGainRead()+visObj.olDcctrlGainRead()+visObj.dcctrlGainRead()+visObj.dampGainRead()+visObj.idampGainRead()+[visObj.masterSwitchRead()]):
        return(False)
    else:
        return(True)

def checkPayloadSafe():
    global visObj
    notify('Checking if all payload outputs are off')
    if any(visObj.testGainRead(levels=['TM','IM'])+visObj.alignGainRead(levels=['TM','IM'])+visObj.olDcctrlGainRead(levels=['TM','IM'])+visObj.dcctrlGainRead(levels=['TM','IM'])+visObj.dampGainRead(levels=['TM','IM'])+visObj.idampGainRead(levels=['TM','IM'])):
        return(False)
    else:
        return(True)
##################################################
# STATE decorators

class watchdog_check(GuardStateDecorator):
    """Decorator to check watchdog"""
    def pre_exec(self):

#        if optic == 'bs':
#            return None
        global visObj
        checkvis()
#        for i in visObj.trippedWds():
#            if i in TWR_WD:
#                return 'TRIPPED'
        if any([i in visObj.trippedWds() for i in TWR_WD]) or any([i in visObj.trippedBioWds() for i in TWR_BIO]):
            pass
            #return 'TRIPPED'
        if any([i in visObj.trippedWds() for i in PAY_WD]) or any([i in visObj.trippedBioWds() for i in PAY_BIO]):
            if state == 'PAYLOAD':
                pass
                #return 'PAY_TRIPPED'
#            elif state == 'OBSERVATION': # Added by Terrence for teaching Fabian. This clause is not necessary when the tower trips in OBSERVATION state.
#                return 'OBSERVATION_TRIPPED'
            else:
                pass
                #return 'TRIPPED'

##################################################
class INIT(GuardState):
    """Guardian starts at the INIT state after a restart, but then 
    transitions immediately to SAFE after ramping down all outputs.
    """
	# we don't use the watchdog_check decorator here
    def main(self):
        global visObj
        checkvis() # we check manually here rather than in the watchdog_check decorator
        notify('INIT state, main()')
        
        return resetSafe(self)  

class TRIPPED(GuardState):
    """We end up at the TRIPPED state if any other state notices
	that one of the WDs has tripped. We ramp things down (but not 
	instantaneously in case it's just one of the BIO WDs and 
	other things are live), and then proceed to SAFE when the WDs have been reset.
    """
    redirect = False
    request = False
	# we don't use the watchdog_check decorator here because the WD will already be tripped
    def main(self):
        global visObj
        checkvis() # check manually here rather than in watchdog_check decorator
        global state
        if state == 'PAYLOAD':
            if not(any([i in visObj.trippedWds() for i in TWR_WD]) or any([i in visObj.trippedBioWds() for i in TWR_BIO])):
                return 'PAY_TRIPPED'
        notify('TRIPPED state, main()')
        resetSafe(self)  
        vf.vis_watchdog_tripped(optic)
        if visObj.trippedWds()!=[]:
            notify("Please reset software WD and DACKILL")
            return(False)
        if visObj.trippedWds('TWR')!=[]:
            notify("Please reset TOWER DACKILL")
            return(False)
        if visObj.trippedWds('PAY')!=[]:
            notify("Please reset PAYLOAD DACKILL")
            return(False)
        if any([i in visObj.trippedBioWds() for i in TWR_BIO]):
            notify("Please reset TOWER BIO")
            return(False)
        if any([i in visObj.trippedBioWds() for i in PAY_BIO]):
            notify("Please reset PAYLOAD BIO")
            return(False)
#        if visObj.trippedBioWds()!=[]:
#            notify("Please reset coil driver WD in BIO")
#            return(False)
        return True

	# we don't use the watchdog_check decorator here because the WD will already be tripped
    def run(self):
        ## turn OLSERVO off
        ezca.get_LIGOFilter('VIS-%s_TM_OPLEV_SERVO_PIT'%OPTIC).ramp_gain(0,0,False)
        ezca.get_LIGOFilter('VIS-%s_TM_OPLEV_SERVO_YAW'%OPTIC).ramp_gain(0,0,False)
        ezca['VIS-%s_IM_OLDCCTRL_P_RSET'%OPTIC] = 2
        ezca['VIS-%s_IM_OLDCCTRL_Y_RSET'%OPTIC] = 2
        
        global state
#        notify(state)
        global visObj
        checkvis() # check manually because we're not using watchdog_check decorator
        if checkSafe()==False:
            resetSafe(self)
        if visObj.trippedWds()!=[]:
            notify("Please reset software WD and DACKILL")
            return False
        if visObj.trippedWds('TWR')!=[]:
            notify("Please reset TOWER DACKILL")
            return(False)
        if visObj.trippedWds('PAY')!=[]:
            notify("Please reset PAYLOAD DACKILL")
            return(False)
        if any([i in visObj.trippedBioWds() for i in TWR_BIO]):
            notify("Please reset TOWER BIO")
            return(False)
        if any([i in visObj.trippedBioWds() for i in PAY_BIO]):
            notify("Please reset PAYLOAD BIO")
            return(False)
#        if visObj.trippedBioWds()!=[]:
#            notify("Please reset coil driver WDs in BIO")
#            return False
        return True

class PAY_TRIPPED(GuardState):
    """We end up at the TRIPPED state if any other state notices
	that one of the WDs has tripped. We ramp things down (but not 
	instantaneously in case it's just one of the BIO WDs and 
	other things are live), and then proceed to SAFE when the WDs have been reset.
    """
    redirect = False
    request = False
	# we don't use the watchdog_check decorator here because the WD will already be tripped
    def main(self):
        global visObj
        checkvis() # check manually here rather than in watchdog_check decorator
        notify('PAY_TRIPPED state, main()')
        resetPayloadSafe(self)  
        vf.vis_pay_watchdog_tripped(optic)
        if visObj.trippedWds()!=[]:
            notify("Please reset software WD and DACKILL")
            return(False)
        if visObj.trippedWds('TWR')!=[]:
            notify("Please reset TOWER DACKILL")
            return(False)
        if visObj.trippedWds('PAY')!=[]:
            notify("Please reset PAYLOAD DACKILL")
            return(False)
        if any([i in visObj.trippedBioWds() for i in TWR_BIO]):
            notify("Please reset TOWER BIO")
            return(False)
        if any([i in visObj.trippedBioWds() for i in PAY_BIO]):
            notify("Please reset PAYLOAD BIO")
            return(False)
#        if visObj.trippedBioWds()!=[]:
#            notify("Please reset coil driver WD in BIO")
#            return(False)
        return True

	# we don't use the watchdog_check decorator here because the WD will already be tripped
    def run(self):

        ## turn OLSERVO off
        ezca.get_LIGOFilter('VIS-%s_TM_OPLEV_SERVO_PIT'%OPTIC).ramp_gain(0,0,False)
        ezca.get_LIGOFilter('VIS-%s_TM_OPLEV_SERVO_YAW'%OPTIC).ramp_gain(0,0,False)
        ezca['VIS-%s_IM_OLDCCTRL_P_RSET'%OPTIC] = 2
        ezca['VIS-%s_IM_OLDCCTRL_Y_RSET'%OPTIC] = 2

        global visObj
        checkvis() # check manually because we're not using watchdog_check decorator
        if checkPayloadSafe()==False:
            resetPayloadSafe(self)
        if visObj.trippedWds()!=[]:
            notify("Please reset software WD and DACKILL")
            return False
        if visObj.trippedWds('TWR')!=[]:
            notify("Please reset TOWER DACKILL")
            return(False)
        if visObj.trippedWds('PAY')!=[]:
            notify("Please reset PAYLOAD DACKILL")
            return(False)
        if any([i in visObj.trippedBioWds() for i in TWR_BIO]):
            notify("Please reset TOWER BIO")
            return(False)
        if any([i in visObj.trippedBioWds() for i in PAY_BIO]):
            notify("Please reset PAYLOAD BIO")
            return(False)
#        if visObj.trippedBioWds()!=[]:
#            notify("Please reset coil driver WDs in BIO")
#            return False
        return True
class SAFE(GuardState):
    """
    SAFE has all actuation shut off at the master switch.
    """
    @watchdog_check
    def main(self):

        global visObj
        global state
        state = 'TOWER'
        notify('In SAFE dayo!')
        for suffix in ['P','T']: # by Miyo
            fec = cdslib.ezca_get_dcuid('K1VIS'+OPTIC+suffix)
            sdflib.restore(fec,'safe') 
        if checkSafe() == False:
            resetSafe(self)

    @watchdog_check
    def run(self):
        ## turn OLSERVO off
        ezca.get_LIGOFilter('VIS-%s_TM_OPLEV_SERVO_PIT'%OPTIC).ramp_gain(0,0,False)
        ezca.get_LIGOFilter('VIS-%s_TM_OPLEV_SERVO_YAW'%OPTIC).ramp_gain(0,0,False)
        ezca['VIS-%s_IM_OLDCCTRL_P_RSET'%OPTIC] = 2
        ezca['VIS-%s_IM_OLDCCTRL_Y_RSET'%OPTIC] = 2

        global visObj
        if checkSafe() == False:
            resetSafe(self)
        return True
class MASTERSWITCH_ON(GuardState):
    """Turn on master switch and continue to NEUTRAL"""
    index = 2
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'TOWER'
        visObj.masterSwitchWrite('ON')
        return True

class MASTERSWITCH_OFF(GuardState):
    """Turn off master switch and continue to SAFE"""
    index = 3
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'TOWER'
        visObj.masterSwitchWrite('OFF')
        return True

class NEUTRAL(GuardState):
    """As for SAFE but with the master switch on and the TEST gains set to 1."""
    index = 4
    @watchdog_check
    def main(self):
        global state
        state = 'TOWER'
        visObj.testRampWrite(0)
        visObj.testOffsetWrite(0.0)
        visObj.testGainWrite(1.0)

    @watchdog_check
    def run(self):
        global visObj
        return True

class ENGAGING_IP_CONTROL(GuardState):
    index=5
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'TOWER'
        return beginControlSequence(self,level='IP')

class DISENGAGING_IP_CONTROL(GuardState):
    index=6
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'TOWER'
        return disengageControlSequence(self,level='IP')

class IP_CONTROL_ENGAGED(GuardState):
    index= 7
    @watchdog_check
    def run(self):
        global visObj
        global state
        state = 'TOWER'
        return True

class ENGAGING_IM_DAMP(GuardState):
    index = 8
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return beginControlSequence(self,level='IM')

class DISENGAGING_IM_DAMP(GuardState):
    index=92
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return disengageControlSequence(self,level='IM')

class IM_DAMP_ENGAGED(GuardState):
    index=101
    @watchdog_check
    def run(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return True

class ENGAGING_TM_DAMP(GuardState):
    index = 111
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return beginControlSequence(self,level='TM')

class DISENGAGING_TM_DAMP(GuardState):
    index=112
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return disengageControlSequence(self,level='TM')

class TM_DAMP_ENGAGED(GuardState):
    index=121
    @watchdog_check
    def run(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return True

class ENGAGING_GAS_CONTROL(GuardState):
    index=8
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'TOWER'
        for level in ['BF','F1','F0']:
            if(beginControlSequence(self,level=level) == 'TRIPPED'):
                pass
                #return 'TRIPPED'
        return True

class DISENGAGING_GAS_CONTROL(GuardState):
    index=9
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'TOWER'
        for level in ['F0','F1','BF']:
            if disengageControlSequence(self,level=level) == 'TRIPPED':
                return 'TRIPPED'
        return True

class GAS_CONTROL_ENGAGED(GuardState):
    index=80
    @watchdog_check
    def run(self):
        global visObj
        global state
        state = 'TOWER'
        return True

#class ENGAGING_OL_CONTROL(GuardState):
#    index=131
#    request = False
#    @watchdog_check
#    def main(self):
#        global visObj
#        return olBeginControlSequence(self,level='IM')

class DISENGAGING_ALIGN(GuardState):
    index=132
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return olDisengageControlSequence(self,level='IM')

#class OL_CONTROL_ENGAGED(GuardState):
#    index=140
#    @watchdog_check
#    def run(self):
#        global visObj
#        return True
class ALIGNING(GuardState):
    index=131
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return olAlign(self,level='IM')

class ALIGNED(GuardState):
    index=140
    @watchdog_check
    def run(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return True

class MISALIGNING(GuardState):
    index=133
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return olMisalign(self,level='IM')

class MISALIGNED(GuardState):
    index=141
    @watchdog_check
    def run(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return True

class DISENGAGING_MISALIGN(GuardState):
    index=134
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return disengageOlMisalign(self,level='IM')
#        return olDisengageControlSequence(self,level='IM') # new concept of OL_ALIGN is to not change alignment


class FREEZING_OUTPUTS(GuardState):
    index=151
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'TOWER'
        return freezingOutputs(self)

class FLOAT(GuardState):
    index=160
    @watchdog_check
    def run(self):
        global visObj
        global state
        state = 'TOWER'
        return True

class UNFREEZING_OUTPUTS(GuardState):
    index=152
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'TOWER'
        return unFreezingOutputs(self)
    
class OL_DCCTRL_FLOAT(GuardState):
    index = 161
    # State to hold at the DCCTRL point without DCLOOP
    @watchdog_check
    def run(self):
        global visObj
        global state
        state = 'TOWER'
        return True
#    def main(self):
#        
#        log('turn off the input of DCCTRL')
#        ezca.switch('VIS-' + OPTIC.upper() + '_IM_OLDCCTRL_P','INPUT','OFF')
#        ezca.switch('VIS-' + OPTIC.upper() + '_IM_OLDCCTRL_Y','INPUT','OFF')
#        self.timer['waiting'] = 5

#    @watchdog_check
#    def run(self):
#        return self.timer['waiting']

class FREEZING_OL_DCCTRL(GuardState):
    index = 153
    request = False
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return freezingOlDcctrl()

class UNFREEZING_OL_DCCTRL(GuardState):
    index = 154
    request = False
    # State to hold at the DCCTRL point without DCLOOP(MN)
    @watchdog_check
    def main(self):
        global visObj
        global state
        state = 'PAYLOAD'
        return unfreezingOlDcctrl()
#    def main(self):
#        log('turn on the input of DCCTRL')
#        for DOF in ['P','Y']:
#            ezca.switch('VIS-' + OPTIC + '_IM_OLDCCTRL_' + DOF,'INPUT','ON')
#            
#        self.timer['waiting'] = 5

#            
#    @watchdog_check
#    def run(self):
#        return self.timer['waiting']


edges = [
('INIT','SAFE'),
('TRIPPED','SAFE'),
('PAY_TRIPPED','ENGAGING_IM_DAMP'),
('SAFE','MASTERSWITCH_ON'),
('MASTERSWITCH_ON','NEUTRAL'),
('NEUTRAL','ENGAGING_IP_CONTROL'),
('NEUTRAL','MASTERSWITCH_OFF'),
('MASTERSWITCH_OFF','SAFE'),
('ENGAGING_IP_CONTROL','IP_CONTROL_ENGAGED'),
('IP_CONTROL_ENGAGED','DISENGAGING_IP_CONTROL'),
('DISENGAGING_IP_CONTROL','NEUTRAL'),
('IP_CONTROL_ENGAGED','ENGAGING_GAS_CONTROL'),
('ENGAGING_GAS_CONTROL','GAS_CONTROL_ENGAGED'),
('GAS_CONTROL_ENGAGED','DISENGAGING_GAS_CONTROL'),
('DISENGAGING_GAS_CONTROL','IP_CONTROL_ENGAGED'),
('GAS_CONTROL_ENGAGED','ENGAGING_IM_DAMP'),
('ENGAGING_IM_DAMP','IM_DAMP_ENGAGED'),
('IM_DAMP_ENGAGED','DISENGAGING_IM_DAMP'),
('DISENGAGING_IM_DAMP','GAS_CONTROL_ENGAGED'),
('IM_DAMP_ENGAGED','ENGAGING_TM_DAMP'),
('ENGAGING_TM_DAMP','TM_DAMP_ENGAGED'),
('TM_DAMP_ENGAGED','DISENGAGING_TM_DAMP'),
('DISENGAGING_TM_DAMP','IM_DAMP_ENGAGED'),
('TM_DAMP_ENGAGED','ALIGNING'),
('TM_DAMP_ENGAGED','MISALIGNING'),
('ALIGNING','ALIGNED'),
('ALIGNED','DISENGAGING_ALIGN'),
('ALIGNED','FREEZING_OUTPUTS'),
('FREEZING_OUTPUTS','FLOAT'),
('FLOAT','UNFREEZING_OUTPUTS'),
('UNFREEZING_OUTPUTS','ALIGNED'),
('MISALIGNING','MISALIGNED'),
('MISALIGNED','DISENGAGING_MISALIGN'),
('DISENGAGING_ALIGN','TM_DAMP_ENGAGED'),
('DISENGAGING_MISALIGN','TM_DAMP_ENGAGED'),
('ALIGNED','FREEZING_OL_DCCTRL'),
('FREEZING_OL_DCCTRL','OL_DCCTRL_FLOAT'),
('OL_DCCTRL_FLOAT','UNFREEZING_OL_DCCTRL'),
('UNFREEZING_OL_DCCTRL','ALIGNED')
]

