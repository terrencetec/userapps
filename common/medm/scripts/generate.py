

text = \
"""
file {
	name="/opt/rtcds/userapps/release/vis/common/medm/filters/call.adl"
	version=030107
}
display {
	object {
		x=1923
		y=39
		width=1500
		height=950
	}
	clr=14
	bclr=4
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
"""

minifilter="""
composite {{
	object {{
		x={x}
		y={y}
		width={width}
		height={height}
	}}
	"composite name"=""
	"composite file"="/opt/rtcds/userapps/release/vis/common/medm/filters/MINI_FILTER.adl; FNAME={fname}, IFO={ifo}, OPTIC={OPTIC}, STAGE={stage}, DOF={dof}, FUNC={func}, FUNCTION={func}, optic={optic}, dof={dof}"
}}
"""

minioverview = """
composite {{
	object {{
		x={x}
		y={y}
		width={width}
		height={height}
	}}
	"composite name"=""
	"composite file"="/opt/rtcds/userapps/release/vis/common/medm/scripts/MINI_MODEL.adl; fname={fname}, IFO={ifo}, subsys={subsys}"
}}
"""


def get(adl):
    parse = adl.replace('.adl','').split('_')[1:]
    if len(parse)>4:
        optic,stage,func = parse[:3]
        dof = '_'.join(parse[3:])
    elif len(parse)==3:
        optic,stage,func = parse
        dof = 'XXX'
    elif len(parse)==2:
        optic,stage = parse
        func,dof = 'XXX','XXX'
    elif len(parse)==1:
        optic = parse[0]
        stage,func,dof = 'XXX','XXX','XXX'
    else:
        optic,stage,func,dof = parse
    return optic,stage,func,dof


def master(minilist,header,minitemplate,fname,overview=False):
    i,j=0,0
    height=0
    text=header
    for mini in minilist:
        if overview:
            subsys = [item for item in mini.split('/') if 'adl' in item][0].split('_')[0]
            text += minitemplate.format(x=j*180+38,y=10+i*16,width=230,height=32,subsys=subsys,ifo='K1',
                                fname=mini)
        else:
            optic,stage,func,dof = get(mini)
            text += minitemplate.format(x=j*180+38,y=10+i*16,width=230,height=32,
                                      OPTIC=optic, stage=stage, func=func,
                                      function=func, optic=optic.lower(), dof=dof,
                                      ifo='K1',fname=_prefix+'/'+mini)            
        height += 32*i
        i+=1
        if height>30000:
            height=0
            j += 1
            i = 0
            
    with open(fname,'w') as f:
        f.write(text)
    print(fname)
    
    
    
if __name__=='__main__':
    import os
    userapps = '/opt/rtcds/userapps/release/vis/common/medm/'
    kamioka = '/opt/rtcds/kamioka/k1/medm'
    
    _subsys_list = os.listdir(kamioka)
    _subsys_list.sort()
    _subsys_list = list(filter(lambda x:'vis' in x, _subsys_list))        
    for subsys in _subsys_list:
        _prefix = kamioka+'/{subsys}'.format(subsys=subsys)
        adl_list = os.listdir(_prefix)
        adl_list.sort()
        fname = '../tmp/'+'{0}_overview'.format(subsys).upper()+'.adl'
        master(adl_list,text,minifilter,fname)
        
    subsys_list = list(map(lambda x:userapps+'/tmp/'+x.upper()+'_OVERVIEW.adl', _subsys_list))    
    fname = '../tmp/VIS_OVERVIEW.adl'    
    master(subsys_list,text,minioverview,fname,overview=True)
