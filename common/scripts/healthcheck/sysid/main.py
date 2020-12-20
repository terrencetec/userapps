import threading
import subprocess
import argparse
import ezca

ezca = ezca.Ezca(timeout=2)

parser = argparse.ArgumentParser()
parser.add_argument('fname')
parser.add_argument('-optics',nargs='+',required=True)
parser.add_argument('-dofs',nargs='+',required=True)
parser.add_argument('--rundiag',action='store_true')
parser.add_argument('--runcp',action='store_true')
args = parser.parse_args()
fname = 'PLANT_SRM_IP_BLEND_LEXC.xml'
fname = 'PLANT_SRM_IP_IDAMP_LEXC.xml'
fname = args.fname
runcp = args.runcp
rundiag = args.rundiag
prefix,optic,stage,func,dof,suffix = fname.replace('.xml','').split('_')

def run_diag(fname):
    _fname = fname.split('/')[3].replace('.xml','')
    with open('./log/tmp_{0}_in'.format(_fname),'w') as f:
        txt = 'open\nrestore {0}\nrun -w\nsave {0}\nquit\n'.format(fname)
        f.write(txt)
    print(' - Run {0}'.format(fname))
    with open('./log/tmp_{0}_in'.format(_fname),'r') as tmp_in:
        with open('./log/tmp_{0}_out'.format(_fname),'w') as tmp_out:
            with open('./log/tmp_{0}_err'.format(_fname),'w') as tmp_err:
                ret = subprocess.run('diag',shell=True,check=True,
                                     stdin=tmp_in,stdout=tmp_out,stderr=tmp_err)   
    print(' - Fnished {0} {1}'.format(fname,ret))

# ------------------------------------------------------------------------------
# Generate other diaggui files by copying the template file.
#

def masterswitch_is_open(optic):
    return ezca['VIS-{0}_MASTERSWITCH'.format(optic)]==True

def is_safe(optic):
    return ezca['GRD-VIS_{0}_STATE_S'.format(optic)]=='SAFE'

def is_ready_to_measure(optic):
    if is_safe(optic) and masterswitch_is_open(optic):
        return True
    else:
        raise ValueError('Please request SAFE, and open the Master Switch.')

# ------------------------------------------------------------------------------    
def run_tf_measurement(target_optic,target_stage,target_dofs):
    for _dof in target_dofs:
        if  target_stage in ['IM']:
            prefix = './payload/measurements/'
        else:
            raise ValueError('!')
        _fname = prefix + fname.replace(optic,target_optic).\
            replace('_'+dof+'_','_'+_dof+'_')
        cmd  = "cp -rf {0} {1}".format(fname,_fname)
        cmd += "; sed -i -e 's/{2}/{3}/' {1}".format(None,_fname,optic,
                                                     target_optic)
        cmd += "; sed -i -e 's/TEST_{4}/TEST_{5}/' {1}".format(None,_fname,
                                                               None,None,dof,
                                                               _dof)
        print('{0} -> {1}'.format(fname,_fname))
        if runcp:
            subprocess.run(cmd,shell=True,check=True)
        if rundiag and is_ready_to_measure(target_optic):            
            print('run',target_optic)
            run_diag(_fname)
    
optics = args.optics
dofs = args.dofs

_stage = stage
_func = func

t = []
for _optic in optics:
    _t = threading.Thread(target=run_tf_measurement,args=(_optic,_stage,dofs))
    _t.start()
    #_t.join()
    t += [_t]
