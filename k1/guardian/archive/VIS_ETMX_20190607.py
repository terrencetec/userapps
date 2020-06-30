############################################
# ETMX gardian
#
# renewed on 2018.Mar.6th by KI
# modified on 2018.Apr.21st by MN (not marionette)
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

# initial REQUEST state
request = 'SAFE'

# NOMINAL state, which determines when node is OK
nominal = 'ALIGNED'

# IP gain setting
IPgains = { 'L':0.0,
            'T':0.0,
            'Y':0.0}

# BF gain setting
BFgains = { 'L':0.0,
            'T':0.0,
            'V':0.0,
            'R':0.0,
            'P':0.0,
            'Y':1.0}

# MN gain setting
MNgains = { 'L':1.0,
            'T':1.0,
            'V':0.0,
            'R':0.0,
            'P':0.0,
            'Y':1.0}


# IM gain setting
IMgains = { 'L':0.0,
            'T':0.0,
            'V':0.0,
            'R':0.0,
            'P':0.0,
            'Y':0.0}
# MN gain setting for MN oplev loop 
MNoplev_gains = { 'P':0.0,
                  'Y':0.0}
# BF gain setting for TM oplev loop 
TMoplev_BF_gains = { 'P':0.0,
                     'Y':0.0,
                     'L':0.0}
# MN gain setting for TM oplev loop 
TMoplev_MN_gains = { 'P':0.0,
                     'Y':1.0,
                     'L':0.0}

# IM gain setting for TM oplev loop 
TMoplev_IM_gains = { 'P':0.0,
                     'Y':0.0,
                     'L':0.0}

# TM oplev gain setting
TMoplev_gains = { 'P':0.0,
                  'Y':0.0,
                  'L':0.0}
reqfile = '/opt/rtcds/kamioka/k1/target/k1visey/k1viseyepics/autoBurt.req'
snapfile = '/opt/rtcds/userapps/release/vis/k1/burtfiles/k1visey_guardian_safe.snap'
##################################################
# STATE decorators

class watchdog_check(GuardStateDecorator):
    """Decorator to check watchdog"""
    def pre_exec(self):
        if lib.is_tripped(optic):
            log("I_am_tripped.")
            return 'TRIPPED'

class oplev_check(GuardStateDecorator):
    """Decorator to check oplev"""
    def pre_exc(self):
        if not lib.is_oplev_inrange(optic):
            log('Some optical lever is out of range')
            return 'OPLEV_OUTOFRANGE'

        
##################################################
class INIT(GuardState):
    index = 0
    goto = True
    

class TRIPPED(GuardState):
    index = 1
    redirect = False
    request = False
    def main(self):
        lib.all_off(self,optic)
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
        notify("please restart WatchDog!")
        return True
    def run(self):
        if not lib.is_tripped(optic):
            return True

class OPLEV_OUTOFRANGE(GuardState):
    index = 2
    redirect = False
    request = False
    @watchdog_check
    def main(self):
        log('Oplev is out of range. Turning off the oplev controls')
        lib.tm_damp_off(self,optic)
        lib.im_oldamp_off(self,optic)
        lib.mn_oldamp_off(self,optic)
        lib.bf_oldamp_off(self,optic)
            
        lib.mn_mnoldamp_off(self,optic)
        return True
#    def run(self):
#        if lib.is_oplev_inrange(optic):
#            return True

        
class RESET(GuardState):
    index = 20
    goto = True
    request = False
    def main(self):
        #log('Turning off the master switch')
        #lib.all_off(self,optic)
        #ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
        return True

class SAFE(GuardState):
    """Safe state is with master switch off not to send any signal"""
    index = 30
    @watchdog_check
    def main(self):
        log('Start to turn all damping off')
        lib.all_off(self,optic)
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
        lib.wait(self,5)

        ## Optic Align
        for DOF in ['P','Y']:
            ezca['VIS-'+optic+'_MN_OPTICALIGN_%s_TRAMP'%DOF] = 10.0
            ezca.switch('VIS-'+optic+'_MN_OPTICALIGN_%s'%DOF,'OFFSET','ON')
        lib.wait(self,ezca['VIS-'+optic+'_MN_OPTICALIGN_Y_TRAMP'])
	return True

class UNDAMPED(GuardState):
    index = 50
    @watchdog_check
    def run(self):
        return True


#class STRANGE_IPOFFSET(GuardState):
#    index = 54
#    request = False
#    @watchdog_check
#    def run(self):
#        if lib.check_IPdamp_OFFSET(optic,n,threshold):
#            return True

    
class ENGAGE_DAMPING(GuardState):
    index = 52
    request = False
    @watchdog_check
    def main(self):
        log('Turning on the damping filters')
	## IP ## (all the gains should be 1)
        for DOF in ['L','T','Y']:
            avgsec = 2 # averaging time
                  
            self.timer['averaging'] = avgsec
            ii = 0
            ofsavg = 0.0
            while not (self.timer['averaging']):
                ofsavg += ezca['VIS-'+optic+'_IP_DAMP_%s_INMON'%DOF]
                ii += 1
                log('Averaging IP dmping input')
            ofsavg/=ii
   
            ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IP_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = IPgains['%s'%DOF]
            ezca['VIS-'+optic+'_IP_DAMP_%s_OFFSET'%DOF] = -ofsavg
            lib.wait(self,ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF])
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
            if BFgains['%s'%DOF]!=0.0:
                lib.wait(self,ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF])
                
	## MN ## 
            ezca['VIS-'+optic+'_MN_DAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_MN_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_MN_DAMP_%s_GAIN'%DOF] = MNgains['%s'%DOF]
            if MNgains['%s'%DOF]!=0.0:
                lib.wait(self,ezca['VIS-'+optic+'_MN_DAMP_%s_TRAMP'%DOF])
	## IM ##
            ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IM_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_IM_DAMP_%s_GAIN'%DOF] = IMgains['%s'%DOF]
            if IMgains['%s'%DOF]!=0.0:
                lib.wait(self,ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF])
                
        ## MNOL ##
        for DOF in ['P','Y']:
            ezca['VIS-'+optic+'_MN_OLDAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_MN_OLDAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_MN_OLDAMP_%s_GAIN'%DOF] = MNoplev_gains['%s'%DOF]
            if MNoplev_gains['%s'%DOF]!=0.0:
                lib.wait(self,ezca['VIS-'+optic+'_MN_OLDAMP_%s_TRAMP'%DOF])
                
	return True

class DISABLE_DAMPING(GuardState):
    index = 53
    request = False

    @watchdog_check
    def main(self):
        log('Turning off the damping filters')
        lib.im_damp_off(self,optic)
        lib.mn_damp_off(self,optic)
        lib.bf_damp_off(self,optic)
        lib.gas_damp_off(self,optic)
        lib.ip_damp_off(self,optic)
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

class ENGAGE_DCCONTROL(GuardState):
    index = 900
    request = False
    @watchdog_check
    @oplev_check
    def main(self):
        log('Turning on the oplev controls')

        ## BF ##
        for DOF in ['L','P','Y']:
            ezca['VIS-'+optic+'_BF_OLDAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_BF_OLDAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_BF_OLDAMP_%s_GAIN'%DOF] = TMoplev_BF_gains['%s'%DOF]
            if TMoplev_BF_gains['%s'%DOF]!=0.0:
                lib.wait(self,ezca['VIS-'+optic+'_BF_OLDAMP_%s_TRAMP'%DOF])
	## MN ##
        for DOF in ['L','P','Y']:
            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_GAIN'%DOF] = TMoplev_MN_gains['%s'%DOF]
            if TMoplev_MN_gains['%s'%DOF]!=0.0:
                lib.wait(self,ezca['VIS-'+optic+'_MN_OLDAMP1_%s_TRAMP'%DOF])
	## IM ##
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = TMoplev_IM_gains['%s'%DOF]
            if TMoplev_IM_gains['%s'%DOF]!=0.0:
                lib.wait(self,ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF])
	## TM ##
            ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = 5.0
            ezca['VIS-'+optic+'_TM_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = TMoplev_gains['%s'%DOF]
            if TMoplev_gains['%s'%DOF]!=0.0:
                lib.wait(self,ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF])
        return True

class DISABLE_DCCONTROL(GuardState):
    index = 54
    request = False

    @watchdog_check
    def main(self):
        log('Turning off the oplev controls')
        lib.tm_damp_off(self,optic)
        lib.im_oldamp_off(self,optic)
        lib.mn_oldamp_off(self,optic)
        lib.mn_mnoldamp_off(self,optic)
        lib.bf_oldamp_off(self,optic)
	return True

class ALIGNED(GuardState):
    index = 100
    @watchdog_check
    @oplev_check
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
    ('UNDAMPED','ENGAGE_DAMPING'),
    ('ENGAGE_DAMPING','DAMPED'),
    ('DAMPED','DISABLE_DAMPING'),
    ('DISABLE_DAMPING','UNDAMPED'),
    ('DAMPED','ENGAGE_DCCONTROL'),
    ('ENGAGE_DCCONTROL','ALIGNED'),
    ('ALIGNED','DISABLE_DCCONTROL'),
    ('DISABLE_DCCONTROL','DAMPED'),
    ('UNDAMPED','SAFE'),
    ('OPLEV_OUTOFRANGE','DAMPED')
   ]
