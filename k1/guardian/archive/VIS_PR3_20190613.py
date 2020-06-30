##################################################
#modified by m.nakano on 2017/11/03

import time
import math
from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import os
import sys
import subprocess
import sendAlert as sa
import VISfunction as vf

##################################################
# initialization values


# initial REQUEST state
request = 'ALIGNED'

# NOMINAL state, which determines when node is OK
nominal = 'ALIGNED'

##################################################

##################################################

optic = 'PR3'
WD = ['TM','IM','BF','SF']
BIO = ['TM','IM1','IM2','GAS','BFV','BFH']


# Tool for taking safe snapshot
"""
userapps = '/opt/rtcds/userapps/release/'
IFO = os.getenv('IFO')
ifo = IFO.lower()
SITE = os.getenv('SITE')
site = SITE.lower()
dorw = 2
verbose=False

def vf.modelName(optic):
    return ifo+'vis'+optic

def vf.req_file_path(optic):
    return os.path.join('/opt/rtcds',site,ifo,'target',vf.modelName(optic),vf.modelName(optic)+'epics')

def vf.snap_file_path(optic):
#    return os.path.join(userapps, 'vis', ifo, 'burtfiles') 
    return os.path.join(userapps, 'vis', ifo, 'guardian') # FIXME temporary only

#reqfile = vf.req_file_path(optic)
#snapfile = vf.snap_file_path(optic)
"""
reqfile = vf.req_file_path(optic)+'/autoBurt.req'
snapfile = '/opt/rtcds/userapps/release/vis/k1/burtfiles/'+vf.modelName(optic)+'_guardian_safe.snap'
"""
###################################################


# utility functions

def vf.is_tripped(optic,WD,BIO):
    if (ezca['VIS-'+optic+'_TM_WDMON_STATE'] != 1) or \
	(ezca['VIS-'+optic+'_IM_WDMON_STATE'] != 1) or \
	(ezca['VIS-'+optic+'_BF_WDMON_STATE'] != 1) or \
	(ezca['VIS-'+optic+'_SF_WDMON_STATE'] != 1): # if WatchDog is triped
        return True

    else:
        return False

def vf.is_pretripped(optic):
        if ezca['VIS-'+optic+'_IM_WD_OSEMAC_V1_RMSMON'] > 2000.0:
                return True
        elif ezca['VIS-'+optic+'_IM_WD_OSEMAC_V2_RMSMON'] > 2000.0:
                return True
        elif ezca['VIS-'+optic+'_IM_WD_OSEMAC_V3_RMSMON'] > 2000.0:
                return True
        elif ezca['VIS-'+optic+'_IM_WD_OSEMAC_H1_RMSMON'] > 2000.0:
                return True
        elif ezca['VIS-'+optic+'_IM_WD_OSEMAC_H2_RMSMON'] > 2000.0:
                return True
        elif ezca['VIS-'+optic+'_IM_WD_OSEMAC_H3_RMSMON'] > 2000.0:
                return True
        elif ezca['VIS-'+optic+'_BF_WD_AC_LVDT_V1_RMSMON'] > 100.0:
                return True
        elif ezca['VIS-'+optic+'_BF_WD_AC_LVDT_V2_RMSMON'] > 100.0:
                return True
        elif ezca['VIS-'+optic+'_BF_WD_AC_LVDT_V3_RMSMON'] > 100.0:
                return True
        elif ezca['VIS-'+optic+'_BF_WD_AC_LVDT_H1_RMSMON'] > 100.0:
                return True
        elif ezca['VIS-'+optic+'_BF_WD_AC_LVDT_H2_RMSMON'] > 100.0:
                return True
        elif ezca['VIS-'+optic+'_BF_WD_AC_LVDT_H3_RMSMON'] > 100.0:
                return True
        elif ezca['VIS-'+optic+'_SF_WD_AC_GAS_RMSMON'] > 100.0:
                return True
	else:
	        return False


def vf.tm_damp_off(optic):
    for DOF in ['L', 'P', 'Y']:
        ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = 10.0
        ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = 0
    #time.sleep(10) # FIXME! no sleeping command.
    
def vf.im_damp_off(optic):
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_IM_DAMP_%s_GAIN'%DOF] = 0

def vf.im_oldamp_off(optic):
    for DOF in ['P','Y']:
        ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = 10.0
        ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = 0


def vf.bf_damp_off(optic):
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_BF_DAMP_Y_TRAMP'] = 10.0
        ezca['VIS-'+optic+'_BF_DAMP_%s_GAIN'%DOF] = 0

def vf.gas_damp_off(optic):
    for DOF in ['BF','SF']:
        ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 10.0
        ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = 0


def vf.test_off(optic):
    for DOF in ['L', 'P', 'Y']:
        ezca['VIS-'+optic+'_TM_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_TM_TEST_%s_GAIN'%DOF] = 0
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_IM_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_IM_TEST_%s_GAIN'%DOF] = 0
    for DOF in ['L','T','V','R','P','Y']:
        ezca['VIS-'+optic+'_BF_TEST_%s_TRAMP'%DOF] = 5.0
        ezca['VIS-'+optic+'_BF_TEST_%s_GAIN'%DOF] = 0
    for DOF in ['BF','SF']:
        ezca['VIS-'+optic+'_%s_TEST_GAS_TRAMP'%DOF] = 10.0
        ezca['VIS-'+optic+'_%s_TEST_GAS_GAIN'%DOF] = 0

def vf.all_off(optic):
    vf.tm_damp_off(optic)
    vf.im_oldamp_off(optic)
    #time.sleep(10)
    vf.test_off(optic)
    vf.im_damp_off(optic)
    vf.bf_damp_off(optic)
    vf.gas_damp_off(optic)
    #time.sleep(10)
 """      
##################################################
# STATE decorators

class watchdog_check(GuardStateDecorator):
    """Decorator to check watchdog"""
    def pre_exec(self):
        if vf.is_tripped(optic,WD,BIO):
            log("I_am_tripped.")
            #sa.sendmail("["+optic+"]Tripped",optic+" is tripped!")
            return 'TRIPPED'

class pre_wd(GuardStateDecorator):
    def pre_exec(self):
        if vf.is_pretripped(optic):
            log("I_am_pre-tripped.")
            return 'PRE_TRIPPED'

##################################################
class INIT(GuardState):
    index = 0
    goto = True
    

class TRIPPED(GuardState):
    index = 1
    redirect = False
    request = False
    def main(self):
        vf.all_off(optic)
        rampT = ezca['VIS-'+optic+'_SHUTDOWN_RAMPT']
        self.timer['wait_for_ALLOFF'] = rampT
        while not (self.timer['wait_for_ALLOFF']):
            log('waiting for all outputs turned off')
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'

        #Send alerts
        #sa.vis_watchdog_tripped(optic)
        
    def run(self):
        if not vf.is_tripped(optic,WD,BIO):
            return True
    
#class PRE_TRIPPED(GuardState):
#    index = 10
#    redirect = False
#    request = False
#    @watchdog_check
#    def main(self):
#        vf.all_off(optic)
#        return True
#    
#    @watchdog_check
#    def run(self):
#        if not vf.is_pretripped(optic):
#            return True

class RESET(GuardState):
    index = 20
    request = False
    def main(self):
        log('Turning off the master switch')
        vf.all_off(optic)
        self.timer['wait_for_ALLOFF'] = 10
        while not (self.timer['wait_for_ALLOFF']):
            log('waiting for all outputs turned off')
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
        return True

class SAFE(GuardState):
    """Safe state is with master switch off not to send any signal"""
    index = 30
    @watchdog_check
    def main(self):
        log('Turning off all the filters')
        vf.all_off(optic)
        self.timer['wait_for_ALLOFF'] = 10
        while not (self.timer['wait_for_ALLOFF']):
            log('waiting for all outputs turned off')
        log('Turning off the master switch')
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
        subprocess.call(['burtrb', '-f', reqfile, '-o', snapfile, '-l','/tmp/controls.read.log', '-v'])
        return True
	

class OUTPUT_ON(GuardState):
    index = 41
    request = False

    @watchdog_check
    def main(self):
        log('Turning on the master switch')
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'ON'
	log('Turning on the TEST filters')
	## GAS ##
        for DOF in ['BF','SF']:
            ezca['VIS-'+optic+'_%s_TEST_GAS_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_%s_TEST_GAS_GAIN'%DOF] = 1.0
	## BF & IM ##
        for DOF in ['L','T','V','R','P','Y']:
            ezca['VIS-'+optic+'_BF_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_BF_TEST_%s_GAIN'%DOF] = 1.0

            ezca['VIS-'+optic+'_IM_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IM_TEST_%s_GAIN'%DOF] = 1.0
        ## TM ##
        for DOF in ['L','P','Y']:
	    ezca['VIS-'+optic+'_TM_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_TM_TEST_%s_GAIN'%DOF] = 1.0
        for DOF in ['P','Y']:
            ezca['VIS-'+optic+'_IM_OPTICALIGN_%s_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_IM_OPTICALIGN_%s_GAIN'%DOF] = 1.0
	return True


class UNDAMPED(GuardState):
    index = 50
    @watchdog_check
    def run(self):
        return True

class DAMPING_ON(GuardState):
    index = 51
    request = False
    @watchdog_check
    def main(self):
	log('Turning on the damping filters')
	## GAS ##
        for DOF in ['BF', 'SF']:                              # 2018-12-13 added out by Y. Fujii.
            ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_%s_DAMP_GAS_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = 1.0
	## BF ##
        for DOF in ['L','T','V','R','P','Y']:                
	    ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_BF_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_BF_DAMP_%s_GAIN'%DOF] = 1.0
	## IM ##
        for DOF in ['L','T','V','R','P','Y']:
	    ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IM_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_IM_DAMP_%s_GAIN'%DOF] = 1.0
	return True


class DAMPING_OFF(GuardState):
    index = 52
    request = False
    @watchdog_check
    def main(self):
	log('Turning on the damping filters')
	vf.im_damp_off(optic)
	vf.bf_damp_off(optic)
	vf.gas_damp_off(optic)
	time.sleep(10)
	return True

class DAMPED(GuardState):
    index = 60
    @watchdog_check
    def main(self):
        log(optic+"damped")
        return True
    @watchdog_check
    def run(self):
        return True  

#class MIS_ALIGN(GuardState):
#    index = 62
#    request = False
#    @watchdog_check
#    def main(self):
#        log("'+optic+' misaligned")
#        ezca['VIS-'+optic+'_IM_OPTICALIGN_P_TRAMP'] = 10.0
#        ezca['VIS-'+optic+'_IM_OPTICALIGN_Y_TRAMP'] = 10.0
#
#        ezca['VIS-'+optic+'_IM_OLDAMP_P_TRAMP'] = 10.0
#        ezca['VIS-'+optic+'_IM_OLDAMP_Y_TRAMP'] = 10.0
#        ezca['VIS-'+optic+'_IM_OPTICALIGN_P_GAIN'] = 0.0
#        ezca['VIS-'+optic+'_IM_OPTICALIGN_Y_GAIN'] = 0.0
#        ezca['VIS-'+optic+'_IM_OLDAMP_P_GAIN'] = 0.0
#        ezca['VIS-'+optic+'_IM_OLDAMP_Y_GAIN'] = 0.0
#        return True
        

class ENGAGE_OLDAMP(GuardState):
    index = 900
    request = False
    @watchdog_check
    def main(self):
	log('Turning on the oplev controls')
#----------- Modified by A. Shoda (2019/06/05) ----------#
        for DOF in ['PIT','YAW']:
            Target = ezca['VIS-'+optic+'_GOOD_OPLEV_%s'%DOF]
            ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_OFFSET'%DOF] = -1.0*Target
            ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_TRAMP'%DOF] = 3.0
            ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_GAIN'%DOF] = 1.0
        ## TM ##
        for DOF in ['P','Y']:
            ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_TM_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = 1.0
        ## IM ##
        for DOF in ['P','Y']:
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = 1.0
        #self.timer['wait_for_boost'] = 3
        self.timer['wait_for_OLLOOP'] = 10
        while not (self.timer['wait_for_OLLOOP']):
            log('waiting for engaging OL LOOP')
        return True
#------------------------------------------------------#

class OLDAMP_OFF(GuardState):
    index = 54
    request = False
    @watchdog_check
    def main(self):
	log('Turning off the oplev controls')
   	vf.tm_damp_off(optic)
 	vf.im_oldamp_off(optic)
        self.timer['wait_for_OLLOOP_OFF'] = 10
	return True


class ALIGNED(GuardState):
    index = 1000
    @watchdog_check
    def run(self):
	log('All controlled')
	# Add DC alignment values with ramp time!
        return True


##################################################
# Edges

edges = [
    ('INIT','SAFE'),
    ('RESET', 'SAFE'),
    ('TRIPPED','SAFE'),
    ('SAFE','OUTPUT_ON'),
    ('OUTPUT_ON','UNDAMPED'),
    ('UNDAMPED','DAMPING_ON'),
    ('DAMPING_ON','DAMPED'),
    ('DAMPED','DAMPING_OFF'),
    ('DAMPING_OFF','UNDAMPED'),
    ('DAMPED','ENGAGE_OLDAMP'),
    ('ENGAGE_OLDAMP','ALIGNED'),
    ('ALIGNED','OLDAMP_OFF'),
    ('OLDAMP_OFF','DAMPED'),
    ('UNDAMPED','SAFE')
   ]
