import numpy as np
from scipy.signal import freqs_zpk
import dtt2hdf
from dtt2hdf import read_diaggui,DiagAccess

import matplotlib.pyplot as plt
# ------------------------------------------------------------------------------
def hoge(exc,hor):
    fname = './SRM_IP_BLEND_{0}_EXC.xml'.format(exc)
    data = DiagAccess(fname)    
    hor1 = data.xfer('K1:VIS-SRM_IP_BLEND_LVDTL_IN1',
                     'K1:VIS-SRM_IP_TEST_{0}_EXC'.format(exc)).xfer
    hor2 = data.xfer('K1:VIS-SRM_IP_BLEND_LVDTT_IN1',
                     'K1:VIS-SRM_IP_TEST_{0}_EXC'.format(exc)).xfer
    hor3 = data.xfer('K1:VIS-SRM_IP_BLEND_LVDTY_IN1',
                     'K1:VIS-SRM_IP_TEST_{0}_EXC'.format(exc)).xfer
    w = data.xfer('K1:VIS-SRM_IP_BLEND_LVDTL_IN1',
                  'K1:VIS-SRM_IP_TEST_{0}_EXC'.format(exc)).FHz
    #
    def p(w0,Q):
        p1 = -w0/(2*Q)+1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
        p2 = -w0/(2*Q)-1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
        return [p1,p2]

    # for H1_EXC
    _w0,_Q0 = 0.06 ,8
    _w1,_Q1 = 0.41 ,50
    _w2,_Q2 = 0.52 ,50
    _w3,_Q3 = 0.67 ,50
    if hor=='L':
        w0,Q0,k0 = _w0, _Q0, 9.0e-4 #
        w1,Q1,k1 = _w1, _Q1, 3.0e-4 #
        w2,Q2,k2 = _w2, _Q2, 2.0e-5 #
        w3,Q3,k3 = _w3, _Q3, 9.0e-5 #
    elif hor=='P':
        w0,Q0,k0 = _w0, _Q0, 9.0e-5 #
        w1,Q1,k1 = _w1, _Q1, 9.0e-6 #
        w2,Q2,k2 = _w2, _Q2, 2.0e-6 #
        w3,Q3,k3 = _w3, _Q3, 9.0e-6 #
    elif hor=='Y':
        w0,Q0,k0 = _w0, _Q0, 9.0e-6 #
        w1,Q1,k1 = _w1, _Q1, 3.0e-8 #
        w2,Q2,k2 = _w2, _Q2, 2.0e-8 #
        w3,Q3,k3 = _w3, _Q3, 9.0e-8 #
    else:
        pass
    
    _w1,h1 = freqs_zpk([],p(w0,Q0),k0,w)
    _w2,h2 = freqs_zpk([],p(w1,Q1),k1,w)
    _w3,h3 = freqs_zpk([],p(w2,Q2),k2,w)
    _w4,h4 = freqs_zpk([],p(w3,Q3),k3,w)
    
    _w,h = _w1,(h1+h2+h3+h4)#*delay
    print(h[0])
    
    if hor=='L':
        hor1 = hor1
        coh = data.xfer('K1:VIS-SRM_IP_BLEND_LVDTL_IN1',
                        'K1:VIS-SRM_IP_TEST_{0}_EXC'.format(exc)).coh    
    elif hor=='P':
        hor1 = hor2
        coh = data.xfer('K1:VIS-SRM_IP_BLEND_LVDTT_IN1',
                        'K1:VIS-SRM_IP_TEST_{0}_EXC'.format(exc)).coh    
    elif hor=='Y':
        hor1 = hor3
        coh = data.xfer('K1:VIS-SRM_IP_BLEND_LVDTY_IN1',
                        'K1:VIS-SRM_IP_TEST_{0}_EXC'.format(exc)).coh
    else:
        pass

    return w,hor1,w1,_w1,h1,_w2,h2,_w3,h3,_w4,h4,_w,h,coh


if __name__=='__main__':
    exc = 'L'
    hors = ['L','P','Y']
    fig,ax = plt.subplots(3,4,figsize=(16,6),sharex=True)
    for i,hor in enumerate(hors):
        w,hor1,w1,_w1,h1,_w2,h2,_w3,h3,_w4,h4,_w,h,coh = hoge(exc,hor)
        ax[0][i].loglog(w,np.abs(hor1),'ro',markersize=1)
        ax[0][i].loglog(_w1,np.abs(h1),'k--',alpha=0.4)
        ax[0][i].loglog(_w2,np.abs(h2),'k--',alpha=0.4)
        ax[0][i].loglog(_w3,np.abs(h3),'k--',alpha=0.4)
        ax[0][i].loglog(_w,np.abs(h),'k')
        ax[0][i].set_ylim(1e-5,5e-1)
        ax[0][i].set_ylim(1e-5,5e1)
        ax[1][i].semilogx(w,np.rad2deg(np.angle(hor1))*-1,'ro',markersize=1) # -1 comes from dtt2hdf's bug???    
        ax[1][i].semilogx(_w,np.rad2deg(np.angle(h)),'k')
        ax[1][i].set_ylim(-180,180)        
        ax[2][i].semilogx(w,coh,'ro',markersize=1)
        ax[2][i].set_ylim(0,1)
        ax[2][i].set_xlim(1e-2,1e1)
        #ax[2][i].set_xlim(5e-2,1e0)        
    plt.tight_layout()
    plt.savefig('l_exc.png')
    plt.close()            
