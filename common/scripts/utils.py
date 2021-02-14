
import sys
sys.path.append('/opt/rtcds/userapps/release/sys/common/guardian')
import cdslib
import ezca
ezca = ezca.Ezca()

models = cdslib.get_active_model_dcuid()
feclist = [model[1] for model in models if 'vis' in model[0]]
models = cdslib.get_active_model_dcuid()
modellist = [model[0].replace('vis','') for model in models if 'vis' in model[0]]
modellist = [model  for model in modellist if 'mon' not in model]


def push_sdf_reload():    
    for fec in feclist:
        hoge = ezca['FEC-{0}_SDF_DROP_CNT'.format(fec)]
        if hoge!=0:
            print(fec,hoge,'Push sdf reload.')
            ezca['FEC-{0}_SDF_RELOAD'.format(fec)] = 2
        else:
            pass

def push_diag_reset():
    for fec in feclist:
        if ezca['FEC-{0}_DIAG_RESET'.format(fec)]!=0:
            ezca['FEC-{0}_DIAG_RESET'.format(fec)] = 1
        else:
            pass

def push_overflow_reset():
    for fec in feclist:
        ezca['FEC-{0}_OVERFLOW_RESET'.format(fec)] = 1
        

def push_wd_reset():
    modellist.remove('ts')
    modellist.remove('tmsx')
    modellist.remove('tmsy')
    for model in modellist:
        if model[-1]=='t':
            ezca['VIS-{0}_WD_RESET'.format(model[:-1].upper())] = 1
            ezca['VIS-{0}_TWR_DACKILL_RESET'.format(model[:-1].upper())] = 1
        elif model[-1]=='p':
            ezca['VIS-{0}_WD_RESET'.format(model[:-1].upper())] = 1
            ezca['VIS-{0}_PAY_DACKILL_RESET'.format(model[:-1].upper())] = 1
        else:
            ezca['VIS-{0}_WD_RESET'.format(model.upper())] = 1
            ezca['VIS-{0}_DACKILL_RESET'.format(model.upper())] = 1
        print(model)
            
if __name__=='__main__':
    push_sdf_reload()
    push_diag_reset()
    push_overflow_reset()
    push_wd_reset()
