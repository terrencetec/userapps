header = '''
file {
	name="/opt/rtcds/userapps/release/vis/common/medm/OVERVIEW/VIS_MINI.adl"
	version=030107
}
display {
	object {
		x=1996
		y=56
		width=1360
		height=958
	}
	clr=14
	bclr=13
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

common = '/opt/rtcds/userapps/release/vis/common'

def grd_mini(x,y,system='ETMX'):
    width = 150
    height = 25
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=300
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/GRD_MINI.adl;SYSTEM={system}"
    }}
    '''.format(common=common,x=x,y=y,system=system)
    return txt,width,height


def sdf_mini(x,y,fec='123',subsys='ETMXT'):
    width = 250
    height = 15
    subsys = subsys.lower()
    SUBSYS = subsys.upper()
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=200
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/SDF_MINI.adl;FEC={fec},SUBSYS={SUBSYS},subsys={subsys}"
    }}
    '''.format(common=common,x=x,y=y,fec=fec,subsys=subsys,SUBSYS=SUBSYS)
    return txt,width,height

def gds_mini(x,y,fec='123',system='ETMX',subsys='ETMXT',part='TWR'):
    width = 150
    height = 15
    subsys = subsys.lower()
    SUBSYS = subsys.upper()
    system = system.lower()
    SYSTEM = system.upper()
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=260
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/GDS_MINI.adl;FEC={fec},SUBSYS={SUBSYS},subsys={subsys},SYSTEM={SYSTEM},PART={part},PICOOP={picoop},PICOOP={pico},PICOBF={picobf},
    }}
    '''.format(common=common,x=x,y=y,fec=fec,subsys=subsys,SUBSYS=SUBSYS,SYSTEM=SYSTEM,part=part)
    return txt,width,height


def user_mini(x,y,fec='123',system='ETMX',suffix='TOWER_OVERVIEW'):
    width = 445
    height = 25
    sustype = sus_type_is(system).lower()
    SUSTYPE = sustype.upper()
    optic = system.lower()
    OPTIC = system.upper()
    if sustype == 'typea':
        macroname = '{common}/medm/macro/vis{optic}t_overview_macro.txt'.format(common=common,optic=optic)
        ctrladl  = '{common}/medm/VIS_IP_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl2  = '{common}/medm/VIS_IPBF_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl3 = '{common}/medm/VIS_GAS_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl4 = '{common}/medm/VIS_PFMN_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl5 = '{common}/medm/VIS_IM_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl6 = '{common}/medm/VIS_TM_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
    elif sustype=='typeb':
        macroname = '{common}/medm/macro/vis{optic}_overview_macro.txt'.format(common=common,optic=optic)
        ctrladl = '{common}/medm/VIS_IP_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl2  = '{common}/medm/VIS_IPBF_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl3 = '{common}/medm/VIS_GAS_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl4 = '{common}/medm/VIS_PFMN_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl5 = '{common}/medm/VIS_IM_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl6 = '{common}/medm/VIS_TM_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)        
    elif sustype=='typebp':
        macroname = '{common}/medm/macro/vis{optic}_overview_macro.txt'.format(common=common,optic=optic)
        ctrladl = '{common}/medm/{sustype}/VIS_{SUSTYPE}_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl2  = '{common}/medm/VIS_IPBF_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl3 = '{common}/medm/VIS_GAS_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl4 = '{common}/medm/VIS_PFMN_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl5 = '{common}/medm/VIS_IM_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl6 = '{common}/medm/VIS_TM_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)        
    elif sustype=='typec':
        macroname = '{common}/medm/macro/vis{optic}_overview_macro.txt'.format(common=common,optic=optic)
        ctrladl = '{common}/medm/VIS_{SUSTYPE}_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE)
        ctrladl2  = '{common}/medm/VIS_IPBF_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl3 = '{common}/medm/VIS_GAS_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl4 = '{common}/medm/VIS_PFMN_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl5 = '{common}/medm/VIS_IM_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl6 = '{common}/medm/VIS_TM_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)        
    elif sustype=='typetms':
        macroname = '{common}/medm/macro/vis{optic}_overview_macro.txt'.format(common=common,optic=optic)
        ctrladl = '{common}/medm/TMS/VIS_TMS_OVERVIEW.adl'.format(common=common)
        ctrladl2  = '{common}/medm/VIS_IPBF_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl3 = '{common}/medm/VIS_GAS_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl4 = '{common}/medm/VIS_PFMN_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl5 = '{common}/medm/VIS_IM_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)
        ctrladl6 = '{common}/medm/VIS_TM_OVERVIEW.adl'.format(common=common,optic=optic,SUSTYPE=SUSTYPE,sustype=sustype)        
    else:
        raise ValueError('!')

    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=260
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/MINI/USER_MINI.adl;FEC={fec},SYSTEM={system},macroname={macroname},ctrladl={ctrladl},ctrladl2={ctrladl2},ctrladl3={ctrladl3},ctrladl4={ctrladl4},ctrladl5={ctrladl5},ctrladl6={ctrladl6}"
    }}
    '''.format(common=common,x=x,y=y,fec=fec,system=system,sustype=sustype,suffix=suffix,SUSTYPE=SUSTYPE,macroname=macroname,ctrladl=ctrladl,ctrladl2=ctrladl2,ctrladl3=ctrladl3,ctrladl4=ctrladl4,ctrladl5=ctrladl5,ctrladl6=ctrladl6)
    return txt,width,height

def trip_mini(x,y,optic='ETMX'):
    width = 150
    height = 25
    sus_type = sus_type_is(optic)
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=148
    height=30
    }}
    "composite name"=""
    "composite file"="{mini_name};OPTIC={optic}"
    }}
    '''.format(common=common,x=x,y=y,mini_name=trip_mini_name_is(optic),optic=optic)
    return txt,width,height


if __name__=='__main__':
    no_installed_date_model = ['VISETMXMON','VISETMYMON','VISITMXMON','VISITMYMON',
                               'MODALETMX','MODALETMY','MODALITMX','MODALITMY']
    systems = ['ETMX','ETMY','ITMX','ITMY','BS','SRM','SR2','SR3','PRM',
               'PR2','PR3','MCI','MCE','MCO','IMMT1','IMMT2','OMMT1','OMMT2',
               'OSTM','TMSX','TMSY']
    
    models = {'ETMX':[['VISETMXT',102],['VISETMXP',103],['VISETMXMON',104],['MODALETMX',105]],
              'ETMY':[['VISETMYT',107],['VISETMYP',108],['VISETMYMON',109],['MODALETMY',110]],
              'ITMX':[['VISITMXT',92],['VISITMXP',93],['VISITMXMON',94],['MODALITMX',95]],
              'ITMY':[['VISITMYT',97],['VISITMYP',98],['VISITMYMON',99],['MODALITMY',100]],
              'BS':[['VISBST',60],['VISBSP',61]],
              'SRM':[['VISSRMT',75],['VISSRMP',76]],
              'SR2':[['VISSR2T',65],['VISSR2P',66]],
              'SR3':[['VISSR3T',70],['VISSR3P',71]],
              'PRM':[['VISPRM',55]],
              'PR2':[['VISPR2',45]],
              'PR3':[['VISPR3',50]],
              'MCI':[['VISMCI',38]],
              'MCE':[['VISMCE',39]],
              'MCO':[['VISMCO',40]],
              'IMMT1':[['VISIMMT1',42]],
              'IMMT2':[['VISIMMT2',43]],
              'OMMT1':[['VISOMMT1',80]],
              'OMMT2':[['VISOMMT2',81]],
              'OSTM':[['VISOSTM',82]],
              'TMSX':[['VISTMSX',113]],
              'TMSY':[['VISTMSY',122]],              
    }
    sus_types = {'TypeA':['ETMX','ETMY','ITMX','ITMY'],
                'TypeB':['BS','SR2','SR3','SRM'],
                'TypeBp':['PR2','PR3','PRM'],
                'TypeC':['MCI','MCO','MCE','IMMT1','IMMT2','OSTM','OMMT1','OMMT2'],
                'TypeTMS':['TMSX','TMSY']}
    
    def sus_type_is(optic):
        for sus_type in ['TypeA','TypeB','TypeBp','TypeC','TypeTMS']:
            if optic in sus_types[sus_type]:
                return sus_type
            else:
                pass
        return None
    
    def trip_mini_name_is(optic):
        prefix = '/users/Commissioning/medm/'
        sus_type = sus_type_is(optic)
        if sus_type == 'TypeA':
            adl = 'tripped_microA.adl'
        elif sus_type == 'TypeB':
            adl = 'tripped_microB.adl'
        elif sus_type == 'TypeBp':
            adl = 'tripped_microBp.adl'            
        elif sus_type == 'TypeC':
            adl = 'tripped_microC.adl'            
        elif sus_type == 'TypeTMS':
            adl = 'tripped_microT.adl'            
        else:
            raise ValueError('!')        
        return prefix+adl
    
        
    height = 10
    width = 10
    contents = header    
    with open('./MINI/VIS_MINI.adl','w') as f:
        for system in systems:
            model,fec = models[system][0]
            txt,w1,h1 = user_mini(x=width,y=height,system=system)
            contents += txt            
            width += w1+5
            txt,w2,h = grd_mini(x=width,y=height,system='VIS_'+system)
            contents += txt
            width += w2+5
            _w = w1+w2+4
            txt,w3,h = trip_mini(x=width,y=height,optic=system)
            contents += txt
            width += w3+5
            _w = w1+w2+w3+15            
            for model in models[system]:
                model,fec = model
                txt,w,h = sdf_mini(x=width,y=height,fec=fec,subsys=model)
                contents += txt
                if model in no_installed_date_model:
                    _system = 'NONE'
                else:
                    _system = system
                    pass
                if 'T'==model[-1]:
                    part = 'TWR'
                else:
                    part = 'PAY'
                txt,w,h = gds_mini(x=width+w+5,y=height,fec=fec,subsys=model,system=_system,part=part)
                contents += txt                
                height += h+2
            try:
                if len(models[system])==1:
                    height += h
            except:
                pass
            
            width -= _w
            
        f.write(contents)    
