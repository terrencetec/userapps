from guardian import GuardState
from guardian import GuardStateDecorator

import vislib

import importlib
import time

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
# Utility functions
##################################################
def is_oplev_outofrange(self):
    #[FIXME] return True if oplev is out of range
    return False

def is_IPoutput_large(self):
    #[FIXME] return True if IP output is close to satulation
    return False

def lost():
    # [FIXME]if suspension is totally off, return True
    return False

def check_fault():
    flag = False
    msg = 'Check ['
    if lost():
        flag = True
        msg += 'suspension status, '
        
    msg += ']'

    return flag,msg

##################################################
# LIGO Filter objects
##################################################
def DCSERVO():
    DCSERVO = {
        'MN': {DoF:ezca.get_LIGOFilter('MOD-%s_OLDC_MN_%s'%(OPTIC,DoF)) for DoF in ['PIT','YAW']},
        'BF': {DoF:ezca.get_LIGOFilter('MOD-%s_OLDC_BF_%s'%(OPTIC,DoF)) for DoF in ['PIT','YAW']},
        'IP': {DoF:ezca.get_LIGOFilter('MOD-%s_IPDC_%s'%(OPTIC,DoF)) for DoF in ['LEN','TRA','YAW']},
        'GAS': {DoF:ezca.get_LIGOFilter('MOD-%s_GASDC_%s'%(OPTIC,DoF)) for DoF in ['F0','F1','F2','F3','BF']},
    }
    return DCSERVO

def DAMPSERVO():
    DAMPSERVO = {
        stage: {DoF: ezca.get_LIGOFilter('MOD-%s_DAMP_%s_%s'%(OPTIC,stage,DoF)) for DoF in ['LEN','TRA','VER','ROL','PIT','YAW']} for stage in ['IP','BF','MN','IM','TM']
    }

    return DAMPSERVO

##################################################
# Decolators
class check_WD(GuardStateDecorator):
    #[FIXME] decorator to check WDs
    def pre_exec(self):
        pass

class is_fault(GuardStateDecorator):
    def pre_exec(self):
        flag, _ = check_fault()
        if flag:
            if ezca['GRD-NEW_%s_STATE'%OPTIC] == 'SAFE':
                return 'FAULT'
            
            ezca['GRD-NEW_%s_REQUEST'%OPTIC] = 'SAFE'
            
        

##################################################
# State Definitions
class INIT(GuardState):
    request = False
    pass

class FAULT(GuardState):
    request = False
    def run(self):
        flag, msg = check_fault()
        if flag:
            notify(msg)
        else:
            return True

class SAFE(GuardState):
    request = True
    index = 1

    def is_output_off(self):
        #[FIXME] check output
        return True

    @is_fault
    def main(self):
        self.timer['speak'] = 0

    @is_fault        
    def run(self):
        if not self.is_output_off():
            notify('CHECK OUTPUT!!!')
            if timer['speak']:
                kagralib.speak_aloud('%s is not safe, although safe state was requested. It has output from some coils. Please check it'%OPTIC)
                self.timer['speak'] = 300

        return True
                
class FLOAT(GuardState):
    request = True
    index = 5
    
    @is_fault
    def run(self):
        return True

class ENGAGE_LOCALDAMP(GuardState):
    request = False
    index = 10
    
    @is_fault
    def main(self):
        self.timer['waiting'] = 0
        self.counter = 0

        self.stagelist = ['IP','BF','MN','IM']

    @is_fault        
    def run(self):
        if not self.timer['waiting']:
            return
        
        if self.counter == 0:
            for stage in self.stagelist:
                for DoF in DAMPSERVO()[stage].keys():
                    DAMPSERVO()[stage][DoF].ramp_gain(1,1,False)
            self.timer['waiting'] = 1
            self.counter += 1

        elif self.counter == 1:
            return True

class ENGAGE_TWRDC(GuardState):
    request = False
    index = 20
    
    @is_fault
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    @is_fault        
    def run(self):
        if not self.timer['waiting']:
            return

        elif self.counter == 0:
            # engage DC servo
            for stage in ['IP',]:
                for key in DCSERVO()[stage].keys():
                    DCSERVO()[stage][key].turn_on('INPUT')
                    
            self.counter += 1
            self.timer['waiting'] = 1

        elif self.counter == 1:
            return True

class DISABLE_TWRDC(GuardState):
    index = 90
    request = False

    @is_fault
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

    @is_fault
    def run(self):
        if not self.timer['waiting']:
            return

        elif self.counter == 0:
            # disable DC servo
            for stage in DCSERVO().keys():
                for key in DCSERVO()[stage].keys():
                    DCSERVO()[stage][key].turn_off('INPUT')

            self.counter += 1
            self.timer['waiting'] = 1

        elif self.counter == 1:
            return True

class DISABLE_LOCALDAMP(GuardState):
    request = False
    index = 80

    @is_fault    
    def main(self):
        self.timer['waiting'] = 0
        self.counter = 0
        
    @is_fault
    def run(self):
        if not self.timer['waiting']:
            return
        
        if self.counter == 0:
            for stage in DAMPSERVO().keys():
                log(stage)
                for DoF in DAMPSERVO()[stage].keys():
                    DAMPSERVO()[stage][DoF].ramp_gain(0,1,False)
            self.timer['waiting'] = 1
            self.counter += 1

        elif self.counter == 1:
            return True
    
    
class CLEAR_DC(GuardState):
    request = False
    index = 3
    
    @is_fault    
    def main(self):
        self.counter = 0
        self.timer['waiting'] = 0

        self.unitTRAMP = 3. # [sec/urad] ramptime for 1 urad when zero output of DC servo when there is output. ex.) if ther is x urad output TRAMP will be x*unitTRAMP
        
    @is_fault    
    def run(self):
        if not self.timer['waiting']:
            return
        
        if self.counter == 0:
            # turn off output with proper ramptime. If there is output, wait until the output get 0
            TRAMP = [0,]
            for stage in DCSERVO().keys():
                for DoF in DCSERVO()[stage].keys():
                    DCSERVO()[stage][DoF].turn_off('INPUT')
                    output = DCSERVO()[stage][DoF].OUTPUT.get()
                    if output:
                        _TRAMP = min([self.unitTRAMP*abs(output),150]) # if output is too large, TRAMP = 150
                        TRAMP.append(_TRAMP)
                        DCSERVO()[stage][DoF].ramp_gain(0,_TRAMP,False)

            self.timer['waiting'] = max(TRAMP)
            self.counter += 1

        elif self.counter == 1:
            for stage in DCSERVO().keys():
                for DoF in DCSERVO()[stage].keys():
                    DCSERVO()[stage][DoF].RSET.put(2)
                    time.sleep(0.1)
                    DCSERVO()[stage][DoF].ramp_gain(1,0,False)
            self.counter += 1

        elif self.counter == 2:
            return True
                    


class LOCALDAMPED(GuardState):
    request = True
    index = 100

    pass

class OBSERVATION(GuardState):
    request = True
    index = 1000

    pass
        
##################################################
# Edges
edges = [('INIT','SAFE'),
         ('FAULT','SAFE'),
         ('SAFE','FLOAT'),
         ('FLOAT','ENGAGE_LOCALDAMP'),
         ('ENGAGE_LOCALDAMP','ENGAGE_TWRDC'),
         ('ENGAGE_TWRDC','LOCALDAMPED'),
         ('LOCALDAMPED','DISABLE_TWRDC'),
         ('DISABLE_TWRDC','DISABLE_LOCALDAMP'),
         ('DISABLE_LOCALDAMP','FLOAT'),
         ('FLOAT','CLEAR_DC'),
         ('CLEAR_DC','SAFE'),
         ]
