import numpy as np
from scipy.signal import freqs,freqs_zpk, zpk2tf
import control
import dtt2hdf
from dtt2hdf import read_diaggui,DiagAccess

import matplotlib.pyplot as plt
# ------------------------------------------------------------------------------
def p(w0,Q):
    p1 = -w0/(2*Q)+1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
    p2 = -w0/(2*Q)-1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
    return [p1,p2]

def read_tf(fname,chname_to,chname_from):
    data = DiagAccess(fname)
    _tf = data.xfer(chname_to,chname_from).xfer
    _coh = data.xfer(chname_to,chname_from).coh
    _omega = data.xfer(chname_to,chname_from).FHz
    return _omega,_tf,_coh    


def get_tf(_from,_to):
    if not '_EXC' in _from:
        raise ValueError('!')
    if not '_IN1' in _to:
        raise ValueError('!')
    
    optic1,stage1,test,dof_exc = _from.replace('_EXC','').split('_')
    optic2,stage2,func2,dof2,_ = _to.split('_')
    if test!='TEST':
        raise ValueError('!')
    if optic1==optic2:
        optic = optic1
    else:
        raise ValueError('!')
    fname = './measurements/PLANT_{0}_IP_{1}_{2}_EXC.xml'.format(optic,test,dof_exc)
    # 
    chname_to = 'K1:VIS-{0}_{1}_{2}_{3}_IN1'
    chname_from = 'K1:VIS-{0}_{1}_TEST_{2}_EXC'
    chname_to = chname_to.format(optic2,stage2,func2,dof2)
    chname_from = chname_from.format(optic1,stage1,dof_exc)    
    return read_tf(fname,chname_to,chname_from)
    

def get_fitted_tf(omega_measured,tf_measured,coh_measured,_exc,dof):
    _tf = control.tf(*zpk2tf([],[],0))
    for i in range(4):
        w0,Q0,k0 = params[_exc][dof][i]
        __tf = control.tf(*zpk2tf([],p(w0,Q0),k0))
        _tf += __tf
    #
    mag, phase, omega = _tf.freqresp(w)
    _w = omega
    h = mag*np.exp(1j*phase)
    h = np.squeeze(h)
    return _w,h

if __name__=='__main__':
    optics = ['SR2','SRM']
    excs = ['L','T','Y']
    dofs = ['L','T','Y']
    funcs = ['IDAMP','BLEND']
    from params import params
    for optic in optics:
        for func in funcs:
            for exc in excs:
                print(optic,func,exc)            
                fig,ax = plt.subplots(3,3,figsize=(16,6),sharex=True)
                plt.title(optic)                    
                for i,dof in enumerate(dofs):
                    if func=='BLEND':
                        _dof = 'LVDT'+dof
                    else:
                        _dof = dof
                    w,tf, coh = get_tf('{0}_IP_TEST_{1}_EXC'.format(optic,exc,func),
                                       '{0}_IP_{2}_{1}_IN1'.format(optic,_dof,func))
                    w,hor1, coh = get_tf('{0}_IP_TEST_{1}_EXC'.format(optic,exc,func),
                                         '{0}_IP_{2}_{1}_IN1'.format(optic,_dof,func))
                    _w,tf_fit = get_fitted_tf(w,tf,coh,'{0}_IP_{2}_{1}_EXC'.format(optic,_dof,func),dof)
                    _w,h = get_fitted_tf(w,hor1,coh,'{0}_IP_{2}_{1}_EXC'.format(optic,_dof,func),dof)
                    ax[0][i].loglog(w,np.abs(hor1),'ro',markersize=1)
                    ax[0][i].loglog(_w,np.abs(h),'k')
                    ax[0][i].set_ylim(1e-5,5e-1)
                    ax[0][i].set_ylim(1e-5,5e1)
                    ax[1][i].semilogx(w,np.rad2deg(np.angle(hor1))*-1,'ro',markersize=1) # -1 comes from dtt2hdf's bug???    
                    ax[1][i].semilogx(_w,np.rad2deg(np.angle(h)),'k')
                    ax[1][i].set_ylim(-180,180)        
                    ax[2][i].semilogx(w,coh,'ro',markersize=1)
                    ax[2][i].set_ylim(0,1)
                    ax[2][i].set_xlim(1e-2,1e1)
                plt.tight_layout()
                plt.savefig('{0}_{2}_{1}.png'.format(optic,exc,func))
                plt.close()            
