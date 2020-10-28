#from ezca import Ezca as ezca
import ezca
_ezca = ezca.Ezca(ifo='K1')


dic = {'ITMY_L':['VIS-ITMY_IP_BLEND_LVDTL_INMON',+120],
       'ITMY_T':['VIS-ITMY_IP_BLEND_LVDTT_INMON',-700],
       'ITMY_Y':['VIS-ITMY_IP_BLEND_LVDTY_INMON',-600],
       'ETMY_L':['VIS-ETMY_IP_BLEND_LVDTL_INMON',+900],
       'ETMY_T':['VIS-ETMY_IP_BLEND_LVDTT_INMON',-400],
       'ETMY_Y':['VIS-ETMY_IP_BLEND_LVDTY_INMON',-450],              
       'ITMX_L':['VIS-ITMX_IP_BLEND_LVDTL_INMON',+500],
       'ITMX_T':['VIS-ITMX_IP_BLEND_LVDTT_INMON',1200],
       'ITMX_Y':['VIS-ITMX_IP_BLEND_LVDTY_INMON',-100],
}



for sus in ['ITMY','ITMX','ETMY']:
    for dof in ['L','T','Y']:
        chname,good = dic['{0}_{1}'.format(sus,dof)]
        data = _ezca.read(chname)
        if abs(data-good)>200:
            print(sus,dof,int(data-good))
        else:
            pass
