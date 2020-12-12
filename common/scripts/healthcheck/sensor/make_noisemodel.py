import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt

def make_tr120qa(f,unit='velo'):    
    data = np.array([[1e-3,-171.0], # Freq [Hz.0], PSD (m/s^2)^2/Hz [dB.0]
                     [3e-3,-179.0],
                     [1e-2,-184.0],
                     [3e-2,-188.0],
                     [1e-1,-189.0],
                     [2e-1,-188.0],
                     [1e0, -186.0],
                     [3e0, -182.0],
                     [1e1, -169.0],
                     [2e1, -158.0],
                     [2e2, -118.0]]) # read from a manual
    _f,selfnoise = data[:,0],data[:,1] # PSD Acceleration with dB
    selfnoise = 10**(selfnoise/10.0) # PSD Acceleration with Magnitude
    if unit=='velo':
        _f, selfnoise = _f, selfnoise/(2.0*np.pi*_f)**2
    elif unit=='disp':
        _f, selfnoise = _f, selfnoise/(2.0*np.pi*_f)**4
    elif unit=='acce':
        pass   
    else:
        raise ValueError('!')
    _f, selfnoise = _f, np.sqrt(selfnoise)*1e6
    func = interp1d(np.log(_f),np.log(selfnoise),kind='linear')
    data = np.stack([f,np.exp(func(np.log(f)))],axis=1)
    return data


def make_ip_lvdt(f,unit='disp'):    
    data = np.array([[1e-3, 6e-1], # Freq [Hz.0], PSD (m/s^2)^2/Hz [dB.0]
                     [1e-2, 2e-1],
                     [1e-1, 6e-2],
                     [1e0 , 2e-2],
                     [1e1 , 2e-2],
                     [1e2 , 2e-2]]) # read from the actual ASD
    _f,selfnoise = data[:,0],data[:,1]
    if unit=='disp':
        pass
    elif unit=='velo':
        _f, selfnoise = _f, selfnoise*(2.0*np.pi*_f)        
    else:
        raise ValueError('!')
    
    func = interp1d(np.log(_f),np.log(selfnoise),kind='linear')
    data = np.stack([f,np.exp(func(np.log(f)))],axis=1)    
    return data


def make_l4c(f,unit='velo'):    
    data = np.array([[1e-3, 2e1], # Freq [Hz.0], PSD (m/s^2)^2/Hz [dB.0]
                     [1e-2, 1e1],
                     [1e-1, 1e-2],
                     [1e0 , 5e-5],
                     [1e1 , 5e-5],
                     [1e2 , 5e-5]]) # read from the actual ASD
    _f,selfnoise = data[:,0],data[:,1]#*10 # TypeB is 10 times larger than TypeA
    if unit=='disp':
        _f, selfnoise = _f, selfnoise/(2.0*np.pi*_f)        
    elif unit=='velo':
        pass
    else:
        raise ValueError('!')    
    data = np.stack([_f,selfnoise],axis=1)
    func = interp1d(np.log(_f),np.log(selfnoise),kind='linear')
    data = np.stack([f,np.exp(func(np.log(f)))],axis=1)    
    return data
    with open('noise_l4c.txt','w') as f:
        np.savetxt(f,data)
        
        
if __name__=='__main__':
    freq = np.logspace(-3,1,100)
    seis = make_tr120qa(freq,unit='disp')
    lvdt = make_ip_lvdt(freq)
    l4c = make_l4c(freq,unit='disp')
    data = np.c_[lvdt,seis[:,1],l4c[:,1]]    
    with open('noise.txt','w') as f:
        np.savetxt(f,data)

    plt.loglog(seis[:,0],seis[:,1])
    plt.savefig('tmp.png')
    plt.close()
