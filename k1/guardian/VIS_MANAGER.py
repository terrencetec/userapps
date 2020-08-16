#
#! coding:utf-8
from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import vislib
import subprocess

#from slack_util import PostMan

# flags
eq_alert_flag = False
eq_calm_down_flag = False

# initial REQUEST state
request = 'INIT'

# NOMINAL state, which determines when node is OK
nominal = 'ALL_ALIGNED'

# slave optics
optics = ['PR2', 'PR3', 'SR2', 'SR3', 'BS', 'ETMX', 'ITMX', 'ETMY', 'ITMY']
managed_optics = ['ETMX','ETMY','ITMX','ITMY','BS','SRM','SR2','SR3','PRM','PR2','PR3']

nodes = NodeManager(list(map(lambda x:'VIS_'+x,managed_optics)))
            
# ------------------------------------------------------------------------------
def send_to_slack(text):
    ''' Need token. Plase
    '''
    postman = PostMan(token='')
    postman.chat_post(text)
    return True    
    
# ------------------------------------------------------------------------------

def is_used(opt):
    msg = ezca['VIS-'+opt+'_COMMISH_MESSAGE']
    button = ezca['VIS-'+opt+'_COMMISH_STATUS']
    return (msg!='') or button==1

def is_pay_localdamped(opt):
    return ezca['GRD-VIS_'+opt+'_STATE']=='PAY_LOCALDAMPED'

def is_oldamped(opt):
    return ezca['GRD-VIS_'+opt+'_STATE']=='OLDAMPED'

def is_damped(opt):
    return pay_localdamped(opt) or lodamped(opt)

def is_aligned(opt):
    return ezca['GRD-VIS_'+opt+'_STATE']=='ALIGNED' \
        or ezca['GRD-VIS_'+opt+'_STATE']=='OBSERVATION'

def _is_earthquake(seisname):
    '''
    ref [1] https://github.com/MiyoKouseki/kagra-gif/issues/112
    '''
    lolo = ezca['PEM-SEIS_{0}_GND_X_BLRMS_30MHZ100'.format(seisname)]
    low = ezca['PEM-SEIS_{0}_GND_X_BLRMS_100MHZ300'.format(seisname)]
    lolo90 = 2.7e-2 # 90th percentile of the stational seismic noise [1]
    low90 = 5.3e-1 # 90th percentile of the stational seismic noise [1]    
    return lolo>lolo90*10 and low>low90*10
    
def is_earthquake():    
    exv = _is_earthquake('EXV')
    ixv = _is_earthquake('IXV')
    eyv = _is_earthquake('EYV')

    if exv and ixv and eyv:
        return True
    else:
        return False

    
class eq_check(GuardStateDecorator):
    """Decorator to check watchdog"""
    def pre_exec(self):
	if is_earthquake():
            return 'EARTHQUAKE'
        
        
# ------------------------------------------------------------------------------
class INIT(GuardState):
    ''' Initial State of VIS_MANAGER.

    '''
    index = 0
    goto = True
    
    def main(self):
        '''
        '''
        nodes.set_managed()
        log('set_managed')
        return True
    
    
class ALL_ALIGNED(GuardState):
    ''' Request the ALIGNED state for all suspensions.
    
    '''    
    index = 1
    request = True

    @eq_check    
    def main(self):
        ''' All suspensions are requested to ALIGNED.
        '''
        someone_use = []        
        # for opt in optics:
        #     if opt in ['BS','SR2','SR3']:
        #         ezca['GRD-VIS_'+opt+'_REQUEST'] = 'ALIGNED'                    
        #     else:
        #         ezca['GRD-VIS_'+opt+'_REQUEST'] = 'OBSERVATION'
        
    @eq_check
    def run(self):
        '''
        Force to request the ALIGNED state if no one use the suspensions.
        '''
        # 1. Force to aligne the suspension
        someone_use = []        
        for opt in managed_optics:
            if nodes['VIS_'+opt]!='ALIGNED':
                if not is_used(opt):
                    nodes['VIS_'+opt]='ALIGNED' 
            if is_used(opt):
                someone_use += [opt]
        notify('Not managed: {0}'.format(','.join(someone_use)))

        # 2. Revive all stalled nodes
        #   (This may be needed in all State?)
        for node in nodes.get_stalled_nodes():
            node.revive()
            
        return all([is_aligned(opt) for opt in optics])
    
        
class EARTHQUAKE(GuardState):
    index = 10
    request = False
    
    def main(self):
        global eq_alert_flag                
        # request to pay_localdamp
        ezca['GRD-LSC_LOCK_REQUEST'] = 'DOWN'
        for opt in optics:
            ezca['GRD-VIS_'+opt+'_REQUEST']='PAY_LOCALDAMPED'

        # notification
        if eq_alert_flag==True:
            text = 'Big earthquake! All suspension was automaticaly requested '\
                 + 'to PAY_LOCALDAMPED.'
            log(text)
            # ----------------------
            # alert_to_gokagra(text)
            # ----------------------
            eq_alert_flag = False
            
        # go to idling state
        ezca['GRD-VIS_MANAGER_REQUEST'] = 'IDLING'        
        self.timer['quiet'] = 1800 # wait 30 minutes. Too long?
        
    @eq_check
    def run(self):
        global eq_alert_flag
        global eq_calm_down_flag        
        # if quiet, go to idling state
        if self.timer['quiet']:
            log('Ground motion is quiet. Go to idling state.')
            eq_alert_flag = True
            eq_calm_down_flag = True
            return True

        
class IDLING(GuardState):
    index = 13
    request = True
    
    def main(self):
        # notification        
        global eq_calm_down_flag
        if eq_calm_down_flag==True:
            eq_calm_down_flag = False
            text = 'Now VIS suspensions are idling. After checking Oplev '\
                 + 'signals, please request VIS_MANAGER guardian to go '\
                 + 'ALL_ALIGN state'
            log(text)
            # ----------------------
            # alert_to_gokagra(text)
            # ----------------------
            
    @eq_check
    def run(self):
        return True

class BUILD_MODEL(GuardState):
    index = 20
    request = True
    def main(self):
        # send
        cmd = ['gnome-terminal -x ssh controls@k1ex1 "cd /opt/rtcds/kamioka/k1/rtbuild/current && make k1visetmxt"']
        subprocess.check_output(cmd, shell=True)
        
        pass
    
    
# ------------------------------------------------------------------------------
edges = [
    ('INIT','ALL_ALIGNED'),
    ('INIT','IDLING'),    
    ('EARTHQUAKE','IDLING'),
    ('IDLING','ALL_ALIGNED'),
]
