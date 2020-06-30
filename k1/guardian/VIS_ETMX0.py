############################################
# ETMX gardian
#
# renewed on 2018.Mar.6th by KI
# modified on 2018.Apr.21st by MN (not marionette)
# modified on 2019.Jun.7th by AS (Still working on)
############################################
import time
import math
from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import os
import sys
import subprocess
import sendAlert as sa

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
IPgains = { 'L':1.0,
            'T':1.0,
            'Y':1.0}

# GAS gain setting
GASgains = { 'F0':1.0,
             'F1':1.0,
             'F2':0.0, # For ETMX
             'F3':1.0,
             'BF':1.0}

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
reqfile = '/opt/rtcds/kamioka/k1/target/k1visey/k1viseyepics/autoBurt.req'  #TO BE FIXED
snapfile = '/opt/rtcds/userapps/release/vis/k1/burtfiles/k1visey_guardian_safe.snap'



BIO_TWR = ['BFH','BFV','GAS','PI']
BIO_PAY = ['TM','IMB','IMH','MNIMV','MNH']

misalign_ramp = 60
misalign_amount = 100

##################################################
# STATE decorators

class watchdog_check(GuardStateDecorator):
    """Decorator to check watchdog"""
    def pre_exec(self):
        if lib.is_twr_tripped(optic, BIO_TWR):
            log("All tripped.")
            return 'TRIPPED'
        elif lib.is_pay_tripped(optic,BIO_PAY):
            log("Payload is tripped")
            return 'PAY_TRIPPED'

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
        lib.all_off_quick(self,optic)
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'
        notify("please restart WatchDog!")
        return True
    def run(self):
        if not (lib.is_pay_tripped(optic) or lib.is_twr_tripped(optic)):
            return True

class PAY_TRIPPED(GuardState):
    index = 2
    redirect = False
    request = False
    def main(self):
        lib.pay_off(self,optic)
        notify("please restart WatchDog!")
        return True
    def run(self):
        if not lib.is_pay_tripped(optic):
            return True

#class OPLEV_OUTOFRANGE(GuardState):
#    index = 3
#    redirect = False
#    request = False
#    @watchdog_check
#    def main(self):
#        log('Oplev is out of range. Turning off the oplev controls')
#        lib.tm_damp_off(self,optic)
#        lib.im_oldamp_off(self,optic)
#        lib.mn_oldamp_off(self,optic)
#        lib.bf_oldamp_off(self,optic)
#            
#        lib.mn_mnoldamp_off(self,optic)
#        return True
#    def run(self):
#        if lib.is_oplev_inrange(optic):
#            return True

        
class RESET(GuardState):
    index = 20
    goto = False
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

    def run(self):
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
            ezca['VIS-'+optic+'_MN_OPTICALIGN_%s_GAIN'%DOF] = 1.0
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

class ENGAGE_TWR_DAMPING(GuardState):
    index = 52
    request = False
    @watchdog_check
    def main(self):
        log('Turning on the damping filters')
	## IP ## (all the gains should be 1)
        for DOF in ['L','T','Y']:
            ezca['VIS-'+optic+'_IP_DAMP_%s_TRAMP'%DOF] = 60.0
            ezca['VIS-'+optic+'_IP_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_IP_DAMP_%s_GAIN'%DOF] = IPgains['%s'%DOF]
            #ezca['VIS-'+optic+'_IP_DAMP_%s_OFFSET'%DOF] = -ofsavg
	## GAS ## (zero gains for now)
        for DOF in ['BF','F3','F2','F1','F0']:
            ezca['VIS-'+optic+'_%s_DAMP_GAS_TRAMP'%DOF] = 15.0
            ezca['VIS-'+optic+'_%s_DAMP_GAS_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_%s_DAMP_GAS_GAIN'%DOF] = GASgains['%s'%DOF]
        lib.wait(self,ezca['VIS-'+optic+'_IP_DAMP_Y_TRAMP'])
	## BF ## (gains are decleared in BFgains individually)
        for DOF in ['L','T','V','R','P','Y']:
            ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = 5.0
            if DOF == 'Y':
                ezca['VIS-'+optic+'_BF_DAMP_%s_TRAMP'%DOF] = 60.0
            ezca['VIS-'+optic+'_BF_DAMP_%s_RSET'%DOF] = 2
            ezca['VIS-'+optic+'_BF_DAMP_%s_GAIN'%DOF] = BFgains['%s'%DOF]
        lib.wait(self,ezca['VIS-'+optic+'_BF_DAMP_Y_TRAMP'])        
	return True

class TWR_DAMPED(GuardState):
    index = 55
    @watchdog_check
    def main(self):
        log(optic+"tower damped")

    @watchdog_check
    def run(self):
        return True  

#class ENGAGE_PAY_DAMPING(GuardSate):
#    index = 57
#    request = False
#    @watchdog_check
#    def main(self):
#        log('Turning on the payload damping filters')
#        for DOF in ['L','T','V','R','P','Y']:
#	## MN ## 
#            ezca['VIS-'+optic+'_MN_DAMP_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_MN_DAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_MN_DAMP_%s_GAIN'%DOF] = MNgains['%s'%DOF]
#            if MNgains['%s'%DOF]!=0.0:
#                lib.wait(self,ezca['VIS-'+optic+'_MN_DAMP_%s_TRAMP'%DOF])
#	## IM ##
#            ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_IM_DAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_IM_DAMP_%s_GAIN'%DOF] = IMgains['%s'%DOF]
#            if IMgains['%s'%DOF]!=0.0:
#                lib.wait(self,ezca['VIS-'+optic+'_IM_DAMP_%s_TRAMP'%DOF])
#        ## MNOL ##
#        for DOF in ['P','Y']:
#            ezca['VIS-'+optic+'_MN_OLDAMP_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_MN_OLDAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_MN_OLDAMP_%s_GAIN'%DOF] = MNoplev_gains['%s'%DOF]
#            if MNoplev_gains['%s'%DOF]!=0.0:
#                lib.wait(self,ezca['VIS-'+optic+'_MN_OLDAMP_%s_TRAMP'%DOF])
#                
#	return True

class ENGAGE_PAY_DAMPING(GuardState):
    index = 520
    request = False
    @watchdog_check
    def main(self):
        TRAMP = 10
        log('Turning on the damping filters')
#        ezca.switch('VIS-' + optic + '_IM_TMOLDAMP_P','FM1','FM2','FM3','FM4','FM5','FM6','LIMIT','INPUT','OUTPUT','ON','FM7','FM8','FM9','FM10','OFF')
#        ezca.switch('VIS-' + optic + '_IM_TMOLDAMP_Y','FM1','FM2','FM3','FM4','FM5','FM6','FM7','FM8','LIMIT','INPUT','OUTPUT','ON','FM9','FM10','OFF')
        ezca['VIS-' + optic + '_IM_TMOLDAMP_P_TRAMP'] = TRAMP
        ezca['VIS-' + optic + '_IM_TMOLDAMP_Y_TRAMP'] = TRAMP
        ezca['VIS-' + optic + '_IM_TMOLDAMP_P_GAIN'] = 1
        ezca['VIS-' + optic + '_IM_TMOLDAMP_Y_GAIN'] = 1
        ezca['VIS-' + optic + '_MN_TMOLDAMP_P_GAIN'] = 0
        ezca['VIS-' + optic + '_MN_TMOLDAMP_Y_GAIN'] = 0
        ezca['VIS-' + optic + '_TM_DAMP_P_GAIN'] = 0
        ezca['VIS-' + optic + '_TM_DAMP_Y_GAIN'] = 0
        self.timer['waiting'] = TRAMP

        # BP comb setting
        lib.clear_PAYINPUT_MTRX(optic)
        lib.clear_PAYOUTPUT_MTRX(optic)

        for ii in range(24):
            lib.config_BPCOMB_from_description(optic = optic, DOFNUM = ii+1,
                                           onSW = [1,2,3],TRAMP = TRAMP, LIMIT = 15000)

        return True
    @watchdog_check
    def run(self):
        if self.timer['waiting']:
            return True

class PAY_DAMPED(GuardState):
    index = 521
    @watchdog_check
    def main(self):
        log('PAYLOAD_DAMPED')

    @watchdog_check
    def run(self):
        return True

class DISABLE_PAY_DAMPING(GuardState):
    index = 522
    request = False
    @watchdog_check
    def main(self):
        TRAMP = 10
        log('Turning off the damping filter')
        self.timer['waiting'] = TRAMP
        ezca['VIS-' + optic + '_IM_TMOLDAMP_P_GAIN'] = 0
        ezca['VIS-' + optic + '_IM_TMOLDAMP_Y_GAIN'] = 0
        ezca['VIS-' + optic + '_MN_TMOLDAMP_P_GAIN'] = 0
        ezca['VIS-' + optic + '_MN_TMOLDAMP_Y_GAIN'] = 0
        ezca['VIS-' + optic + '_TM_DAMP_P_GAIN'] = 0
        ezca['VIS-' + optic + '_TM_DAMP_Y_GAIN'] = 0

        lib.disable_BPCOMB(optic)

    @watchdog_check
    def run(self):
        if self.timer['waiting']:
            return True
    

#class ALL_DAMPED(GuardSate):
#    index = 60
#    @watchdog_check
#    def main(self):
#        log(optic+"all damped")
#        return True
#    @watchdog_check
#    def run(self):
#        return True  


class DISABLE_TWR_DAMPING(GuardState):
    index = 53
    request = False
    @watchdog_check
    def main(self):
        log('Turning off the damping filters')
        rampt_bf = 60.0
        rampt_gas = 10.0
        rampt_ip = 60.0
        rampt_ip_blend = 10.0
        lib.bf_damp_off(self,optic, rampt_bf)
        lib.gas_damp_off(self,optic, rampt_gas)
        lib.ip_damp_off(self,optic, rampt_ip)
        lib.ip_blend_off(self,optic, rampt_ip_blend)
	return True


#class ENGAGE_DCCONTROL(GuardState):
#    index = 900
#    request = False
#    @watchdog_check
#    @oplev_check
#    def main(self):
#        log('Turning on the oplev controls')
#
#        ## BF ##
#        for DOF in ['L','P','Y']:
#            ezca['VIS-'+optic+'_BF_OLDAMP_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_BF_OLDAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_BF_OLDAMP_%s_GAIN'%DOF] = TMoplev_BF_gains['%s'%DOF]
#            if TMoplev_BF_gains['%s'%DOF]!=0.0:
#                lib.wait(self,ezca['VIS-'+optic+'_BF_OLDAMP_%s_TRAMP'%DOF])
#	## MN ##
#        for DOF in ['L','P','Y']:
#            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_MN_OLDAMP1_%s_GAIN'%DOF] = TMoplev_MN_gains['%s'%DOF]
#            if TMoplev_MN_gains['%s'%DOF]!=0.0:
#                lib.wait(self,ezca['VIS-'+optic+'_MN_OLDAMP1_%s_TRAMP'%DOF])
#	## IM ##
#            ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_IM_OLDAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_IM_OLDAMP_%s_GAIN'%DOF] = TMoplev_IM_gains['%s'%DOF]
#            if TMoplev_IM_gains['%s'%DOF]!=0.0:
#                lib.wait(self,ezca['VIS-'+optic+'_IM_OLDAMP_%s_TRAMP'%DOF])
#	## TM ##
#            ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF] = 5.0
#            ezca['VIS-'+optic+'_TM_DAMP_%s_RSET'%DOF] = 2
#            ezca['VIS-'+optic+'_TM_DAMP_%s_GAIN'%DOF] = TMoplev_gains['%s'%DOF]
#            if TMoplev_gains['%s'%DOF]!=0.0:
#                lib.wait(self,ezca['VIS-'+optic+'_TM_DAMP_%s_TRAMP'%DOF])
#        return True

#class DISABLE_DCCONTROL(GuardState):
#    index = 54
#    request = False
#
#    @watchdog_check
#    def main(self):
#        log('Turning off the oplev controls')
#        lib.tm_damp_off(self,optic)
#        lib.im_oldamp_off(self,optic)
#        lib.mn_oldamp_off(self,optic)
#        lib.mn_mnoldamp_off(self,optic)
#        lib.bf_oldamp_off(self,optic)
# 	return True

class ALIGNING(GuardState):
    index = 99
    request = False
    @watchdog_check
    @oplev_check
    def main(self):
        log('Enabling the DC control')
        ezca['VIS-'+ optic +'_MN_OLSET_P_TRAMP'] = 15
        ezca['VIS-'+ optic +'_MN_OLSET_Y_TRAMP'] = 15
        ezca['VIS-'+ optic +'_MN_OLSET_P_OFFSET'] = ezca['VIS-'+ optic +'_GOOD_OPLEV_PIT']
        ezca['VIS-'+ optic +'_MN_OLSET_Y_OFFSET'] = ezca['VIS-'+ optic +'_GOOD_OPLEV_YAW']

        for DOF in ['P','Y']:
            ezca['VIS-'+ optic +'_MN_OLDCCTRL_%s_TRAMP'%DOF] = 15
            ezca['VIS-'+ optic +'_MN_OLDCCTRL_%s_GAIN'%DOF] = 0
            ezca['VIS-'+ optic +'_MN_OLDCCTRL_%s_RSET'%DOF] = 2
            ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_Y','OUTPUT','FM1','FM2','FM4','FM8','FM9','ON','INPUT','FM3','FM5','FM6','FM7','FM10','OFFSET','OFF')

        ezca['VIS-'+ optic +'_MN_OLCTRL_Y_MTRX_1_1'] = 1 # MN feedback
        ezca['VIS-'+ optic +'_MN_OLCTRL_Y_MTRX_2_1'] = 1 # BF feed-back


        ezca['VIS-'+ optic +'_MN_OLDCCTRL_P_TRAMP'] = 1
        ezca['VIS-'+ optic +'_MN_OLDCCTRL_Y_TRAMP'] = 1
        lib.wait(self, 3 * ezca['VIS-'+optic+'_MN_OLDCCTRL_P_TRAMP'])
        ezca['VIS-'+ optic +'_MN_OLDCCTRL_P_GAIN'] = 1
        ezca['VIS-'+ optic +'_MN_OLDCCTRL_Y_GAIN'] = 1
        ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_P','INPUT','ON')
        ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_Y','INPUT','ON')
        lib.wait(self, 3 * ezca['VIS-'+optic+'_MN_OLDCCTRL_P_TRAMP'])
        ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_P','FM3','ON')
        ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_Y','FM3','ON')
        ezca['VIS-'+ optic +'_MN_OLDCCTRL_P_TRAMP'] = 15

        lib.wait(self, ezca['VIS-'+optic+'_MN_OLDCCTRL_Y_TRAMP'])
        ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_TRAMP'] = 1
        ezca.switch('VIS-'+optic+'_BF_PAYOL_DCCTRL_Y','FM1','ON')
        ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_GAIN'] = 1
        lib.wait(self, ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_TRAMP'])
        ezca.switch('VIS-' + optic + '_BF_PAYOL_DCCTRL_Y', 'FM1','ON')
        lib.wait(self, ezca['VIS-'+optic+'_MN_OLDCCTRL_Y_TRAMP'])
        return True

class ALIGNED(GuardState):
    index = 100
    @watchdog_check
    @oplev_check
    def main(self):
        log('ALIGNED')
    @watchdog_check
    @oplev_check
    def run(self):
        return True

class FREEZING_OUTPUTS(GuardState):
    index = 106
    request = False
    @watchdog_check
    @oplev_check
    def main(self):
        log('Turning off the OLDCCTRL inputs')
        ezca.switch('VIS-' + optic + '_MN_OLDCCTRL_Y','INPUT','OFF')
        ezca.switch('VIS-' + optic + '_MN_OLDCCTRL_P','INPUT','OFF')
        ezca.switch('VIS-' + optic + '_BF_PAYOL_DCCTRL_Y','INPUT','OFF')

    @watchdog_check
    @oplev_check
    def run(self):
        return True


class UNFREEZING_OUTPUTS(GuardState):
    index = 107
    request = False
    @watchdog_check
    @oplev_check
    def main(self):
        log('Turning off the OLDCCTRL inputs')
        ezca.switch('VIS-' + optic + '_MN_OLDCCTRL_Y','INPUT','ON')
        ezca.switch('VIS-' + optic + '_MN_OLDCCTRL_P','INPUT','ON')
        ezca.switch('VIS-' + optic + '_BF_PAYOL_DCCTRL_Y','INPUT','ON')        
        lib.wait(self, ezca['VIS-'+optic+'_MN_OLDCCTRL_P_TRAMP'])
    @watchdog_check
    @oplev_check
    def run(self):
        return True



class FREEZE(GuardState):
    index = 108
    @watchdog_check
    @oplev_check
    def main(self):
        log('FLOATING')
    @watchdog_check
    @oplev_check
    def run(self):
        return True

class MISALIGNING(GuardState):
    index = 101
    request = False
    @watchdog_check
    @oplev_check
    def main(self):
        log('Turning off the DC control, turning on the BF offset')
        ezca.switch('VIS-' + optic + '_MN_OLDCCTRL_Y','INPUT','OFF')
        ezca.switch('VIS-' + optic + '_MN_OLDCCTRL_Y','FM3','OFF')
        ezca.switch('VIS-' + optic + '_BF_PAYOL_DCCTRL_Y', 'FM1','OFF')
        lib.wait(self, ezca['VIS-'+optic+'_MN_OLDCCTRL_Y_TRAMP'])

        ezca['VIS-' + optic + '_BF_PAYOL_DCCTRL_Y_OFS_TRAMP'] = misalign_ramp
        ezca['VIS-' + optic + '_BF_PAYOL_DCCTRL_Y_OFS_OFFSET'] = misalign_amount
        ezca.switch('VIS-' + optic + '_BF_PAYOL_DCCTRL_Y_OFS','OFFSET','ON')
        lib.wait(self, ezca['VIS-' + optic + '_BF_PAYOL_DCCTRL_Y_OFS_TRAMP'])
        return True


class MISALIGNED(GuardState):
    index = 102
    @watchdog_check
    @oplev_check
    def main(self):
        log('Misaligned')
    @watchdog_check
    def run(self):
        return True

class REALIGNING(GuardState):
    index = 104
    request = False
    @watchdog_check
    @oplev_check
    def main(self):
        ezca['VIS-' + optic + '_BF_PAYOL_DCCTRL_Y_OFS_TRAMP'] = misalign_ramp
        ezca.switch('VIS-' + optic + '_BF_PAYOL_DCCTRL_Y_OFS','OFFSET','OFF')
        lib.wait(self, ezca['VIS-' + optic + '_BF_PAYOL_DCCTRL_Y_OFS_TRAMP'])
        for DOF in ['Y']:
            ezca['VIS-'+ optic +'_MN_OLDCCTRL_%s_TRAMP'%DOF] = 15
            ezca['VIS-'+ optic +'_MN_OLDCCTRL_%s_GAIN'%DOF] = 0
            ezca['VIS-'+ optic +'_MN_OLDCCTRL_P_RSET'] = 2
            ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_Y','OUTPUT','FM1','FM2','FM4','FM8','FM9','ON','INPUT','FM3','FM5','FM6','FM7','FM10','OFFSET','OFF')
        for DOF in ['Y']:
            ezca['VIS-'+ optic +'_MN_OLDCCTRL_%s_TRAMP'%DOF] = 1
            lib.wait(self, 3 * ezca['VIS-'+optic+'_MN_OLDCCTRL_%s_TRAMP'%DOF])
            ezca['VIS-'+ optic +'_MN_OLDCCTRL_%s_GAIN'%DOF] = 1
            ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_%s'%DOF,'INPUT','ON')
            lib.wait(self, 3 * ezca['VIS-'+optic+'_MN_OLDCCTRL_%s_TRAMP'%DOF])
            ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_%s'%DOF,'FM3','ON')
            ezca['VIS-'+ optic +'_MN_OLDCCTRL_%s_TRAMP'%DOF] = 15
            lib.wait(self, ezca['VIS-'+optic+'_MN_OLDCCTRL_%s_TRAMP'%DOF])

        ezca.switch('VIS-' + optic + '_BF_PAYOL_DCCTRL_Y', 'FM1','ON')
        log('Turned off the BF offset, Y DCCTRL ON')
        return True


class DISABLE_MISALIGNMENT(GuardState):
    index = 105
    request = False
    @watchdog_check
    @oplev_check
    def main(self):
        log('DISABLING OL DC CONTROL...')
        ezca['VIS-' + optic + '_BF_PAYOL_DCCTRL_Y_OFS_TRAMP'] = misalign_ramp
        ezca.switch('VIS-' + optic + '_BF_PAYOL_DCCTRL_Y_OFS','OFFSET','OFF')
        lib.wait(self, ezca['VIS-' + optic + '_BF_PAYOL_DCCTRL_Y_OFS_TRAMP'])
    @watchdog_check
    @oplev_check
    def run(self):
        return True


class DISABLE_DCOLCTRL(GuardState):
    index = 103
    request = False
    @watchdog_check
    @oplev_check
    def main(self):
        log('DISABLING OL DC CONTROL...')
        ezca['VIS-'+optic+'_MN_OLDCCTRL_P_TRAMP']=15
        ezca['VIS-'+optic+'_MN_OLDCCTRL_Y_TRAMP']=15

        ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_P','FM3','OFF')
        ezca.switch('VIS-'+ optic +'_MN_OLDCCTRL_Y','FM3','OFF')
        ezca.switch('VIS-'+ optic +'_BF_PAYOL_DCCTRL_Y','FM1','OFF')

        ezca['VIS-'+optic+'_MN_OLDCCTRL_P_GAIN'] = 0
        ezca['VIS-'+optic+'_MN_OLDCCTRL_Y_GAIN'] = 0
        ezca['VIS-'+optic+'_BF_PAYOL_DCCTRL_Y_GAIN'] = 0

        lib.wait(self, ezca['VIS-'+optic+'_MN_OLDCCTRL_P_TRAMP'])

        ezca['VIS-'+optic+'_MN_OLCTRL_Y_MTRX_1_1'] = 0 # MN off
        ezca['VIS-'+optic+'_MN_OLCTRL_Y_MTRX_2_1'] = 0 # BF off
        ezca['VIS-'+optic+'_MN_OLDCCTRL_P_RSET'] = 2
        ezca['VIS-'+optic+'_MN_OLDCCTRL_Y_RSET'] = 2

    @watchdog_check
    @oplev_check
    def run(self):
        return True

##################################################
# Edges

edges = [
    ('INIT','SAFE'),
    ('RESET', 'SAFE'),
    ('TRIPPED','SAFE'),
    ('PAY_TRIPPED','TWR_DAMPED'),
    ('SAFE','OUTPUT_ON'),
    ('OUTPUT_ON','UNDAMPED'),
    ('UNDAMPED','ENGAGE_TWR_DAMPING'),
    ('ENGAGE_TWR_DAMPING','TWR_DAMPED'),
    ('TWR_DAMPED','ENGAGE_PAY_DAMPING'),
    ('ENGAGE_PAY_DAMPING','PAY_DAMPED'),
    ('PAY_DAMPED','DISABLE_PAY_DAMPING'),
    ('DISABLE_PAY_DAMPING','TWR_DAMPED'),
    ('TWR_DAMPED','DISABLE_TWR_DAMPING'),
    ('DISABLE_TWR_DAMPING','UNDAMPED'),
    ('UNDAMPED','SAFE'),
    ('PAY_DAMPED','ALIGNING'),
    ('ALIGNING','ALIGNED'),
    ('ALIGNED','DISABLE_DCOLCTRL'),
    ('DISABLE_DCOLCTRL','PAY_DAMPED'),
    ('ALIGNED','MISALIGNING'),
    ('MISALIGNING','MISALIGNED'),
    ('MISALIGNED','REALIGNING'),
    ('REALIGNING','ALIGNED'),
    ('MISALIGNED','DISABLE_MISALIGNMENT'),
    ('DISABLE_MISALIGNMENT','PAY_DAMPED'),
    ('PAY_DAMPED','MISALIGNING'),
    ('ALIGNED','FREEZING_OUTPUTS'),
    ('FREEZING_OUTPUTS','FREEZE'),
    ('FREEZE','UNFREEZING_OUTPUTS'),
    ('UNFREEZING_OUTPUTS','ALIGNED'),
    ('FREEZE','DISABLE_DCOLCTRL')
   ]
