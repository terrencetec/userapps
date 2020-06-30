############################################
# ETMX gardian
#
# renewed on 2018.Mar.6th by KI
############################################
from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import time, subprocess, sys

# importing a set of useful functions.
sys.path.append('/opt/rtcds/userapps/release/vis/common/guardian/')
import typea_lib as lib

##################################################
# Tool for taking safe snapshot
optic = 'ETMX'

# BF gain setting
BFgains = { 'L':0.0,
            'T':0.0,
            'V':0.0,
            'R':0.0,
            'P':0.0,
            'Y':1.0}

# MN gain setting
MNgains = { 'L':0.0,
            'T':0.0,
            'V':0.0,
            'R':0.0,
            'P':0.0,
            'Y':0.0}

reqfile = '/opt/rtcds/kamioka/k1/target/k1visex/k1visexepics/autoBurt.req'
snapfile = '/opt/rtcds/userapps/release/vis/k1/burtfiles/k1visex_guardian_safe.snap'
##################################################
# STATE decorators

class watchdog_check(GuardStateDecorator):
    """Decorator to check watchdog"""
    def pre_exec(self):
        if lib.is_tripped(optic):
            log("I_am_tripped.")
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
        lib.all_off(optic)
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
        notify("please restart WatchDog!")
        return True
    def run(self):
        if not lib.is_tripped(optic):
            return True
    
class RESET(GuardState):
    index = 20
    goto = True
    request = False
    def main(self):
        log('Turning off ethe master switch')
        lib.all_off(optic)
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
        return True

class SAFE(GuardState):
    """Safe state is with master switch off not to send any signal"""
    index = 30
    @watchdog_check
    def main(self):
        log('Turning off the master switch')
        lib.test_off(optic)
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
	## IP ##
        for DOF in ['L','T','Y']:
            ezca['VIS-'+optic+'_IP_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IP_TEST_%s_GAIN'%DOF] = 1.0
	## GAS ##
        for DOF in ['BF','F3','F2','F1','F0']:
            ezca['VIS-'+optic+'_%s_TEST_GAS_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_%s_TEST_GAS_GAIN'%DOF] = 1.0
	## BF, MN and IM##
        for DOF in ['L','T','V','R','P','Y']:
            ezca['VIS-'+optic+'_BF_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_BF_TEST_%s_GAIN'%DOF] = 1.0

            ezca['VIS-'+optic+'_MN_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_MN_TEST_%s_GAIN'%DOF] = 1.0

            ezca['VIS-'+optic+'_IM_TEST_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IM_TEST_%s_GAIN'%DOF] = 1.0
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
	## IP ## (all the gains should be 1)
        for DOF in ['L','T','Y']:
            ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IP_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = 1.0
	## GAS ## (zero gains for now)
        for DOF in ['BF','F3','F2','F1','F0']:
            ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_%s_DAMP_GAS_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = 0.0
	## BF ## (gains are decleared in BFgains individually)
        for DOF in ['L','T','V','R','P','Y']:
            ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_BF_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_BF_DAMP_%s_GAIN'%DOF] = BFgains['%s'%DOF]
	## MN ## 
            ezca['VIS-'+optic+'_MN_DAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_MN_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_MN_DAMP_%s_GAIN'%DOF] = MNgains['%s'%DOF]
	## IM ##
            ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IM_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_IM_DAMP_%s_GAIN'%DOF] = 0.0
	return True

class DAMPING_OFF(GuardState):
    index = 52
    request = False

    @watchdog_check
    def main(self):
        log('Turning on the damping filters')
        lib.im_damp_off(optic)
        lib.mn_damp_off(optic)
        lib.bf_damp_off(optic)
        lib.gas_damp_off(optic)
        lib.ip_damp_off(optic)
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

class ENGAGE_OLDAMP(GuardState):
    index = 900
    request = False
    @watchdog_check
    def main(self):
        log('Turning on the oplev controls')
	## MNOL ##
        for DOF in ['P','Y']:
            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_GAIN'%DOF] = 1.0
	## MN ##
        for DOF in ['L','P','Y']:
            ezca['VIS-'+optic+'_MN_OLDAMP_%s_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_MN_OLDAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_MN_OLDAMP_%s_GAIN'%DOF] = 1.0
	## IM ##
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = 1.0
	## TM ##
            ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = 10.0
            ezca['VIS-'+optic+'_TM_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = 1.0
        return True

class OLDAMP_OFF(GuardState):
    index = 54
    request = False

    @watchdog_check
    def main(self):
        log('Turning off the oplev controls')
        lib.tm_damp_off(optic)
        lib.im_oldamp_off(optic)
        lib.mn_oldamp_off(optic)
    	time.sleep(10)
        lib.mn_mnoldamp_off(optic)
    	time.sleep(10)
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
