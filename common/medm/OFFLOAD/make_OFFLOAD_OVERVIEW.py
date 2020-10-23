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
		width=1300
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


def mini(x,y,system,stage,dof,damp,bio,stepname):
    width = 300
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
    "composite file"="./OFFLOAD_MINI.adl;IFO=$(IFO),ifo=$(ifo),SYSTEM={system},STAGE={stage},DOF={dof},DAMP={damp},BIO={bio},STEPNAME={stepname}"
    }}
    '''.format(common=common,x=x,y=y,system=system,stage=stage,dof=dof,damp=damp,bio=bio,stepname=stepname)
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

def foot(x,y,system):
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
    "composite file"="./FOOT_MINI.adl;IFO=$(IFO),ifo=$(ifo),SYSTEM={system},DAMP={damp}"
    }}
    '''.format(common=common,x=x,y=y,system=system,damp=damp)
    return txt,width,height



if __name__=='__main__':
    systems = ['ETMX', 'ITMX', 'ETMY', 'ITMY', 'BS', 'SRM', 'SR2', 'SR3', 'PRM', 'PR2', 'PR3']
    #systems = ['TEST', 'TESTSR'] # TEST
    #systems = ['ETMX', 'ITMX', 'ETMY', 'ITMY']


    # K1:VIS-ITMY_IP_DAMP_L_INMON
    # K1:VIS-ITMY_F0_DAMP_GAS_INMON
    # K1:VIS-BS_IP_DCCTRL_L_INMON
    # K1:VIS-BS_F0_DCCTRL_GAS_INMON
    # K1:VIS-PR2_BF_DAMP_GAS_INMON


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
    dofs = {'IP':['L','T','Y'],
            'F0':['GAS'],
            'F1':['GAS'],
            'F2':['GAS'],
            'F3':['GAS'],
            'BF':['GAS'],
            'SF':['GAS'],}


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

    def damp_is(system):
        if system in ['BS','SR2','SR3','SRM']:
            damp = 'DCCTRL'
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
            print('{0}'.format(system))
            mtype = mtype_is(system)                
            txt,w0,h0 = head(width,height,system,mtype)
            contents += txt         
            _h = h0
            for stage in stages[system]:
                print(' - ',stage,dofs[stage])
                for dof in dofs[stage]:
                    damp = damp_is(system)
                    print(damp)
                    bio = bio_is(system)
                    stepname = stepname_is(dof)
                    txt,w1,h1 = mini(width,height+_h,system,stage,dof,damp,bio,stepname)
                    _h += h1
                    contents += txt
            txt,w2,h2 = foot(width,height+_h,system)
            contents += txt
            _h += h2
            _w = max(w0,w1,w2) +10
            
            q,mod = divmod(num+1,4)
            height = q*300 + _h0
            width = mod*_w + _w0
                
        f.write(contents)    
