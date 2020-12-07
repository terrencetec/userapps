import subprocess
import ezca

from info import picoDict,stepperDict,optics
ezca = ezca.Ezca(timeout=0.1)
# ------------------------------------------------------------------------------

def hoge(name):
    '''
    '''
    try:
        optic,stage = name.split('_')
    except:
        optic,stage = name,None
        
    if optic in ['MCE','MCI','MCO','IMMT1','IMMT2','OMMT1','OMMT2','OSTM']:
        drivername = 'PICO_OP'
    elif optic in ['ETMX','ETMY','ITMX','ITMY'] and stage==None:
        drivername = 'PICO_BF'
    elif stage in ['BF','IM'] :
        drivername = 'PICO_{0}'.format(stage)
    elif stage in ['GAS','IP']:
        drivername = 'STEP_{0}'.format(stage)
    else:
        drivername = None
        
    chname = 'VIS-{0}_{1}_STATUS'.format(optic,drivername)
    return chname

    

driverDict = picoDict
driverDict.update(stepperDict)


if __name__=='__main__':

    drivernames = ['PICO_OP','PICO_IM','PICO_BF','STEP_GAS','STEP_IP']
    
    for optic in optics:
        for drivername in drivernames:
            try:
                print('VIS-{0}_{1}_STATUS'.format(optic,drivername))
                ezca['VIS-{0}_{1}_STATUS'.format(optic,drivername)] = -1
            except:
                print('No Channel VIS-{0}_{1}_STATUS'.format(optic,drivername))
                pass
    exit()
    for name,ipaddr in list(driverDict.items()):
        cmd = 'ping -w 1 {0}'.format(ipaddr)
        with open('out','w') as out:
            ret = subprocess.run(cmd,shell=True,check=False,stdout=out)
        if ret.returncode==0:
            chname = hoge(name)
            print('{0:10s}: OK         \t {1}'.format(name,chname))
            status = 1
        elif ret.returncode==1:
            chname = hoge(name)        
            print('{0:10s}: Unreachable\t {1}'.format(name,chname))
            status = 0
        else:
            raise ValueError('Unknown error.')

        if 'None' in chname:
            status = -1
        try:
            ezca[chname] = status
        except:
            pass
        
