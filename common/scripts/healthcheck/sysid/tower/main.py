import subprocess

fname = 'SRM_IP_BLEND_LVDTL_EXC.xml'
optic,stage,func,dof,suffix = fname.replace('.xml','').split('_')
dof = dof[-1]
print(optic,stage,dof,suffix)

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
optics = ['ETMX']
_stage = stage
_func = func
dofs = ['L','T','Y']
for _optic in optics:
    for _dof in dofs:
        _fname = './measurements/{0}_{1}_{2}_LVDT{3}_{4}.xml'.format(_optic,_stage,_func,_dof,suffix)
        if fname!=_fname:
            cmd  = "cp -rf {0} {1}".format(fname,_fname)
            cmd += "; sed -i -e 's/{2}/{3}/' {1}".format(None,_fname,optic,_optic)
            cmd += "; sed -i -e 's/TEST_{4}/TEST_{5}/' {1}".format(None,_fname,None,None,dof,_dof)
            #print(cmd)
            #print(_fname)
            print('{0} -> {1}'.format(fname,_fname))
            subprocess.run(cmd,shell=True,check=True)
            #huge(_fname)
