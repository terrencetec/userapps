class VIS():
    def __init__(self,OPTIC):
        for _type in VIS_DICT['type']:
            if OPTIC in VIS_DICT[_type]:
                self.type=_type
                self.levels=VIS_DICT[_type+'_levels']
                self.INMON=VIS_DICT[_type+'_INMON']
                self.OUTMON=VIS_DICT[_type+'_OUTMON']
default_lim=[-2**15,2**15]
default_OL_SUM=[1000,100000]
VIS_DICT={
# VIS Types
'type':['typeA','typeB','typeBp'],

# VIS-Optics Dictionary
'typeA':['ITMX','ITMY','ETMX','ETMY'],
'typeB':['BS','SR2','SR3','SRM'],
'typeBp':['PR2','PR3','PRM'],
'typeC':['MCI','MCO','MCE','IMMT1','IMMT2','OMMT1','OMMT2','OSTM'],

# VIS-levels Dictionary
'typeA_levels':['IP','F0','F1','F2','F3','BF','MN','IM','TM'],
'typeB_levels':['IP','F0','F1','BF','IM','TM'],
'typeBp_levels':['SF','BF','IM','TM'],
'typeC_levels':[],

# Type A Channels
'typeA_INMON':[
'IP_LVDTINF_H1','IP_LVDTINF_H2','IP_LVDTINF_H3',
'IP_ACCINF_H1','IP_ACCINF_H2','IP_ACCINF_H3',
'F0_LVDTINF_GAS','F1_LVDTINF_GAS','F2_LVDTINF_GAS','F3_LVDTINF_GAS','BF_LVDTINF_GAS',
'BF_LVDTINF_V1','BF_LVDTINF_V2','BF_LVDTINF_V3','BF_LVDTINF_H1','BF_LVDTINF_H2','BF_LVDTINF_H3',
'MN_PSINF_V1','MN_PSINF_V2','MN_PSINF_V3','MN_PSINF_H1','MN_PSINF_H2','MN_PSINF_H3',
'MN_OPLEV_TILT_PIT','MN_OPLEV_TILT_YAW','MN_OPLEV_TILT_SUM',
'IM_PSINF_V1','IM_PSINF_V2','IM_PSINF_V3','IM_PSINF_H1','IM_PSINF_H2','IM_PSINF_H3',
'TM_OPLEV_LEN_PIT','TM_OPLEV_LEN_YAW','TM_OPLEV_LEN_SUM','TM_OPLEV_TILT_PIT','TM_OPLEV_TILT_YAW','TM_OPLEV_TILT_SUM'
],
'typeA_OUTMON':[
'IP_COILOUTF_H1','IP_COILOUTF_H2','IP_COILOUTF_H3',
'F0_COILOUTF_GAS','F1_COILOUTF_GAS','F2_COILOUTF_GAS','F3_COILOUTF_GAS','BF_COILOUTF_GAS',
'BF_COILOUTF_V1','BF_COILOUTF_V2','BF_COILOUTF_V3','BF_COILOUTF_H1','BF_COILOUTF_H2','BF_COILOUTF_H3',
'MN_COILOUTF_V1','MN_COILOUTF_V2','MN_COILOUTF_V3','MN_COILOUTF_H1','MN_COILOUTF_H2','MN_COILOUTF_H3',
'IM_COILOUTF_V1','IM_COILOUTF_V2','IM_COILOUTF_V3','IM_COILOUTF_H1','IM_COILOUTF_H2','IM_COILOUTF_H3',
'TM_COILOUTF_H1','TM_COILOUTF_H2','TM_COILOUTF_H3','TM_COILOUTF_H4'
],

# Type A Channel Limits
'ITMX_INMON_lim':{
'IP_LVDTINF_H1':default_lim,'IP_LVDTINF_H2':default_lim,'IP_LVDTINF_H3':default_lim,
'IP_ACCINF_H1':default_lim,'IP_ACCINF_H2':default_lim,'IP_ACCINF_H3':default_lim,
'F0_LVDTINF_GAS':default_lim,'F1_LVDTINF_GAS':default_lim,'F2_LVDTINF_GAS':default_lim,'F3_LVDTINF_GAS':default_lim,'BF_LVDTINF_GAS':default_lim,
'BF_LVDTINF_V1':default_lim,'BF_LVDTINF_V2':default_lim,'BF_LVDTINF_V3':default_lim,'BF_LVDTINF_H1':default_lim,'BF_LVDTINF_H2':default_lim,'BF_LVDTINF_H3':default_lim,
'MN_PSINF_V1':default_lim,'MN_PSINF_V2':default_lim,'MN_PSINF_V3':default_lim,'MN_PSINF_H1':default_lim,'MN_PSINF_H2':default_lim,'MN_PSINF_H3':default_lim,
'MN_OPLEV_TILT_PIT':[-1,1],'MN_OPLEV_TILT_YAW':[-1,1],'MN_OPLEV_TILT_SUM':default_OL_SUM,
'IM_PSINF_V1':default_lim,'IM_PSINF_V2':default_lim,'IM_PSINF_V3':default_lim,'IM_PSINF_H1':default_lim,'IM_PSINF_H2':default_lim,'IM_PSINF_H3':default_lim,
'TM_OPLEV_LEN_PIT':[-1,1],'TM_OPLEV_LEN_YAW':[-1,1],'TM_OPLEV_LEN_SUM':default_OL_SUM,'TM_OPLEV_TILT_PIT':[-1,1],'TM_OPLEV_TILT_YAW':[-1,1],'TM_OPLEV_TILT_SUM':default_OL_SUM
},
'ITMX_OUTMON_lim':{
'IP_COILOUTF_H1':default_lim,'IP_COILOUTF_H2':default_lim,'IP_COILOUTF_H3':default_lim,
'F0_COILOUTF_GAS':default_lim,'F1_COILOUTF_GAS':default_lim,'F2_COILOUTF_GAS':default_lim,'F3_COILOUTF_GAS':default_lim,'BF_COILOUTF_GAS':default_lim,
'BF_COILOUTF_V1':default_lim,'BF_COILOUTF_V2':default_lim,'BF_COILOUTF_V3':default_lim,'BF_COILOUTF_H1':default_lim,'BF_COILOUTF_H2':default_lim,'BF_COILOUTF_H3':default_lim,
'MN_COILOUTF_V1':default_lim,'MN_COILOUTF_V2':default_lim,'MN_COILOUTF_V3':default_lim,'MN_COILOUTF_H1':default_lim,'MN_COILOUTF_H2':default_lim,'MN_COILOUTF_H3':default_lim,
'IM_COILOUTF_V1':default_lim,'IM_COILOUTF_V2':default_lim,'IM_COILOUTF_V3':default_lim,'IM_COILOUTF_H1':default_lim,'IM_COILOUTF_H2':default_lim,'IM_COILOUTF_H3':default_lim,
'TM_COILOUTF_H1':default_lim,'TM_COILOUTF_H2':default_lim,'TM_COILOUTF_H3':default_lim,'TM_COILOUTF_H4':default_lim
},

'ITMY_INMON_lim':{
'IP_LVDTINF_H1':default_lim,'IP_LVDTINF_H2':default_lim,'IP_LVDTINF_H3':default_lim,
'IP_ACCINF_H1':default_lim,'IP_ACCINF_H2':default_lim,'IP_ACCINF_H3':default_lim,
'F0_LVDTINF_GAS':default_lim,'F1_LVDTINF_GAS':default_lim,'F2_LVDTINF_GAS':default_lim,'F3_LVDTINF_GAS':default_lim,'BF_LVDTINF_GAS':default_lim,
'BF_LVDTINF_V1':default_lim,'BF_LVDTINF_V2':default_lim,'BF_LVDTINF_V3':default_lim,'BF_LVDTINF_H1':default_lim,'BF_LVDTINF_H2':default_lim,'BF_LVDTINF_H3':default_lim,
'MN_PSINF_V1':default_lim,'MN_PSINF_V2':default_lim,'MN_PSINF_V3':default_lim,'MN_PSINF_H1':default_lim,'MN_PSINF_H2':default_lim,'MN_PSINF_H3':default_lim,
'MN_OPLEV_TILT_PIT':[-1,1],'MN_OPLEV_TILT_YAW':[-1,1],'MN_OPLEV_TILT_SUM':default_OL_SUM,
'IM_PSINF_V1':default_lim,'IM_PSINF_V2':default_lim,'IM_PSINF_V3':default_lim,'IM_PSINF_H1':default_lim,'IM_PSINF_H2':default_lim,'IM_PSINF_H3':default_lim,
'TM_OPLEV_LEN_PIT':[-1,1],'TM_OPLEV_LEN_YAW':[-1,1],'TM_OPLEV_LEN_SUM':default_OL_SUM,'TM_OPLEV_TILT_PIT':[-1,1],'TM_OPLEV_TILT_YAW':[-1,1],'TM_OPLEV_TILT_SUM':default_OL_SUM
},
'ITMY_OUTMON_lim':{
'IP_COILOUTF_H1':default_lim,'IP_COILOUTF_H2':default_lim,'IP_COILOUTF_H3':default_lim,
'F0_COILOUTF_GAS':default_lim,'F1_COILOUTF_GAS':default_lim,'F2_COILOUTF_GAS':default_lim,'F3_COILOUTF_GAS':default_lim,'BF_COILOUTF_GAS':default_lim,
'BF_COILOUTF_V1':default_lim,'BF_COILOUTF_V2':default_lim,'BF_COILOUTF_V3':default_lim,'BF_COILOUTF_H1':default_lim,'BF_COILOUTF_H2':default_lim,'BF_COILOUTF_H3':default_lim,
'MN_COILOUTF_V1':default_lim,'MN_COILOUTF_V2':default_lim,'MN_COILOUTF_V3':default_lim,'MN_COILOUTF_H1':default_lim,'MN_COILOUTF_H2':default_lim,'MN_COILOUTF_H3':default_lim,
'IM_COILOUTF_V1':default_lim,'IM_COILOUTF_V2':default_lim,'IM_COILOUTF_V3':default_lim,'IM_COILOUTF_H1':default_lim,'IM_COILOUTF_H2':default_lim,'IM_COILOUTF_H3':default_lim,
'TM_COILOUTF_H1':default_lim,'TM_COILOUTF_H2':default_lim,'TM_COILOUTF_H3':default_lim,'TM_COILOUTF_H4':default_lim
},

'ETMX_INMON_lim':{
'IP_LVDTINF_H1':default_lim,'IP_LVDTINF_H2':default_lim,'IP_LVDTINF_H3':default_lim,
'IP_ACCINF_H1':default_lim,'IP_ACCINF_H2':default_lim,'IP_ACCINF_H3':default_lim,
'F0_LVDTINF_GAS':default_lim,'F1_LVDTINF_GAS':default_lim,'F2_LVDTINF_GAS':default_lim,'F3_LVDTINF_GAS':default_lim,'BF_LVDTINF_GAS':default_lim,
'BF_LVDTINF_V1':default_lim,'BF_LVDTINF_V2':default_lim,'BF_LVDTINF_V3':default_lim,'BF_LVDTINF_H1':default_lim,'BF_LVDTINF_H2':default_lim,'BF_LVDTINF_H3':default_lim,
'MN_PSINF_V1':default_lim,'MN_PSINF_V2':default_lim,'MN_PSINF_V3':default_lim,'MN_PSINF_H1':default_lim,'MN_PSINF_H2':default_lim,'MN_PSINF_H3':default_lim,
'MN_OPLEV_TILT_PIT':[-1,1],'MN_OPLEV_TILT_YAW':[-1,1],'MN_OPLEV_TILT_SUM':default_OL_SUM,
'IM_PSINF_V1':default_lim,'IM_PSINF_V2':default_lim,'IM_PSINF_V3':default_lim,'IM_PSINF_H1':default_lim,'IM_PSINF_H2':default_lim,'IM_PSINF_H3':default_lim,
'TM_OPLEV_LEN_PIT':[-1,1],'TM_OPLEV_LEN_YAW':[-1,1],'TM_OPLEV_LEN_SUM':default_OL_SUM,'TM_OPLEV_TILT_PIT':[-1,1],'TM_OPLEV_TILT_YAW':[-1,1],'TM_OPLEV_TILT_SUM':default_OL_SUM
},
'ETMX_OUTMON_lim':{
'IP_COILOUTF_H1':default_lim,'IP_COILOUTF_H2':default_lim,'IP_COILOUTF_H3':default_lim,
'F0_COILOUTF_GAS':default_lim,'F1_COILOUTF_GAS':default_lim,'F2_COILOUTF_GAS':default_lim,'F3_COILOUTF_GAS':default_lim,'BF_COILOUTF_GAS':default_lim,
'BF_COILOUTF_V1':default_lim,'BF_COILOUTF_V2':default_lim,'BF_COILOUTF_V3':default_lim,'BF_COILOUTF_H1':default_lim,'BF_COILOUTF_H2':default_lim,'BF_COILOUTF_H3':default_lim,
'MN_COILOUTF_V1':default_lim,'MN_COILOUTF_V2':default_lim,'MN_COILOUTF_V3':default_lim,'MN_COILOUTF_H1':default_lim,'MN_COILOUTF_H2':default_lim,'MN_COILOUTF_H3':default_lim,
'IM_COILOUTF_V1':default_lim,'IM_COILOUTF_V2':default_lim,'IM_COILOUTF_V3':default_lim,'IM_COILOUTF_H1':default_lim,'IM_COILOUTF_H2':default_lim,'IM_COILOUTF_H3':default_lim,
'TM_COILOUTF_H1':default_lim,'TM_COILOUTF_H2':default_lim,'TM_COILOUTF_H3':default_lim,'TM_COILOUTF_H4':default_lim
},

'ETMY_INMON_lim':{
'IP_LVDTINF_H1':default_lim,'IP_LVDTINF_H2':default_lim,'IP_LVDTINF_H3':default_lim,
'IP_ACCINF_H1':default_lim,'IP_ACCINF_H2':default_lim,'IP_ACCINF_H3':default_lim,
'F0_LVDTINF_GAS':default_lim,'F1_LVDTINF_GAS':default_lim,'F2_LVDTINF_GAS':default_lim,'F3_LVDTINF_GAS':default_lim,'BF_LVDTINF_GAS':default_lim,
'BF_LVDTINF_V1':default_lim,'BF_LVDTINF_V2':default_lim,'BF_LVDTINF_V3':default_lim,'BF_LVDTINF_H1':default_lim,'BF_LVDTINF_H2':default_lim,'BF_LVDTINF_H3':default_lim,
'MN_PSINF_V1':default_lim,'MN_PSINF_V2':default_lim,'MN_PSINF_V3':default_lim,'MN_PSINF_H1':default_lim,'MN_PSINF_H2':default_lim,'MN_PSINF_H3':default_lim,
'MN_OPLEV_TILT_PIT':[-1,1],'MN_OPLEV_TILT_YAW':[-1,1],'MN_OPLEV_TILT_SUM':default_OL_SUM,
'IM_PSINF_V1':default_lim,'IM_PSINF_V2':default_lim,'IM_PSINF_V3':default_lim,'IM_PSINF_H1':default_lim,'IM_PSINF_H2':default_lim,'IM_PSINF_H3':default_lim,
'TM_OPLEV_LEN_PIT':[-1,1],'TM_OPLEV_LEN_YAW':[-1,1],'TM_OPLEV_LEN_SUM':default_OL_SUM,'TM_OPLEV_TILT_PIT':[-1,1],'TM_OPLEV_TILT_YAW':[-1,1],'TM_OPLEV_TILT_SUM':default_OL_SUM
},
'ETMY_OUTMON_lim':{
'IP_COILOUTF_H1':default_lim,'IP_COILOUTF_H2':default_lim,'IP_COILOUTF_H3':default_lim,
'F0_COILOUTF_GAS':default_lim,'F1_COILOUTF_GAS':default_lim,'F2_COILOUTF_GAS':default_lim,'F3_COILOUTF_GAS':default_lim,'BF_COILOUTF_GAS':default_lim,
'BF_COILOUTF_V1':default_lim,'BF_COILOUTF_V2':default_lim,'BF_COILOUTF_V3':default_lim,'BF_COILOUTF_H1':default_lim,'BF_COILOUTF_H2':default_lim,'BF_COILOUTF_H3':default_lim,
'MN_COILOUTF_V1':default_lim,'MN_COILOUTF_V2':default_lim,'MN_COILOUTF_V3':default_lim,'MN_COILOUTF_H1':default_lim,'MN_COILOUTF_H2':default_lim,'MN_COILOUTF_H3':default_lim,
'IM_COILOUTF_V1':default_lim,'IM_COILOUTF_V2':default_lim,'IM_COILOUTF_V3':default_lim,'IM_COILOUTF_H1':default_lim,'IM_COILOUTF_H2':default_lim,'IM_COILOUTF_H3':default_lim,
'TM_COILOUTF_H1':default_lim,'TM_COILOUTF_H2':default_lim,'TM_COILOUTF_H3':default_lim,'TM_COILOUTF_H4':default_lim
},

# Type B Channels
'typeB_INMON':[
'IP_LVDTINF_H1','IP_LVDTINF_H2','IP_LVDTINF_H3',
'IP_ACCINF_H1','IP_ACCINF_H2','IP_ACCINF_H3',
'F0_LVDTINF_GAS','F1_LVDTINF_GAS','BF_LVDTINF_GAS',
'IM_OSEMINF_V1','IM_OSEMINF_V2','IM_OSEMINF_V3','IM_OSEMINF_H1','IM_OSEMINF_H2','IM_OSEMINF_H3',
'TM_OPLEV_LEN_PIT','TM_OPLEV_LEN_YAW','TM_OPLEV_LEN_SUM','TM_OPLEV_TILT_PIT','TM_OPLEV_TILT_YAW','TM_OPLEV_TILT_SUM'
],

'typeB_OUTMON':[
'IP_COILOUTF_H1','IP_COILOUTF_H2','IP_COILOUTF_H3',
'F0_COILOUTF_GAS','F1_COILOUTF_GAS','BF_COILOUTF_GAS',
'IM_COILOUTF_V1','IM_COILOUTF_V2','IM_COILOUTF_V3','IM_COILOUTF_H1','IM_COILOUTF_H2','IM_COILOUTF_H3',
'TM_COILOUTF_H1','TM_COILOUTF_H2','TM_COILOUTF_H3','TM_COILOUTF_H4'
],

# Type B Channel Limits
'BS_INMON_lim':{
'IP_LVDTINF_H1':default_lim,'IP_LVDTINF_H2':default_lim,'IP_LVDTINF_H3':default_lim,
'IP_ACCINF_H1':default_lim,'IP_ACCINF_H2':default_lim,'IP_ACCINF_H3':default_lim,
'F0_LVDTINF_GAS':default_lim,'F1_LVDTINF_GAS':default_lim,'BF_LVDTINF_GAS':default_lim,
'IM_OSEMINF_V1':default_lim,'IM_OSEMINF_V2':default_lim,'IM_OSEMINF_V3':default_lim,'IM_OSEMINF_H1':default_lim,'IM_OSEMINF_H2':default_lim,'IM_OSEMINF_H3':default_lim,
'TM_OPLEV_LEN_PIT':[-1,1],'TM_OPLEV_LEN_YAW':[-1,1],'TM_OPLEV_LEN_SUM':default_OL_SUM,'TM_OPLEV_TILT_PIT':[-1,1],'TM_OPLEV_TILT_YAW':[-1,1],'TM_OPLEV_TILT_SUM':default_OL_SUM
},
'BS_OUTMON_lim':{
'IP_COILOUTF_H1':default_lim,'IP_COILOUTF_H2':default_lim,'IP_COILOUTF_H3':default_lim,
'F0_COILOUTF_GAS':default_lim,'F1_COILOUTF_GAS':default_lim,'BF_COILOUTF_GAS':default_lim,
'IM_COILOUTF_V1':default_lim,'IM_COILOUTF_V2':default_lim,'IM_COILOUTF_V3':default_lim,'IM_COILOUTF_H1':default_lim,'IM_COILOUTF_H2':default_lim,'IM_COILOUTF_H3':default_lim,
'TM_COILOUTF_H1':default_lim,'TM_COILOUTF_H2':default_lim,'TM_COILOUTF_H3':default_lim,'TM_COILOUTF_H4':default_lim
},

'SR2_INMON_lim':{
'IP_LVDTINF_H1':default_lim,'IP_LVDTINF_H2':default_lim,'IP_LVDTINF_H3':default_lim,
'IP_ACCINF_H1':default_lim,'IP_ACCINF_H2':default_lim,'IP_ACCINF_H3':default_lim,
'F0_LVDTINF_GAS':default_lim,'F1_LVDTINF_GAS':default_lim,'BF_LVDTINF_GAS':default_lim,
'IM_OSEMINF_V1':default_lim,'IM_OSEMINF_V2':default_lim,'IM_OSEMINF_V3':default_lim,'IM_OSEMINF_H1':default_lim,'IM_OSEMINF_H2':default_lim,'IM_OSEMINF_H3':default_lim,
'TM_OPLEV_LEN_PIT':[-1,1],'TM_OPLEV_LEN_YAW':[-1,1],'TM_OPLEV_LEN_SUM':default_OL_SUM,'TM_OPLEV_TILT_PIT':[-1,1],'TM_OPLEV_TILT_YAW':[-1,1],'TM_OPLEV_TILT_SUM':default_OL_SUM
},
'SR2_OUTMON_lim':{
'IP_COILOUTF_H1':default_lim,'IP_COILOUTF_H2':default_lim,'IP_COILOUTF_H3':default_lim,
'F0_COILOUTF_GAS':default_lim,'F1_COILOUTF_GAS':default_lim,'BF_COILOUTF_GAS':default_lim,
'IM_COILOUTF_V1':default_lim,'IM_COILOUTF_V2':default_lim,'IM_COILOUTF_V3':default_lim,'IM_COILOUTF_H1':default_lim,'IM_COILOUTF_H2':default_lim,'IM_COILOUTF_H3':default_lim,
'TM_COILOUTF_H1':default_lim,'TM_COILOUTF_H2':default_lim,'TM_COILOUTF_H3':default_lim,'TM_COILOUTF_H4':default_lim
},

'SR3_INMON_lim':{
'IP_LVDTINF_H1':default_lim,'IP_LVDTINF_H2':default_lim,'IP_LVDTINF_H3':default_lim,
'IP_ACCINF_H1':default_lim,'IP_ACCINF_H2':default_lim,'IP_ACCINF_H3':default_lim,
'F0_LVDTINF_GAS':default_lim,'F1_LVDTINF_GAS':default_lim,'BF_LVDTINF_GAS':default_lim,
'IM_OSEMINF_V1':default_lim,'IM_OSEMINF_V2':default_lim,'IM_OSEMINF_V3':default_lim,'IM_OSEMINF_H1':default_lim,'IM_OSEMINF_H2':default_lim,'IM_OSEMINF_H3':default_lim,
'TM_OPLEV_LEN_PIT':[-1,1],'TM_OPLEV_LEN_YAW':[-1,1],'TM_OPLEV_LEN_SUM':default_OL_SUM,'TM_OPLEV_TILT_PIT':[-1,1],'TM_OPLEV_TILT_YAW':[-1,1],'TM_OPLEV_TILT_SUM':default_OL_SUM
},
'SR3_OUTMON_lim':{
'IP_COILOUTF_H1':default_lim,'IP_COILOUTF_H2':default_lim,'IP_COILOUTF_H3':default_lim,
'F0_COILOUTF_GAS':default_lim,'F1_COILOUTF_GAS':default_lim,'BF_COILOUTF_GAS':default_lim,
'IM_COILOUTF_V1':default_lim,'IM_COILOUTF_V2':default_lim,'IM_COILOUTF_V3':default_lim,'IM_COILOUTF_H1':default_lim,'IM_COILOUTF_H2':default_lim,'IM_COILOUTF_H3':default_lim,
'TM_COILOUTF_H1':default_lim,'TM_COILOUTF_H2':default_lim,'TM_COILOUTF_H3':default_lim,'TM_COILOUTF_H4':default_lim
},

'SRM_INMON_lim':{
'IP_LVDTINF_H1':default_lim,'IP_LVDTINF_H2':default_lim,'IP_LVDTINF_H3':default_lim,
'IP_ACCINF_H1':default_lim,'IP_ACCINF_H2':default_lim,'IP_ACCINF_H3':default_lim,
'F0_LVDTINF_GAS':default_lim,'F1_LVDTINF_GAS':default_lim,'BF_LVDTINF_GAS':default_lim,
'IM_OSEMINF_V1':default_lim,'IM_OSEMINF_V2':default_lim,'IM_OSEMINF_V3':default_lim,'IM_OSEMINF_H1':default_lim,'IM_OSEMINF_H2':default_lim,'IM_OSEMINF_H3':default_lim,
'TM_OPLEV_LEN_PIT':[-1,1],'TM_OPLEV_LEN_YAW':[-1,1],'TM_OPLEV_LEN_SUM':default_OL_SUM,'TM_OPLEV_TILT_PIT':[-1,1],'TM_OPLEV_TILT_YAW':[-1,1],'TM_OPLEV_TILT_SUM':default_OL_SUM
},
'SRM_OUTMON_lim':{
'IP_COILOUTF_H1':default_lim,'IP_COILOUTF_H2':default_lim,'IP_COILOUTF_H3':default_lim,
'F0_COILOUTF_GAS':default_lim,'F1_COILOUTF_GAS':default_lim,'BF_COILOUTF_GAS':default_lim,
'IM_COILOUTF_V1':default_lim,'IM_COILOUTF_V2':default_lim,'IM_COILOUTF_V3':default_lim,'IM_COILOUTF_H1':default_lim,'IM_COILOUTF_H2':default_lim,'IM_COILOUTF_H3':default_lim,
'TM_COILOUTF_H1':default_lim,'TM_COILOUTF_H2':default_lim,'TM_COILOUTF_H3':default_lim,'TM_COILOUTF_H4':default_lim
},

# Type Bp Channels
'typeBp_INMON':[
'SF_LVDTINF_GAS','BF_LVDTINF_GAS',
'BF_LVDTINF_V1','BF_LVDTINF_V2','BF_LVDTINF_V3','BF_LVDTINF_H1','BF_LVDTINF_H2','BF_LVDTINF_H3',
'IM_OSEMINF_V1','IM_OSEMINF_V2','IM_OSEMINF_V3','IM_OSEMINF_H1','IM_OSEMINF_H2','IM_OSEMINF_H3',
'TM_OPLEV_LEN_PIT','TM_OPLEV_LEN_YAW','TM_OPLEV_LEN_SUM','TM_OPLEV_TILT_PIT','TM_OPLEV_TILT_YAW','TM_OPLEV_TILT_SUM'
],

'typeBp_OUTMON':[
'SF_COILOUTF_GAS','BF_COILOUTF_GAS',
'BF_COILOUTF_V1','BF_COILOUTF_V2','BF_COILOUTF_V3','BF_COILOUTF_H1','BF_COILOUTF_H2','BF_COILOUTF_H3',
'IM_COILOUTF_V1','IM_COILOUTF_V2','IM_COILOUTF_V3','IM_COILOUTF_H1','IM_COILOUTF_H2','IM_COILOUTF_H3',
'TM_COILOUTF_H1','TM_COILOUTF_H2','TM_COILOUTF_H3','TM_COILOUTF_H4'
],
# Type Bp Channel Limits
'PR2_INMON_lim':{
'SF_LVDTINF_GAS':default_lim,'BF_LVDTINF_GAS':default_lim,
'BF_LVDTINF_V1':default_lim,'BF_LVDTINF_V2':default_lim,'BF_LVDTINF_V3':default_lim,'BF_LVDTINF_H1':default_lim,'BF_LVDTINF_H2':default_lim,'BF_LVDTINF_H3':default_lim,
'IM_OSEMINF_V1':default_lim,'IM_OSEMINF_V2':default_lim,'IM_OSEMINF_V3':default_lim,'IM_OSEMINF_H1':default_lim,'IM_OSEMINF_H2':default_lim,'IM_OSEMINF_H3':default_lim,
'TM_OPLEV_LEN_PIT':[-1,1],'TM_OPLEV_LEN_YAW':[-1,1],'TM_OPLEV_LEN_SUM':default_OL_SUM,'TM_OPLEV_TILT_PIT':[-1,1],'TM_OPLEV_TILT_YAW':[-1,1],'TM_OPLEV_TILT_SUM':default_OL_SUM
},
'PR2_OUTMON_lim':{
'SF_COILOUTF_GAS':default_lim,'BF_COILOUTF_GAS':default_lim,
'BF_COILOUTF_V1':default_lim,'BF_COILOUTF_V2':default_lim,'BF_COILOUTF_V3':default_lim,'BF_COILOUTF_H1':default_lim,'BF_COILOUTF_H2':default_lim,'BF_COILOUTF_H3':default_lim,
'IM_COILOUTF_V1':default_lim,'IM_COILOUTF_V2':default_lim,'IM_COILOUTF_V3':default_lim,'IM_COILOUTF_H1':default_lim,'IM_COILOUTF_H2':default_lim,'IM_COILOUTF_H3':default_lim,
'TM_COILOUTF_H1':default_lim,'TM_COILOUTF_H2':default_lim,'TM_COILOUTF_H3':default_lim,'TM_COILOUTF_H4':default_lim
},

'PR3_INMON_lim':{
'SF_LVDTINF_GAS':default_lim,'BF_LVDTINF_GAS':default_lim,
'BF_LVDTINF_V1':default_lim,'BF_LVDTINF_V2':default_lim,'BF_LVDTINF_V3':default_lim,'BF_LVDTINF_H1':default_lim,'BF_LVDTINF_H2':default_lim,'BF_LVDTINF_H3':default_lim,
'IM_OSEMINF_V1':default_lim,'IM_OSEMINF_V2':default_lim,'IM_OSEMINF_V3':default_lim,'IM_OSEMINF_H1':default_lim,'IM_OSEMINF_H2':default_lim,'IM_OSEMINF_H3':default_lim,
'TM_OPLEV_LEN_PIT':[-1,1],'TM_OPLEV_LEN_YAW':[-1,1],'TM_OPLEV_LEN_SUM':default_OL_SUM,'TM_OPLEV_TILT_PIT':[-1,1],'TM_OPLEV_TILT_YAW':[-1,1],'TM_OPLEV_TILT_SUM':default_OL_SUM
},
'PR3_OUTMON_lim':{
'SF_COILOUTF_GAS':default_lim,'BF_COILOUTF_GAS':default_lim,
'BF_COILOUTF_V1':default_lim,'BF_COILOUTF_V2':default_lim,'BF_COILOUTF_V3':default_lim,'BF_COILOUTF_H1':default_lim,'BF_COILOUTF_H2':default_lim,'BF_COILOUTF_H3':default_lim,
'IM_COILOUTF_V1':default_lim,'IM_COILOUTF_V2':default_lim,'IM_COILOUTF_V3':default_lim,'IM_COILOUTF_H1':default_lim,'IM_COILOUTF_H2':default_lim,'IM_COILOUTF_H3':default_lim,
'TM_COILOUTF_H1':default_lim,'TM_COILOUTF_H2':default_lim,'TM_COILOUTF_H3':default_lim,'TM_COILOUTF_H4':default_lim
},

'PRM_INMON_lim':{
'SF_LVDTINF_GAS':default_lim,'BF_LVDTINF_GAS':default_lim,
'BF_LVDTINF_V1':default_lim,'BF_LVDTINF_V2':default_lim,'BF_LVDTINF_V3':default_lim,'BF_LVDTINF_H1':default_lim,'BF_LVDTINF_H2':default_lim,'BF_LVDTINF_H3':default_lim,
'IM_OSEMINF_V1':default_lim,'IM_OSEMINF_V2':default_lim,'IM_OSEMINF_V3':default_lim,'IM_OSEMINF_H1':default_lim,'IM_OSEMINF_H2':default_lim,'IM_OSEMINF_H3':default_lim,
'TM_OPLEV_LEN_PIT':[-1,1],'TM_OPLEV_LEN_YAW':[-1,1],'TM_OPLEV_LEN_SUM':default_OL_SUM,'TM_OPLEV_TILT_PIT':[-1,1],'TM_OPLEV_TILT_YAW':[-1,1],'TM_OPLEV_TILT_SUM':default_OL_SUM
},
'PRM_OUTMON_lim':{
'SF_COILOUTF_GAS':default_lim,'BF_COILOUTF_GAS':default_lim,
'BF_COILOUTF_V1':default_lim,'BF_COILOUTF_V2':default_lim,'BF_COILOUTF_V3':default_lim,'BF_COILOUTF_H1':default_lim,'BF_COILOUTF_H2':default_lim,'BF_COILOUTF_H3':default_lim,
'IM_COILOUTF_V1':default_lim,'IM_COILOUTF_V2':default_lim,'IM_COILOUTF_V3':default_lim,'IM_COILOUTF_H1':default_lim,'IM_COILOUTF_H2':default_lim,'IM_COILOUTF_H3':default_lim,
'TM_COILOUTF_H1':default_lim,'TM_COILOUTF_H2':default_lim,'TM_COILOUTF_H3':default_lim,'TM_COILOUTF_H4':default_lim
}
}
