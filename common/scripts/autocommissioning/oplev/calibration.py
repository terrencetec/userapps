#!/usr/bin/env python3
#! coding:utf-8
from cdsutils import avg
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from scipy.optimize import curve_fit
import scipy

oplev_info = {# name: [type, lever_arm_length [m], ...]
    'MCE_TM_OPLEV_TILT':['REGULAR',0.95], #klog#3175
    'MCI_TM_OPLEV_TILT':['REGULAR',0.86], #klog#3175
    'MCO_TM_OPLEV_TILT':['FOLDED' ,0.85],  #klog#3175
    'IMMT1_TM_OPLEV_TILT':[None ,None],  #
    'IMMT2_TM_OPLEV_TILT':[None ,None],  #
    'PR2_TM_OPLEV_TILT':[None ,None],  #
    'PR2_TM_OPLEV_LEN':[None ,None],   #
    'PR3_TM_OPLEV_TILT':[None ,None],  #
    'PR3_TM_OPLEV_LEN':[None ,None],   #    
    'PRM_TM_OPLEV_TILT':[None ,None],  #
    'PRM_TM_OPLEV_LEN':[None ,None],   #
    'SR2_TM_OPLEV_TILT':[None ,None],  #
    'SR2_TM_OPLEV_LEN':[None ,None],   #
    'SR3_TM_OPLEV_TILT':[None ,None],  #
    'SR3_TM_OPLEV_LEN':[None ,None],   #    
    'SRM_TM_OPLEV_TILT':[None ,None],  #
    'SRM_TM_OPLEV_LEN':[None ,None],   #
    'BS_TM_OPLEV_TILT':[None ,None],   #
    'BS_TM_OPLEV_LEN':[None ,None],    #
    #
    'ETMX_TM_OPLEV_TILT':[None ,None],   #
    'ETMX_TM_OPLEV_LEN':[None ,None],    #
    'ETMX_MN_OPLEV_TILT':[None ,None],   #        
    'ETMX_MN_OPLEV_LEN':[None ,None],    #
    'ETMX_MN_OPLEV_ROL':[None ,None],    #
    'ETMX_MN_OPLEV_TRA':[None ,None],    #
    'ETMX_MN_OPLEV_VER':[None ,None],    #
    'ETMX_PF_OPLEV_TILT':[None ,None],   #
    'ETMX_PF_OPLEV_LEN':[None ,None],    #
    # 
    'ETMY_TM_OPLEV_TILT':[None ,None],   #
    'ETMY_TM_OPLEV_LEN':[None ,None],    #
    'ETMY_MN_OPLEV_TILT':[None ,None],   #        
    'ETMY_MN_OPLEV_LEN':[None ,None],    #
    'ETMY_MN_OPLEV_ROL':[None ,None],    #
    'ETMY_MN_OPLEV_TRA':[None ,None],    #
    'ETMY_MN_OPLEV_VER':[None ,None],    #
    'ETMY_PF_OPLEV_TILT':[None ,None],   #
    'ETMY_PF_OPLEV_LEN':[None ,None],    #
    # 
    'ITMX_TM_OPLEV_TILT':[None ,None],   #
    'ITMX_TM_OPLEV_LEN':[None ,None],    #
    'ITMX_MN_OPLEV_TILT':[None ,None],   #        
    'ITMX_MN_OPLEV_LEN':[None ,None],    #
    'ITMX_MN_OPLEV_ROL':[None ,None],    #
    'ITMX_MN_OPLEV_TRA':[None ,None],    #
    'ITMX_MN_OPLEV_VER':[None ,None],    #
    'ITMX_PF_OPLEV_TILT':[None ,None],   #
    'ITMX_PF_OPLEV_LEN':[None ,None],    #
    # 
    'ITMY_TM_OPLEV_TILT':[None ,None],   #
    'ITMY_TM_OPLEV_LEN':[None ,None],    #
    'ITMY_MN_OPLEV_TILT':[None ,None],   #        
    'ITMY_MN_OPLEV_LEN':[None ,None],    #
    'ITMY_MN_OPLEV_ROL':[None ,None],    #
    'ITMY_MN_OPLEV_TRA':[None ,None],    #
    'ITMY_MN_OPLEV_VER':[None ,None],    #
    'ITMY_PF_OPLEV_TILT':[None ,None],   #
    'ITMY_PF_OPLEV_LEN':[None ,None],    #            
}

def oplev_factor_is(optic,stage,func):
    '''
    '''
    try:
        name = '{0}_{1}_{2}'.format(optic,stage,func)
        _type = oplev_info[name][0] # 0 is for oplev_type
    except:
        raise ValueError('Invalid oplev name: {0}'.format(name))
    if _type=='REGULAR':
        factor = 2
    elif _type=='FOLDED':
        factor = 4
    else:
        raise ValueError('Invalid oplev type: {0}'.format(_type))
    return factor

def lever_arm_is(optic,stage,func):
    '''
    '''
    try:
        name = '{0}_{1}_{2}'.format(optic,stage,func)
        length = oplev_info[name][1] # 1 is for lever_arm_length
    except:
        raise ValueError('Invalid oplev name: {0}'.format(name))
    return length

def get_calib(slope,optic,stage,func,dof):
    '''
    '''    
    factor = oplev_factor_is(optic,stage,func)
    length = lever_arm_is(optic,stage,func)
    calib = slope/(factor*length)*1000 # [um/count]
    return calib


def calibration(output,optic,stage,func,dof,show=False):
    '''
    '''
    optic,stage,func1,func2,dof = output.split('/')[-1].replace('.txt','').split('_')
    optic = optic.upper()
    dof = dof.upper()
    f = open(output,'r',encoding='UTF-8')
    df = f.readlines()
    f.close()
    df = [i.split(',') for i in df]
    df = pd.read_csv(output,header=0)
    df = df.sort_values('Disp')
    
    _name = ['K1:VIS-{0}_{1}_OPLEV_TILT_PIT_INMON'.format(optic,stage),
             'K1:VIS-{0}_{1}_OPLEV_TILT_YAW_INMON'.format(optic,stage),
             'K1:VIS-{0}_{1}_OPLEV_TILT_SUM_INMON'.format(optic,stage),
             'K1:VIS-{0}_{1}_OPLEV_TILT_CRS_INMON'.format(optic,stage)]
    
    col,row = 4,1
    fig, ax = plt.subplots(col,row,figsize=(8,8),sharex=True)
    fig.subplots_adjust(wspace=0.1, hspace=0.05, left=0.15, right=0.6, top=0.92)
    plt.suptitle('OpLev calibration of {0} {1}'.format(optic,dof),fontsize=20)
    for i,_ax in enumerate(ax):
        if i==3:
            _ax.set_xlabel('Distance [mm]')
        n = i
        
        if n>=len(_name):
            break
        ylabel = 'Value [count]'
        _ax.set_ylabel(ylabel)
        
        if n<len(_name):
            _ax.errorbar(x=df['Disp'],
                         y=df[_name[n]+'.mean'],
                         yerr=df[_name[n]+'.std'],
                         fmt='ko',label=_name[n],
                         markersize=2,capsize=3)
            #
            _df = df
            x = _df['Disp'].values            
            _ave = x.mean()            
            _x = np.arange(_ave-2,_ave+2,0.05)
            y = _df[_name[n]+'.mean'].values            
            if dof not in _name[n]:
                if 'SUM' not in _name[n] and 'CRS' not in _name[n]:
                    _func = lambda x,a,b: a+b*x
                    slope = (y[-1]-y[0])/(x[-1]-x[0])
                    ini_param = np.array([slope,0.0])
                    popt, pcov = curve_fit(_func,x,y,p0=ini_param)
                    label = '{0:3.2f}*x + {1:3.2f}'.format(*popt)
                    _ax.plot(_x,_func(_x,*popt),label=label)
            if dof in _name[n]:
                # fit error _func
                _func = lambda x,a,b,c,d: a*scipy.special.erf(b*(x-c)) + d
                if (y[-1]-y[0])>0:
                    ini_param = np.array([-1.0,-4,x.mean(),0.0])
                else:
                    ini_param = np.array([-1.0,+5,x.mean(),0.0])
                popt, pcov = curve_fit(_func,x,y,p0=ini_param)
                a,b,c,d = popt
                label = '{0:3.2f}* erf({1:3.2f}(x-{2:3.2f})) + {3:3.2f}'.format(*popt)
                _ax.plot(_x,_func(_x,*popt),label=label)
                # fit linear
                _func = lambda x,a,b,c: a*b*(x-c)*2/np.sqrt(np.pi)
                slope_inv = a*b*2/np.sqrt(np.pi)
                slope = 1./slope_inv
                label = '{0:3.2f}*(x-{1:3.2f})'.format(slope_inv,c)
                _ax.plot(_x,_func(_x,a,b,c),label=label)
                sigma = 1/(abs(b)*np.sqrt(2))
                radius = 2*sigma
                width = 2*radius
                linrange = sigma#/2
                print('{1}_{2}, Beam width(1/e^2) is {0:3.2f} [mm]?.'.format(width,optic,dof))
                print('       , Linear range is {0:3.2f} [mm]?.'.format(linrange))
                calib = get_calib(slope,optic,stage,func,dof)
                print('       , Linear range is {0:3.2f} [urad]?.'.format(abs(linrange*calib)))
                _ax.vlines(x=c,ymin=-1,ymax=1,color='black',linestyle='--')                
                _ax.axvspan(c-linrange,c+linrange,color='gray',alpha=0.3)
                
            if 'SUM' in _name[n]:
                func = lambda x,a,b: a+b*x
                popt, pcov = curve_fit(func,x,_df[_name[n]+'.mean'])
                a,b = popt
                label = '{0:3.2f}*x + {1:3.2f}'.format(b,a)
                _ax.plot(_x,func(_x,*popt),label=label)   
                
            if 'SEG' in _name[n]:
                _ax.set_ylim(-10000,0)
            elif 'SUM' in _name[n]:
                _ax.set_ylim(0,20000)                    
            elif 'CRS' in _name[n]:
                _ax.set_ylim(-5000,5000)
            else:
                _ax.set_ylim(-1.1,1.1)
            _ax.legend(fontsize=8,loc='upper left',bbox_to_anchor=(1, 1))
            _ax.grid(which='major',color='gray',linestyle='--')
        else:
            break
    #
    fname = output.replace('data','results').replace('.txt','.png')
    plt.savefig(fname)
    if show:
        plt.show()    
    plt.close()
    return slope
    
if __name__=='__main__':
    #plot('./mco_yaw.txt')
    calibration('./data/MCO_TM_OPLEV_TILT_YAW.txt','MCO','TM','OPLEV_TILT','YAW',show=True)
    calibration('./data/MCO_TM_OPLEV_TILT_PIT.txt','MCO','TM','OPLEV_TILT','PIT',show=True)                    
    calibration('./data/MCI_TM_OPLEV_TILT_YAW.txt','MCI','TM','OPLEV_TILT','YAW',show=True)
    calibration('./data/MCI_TM_OPLEV_TILT_PIT.txt','MCI','TM','OPLEV_TILT','PIT',show=True)                
    calibration('./data/MCE_TM_OPLEV_TILT_YAW.txt','MCE','TM','OPLEV_TILT','YAW',show=True)
    calibration('./data/MCE_TM_OPLEV_TILT_PIT.txt','MCE','TM','OPLEV_TILT','PIT',show=True)    
    #calibration('mce_yaw.txt')
    #calibration('mce_pit.txt')
