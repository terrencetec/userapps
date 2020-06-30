from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import vislib

##################################################
# initialization values

# initial REQUEST state
request = 'INIT'

# NOMINAL state, which determines when node is OK
nominal = 'PRFPMI'

##################################################
nodes = NodeManager(['ETMX','ETMY'])

##################################################
# State definitions
class INIT(GuardState):
    request = False

class PRFPMI_LOCK_ACQUISITION(GuardState):
    request = True

    def main(self):
        self.managing_optics = ['ETMX','ETMY']
        self.LOCK = {optic:{stage:vislib.Lock(optic,'LEN',stage) for stage in ['MN','TM']} for optic in self.managing_optics}
        self.ISCINF = {optic:vislib.ISCINF(optic,'LEN') for optic in self.managing_optics}

    def run(self):
        for optic in self.managing_optics:
            if abs(self.LOCK[optic]['MN'].OUT16.get()) > 25000:
                notify('%s was kicked. Hold output.')
                self.ISCINF[optic].turn_on('HOLD')
                ezca['GRD-VIS_%s_REQUEST'%optic] = 'REMOVE_ISCSIG'
                
                
                
            
        
    

