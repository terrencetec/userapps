import threading
import subprocess
import argparse
import ezca
import time
from plot import plot_3dofs, plot_3sus
from plot import plot_plant_sus_diag_exc
from datetime import datetime
import os 
# ------------------------------------------------------------------------------    
def run_diag(fname):
    ''' Run shell command which executes the diaggui xml file.

    This function runs the diaggui file and output some files;
     * './log/tmp_*_in' is a command file to execute via diag command,
     * './log/tmp*_out' is a stdout file for shell command,
     * './log/tmp*_err' is a stderr file for shell command.

    Parameters
    ----------
    fname: `str`
        File name of the diaggui xml file.

    '''
    _fname = fname.split('/')[2].replace('.xml','')
    
    # make command file for execution
    with open('./log/tmp_{0}_in'.format(_fname),'w') as f:
        txt = 'open\nrestore {0}\nrun -w\nsave {0}\nquit\n'.format(fname)
        f.write(txt)
    print(' - Run {0}'.format(fname))
    
    # run diag command with command file
    with open('./log/tmp_{0}_in'.format(_fname),'r') as tmp_in:
        with open('./log/tmp_{0}_out'.format(_fname),'w') as tmp_out:
            with open('./log/tmp_{0}_err'.format(_fname),'w') as tmp_err:
                ret = subprocess.run('diag',
                                     shell=True,
                                     check=True,
                                     stdin=tmp_in,
                                     stdout=tmp_out,
                                     stderr=tmp_err)
    print(' - Fnished {0} {1}'.format(fname,ret))                

    archive_fname = fname
    current_fname = _fname.split('EXC')[0]+'EXC.xml'
    cmd = 'cp {0} ./current/{1}'.format(archive_fname,current_fname)
    subprocess.run(cmd,shell=True,check=True)
    print(' -',cmd)

def masterswitch_is_open(optic):
    return ezca['VIS-{0}_MASTERSWITCH'.format(optic)]==True

def is_safe(optic):
    return ezca['GRD-VIS_{0}_STATE_S'.format(optic)]=='SAFE'

def is_ready_to_measure(optic):
    if is_safe(optic) and masterswitch_is_open(optic):
        return True
    else:
        raise ValueError('Please request SAFE, and open the Master Switch.')

def get_dofs(optic,stage):
    ''' DOF list for all VIS stages
    
    This function gives DOF lists for each VIS stages.
    
    Parameters
    ----------
    optic: `str`
        optic name

    stage: `str`
        stage name

    Returns
    -------
    dofs: list
        String list of DOFs

    '''
    if stage in ['IM']:
        dofs = ['L','T','V','R','P','Y']
    elif stage in ['MN']:
        dofs = ['L','T','V','R','P','Y']        
    elif stage in ['TM']:
        dofs = ['L','P','Y']
    elif stage in ['BF']:
        if optic in ['PRM','PR2','PR3','ETMX','ITMX','ETMY','ITMY']: 
            dofs = ['L','T','V','R','P','Y']
        else:
            raise ValueError('{0} does not has the BF-damper'.format(optic))
    elif stage in ['IP']:
        dofs = ['L','T','Y']
    elif stage in ['F0','SF']:
        dofs = ['GAS']                
    elif stage in ['F1','F2','F3']:
        raise ValueError('Please choose F0 or SF if you want to measure for GAS chain')
    return dofs

def get_prefix(stage):
    '''
    '''
    return './archive/'

def new_fname(template,optic,stage,dof):
    _,_optic,_stage,_,_dof,_ = template.replace('.xml','').split('_')
    new = template.replace(_optic,optic).replace('_'+_dof+'_','_'+dof+'_')
    new = new.replace('_'+_dof+'_','_'+dof+'_')
    new = new.replace('_'+_stage+'_','_'+stage+'_')
    now = datetime.now().strftime('%Y%m%d%H')
    new_fname = get_prefix(stage) + new.replace('.xml','_{0}.xml'.format(now))
    return new_fname, now

# ------------------------------------------------------------------------------    
def run_tf_measurement(template,optic,stage,dofs=['L','P','Y'],run=False):
    ''' Run diaggui xml file which measures the Transfer Function.
    
    This function runs shell command which executes the diaggui xml file for TF
    measurement. Name of the file is given by  arguments


    Parameters
    ----
    template: `str`
        name of the template diaggui file.

    target_optic: `str`
        optic name that you want to measure

    target_stage: `str`
        stage name that you want to measure

    Returns
    ----
    None
    '''
    # run diag
    prefix = get_prefix(stage)
    for dof in get_dofs(optic,stage):
        if dof in dofs:
            # new_fname
            fname, _now = new_fname(template,optic,stage,dof)
            # run
            if is_ready_to_measure(optic):
                if run:
                    run_diag(fname) 
            else:
                raise ValueError('!')

# ------------------------------------------------------------------------------
        
def run_copy(template,optic,stage,dofs=['L','P','Y'],run=False):
    ''' Copy template file to working directory.

    This function run shell command which copies template file for TF measurement
    to measurement directory. File path to this directory is given by new_fname().
    
    Parameters
    ----------
    template: `str`
        Diaggui template file name.

    optic: `str`
        Optic name which you want to measure.

    stage: `str`
        Stage name which you want to measure.

    run: optional
        If true, execute shell command. Default is false.

    '''    
    # run command
    for dof in get_dofs(optic,stage):
        if dof in dofs:
            # new_fname
            _,_optic,_stage,_,_dof,_ = template.replace('.xml','').split('_')
            fname, _now = new_fname(template,optic,stage,dof)
            
            # make command
            print('copy {0} -> {1}'.format('./template/'+template,fname))
            cmd = "cp -rf {0} {1}".format('./template/'+template,fname)
            cmd += "; sed -i -e 's/{1}_{3}_DAMP/{2}_{4}_DAMP/' {0}".\
                format(fname,_optic,optic,_stage,stage)
            cmd += "; sed -i -e 's/{1}_{3}_TEST_{5}_EXC/{2}_{4}_TEST_{6}_EXC/' {0}".\
                format(fname,_optic,optic,_stage,stage,_dof,dof)
            cmd += "; sed -i -e 's/{1}_{3}_{5}/{2}_{4}_{6}/' {0}".\
                format(fname,_optic,optic,_stage,stage,_dof,dof)        
            # run
            if run:
                subprocess.run(cmd,shell=True,check=True)
            
if __name__=="__main__":
    ezca = ezca.Ezca(timeout=2)
    parser = argparse.ArgumentParser()
    parser.add_argument('-optics','-o',nargs='+',required=True)
    parser.add_argument('-stage','-s',nargs='+',required=True)
    parser.add_argument('-dofs','-d',nargs='+',required=True)    
    parser.add_argument('--rundiag',action='store_true')
    parser.add_argument('--init',action='store_true')
    parser.add_argument('--plot',action='store_true')
    args = parser.parse_args()
    
    t = []
        
    optics = args.optics
    stage = args.stage[0]
    dofs = args.dofs
    if stage=='IM':
        template = 'PLANT_PRM_IM_TEST_L_EXC.xml'
    elif stage=='BF':        
        template = 'PLANT_PRM_BF_TEST_L_EXC.xml'
    else:
        raise ValueError('{0}!'.format(stage))
    
    #
    # Notification
    #
    if stage not in ['IM','BF']:
        raise ValueError('{0} is not supported now.'.format(stage))
    if len(optics)>3 and not args.plot:
        raise ValueError('Please reduce the number of optics because it may ' \
                         'reach to the limit of the maximum number of '\
                         'the test point. ')

    #
    # Start main functions
    #                    
    if args.init: # Copy template file to working directory.
        for optic in optics:
            run_copy(template,optic,stage,dofs=dofs,run=True)

    if args.rundiag: # Parallel measurement for each optics!
        for optic in optics:
            _t = threading.Thread(target=run_tf_measurement,
                                  args=(template,optic,stage),
                                  kwargs={'run':True,'dofs':dofs})
            _t.start()
            #_t.join()
            t += [_t]

    if args.plot:
        excs = ['L','T','V','R','P','Y']
        func = 'DAMP'
        stage = stage
        if False:
            for exc in excs:
                print(optics,stage,func,dofs,exc)
                plot_3sus(optics,stage,func,dofs,exc)
        if True:
            plot_plant_sus_diag_exc(optics,stage,func,dofs,excs)
        
