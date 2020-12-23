
import subprocess
from datetime import datetime

import sys
#print(sys.path)
sys.path.append('/opt/rtcds/userapps/release/sys/common/guardian')
import cdslib
import ezca as ezca2

ezca=ezca2.Ezca()
FEMODELS = [(fe.name, fe.DCUID) for fe in list(cdslib.get_all_models())]
ifo='k1'
#hoge='prmt'

filename = '/opt/rtcds/kamioka/k1/target/gds/param/testpoint.par'
systems = dict() 
hostnames = []

def initialize():
    f = open(filename,'r')

    lines = f.readlines()
    newdict = False
    system = ''
    hostname = ''
    for line in lines:
        if line[0] == '[':
            newdict = True

        if newdict == True:
            if line.find('hostname=',0) == 0:
                hostname = line[9:-1]
                if hostname not in hostnames:
                    hostnames.append(hostname)

            if line.find('system=',0) == 0:
                system = line[7:-1]

                # Not including vis
                if line.find('vis') == -1:
                    newdict = False
                    system = ''
                    hostname = ''
            # `registerto systems
            if hostname != '' and system != '':
                systems[system] = hostname
                newdict = False
                system = ''
                hostname = ''

def getmodel2hostname(modelname):
    if len(systems) == 0:
        initialize()
    return systems[modelname]

def getHostnameList():
    if len(systems) == 0:
        initialize()
    return hostnames

def getmodels(sysname,optic):
  return [(name, dcuid) for (name, dcuid) in FEMODELS if sysname + optic in name]

def buildoptic(optic_tp, sysname='vis', make=False, makeinstall=False, restart=False):
    '''
    String :: optic name
    String :: subsystem name (default = 'vis')
    Bool   :: make flg (default = Falase)
    Bool   :: make install flg (default = Falase)
    Bool   :: restart flg (default = Falase)
    -> Int :: exit code
    '''

    if optic_tp[-1:] == 't' or optic_tp[-1:] == 'p':
        optic = optic_tp[:-1]
    else:
        optic = optic_tp[:-1]

    models = [(name, dcuid) for (name, dcuid) in FEMODELS if sysname + optic_tp in name]

    for (model, fec) in models:
        '''
        Condition:
            Guardian state == SAFE
            Commish status == OFF
            Commish message == NULL
            SDF diff == 0
            CFC bit == OFF
        '''

        flag = ezca['GRD-' + (sysname + '_' + optic).upper() + '_STATE_S'] == 'SAFE'
        flag &= ezca[(sysname + '-' + optic).upper() + '_COMMISH_STATUS'] == 1
        flag &= ezca[(sysname + '-' + optic).upper() + '_COMMISH_MESSAGE'] != ''
        flag &= ezca['FEC-' + str(fec) + '_SDF_DIFF_CNT'] == 0
        flag &= int(ezca['FEC-' + str(fec) + '_STATE_WORD']) & 1024 == 0

        node = getmodel2hostname(ifo + model)
        ret = False
        if flag == True:
            ret = buildmodel(ifo + model, node, make, makeinstall, restart)

        #if ret:
        #    ezca[(sysname + '-' + optic).upper() + '_INSTALLED_DATE'] = datetime.now().strftime("%Y-%m-%d")
    #return 0

def buildmodel(model, node, make=False, makeinstall=False, restart=False):
    '''
    String :: model name
    String :: node name
    Bool   :: make flg (default = Falase)
    Bool   :: make install flg (default = Falase)
    Bool   :: restart flg (default = Falase)
    -> Int :: exit code
    '''

    ssh=["ssh", "-oStrictHostKeyChecking=no", node]
    cmd = 'cd /opt/rtcds/kamioka/k1/rtbuild/current/'
    if make == True:
        cmd += ' && make ' + model
    if makeinstall == True:
        cmd += ' && make install-' + model
    if restart == True:
        cmd += ' && cd /opt/rtcds/userapps/release/cds/common/scripts'
        cmd += ' && ./restart_slave_model.sh ' + model

    ret=subprocess.run(ssh + [cmd],
                           # stdout = subprocess.DEVNULL,
                           # stderr = subprocess.DEVNULL,
    )
    return ret.returncode == 0

if __name__ == "__main__":


    buildoptic(hoge,'vis',True,False,False)
