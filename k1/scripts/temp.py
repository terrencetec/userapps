		notify('Engaging IP control 1: everything to OFF/0')
		vis.dcctrlInputSwitchWrite('OFF',levels=['IP'])
		vis.dampInputSwitchWrite('OFF',levels=['IP'])
		vis.dcctrlOutputSwitchWrite('OFF',levels=['IP'])
		vis.dampOutputSwitchWrite('OFF',levels=['IP'])
		vis.dcctrlOffsetSwitchWrite('OFF',levels=['IP'])
		vis.dampOffsetSwitchWrite('OFF',levels=['IP'])
		notify('Engaging IP control 2: copying current position to SET')
		for DOF in ['L','T','Y']:
			val=ezca.read('VIS-'+OPTIC+'_'+STAGE+'_BLEND_LVDT'+DOF+'_OUTPUT')
			vis.setRampWrite(0,levels=['IP'],chans=[DOF])
			vis.setGainWrite(1,levels=['IP'],chans=[DOF])
			vis.setOffsetWrite(val,levels=['IP'],chans=[DOF])
		notify('Engaging IP control 3: ramping up DCCTRL and DAMP gains')
		vis.dcctrlPressButton('CLEAR',levels=['IP'])
		vis.dampPressButton('CLEAR',levels=['IP'])
		vis.dcctrlRampWrite(typeBtime.DCCTRLRamp,levels=['IP'])
		vis.dampRampWrite(typeBtime.DAMPRamp,levels=['IP'])
		vis.dcctrlOffsetSwitchWrite('ON',levels=['IP'])
		vis.dampOffsetSwitchWrite('ON',levels=['IP'])
		self.timer['ramping']=typeBtime.rampNotifyInterval
		while any(vis.dcctrlRampingRead) or any(vis.dampRampingRead):
			if vis.trippedWds()!=[] or is_tripped_BIO(BIO):
				return 'TRIPPED'
			if self.timer['ramping']:
				self.timer['ramping']=typeBtime.rampNotifyInterval
		notify('Engaging IP control 4: moving to snapshot SET point')
		val=valFromSnap(STAGE,BLOCK,DOF,ipSnap,'OFFSET')
		vis.setRampWrite(typeBtime.IPSETRamp,levels=['IP'])
		vis.setOffsetWrite(val,levels=['IP'])
		self.timer['ramping']=typeBtime.rampNotifyInterval
		while any(vis.setRampingRead):
			if vis.trippedWds()!=[] or is_tripped_BIO(BIO):
				return 'TRIPPED'
			if self.timer['ramping']:
				self.timer['ramping']=typeBtime.rampNotifyInterval

