#!/usr/bin/env python3
#! coding:utf-8
from cdsutils import avg
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

chname = []
plotnum = []
screw_pitch = 1.0 * 1000.0

def plot(output):
    f = open(output,'r',encoding='UTF-8')
    df = f.readlines()
    f.close()
    df = [i.split(',') for i in df]
    df = pd.read_csv(output,header=0)
    
    _name = ['K1:VIS-MCO_TM_OPLEV_TILT_SEG1_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_SEG2_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_SEG3_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_SEG4_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_PIT_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_YAW_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_SUM_INMON',
             'K1:VIS-MCO_TM_OPLEV_TILT_CRS_INMON']
    
    col,row = 3,3
    fig, ax = plt.subplots(col,row,figsize=(10,5),sharex=True)
    for i,ax_col in enumerate(ax):
        for j,_ax in enumerate(ax_col):
            if i==col-1:
                _ax.set_xlabel('Distance [um]')
            n = i*col+j

            if n>=len(_name):
                break
            # if 'INMON' in _name[n]:
            #     ylabel = 'Value [count]'
            # elif 'OUT':
            #     ylabel = 'Value [um]'
            ylabel = 'Value [a.u.]'
            _ax.set_ylabel(ylabel)
            
            if n<len(_name):                
                _ax.errorbar(x=df['Memo'],
                             y=df[_name[n]+'.mean'],
                             yerr=df[_name[n]+'.std'],
                             fmt='ko',label=_name[n],
                             markersize=2,capsize=3)
                _ax.legend(fontsize=7)
                if 'SEG' in _name[n]:
                    _ax.set_ylim(-10000,0)
                elif 'SUM' in _name[n]:
                    _ax.set_ylim(0,16000)                    
                elif 'CRS' in _name[n]:
                    _ax.set_ylim(-5000,5000)
                else:
                    _ax.set_ylim(-1,1)
            else:
                break
    #plt.show()
    plt.savefig('hoge.png')
    plt.close()
    
def init(epicschannel):
    f = open(epicschannel,'r',encoding='UTF-8')
    chname = f.readlines()
    f.close()
    chname = [name[:-1] for name in chname if name[0]!='#'] 
    chname = [ name.split(',') if ',' in name else [name, 999] for name in chname]
    plotnum = [int(i[1]) for i in chname]
    chname = [i[0] for i in chname]
    return plotnum, chname

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description='hoge')
    parser.add_argument('args1')
    parser.add_argument('-m','--memo')
    parser.add_argument('-f','--output',default='result.txt')
    parser.add_argument('-l','--epicschannel')
    parser.add_argument('-s','--screw_pitch',default = 1.0)
    args = parser.parse_args()
    memo = args.memo
    screw_pitch = args.screw_pitch
    print('screw_pitch :',screw_pitch)
    
    if args.args1=='add':
        plotnum, chname = init(args.epicschannel)

        now = datetime.now()
        avg = np.array(avg(1,chname,stddev=True))
        data = [[str(now),memo,*list(map(lambda x:'{0:.3f}'.format(x),avg.flatten()))]]
        #print(data[0])
        txt = ','.join(data[0])+'\n'
        #print(txt)
        
        with open(args.output,'a') as f:
            f.write(txt)
        plot(args.output)

    elif args.args1=='new':
        plotnum, chname = init(args.epicschannel)
        name = np.array([[ch+'.mean',ch+'.std'] for ch in chname]).flatten()
        txt = 'DateTime,Memo,'+','.join(name)+'\n'
        with open(args.output,'w') as f:
            f.write(txt)

        now = datetime.now()
        avg = np.array(avg(1,chname,stddev=True))
        data = [[str(now),memo,*list(map(lambda x:'{0:.3f}'.format(x),avg.flatten()))]]
        #print(data[0])
        print(data[0])
        txt = ','.join(data[0])+'\n'
        #print(txt)
        with open(args.output,'a') as f:
            f.write(txt)
        #print(len(data))
        plot(args.output)
        
    elif args.args1=='plot':
        plotnum, chname = init(args.epicschannel)
        plot(args.output)


