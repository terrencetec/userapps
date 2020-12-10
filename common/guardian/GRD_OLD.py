import matplotlib
matplotlib.use('Agg')

from guardian import GuardState
from guardian import GuardStateDecorator

import cdslib
import sdflib
import kagralib
import vislib
import time
import foton

import numpy as np
import balanceCOILOUTF_TypeA
import logging, sys, os
from datetime import datetime
import matplotlib.pyplot as plt

import importlib
sysmod = importlib.import_module(SYSTEM)

__,OPTIC = SYSTEM.split('_') # This instruction retrieves the name of the Guardian node running the code e.i. the suspension name: SYSTEM='VIS_BS'.
optic = OPTIC.lower()
sustype = vislib.get_Type(OPTIC)

##################################################
# initialization values
state = 'INIT' # For determining where the guardian state is.

# initial REQUEST state
request = 'SAFE'

# NOMINAL state, which determines when node is OK
nominal = 'OBSERVATION'

##################################################
# Decolators
class check_WD(GuardStateDecorator):
    '''Decorator to check watchdoc of payload'''
    def pre_exec(self):
        if vislib.is_WD_tripped(OPTIC, payload=True) or vislib.is_DGWD_tripped(OPTIC,payload=True):
            if sustype == 'TypeBp':
                return 'TRIPPED'
            else:
                return 'PAY_TRIPPED'

class check_TWWD(GuardStateDecorator):
    '''Decorator to check watchdoc of tower part.'''
    def pre_exc(self):
        if vislib.is_WD_tripped(OPTIC, payload=False) or vislib.is_DGWD_tripped(OPTIC,payload=False):
            return 'TRIPPED'
            # if sustype == 'TypeBp':
            #     return 'TRIPPED'
            # else:
            #     return 'TW_TRIPPED'


class check_OL(GuardStateDecorator):
    '''Decorator to check rms of OpLev signal'''
    def pre_exec(self):
        if vislib.is_OL_lost(OPTIC):
            return 'PAY_LOCALDAMPED'
        elif vislib.is_OL_insane(OPTIC):
            return 'TM_OLDAMPED'

class check_ISCSIG(GuardStateDecorator):
    '''Decorator to check iscsignal'''
    def pre_exec(self):
        if sustype == 'TypeA':
            if ezca['VIS-%s_ISCWD_WDMON_BLOCK'%OPTIC]:
                kagralib.speak_aloud('%s ISC watchdog has tripped.'%OPTIC)
                return 'REMOVE_ISCSIG'

##################################################
# Common guardian state
def engage_main(self):
    self.counter = 0
    self.timer['waiting'] = 0
    for DoF in self.DoFs:
        if self.initialization:
            kagralib.init_FB(
                self.chanfunc(OPTIC,DoF,self.stage),
                gain = [0,self.gain][self.integrator],
                limit = 60000,
                engaged_FM = self.init_FM[DoF],
                clear_history=(not self.integrator),
                hold_offset=True,
                disable_input=self.integrator)

def engage_run(self):
    return all([kagralib.engage_FB(self,self.chanfunc(OPTIC,DoF,self.stage),
                                   FM_list=self.bst_FM[DoF],
                                   gain=self.gain,
                                   ramptime=self.ramptime,
                                   integrate=self.integrator,
                                   initialization=self.initialization,
                               ) for DoF in self.DoFs])



class engage_damping(GuardState):
    def __init__(self, logfunc, chanfunc, stage, init_FM, bst_FM, ramptime, integrator, initialization=True):
        super(engage_damping, self).__init__(logfunc)
        self.chanfunc = chanfunc
        self.stage = stage
        self.DoFs = init_FM.keys()
        self.init_FM = init_FM
        self.bst_FM = bst_FM
        self.gain = 1
        self.ramptime = ramptime
        self.integrator = integrator
        self.initialization = initialization

    @check_TWWD
    def main(self):
        engage_main(self)

    @check_TWWD
    def run(self):
        return engage_run(self)

# Due to the difference of WDs to be checked, we need another class for Payload.
class engage_damping_for_PAY(GuardState):
    def __init__(self, logfunc, chanfunc, stage, init_FM, bst_FM, ramptime, integrator, initialization=True):
        super(engage_damping_for_PAY, self).__init__(logfunc)
        self.chanfunc = chanfunc
        self.stage = stage
        self.DoFs = init_FM.keys()
        self.init_FM = init_FM
        self.bst_FM = bst_FM
        self.gain = 1
        self.ramptime = ramptime
        self.integrator = integrator
        self.initialization = initialization


    @check_TWWD
    @check_WD
    def main(self):
        engage_main(self)

    @check_TWWD
    @check_WD
    def run(self):
        return engage_run(self)


class disable_damping_for_PAY(GuardState):
    def __init__(self, logfunc, chanfunc, stage, bst_FM, ramptime, integrator, zero_gain=True, wait=True):
        super(disable_damping_for_PAY, self).__init__(logfunc)
        self.chanfunc = chanfunc
        self.stage = stage
        self.DoFs = bst_FM.keys()
        self.bst_FM = bst_FM
        self.ramptime = ramptime
        self.integrator = integrator
        self.zero_gain = zero_gain
        self.wait = wait

    @check_WD
    @check_TWWD
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    @check_WD
    @check_TWWD
    def run(self):
        return all([kagralib.disable_FB(self,self.chanfunc(OPTIC,DoF,self.stage),FM_list=self.bst_FM[DoF],ramptime=self.ramptime,integrate=self.integrator,zero_gain=self.zero_gain,wait=self.wait) for DoF in self.DoFs])

class disable_damping(GuardState):
    def __init__(self, logfunc, chanfunc, stage, bst_FM, ramptime, integrator, zero_gain=True, wait=True):
        super(disable_damping, self).__init__(logfunc)
        self.chanfunc = chanfunc
        self.stage = stage
        self.DoFs = bst_FM.keys()
        self.bst_FM = bst_FM
        self.ramptime = ramptime
        self.integrator = integrator
        self.zero_gain = zero_gain
        self.wait = wait

    @check_TWWD
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    @check_TWWD
    def run(self):
        return all([kagralib.disable_FB(self,self.chanfunc(OPTIC,DoF,self.stage),FM_list=self.bst_FM[DoF],ramptime=self.ramptime,integrate=self.integrator, zero_gain=self.zero_gain, wait=self.wait) for DoF in self.DoFs])


##################################################
# State Definitions
class INIT(GuardState):
    request = False
    pass

class TRIPPED(GuardState):
    request = False
    def main(self):
        notify("please restart WatchDog!")
        self.timer['speak'] = 10


    def run(self):
        lib.all_off_quick(self,optic)
        ezca['VIS-'+optic+'_PAY_MASTERSWITCH'] = 'OFF'
        ezca['VIS-'+optic+'_MASTERSWITCH'] = 'OFF'

        kagralib.speak_aloud(optic+' watchdog has tripped')
        kagralib.speak_aloud('Please check the status of '+optic)

        return not (lib.is_pay_tripped(optic,par.BIO_PAY) or lib.is_twr_tripped(optic,par.BIO_TWR))


class TWR_TRIPPED(GuardState):
    request = False
    pass


class SAFE(GuardState):
    index = 0
    request = True
    pass

class REMOVE_TWR_DC(GuardState):
    pass

class TWR_IDLE(GuardState):
    index = 1
    request = True

    def main(self):
        ezca['VIS-%s_MASTERSWITCH'%OPTIC] = 1

    def run(self):
        return True

class ENGAGE_IP_LOCALDAMP(engage_damping):
    index = 2
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_IP_LOCALDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.IPDamp,
            stage = None,
            init_FM = sysmod.IP_LOCALDAMP['init_FM'],
            bst_FM = sysmod.IP_LOCALDAMP['bst_FM'],
            ramptime = sysmod.IP_LOCALDAMP['ramptime'],
            integrator = sysmod.IP_LOCALDAMP['integrator']
        )

class ENGAGE_GAS_LOCALDAMP(engage_damping):
    index = 3
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_GAS_LOCALDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.GASDamp,
            stage = None,
            init_FM = sysmod.GAS_LOCALDAMP['init_FM'],
            bst_FM = sysmod.GAS_LOCALDAMP['bst_FM'],
            ramptime = sysmod.GAS_LOCALDAMP['ramptime'],
            integrator = sysmod.GAS_LOCALDAMP['integrator']
        )

class ENGAGE_BF_LOCALDAMP(engage_damping):
    index = 4
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_BF_LOCALDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.LocalDamp,
            stage = 'BF',
            init_FM = sysmod.BF_LOCALDAMP['init_FM'],
            bst_FM = sysmod.BF_LOCALDAMP['bst_FM'],
            ramptime = sysmod.BF_LOCALDAMP['ramptime'],
            integrator = sysmod.BF_LOCALDAMP['integrator']
        )

    def main(self):
        super(ENGAGE_BF_LOCALDAMP,self).main()
        self.counter = 0
        self.timer['waiting'] = 0

    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            if super(ENGAGE_BF_LOCALDAMP,self).run():
                self.timer['waiting'] = 2
                self.counter += 1

        elif self.counter == 1:
            # if NOMINAL_BF_OFS is defined, put that number to BF TEST Y. This is for PRM.
            try:
                log('put BF nominal offset if defined.')
                filt = ezca.get_LIGOFilter('VIS-%s_BF_TEST_Y'%OPTIC)
                filt.ramp_offset(0,0,True)
                filt.ramp_gain(1,0,True)
                filt.turn_on('OFFSET')
                filt.ramp_offset(sysmod.NOMINAL_BF_OFS,sysmod.TRAMP_BF_OFS,False)
                self.counter += 1
            except:
                return True

        elif self.counter == 2:
            filt = ezca.get_LIGOFilter('VIS-%s_BF_TEST_Y'%OPTIC)
            return not filt.is_offset_ramping()




class TWR_DAMPED(GuardState):
    index = 50
    request = True

    def main(self):
        if sustype == 'TypeB':
            ezca['VIS-%s_IM_DAMPMODE_LOAD_MATRIX'%OPTIC] = 1

    @check_TWWD
    def run(self):
        return True


class ENGAGE_MN_LOCALDAMP(engage_damping_for_PAY):
    index = 60
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_MN_LOCALDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.LocalDamp,
            stage = 'MN',
            init_FM = sysmod.MN_LOCALDAMP['init_FM'],
            bst_FM = sysmod.MN_LOCALDAMP['bst_FM'],
            ramptime = sysmod.MN_LOCALDAMP['ramptime'],
            integrator = sysmod.MN_LOCALDAMP['integrator']
        )



class ENGAGE_IM_LOCALDAMP(engage_damping_for_PAY):
    index = 70
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_IM_LOCALDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.LocalDamp,
            stage = 'IM',
            init_FM = sysmod.IM_LOCALDAMP['init_FM'],
            bst_FM = sysmod.IM_LOCALDAMP['bst_FM'],
            ramptime = sysmod.IM_LOCALDAMP['ramptime'],
            integrator = sysmod.IM_LOCALDAMP['integrator']
        )


class PAY_LOCALDAMPED(GuardState):
    index = 100
    request = True

    @check_WD
    @check_TWWD
    def run(self):
        return True

class MISALIGNING(GuardState):
    index = 101
    request = False

    @check_TWWD
    @check_WD
    def main(self):
        self.ofschan = ezca.get_LIGOFilter(sysmod.MISALIGN_CHAN)
        self.ofschan.turn_on('OFFSET')
        self.ofschan.ramp_offset(sysmod.MISALIGN_OFFSET, sysmod.MISALIGN_TRAMP, False)
        self.ofschan.ramp_gain(1, sysmod.MISALIGN_TRAMP, False)

    @check_TWWD
    @check_WD
    def run(self):
        return not self.ofschan.is_offset_ramping()

class MISALIGNED(GuardState):
    index = 102
    request = True

    @check_TWWD
    @check_WD
    def main(self):
        if sustype in ['TypeA','TypeB','TypeBp']: # by Miyo
            for suffix in ['P','T']: 
                fec = cdslib.ezca_get_dcuid('K1VIS'+OPTIC+suffix)
                sdflib.restore(fec,'misaligned')
        else:
            fec = cdslib.ezca_get_dcuid('K1VIS'+OPTIC)
            sdflib.restore(fec,'misaligned')
        
        kagralib.speak_aloud('%s is misaligned'%(OPTIC))

    def run(self):
        return True

class REALIGNING(GuardState):
    index = 103
    request = False

    @check_TWWD
    @check_WD
    def main(self):
        self.ofschan = ezca.get_LIGOFilter(sysmod.MISALIGN_CHAN)
        self.ofschan.ramp_offset(0, sysmod.MISALIGN_TRAMP, False)

    @check_TWWD
    @check_WD
    def run(self):
        return not self.ofschan.is_offset_ramping()


class ENGAGE_OLSERVO(engage_damping_for_PAY):
    index = 105
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_OLSERVO, self).__init__(
            logfunc,
            chanfunc = vislib.OLServo,
            stage = 'TM',
            init_FM = sysmod.OLSERVO['init_FM'],
            bst_FM = sysmod.OLSERVO['bst_FM'],
            ramptime = sysmod.OLSERVO['ramptime'],
            integrator = sysmod.OLSERVO['integrator'],
            )

'''
class CHECK_TM_ANGLE(GuardState):
    index = 105
    request = False

    @check_WD
    @check_TWWD
    def main(self):
        self.timer['speak'] = 60

    @check_WD
    @check_TWWD
    def run(self):
        is_too_far = any([abs(ezca[vislib.DiagChan(OPTIC, DoF)] - vislib.OLSet(OPTIC,DoF).OUT16.get()) > sysmod.THRED_DISTANCE_SET2CURRENT for DoF in ['PIT','YAW']])
        if is_too_far and self.timer['speak']:
            kagralib.speak_aloud('%s cannot engage optical lever servo, since %s is too far from setpoint. Change the setpoint or align by yourself first.'%(OPTIC,OPTIC))
            self.timer['speak'] = 120

        is_outrange = any([(abs(ezca['VIS-%s_TM_OPLEV_%s_SEG%d_INMON'%(OPTIC,Type,ii+1)]) < 50) for ii in range(4) for Type in ['TILT','LEN']])
        log(is_outrange)
        if is_outrange and self.timer['speak']:
            kagralib.speak_aloud('%s cannot engage optical lever servo, since %s is out of optical lever range. Align by yourself first.'%(OPTIC,OPTIC))
            self.timer['speak'] = 120

        return not any([is_too_far, is_outrange])
'''


class ENGAGE_MN_MNOLDAMP(engage_damping_for_PAY):
    index = 110
    request = False

    def __init__(self,logfunc=None):
        super(ENGAGE_MN_MNOLDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.MNOLDamp,
            stage = 'MN',
            init_FM = sysmod.MN_MNOLDAMP['init_FM'],
            bst_FM = sysmod.MN_MNOLDAMP['bst_FM'],
            ramptime = sysmod.MN_MNOLDAMP['ramptime'],
            integrator = sysmod.MN_MNOLDAMP['integrator']
        )


class ENGAGE_MN_OLDAMP(engage_damping_for_PAY):
    index = 120
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_MN_OLDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.OLDamp,
            stage = 'MN',
            init_FM = sysmod.MN_OLDAMP['init_FM'],
            ramptime = sysmod.MN_OLDAMP['ramptime'],
            bst_FM = sysmod.MN_OLDAMP['bst_FM'],
            integrator = sysmod.MN_OLDAMP['integrator'],
        )

class ENGAGE_BF_OLDAMP(GuardState):
    index = 129
    request = False

    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            ezca.get_LIGOFilter('VIS-%s_BF_OLDAMP_L'%OPTIC).ramp_gain(1,2)
            self.counter += 1
            self.timer['waiting'] = 2

        else:
            return True


class ENGAGE_IM_OLDAMP(engage_damping_for_PAY):
    index = 130
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_IM_OLDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.OLDamp,
            stage = 'IM',
            init_FM = sysmod.IM_OLDAMP['init_FM'],
            bst_FM = sysmod.IM_OLDAMP['bst_FM'],
            ramptime = sysmod.IM_OLDAMP['ramptime'],
            integrator = sysmod.IM_OLDAMP['integrator'],
        )


class ENGAGE_TM_OLDAMP(engage_damping_for_PAY):
    index = 140
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_TM_OLDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.OLDamp,
            stage = 'TM',
            init_FM = sysmod.TM_OLDAMP['init_FM'],
            bst_FM = sysmod.TM_OLDAMP['bst_FM'],
            ramptime = sysmod.TM_OLDAMP['ramptime'],
            integrator = sysmod.TM_OLDAMP['integrator'],
        )

class ENGAGE_BPCOMB(GuardState):
    index = 160
    request = False

    @check_WD
    @check_TWWD
    def main(self):
        for ii in range(24):
            vislib.config_BPCOMB_from_description(optic = OPTIC, DOFNUM = ii+1,
                                           onSW = [1,2,3],TRAMP = 3, LIMIT = 15000)
        self.timer['waiting'] = 3

    @check_WD
    @check_TWWD
    def run(self):
        return self.timer['waiting']

class OLDAMPED(GuardState):
    index = 300
    request = True

    @check_WD
    @check_TWWD
    def run(self):
        return True

class ENGAGE_MN_MNOLDC(engage_damping_for_PAY):
    index = 310
    request = False

    def __init__(self,logfunc=None):
        super(ENGAGE_MN_MNOLDC, self).__init__(
            logfunc,
            chanfunc = vislib.MNOLDamp,
            stage = 'MN',
            init_FM = sysmod.MN_MNOLDAMP['init_FM'],
            bst_FM = sysmod.MN_MNOLDAMP['DC_FM'],
            ramptime = sysmod.MN_MNOLDAMP['ramptime'],
            integrator = False,
            initialization = False
        )


class ENGAGE_MN_OLDC(engage_damping_for_PAY):
    index = 320
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_MN_OLDC, self).__init__(
            logfunc,
            chanfunc = vislib.OLDamp,
            stage = 'MN',
            init_FM = sysmod.MN_OLDAMP['DC_FM'],
            bst_FM = sysmod.MN_OLDAMP['DC_FM'],
            ramptime = sysmod.MN_OLDAMP['ramptime'],
            integrator = False,
            initialization = False,
        )

class ENGAGE_IM_OLDC(engage_damping_for_PAY):
    index = 330
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_IM_OLDC, self).__init__(
            logfunc,
            chanfunc = vislib.OLDamp,
            stage = 'IM',
            init_FM = sysmod.IM_OLDAMP['DC_FM'],
            bst_FM = sysmod.IM_OLDAMP['DC_FM'],
            ramptime = sysmod.IM_OLDAMP['ramptime'],
            integrator = False,
            initialization = False
        )


class ENGAGE_TM_OLDC(engage_damping_for_PAY):
    index = 340
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_TM_OLDC, self).__init__(
            logfunc,
            chanfunc = vislib.OLDamp,
            stage = 'TM',
            init_FM = None,
            bst_FM = sysmod.TM_OLDAMP['DC_FM'],
            ramptime = sysmod.TM_OLDAMP['ramptime'],
            integrator = False,
            initialization = False
        )

class ENGAGE_OLSERVO_DC(engage_damping_for_PAY):
    index = 350
    request = False
    def __init__(self,logfunc=None):
        super(ENGAGE_OLSERVO_DC, self).__init__(
            logfunc,
            chanfunc = vislib.OLServo,
            stage = 'TM',
            init_FM = sysmod.OLSERVO['init_FM'],
            bst_FM = sysmod.OLSERVO['DC_FM'],
            ramptime = sysmod.OLSERVO['ramptime'],
            integrator = sysmod.OLSERVO['integrator'],
            initialization = False
            )
    @check_OL
    def main(self):
        return super(ENGAGE_OLSERVO_DC,self).main()

    @check_OL
    def run(self):
        return super(ENGAGE_OLSERVO_DC,self).run()

class ALIGNED(GuardState):
    index = 500
    request = True

    @check_WD
    @check_TWWD
    @check_ISCSIG
    def main(self):
        #[FIXME] temporally use only for TypeA
        if sustype in []:
            for DoF in ['PIT','YAW']:
                OPAL = vislib.OpticAlign(optic=OPTIC,DOF=DoF,)
                if OPAL.OUTPUT.get() == 0:
                    OPAL.ramp_offset(0,0,False)
                    OPAL.ramp_gain(1,0,False)
                    OPAL.turn_on('OFFSET')

            vislib.offload2OPAL(self, OPTIC, gain=sysmod.offload_gain, functype='main')
        if sustype in ['TypeA','TypeB','TypeBp']: # by Miyo
            for suffix in ['P','T']: 
                fec = cdslib.ezca_get_dcuid('K1VIS'+OPTIC+suffix)
                sdflib.restore(fec,'aligned')
        else:
            fec = cdslib.ezca_get_dcuid('K1VIS'+OPTIC)
            sdflib.restore(fec,'aligned')
            

    @check_WD
    @check_TWWD
    @check_ISCSIG
    def run(self):
        if sustype in []:
            try:
                vislib.offload2OPAL(self, OPTIC, gain=sysmod.offload_gain, functype='run')
            except:
                vislib.offload2OPAL(self, OPTIC, gain=sysmod.offload_gain, functype='main')

        return True


class TRANSIT_TO_LOCKACQ(GuardState):
    index = 510
    request = False
    pass

class REMOVE_ISCSIG(GuardState):
    index = 799
    request = False

    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0
        self.timer['ISC_input_checker'] = 1
        self.TRAMP = 2.5
        for stage in ['TM','IM','MN']:
            ezca['VIS-%s_%s_ISCRAMPHOLD_TRAMP'%(OPTIC,stage)] = self.TRAMP



    def run(self):
        if not self.timer['waiting']:
            return None

        if self.counter == 0:
            for DoF in ['LEN','PIT','YAW']:
                vislib.ISCINF(OPTIC, DOF = DoF).turn_off('INPUT')
                self.timer['waiting'] = 0.3
            self.counter += 1

        elif self.counter == 1:
            for DoF in ['LEN','PIT','YAW']:
                for stage in ['MN','IM','TM']:
                    vislib.Lock(OPTIC, DOF = DoF, stage = stage).RSET.put(2)

            self.counter += 1

        elif self.counter == 2:
            ezca['VIS-%s_ISCWD_RESET'%OPTIC] = 1
            time.sleep(0.5)
            ezca['VIS-%s_ISCWD_RESET'%OPTIC] = 0
            self.timer['waiting'] =2
            self.counter += 1

        elif self.counter == 3:
            if ezca['VIS-%s_ISCWD_WDMON_BLOCK'%OPTIC]:
                self.counter -= 1
            else:
                return True







class LOCK_ACQUISITION(GuardState):
    index = 800
    request = True

    @check_TWWD
    @check_WD
    @check_ISCSIG
    def run(self):
        return True

class TRANSIT_TO_OBS(GuardState):
    index = 810
    request = False
    pass

class OBSERVATION(GuardState):
    index = 1000
    request = True

    @check_TWWD
    @check_WD
    @check_ISCSIG
    def run(self):
        return True


class BACK_TO_LOCKACQ(GuardState):
    index = 990
    request = False
    pass


class BACK_TO_ALIGNED(GuardState):
    index = 790
    request = False
    pass




class DISABLE_OLSERVO_DC(disable_damping_for_PAY):
    index = 490
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_OLSERVO_DC, self).__init__(
            logfunc,
            chanfunc = vislib.OLServo,
            stage = 'TM',
            bst_FM = sysmod.OLSERVO['DC_FM'],
            ramptime = sysmod.OLSERVO['ramptime'],
            integrator = sysmod.OLSERVO['integrator'],
            zero_gain = False,
            wait = True
            )



class DISABLE_TM_OLDC(disable_damping_for_PAY):
    index = 480
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_TM_OLDC, self).__init__(
            logfunc,
            chanfunc = vislib.OLDamp,
            stage = 'TM',
            bst_FM = sysmod.TM_OLDAMP['DC_FM'],
            ramptime = sysmod.TM_OLDAMP['ramptime'],
            integrator = sysmod.TM_OLDAMP['integrator'],
            zero_gain = False,
            wait = True,
            )

class DISABLE_IM_OLDC(disable_damping_for_PAY):
    index = 470
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_IM_OLDC, self).__init__(
            logfunc,
            chanfunc = vislib.OLDamp,
            stage = 'IM',
            bst_FM = sysmod.IM_OLDAMP['DC_FM'],
            ramptime = sysmod.IM_OLDAMP['ramptime'],
            integrator = sysmod.IM_OLDAMP['integrator'],
            zero_gain = False,
            wait = True,
            )


class DISABLE_MN_OLDC(disable_damping_for_PAY):
    index = 460
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_MN_OLDC, self).__init__(
            logfunc,
            chanfunc = vislib.OLDamp,
            stage = 'MN',
            bst_FM = sysmod.MN_OLDAMP['DC_FM'],
            ramptime = sysmod.MN_OLDAMP['ramptime'],
            integrator = sysmod.MN_OLDAMP['integrator'],
            zero_gain = False,
            wait = True,
        )


class DISABLE_MN_MNOLDC(disable_damping_for_PAY):
    index = 450
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_MN_MNOLDC, self).__init__(
            logfunc,
            chanfunc = vislib.MNOLDamp,
            stage = 'MN',
            bst_FM = sysmod.MN_MNOLDAMP['DC_FM'],
            ramptime = sysmod.MN_MNOLDAMP['ramptime'],
            integrator = sysmod.MN_MNOLDAMP['integrator'],
            zero_gain = False,
            wait = True,
        )


class DISABLE_BPCOMB(GuardState):
    index = 295
    request = False

    @check_WD
    @check_TWWD
    def main(self):
        vislib.disable_BPCOMB(OPTIC)
        self.timer['waiting'] = 3

    @check_WD
    @check_TWWD
    def run(self):
        return self.timer['waiting']


class DISABLE_TM_OLDAMP(disable_damping_for_PAY):
    index = 280
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_TM_OLDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.OLDamp,
            stage = 'TM',
            bst_FM = sysmod.TM_OLDAMP['bst_FM'],
            ramptime = sysmod.TM_OLDAMP['ramptime'],
            integrator = sysmod.TM_OLDAMP['integrator'],
            wait = True,
            )

class DISABLE_IM_OLDAMP(disable_damping_for_PAY):
    index = 270
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_IM_OLDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.OLDamp,
            stage = 'IM',
            bst_FM = sysmod.IM_OLDAMP['bst_FM'],
            ramptime = sysmod.IM_OLDAMP['ramptime'],
            integrator = sysmod.IM_OLDAMP['integrator'],
            wait = True,
            )


class DISABLE_MN_OLDAMP(disable_damping_for_PAY):
    index = 260
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_MN_OLDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.OLDamp,
            stage = 'MN',
            bst_FM = sysmod.MN_OLDAMP['bst_FM'],
            ramptime = sysmod.MN_OLDAMP['ramptime'],
            integrator = sysmod.MN_OLDAMP['integrator'],
        )

class DISABLE_BF_OLDAMP(GuardState):
    index = 259
    request = False

    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    def run(self):
        if not self.timer['waiting']:
            return

        if self.counter == 0:
            ezca.get_LIGOFilter('VIS-%s_BF_OLDAMP_L'%OPTIC).ramp_gain(0,2)
            self.counter += 1
            self.timer['waiting'] = 2

        else:
            return True

class DISABLE_MN_MNOLDAMP(disable_damping_for_PAY):
    index = 250
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_MN_MNOLDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.MNOLDamp,
            stage = 'MN',
            bst_FM = sysmod.MN_MNOLDAMP['bst_FM'],
            ramptime = sysmod.MN_MNOLDAMP['ramptime'],
            integrator = sysmod.MN_MNOLDAMP['integrator'],
            wait = True,
        )


class DISABLE_OLSERVO(disable_damping_for_PAY):
    index = 240
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_OLSERVO, self).__init__(
            logfunc,
            chanfunc = vislib.OLServo,
            stage = 'MN',
            bst_FM = sysmod.OLSERVO['bst_FM'],
            ramptime = sysmod.OLSERVO['ramptime'],
            integrator = sysmod.OLSERVO['integrator'],
        )



class DISABLE_IM_LOCALDAMP(disable_damping_for_PAY):
    index = 90
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_IM_LOCALDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.LocalDamp,
            stage = 'IM',
            bst_FM = sysmod.IM_LOCALDAMP['bst_FM'],
            ramptime = sysmod.IM_LOCALDAMP['ramptime'],
            integrator = sysmod.IM_LOCALDAMP['integrator'],
        )


class DISABLE_MN_LOCALDAMP(disable_damping_for_PAY):
    index = 70
    request = False

    def __init__(self,logfunc=None):
        super(DISABLE_MN_LOCALDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.LocalDamp,
            stage = 'MN',
            bst_FM = sysmod.MN_LOCALDAMP['bst_FM'],
            ramptime = sysmod.MN_LOCALDAMP['ramptime'],
            integrator = sysmod.MN_LOCALDAMP['integrator'],
        )


class DISABLE_BF_LOCALDAMP(disable_damping):
    index = 9
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_BF_LOCALDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.LocalDamp,
            stage = 'BF',
            bst_FM = sysmod.BF_LOCALDAMP['bst_FM'],
            ramptime = sysmod.BF_LOCALDAMP['ramptime'],
            integrator = sysmod.BF_LOCALDAMP['integrator'],
        )

    def main(self):
        super(DISABLE_BF_LOCALDAMP, self).main()
        self.timer['waiting'] = 0
        self.counter = 0

    def run(self):

        if not self.timer['waiting']:
            return

        if self.counter == 0:
            if super(DISABLE_BF_LOCALDAMP, self).run():
                self.timer['waiting'] = 3
                self.counter += 1

        elif self.counter == 1:
            # if NOMINAL_BF_OFS is defined, remove from BF TEST Y. This is for PRM.
            try:
                log('remove BF nominal offset')
                filt = ezca.get_LIGOFilter('VIS-%s_BF_TEST_Y'%OPTIC)
                filt.ramp_offset(0,sysmod.TRAMP_BF_OFS,False)
                self.counter += 1
            except:
                return True

        elif self.counter == 2:
            filt = ezca.get_LIGOFilter('VIS-%s_BF_TEST_Y'%OPTIC)
            return not filt.is_offset_ramping()



class DISABLE_GAS_LOCALDAMP(disable_damping_for_PAY):
    index = 8
    request = False
    def __init__(self,logfunc=None):
        super(DISABLE_GAS_LOCALDAMP, self).__init__(
            logfunc,
            chanfunc = vislib.GASDamp,
            stage = None,
            bst_FM = sysmod.GAS_LOCALDAMP['bst_FM'],
            ramptime = sysmod.GAS_LOCALDAMP['ramptime'],
            integrator = sysmod.GAS_LOCALDAMP['integrator'],
        )


class DISABLE_IP_LOCALDAMP(disable_damping_for_PAY):
    index = 7
    request = False
    pass

class CALMDOWN(GuardState):
    request = True
    pass

#############
# COIL BALANCE
# add by K. TANAKA on 21 Jul 2020
#############

def coil_engage_main(self):
    self.counter = 0
    self.timer['waiting'] = 0

    fotonfile = '/opt/rtcds/kamioka/k1/chans/K1VIS%sP.txt'%OPTIC



     ##### Define logger
    dt_now = datetime.now()
    year = dt_now.year
    month = dt_now.month
    day = dt_now.day
    hour = dt_now.hour
    minute = dt_now.minute

    log_dir = '/users/Measurements/VIS/%s/coil_balance/log/'%OPTIC
    date_str = '%d%s%s_%s%s'%(year,str(month).zfill(2),str(day).zfill(2),str(hour).zfill(2),str(minute).zfill(2))
    log_file = log_dir + '/archives/balanceCOILOUTF_%s_'%OPTIC + date_str + '.log'
    #logging.basicConfig(filename=log_file,level=logging.DEBUG)
    logger = logging.getLogger('flogger')
    logger.setLevel(logging.DEBUG)
    handler=logging.StreamHandler()
    logger.addHandler(handler)
    handler=logging.FileHandler(filename=log_file)
    logger.addHandler(handler)

    # define sign of coilout
    if self.stage == 'TM':
        coil_gain = balanceCOILOUTF_TypeA.SIGN_TM_COILOUT(self.optic,logger)
    else:
        coil_gain = balanceCOILOUTF_TypeA.SIGN_MNIM_COILOUT(self.optic,self.stage,logger)

    for coil in self.coils:

        gg,avgI,avgQ,stdI,stdQ = balanceCOILOUTF_TypeA.Balancing(
            self.optic,
            self.stage,
            coil,
            self.freq[coil],
            self.oscAMP[coil],
            coil_gain,
            self.sweeprange,
            logger
            )



        ### fitting
        pI = np.polyfit(gg,avgI,1)
        pQ = np.polyfit(gg,avgQ,1)
        pGAIN = float(pI[1])/float(pI[0])*(-1) # final gain of the balanced coil

        logger.debug('fitresult with a*gain + b:')
        logger.debug('-I (a,b) = (%f,%f)'%(pI[0],pI[1]))
        logger.debug('-Q (a,b) = (%f,%f)'%(pQ[0],pQ[1]))
        logger.debug('%s BALANCED GAIN = %f'%(coil,pGAIN))
        logger.debug('put %f in VIS-%s_%s_COILOUTF_%s_GAIN'%(pGAIN, self.optic, self.stage, coil))
        ezca['VIS-%s_%s_COILOUTF_%s_GAIN'%(self.optic, self.stage, coil)] = pGAIN

        ### plot results
        plt.close()
        plt.scatter(gg,avgI,label="I")
        plt.scatter(gg,avgQ,color='red',label="Q")
        plt.plot(gg,np.polyval(pI,gg))
        plt.plot(gg,np.polyval(pQ,gg))
        plt.grid()

        plt.title(date_str)
        plt.xlabel('%s_%s_COILOUTF_%s_GAIN'%(self.optic, self.stage, coil))
        plt.ylabel('Amplitude of demodulated signal')
        plt.legend()

        plt.savefig(log_dir+'archives/balanceCOILOUTF_%s_'%(self.optic) + date_str +'_%s_%s'%(self.stage,coil)+'.png')
        plt.savefig(log_dir+'balanceCOILOUTF_%s_%s_%s_latest'%(self.optic,self.stage,coil)+'.png')

        self.timer['waiting'] = 3

        ## Turn off excitation when finish the measuremetn
        ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_CLKGAIN'%self.optic] = 0
        time.sleep(ezca['VIS-%s_PAY_OLSERVO_LKIN_OSC_TRAMP'%self.optic])

        self.timer['waiting'] = 3

    os.system('cp %s %s'%(log_file,(log_dir+'balanceCOILOUTF_%s_latest.log'%(self.optic))))
    balanceCOILOUTF_TypeA.ShutdownLOCKIN(self.optic)

    ### show the balanced date on Type-A medm screen
    ezca['VIS-%s_%s_COILBAL_DATE_YEAR'%(self.optic,self.stage)] = year
    ezca['VIS-%s_%s_COILBAL_DATE_MON'%(self.optic,self.stage)]  = month
    ezca['VIS-%s_%s_COILBAL_DATE_DAY'%(self.optic,self.stage)]  = day
    ezca['VIS-%s_%s_COILBAL_DATE_HOUR'%(self.optic,self.stage)] = hour
    ezca['VIS-%s_%s_COILBAL_DATE_MIN'%(self.optic,self.stage)]  = minute

    kagralib.speak_aloud('%s %s coils are balanced'%(self.optic,self.stage))
    self.timer['waiting'] = 3

def coil_engage_run(self):
    return self.timer['waiting']


class COIL_BALANCED(GuardState):
    index = 75
    request = True

    @check_TWWD
    @check_WD



    def run(self):
        return True

class engage_coil_balance(GuardState):
    def __init__(self,logfunc,optic,stage,coils,freq,oscAMP,sweeprange,Np=10,avgDuration=10,settleDuration=30,oscTRAMP=10):
        super(engage_coil_balance,self).__init__(logfunc)
        self.optic = OPTIC
        self.stage = stage
        self.coils = coils
        self.freq = freq
        self.oscAMP = oscAMP
        #self.coil_gain = coil_gain
        self.sweeprange = sweeprange



    @check_WD
    @check_TWWD
    def main(self):
        coil_engage_main(self)


    @check_WD
    @check_TWWD
    def run(self):
        return coil_engage_run(self)

class MN_COIL_BALANCING(engage_coil_balance):
    index = 72
    request = False
    def __init__(self, logfunc=None):
        super(MN_COIL_BALANCING,self).__init__(
            logfunc,
            optic = OPTIC,
            stage = 'MN',
            coils = sysmod.MN_COIL_BALANCE['coils'],
            freq = sysmod.MN_COIL_BALANCE['freq'],
            oscAMP = sysmod.MN_COIL_BALANCE['oscAMP'],
            #coil_gain = Signcoiloutgain(optic),
            sweeprange = sysmod.MN_COIL_BALANCE['sweeprange'],
            Np = sysmod.MN_COIL_BALANCE['Npoints'],
            avgDuration = sysmod.MN_COIL_BALANCE['duration'],
            settleDuration = sysmod.MN_COIL_BALANCE['SettleDuration'],
            oscTRAMP = sysmod.MN_COIL_BALANCE['oscTRAMP'],
        )

class IM_COIL_BALANCING(engage_coil_balance):
    index = 73
    request = False
    def __init__(self, logfunc=None):
        super(IM_COIL_BALANCING,self).__init__(
            logfunc,
            optic = OPTIC,
            stage = 'IM',
            coils = sysmod.IM_COIL_BALANCE['coils'],
            freq = sysmod.IM_COIL_BALANCE['freq'],
            oscAMP = sysmod.IM_COIL_BALANCE['oscAMP'],
            #coil_gain = Signcoiloutgain(optic),
            sweeprange = sysmod.IM_COIL_BALANCE['sweeprange'],
            Np = sysmod.IM_COIL_BALANCE['Npoints'],
            avgDuration = sysmod.IM_COIL_BALANCE['duration'],
            settleDuration = sysmod.IM_COIL_BALANCE['SettleDuration'],
            oscTRAMP = sysmod.IM_COIL_BALANCE['oscTRAMP'],
        )

class TM_COIL_BALANCING(engage_coil_balance):
    index = 74
    request = False
    def __init__(self, logfunc=None):
        super(TM_COIL_BALANCING,self).__init__(
            logfunc,
            optic = OPTIC,
            stage = 'TM',
            coils = sysmod.TM_COIL_BALANCE['coils'],
            freq = sysmod.TM_COIL_BALANCE['freq'],
            oscAMP = sysmod.TM_COIL_BALANCE['oscAMP'],
            #coil_gain = Signcoiloutgain(optic),
            sweeprange = sysmod.TM_COIL_BALANCE['sweeprange'],
            Np = sysmod.TM_COIL_BALANCE['Npoints'],
            avgDuration = sysmod.TM_COIL_BALANCE['duration'],
            settleDuration = sysmod.TM_COIL_BALANCE['SettleDuration'],
            oscTRAMP = sysmod.TM_COIL_BALANCE['oscTRAMP'],
        )




##################################################
# SUSCHAR
##################################################
class INIT_MON(GuardState):
    request = True
    index = 58

    def main(self):


        # copy INF
        '''
        chans = '/opt/rtcds/kamioka/k1/chans/'
        test = foton.FilterFile(chans+'K1LSC.txt')

        FBs = foton.FilterFile(chans+'K1VIS%sP.txt'%(optic.upper()))
        FBs_MON = foton.FilterFile(chans+'K1VIS%sMON.txt'%(optic.upper()))
        for stage in ['MN','IM']:
            for DoF in ['V1','V2','V3','H1','H2','H3']:
                PSINF_MON = 'VIS-%s_MON_%s_PSINF_%s'%(optic,stage,DoF)
                PSINF = 'VIS-%s_%s_PSINF_%s'%(optic,stage,DoF)
                for char in ['_SW1S','_SW2S','_GAIN']:
                    ezca[PSINF_MON+char] = ezca[PSINF+char]

                for index in range(10):
                    kagralib.copy_FB(FBs,PSINF[4:],FBs_MON,PSINF_MON[4:])
                ezca[PSINF_MON+'_RSET'] = 1
        FBs_MON.write()
        '''





##################################################
# EDGES
##################################################

if sustype == 'TypeB':
    edges = [
        ('INIT','SAFE'),
        ('TRIPPED','SAFE'),
        ('SAFE','MASTERSWITCH_ON'),
        ('MASTERSWITCH_ON','NEUTRAL'),
        ('NEUTRAL','ENGAGING_IP_CONTROL'),
        ('NEUTRAL','MASTERSWITCH_OFF'),
        ('MASTERSWITCH_OFF','SAFE'),
        ('ENGAGING_IP_CONTROL','IP_CONTROL_ENGAGED'),
        ('IP_CONTROL_ENGAGED','DISENGAGING_IP_CONTROL'),
        ('DISENGAGING_IP_CONTROL','NEUTRAL'),
        ('IP_CONTROL_ENGAGED','ENGAGING_GAS_CONTROL'),
        ('ENGAGING_GAS_CONTROL','TWR_DAMPED'),
        ('TWR_DAMPED','DISENGAGING_GAS_CONTROL'),
        ('DISENGAGING_GAS_CONTROL','IP_CONTROL_ENGAGED'),

        ('PAY_TRIPPED','TWR_DAMPED'),

        ('TWR_DAMPED','ENGAGE_IM_LOCALDAMP'),
        ('ENGAGE_IM_LOCALDAMP','PAY_LOCALDAMPED'),
        ('PAY_LOCALDAMPED','DISABLE_IM_LOCALDAMP'),
        ('DISABLE_IM_LOCALDAMP','TWR_DAMPED'),
        ('PAY_LOCALDAMPED','ENGAGE_TM_OLDAMP'),
        # ('PAY_LOCALDAMPED','CHECK_TM_ANGLE'),
        # ('CHECK_TM_ANGLE','PAY_LOCALDAMPED',),
        # ('CHECK_TM_ANGLE','ENGAGE_TM_OLDAMP'),
        ('ENGAGE_TM_OLDAMP','ENGAGE_IM_OLDAMP'),
        ('ENGAGE_IM_OLDAMP','ENGAGE_OLSERVO'),
        ('ENGAGE_OLSERVO','ALIGNED'),
        ('ALIGNED','DISABLE_OLSERVO'),
        ('DISABLE_OLSERVO','DISABLE_IM_OLDAMP'),
        ('DISABLE_IM_OLDAMP','DISABLE_TM_OLDAMP'),
        ('DISABLE_TM_OLDAMP','PAY_LOCALDAMPED'),

        ('ALIGNED','TRANSIT_TO_OBS'),
        ('TRANSIT_TO_OBS','OBSERVATION'),
        ('OBSERVATION','BACK_TO_ALIGNED'),
        ('BACK_TO_ALIGNED','ALIGNED'),

        ('PAY_LOCALDAMPED','MISALIGNING'),
        ('MISALIGNING','MISALIGNED'),
        ('MISALIGNED','REALIGNING'),
        ('REALIGNING','PAY_LOCALDAMPED'),
    ]

elif sustype == 'TypeBp':

    edges = [
        ('INIT','SAFE'),
        ('TRIPPED','SAFE'),
        ('SAFE','TWR_IDLE'),
        ('TWR_IDLE','SAFE'),
        ('TWR_IDLE','ENGAGE_GAS_LOCALDAMP'),
        ('ENGAGE_GAS_LOCALDAMP','ENGAGE_BF_LOCALDAMP'),
        ('ENGAGE_BF_LOCALDAMP','TWR_DAMPED'),
        ('TWR_DAMPED','DISABLE_BF_LOCALDAMP'),
        ('DISABLE_BF_LOCALDAMP','DISABLE_GAS_LOCALDAMP'),
        ('DISABLE_GAS_LOCALDAMP','TWR_IDLE'),

        ('TWR_DAMPED','ENGAGE_IM_LOCALDAMP'),
        ('ENGAGE_IM_LOCALDAMP','PAY_LOCALDAMPED'),
        ('PAY_LOCALDAMPED','DISABLE_IM_LOCALDAMP'),
        ('DISABLE_IM_LOCALDAMP','TWR_DAMPED'),

        ('PAY_LOCALDAMPED','ENGAGE_OLSERVO'),
        ('ENGAGE_OLSERVO','DISABLE_OLSERVO'),
        ('DISABLE_OLSERVO','ENGAGE_OLSERVO'),
        ('DISABLE_OLSERVO','PAY_LOCALDAMPED'),


        ('ENGAGE_OLSERVO','ENGAGE_IM_OLDAMP'),
        ('ENGAGE_IM_OLDAMP','DISABLE_IM_OLDAMP'),
        ('DISABLE_IM_OLDAMP','ENGAGE_IM_OLDAMP'),
        ('DISABLE_IM_OLDAMP','DISABLE_OLSERVO'),

        ('ENGAGE_IM_OLDAMP','ENGAGE_TM_OLDAMP'),
        ('ENGAGE_TM_OLDAMP','DISABLE_TM_OLDAMP'),
        ('DISABLE_TM_OLDAMP','ENGAGE_TM_OLDAMP'),
        ('DISABLE_TM_OLDAMP','DISABLE_IM_OLDAMP'),
        
        ('ENGAGE_TM_OLDAMP','ENGAGE_BF_OLDAMP'),
        ('ENGAGE_BF_OLDAMP','DISABLE_BF_OLDAMP'),
        ('DISABLE_BF_OLDAMP','ENGAGE_BF_OLDAMP'),
        ('DISABLE_BF_OLDAMP','DISABLE_TM_OLDAMP'),

        ('ENGAGE_BF_OLDAMP','OLDAMPED'),
        ('OLDAMPED','DISABLE_BF_OLDAMP'),

        ('OLDAMPED','ENGAGE_IM_OLDC'),
        ('ENGAGE_IM_OLDC','DISABLE_IM_OLDC'),
        ('DISABLE_IM_OLDC','ENGAGE_IM_OLDC'),
        ('DISABLE_IM_OLDC','OLDAMPED'),

        ('ENGAGE_IM_OLDC','ENGAGE_OLSERVO_DC'),
        ('ENGAGE_OLSERVO_DC','DISABLE_OLSERVO_DC'),
        ('DISABLE_OLSERVO_DC','ENGAGE_OLSERVO_DC'),
        ('DISABLE_OLSERVO_DC','DISABLE_IM_OLDC'),

        ('ENGAGE_OLSERVO_DC','ALIGNED'),
        ('ALIGNED','DISABLE_OLSERVO_DC'),

        ('ALIGNED','TRANSIT_TO_LOCKACQ'),
        ('TRANSIT_TO_LOCKACQ','LOCK_ACQUISITION'),
        ('LOCK_ACQUISITION','TRANSIT_TO_OBS'),
        ('TRANSIT_TO_OBS','OBSERVATION'),
        ('OBSERVATION','BACK_TO_LOCKACQ'),
        ('BACK_TO_LOCKACQ','LOCK_ACQUISITION'),
        ('LOCK_ACQUISITION','BACK_TO_ALIGNED'),
        ('BACK_TO_ALIGNED','ALIGNED'),

        ('PAY_LOCALDAMPED','MISALIGNING'),
        ('MISALIGNING','MISALIGNED'),
        ('MISALIGNED','REALIGNING'),
        ('REALIGNING','PAY_LOCALDAMPED'),
    ]

elif sustype == 'TypeA':

    edges = [
    ('INIT','SAFE'),
        ('RESET', 'SAFE'),
        ('TRIPPED','SAFE'),
        ('PAY_TRIPPED','TWR_DAMPED'),
        ('SAFE','OUTPUT_ON'),
        ('OUTPUT_ON','UNDAMPED'),
        ('UNDAMPED','ENGAGE_TWR_DAMPING'),
        ('ENGAGE_TWR_DAMPING','TWR_DAMPED'),
        ('TWR_DAMPED','DISABLE_TWR_DAMPING'),
        ('DISABLE_TWR_DAMPING','UNDAMPED'),
        ('UNDAMPED','SAFE'),

        ('TWR_DAMPED','ENGAGE_MN_LOCALDAMP'),
        ('ENGAGE_MN_LOCALDAMP','PAY_LOCALDAMPED'),
        ('PAY_LOCALDAMPED','DISABLE_MN_LOCALDAMP'),
        ('DISABLE_MN_LOCALDAMP','TWR_DAMPED'),
        #MNMNOLDAMP
        ('PAY_LOCALDAMPED','ENGAGE_MN_MNOLDAMP'),
        ('ENGAGE_MN_MNOLDAMP','DISABLE_MN_MNOLDAMP'),
        ('DISABLE_MN_MNOLDAMP','ENGAGE_MN_MNOLDAMP'),
        ('DISABLE_MN_MNOLDAMP','PAY_LOCALDAMPED'),
        #MNOLDAMP
        ('ENGAGE_MN_MNOLDAMP','ENGAGE_MN_OLDAMP'),
        ('ENGAGE_MN_OLDAMP','DISABLE_MN_OLDAMP'),
        ('DISABLE_MN_OLDAMP','ENGAGE_MN_OLDAMP'),
        ('DISABLE_MN_OLDAMP','DISABLE_MN_MNOLDAMP'),
        #IMOLDAMP
        ('ENGAGE_MN_OLDAMP','ENGAGE_IM_OLDAMP'),
        ('ENGAGE_IM_OLDAMP','DISABLE_IM_OLDAMP'),
        ('DISABLE_IM_OLDAMP','ENGAGE_IM_OLDAMP'),
        ('DISABLE_IM_OLDAMP','DISABLE_MN_OLDAMP'),
        #TMOLDAMP
        ('ENGAGE_IM_OLDAMP','ENGAGE_TM_OLDAMP'),
        ('ENGAGE_TM_OLDAMP','DISABLE_TM_OLDAMP'),
        ('DISABLE_TM_OLDAMP','ENGAGE_TM_OLDAMP'),
        ('DISABLE_TM_OLDAMP','DISABLE_IM_OLDAMP'),
        # BPCOMB
        ('ENGAGE_TM_OLDAMP','ENGAGE_BPCOMB'),
        ('ENGAGE_BPCOMB','DISABLE_BPCOMB'),
        ('DISABLE_BPCOMB','ENGAGE_BPCOMB'),
        ('DISABLE_BPCOMB','DISABLE_TM_OLDAMP'),

        ('ENGAGE_BPCOMB','OLDAMPED'),
        ('OLDAMPED','DISABLE_BPCOMB'),

        ('OLDAMPED','ENGAGE_MN_MNOLDC'),
        ('ENGAGE_MN_MNOLDC','DISABLE_MN_MNOLDC'),
        ('DISABLE_MN_MNOLDC','ENGAGE_MN_MNOLDC'),
        ('DISABLE_MN_MNOLDC','OLDAMPED'),

        ('ENGAGE_MN_MNOLDC','ENGAGE_MN_OLDC'),
        ('ENGAGE_MN_OLDC','DISABLE_MN_OLDC'),
        ('DISABLE_MN_OLDC','ENGAGE_MN_OLDC'),
        ('DISABLE_MN_OLDC','DISABLE_MN_MNOLDC'),

        ('ENGAGE_MN_OLDC','ENGAGE_IM_OLDC'),
        ('ENGAGE_IM_OLDC','DISABLE_IM_OLDC'),
        ('DISABLE_IM_OLDC','ENGAGE_IM_OLDC'),
        ('DISABLE_IM_OLDC','DISABLE_MN_OLDC'),

        ('ENGAGE_IM_OLDC','ALIGNED'),
        ('ALIGNED','DISABLE_IM_OLDC'),
        ('ALIGNED','TRANSIT_TO_LOCKACQ'),
        ('TRANSIT_TO_LOCKACQ','LOCK_ACQUISITION'),
        ('LOCK_ACQUISITION','TRANSIT_TO_OBS'),
        ('TRANSIT_TO_OBS','OBSERVATION'),
        ('OBSERVATION','BACK_TO_LOCKACQ'),
        ('BACK_TO_LOCKACQ','LOCK_ACQUISITION'),
        ('LOCK_ACQUISITION','BACK_TO_ALIGNED'),
        ('BACK_TO_ALIGNED','ALIGNED'),
        ('REMOVE_ISCSIG','LOCK_ACQUISITION'),

        ('PAY_LOCALDAMPED','MISALIGNING'),
        ('MISALIGNING','MISALIGNED'),
        ('MISALIGNED','REALIGNING'),
        ('REALIGNING','PAY_LOCALDAMPED'),
    ]
