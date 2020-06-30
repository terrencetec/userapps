import time
import math
from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import os
import sendAlert as sa
import VISfunction as vf

##################################################
# initialization values

# initial REQUEST state
request = 'ALIGNED'

# NOMINAL state, which determines when node is OK
nominal = 'ALIGNED'

##################################################

optic = 'SR2'
WD = ['TM','IM','BF','F1','F0','IP']
BIO = ['TM','IM1','IM2','GAS','IP']
ochitsuke_sec = 20 # waiting time to stay at DAMPED in seconds
# Tool for taking safe snapshot
reqfile = vf.req_file_path(optic)+'/autoBurt.req'
snapfile = '/opt/rtcds/userapps/release/vis/k1/burtfiles/'+vf.modelName(optic)+'_guardian_safe.snap'
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
        vf.all_off(optic)
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
        notify("please reset WatchDog!")
        sa.vis_watchdog_tripped(optic)

    def run(self):
        notify("please reset WatchDog!")
        if not vf.is_tripped(optic,WD,BIO):
            return True

class RESET(GuardState):
    index = 20
    goto = True
    request = False
    def main(self):
        log('Turning off the master switch')
        vf.all_off(optic)
        time.sleep(10)
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
        return True

class SAFE(GuardState):
    """Safe state is with master switch off so as not to send any signal"""
    index = 30
    @watchdog_check
    def main(self):
        log('Turning off all the filters')
        vf.all_off(optic)
        time.sleep(10)
        log('Turning off the master switch')
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
        return True

class OUTPUT_ON(GuardState):
    index = 41
    request = False

    @watchdog_check
    def main(self):
        log('Turning on the master switch')
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'ON'
	log('Turning on the TEST filters')
	## IP ##
        for DOF in ['L','T','Y']:
	    ezca['VIS-'+optic+'_IP_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IP_TEST_%s_GAIN'%DOF] = 1.0
	## GAS ##
        for DOF in ['BF','F1','F0']:
            ezca['VIS-'+optic+'_%s_TEST_GAS_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_%s_TEST_GAS_GAIN'%DOF] = 1.0
	## IM ##
        for DOF in ['L','T','V','R','P','Y']:
            ezca['VIS-'+optic+'_IM_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IM_TEST_%s_GAIN'%DOF] = 1.0
        for DOF in ['P','Y']:
            ezca['VIS-'+optic+'_IM_OPTICALIGN_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IM_OPTICALIGN_%s_GAIN'%DOF] = 1.0
        ## TM ##
        for DOF in ['L','P','Y']:
	    ezca['VIS-'+optic+'_TM_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_TM_TEST_%s_GAIN'%DOF] = 1.0
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
	## IP ##
        for DOF in ['L','T','Y']:
	    ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_IP_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = 1.0
	## GAS ##
        for DOF in ['BF','F1','F0']:
            ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_%s_DAMP_GAS_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = 1.0
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
	log('Turning off the damping filters')
	vf.im_damp_off(optic)
	vf.gas_damp_off(optic)
	vf.ip_damp_off(optic)
	time.sleep(10) # FIXME - use proper timer
	return True

class DAMPED(GuardState):
    index = 60
    @watchdog_check
    def main(self):
        log(optic+"damped")
        self.timer['ochitsuke'] = ochitsuke_sec 

    @watchdog_check
    def run(self):
        if self.timer['ochitsuke']:
            return True  


class ENGAGE_OLDAMP(GuardState):
    index = 900
    request = False
    @watchdog_check
    def main(self):
        log('Turning on the oplev controls')
        ## IM ##
        for DOF in ['P','Y']:
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = 3.0
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = 1.0
        ## TM ##
        for DOF in ['L','P','Y']:
            ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = 3.0
            ezca['VIS-'+optic+'_TM_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = 1.0
        for DOF in ['PIT','YAW']:
            ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_GAIN'%DOF] = 1.0
        self.timer['ochitsuke'] = ochitsuke_sec

    @watchdog_check
    def run(self):
        if self.timer['ochitsuke']:
            return True

class OLDAMP_OFF(GuardState):
    index = 54
    request = False
    @watchdog_check
    def main(self):
	log('Turning off the oplev controls')
   	vf.tm_damp_off(optic)
 	vf.im_oldamp_off(optic)
    	time.sleep(10)
	return True

class ALIGNED(GuardState):
    index = 1000
    @watchdog_check
    def run(self):
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
