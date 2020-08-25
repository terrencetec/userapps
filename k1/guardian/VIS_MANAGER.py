#
#! coding:utf-8
from guardian import GuardState
from guardian import GuardStateDecorator
from guardian import NodeManager
import vislib
import subprocess

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

def manager_request(opt,state):
    '''
    '''
    nodes['VIS_'+opt]=state

def used_optics():
    ''' Return name list of the optics which are not used someone
    
    Returns
    -------
    used : `list`
        used optics name list as the set object.
    '''
    used = [opt for opt in managed_optics if is_used(opt)]
    return used

def unused_optics():
    ''' Return name list of the optics which are not used someone
    
    Returns
    -------
    unused : `set`
        unused optics name list as the set object.
    '''
    use = []
    for opt in managed_optics:
        if is_used(opt):
            use += [opt]
    unused = set(managed_optics)-set(use)
    return unused


def is_used(opt):
    ''' check if someone use the optics

    Parameters
    ----------
    opt : `str`
        optics name.

    Returns
    -------
    flag : `Bool`
        return true if someone use.
    '''
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
    def pre_exec(self):
	if is_earthquake():
            return 'EARTHQUAKE'

class revive(GuardStateDecorator):
    def pre_exec(self):
        for node in nodes.get_stalled_nodes():
            node.revive()
                
        
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
        #cmd = ['gnome-terminal -x ssh controls@k1ex1 "cd /opt/rtcds/kamioka/k1/rtbuild/current && make k1visetmxt"']
        #subprocess.check_output(cmd, shell=True)
        
        pass

    
class XARM_READY(GuardState):
    index = 30
    request = True

    @eq_check    
    def main(self):
        ''' All suspensions are requested to ALIGNED.
        '''
        self.timer['test'] = 0
        someone_use = []        
        
    @eq_check
    @revive
    def run(self):
        '''
        Force to request the ALIGNED state if no one use the suspensions.
        '''
        # 1. Force to aligne the suspension
        someone_use = []
        misaligned_optics = ['PRM','SRM']
        aligned_optics = set(managed_optics) - set(misaligned_optics)
        for opt in aligned_optics:
            if nodes['VIS_'+opt]!='ALIGNED':
                if not is_used(opt):
                    nodes['VIS_'+opt]='ALIGNED' 
            if is_used(opt):
                someone_use += [opt]                
        for opt in misaligned_optics:
            if nodes['VIS_'+opt]!='MISALIGNED':
                if not is_used(opt):
                    nodes['VIS_'+opt]='MISALIGNED' 
            if is_used(opt):
                someone_use += [opt]                
        notify('Not managed: {0}'.format(','.join(someone_use)))            
        return True


class ALL_ALIGNED(GuardState):
    ''' Request the ALIGNED state for all suspensions.
    
    '''    
    index = 1
    request = True

    @eq_check    
    def main(self):
        '''
        '''
        self.timer['test'] = 0
                
    @eq_check
    @revive
    def run(self):
        ''' Force to request the ALIGNED state if no one use the suspensions.
        '''
        notify('Not managed: {0}'.format(','.join(used_optics())))
        optics = unused_optics()
        optics = [opt for opt in optics if nodes['VIS_'+opt]!='ALIGNED']
        [manager_request(opt,'ALIGNED') for opt in optics]
        return True

    
class ALL_SAFE(GuardState):
    ''' Request the ALIGNED state for all suspensions.
    
    '''    
    index = 2
    request = True

    @eq_check    
    def main(self):
        '''
        '''
        self.timer['test'] = 0
        
    @eq_check
    @revive    
    def run(self):
        ''' Force to request the SAFE state if no one use the suspensions.
        '''
        notify('Not managed: {0}'.format(','.join(used_optics()))) 
        optics = unused_optics()        
        optics = [opt for opt in optics if nodes['VIS_'+opt]!='SAFE']   
        [manager_request(opt,'SAFE') for opt in optics]
        return True

    
class ALL_MISALIGNED(GuardState):
    ''' Request the ALIGNED state for all suspensions.
    
    '''    
    index = 3
    request = True

    @eq_check    
    def main(self):
        ''' All suspensions are requested to ALIGNED.
        '''
        self.timer['test'] = 0
        
    @eq_check
    @revive
    def run(self):
        ''' Force to request the MISALIGNED state if no one use the suspensions.
        '''
        notify('Not managed: {0}'.format(','.join(used_optics())))
        optics = unused_optics()
        optics = [opt for opt in optics if nodes['VIS_'+opt]!='MISALIGNED']
        [manager_request(opt,'MISALIGNED') for opt in optics]
        return True
        
    
# ------------------------------------------------------------------------------
edges = [
    ('INIT','ALL_ALIGNED'),
    ('INIT','ALL_MISALIGNED'),
    ('INIT','ALL_SAFE'),
    ('INIT','IDLING'),        
    ('EARTHQUAKE','IDLING'),
    ('IDLING','ALL_ALIGNED'),
    ('INIT','XARM_READY'),
]
