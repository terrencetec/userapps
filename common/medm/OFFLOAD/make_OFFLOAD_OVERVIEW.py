#!/usr/bin/env python3

header = '''
file {
	name="/opt/rtcds/userapps/release/cds/common/medm/steppingmotor/OFFLOAD_OVERVIEW/OFFLOAD_OVERVIEW.adl"
	version=030107
}
display {
	object {
		x=1996
		y=56
		width=1500
		height=900
	}
	clr=14
	bclr=11
	cmap=""
	gridSpacing=5
	gridOn=0
	snapToGrid=0
}
"color map" {
	ncolors=65
	colors {
		ffffff,
		ececec,
		dadada,
		c8c8c8,
		bbbbbb,
		aeaeae,
		9e9e9e,
		919191,
		858585,
		787878,
		696969,
		5a5a5a,
		464646,
		2d2d2d,
		000000,
		00d800,
		1ebb00,
		339900,
		2d7f00,
		216c00,
		fd0000,
		de1309,
		be190b,
		a01207,
		820400,
		5893ff,
		597ee1,
		4b6ec7,
		3a5eab,
		27548d,
		fbf34a,
		f9da3c,
		eeb62b,
		e19015,
		cd6100,
		ffb0ff,
		d67fe2,
		ae4ebc,
		8b1a96,
		610a75,
		a4aaff,
		8793e2,
		6a73c1,
		4d52a4,
		343386,
		c7bb6d,
		b79d5c,
		a47e3c,
		7d5627,
		58340f,
		99ffff,
		73dfff,
		4ea5f9,
		2a63e4,
		0a00b8,
		ebf1b5,
		d4db9d,
		bbc187,
		a6a462,
		8b8239,
		73ff6b,
		52da3b,
		3cb420,
		289315,
		1a7309,
	}
}
'''

channel_dict = {
    'ETMX_F0_GAS': 0,
    'ETMX_F1_GAS': 1,
    'ETMX_F2_GAS': 5,
    'ETMX_F3_GAS': 3,
    'ETMX_BF_GAS': 4,
    
    'ITMX_F0_GAS': 0,
    'ITMX_F1_GAS': 1,
    'ITMX_F2_GAS': 2,
    'ITMX_F3_GAS': 3,
    'ITMX_BF_GAS': 4,

    'ETMY_F0_GAS': 0,
    'ETMY_F1_GAS': 1,
    'ETMY_F2_GAS': 2,
    'ETMY_F3_GAS': 5,
    'ETMY_BF_GAS': 4,

    'ITMY_F0_GAS': 0,
    'ITMY_F1_GAS': 1,
    'ITMY_F2_GAS': 2,
    'ITMY_F3_GAS': 3,
    'ITMY_BF_GAS': 4,

    'BS_F0_GAS': 3,
    'BS_F1_GAS': 1,
    'BS_BF_GAS': 0,

    'SR2_F0_GAS': 2,
    'SR2_F1_GAS': 1,
    'SR2_BF_GAS': 0,

    'SR3_F0_GAS': 3,    # 2->3 Klog#15541
    'SR3_F1_GAS': 1,
    'SR3_BF_GAS': 0,

    'SRM_F0_GAS': 2,    # 3->2 Klog#215681
    'SRM_F1_GAS': 1,
    'SRM_BF_GAS': 0,

    'PR2_BF_GAS': 0, 
    'PR2_SF_GAS': 2,
    
    'PR3_BF_GAS': 0,    # STEPPER PR0
    'PR3_SF_GAS': 1,    # STEPPER PR0
    
    'PRM_BF_GAS': 2,    # STEPPER PR0
    'PRM_SF_GAS': 3     # STEPPER PR0
}


#common = '/opt/rtcds/userapps/release/vis/common'
common = './'

def top(x,y):
    width = 300
    height = 100
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=300
    height=30
    }}
    "composite name"=""
    "composite file"="./OFFLOAD_TOP.adl"
    }}
    '''.format(common=common,x=x,y=y)
    return txt,width,height


def mini(x,y,system,stage,sensor_stage,dof,sensor_dof,damp,bio,stepname,stepid,motor,label,mode='ERR'):
    width = 350
    height = 25
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=300
    height=30
    }}
    "composite name"=""
    "composite file"="./OFFLOAD_MINI.adl;IFO=$(IFO),ifo=$(ifo),SYSTEM={system},STAGE={stage},SENSOR_STAGE={sensor_stage},DOF={dof},SENSOR_DOF={sensor_dof},DAMP={damp},BIO={bio},STEPNAME={stepname},STEPID={stepid},MOTOR={motor},LABEL={label}"
    }}
    '''.format(common=common,x=x,y=y,system=system,stage=stage,sensor_stage=sensor_stage,dof=dof,sensor_dof=sensor_dof,damp=damp,bio=bio,stepname=stepname,stepid=stepid,motor=motor,label=label)
    return txt,width,height

def head(x,y,system,mtype):
    width = 300
    height = 50
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=300
    height=30
    }}
    "composite name"=""
    "composite file"="./HEAD_MINI.adl;IFO=$(IFO),ifo=$(ifo),SYSTEM={system},TYPE={mtype}"
    }}
    '''.format(common=common,x=x,y=y,system=system,mtype=mtype)
    return txt,width,height

def foot(x,y,stepperid,systems,vacsystem,ip_lvdtinf_yaml,ip_damp_yaml,gas_damp_yaml,ip_stepper_yaml,gas_stepper_yaml,ip_stepper_limit_yaml,gas_stepper_limit_yaml):
    width = 300
    height = 50
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=300
    height=30
    }}
    "composite name"=""
    "composite file"="./FOOT_MINI.adl;IFO=$(IFO),ifo=$(ifo),STEPPERID={stepperid},OPTICS={system},VACOPTICS={vacsystem},ip_lvdtinf_yaml={ip_lvdtinf_yaml},ip_damp_yaml={ip_damp_yaml},gas_damp_yaml={gas_damp_yaml},ip_stepper_yaml={ip_stepper_yaml},gas_stepper_yaml={gas_stepper_yaml},ip_stepper_limit_yaml={ip_stepper_limit_yaml},gas_stepper_limit_yaml={gas_stepper_limit_yaml}"
    }}
    '''.format(common=common,x=x,y=y,stepperid=stepperid,system=system,vacsystem=vacsystem,ip_lvdtinf_yaml=ip_lvdtinf_yaml,ip_damp_yaml=ip_damp_yaml,gas_damp_yaml=gas_damp_yaml,ip_stepper_yaml=ip_stepper_yaml,gas_stepper_yaml=gas_stepper_yaml,ip_stepper_limit_yaml=ip_stepper_limit_yaml,gas_stepper_limit_yaml=gas_stepper_limit_yaml)
    return txt,width,height


def mtype_is(system):
    if 'TM' in system:
        mtype = 'TM'
    elif 'BS' == system:
        mtype = 'BS'
    elif 'SR' in system:
        mtype = 'SR'
    else:            
        mtype = None
    return mtype

def sensor_stage_is(system,mtype,stage,dof):
    if stage == 'IP' and dof == 'F0Y':
        if mtype == 'TM': 
            if system == 'ITMY': # old model
                stage = 'BF'
            else:
                stage = 'TM'
        else:
            stage = 'TM'
        dof = "Y"
    return stage, dof

def damp_is(system,dof,mode='ERR'):
    if system in ['BS']:
        if dof == 'F0Y':
            damp = 'DAMP'                        
        else:
            damp = 'DCCTRL'
    else:
        if dof == 'F0Y' and system != 'ITMY': # old model
            damp = 'OLDAMP'                        
        else:
            damp = 'DAMP'                        
    return damp
    
def bio_is(system):
    if system in ['BS','SR2','SR3','SRM']:
        bio = 'BIO'
    else:
        bio = 'BO'
    return bio
    
def stepname_is(dof):
    if dof == 'GAS':
        return 'STEP_GAS'
    else:
        return 'STEP_IP'

def stepperid_is(system):
    if system == 'PRM' or system == 'PR3':
        return 'PR0'
    else:
        return system

def stepid_is(system,stage):
    if stage == 'IP':
        return system+'_IP'
    else:
        return stepperid_is(system)+'_GAS'

def motor_is(system,stage,dof):
    if stage == 'IP':
        return dof
    else:
        return channel_dict[system+'_'+stage+'_'+dof]

def label_is(stage,dof):
    if stage == 'IP':
        if dof == 'F0Y':
            return 'F0_Y'

    return stage + '_' + dof

if __name__=='__main__':
    systems = ['ETMX', 'ITMX', 'ETMY', 'ITMY', 'BS', 'SRM', 'SR2', 'SR3', 'PRM', 'PR2', 'PR3']
    #systems = ['TEST', 'TESTSR'] # TEST
    #systems = ['ETMX', 'ITMX', 'ETMY', 'ITMY']

    # ERROR mode
    # TypeA
    #   K1:VIS-ITMY_IP_DAMP_L_INMON
    #   K1:VIS-ITMY_F0_DAMP_GAS_INMON
    # TypeB    
    #   K1:VIS-BS_IP_DCCTRL_L_INMON
    #   K1:VIS-BS_F0_DCCTRL_GAS_INMON
    # TypeBp
    #   K1:VIS-PR2_BF_DAMP_GAS_INMON
    #
    # FB mode 
    # TypeA
    #   K1:VIS-ETMY_IP_SUMOUT_L_OUTMON
    #   K1:VIS-ETMY_F0_SUMOUT_GAS_OUTMON
    # TypeB
    #   K1:VIS-BS_IP_DCCTRL_L_OUTMON
    #   K1:VIS-BS_F0_COILOUTF_GAS_OUTMON
    # TypeBp
    #   K1:VIS-PR2_SF_DAMP_GAS_OUTMON

    stages = {'ETMX':['IP','F0','F1','F2','F3','BF'],
              'ITMX':['IP','F0','F1','F2','F3','BF'],
              'ETMY':['IP','F0','F1','F2','F3','BF'],
              'ITMY':['IP','F0','F1','F2','F3','BF'],
              'BS':['IP','F0','F1','BF'],
              'SR2':['IP','F0','F1','BF'],
              'SR3':['IP','F0','F1','BF'],
              'SRM':['IP','F0','F1','BF'],
              'PR2':['SF','BF'],
              'PR3':['SF','BF'],
              'PRM':['SF','BF']}
    dofs = {'IP':['L','T','Y','F0Y'],
            'F0':['GAS'],
            'F1':['GAS'],
            'F2':['GAS'],
            'F3':['GAS'],
            'BF':['GAS'],
            'SF':['GAS']}
    vacsystem = {'ETMX':'X_EXA',
                 'ITMX':'X_IXA',
                 'ETMY':'Y_EYA',
                 'ITMY':'Y_IYA',
                 'BS':'None',
                 'SR2':'None',
                 'SR3':'None',
                 'SRM':'None',
                 'PR2':'None',
                 'PR3':'None',
                 'PRM':'CS_IMC'}

    yamlfile_path ='/opt/rtcds/userapps/release/vis/common/medm/OFFLOAD/'
    yamlfile_ip_lvdtinf_with_vac = yamlfile_path + 'ip_lvdtinf_with_vac.yml'
    yamlfile_ip_damp_with_vac    = yamlfile_path + 'ip_damp_with_vac.yml'
    yamlfile_gas_damp_typea      = yamlfile_path + 'gas_damp_typea.yml'
    yamlfile_ip_lvdtinf          = yamlfile_path + 'ip_lvdtinf.yml'
    yamlfile_ip_damp             = yamlfile_path + 'ip_damp.yml'
    yamlfile_gas_damp_typeb      = yamlfile_path + 'gas_damp_typeb.yml'
    yamlfile_gas_damp_typebp     = yamlfile_path + 'gas_damp_typebp.yml'
    yamlfile_ip_stepper          = yamlfile_path + 'ip_stepper.yml'
    yamlfile_gas_stepper         = yamlfile_path + 'gas_stepper.yml'
    yamlfile_ip_limit_stepper    = yamlfile_path + 'ip_stepper_limit.yml'
    yamlfile_gas_limit_stepper   = yamlfile_path + 'gas_stepper_limit.yml'
    yamlfile = {'ETMX':[yamlfile_ip_lvdtinf_with_vac, yamlfile_ip_damp_with_vac, yamlfile_gas_damp_typea,   yamlfile_ip_stepper,    yamlfile_gas_stepper,   yamlfile_ip_limit_stepper,    yamlfile_gas_limit_stepper],
                'ITMX':[yamlfile_ip_lvdtinf_with_vac, yamlfile_ip_damp_with_vac, yamlfile_gas_damp_typea,   yamlfile_ip_stepper,    yamlfile_gas_stepper,   yamlfile_ip_limit_stepper,    yamlfile_gas_limit_stepper],
                'ETMY':[yamlfile_ip_lvdtinf_with_vac, yamlfile_ip_damp_with_vac, yamlfile_gas_damp_typea,   yamlfile_ip_stepper,    yamlfile_gas_stepper,   yamlfile_ip_limit_stepper,    yamlfile_gas_limit_stepper],
                'ITMY':[yamlfile_ip_lvdtinf_with_vac, yamlfile_ip_damp_with_vac, yamlfile_gas_damp_typea,   yamlfile_ip_stepper,    yamlfile_gas_stepper,   yamlfile_ip_limit_stepper,    yamlfile_gas_limit_stepper],
                'BS':  [yamlfile_ip_lvdtinf,          yamlfile_ip_damp,          yamlfile_gas_damp_typeb,   yamlfile_ip_stepper,    yamlfile_gas_stepper,   yamlfile_ip_limit_stepper,    yamlfile_gas_limit_stepper],
                'SR2': [yamlfile_ip_lvdtinf,          yamlfile_ip_damp,          yamlfile_gas_damp_typeb,   yamlfile_ip_stepper,    yamlfile_gas_stepper,   yamlfile_ip_limit_stepper,    yamlfile_gas_limit_stepper],
                'SR3': [yamlfile_ip_lvdtinf,          yamlfile_ip_damp,          yamlfile_gas_damp_typeb,   yamlfile_ip_stepper,    yamlfile_gas_stepper,   yamlfile_ip_limit_stepper,    yamlfile_gas_limit_stepper],
                'SRM': [yamlfile_ip_lvdtinf,          yamlfile_ip_damp,          yamlfile_gas_damp_typeb,   yamlfile_ip_stepper,    yamlfile_gas_stepper,   yamlfile_ip_limit_stepper,    yamlfile_gas_limit_stepper],
                'PR2': ['None',                       'None',                    yamlfile_gas_damp_typebp,  'None',                 yamlfile_gas_stepper,   'None',                       yamlfile_gas_limit_stepper],
                'PR3': ['None',                       'None',                    yamlfile_gas_damp_typebp,  'None',                 yamlfile_gas_stepper,   'None',                       yamlfile_gas_limit_stepper],
                'PRM': ['None',                       'None',                    yamlfile_gas_damp_typebp,  'None',                 yamlfile_gas_stepper,   'None',                       yamlfile_gas_limit_stepper]
                }
    mode = 'ERR'
    
    height = 10
    width = 10
    _h0 = height
    _w0 = width
    contents = header
    _h = 0
    _w = 0
    with open('./OFFLOAD_OVERVIEW.adl','w') as f:
        txt,w0,h0 = top(width,height)
        contents += txt
        height += h0
        _h0 = height
        for num,system in enumerate(systems):
            #print('{0}'.format(system))
            mtype = mtype_is(system)
            stepperid = stepperid_is(system)                
            txt,w0,h0 = head(width,height,system,mtype)
            contents += txt         
            _h = h0
            for stage in stages[system]:
                print(' - ',stage,dofs[stage])
                for dof in dofs[stage]:
                    damp = damp_is(system,dof)
                    bio = bio_is(system)
                    stepname = stepname_is(dof)
                    stepid = stepid_is(system,stage)
                    motor = motor_is(system,stage,dof)
                    sensor_stage, sensor_dof = sensor_stage_is(system,mtype,stage,dof)
                    label = label_is(stage, dof)
                    txt,w1,h1 = mini(width,height+_h,system,stage,sensor_stage,dof,sensor_dof,damp,bio,stepname,stepid,motor,label,mode=mode)
                    _h += h1
                    contents += txt

            print(stepperid,system,vacsystem[system])
            txt,w2,h2 = foot(width,height+_h,stepperid,system,vacsystem[system],yamlfile[system][0],yamlfile[system][1],yamlfile[system][2],yamlfile[system][3],yamlfile[system][4],yamlfile[system][5],yamlfile[system][6])
            contents += txt
            _h += h2 + 10
            _w = max(w0,w1,w2) +10
            q,mod = divmod(num+1,4)
            height = q*320 + _h0
            width = mod*_w + _w0
                
        f.write(contents)    
