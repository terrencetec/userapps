import subprocess


fname = 'OSTM_TM_H1_EXC.xml'
optic,stage,dof,prefix = fname.replace('.xml','').split('_')
print(optic,stage,dof,prefix)

def huge(_fname):
    with open('./log/tmp_in','w') as f:
        txt = 'open\nrestore {0}\nrun -w\nsave {0}\nquit\n'.format(_fname)
        f.write(txt)
    print(' - Run {0}'.format(_fname))
    with open('./log/tmp_in','r') as tmp_in:
        with open('./log/tmp_out','w') as tmp_out:
            with open('./log/tmp_err','w') as tmp_err:
                ret = subprocess.run('diag',shell=True,check=True,
                                     stdin=tmp_in,stdout=tmp_out,stderr=tmp_err)                
    print(' - Fnished {0} {1}'.format(_fname,ret))    

# ------------------------------------------------------------------------------
# Generate other diaggui files by copying the template file.
# 
optics = ['OSTM','OMMT1','OMMT2']
optics = ['OSTM']
_stage = 'TM'
dofs = ['H1','H2','H3','H4']
#dofs = ['H2']
for _optic in optics:
    for _dof in dofs:
        _fname = './measurements/{0}_{1}_{2}_{3}.xml'.format(_optic,_stage,_dof,prefix)
        if fname!=_fname:        
            cmd  = "cp -rf {0} {1}".format(fname,_fname)
            cmd += "; sed -i -e 's/{2}/{3}/' {1}".format(None,_fname,optic,_optic)
            cmd += "; sed -i -e 's/{4}/{5}/' {1}".format(None,_fname,None,None,dof,_dof)
            print('{0} -> {1}'.format(fname,_fname))
            subprocess.run(cmd,shell=True,check=True)
            huge(_fname)        
