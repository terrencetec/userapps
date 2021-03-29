#!/usr/bin/env python3
#! coding:utf-8

import os
from cdsutils import avg
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

chname = []
plotnum = []

def plot(chname,output):
    '''
    '''
    df = pd.read_csv(output,header=0)
    col,row = 3,3
    fig, ax = plt.subplots(col,row,figsize=(10,5),sharex=True)
    for i,ax_col in enumerate(ax):
        for j,_ax in enumerate(ax_col):
            if i==col-1:
                _ax.set_xlabel('Distance [um]')
            n = i*col+j

            if n>=len(chname):
                break
            ylabel = 'Value [a.u.]'
            _ax.set_ylabel(ylabel)
            
            if n<len(chname):           
                _ax.errorbar(x=df['Disp'],
                             y=df[chname[n]+'.mean'],
                             yerr=df[chname[n]+'.std'],
                             fmt='ko',label=chname[n],
                             markersize=2,capsize=3)
                _ax.legend(fontsize=7)
                if 'SEG' in chname[n]:
                    _ax.set_ylim(-10000,0)
                elif 'SUM' in chname[n]:
                    _ax.set_ylim(0,16000)                    
                elif 'CRS' in chname[n]:
                    _ax.set_ylim(-5000,5000)
                else:
                    _ax.set_ylim(-1,1)
            else:
                break
    plt.show()
    plt.savefig('hoge.png')
    plt.close()
    
def init(channellist):
    '''
    '''
    with open(channellist,'r',encoding='UTF-8') as f: 
        chname = f.read().splitlines()
        chname = [name for name in chname if name[0]!='#']
    return chname

def getdata(channel):
    '''
    '''
    now = datetime.now()
    _avg = np.array(avg(1,chname,stddev=True))        
    data = [[str(now),disp,*list(map(lambda x:'{0:.3f}'.format(x),_avg.flatten()))]]
    return data
    
def add(chname,output):
    data = getdata(chname)
    txt = ','.join(data[0])+'\n'        
    with open(output,'a') as f:
        f.write(txt)

def init(chname,output):
    data = getdata(chname)        
    name = np.array([[ch+'.mean',ch+'.std'] for ch in chname]).flatten()
    txt = 'DateTime,Disp,'+','.join(name)+'\n'
    with open(args.output,'w') as f:
        f.write(txt)
        

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description='hoge')
    parser.add_argument('args1')
    parser.add_argument('-d','--disp',default='34')
    parser.add_argument('-f','--output',default='output.txt')
    args = parser.parse_args()
    disp = args.disp

    dofs = ['SEG1','SEG2','SEG3','SEG4','PIT','YAW','SUM','CRS']
    optic = 'MCE'
    func = 'OPLEV_TILT'
    chname = []
    for dof in dofs:
        chname +=['K1:VIS-{0}_TM_{1}_{2}_INMON'.format(optic,func,dof)]

    if args.args1=='plot':
        plot(chname,args.output)
        exit()

    if args.args1=='init':
        init(chname,args.output)
        
    if os.path.exists(args.output):
        add(chname,args.output)
        plot(chname,args.output)                
    else:
        init(chname,args.output)
        add(chname,args.output)        
        plot(chname,args.output)        
