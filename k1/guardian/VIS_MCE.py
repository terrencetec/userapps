import time
import math
from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager

##################################################
# initialization values

# initial REQUEST state
request = 'ALIGNED'

# NOMINAL state, which determines when node is OK
nominal = 'ALIGNED'

##################################################

# utility functions

def is_tripped():
        if ezca['VIS-MCE_TM_WDMON_STATE'] != 1:
		return False
	return True

##################################################
# STATE decorators

class watchdog_check(GuardStateDecorator):
    """Decorator to check watchdog"""
    def pre_exec(self):
        if not is_tripped():
            return 'TRIPPED'

##################################################
class INIT(GuardState):
    index = 0
    goto = True

class TRIPPED(GuardState):
    index = 1
    redirect = False
    request = False
    def run(self):
        if is_tripped():
            log("I_am_tripped.")
            return
        log("I_am_tripped.")
        return 'TRIPPED'

class RESET(GuardState):
    index = 20
    goto = True
    request = False
    def main(self):
        log('Turning off the master switch')
        ezca['VIS-MCE_MASTERSWITCH'] = 'OFF'
        return True

class SAFE(GuardState):
    """Safe state is with master switch off not to send any signal"""
    index = 30
    @watchdog_check
    def main(self):
        log('Turning off the master switch')
        ezca['VIS-MCE_MASTERSWITCH'] = 'OFF'
        return True
	
class MASTERSWITCHON(GuardState):
    index = 40
    request = False

    @watchdog_check
    def run(self):
        log('Turning on the master switch')
        ezca['VIS-MCE_MASTERSWITCH'] = 'ON'
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
    ('INIT', 'SAFE'),
    ('RESET', 'SAFE'),
    ('TRIPPED','SAFE'),
    ('SAFE','MASTERSWITCHON'),
    ('MASTERSWITCHON','ALIGNED')
   ]
