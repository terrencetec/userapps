header = '''
file {
	name="/opt/rtcds/userapps/release/vis/common/medm/OVERVIEW/OPLEV_MINI/OPLEV_MINI.adl"
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

def oplev_mini(x,y,SYSTEM='VIS_ETMX',OPTIC='ETMX',func='OPLEV_TILT',stage='TM',function='OPLEV_TILT'):
    width = 205
    height = 225
    txt = '''
    composite {{
    object {{
    x={x}
    y={y}
    width=300
    height=15
    }}
    "composite name"=""
    "composite file"="{common}/medm/OVERVIEW/OPLEV_MINI/OPLEV_MINI.adl;IFO={ifo},OPTIC={optic},STAGE={stage},FUNC={func},FUNCTION={function},XLABEL={xlabel},YLABEL={ylabel}"
    }}
xo    '''.format(common=common,x=x,y=y,ifo='K1',optic=OPTIC,stage=stage,func=func,function=function,xlabel='YAW_[urad]',ylabel='PIT_[urad]')
    return txt,width,height

if __name__=='__main__':
    no_installed_date_model = ['VISETMXMON','VISETMYMON','VISITMXMON','VISITMYMON',
                               'MODALETMX','MODALETMY','MODALITMX','MODALITMY']
    optics = ['ETMX','ETMY','ITMX','ITMY',
              'BS','SRM','SR2','SR3',
              'PRM','PR2','PR3',
              'MCI','MCE','MCO','IMMT1','IMMT2']
    
    models = {'ETMX':[['VISETMXP',103],['VISETMXT',102]],
              'ETMY':[['VISETMYP',108],['VISETMYT',107]],
              'ITMX':[['VISITMXP',93],['VISITMXT',92]],
              'ITMY':[['VISITMYP',98],['VISITMYT',97]],
              'BS':[['VISBSP',61],['VISBST',60]],
              'SRM':[['VISSRMP',76],['VISSRMT',75]],
              'SR2':[['VISSR2P',66],['VISSR2T',65]],
              'SR3':[['VISSR3P',71],['VISSR3T',70]],
              'PRM':[['VISPRMP',56],['VISPRMT',55]],
              'PR2':[['VISPR2P',46],['VISPR2T',45]],
              'PR3':[['VISPR3P',51],['VISPR3T',50]],
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
                'TypeC-IMC':['MCI','MCO','MCE','IMMT1','IMMT2'],
                'TypeC-OMC':['OSTM','OMMT1','OMMT2'],                 
                'TypeTMS':['TMSX','TMSY']}
    
    def sus_type_is(optic):
        for sus_type in ['TypeA','TypeB','TypeBp','TypeC-IMC','TypeC-OMC','TypeTMS']:
            if optic in sus_types[sus_type]:
                return sus_type
            else:
                pass
        return None        
        
    height = 10
    width = 0
    contents = header
    count = 1
    with open('./OPLEV_MINI/OPLEV_TILT_OVERVIEW_MINI.adl','w') as f:
        for optic in optics:
            OPTIC = optic.upper()
            model,fec = models[optic][0]
            txt,w0,h0 = oplev_mini(x=width,y=height,SYSTEM='VIS_'+OPTIC,OPTIC=OPTIC,func='OPLEV_TILT',function='OPLEV_TILT')
            contents += txt
            width += w0
            if count==5:
                height += h0
                width = 0
                count = 1
            if optic in ['ITMY','SR3','PR3']:
                height += h0
                width = 0
                count = 1            
            else:
                count += 1                
        f.write(contents)

    height = 10
    width = 0
    contents = header
    count = 1
    [optics.remove(optic) for optic in ['MCI','MCE','MCO','IMMT1','IMMT2']]
    with open('./OPLEV_MINI/OPLEV_LEN_OVERVIEW_MINI.adl','w') as f:
        for optic in optics:
            OPTIC = optic.upper()
            model,fec = models[optic][0]
            txt,w0,h0 = oplev_mini(x=width,y=height,SYSTEM='VIS_'+OPTIC,OPTIC=OPTIC,func='OPLEV_LEN',function='OPLEV_LEN')
            contents += txt
            width += w0
            if count==5:
                height += h0
                width = 0
                count = 1
            if optic in ['ITMY','SR3','PR3']:
                height += h0
                width = 0
                count = 1            
            else:
                count += 1
                
        f.write(contents)    


    height = 0
    width = 0
    contents = header
    count = 1
    [optics.remove(optic) for optic in ['BS','SR2','SR3','SRM','PR2','PR3','PRM']]
    with open('./OPLEV_MINI/OPLEV_PF_OVERVIEW_MINI.adl','w') as f:
        for optic in optics:
            OPTIC = optic.upper()
            model,fec = models[optic][0]
            txt,w0,h0 = oplev_mini(x=width,y=height,SYSTEM='VIS_'+OPTIC,OPTIC=OPTIC,func='OPLEV_TILT',function='OPLEV_TILT',stage='PF')
            contents += txt
            height += h0
            if count==5:
                width += w0
                height = 0
                count = 1
            if optic in ['ITMY','SR3','PR3']:
                width += w0
                height = 0
                count = 1            
            else:
                count += 1                
        f.write(contents)
    with open('./OPLEV_MINI/OPLEV_PF_OVERVIEW_MINI.adl','w') as f:
        for optic in optics:
            OPTIC = optic.upper()
            model,fec = models[optic][0]
            txt,w0,h0 = oplev_mini(x=width,y=height,SYSTEM='VIS_'+OPTIC,OPTIC=OPTIC,func='OPLEV_LEN',function='OPLEV_LEN',stage='PF')
            contents += txt
            height += h0
            if count==5:
                width += w0
                height = 0
                count = 1
            if optic in ['ITMY','SR3','PR3']:
                width += w0
                height = 0
                count = 1            
            else:
                count += 1                
        f.write(contents)    
        

        
    height = 0
    width = 0
    contents = header
    count = 1
    with open('./OPLEV_MINI/OPLEV_MN_OVERVIEW_MINI.adl','w') as f:
        for optic in optics:
            OPTIC = optic.upper()
            model,fec = models[optic][0]
            txt,w0,h0 = oplev_mini(x=width,y=height,SYSTEM='VIS_'+OPTIC,OPTIC=OPTIC,func='OPLEV_TILT',function='OPLEV_TILT',stage='MN')
            contents += txt
            height += h0
            if count==5:
                width += w0
                height = 0
                count = 1
            if optic in ['ITMY','SR3','PR3']:
                width += w0
                height = 0
                count = 1            
            else:
                count += 1                
        f.write(contents)
    with open('./OPLEV_MINI/OPLEV_MN_OVERVIEW_MINI.adl','w') as f:
        for optic in optics:
            OPTIC = optic.upper()
            model,fec = models[optic][0]
            txt,w0,h0 = oplev_mini(x=width,y=height,SYSTEM='VIS_'+OPTIC,OPTIC=OPTIC,func='OPLEV_LEN',function='OPLEV_LEN',stage='MN')
            contents += txt
            height += h0
            if count==5:
                width += w0
                height = 0
                count = 1
            if optic in ['ITMY','SR3','PR3']:
                width += w0
                height = 0
                count = 1            
            else:
                count += 1                
        f.write(contents)    
    with open('./OPLEV_MINI/OPLEV_MN_OVERVIEW_MINI.adl','w') as f:
        for optic in optics:
            OPTIC = optic.upper()
            model,fec = models[optic][0]
            txt,w0,h0 = oplev_mini(x=width,y=height,SYSTEM='VIS_'+OPTIC,OPTIC=OPTIC,func='OPLEV_ROL',function='OPLEV_ROL',stage='MN')
            contents += txt
            height += h0
            if count==5:
                width += w0
                height = 0
                count = 1
            if optic in ['ITMY','SR3','PR3']:
                width += w0
                height = 0
                count = 1            
            else:
                count += 1                
        f.write(contents)
    with open('./OPLEV_MINI/OPLEV_MN_OVERVIEW_MINI.adl','w') as f:
        for optic in optics:
            OPTIC = optic.upper()
            model,fec = models[optic][0]
            txt,w0,h0 = oplev_mini(x=width,y=height,SYSTEM='VIS_'+OPTIC,OPTIC=OPTIC,func='OPLEV_TRA',function='OPLEV_TRA',stage='MN')
            contents += txt
            height += h0
            if count==5:
                width += w0
                height = 0
                count = 1
            if optic in ['ITMY','SR3','PR3']:
                width += w0
                height = 0
                count = 1            
            else:
                count += 1                
        f.write(contents)
    with open('./OPLEV_MINI/OPLEV_MN_OVERVIEW_MINI.adl','w') as f:
        for optic in optics:
            OPTIC = optic.upper()
            model,fec = models[optic][0]
            txt,w0,h0 = oplev_mini(x=width,y=height,SYSTEM='VIS_'+OPTIC,OPTIC=OPTIC,func='OPLEV_VER',function='OPLEV_VER',stage='MN')
            contents += txt
            height += h0
            if count==5:
                width += w0
                height = 0
                count = 1
            if optic in ['ITMY','SR3','PR3']:
                width += w0
                height = 0
                count = 1            
            else:
                count += 1                
        f.write(contents)
        
