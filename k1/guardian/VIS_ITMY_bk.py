'''
ITMY guardian

Wrote by K. Miyo
'''
import subprocess
import sys

from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager

sys.path.append('/opt/rtcds/userapps/release/vis/common/guardian/')
import typea_lib as lib

target = '/opt/rtcds/kamioka/k1/target/' # read me from os.environ
userapps = '/opt/rtcds/userapps/release/' # read me from os.environ

optic = 'ITMY'
sus = 'itmy'

#reqfile = target + 'k1vis{sus}/k1vis{sus}epics/autoBurt.req'.fomrat(sus='itmy')
#snapfile = release + 'vis/k1/burtfiles/k1vis{sus}_guardian_safe.snap'.fomrat(sus='itmy')

# hogeeeeeeeeeeeeeeeeeeeeeeeeeee
ip_damp_gains = { 'L':0.0,
                  'T':0.0,
                  'Y':0.0}
bf_damp_gains = { 'L':0.0,
                  'T':0.0,
                  'V':0.0,
                  'R':0.0,
                  'P':0.0,
                  'Y':1.0}
mn_damp_gains = { 'L':0.0,
                  'T':0.0,
                  'V':0.0,
                  'R':0.0,
                  'P':0.0,
                  'Y':0.0}
im_damp_gains = { 'L':0.0,
                  'T':0.0,
                  'V':0.0,
                  'R':0.0,
                  'P':0.0,
                  'Y':0.0}
mnoplev_damp_gains = { 'P':0.0,
                       'Y':1.0}
TMoplev_MN_gains = { 'P':1.0,
                     'Y':1.0,
                     'L':0.0}
TMoplev_IM_gains = { 'P':0.0,
                     'Y':0.0,
                     'L':0.0}
tmoplev_damp_gains = { 'P':0.0,
                       'Y':0.0,
                       'L':0.0}
# hogeeeeeeeeeeeeeeeeeeeeeeeeeeee


request = 'SAFE'
nominal = 'ALIGNED'

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
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF' # should be "lib.masterswitch_off(self,optic)"
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
        lib.mn_mnoldamp_off(self,optic)
        return True
    def run(self):
        if lib.is_oplev_inrange(optic):
            return True

        
class RESET(GuardState):
    index = 20
    goto = True
    request = False
    def main(self):
        log('Turning off the master switch')
        lib.all_off(self,optic)
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
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
        # subprocess.call(['burtrb', '-f', reqfile, '-o', snapfile, '-l','/tmp/controls.read.log', '-v'])
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

    
class TOWER_DAMPING_ON(GuardState):
    index = 52
    request = False
    @watchdog_check
    def main(self):
        log('Turning on the TOWER damping filters')
	## IP ## (all the gains should be 1)
        for DOF in ['L','T','Y']:
        #     avgsec = 2 # averaging time
                  
        #     self.timer['averaging'] = avgsec
        #     ii = 0
        #     ofsavg = 0.0
        #     while not (self.timer['averaging']):
        #         ofsavg += ezca['VIS-'+optic+'_IP_DAMP_%s_INMON'%DOF]
        #         ii += 1
        #         log('Averaging IP dmping input')
        #     ofsavg/=ii
            ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF] = 20.0
            ezca['VIS-'+optic+'_IP_DAMP_%s_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_IP_DAMP_%s_OFFSET'%DOF] = -ofsavg
        #     ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = ip_damp_gains['%s'%DOF]
            ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = 1.0
        #     lib.wait(self,ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF])
	# ## GAS ## (zero gains for now)
        # for DOF in ['BF','F3','F2','F1','F0']:
        #     ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 5.0
        #     ezca['VIS-'+optic+'_%s_DAMP_GAS_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = 0.0
	# ## BF ## (gains are decleared in bf_damp_gains individually)
        # for DOF in ['L','T','V','R','P','Y']:
        # for DOF in ['L','T','V','R','P','Y']:
        #     ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = 5.0
        #     ezca['VIS-'+optic+'_BF_DAMP_%s_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_BF_DAMP_%s_GAIN'%DOF] = bf_damp_gains['%s'%DOF]
        #     if bf_damp_gains['%s'%DOF]!=0.0:
        #         lib.wait(self,ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF])                
	# ## MN ## 
        #     ezca['VIS-'+optic+'_MN_DAMP_%s_TRAMP'%DOF] = 5.0
        #     ezca['VIS-'+optic+'_MN_DAMP_%s_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_MN_DAMP_%s_GAIN'%DOF] = mn_damp_gains['%s'%DOF]
        #     if mn_damp_gains['%s'%DOF]!=0.0:
        #         lib.wait(self,ezca['VIS-'+optic+'_MN_DAMP_%s_TRAMP'%DOF])
	# ## IM ##
        #     ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF] = 5.0
        #     ezca['VIS-'+optic+'_IM_DAMP_%s_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_IM_DAMP_%s_GAIN'%DOF] = im_damp_gains['%s'%DOF]
        #     if im_damp_gains['%s'%DOF]!=0.0:
        #         lib.wait(self,ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF])                
        # ## MNOL ##
        # for DOF in ['P','Y']:
        #     ezca['VIS-'+optic+'_MN_OLDAMP_%s_TRAMP'%DOF] = 5.0
        #     ezca['VIS-'+optic+'_MN_OLDAMP_%s_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_MN_OLDAMP_%s_GAIN'%DOF] = mnoplev_damp_gains['%s'%DOF]
        #     if mnoplev_damp_gains['%s'%DOF]!=0.0:
        #         lib.wait(self,ezca['VIS-'+optic+'_MN_OLDAMP_%s_TRAMP'%DOF])                
	return True


class TOWER_DAMPED(GuardState):
    index = 51
    @watchdog_check
    def run(self):
        return True
    
class DISABLE_TOWER_DAMPING(GuardState):
    index = 53
    request = False

    @watchdog_check
    def main(self):
        log('Turning off the TOWER damping filters')
        # lib.im_damp_off(self,optic)
        # lib.mn_damp_off(self,optic)
        # lib.bf_damp_off(self,optic)
        # lib.gas_damp_off(self,optic)
        lib.ip_damp_off(self,optic)
	return True
    




#class PAYLOAD_DAMPING_ON(GuardState):
#    index = 61
#    request = False
#    @watchdog_check
#    def main(self):
#        log('Turning on the PAYLOAD damping filters')               
	# ## MN ## 
        #     ezca['VIS-'+optic+'_MN_DAMP_%s_TRAMP'%DOF] = 5.0
        #     ezca['VIS-'+optic+'_MN_DAMP_%s_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_MN_DAMP_%s_GAIN'%DOF] = mn_damp_gains['%s'%DOF]
        #     if mn_damp_gains['%s'%DOF]!=0.0:
        #         lib.wait(self,ezca['VIS-'+optic+'_MN_DAMP_%s_TRAMP'%DOF])
	# ## IM ##
        #     ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF] = 5.0
        #     ezca['VIS-'+optic+'_IM_DAMP_%s_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_IM_DAMP_%s_GAIN'%DOF] = im_damp_gains['%s'%DOF]
        #     if im_damp_gains['%s'%DOF]!=0.0:
        #         lib.wait(self,ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF])                
        # ## MNOL ##
        # for DOF in ['P','Y']:
        #     ezca['VIS-'+optic+'_MN_OLDAMP_%s_TRAMP'%DOF] = 5.0
        #     ezca['VIS-'+optic+'_MN_OLDAMP_%s_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_MN_OLDAMP_%s_GAIN'%DOF] = mnoplev_damp_gains['%s'%DOF]
        #     if mnoplev_damp_gains['%s'%DOF]!=0.0:
        #         lib.wait(self,ezca['VIS-'+optic+'_MN_OLDAMP_%s_TRAMP'%DOF])                
#	return True

#class DISABLE_PAYLOAD_DAMPING(GuardState):
#    index = 62
#    request = False

#    @watchdog_check
#    def main(self):
#        log('Turning off the TOWER damping filters')
        # lib.im_damp_off(self,optic)
        # lib.mn_damp_off(self,optic)
        # lib.bf_damp_off(self,optic)
        # lib.gas_damp_off(self,optic)
#        lib.ip_damp_off(self,optic)
#	return True

#class PAYLOAD_DAMPED(GuardState):
#    index = 63
#    @watchdog_check
#    def main(self):
#        log(optic+"PAYLOAD damped")
#        return True
#    @watchdog_check
#    def run(self):
#        return True  


#class INERTIAL_DAMPING_ON(GuardState):
#    index = 70
#    request = False
#    @watchdog_check
#    def main(self):
#        log('Turning on the damping filters')
	## IP ## (all the gains should be 1)
        # for DOF in ['L','T','Y']:
        #     avgsec = 2 # averaging time
                  
        #     self.timer['averaging'] = avgsec
        #     ii = 0
        #     ofsavg = 0.0
        #     while not (self.timer['averaging']):
        #         ofsavg += ezca['VIS-'+optic+'_IP_DAMP_%s_INMON'%DOF]
        #         ii += 1
        #         log('Averaging IP dmping input')
        #     ofsavg/=ii
        #     ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF] = 20.0
        #     ezca['VIS-'+optic+'_IP_DAMP_%s_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_IP_DAMP_%s_OFFSET'%DOF] = -ofsavg
        #     ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = ip_damp_gains['%s'%DOF]
        #    ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = 1.0
        #     lib.wait(self,ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF])    
#	return True

#class DISABLE_INERTIAL_DAMPING(GuardState):
#    index = 75
#    request = False

#    @watchdog_check
#    def main(self):
#        log('Turning off the damping filters')
        # lib.im_damp_off(self,optic)
        # lib.mn_damp_off(self,optic)
        # lib.bf_damp_off(self,optic)
        # lib.gas_damp_off(self,optic)
#        lib.ip_damp_off(self,optic)
#	return True

#class INERTIALLY_DAMPED(GuardState):
#   index = 80
#    @watchdog_check
#    def main(self):
#        log(optic+"inertially damped")
#        return True
#    @watchdog_check
#    def run(self):
#        return True  

    
class ENGAGE_DCCONTROL(GuardState):
    index = 900
    request = False
    @watchdog_check
    @oplev_check
    def main(self):
        log('Turning on the oplev controls')
	# ## MN ##
        # for DOF in ['L','P','Y']:
        #     ezca['VIS-'+optic+'_MN_OLDAMP1_%s_TRAMP'%DOF] = 5.0
        #     ezca['VIS-'+optic+'_MN_OLDAMP1_%s_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_MN_OLDAMP1_%s_GAIN'%DOF] = TMoplev_MN_gains['%s'%DOF]
        #     if TMoplev_MN_gains['%s'%DOF]!=0.0:
        #         lib.wait(self,ezca['VIS-'+optic+'_MN_OLDAMP1_%s_TRAMP'%DOF])
	# ## IM ##
        #     ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = 5.0
        #     ezca['VIS-'+optic+'_IM_OLDAMP_%s_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = TMoplev_IM_gains['%s'%DOF]
        #     if TMoplev_IM_gains['%s'%DOF]!=0.0:
        #         lib.wait(self,ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF])
	# ## TM ##
        #     ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = 5.0
        #     ezca['VIS-'+optic+'_TM_DAMP_%s_RSET'%DOF] = 2
        #     ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = tmoplev_damp_gains['%s'%DOF]
        #     if tmoplev_damp_gains['%s'%DOF]!=0.0:
        #         lib.wait(self,ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF])
        return True

    
class DISABLE_DCCONTROL(GuardState):
    index = 100
    request = False

    @watchdog_check
    def main(self):
        log('Turning off the oplev controls')
        # lib.tm_damp_off(self,optic)
        # lib.im_oldamp_off(self,optic)
        # lib.mn_oldamp_off(self,optic)
        # lib.mn_mnoldamp_off(self,optic)
	return True

    
class ALIGNED(GuardState):
    index = 200
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
    ('UNDAMPED','TOWER_DAMPING_ON'),
    ('TOWER_DAMPING_ON','TOWER_DAMPED'),
    ('TOWER_DAMPED','DISABLE_TOWER_DAMPING'),
    ('DISABLE_TOWER_DAMPING','UNDAMPED'),

#    ('TOWER_DAMPED','PAYLOAD_DAMPING_ON'),
#    ('PAYLOAD_DAMPING_ON','PAYLOAD_DAMPED'),
#    ('PAYLOAD_DAMPED','DISABLE_PAYLOAD_DAMPING'),
#    ('DISABLE_PAYLOAD_DAMPING','TOWER_DAMPED'),
#    ('TOWER_DAMPED','INERTIAL_DAMPING_ON'),
#    ('INERTIAL_DAMPING_ON','INERTIALLY_DAMPED'),
#    ('INERTIALLY_DAMPED','DISABLE_INERTIAL_DAMPING'),
#    ('DISABLE_INERTIAL_DAMPING','TOWER_DAMPED'),

    ('TOWER_DAMPED','ENGAGE_DCCONTROL'),
    ('ENGAGE_DCCONTROL','ALIGNED'),
    ('ALIGNED','DISABLE_DCCONTROL'),
    ('DISABLE_DCCONTROL','TOWER_DAMPED'),
    ('UNDAMPED','SAFE'),
    ('OPLEV_OUTOFRANGE','TOWER_DAMPED')
   ]
