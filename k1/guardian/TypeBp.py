# copied from PR2 GRD on 2018/4/12
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
import VISfunction as vf
import kagralib

__,optic = SYSTEM.split('_')

##################################################
# initialization values

# initial REQUEST state
request = 'SAFE'

# NOMINAL state, which determines when node is OK
nominal = 'ALIGNED'

##################################################

##################################################

WD = ['TM','IM','BF','SF']
BIO = ['TM','IM1','IM2','GAS','BFV','BFH']


# Tool for taking safe snapshot
reqfile = vf.req_file_path(optic)+'/autoBurt.req'
snapfile = '/opt/rtcds/userapps/release/vis/k1/burtfiles/'+vf.modelName(optic)+'_guardian_safe.snap'
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
    goto = False
    

class TRIPPED(GuardState):
    redirect = False
    request = False
    def main(self):

        self.counter = 1
        self.TRAMP = ezca['VIS-'+optic+'_SHUTDOWN_RAMPT']
        self.timer['waiting'] = self.TRAMP
        self.counter = 1

        #Send alerts
        vf.vis_watchdog_tripped(optic)
    
    def run(self):
        log('waiting for all outputs turned off')
    
        if vf.all_off(optic,self):
            ezca.switch('VIS-' + optic + '_TM_DAMP_P','FMALL','OFF')
            ezca.switch('VIS-' + optic + '_TM_DAMP_Y','FMALL','OFF')
            ezca.get_LIGOFilter('VIS-%s_TM_OPLEV_SERVO_PIT'%optic).ramp_gain(0,0,False)
            ezca.get_LIGOFilter('VIS-%s_TM_OPLEV_SERVO_YAW'%optic).ramp_gain(0,0,False)
            log('Turning off the master switch')
            ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
            return not vf.is_tripped(optic,WD,BIO)

    
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

class SAFE(GuardState):
    """Safe state is with master switch off not to send any signal"""
    @watchdog_check
    def main(self):
        log('Turning off all the filters')
        self.counter = 1
        self.timer['waiting'] = 0
        self.TRAMP = 10
    @watchdog_check
    def run(self):
        log('waiting for all outputs turned off')
        if vf.all_off(optic,self):
            ezca.switch('VIS-' + optic + '_TM_DAMP_P','FMALL','OFF')
            ezca.switch('VIS-' + optic + '_TM_DAMP_Y','FMALL','OFF')
            ezca.get_LIGOFilter('VIS-%s_TM_OPLEV_SERVO_PIT'%optic).ramp_gain(0,0,False)
            ezca.get_LIGOFilter('VIS-%s_TM_OPLEV_SERVO_YAW'%optic).ramp_gain(0,0,False)
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
        log('Setting off the offsets for misaligning')
        ezca.switch('VIS-'+optic+'_BF_TEST_Y','OFFSET','OFF')
        ezca.switch('VIS-'+optic+'_IM_TEST_P','OFFSET','OFF')
        ezca.switch('VIS-'+optic+'_IM_TEST_Y','OFFSET','OFF')

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
        return True            
#        for DOF in ['P','Y']:
#            ezca['VIS-'+optic+'_IM_OPTICALIGN_%s_TRAMP'%DOF] = 10.0
#            ezca['VIS-'+optic+'_IM_OPTICALIGN_%s_GAIN'%DOF] = 1.0



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
        self.TRAMP = 10
        self.counter = 1
        self.timer['waiting'] = 0
        log('Setting off the offsets for misaligning')        

    @watchdog_check        
    def run(self):
        if self.timer['waiting']:
            if self.counter == 1:
                ezca.switch('VIS-'+optic+'_BF_TEST_Y','OFFSET','OFF')
                ezca.switch('VIS-'+optic+'_IM_TEST_P','OFFSET','OFF')
                ezca.switch('VIS-'+optic+'_IM_TEST_Y','OFFSET','OFF')

                log('Turning on the damping filters')
                ## GAS ##
                for DOF in ['BF', 'SF']:
                    ezca.switch('VIS-'+optic+'_%s_DAMP_GAS'%DOF,'INPUT','ON')
                    ezca.switch('VIS-'+optic+'_%s_DAMP_GAS'%DOF,'OFFSET','ON')
#-- FIXME --#
                    ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 30
                    ezca['VIS-'+optic+'_%s_DAMP_GAS_RSET'%DOF] = 2
                    ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = 1.0
#-- until here written by YF on Sep30th 2019. please delete this sentence after modification --#
                ## BF ##
                for DOF in ['L','T','V','R','P','Y']:
                    ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = self.TRAMP
                    ezca['VIS-'+optic+'_BF_DAMP_%s_RSET'%DOF] = 2
                    ezca['VIS-'+optic+'_BF_DAMP_%s_GAIN'%DOF] = 1.0
                    ## IM ##
                    ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF] = self.TRAMP
                    ezca['VIS-'+optic+'_IM_DAMP_%s_RSET'%DOF] = 2
                    ezca['VIS-'+optic+'_IM_DAMP_%s_GAIN'%DOF] = 1.0
                self.timer['waiting'] = self.TRAMP
                self.counter += 1

            elif self.counter == 2:
                return True
                

class DAMPING_OFF(GuardState):
    index = 52
    request = False
    @watchdog_check
    def main(self):
        self.TRAMP = 10
        vf.im_offload_off(optic, self.TRAMP)
	log('Turning on the damping filters')
	vf.im_damp_off(optic)
	vf.bf_damp_off(optic)
	vf.gas_damp_off(optic)
        self.timer['waiting'] = 10
        
    @watchdog_check
    def run(self):
        if self.timer['waiting']:
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

class ENGAGE_MISALIGN(GuardState):
    index = 62
    request = False
    @watchdog_check
    def main(self):
        self.TRAMP = 10
        ezca['VIS-PRM_IM_TEST_P_TRAMP'] = self.TRAMP
        ezca['VIS-PRM_IM_TEST_Y_TRAMP'] = self.TRAMP
        ezca['VIS-PRM_BF_TEST_Y_TRAMP'] = self.TRAMP                
        log( optic+"misaligning" )
        ezca.switch('VIS-'+optic+'_BF_TEST_Y','OFFSET','ON')
        ezca.switch('VIS-'+optic+'_IM_TEST_P','OFFSET','ON')
        ezca.switch('VIS-'+optic+'_IM_TEST_Y','OFFSET','ON')
        self.timer['waiting'] = self.TRAMP
        
    @watchdog_check
    def run(self):
        if self.timer['waiting']:
            return True

class MISALIGNED(GuardState):
    index = 800
    @watchdog_check
    def main(self):
        log(optic+"mis-aligned")

    @watchdog_check
    def run(self):
        return True

class MISALIGN_OFF(GuardState):
    index = 64
    request = False
    @watchdog_check
    def main(self):
        log("turning off"+optic+"misalignment" )
        ezca.switch('VIS-'+optic+'_BF_TEST_Y','OFFSET','OFF')
        ezca.switch('VIS-'+optic+'_IM_TEST_P','OFFSET','OFF')
        ezca.switch('VIS-'+optic+'_IM_TEST_Y','OFFSET','OFF')
        self.timer['waiting'] = 5
        
    @watchdog_check
    def run(self):
        if self.timer['waiting']:
            return True

        

class ENGAGE_OLDAMP(GuardState):
    index = 900
    request = False
    @watchdog_check
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

        self.Target = {'P':ezca['VIS-'+optic+'_GOOD_OPLEV_PIT'],
                       'Y':ezca['VIS-'+optic+'_GOOD_OPLEV_YAW'],
                       }
        self.TMdampinitFMlist = {
        'PR3':{'L':('INPUT','OUTPUT','LIMIT','FM1','FM2','FM6','FM7','FM9',),'P':('INPUT','OUTPUT','LIMIT','FM1','FM2','FM6','FM9',),'Y':('INPUT','OUTPUT','LIMIT','FM1','FM2','FM9',)},
        'PR2':{'L':('INPUT','OUTPUT','LIMIT','FM1','FM2','FM3','FM4','FM9',),'P':('INPUT','OUTPUT','LIMIT','FM1','FM2','FM3','FM4','FM9',),'Y':('INPUT','OUTPUT','LIMIT','FM1','FM2','FM9',)},
        'PRM':{'L':('INPUT','OUTPUT','LIMIT','FM1','FM2','FM3','FM4','FM9',),'P':('INPUT','OUTPUT','LIMIT','FM1','FM2','FM3','FM4','FM9',),'Y':('INPUT','OUTPUT','LIMIT','FM1','FM2','FM9',)},
        }

        self.TMdampBSTFMlist = {
            'PR3':{'L':('FM8',),'P':('FM7','FM8',),'Y':('FM7','FM8',)},
            'PR2':{'L':('FM8',),'P':('FM8',),'Y':('FM8',)},
            'PRM':{'L':(),'P':('FM8',),'Y':('FM8',)},
            }        
        self.TRAMP = 2
        self.IMlimit = 24000
        self.TMlimit = 8000
	log('Turning on the oplev controls')
        
    @watchdog_check
    def run(self):
        if self.timer['waiting']:
            if self.counter == 0:
                for DOF in ['P','Y']:
                    ezca['VIS-'+optic+'_TM_OLSET_%s_TRAMP'%DOF] = 0
                    ezca['VIS-'+optic+'_TM_OLSET_%s_OFFSET'%DOF] = self.Target[DOF]
                    ezca['VIS-'+optic+'_TM_OLSET_%s_GAIN'%DOF] = 1
                    ezca['VIS-'+optic+'_TM_OLSET_%s_TRAMP'%DOF] = 2                    
                    ezca.get_LIGOFilter('VIS-'+optic+'_TM_OLSET_%s'%DOF).only_on('INPUT','OUTPUT','OFFSET')

                for DOF in ['L','P','Y']:                    
                    ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = self.TRAMP
                    ezca['VIS-'+optic+'_TM_DAMP_%s_LIMIT'%DOF] = self.TMlimit
                    ezca.get_LIGOFilter('VIS-'+optic+'_TM_DAMP_%s'%DOF).only_on(*self.TMdampinitFMlist[optic][DOF])
                    ezca['VIS-'+optic+'_TM_DAMP_%s_RSET'%DOF] = 2
                    ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = 1.0

                for DOF in ['PIT','YAW']:
                    ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_OFFSET'%DOF] = 0
                    ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_TRAMP'%DOF] = 0
                    ezca['VIS-'+optic+'_TM_OPLEV_SERVO_%s_GAIN'%DOF] = 1.0
                    ezca.get_LIGOFilter('VIS-'+optic+'_TM_OPLEV_SERVO_%s'%DOF).only_on('INPUT','OUTPUT')
                    
                self.counter += 1
                self.timer['waiting'] = self.TRAMP

            elif self.counter == 1:
                # turn Boost on
                for DOF in ['P','Y']:
                    ezca.get_LIGOFilter('VIS-'+optic+'_TM_DAMP_%s'%DOF).switch_on(*self.TMdampBSTFMlist[optic][DOF])
                self.timer['waiting'] = self.TRAMP
                self.counter += 1                

            elif self.counter == 2:
                return True

class OLDAMPED(GuardState):
    index = 333
    request = True

    @watchdog_check
    def run(self):
        return True

class OLDAMP_OFF(GuardState):
    index = 74             
    request = False
    @watchdog_check
    def main(self):
	log('Turning off the oplev controls')
        self.TRAMP = 2
        self.timer['waiting'] = 0
        self.counter = 0
        self.TMdampBSTFMlist = {
            'PR2':{'L':('FM8',),'P':('FM8',),'Y':('FM8',)},
            'PR3':{'L':('FM8',),'P':('FM8',),'Y':('FM8',)},
            'PRM':{'P':('FM8',),'Y':('FM8',),'L':()},
            }        

    @watchdog_check        
    def run(self):
        if self.timer['waiting']:
            if self.counter == 0:
                # turn Boost off
                for DOF in ['L','P','Y']:
                    ezca.get_LIGOFilter('VIS-'+optic+'_TM_DAMP_%s'%DOF).switch_off(*self.TMdampBSTFMlist[optic][DOF])
                self.timer['waiting'] = self.TRAMP
                self.counter += 1
                
            if self.counter == 1:
                for DOF in ['P','Y','L']:
                    ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = self.TRAMP
                    ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = 0
                self.timer['waiting'] = self.TRAMP
                self.counter += 1

            elif self.counter == 2:
                return True


class ENGAGE_OLDCCTRL(GuardState):
    index = 334
    request = False
    @watchdog_check
    def main(self):
        self.counter = 1
        self.timer['waiting'] = 0
        self.Target = {'P':ezca['VIS-'+optic+'_GOOD_OPLEV_PIT'],
                       'Y':ezca['VIS-'+optic+'_GOOD_OPLEV_YAW'],
                       }
        

        self.IMintFMlist = {
            'PR3':{'P':('OUTPUT','LIMIT','FM6','FM2','FM3','FM1'),'Y':('OUTPUT','LIMIT','FM1','FM2','FM6')},
            'PR2':{'P':('OUTPUT','LIMIT','FM6','FM2','FM3','FM1'),'Y':('OUTPUT','LIMIT','FM1','FM2','FM6')},            
            'PRM':{'P':('OUTPUT','LIMIT','FM1','FM2','FM3','FM5'),'Y':('OUTPUT','LIMIT','FM1','FM2','FM3','FM5')},
            }        
        self.TRAMP = 10
        self.IMlimit = 24000
        self.TMlimit = 8000
	log('Turning on the oplev controls')
        
    @watchdog_check
    def run(self):
        if self.timer['waiting']:
            if self.counter == 1:
                # turn integrator on
                for DOF in ['P','Y']:
                    ezca.get_LIGOFilter('VIS-'+optic+'_IM_OLDAMP_%s'%DOF).only_on(*self.IMintFMlist[optic][DOF])
                    ezca['VIS-'+optic+'_IM_OLDAMP_%s_LIMIT'%DOF] = self.IMlimit
                    if not ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF]:
                        ezca['VIS-'+optic+'_IM_OLDAMP_%s_RSET'%DOF] = 2
                        ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = 1
                    ezca.get_LIGOFilter('VIS-'+optic+'_IM_OLDAMP_%s'%DOF).switch_on('INPUT')
                self.timer['waiting'] = self.TRAMP
                self.counter += 1
                    
            elif self.counter == 2:
                return True    

class ALIGNED(GuardState):
    index = 1000
    #####  UNCOMMENT (see klog )
    # @watchdog_check
    # def main(self):
    #     for fec in get_dcuid(optic):
    #         restore(fec, "ALIGNED")

    @watchdog_check
    def run(self):
	log('All controlled')
	# Add DC alignment values with ramp time!
        return True

class DISABLE_OLDCCTRL(GuardState):
    index = 996
    def main(self):
        self.TRAMP = 5

        self.timer['waiting'] = 0
        self.counter = 1

    def run(self):
        if self.timer['waiting']:
            
            if self.counter == 1:
                for DOF in ['P','Y']:
                    ezca.get_LIGOFilter('VIS-'+optic+'_IM_OLDAMP_%s'%DOF).switch_off('INPUT')
                self.timer['waiting'] = 2
                self.counter += 1


            elif self.counter == 2:
                return True

        
class OBSERVATION(GuardState):
    index = 2000
    @watchdog_check
    def main(self):
        self.timer['waiting'] = 10
        log('Changing the filter configuration to low-noise mode')
    @watchdog_check
    def run(self):
        return self.timer['waiting']

class ENGAGE_LOCKACQUISITION_FILTER(GuardState):
    index = 1333
    request = False
    @watchdog_check
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0
        self.TRAMP = 2

        self.flag = {'PR3':True,'PR2':False,'PRM':False}
        self.initFMs = {'PR3':{'L':[],'P':['FM3','FM4'],'Y':['FM3','FM4']},
                        'PR2':False,
                        'PRM':False}
        self.bstFMs = {'PR3':{'L':[],'P':['FM5',],'Y':['FM5',]},
                        'PR2':False,
                        'PRM':False}

    @watchdog_check
    def run(self):
        if not self.flag[optic]:
            return True
        else:
            if self.timer['waiting']:
                if self.counter == 0:
                    # turn off the DCCTRL
                    for DOF in ['P','Y']:
                        ezca.get_LIGOFilter('VIS-'+optic+'_IM_OLDAMP_%s'%DOF).switch_off('INPUT')
                    self.timer['waiting'] = 2
                    self.counter += 1
                elif self.counter == 1:
                    # turn nominal damping off
                    for DOF in ['P','Y','L']:
                        if self.initFMs[optic][DOF]:
                            ezca.get_LIGOFilter('VIS-'+optic+'_TM_DAMP_' + DOF).ramp_gain(0,self.TRAMP,wait=False)
                    self.timer['waiting'] = self.TRAMP
                    self.counter += 1
                elif self.counter == 2:
                    for DOF in ['P','Y','L']:
                        kagralib.init_FB('VIS-'+optic+'_TM_DAMP_'+DOF, engaged_FM = self.initFMs[optic][DOF],
                                         gain = 1, ramptime = self.TRAMP,ramp = True)
                    self.counter += 1
                    self.timer['waiting'] = self.TRAMP

                elif self.counter == 3:
                    for DOF in ['P','Y','L']:
                        ezca.get_LIGOFilter('VIS-'+optic+'_TM_DAMP_'+DOF).turn_on(*self.bstFMs[optic][DOF])
                    self.counter += 1
                    self.timer['waiting'] = 2
                elif self.counter == 4:
                    return True

class LOCK_ACQUISITION(GuardState):
    index = 166
    @watchdog_check
    def run(self):
        notify('I am waiting for the lock!! Good Lock!!')
        return True

class DISABLE_LOCK_ACQUISITION_FILTERS(GuardState):
    index = 167

    @watchdog_check
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0
        self.TRAMP = 2

        self.flag = {'PR3':True,'PR2':False,'PRM':False}

    @watchdog_check
    def run(self):
        if not self.flag[optic]:
            return True
        else:
            if self.timer['waiting']:
                if self.counter == 0:
                    for DOF in ['P','Y','L']:
                        kagralib.init_FB('VIS-'+optic+'_TM_DAMP_'+DOF,
                                         gain = 0, ramptime = self.TRAMP,ramp = True)
                    self.counter += 1
                    self.timer['waiting'] = self.TRAMP

                elif self.counter == 1:
                    return True


                                                            
                

##################################################
# Edges

edges = [
    ('INIT','SAFE'),
    ('TRIPPED','SAFE'),
    ('SAFE','OUTPUT_ON'),
    ('OUTPUT_ON','UNDAMPED'),
    ('UNDAMPED','DAMPING_ON'),
    ('DAMPING_ON','DAMPED'),
    ('DAMPED','DAMPING_OFF'),
    ('DAMPING_OFF','UNDAMPED'),
    # modified downstream by MN, 2019/09/12
    ('DAMPED','ENGAGE_OLDAMP'),
    ('ENGAGE_OLDAMP','OLDAMPED'),    
    ('DAMPED', 'ENGAGE_MISALIGN'),
    ('ENGAGE_MISALIGN', 'MISALIGNED'),
    ('MISALIGNED','MISALIGN_OFF'),
    ('MISALIGN_OFF','DAMPED'),
    ('OLDAMPED','OLDAMP_OFF'),
    ('OLDAMP_OFF','DAMPED'),
    ('OLDAMPED','ENGAGE_OLDCCTRL'),
    ('ENGAGE_OLDCCTRL','ALIGNED'),
    ('UNDAMPED','SAFE'),
    ('ALIGNED','DISABLE_OLDCCTRL'),
    ('DISABLE_OLDCCTRL','OLDAMPED'),
    ('ALIGNED','OBSERVATION'),
    ('ALIGNED','ENGAGE_LOCKACQUISITION_FILTER'),
    ('ENGAGE_LOCKACQUISITION_FILTER','LOCK_ACQUISITION'),
    ('LOCK_ACQUISITION','DISABLE_LOCK_ACQUISITION_FILTERS'),
    ('DISABLE_LOCK_ACQUISITION_FILTERS','ENGAGE_OLDAMP'),
   ]
