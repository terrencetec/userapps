import ezca
import cdsutils
from cdsutils import avg
from datetime import datetime
import pickle
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

chname = ['K1:VIS-IMMT1_TM_OPLEV_SEG1_OUT16',
          'K1:VIS-IMMT1_TM_OPLEV_SEG2_OUT16',
          'K1:VIS-IMMT1_TM_OPLEV_SEG3_OUT16',
          'K1:VIS-IMMT1_TM_OPLEV_SEG4_OUT16']

if __name__=='__main__':
    import argparse
    parser = argparse.ArgumentParser(description='hoge')
    parser.add_argument('args1')
    parser.add_argument('--memo')
    args = parser.parse_args()
    memo = args.memo
    
    if args.args1=='add':
        now = datetime.now()
        avg = np.array(avg(1,chname,stddev=True))
        data = [[str(now),memo,*list(map(lambda x:'{0:.3f}'.format(x),avg.flatten()))]]
        print(data[0])
        txt = ','.join(data[0])+'\n'
        print(txt)
        
        with open('result.txt','a') as f:
            f.write(txt)
        

    elif args.args1=='new':
        now = datetime.now()
        avg = np.array(avg(1,chname,stddev=True))
        data = [[str(now),memo,*list(map(lambda x:'{0:.3f}'.format(x),avg.flatten()))]]
        print(data[0])
        txt = ','.join(data[0])+'\n'
        print(txt)
        with open('result.txt','w') as f:
            f.write(txt)
            f.write(txt)            
        print(len(data))
        

    elif args.args1=='plot':
        df = pd.read_csv('result.txt')
        print(df)
        #print(df.columns[3])
        exit()
        plt.errorbar(df[1].astype(float),df[2],yerr=df[3],fmt='ko',
                     capsize=3,markersize=2,label='seg1')
        plt.errorbar(df[1].astype(float),df[4],yerr=df[5],fmt='ro',
                     capsize=3,markersize=2,label='seg2')
        plt.errorbar(df[1].astype(float),df[6],yerr=df[7],fmt='go',
                     capsize=3,markersize=2,label='seg3')
        plt.errorbar(df[1].astype(float),df[8],yerr=df[9],fmt='bo',
                     capsize=3,markersize=2,label='seg4')
        plt.ylim(0,200)
        plt.legend()
        plt.ylabel('[count]')
        plt.xlabel('Distance [mm]')
        plt.savefig('hoge.png')
        plt.close()
