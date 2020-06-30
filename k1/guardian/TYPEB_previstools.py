import time
import math
from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import os
import sendAlert as sa
import VISfunction as vf
from burt import *
import vistools
import sys
#from ezca import Ezca

userapps = '/opt/rtcds/userapps/release/'
IFO = os.getenv('IFO')
ifo = IFO.lower()
SITE = os.getenv('SITE')
site = SITE.lower()
dorw = 2
verbose=False

def modelName(optic):
    return ifo+'vis'+optic

##################################################
# initialization values

# initial REQUEST state
request = 'SAFE'

# NOMINAL state, which determines when node is OK
nominal = 'SAFE'

##################################################
##################################################
# Define useful constants here
class timeConsts():
	IPSETRamp=30
	GASSETRamp=10
	OLSETRamp=10
	DCCTRLRamp=5
	DAMPRamp=5
	offRamp=10
	OLSERVORamp=0
class buttons():
# 	format:
# 	buttonName=['Switch name (shown as channel name)','bit number']
	input=['SW1',2]
	offset=['SW1',3]
	output=['SW2',10]
	ramping=['SW2',12] #bit number is 12 if the filter is turned on by setting gain to 1, 13 if the filter is turned on by pressing offset. NOTE: INPUT/OUTPUT DOESN'T TRIGGER RAMP.
	clrHist=['RSET',1]
#

typeBtime=timeConsts()
typeBsw=buttons()
##################################################
optic = SYSTEM.split('_')[1] #2019-01-16 Terrence
#vis = vistools.Vis()
print('%s is a type-B SAS'%(optic)) #For debugging
WD = ['TM','IM','BF','F1','F0','IP']
BIO = ['TM','IMV','IMH','GAS','IP']
ochitsuke_sec = 20 # waiting time to stay at DAMPED in seconds
# Tool for taking safe snapshot
reqfile = vf.req_file_path(optic)+'/autoBurt.req'
snapfile = '/opt/rtcds/userapps/release/vis/k1/burtfiles/'+vf.modelName(optic)+'_guardian_safe.snap'
safeDir= userapps+'vis/'+ifo+'/burtfiles/'+ifo+'vis'+optic.lower()+'_safe.snap'
alignDir= userapps+'vis/'+ifo+'/burtfiles/'+ifo+'vis'+optic.lower()+'_align.snap'
misalignDir= userapps+'vis/'+ifo+'/burtfiles/'+ifo+'vis'+optic.lower()+'_misalign.snap'

##################################################
# functions
def is_tripped_BIO(optic,BIO):
    AnalogWD_state = False
    for name in BIO:
        AnalogWD_state = AnalogWD_state or ( (int(ezca['VIS-'+optic+'_BIO_'+name+'_MON']) & 983040) != 0 ) # check if any coil driver is tripped or not
    return AnalogWD_state

def is_tripped_SWD(optic,WD):
    WD_state = False
    for name in WD:
        WD_state = WD_state or (ezca['VIS-'+optic+'_'+name+'_WDMON_STATE'] != 1) # check if any user WD is tripped or not
    return WD_state

def is_tripped_IOP(optic):
    return ezca['VIS-'+optic+'_DACKILL_STATE'] != 1 # check if IOP WD is tripped

def is_tripped(optic,WD,BIO):
    # list of WD channel names and BIO channel names to be specified
    return is_tripped_SWD(optic,WD) or is_tripped_IOP(optic) or is_tripped_BIO(optic,BIO)

def is_ramping(stage,block,dof,rampButton=typeBsw.ramping):
	val1=(int(ezca.read('VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+rampButton[0]+'R'))&2**12)>>12
#	log(int(ezca.read('VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+rampButton[0]+'R')))
#	time.sleep(0.3)
	val2=(int(ezca.read('VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+rampButton[0]+'R'))&2**13)>>13
#	print(val2)
	return val1==1 or val2 ==1

def buttonOn(stage,block,dof,button):
	val=(int(ezca.read('VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+button[0]+'R'))&2**button[1])>>button[1]
	while val==0:												#While the button is off, switch it on
		ezca['VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+button[0]] = 2**button[1] #Release button
		time.sleep(0.3)                              #Had to introduce some delay in between channeling writing, or else some will be ignored. I don't know why.
		val=(int(ezca.read('VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+button[0]+'R'))&2**button[1])>>button[1]
def buttonOff(stage,block,dof,button):
	val=(int(ezca.read('VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+button[0]+'R'))&2**button[1])>>button[1]
	while val==1:												#While the button is on, switch it off
		ezca['VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+button[0]] = 2**button[1] #Release button
		time.sleep(0.3)                              #Had to introduce some delay in between channeling writing, or else some will be ignored. I don't know why.
		val=(int(ezca.read('VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+button[0]+'R'))&2**button[1])>>button[1]
def buttonRelease(stage,block,dof,button):
	ezca['VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+button[0]] = 2**button[1] #Release button
def setVal(stage,block,dof,valName,val):
	ezca['VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+valName]=val
	time.sleep(0.3)  
def valFromSnap(stage,block,dof,snapDir,valName):
	dict=readBurt(snapDir)
	val=dict['K1:VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+valName]
	return(val)
def valFromEzca(stage,block,dof,valName):
	val=ezca.read('VIS-'+optic+'_'+stage+'_'+block+'_'+dof+'_'+valName)
	return(val)
def engageControl(stage,DIR = alignDir):
    notify('Engaging control')
    #Cutting off controller input, output and offset
    for STAGE in [stage]:
        for BLOCK in ['DCCTRL','DAMP']:
            if STAGE == 'IP':
                for DOF in ['L','T','Y']:
                    for button in [typeBsw.input,typeBsw.offset,typeBsw.output]:
                        buttonOff(STAGE,BLOCK,DOF,button)
            if STAGE == 'BF' or STAGE == 'F1' or STAGE == 'F0':
                 for DOF in ['GAS']:
                    for button in [typeBsw.input,typeBsw.offset,typeBsw.output]:
                        buttonOff(STAGE,BLOCK,DOF,button)
            if STAGE == 'OL':
                for DOF in ['P','Y']:
                    for button in [typeBsw.input,typeBsw.offset,typeBsw.output]:
                        buttonOff('IM',STAGE+BLOCK,DOF,button)
            if STAGE == 'IM' and BLOCK == 'DAMP':
                for DOF in ['L','T','V','R','P','Y']:
                    for button in [typeBsw.input,typeBsw.offset,typeBsw.output]:
                        buttonOff(STAGE,BLOCK,DOF,button)
            if STAGE == 'TM' and BLOCK == 'DAMP':
                for DOF in ['L','P','Y']:
                    for button in [typeBsw.input,typeBsw.offset,typeBsw.output]:
                        buttonOff(STAGE,BLOCK,DOF,button)
                for DOF in ['LEN','PIT','YAW']:
                    for button in [typeBsw.input,typeBsw.offset,typeBsw.output]:
                        buttonOff(STAGE,'OPLEV_SERVO',DOF,button)
#    notify('Setting Setpoint to current position')
    for STAGE in [stage]:
        for BLOCK in ['SET']:
            if STAGE == 'IP':
                for DOF in ['L','T','Y']:
                    val=ezca.read('VIS-'+optic+'_'+STAGE+'_BLEND_LVDT'+DOF+'_OUTPUT')
                    setVal(STAGE,BLOCK,DOF,'TRAMP',0)
                    setVal(STAGE,BLOCK,DOF,'GAIN',1)
                    setVal(STAGE,BLOCK,DOF,'OFFSET',val)
                    for button in [typeBsw.input,typeBsw.output,typeBsw.offset]:
                        buttonOn(STAGE,BLOCK,DOF,button)
            if STAGE == 'BF' or STAGE == 'F1' or STAGE == 'F0':
                for DOF in ['GAS']:
                    val=ezca.read('VIS-'+optic+'_'+STAGE+'_LVDTINF_'+DOF+'_OUTPUT')
                    setVal(STAGE,BLOCK,DOF,'TRAMP',0)
                    setVal(STAGE,BLOCK,DOF,'GAIN',1)
                    setVal(STAGE,BLOCK,DOF,'OFFSET',val)
                    for button in [typeBsw.input,typeBsw.output,typeBsw.offset]:
                        buttonOn(STAGE,BLOCK,DOF,button)
            if STAGE == 'OL':
                for DOF in ['P','Y']:
                    if DOF=='P':
                        val=ezca.read('VIS-'+optic+'_TM_OPLEV_SERVO_PIT_OUTPUT')
                    elif DOF == 'Y':
                        val=ezca.read('VIS-'+optic+'_TM_OPLEV_SERVO_YAW_OUTPUT')
                    setVal('IM',STAGE+BLOCK,DOF,'TRAMP',0)
                    setVal('IM',STAGE+BLOCK,DOF,'GAIN',1)
                    setVal('IM',STAGE+BLOCK,DOF,'OFFSET',val)
                    for button in [typeBsw.input,typeBsw.output,typeBsw.offset]:
                        buttonOn('IM',STAGE+BLOCK,DOF,button)
#	notify('Engaging DC and Damping control')
    for STAGE in [stage]:
        for BLOCK in ['DCCTRL','DAMP']:
            if STAGE == 'IP':
                for DOF in ['L','T','Y']:
                    buttonRelease(STAGE,BLOCK,DOF,typeBsw.clrHist)
                    for button in [typeBsw.input,typeBsw.offset,typeBsw.output]:
                        buttonOn(STAGE,BLOCK,DOF,button)
                    if BLOCK == 'DCCTRL':
                        setVal(STAGE,BLOCK,DOF,'TRAMP',typeBtime.DCCTRLRamp)
                    if BLOCK == 'DAMP':
                        setVal(STAGE,BLOCK,DOF,'TRAMP',typeBtime.DAMPRamp)
                    setVal(STAGE,BLOCK,DOF,'GAIN',1)
            if STAGE == 'BF' or STAGE == 'F1' or STAGE == 'F0':
                for DOF in ['GAS']:
                    buttonRelease(STAGE,BLOCK,DOF,typeBsw.clrHist)
                    for button in [typeBsw.input,typeBsw.offset,typeBsw.output]:
                        buttonOn(STAGE,BLOCK,DOF,button)
                    if BLOCK == 'DCCTRL':
                        setVal(STAGE,BLOCK,DOF,'TRAMP',typeBtime.DCCTRLRamp)
                    if BLOCK == 'DAMP':
                        setVal(STAGE,BLOCK,DOF,'TRAMP',typeBtime.DAMPRamp)
                    setVal(STAGE,BLOCK,DOF,'GAIN',1)
            if STAGE == 'OL':
                for DOF in ['P','Y']:
                    buttonRelease('IM',STAGE+BLOCK,DOF,typeBsw.clrHist)
                    for button in [typeBsw.input,typeBsw.offset,typeBsw.output]:
                        buttonOn('IM',STAGE+BLOCK,DOF,button)
                    if BLOCK == 'DCCTRL':
                        setVal('IM',STAGE+BLOCK,DOF,'TRAMP',typeBtime.DCCTRLRamp)
                    if BLOCK == 'DAMP':
                        setVal('IM',STAGE+BLOCK,DOF,'TRAMP',typeBtime.DAMPRamp)
                    setVal('IM',STAGE+BLOCK,DOF,'GAIN',1)
            if STAGE == 'IM' and BLOCK == 'DAMP':
                for DOF in ['L','T','V','R','P','Y']:
                    buttonRelease(STAGE,BLOCK,DOF,typeBsw.clrHist)
                    for button in [typeBsw.input,typeBsw.offset,typeBsw.output]:
                        buttonOn(STAGE,BLOCK,DOF,button)
                    setVal(STAGE,BLOCK,DOF,'TRAMP',typeBtime.DAMPRamp)
                    setVal(STAGE,BLOCK,DOF,'GAIN',1)
            if STAGE == 'TM' and BLOCK == 'DAMP':
                for DOF in ['L','P','Y']:
                    buttonRelease(STAGE,BLOCK,DOF,typeBsw.clrHist)
                    for button in [typeBsw.input,typeBsw.offset,typeBsw.output]:
                        buttonOn(STAGE,BLOCK,DOF,button)
                    setVal(STAGE,BLOCK,DOF,'TRAMP',typeBtime.DAMPRamp)
                    setVal(STAGE,BLOCK,DOF,'GAIN',1)
                for DOF in ['LEN','PIT','YAW']:
                    buttonRelease(STAGE,'OPLEV_SERVO',DOF,typeBsw.clrHist)
                    for button in [typeBsw.input,typeBsw.offset,typeBsw.output]:
                        buttonOn(STAGE,'OPLEV_SERVO',DOF,button)
                    setVal(STAGE,'OPLEV_SERVO',DOF,'TRAMP',typeBtime.OLSERVORamp)
                    setVal(STAGE,'OPLEV_SERVO',DOF,'GAIN',1)
	while 1:
		ramping=0
		for STAGE in [stage]:
			for BLOCK in ['DCCTRL','DAMP']:
				if STAGE == 'IP':
					for DOF in ['L','T','Y']:
						if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping|=1
				if STAGE == 'BF' or STAGE == 'F1' or STAGE == 'F0':
					for DOF in ['GAS']:
						if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping|=1
                if STAGE == 'IM' and BLOCK == 'DAMP':
                    for DOF in ['L','T','V','R','P','Y']:
                        if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping|=1
                if STAGE == 'OL':
                    for DOF in ['P','Y']:
                        if is_ramping('IM',STAGE+BLOCK,DOF) == True:
							ramping|=1
                if STAGE == 'TM' and BLOCK == 'DAMP':
                    for DOF in ['L','P','Y']:
                        if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping|=1
                    for DOF in ['LEN','PIT','YAW']:
                        if is_ramping(STAGE,'OPLEV_SERVO',DOF) == True:
							ramping|=1
		if ramping == 1:
			notify('Ramp not finish, please wait')
		else:
			break
		if is_tripped(optic,WD,BIO)==True:
			return 'TRIPPED'
#	notify('Setting setpoint according to the align snapshot with 100 seconds ramp')
    for STAGE in [stage]:
        for BLOCK in ['SET']:
            if STAGE == 'IP':
                for DOF in ['L','T','Y']:
                    for valName in ['OFFSET']:
                        val=valFromSnap(STAGE,BLOCK,DOF,DIR,valName)
                        setVal(STAGE,BLOCK,DOF,'TRAMP',typeBtime.IPSETRamp)
                        setVal(STAGE,BLOCK,DOF,valName,val)
            if STAGE == 'BF' or STAGE == 'F1' or STAGE == 'F0':
                for DOF in ['GAS']:
                    for valName in ['OFFSET']:
                        val=valFromSnap(STAGE,BLOCK,DOF,DIR,valName)
                        setVal(STAGE,BLOCK,DOF,'TRAMP',typeBtime.GASSETRamp)
                        setVal(STAGE,BLOCK,DOF,valName,val)
#            if STAGE == 'OL':
#                for DOF in ['P','Y']:
#                    for valName in ['OFFSET']:
#                        val=valFromSnap('IM',STAGE+BLOCK,DOF,DIR,valName)
#                        setVal('IM',STAGE+BLOCK,DOF,'TRAMP',typeBtime.OLSETRamp)
#                        setVal('IM',STAGE+BLOCK,DOF,valName,val)
	while 1:
		ramping=0
		for STAGE in [stage]:
			for BLOCK in ['SET']:
				if STAGE == 'IP':
					for DOF in ['L','T','Y']:
						if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping|=1
				if STAGE == 'BF' or STAGE == 'F1' or STAGE == 'F0':
					for DOF in ['GAS']:
						if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping|=1
                if STAGE == 'OL':
                    for DOF in ['P','Y']:
                        if is_ramping('IM',STAGE+BLOCK,DOF) == True:
							ramping|=1
		if ramping == 1:
			notify('Ramp not finish, please wait')
		else:
			break
		if is_tripped(optic,WD,BIO)==True:
			return 'TRIPPED'
	return True

def align(DIR=alignDir):
    for STAGE in ['OL']:
        for BLOCK in ['SET']:
            if STAGE == 'OL':
                for DOF in ['P','Y']:
                    for valName in ['OFFSET']:
                        val=valFromSnap('IM',STAGE+BLOCK,DOF,DIR,valName)
                        setVal('IM',STAGE+BLOCK,DOF,'TRAMP',typeBtime.OLSETRamp)
                        setVal('IM',STAGE+BLOCK,DOF,valName,val)
	while 1:
		ramping=0
		for STAGE in ['OL']:
		    for BLOCK in ['SET']:
		        for DOF in ['P','Y']:
		            if is_ramping('IM',STAGE+BLOCK,DOF) == True:
			            ramping|=1
		if ramping == 1:
			notify('Ramp not finish, please wait')
		else:
			break
		if is_tripped(optic,WD,BIO)==True:
			return 'TRIPPED'
	return True

#def disableAlign(DIR=alignDir):
#    for STAGE in ['OL']:
#        for BLOCK in ['SET']:
#            if STAGE == 'OL':
#                for DOF in ['P','Y']:
#                    for valName in ['OFFSET']:
#                        if DOF=='P':
#                            val=ezca.read('VIS-'+optic+'_TM_OPLEV_SERVO_PIT_OUTPUT')
#                        elif DOF == 'Y':
#                            val=ezca.read('VIS-'+optic+'_TM_OPLEV_SERVO_YAW_OUTPUT')
#                        setVal('IM',STAGE+BLOCK,DOF,'TRAMP',typeBtime.OLSETRamp)
#                        setVal('IM',STAGE+BLOCK,DOF,valName,val)
#    while 1:
#        ramping=0
#        for STAGE in ['OL']:
#            for BLOCK in ['SET']:
#                if STAGE == 'OL':
#                    for DOF in ['P','Y']:
#                        if is_ramping('IM',STAGE+BLOCK,DOF) == True:
#			                ramping|=1
#		if ramping == 1:
#			notify('Ramp not finish, please wait')
#		else:
#			break
#		if is_tripped(optic,WD,BIO)==True:
#			return 'TRIPPED'
#	return True

def rampDown(stage):
    for STAGE in [stage]:
        for BLOCK in ['DCCTRL','DAMP']:
            if STAGE == 'IP':
                for DOF in ['L','T','Y']:
                    setVal(STAGE,BLOCK,DOF,'TRAMP',typeBtime.offRamp)
                    setVal(STAGE,BLOCK,DOF,'GAIN',0)
            if STAGE == 'BF' or STAGE == 'F1' or STAGE == 'F0':
                for DOF in ['GAS']:
                    setVal(STAGE,BLOCK,DOF,'TRAMP',typeBtime.offRamp)
                    setVal(STAGE,BLOCK,DOF,'GAIN',0)
            if STAGE == 'OL':
                for DOF in ['P','Y']:
                    setVal('IM',STAGE+BLOCK,DOF,'TRAMP',typeBtime.offRamp)
                    setVal('IM',STAGE+BLOCK,DOF,'GAIN',0)
            if STAGE == 'IM' and BLOCK == 'DAMP':
                for DOF in ['L','T','V','R','P','Y']:
                    setVal(STAGE,BLOCK,DOF,'TRAMP',typeBtime.offRamp)
                    setVal(STAGE,BLOCK,DOF,'GAIN',0)
            if STAGE == 'TM' and BLOCK == 'DAMP':
                for DOF in ['L','P','Y']:
                    setVal(STAGE,BLOCK,DOF,'TRAMP',typeBtime.offRamp)
                    setVal(STAGE,BLOCK,DOF,'GAIN',0)
	while 1:
		ramping=0
		for STAGE in [stage]:
			for BLOCK in ['DCCTRL','DAMP']:
				if STAGE == 'IP':
					for DOF in ['L','T','Y']:
						if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping|=1
				if STAGE == 'BF' or STAGE == 'F1' or STAGE == 'F0':
					for DOF in ['GAS']:
						if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping|=1
                if STAGE == 'IM' and BLOCK == 'DAMP':
                    for DOF in ['L','T','V','R','P','Y']:
                        if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping|=1
                if STAGE == 'OL':
                    for DOF in ['P','Y']:
                        if is_ramping('IM',STAGE+BLOCK,DOF) == True:
							ramping|=1
                if STAGE == 'TM' and BLOCK == 'DAMP':
                    for DOF in ['L','P','Y']:
                        if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping|=1
                    for DOF in ['LEN','PIT','YAW']:
                        if is_ramping(STAGE,'OPLEV_SERVO',DOF) == True:
							ramping|=1
		if ramping == 1:
			notify('Ramp not finish, please wait')
		else:
			break
		if is_tripped(optic,WD,BIO)==True:
			return 'TRIPPED'
    return True
##################################################
# STATE decorators

class watchdog_check(GuardStateDecorator):
    """Decorator to check watchdog"""
    def pre_exec(self):
		if vf.is_tripped(optic,WD,BIO):
			return 'TRIPPED'

##################################################
class INIT(GuardState):
    index = 0
    goto = True
    

class TRIPPED(GuardState):
    index = 1
    redirect = False
    request = False
    def main(self):
#        vf.all_off(optic)
        waitFlag=0
        for BLOCK in ['TEST','DAMP']:
            for DOF in ['L', 'P', 'Y']:
                ezca['VIS-'+optic+'_TM_%s_%s_TRAMP'%(BLOCK,DOF)] = typeBtime.offRamp
                if(ezca.read('VIS-'+optic+'_TM_%s_%s_GAIN'%(BLOCK,DOF)))!=0:
                    waitFlag=1
                    ezca['VIS-'+optic+'_TM_%s_%s_GAIN'%(BLOCK,DOF)] = 0
#		for DOF in ['LEN','PIT','YAW']:
#			ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_TRAMP'%DOF] = typeBtime.offRamp
#			if(ezca.read('VIS-'+optic+'_TM_OPLEV_SERVO_%s_GAIN'%DOF))!=0:
#				waitFlag=1
#				ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_GAIN'%DOF] = 0
			#ezca.switch('VIS-'+optic+'_TM_OPLEV_SERVO_%s'%DOF,'FM1','OFF')
        ## IM ##
        for DOF in ['L','T','V','R','P','Y']:
            for BLOCK in ['TEST','DAMP']:			
                ezca['VIS-'+optic+'_IM_%s_%s_TRAMP'%(BLOCK,DOF)] = typeBtime.offRamp
                if(ezca.read('VIS-'+optic+'_IM_%s_%s_GAIN'%(BLOCK,DOF)))!=0:
                    waitFlag=1
                    ezca['VIS-'+optic+'_IM_%s_%s_GAIN'%(BLOCK,DOF)] = 0
                if DOF == 'P' or DOF == 'Y':
                    for BLOCK in ['OPTICALIGN','OLDAMP','OLDCCTRL']:			
                        ezca['VIS-'+optic+'_IM_%s_%s_TRAMP'%(BLOCK,DOF)] = typeBtime.offRamp
                        if(ezca.read('VIS-'+optic+'_IM_%s_%s_GAIN'%(BLOCK,DOF)))!=0:
                            waitFlag=1
                            ezca['VIS-'+optic+'_IM_%s_%s_GAIN'%(BLOCK,DOF)] = 0
        ## GAS ##
        for DOF in ['BF','F1','F0']:
            for BLOCK in ['TEST','DAMP','DCCTRL']:
                ezca['VIS-'+optic+'_%s_%s_GAS_TRAMP'%(DOF,BLOCK)] = typeBtime.offRamp
                if(ezca.read('VIS-'+optic+'_%s_%s_GAS_GAIN'%(DOF,BLOCK)))!=0:
                    waitFlag=1
                    ezca['VIS-'+optic+'_%s_%s_GAS_GAIN'%(DOF,BLOCK)] = 0
        ## IP ##
        for DOF in ['L','T','Y']:
            for BLOCK in ['TEST','DAMP','DCCTRL']:
                ezca['VIS-'+optic+'_IP_%s_%s_TRAMP'%(BLOCK,DOF)] = typeBtime.offRamp
                if(ezca.read('VIS-'+optic+'_IP_%s_%s_GAIN'%(BLOCK,DOF)))!=0:
                    waitFlag=1
                    ezca['VIS-'+optic+'_IP_%s_%s_GAIN'%(BLOCK,DOF)] = 0

        while 1:
			#check if ramp finished		
			## IP ##
            ramping = 0
            for STAGE in ['IP']:
                for BLOCK in ['TEST','DAMP','DCCTRL']:
                    for DOF in ['L','T','Y']:
                        if is_ramping(STAGE,BLOCK,DOF) == True:
                            ramping |= 1
                        else:
                            ramping |= 0
			## GAS ##
            for STAGE in ['F0','F1','BF']:
                for BLOCK in ['TEST','DAMP','DCCTRL']:
                    for DOF in ['GAS']:
                        if is_ramping(STAGE,BLOCK,DOF) == True:
                            ramping |= 1
                        else:
                            ramping |= 0
			## IM ##
            for STAGE in ['IM']:
                for BLOCK in ['OPTICALIGN','OLDAMP','OLDCCTRL']:
                    for DOF in ['P','Y']:
                        if is_ramping(STAGE,BLOCK,DOF) == True:
                            ramping |= 1
                        else:
                            ramping |= 0
                for BLOCK in ['TEST','DAMP']:
                    for DOF in ['L','T','V','R','P','Y']:
                        if is_ramping(STAGE,BLOCK,DOF) == True:
                            ramping |= 1
                        else:
                            ramping |= 0
                        ## TM ##
            for STAGE in ['TM']:
                for BLOCK in ['TEST','DAMP']:
                    for DOF in ['L','P','Y']:
                        if is_ramping(STAGE,BLOCK,DOF) == True:
                            ramping |= 1
                        else:
                            ramping |= 0

            if ramping == 1:
                notify('Ramping down, please wait')
            else:
                log('Turning off the master switch')
                ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
                break
            if is_tripped_SWD(optic,WD):
		notify("Please reset software WD and DACKILL")
                return(False)
            if is_tripped_IOP(optic):
		notify("Please reset DACKILL")
                return(False)
            if is_tripped_BIO(optic,BIO):
		notify("Please reset coil driver WD in BIO")
                return(False)
            return True
    def run(self):
        if is_tripped_SWD(optic,WD):
            notify("Please reset software WD and DACKILL")
	    return False
        if is_tripped_IOP(optic):
            notify("Please reset DACKILL")
	    return False
        if is_tripped_BIO(optic,BIO):
	    notify("Please reset coil driver WDs in BIO")
	    return False
        return True

class RESET(GuardState):
    index = 20
    goto = True
    request = False
    def main(self):
		
		return True

class SAFE(GuardState):
    """Safe state is with master switch off so as not to send any signal"""
    index = 30
    @watchdog_check
    def main(self):
		log(dir())
#        vf.all_off(optic) # turning off all test offsets, all damping filters and all optic align offsets
#		time.sleep(10)
		#		log('Turning off align offsets')
		## Turning off all ALIGN offsets with 10 seconds ramp
		## TM ##
		waitFlag=0
		for BLOCK in ['TEST','DAMP']:
			for DOF in ['L', 'P', 'Y']:
				ezca['VIS-'+optic+'_TM_%s_%s_TRAMP'%(BLOCK,DOF)] = typeBtime.offRamp
				if(ezca.read('VIS-'+optic+'_TM_%s_%s_GAIN'%(BLOCK,DOF)))!=0:
					waitFlag=1
					ezca['VIS-'+optic+'_TM_%s_%s_GAIN'%(BLOCK,DOF)] = 0
#		for DOF in ['LEN','PIT','YAW']:
#			ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_TRAMP'%DOF] = typeBtime.offRamp
#			if(ezca.read('VIS-'+optic+'_TM_OPLEV_SERVO_%s_GAIN'%DOF))!=0:
#				waitFlag=1
#				ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_GAIN'%DOF] = 0
			#ezca.switch('VIS-'+optic+'_TM_OPLEV_SERVO_%s'%DOF,'FM1','OFF')
		## IM ##
		for DOF in ['L','T','V','R','P','Y']:
			for BLOCK in ['TEST','DAMP']:			
				ezca['VIS-'+optic+'_IM_%s_%s_TRAMP'%(BLOCK,DOF)] = typeBtime.offRamp
				if(ezca.read('VIS-'+optic+'_IM_%s_%s_GAIN'%(BLOCK,DOF)))!=0:
					waitFlag=1
					ezca['VIS-'+optic+'_IM_%s_%s_GAIN'%(BLOCK,DOF)] = 0
			if DOF == 'P' or DOF == 'Y':
				for BLOCK in ['OPTICALIGN','OLDAMP','OLDCCTRL']:			
					ezca['VIS-'+optic+'_IM_%s_%s_TRAMP'%(BLOCK,DOF)] = typeBtime.offRamp
					if(ezca.read('VIS-'+optic+'_IM_%s_%s_GAIN'%(BLOCK,DOF)))!=0:
						waitFlag=1
						ezca['VIS-'+optic+'_IM_%s_%s_GAIN'%(BLOCK,DOF)] = 0
		## GAS ##
		for DOF in ['BF','F1','F0']:
			for BLOCK in ['TEST','DAMP','DCCTRL']:
				ezca['VIS-'+optic+'_%s_%s_GAS_TRAMP'%(DOF,BLOCK)] = typeBtime.offRamp
				if(ezca.read('VIS-'+optic+'_%s_%s_GAS_GAIN'%(DOF,BLOCK)))!=0:
					waitFlag=1
					ezca['VIS-'+optic+'_%s_%s_GAS_GAIN'%(DOF,BLOCK)] = 0
		## IP ##
		for DOF in ['L','T','Y']:
			for BLOCK in ['TEST','DAMP','DCCTRL']:
				ezca['VIS-'+optic+'_IP_%s_%s_TRAMP'%(BLOCK,DOF)] = typeBtime.offRamp
				if(ezca.read('VIS-'+optic+'_IP_%s_%s_GAIN'%(BLOCK,DOF)))!=0:
					waitFlag=1
					ezca['VIS-'+optic+'_IP_%s_%s_GAIN'%(BLOCK,DOF)] = 0
#		if(waitFlag==1):		
#			log('Sleeping for 10 seconds')
#			time.sleep(10)
		while 1:
			#check if ramp finished		
			## IP ##
			ramping = 0
			for STAGE in ['IP']:
				for BLOCK in ['TEST','DAMP','DCCTRL']:
					for DOF in ['L','T','Y']:
						if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping |= 1
						else:
							ramping |= 0
			## GAS ##
			for STAGE in ['F0','F1','BF']:
				for BLOCK in ['TEST','DAMP','DCCTRL']:
					for DOF in ['GAS']:
						if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping |= 1
						else:
							ramping |= 0
			## IM ##
			for STAGE in ['IM']:
				for BLOCK in ['OPTICALIGN','OLDAMP','OLDCCTRL']:
					for DOF in ['P','Y']:
						if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping |= 1
						else:
							ramping |= 0
				for BLOCK in ['TEST','DAMP']:
					for DOF in ['L','T','V','R','P','Y']:
						if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping |= 1
						else:
							ramping |= 0
			## TM ##
			for STAGE in ['TM']:
				for BLOCK in ['TEST','DAMP']:
					for DOF in ['L','P','Y']:
						if is_ramping(STAGE,BLOCK,DOF) == True:
							ramping |= 1
						else:
							ramping |= 0
#			for STAGE in ['TM','IM','BF','F0','F1','IP']:
#				if STAGE == 'IP' or STAGE == 'BF' or STAGE == 'F1' or STAGE == 'F0':
#					for BLOCK in ['TEST', 'DAMP', 
			if ramping == 1:
				notify('Ramp not finish, please wait')
			else:
				log('Turning off the master switch')
				ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
				break
			if is_tripped(optic,WD,BIO):
				return('TRIPPED')
		return True
    def run(self):
        if is_tripped(optic,WD,BIO):
            return('TRIPPED')
        else:
            return True
class MASTERSWITCH_ON(GuardState): # Turn on master switch
	index = 41
	request = False
	@watchdog_check
	def main(self):
		ezca['VIS-'+optic+'_MASTERSWITCH'] = 'ON' #Commented for testing
		return True

class ENGAGING_IP_CONTROL(GuardState):
    index=51
    request = False
    @watchdog_check
    def main(self):
        if(engageControl('IP') == 'TRIPPED'):
            return 'TRIPPED'
        else:
            return True

class IP_CONTROL_ENGAGED(GuardState):
    index=60
    @watchdog_check
    def run(self):
		if is_tripped(optic,WD,BIO)==True:
			return 'TRIPPED'
		else:
			return True

class ENGAGING_IM_DAMP(GuardState):
    index = 71
    request = False
    @watchdog_check
    def main(self):
        if(engageControl('IM') == 'TRIPPED'):
            return 'TRIPPED'
        else:
            return True

class DISABLE_IM_DAMP(GuardState):
    index=72
    request = False
    @watchdog_check
    def main(self):
        if rampDown('IM') == 'TRIPPED':
            return 'TRIPPED'
        else:
            return True

class IM_DAMP_ENGAGED(GuardState):
    index=80
    @watchdog_check
    def run(self):
		if is_tripped(optic,WD,BIO)==True:
			return 'TRIPPED'
		else:
			return True

class ENGAGING_TM_DAMP(GuardState):
    index = 91
    request = False
    @watchdog_check
    def main(self):
        if(engageControl('TM') == 'TRIPPED'):
            return 'TRIPPED'
        else:
            return True

class DISABLE_TM_DAMP(GuardState):
    index=92
    request = False
    @watchdog_check
    def main(self):
        if rampDown('TM') == 'TRIPPED':
            return 'TRIPPED'
        else:
            return True

class TM_DAMP_ENGAGED(GuardState):
    index=100
    @watchdog_check
    def run(self):
		if is_tripped(optic,WD,BIO)==True:
			return 'TRIPPED'
		else:
			return True

class ENGAGING_GAS_CONTROL(GuardState):
    index=111
    request = False
    @watchdog_check
    def main(self):
        for DOF in ['BF','F1','F0']:
            if(engageControl(DOF) == 'TRIPPED'):
                return 'TRIPPED'
        return True

class DISABLE_GAS_CONTROL(GuardState):
    index=112
    request = False
    @watchdog_check
    def main(self):
        for DOF in ['F0','F1','BF']:
            if rampDown(DOF) == 'TRIPPED':
                return 'TRIPPED'
        return True

class GAS_CONTROL_ENGAGED(GuardState):
    index=120
    @watchdog_check
    def run(self):
		if is_tripped(optic,WD,BIO)==True:
			return 'TRIPPED'
		else:
			return True

class ENGAGING_OL_CONTROL(GuardState):
    index=131
    request = False
    @watchdog_check
    def main(self):
        if(engageControl('OL') == 'TRIPPED'):
            return 'TRIPPED'
        else:
            return True

class DISABLE_OL_CONTROL(GuardState):
    index=132
    request = False
    @watchdog_check
    def main(self):
        if rampDown('OL') == 'TRIPPED':
            return 'TRIPPED'
        else:
            return True

class OL_CONTROL_ENGAGED(GuardState):
    index=140
    @watchdog_check
    def run(self):
		if is_tripped(optic,WD,BIO)==True:
			return 'TRIPPED'
		else:
			return True
class ALIGNING(GuardState):
    index=151
    request = False
    @watchdog_check
    def main(self):
        if (align(alignDir) == 'TRIPPED'):
            return 'TRIPPED'
        else:
            return True

class ALIGNED(GuardState):
    index=160
    @watchdog_check
    def run(self):
#		log(is_ramping('IM','OLSET','P'))
		if is_tripped(optic,WD,BIO)==True:
			return 'TRIPPED'
		else:
			return True

class MISALIGNING(GuardState):
    index=152
    request = False
    @watchdog_check
    def main(self):
        if (align(misalignDir) == 'TRIPPED'):
            return 'TRIPPED'
        else:
            return True

class MISALIGNED(GuardState):
    index=161
    @watchdog_check
    def run(self):
		if is_tripped(optic,WD,BIO)==True:
			return 'TRIPPED'
		else:
			return True

class DISABLE_ALIGN(GuardState):
    index=153
    request = False
    @watchdog_check
    def main(self):
        if rampDown('OL') == 'TRIPPED':
            return 'TRIPPED'
        else:
            return True

edges = [
('INIT','SAFE'),
('RESET', 'SAFE'),
('TRIPPED','SAFE'),
('SAFE','MASTERSWITCH_ON'),
('MASTERSWITCH_ON','ENGAGING_IP_CONTROL'),
('ENGAGING_IP_CONTROL','IP_CONTROL_ENGAGED'),
('IP_CONTROL_ENGAGED','ENGAGING_GAS_CONTROL'),
('ENGAGING_GAS_CONTROL','GAS_CONTROL_ENGAGED'),
('GAS_CONTROL_ENGAGED','DISABLE_GAS_CONTROL'),
('DISABLE_GAS_CONTROL','IP_CONTROL_ENGAGED'),
('GAS_CONTROL_ENGAGED','ENGAGING_IM_DAMP'),
('ENGAGING_IM_DAMP','IM_DAMP_ENGAGED'),
('IM_DAMP_ENGAGED','DISABLE_IM_DAMP'),
('DISABLE_IM_DAMP','GAS_CONTROL_ENGAGED'),
('IM_DAMP_ENGAGED','ENGAGING_TM_DAMP'),
('ENGAGING_TM_DAMP','TM_DAMP_ENGAGED'),
('TM_DAMP_ENGAGED','DISABLE_TM_DAMP'),
('DISABLE_TM_DAMP','IM_DAMP_ENGAGED'),
('TM_DAMP_ENGAGED','ENGAGING_OL_CONTROL'),
('ENGAGING_OL_CONTROL','OL_CONTROL_ENGAGED'),
('OL_CONTROL_ENGAGED','DISABLE_OL_CONTROL'),
('DISABLE_OL_CONTROL','TM_DAMP_ENGAGED'),
('OL_CONTROL_ENGAGED','ALIGNING'),
('OL_CONTROL_ENGAGED','MISALIGNING'),
('ALIGNING','ALIGNED'),
('MISALIGNING','MISALIGNED'),
('ALIGNED','MISALIGNING'),
('ALIGNED','DISABLE_ALIGN'),
('MISALIGNED','ALIGNING'),
('MISALIGNED','DISABLE_ALIGN'),
('DISABLE_ALIGN','TM_DAMP_ENGAGED')
]
#class OUTPUT_ON(GuardState):
## 2019-02-13, changed TEST to ALIGN for tower and deleted OPTICALIGN OFFSETs which
#    index = 41
#    request = False
#    @watchdog_check
#    def main(self):
#        log('Turning on the master switch (DISABLED for testing)')
#        #ezca['VIS-'+optic+'_MASTERSWITCH'] = 'ON'
#        log('Turning on the ALIGN filters')
#	val=ezca.read('VIS-'+optic+'_IP_DAMP_L_OUTPUT')
#	log('OUTMON: %f'%val)
#        ezca['VIS-'+optic+'_IP_DAMP_L_RSET'] = 2 #test
#	
#        ## IP ##
#        for DOF in ['L','T','Y']:
#            ezca['VIS-'+optic+'_IP_ALIGN_%s_TRAMP'%DOF] = 30.0 #2019-02-13 Tab missing, added. Terrence.
#            ezca['VIS-'+optic+'_IP_ALIGN_%s_GAIN'%DOF] = 1.0
#        ## GAS ##
#        for DOF in ['BF','F1','F0']:
#            ezca['VIS-'+optic+'_%s_ALIGN_GAS_TRAMP'%DOF] = 30.0
#            ezca['VIS-'+optic+'_%s_ALIGN_GAS_GAIN'%DOF] = 1.0
#        ## IM ##
#        for DOF in ['L','T','V','R','P','Y']:
#            ezca['VIS-'+optic+'_IM_TEST_%s_TRAMP'%DOF] = 30.0
#            ezca['VIS-'+optic+'_IM_TEST_%s_GAIN'%DOF] = 1.0
#        ## TM ##
#        for DOF in ['L','P','Y']:
#            ezca['VIS-'+optic+'_TM_TEST_%s_TRAMP'%DOF] = 5.0 #2019-02-13 Tab missing, added. Terrence.
#            ezca['VIS-'+optic+'_TM_TEST_%s_GAIN'%DOF] = 1.0
#	while(1):
#		val=ezca.read('VIS-'+optic+'_IP_DAMP_L_OUTPUT')
#		log('OUTMON: %f'%val)
#        return True
#    
#class UNDAMPED(GuardState):
#    index = 50
#    @watchdog_check
#    def run(self):
#        return True

#class DAMPING_ON(GuardState):
#    index = 51
#    request = False
#    @watchdog_check
#    def main(self):
#	log('Turning on the damping filters')
#	## IP ##
#        for DOF in ['L','T','Y']:
#            ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF] = 10.0
#            ezca['VIS-'+optic+'_IP_DAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = 1.0
#	## GAS ##
#        for DOF in ['BF','F1','F0']:
#            ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 10.0
#            ezca['VIS-'+optic+'_%s_DAMP_GAS_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = 1.0
#	## IM ##
#	    for DOF in ['L','T','V','R','P','Y']:
#	        ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_IM_DAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_IM_DAMP_%s_GAIN'%DOF] = 1.0 # 2018-03-12 had lacked %DOF; added, Mark B.
#	return True


#class DAMPING_OFF(GuardState):
#    index = 52
#    request = False
#    @watchdog_check
#    def main(self):
#	log('Turning off the damping filters')
#	vf.im_damp_off(optic)
#	vf.gas_damp_off(optic)
#	vf.ip_damp_off(optic)
#	time.sleep(10) # FIXME - use proper timer
#	return True

#class DAMPED(GuardState):
#    index = 60
#    @watchdog_check
#    def main(self):
#        log(optic+"damped")
#        self.timer['ochitsuke'] = ochitsuke_sec 

#    @watchdog_check
#    def run(self):
#        if self.timer['ochitsuke']:
#            return True  


#class ENGAGE_OLDAMP(GuardState):
#    index = 900
#    request = False
#    @watchdog_check
#    def main(self):
#        log('Turning on the oplev controls')
#        ## IM ##
#        for DOF in ['P','Y']:
#            ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = 3.0
#            ezca['VIS-'+optic+'_IM_OLDAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = 1.0
#        ## TM ##
#        for DOF in ['L','P','Y']:
#            ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = 3.0
#            ezca['VIS-'+optic+'_TM_DAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = 1.0
#        for DOF in ['PIT','YAW']:
#            ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_GAIN'%DOF] = 1.0
#        self.timer['ochitsuke'] = ochitsuke_sec

#    @watchdog_check
#    def run(self):
#        if self.timer['ochitsuke']:
#            return True

#class OLDAMP_OFF(GuardState):
#    index = 54
#    request = False
#    @watchdog_check
#    def main(self):
#        log('Turning off the oplev controls')
#       	vf.tm_damp_off(optic)
#     	vf.im_oldamp_off(optic)
#        time.sleep(10)
#	return True

#class ALIGNED(GuardState):
#    index = 1000
#    @watchdog_check
#    #    def run(self):
#    #	# Add DC alignment values with ramp time!
#    #^^^2019-02-15 Commented and replaced with def main(self): below .terrence
#    #        return True
#    def main(self):
#        for DOF in ['P','Y']:
#            ezca['VIS-'+optic+'_IM_OPTICALIGN_%s_TRAMP'%DOF] = 30
#            ezca['VIS-'+optic+'_IM_OPTICALIGN_%s_GAIN'%DOF] = 1.0


##################################################
# Edges

#edges = [
#    ('INIT','SAFE'),
#    ('RESET', 'SAFE'),
#    ('TRIPPED','SAFE'),
#    ('SAFE','OUTPUT_ON'),
#    ('OUTPUT_ON','UNDAMPED'),
#    ('UNDAMPED','DAMPING_ON'),
#    ('DAMPING_ON','DAMPED'),
#    ('DAMPED','DAMPING_OFF'),
#    ('DAMPING_OFF','UNDAMPED'),
#    ('DAMPED','ENGAGE_OLDAMP'),
#    ('ENGAGE_OLDAMP','ALIGNED'),
#    ('ALIGNED','OLDAMP_OFF'),
#    ('OLDAMP_OFF','DAMPED'),
#    ('UNDAMPED','SAFE')
#   ]
