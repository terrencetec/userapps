import numpy as np
from scipy.signal import freqs_zpk
import dtt2hdf
from dtt2hdf import read_diaggui,DiagAccess

import matplotlib.pyplot as plt

def hoge(exc,hor):
    fname = './measurements/OSTM_TM_{0}_EXC.xml'.format(exc)
    data = DiagAccess(fname)
    hor1 = data.xfer('K1:VIS-OSTM_TM_OSEMINF_H1_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).xfer
    hor2 = data.xfer('K1:VIS-OSTM_TM_OSEMINF_H2_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).xfer
    hor3 = data.xfer('K1:VIS-OSTM_TM_OSEMINF_H3_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).xfer
    hor4 = data.xfer('K1:VIS-OSTM_TM_OSEMINF_H4_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).xfer
    w = data.xfer('K1:VIS-OSTM_TM_OSEMINF_H1_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).FHz
    #
    def p(w0,Q):
        p1 = -w0/(2*Q)+1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
        p2 = -w0/(2*Q)-1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
        return [p1,p2]

    # for H1_EXC
    if hor=='H1':
        w0,Q0,k0 = 1.3  ,4  , 1.5e-1 # Len
        w1,Q1,k1 = 8    ,5  , 3.0e-2 #
        w2,Q2,k2 = 15   ,30 , 1.0e-2 # Len
        w3,Q3,k3 = 20   ,20 , 1.0e-4 #
        w4,Q4,k4 = 15   ,20 , 3.0e-4 #
        w5,Q5,k5 = 17   ,20 , 2.0e-4 # 
    elif hor=='H2':
        w0,Q0,k0 = 1.3  ,4  , 1.5e-1
        w1,Q1,k1 = 8    ,5  ,-1.0e-1
        w2,Q2,k2 = 20   ,7  , 2.0e-4
        w3,Q3,k3 = 20   ,20 , 2.0e-4 #
        w4,Q4,k4 = 15   ,20 , 1.0e-4 #
        w5,Q5,k5 = 17   ,20 ,-1.0e-4 #         
    elif hor=='H3':
        w0,Q0,k0 = 1.3  ,4  , 1.5e-1
        w1,Q1,k1 = 8    ,5  ,-8.0e-3
        w2,Q2,k2 = 20   ,7  , 1.5e-4
        w3,Q3,k3 = 20   ,20 ,-1.0e-4 #
        w4,Q4,k4 = 15   ,20 , 1.0e-4 #
        w5,Q5,k5 = 17   ,20 ,-7.0e-4 #
    elif hor=='H4':
        w0,Q0,k0 = 1.3  ,4  , 1.5e-1 # Len
        w1,Q1,k1 = 8    ,5  , 1.5e-3 #
        w2,Q2,k2 = 20   ,7  , 3.5e-4 # Len
        w3,Q3,k3 = 20   ,20 ,-3.0e-4 #
        w4,Q4,k4 = 15   ,20 , 3.5e-4 #
        w5,Q5,k5 = 17   ,20 ,-4.5e-4 #
    else:
        pass
    
    _w1,h1 = freqs_zpk([],p(w0,Q0),k0,w)
    _w2,h2 = freqs_zpk([],p(w1,Q1),k1,w)
    _w3,h3 = freqs_zpk([],p(w2,Q2),k2,w)
    _w4,h4 = freqs_zpk([],p(w3,Q3),k3,w)
    _w5,h5 = freqs_zpk([],p(w4,Q4),k4,w)
    _w6,h6 = freqs_zpk([],p(w5,Q5),k5,w)

    # unknown Delay
    if hor=='H3':
        _w1,delay = freqs_zpk([-0.46],[-12.3],-7,w) # de-white
        #_w1,delay = freqs_zpk([-0.5],[-1],-8,w) # de-white and minus sign caused from dtt2hdf
    else:
        _w1,delay = freqs_zpk([-0.46],[-12.3],-7,w) # de-white        
        #_w1,delay = freqs_zpk([-0.5],[-1],-8,w) # de-white
    
    _w,h = _w1,(h1+h2+h3+h4+h5+h6)*delay
    
    if hor=='H1':
        hor1 = hor1
        coh = data.xfer('K1:VIS-OSTM_TM_OSEMINF_H1_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).coh    
    elif hor=='H2':
        hor1 = hor2
        coh = data.xfer('K1:VIS-OSTM_TM_OSEMINF_H2_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).coh    
    elif hor=='H3':
        hor1 = hor3
        coh = data.xfer('K1:VIS-OSTM_TM_OSEMINF_H3_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).coh        
    elif hor=='H4':
        hor1 = hor4
        coh = data.xfer('K1:VIS-OSTM_TM_OSEMINF_H4_IN1_DQ','K1:VIS-OSTM_TM_COILOUTF_{0}_EXC'.format(exc)).coh            
    else:
        pass

    return w,hor1,w1,_w1,h1,_w2,h2,_w3,h3,_w4,h4,_w5,h5,_w6,h6,_w,h,coh

def hoge(exc,hor):
    fname = './OSTM_TM_{0}_EXC.xml'.format(exc)
    data = DiagAccess(fname)
    hor1 = data.xfer('K1:VIS-OSTM_TM_DAMP_L_IN1','K1:VIS-OSTM_TM_TEST_{0}_EXC'.format(exc)).xfer
    hor2 = data.xfer('K1:VIS-OSTM_TM_DAMP_P_IN1','K1:VIS-OSTM_TM_TEST_{0}_EXC'.format(exc)).xfer
    hor3 = data.xfer('K1:VIS-OSTM_TM_DAMP_Y_IN1','K1:VIS-OSTM_TM_TEST_{0}_EXC'.format(exc)).xfer
    w = data.xfer('K1:VIS-OSTM_TM_DAMP_L_IN1','K1:VIS-OSTM_TM_TEST_{0}_EXC'.format(exc)).FHz
    #
    def p(w0,Q):
        p1 = -w0/(2*Q)+1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
        p2 = -w0/(2*Q)-1j*np.sqrt((w0)**2-w0**2/(4*Q**2))
        return [p1,p2]

    # for H1_EXC
    if hor=='L':
        w0,Q0,k0 = 1.3  ,4  , 3.0e-0 # Len
        w1,Q1,k1 = 8    ,5  , 3.0e-1 #
        w2,Q2,k2 = 15   ,30 , 1.0e-1 # Len
        w3,Q3,k3 = 20   ,20 , 1.0e-4 #
        w4,Q4,k4 = 15   ,20 , 3.0e-4 #
        w5,Q5,k5 = 17   ,20 , 2.0e-4 # 
    elif hor=='P':
        w0,Q0,k0 = 1.3  ,4  , 3.0e-0
        w1,Q1,k1 = 8    ,5  ,-1.0e-4
        w2,Q2,k2 = 20   ,7  , 2.0e-4
        w3,Q3,k3 = 20   ,20 , 2.0e-4 #
        w4,Q4,k4 = 15   ,20 , 1.0e-4 #
        w5,Q5,k5 = 17   ,20 ,-1.0e-4 #         
    elif hor=='Y':
        w0,Q0,k0 = 1.3  ,4  , 1.5e-1
        w1,Q1,k1 = 8    ,5  ,-8.0e-4
        w2,Q2,k2 = 20   ,7  , 1.5e-4
        w3,Q3,k3 = 20   ,20 ,-1.0e-4 #
        w4,Q4,k4 = 15   ,20 , 1.0e-4 #
        w5,Q5,k5 = 17   ,20 ,-7.0e-4 #
    else:
        pass
    
    _w1,h1 = freqs_zpk([],p(w0,Q0),k0,w)
    _w2,h2 = freqs_zpk([],p(w1,Q1),k1,w)
    _w3,h3 = freqs_zpk([],p(w2,Q2),k2,w)
    _w4,h4 = freqs_zpk([],p(w3,Q3),k3,w)
    _w5,h5 = freqs_zpk([],p(w4,Q4),k4,w)
    _w6,h6 = freqs_zpk([],p(w5,Q5),k5,w)

    # unknown Delay
    if hor=='L':
        _w1,delay = freqs_zpk([-0.46],[-12.3],-7,w) # de-white
        _w1,delay = freqs_zpk([-0.5],[-10],-8,w) # de-white and minus sign caused from dtt2hdf
    else:
        _w1,delay = freqs_zpk([-0.46],[-12.3],-7,w) # de-white
        _w1,delay = freqs_zpk([-0.5],[-10],-8,w) # de-white
    
    _w,h = _w1,(h1+h2+h3+h4+h5+h6)*delay
    
    if hor=='L':
        hor1 = hor1
        coh = data.xfer('K1:VIS-OSTM_TM_DAMP_L_IN1','K1:VIS-OSTM_TM_TEST_{0}_EXC'.format(exc)).coh    
    elif hor=='P':
        hor1 = hor2
        coh = data.xfer('K1:VIS-OSTM_TM_DAMP_P_IN1','K1:VIS-OSTM_TM_TEST_{0}_EXC'.format(exc)).coh    
    elif hor=='Y':
        hor1 = hor3
        coh = data.xfer('K1:VIS-OSTM_TM_DAMP_Y_IN1','K1:VIS-OSTM_TM_TEST_{0}_EXC'.format(exc)).coh        
    else:
        pass

    return w,hor1,w1,_w1,h1,_w2,h2,_w3,h3,_w4,h4,_w5,h5,_w6,h6,_w,h,coh


if __name__=='__main__':
    exc = 'H1'
    exc = 'L'
    hors = ['H1','H2','H3','H4']
    hors = ['L','P','Y']
    fig,ax = plt.subplots(3,4,figsize=(16,6),sharex=True)
    for i,hor in enumerate(hors):
        w,hor1,w1,_w1,h1,_w2,h2,_w3,h3,_w4,h4,_w5,h5,_w6,h6,_w,h,coh = hoge(exc,hor)
        ax[0][i].loglog(w,np.abs(hor1),'ro',markersize=1)
        ax[0][i].loglog(_w1,np.abs(h1),'k--',alpha=0.4)
        ax[0][i].loglog(_w2,np.abs(h2),'k--',alpha=0.4)
        ax[0][i].loglog(_w3,np.abs(h3),'k--',alpha=0.4)
        ax[0][i].loglog(_w4,np.abs(h4),'k--',alpha=0.4)
        ax[0][i].loglog(_w5,np.abs(h5),'k--',alpha=0.4)
        ax[0][i].loglog(_w6,np.abs(h6),'k--',alpha=0.4)
        ax[0][i].loglog(_w,np.abs(h),'k')
        ax[0][i].set_ylim(1e-5,5e-1)
        ax[0][i].set_ylim(1e-5,5e1)
        ax[1][i].semilogx(w,np.rad2deg(np.angle(hor1))*-1,'ro',markersize=1) # -1 comes from dtt2hdf's bug???    
        ax[1][i].semilogx(_w,np.rad2deg(np.angle(h)),'k')
        ax[1][i].set_ylim(-180,180)        
        ax[2][i].semilogx(w,coh,'ro',markersize=1)
        ax[2][i].set_ylim(0,1)
        ax[2][i].set_xlim(1e-1,5e1)        
    plt.tight_layout()
    plt.savefig('h3_exc.png')
    plt.close()
            
