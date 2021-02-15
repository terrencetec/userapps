import numpy as np
from scipy.signal import freqs,freqs_zpk, zpk2tf
import control
import dtt2hdf
from dtt2hdf import read_diaggui,DiagAccess

import matplotlib.pyplot as plt

color = ['k','r','g','m','c','b']

# ------------------------------------------------------------------------------
def p(w0,Q):
    p1 = -w0/(2*Q)+1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
    p2 = -w0/(2*Q)-1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
    return [p1,p2]

def read_tf(fname,chname_to,chname_from):
    try:
        data = DiagAccess(fname)
        _tf = data.xfer(chname_to,chname_from).xfer
        _coh = data.xfer(chname_to,chname_from).coh
        _omega = data.xfer(chname_to,chname_from).FHz
    except:
        raise ValueError('{0} is invalid file. Please open with diaggui and check the measurement result.'.format(fname))
    return _omega,_tf,_coh

def get_tf(_from,_to):
    if not '_EXC' in _from:
        raise ValueError('!')
    if not '_IN1' in _to:
        raise ValueError('!')
    
    optic1,stage1,test,dof_exc = _from.replace('_EXC','').split('_')
    optic2,stage2,func2,dof2,_ = _to.split('_')
    if stage1==stage2:
        stage = stage1
    
    if test!='TEST':
        raise ValueError('!')
    if optic1==optic2:
        optic = optic1
    else:
        raise ValueError('!')
        
    fname = './current/PLANT_{0}_{3}_{1}_{2}_EXC.xml'.format(optic,test,
                                                             dof_exc,stage)
    # 
    chname_to = 'K1:VIS-{0}_{1}_{2}_{3}_IN1'
    chname_from = 'K1:VIS-{0}_{1}_TEST_{2}_EXC'
    chname_to = chname_to.format(optic2,stage2,func2,dof2)
    chname_from = chname_from.format(optic1,stage1,dof_exc)    
    return read_tf(fname,chname_to,chname_from)

def blend(lp='high'):
    w0 = 0.5
    f0 = w0/(2.0*np.pi)
    #f0=w0
    if lp=='high':
        num = np.array([1,5*f0**1,10*f0**2,       0,      0,      0])*-1
    else:
        num = np.array([0,      0,       0,10*f0**3,5*f0**4,1*f0**5])
    den =     np.array([1,5*f0**1,10*f0**2,10*f0**3,5*f0**4,1*f0**5])
    blend = control.tf(num,den)
    #control.bode(blend,Plot=True)
    #plt.savefig('hoge.png')
    return blend

def get_fitted_tf(omega_measured,tf_measured,coh_measured,_exc,dof):
    _tf = control.tf(*zpk2tf([],[],0))
    print(_exc,dof)    
    for i in range(5):
        try:
            w0,Q0,k0 = params[_exc][dof][i]
            __tf = control.tf(*zpk2tf([],p(w0,Q0),k0))
            _tf += __tf            
        except:
            pass
            #
    if dof not in _exc:
        _tf = _tf*(blend(lp='low')+blend(lp='high'))
        #_tf = _tf*(blend(lp='low'))
    mag, phase, omega = _tf.freqresp(omega_measured)
    _w = omega
    h = mag*np.exp(1j*phase)#*np.exp(1j*10)
    h = np.squeeze(h)
    return _w,h

def plot_tf(w,tf,coh,ax=None,label='None',style='-',subtitle='No title'):
    '''
    '''    
    ax[0].set_title(subtitle)    
    ax[0].loglog(w,np.abs(tf),style,label=label)
    ax[0].set_ylim(1e-6,1e0)
    ax[1].semilogx(w,np.rad2deg(np.angle(tf))*-1,# -1 is bug of dtt2hdf
                   style,label=label)
    ax[2].semilogx(w,coh,style,label=label)
    ax[1].set_ylim(-180,180)
    ax[1].set_yticks(range(-180,181,90))
    ax[2].set_ylim(0,1)
    ax[2].set_xlim(1e-2,10)
    leg = ax[0].legend(loc='lower left',numpoints=1,markerscale=5)
    [l.set_linewidth(3) for l in leg.legendHandles]
    
def plot(optics,stages,dofs,excs,func='DAMP'):
    ''' 
    '''
    fig,ax = plt.subplots(3,6,figsize=(14,8),sharex=True,sharey='row')
    #
    if len(dofs)*len(excs)==1:  # for GAS
        dof,exc = dofs[0],excs[0]
        fig.suptitle('{0} {1} EXC'.format(func,exc))        
        for j,stage in enumerate(stages): # j: plot other figure
            for i,optic in enumerate(optics): # i: plot same figure
                # get_data
                _in = '{0}_{1}_TEST_{2}_EXC'.format(optic,stage,exc)
                _out = '{0}_{1}_{2}_{3}_IN1'.format(optic,stage,func,dof)
                w, tf, coh = get_tf(_in,_out)
                # plot
                label = '{0}'.format(optic)
                title = '{0}->{0}'.format(stage)
                plot_tf(w,tf,coh,ax[:,j],label=label,subtitle=title)        
        fname = './current/PLANT_SUS_GAS_DIAG_EXC.png'
    elif len(stages)*len(excs)==1:
        stage,exc = stages[0],excs[0]
        fig.suptitle('{0} {1} {2} EXC'.format(stage,func,exc))                
        for j,dof in enumerate(dofs): # j: plot other figure
            for i,optic in enumerate(optics): # i: plot same figure
                # get_data
                _in = '{0}_{1}_TEST_{2}_EXC'.format(optic,stage,exc)
                _out = '{0}_{1}_{2}_{3}_IN1'.format(optic,stage,func,dof)
                w, tf, coh = get_tf(_in,_out)            
                # plot
                label = '{0}'.format(optic)
                title = '{0}->{1}'.format(exc,dof)
                plot_tf(w,tf,coh,ax[:,j],label=label,subtitle=title)
        fname = './current/PLANT_SUS_{1}_{2}_{3}_EXC.png'.format(optic,stage,func,exc)
    elif excs==dofs and len(stages)==1:
        stage = stages[0]
        fig.suptitle('{0} {1} DIAG EXC'.format(stage,func))
        for j,dof in enumerate(dofs): # j: plot other figure
            for i,optic in enumerate(optics): # i: plot same figure
                exc = dof
                # get_data
                _in = '{0}_{1}_TEST_{2}_EXC'.format(optic,stage,exc)
                _out = '{0}_{1}_{2}_{3}_IN1'.format(optic,stage,func,dof)
                w, tf, coh = get_tf(_in,_out)            
                # plot
                label = '{0}'.format(optic)
                title = '{0}->{1}'.format(exc,dof)
                plot_tf(w,tf,coh,ax[:,j],label=label,subtitle=title)
        fname = './current/PLANT_SUS_{1}_{2}_DIAG_EXC.png'.format(optic,stage,func,exc)
    else:
        raise ValueError('!')    
    print(fname)
    [ax[2][k].set_xlabel('Frequency [Hz]') for k in range(6)]
    ax[0][0].set_ylabel('Magnitude\n[um/count, urad/count]')
    ax[1][0].set_ylabel('Phase [Degree]')
    ax[2][0].set_ylabel('Coherence')    
    plt.tight_layout()
    plt.savefig(fname)
    plt.close()
        
if __name__=='__main__':
    stages = ['SF','BF']
    optics = ['PRM','PR2','PR3']
    excs = ['GAS']
    dofs = ['GAS']
    plot(optics,stages,dofs,excs,func='DAMP')

    stages = ['BF']
    optics = ['PRM','PR2','PR3']    
    excs = ['L']
    dofs = ['L','T','V']
    plot(optics,stages,dofs,excs,func='DAMP')

    stages = ['BF']
    optics = ['PRM','PR2','PR3']
    excs = ['L','T','V']
    dofs = ['L','T','V']
    plot(optics,stages,dofs,excs,func='DAMP')
    
