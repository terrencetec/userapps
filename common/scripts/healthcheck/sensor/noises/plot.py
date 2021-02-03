import numpy as np
from scipy.interpolate import interp1d
import matplotlib.pyplot as plt
import dtt2hdf
from dtt2hdf import read_diaggui,DiagAccess

def read_asd(fname,chname,refnum=-1,cal=1):
    try:
        data = DiagAccess(fname)
    except FileNotFoundError:
        return None
    
    if refnum!=-1:
        psd = data.references[refnum].PSD[0]
        freq = data.references[refnum].FHz
    else:
        psd = data.results[refnum].PSD[0]
        freq = data.results[refnum].FHz
    asd = psd**(0.5)*cal
    return freq,asd


if __name__=='__main__':
    #freq, asd = read_asd(fname,chname,refnum=refnum,cal=cal)

    # F3 GAS Noise
    data = np.loadtxt('./TypeA_F3_GAS.txt')
    f3_gas_cal = 0.2806 # um/count klog#15891    
    freq = data[:,0]
    f3_gas = data[:,1]#*f3_gas_cal
    adc = data[:,2]#*f3_gas_cal

    # BF GAS Noise
    data = np.loadtxt('./TypeA_BF_GAS.txt')
    cal_new = 0.848 # um/um klog15803
    cal_old = 0.883
    freq = data[:,0]
    bf_gas = data[:,1]/cal_old
    _adc = data[:,2]/cal_old
    free = data[:,3]/cal_new
    
    # ADC model
    adc_model = (2.5e-4*freq**(-1) + 1e-4)**(1/2.)
    
    #
    fig, ax = plt.subplots(1,1)
    plt.title('Noises')
    ax.loglog(freq,f3_gas,'r-',label='F3 GAS LVDT (klog#15904)')
    ax.loglog(freq,bf_gas,'k-',label='BF GAS LVDT (klog#15803)')    
    ax.loglog(freq,adc,'r--',label='ADC (klog#15904)',alpha=0.3)
    ax.loglog(freq,_adc,'k--',label='ADC (klog#15803)',alpha=0.3)
    ax.loglog(freq,adc_model,'b-',label='ADC (model)',linewidth=3)
    ax.set_xlim(1e-3,1e1)
    ax.set_ylim(0.5e-2,1e1)
    ax.legend()
    ax.set_ylabel('Displacement [count/rtHz]')
    ax.set_xlabel('Frequency [Hz]')
    plt.show()
