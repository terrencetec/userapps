#!/usr/bin/env python 
# -*- mode: python -*-

# Note: the shebang line above needs to invoke vanilla python (rather than Guardian, which is a python interpreter with stuff pre-loaded)
# so that when this module is used from the command line it can parse its own options and arguments.

# Please use 4-space indenting, not tabs. In the Tab Width menu in the lower window frame in gedit, 
#  select Automatic Indentation off, Tab Width 4, Use Spaces on.
# Please use Python 2.7.x idioms to remain compatible with Guardian (currently at 2.7.9).

"""vistools.py - module for managing suspensions via EPICS/ezca; also callable from the command line.

vistools.visData is a large nested dictionary structure with information about different suspension types ('TYPEA', 'TYPEB' etc)
vistools.visTypes is dictionary mapping suspensions ('BS' etc) to suspension types.
vistools.Vis is a class with a large number of methods for accessing the information in visData and manipulating the suspension via ezca.

Within Python or iPython, create a Vis object from a string (or Guardian SYSTEM string or ezca object):
BS=vistools.Vis('BS') # creates an object that works on the beamsplitter

Within Guardian, from within a GuardState (e.g., SAFE) do
visobj = vistools.Vis((SYSTEM,ezca)) # create a Vis object without needing to hardcode the suspension name and recycling the ezca object

Then call its various methods, which are mostly organized and named by groups of filters:

vis.masterSwitchWrite('ON') # turns the master switch on
vis.dampGainWrite(1.0) # sets all gain values in all DAMP blocks to 1.0. 
vis.dampGainWrite(1.0,levels=['IP']) # sets all gain values in the IP DAMP block to 1.0.  
vis.dampGainWrite(1.0,levels=['IP'],chans=['L','T']) # sets the gain values for the L and T channels of the IP DAMP block to 1.0 

From the command line, make sure that vistools.py has the executable (x) bit set (chmod +x vistools.py) then do
./vistools.py --help
./vistools.py -o BS dampGainWrite -l IP -c L T -v 1 # sets the gain values for the L and T channels of the IP DAMP block to 1.0

Many methods are now generated programmatically. If the one you want doesn't exist, you may be able to add it by tweaking
the lists lfMethodsToGenerate and lmMethodsToGenerate.
"""


## SVN $Id: vistools.py 12265 2015-12-11 01:40:50Z arnaud.pele@LIGO.ORG $

# Version history

# 8/9/13: Version 0 by Mark Barton.
# 8/10/13: Version 1.0
# 8/16/13: Version 1.1 - add magnet sign info; fix types for TMSX/Y (was HLTS!); 
#    added new helper methods genOutputSwitch etc enabling one-liner definitions for dampOutputSwitch etc;
#    fixed HLTS and separate out SR2 and SRM (to HSTS2) because they have SD OSEM on opposite side from E1100109-v2;
#    key susTypes on full prefix in case H1<>L1; fix manual mode methods to pass return value;
#    added provisions for test stands; fixed masterSwitch (had been using filter-style method);
#    defined SusError and replaced sys.exit() calls; reworked Sus.__init__() to add (SWITCH,ezca) option
# 8/27/13: Version 1.2: Changed 'chan' to 'pv' in many names; added lever arm info; 
#    added support for PV list output in Matlab cell array format and/or with a suffix and/or with full prefix;
#    added PV list functions for matrices
# 8/28/13: Version 1.3: reworked command line processing in terms of argparse rather than optparse
#    added support for more types to toMatlabString; renamed most commands to camelCase; added xxxxFilterSwitchRead commands;
#    added 'levelorder' field to each item in susTypes; made PV list methods use user-specified level order, or 'levelorder' when levels==[]
# 8/30/13: Version 1.4: added optional fakeguardian for off-line testing; fixed HTTS prefixes to have 'ASC-' not 'SUS-';
#    refactored many switch/numeric read/write methods in terms of more generic genNumWrite, genRead, genSwitch and genSwitchRead;
#    made -l etc have nargs='+' instead of '*'
# 9/4/13: Version 1.5: added support for writing lists of values to PVs; added methods for generating matrix PV lists; 
#    updated susData with default matrices for o2e, e2l, sensalign; moved ISI offload stuff into M0/M1 where it belonged;
#    extended filter block definition to have default gains; moved magnet signs into COILOUTF default gains
# 9/5/13: Version 1.6 add -x switch; rename toMatlabString to toMatlab.
# 10/4/13: Version 1.7 add -X switch; fix logic of -x, -X and command; change format of OSEM data in susData; 
#    add -k switch and data access methods.
# 10/4/13 Version 1.8 added "suspensionType" method (A.Pele)
# 11/8/13 Version 1.9 : modified HSTS/HSTSM/HSTS2/HSTS2M/HLTS dictionary : [levels][M3][test] = test3 instead of None. Modification has been tested for all of HSTS/HLTS (A.Pele)
# 11/12/13 Version 2.0 : support for WIT channels as added to Simulink by Jeff K (): added 'wit' entries and removed some 'damp' entries in susData, added new witPvs() function; updated import calls to look in susScriptDir for ezca or guardianScriptDir for guardian.ezca depending on init_thingy argument.
# 11/20/13: Version 2.1: fixed top level LOCK stuff by adding new 'lockdofs' entry with just L/P/Y (had been trying to access non-existent T/V/R). 
#    Renamed all EPICS read/write functions to have Read or Write in the name. 
#    Added new pair argument to most functions and new -pair switch to specify whether read/write functions should return PV, value, (PV,value) or nothing. 
#    Renamed RAMP=4096 bitmask to GRAMP (G=gain) and added ORAMP=8192 (O=offset). Extended genSwitchRead to accept a list of bit names (e.g., ['GRAMP','ORAMP']). 
#    Added new functions *OffsetRampingRead and *GainRampingRead (*=damp/test/lock/align). Added additional *GainRead functions for *=test/lock/align.
#    Fixed -x and -X to take multiple words of input. Allowed the keywords from -k to be applied to things in callableGlobals. Removed EUL2CART stuff.
#    Made Write functions return PV/values.
# 12/20/13: Version 2.2: Changed LHO HTTS data (but not yet LLO's) to reflect move from ASC to SUS.
# 1/9/14: Version 2.3: Added support for watchdogs: new fields in susType, new methods wdNames and trippedWDs
# 1/10/14: Version 2.4: Cleaned up and extended WD support: removed creating separate ezca object just for IOP WD chans 
#     (old one does the right thing if given a channel in form ':IOP-SUS_B123_DACKILL'); added WD info for all H1/L1;
#     improved trigger logic now ignores bypassed IOP DACKILL; 
# 1/15/14: Version 2.5 Added masterSwitchRead. Fixed bug: genRead and genGainRead should have been genNumRead.
# 1/16/14: Version 2.6 (Jamie) Fixed bug causing __TRAMP etc. Fixed prefix not set bug in initialization.
# 1/23/14: Version 2.7 Added 1 and True as synonyms for enable='ON' in genSwitchWrite and likewise for 0/False/'OFF';
#      tweaked Jamie's fix for __TRAMP (genNumWrite back to not supplying '_', calls should).
# 02/24/14 Version 2.8 Added a method for ISC block in order to turn off the output switch of length and angular control as well as (experimental) olOutputSwitchWrite for OL damping filters;
#      added alignOffsetRead(), alignOffsetSwitchRead(), fixed entry for OFFSET in cdsFiltMask (had said OUTPUT) 
# 03/14/14: Version 2.9 Changed L1 HTTS's from ASC to SUS.
# 03/17/14: Version 3. Added isc definition for TMTSs OMC and HAUX and HTTS with isc=None
# 04/21/14: Version 3.1 Deleted QUAD L3 WD from watchdog list.
# 04/29/14: Version 3.2 Revised OL stuff: changed olConfig items to distinguish 'inf' (with dofs P, Y and SUM) and 'full' (with dofs PIT, YAW and SUM). 
#      Added olSegPvs referencing SEG1/SEG2/etc. Added olRead and olSegRead. Added lots of susData entries for OLDAMP blocks, with method olDampPvs to access. 
#      Renamed Arnaud's olOutputSwitchWrite to olDampOutputSwitchWrite and got working.
# 06/27/14: Version 3.3 Stuart A, Added olDampRead for enabling capability of turning ON/OFF BS OpLev Damping.
# 07/02/14: Version 3.4 Stuart A & Joe B, Added capability to clear filter history.    
# 03/22/16: Version K1: rework for Kagra, rename lots of "SUS"/"Sus" stuff to "VIS"/"Vis", add visdata for PR3. Add dorw arguments and -z and -Z switches to selectively disable reading and writing to live system.
# 05/06/19: Lots of stuff: removed all ISI and ESD related stuff; added BIO stuff; updated WD stuff to include BIO WDs; 
# automated generation of methods for most filter and matrix blocks; added support for many more elements in filter blocks;
# added first approximation to Type B section of visData; 
# added lots of checks for non-existent keys in visData to the low-level methods so that they fail silently 
# and visData doesn't have to have lots of 'key':None entries; rewrote and tested levelmatrixblockpvs, levelmatrixblockdefs, 
# levelsensactmatrixblockpvs and levelsensactmatrixblockdefs.

# To do:
# FIXME: Figure out how to include DRIVEALIGN.
# FIXME: Figure out how to include BIO switches.

# Import other useful modules
import os
import sys
import time
import platform

if platform.system() == 'Linux': # KAGRA system
    if "/opt/rtcds/userapps/release/vis/k1/scripts" not in sys.path:
        sys.path.append('/opt/rtcds/userapps/release/vis/k1/scripts')        

try:
    from ezca import Ezca
except ImportError:
    if platform.system() == 'Darwin': # Mark B's Mac
        os.environ['IFO']='K1'
        if '/Users/mbarton/Dropbox/KAGRA-Dropbox/TypeB/guardian/scripts' not in sys.path:
            sys.path.append('/Users/mbarton/Dropbox/KAGRA-Dropbox/TypeB/guardian/scripts')
        from fakeezca import Ezca

sleepTime = 0.0 # Time to allow after each EPICS write
dummyval = -123456789

# -------------------------------------------------------------------------------------------------
# Error class for VIS
class VisError(Exception):
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)

# -------------------------------------------------------------------------------------------------
# Class representing a single suspension.
class Vis(object):
    """
    A class representing suspensions to be manipulated via EPICs and the guardian.ezca module. For non-Guardian use, create an instance using any of the following patterns:
        bs = vistools.Vis('BS') # bare name
        bs = vistools.Vis('VIS-BS') # PV style
        bs = vistools.Vis('VIS_BS') # Guardian name style
        
    For Guardian use, you can pass just the value of the global variable SYSTEM (e.g., 'VIS_BS') or a tuple (SYSTEM, ezca) to reuse the Guardian Ezca instance:
        vis = vistools.Vis(SYSTEM)
        vis = vistools,Vis((SYSTEM,ezca))
    
    Key attributes:
        .ezca: an Ezca instance with prefix 'K1:' (or whatever the environment variable IFO is plus ':').
        .name: 'BS' or the like
        .fullprefix: 'K1:VIS-BS_' or the like - what conceptually needs to be added to short PVs.
        .infix: 'VIS-BS_' or the like - what vistools adds to short PVs internally (ezca is responsible for the 'K1:').
        .system: 'VIS_BS' - same as Guardian name
    """
    # -------------------------------------------------------------
    # Initialization
    def __init__(self, init_thingy, ifo=os.environ['IFO']):
        self.IFO=ifo.upper()
        if type(init_thingy) == tuple and len(init_thingy) == 2 and type(init_thingy[0]) == str and isinstance(init_thingy[1], Ezca):
            string_thingy, self.ezca = init_thingy # hold the string part for more processing; save the ezca part
            if self.ezca.prefix != self.IFO+':':
                raise VisError('Passed in Ezca object has unexpected prefix '+self.ezca.prefix+' - should be'+self.IFO+':.')
        elif type(init_thingy) == str: # e.g., 'ITMY'
            string_thingy = init_thingy # hold the string part for more processing
            self.ezca = Ezca(self.IFO+':') # create our own Ezca instance with 'K1:'-style prefix for ourselves
        else:
            raise VisError('Unrecognized initializer type for class Vis.')
        
        string_thingy = string_thingy.rstrip('-_')
        if '-' in string_thingy:
            subsystem,optic = string_thingy.split('-') # 'VIS-BS' -> 'VIS','BS'
            if subsystem != 'VIS':
                raise VisError('Subsystem '+subsystem+' is not VIS.')
        elif '_' in string_thingy:
            subsystem,optic = string_thingy.split('_') # 'VIS_BS' -> 'VIS','BS'
            if subsystem != 'VIS':
                raise VisError('Subsystem '+subsystem+' is not VIS.')
        else:
            optic = string_thingy
        self.name = optic
        self.fullprefix = self.IFO+':VIS-'+self.name+'_'
        self.infix = 'VIS-'+self.name+'_'
        try:
            data = visTypes[(self.IFO,self.name)]
        except:
            raise VisError('Unrecognized IFO:VIS type: '+self.IFO+':'+self.name)
        if type(data['type']) == str:
            try:
                self.data = visData[data['type']]
            except:
                raise VisError('Oops, value '+repr(data['type'])+' in visTypes not found as key in visData')
            self.system = 'VIS-'+self.name # e.g., 'VIS-ITMX' # FIXME allow for ASC
            self.prefix = self.IFO+':'+self.system+'_' # e.g., 'K1:VIS-ITMX_'
        elif type(data['type']) == tuple: # a tuple of (prefix, actual VIS type)
            prefix, realVisType = data['type']
            try:
                self.data = visData[realVisType]
            except:
                raise VisError('Oops, value '+repr(realVisType)+' in visTypes not found as key in visData')
            self.fullprefix = prefix # e.g., 'X1:VIS-HXTS_'
            self.system = 'VIS-'+prefix[3:-1] # e.g., 'VIS-HXTS' # FIXME allow for ASC
        self.watchdogs = data['watchdogs']
        self.bio = data['bio']

    # -------------------------------------------------------------------------------------------------
    # Assorted building-block methods
    def onorthelike(self,enable):
        """Building-block method to convert 'ON' or other truthy things to True."""
        return enable=='ON' or enable == True or (isinstance(enable, (int, float)) and enable != 0)
            
    def offorthelike(self,enable):
        """Building-block method to convert 'OFF' or other non-truthy things to False."""
        return enable=='OFF' or enable == False or (isinstance(enable, (int, float)) and enable == 0)
            
    def fmtprefix(self, withprefix):
        """Building-block method to return longer or shorter version of the PV prefix string. withprefix = 'full' -> "K1:VIS-BS or the like, 'halffull' -> 'VIS-BS_', 'halfbare' -> 'BS_', 'bare' ->''."""
        if withprefix=='full':
            return self.prefix 
        elif withprefix=='halffull':
            return 'VIS-'+self.name+'_'
        elif withprefix=='halfbare':
            return self.name+'_'
        elif withprefix=='bare':
            return ''
        else:
            return ''

    def levels(self, verbose=False, matlab=False):
        """Building-block method to return the list of all levels in the canonical sort order defined by the levelorder key in visData."""
        result = self.data['levelorder']
        if matlab: return toMatlab(result)
        else: return result

    def suspensionType(self, verbose=False, matlab=False):
        """Building-block method to return what the type of the suspension 'really is' per the 'reallyis' field of the definition. (Allows for variant types, e.g., HSTS->HSTS2, HSTS2M at LIGO.)"""
        result = self.data['reallyis']
        if matlab: return toMatlab(result)
        else: return result

    def levelchannames(self, sensact, nametype, levels=[], chans=[], verbose=False, matlab=False):
        """Building-block method to return a list of pvs for a block of type sensact. levels and chans narrow the list."""
        if levels==[]: ilevels = self.data['levelorder']
        else: ilevels = levels
        result = [
            chan
            for level in ilevels if sensact in self.data['levels'][level] and self.data['levels'][level][sensact]
            for chan in self.data['levels'][level][sensact][nametype] if chans==[] or chan in chans
        ]
        if matlab: return toMatlab(result)
        else: return result


    def levelsensactdata(self, sensact, data, key, levels=[], verbose=False, matlab=False):
        """Building-block method to return data stored at location specified by list key for a block of type sensact. levels and chans narrow the list."""
        if levels==[]: ilevels = self.data['levelorder']
        else: ilevels = levels
        if key==[]:
            result = [
                self.data['levels'][level][sensact][data]
                for level in ilevels if sensact in self.data['levels'][level] and self.data['levels'][level][sensact]
            ]
        elif len(key)==1:
            result = [
                self.data['levels'][level][sensact][data][key[0]]
                for level in ilevels if sensact in self.data['levels'][level] and self.data['levels'][level][sensact]
            ]
        elif len(key)==2:
            result = [
                self.data['levels'][level][sensact][data][key[0]][key[1]]
                for level in ilevels if sensact in self.data['levels'][level] and self.data['levels'][level][sensact]
            ]
        elif len(key)==3:
            result = [
                self.data['levels'][level][sensact][data][key[0]][key[1]][key[2]]
                for level in ilevels if sensact in self.data['levels'][level] and self.data['levels'][level][sensact]
            ]
        if matlab: return toMatlab(result)
        else: return result


    def switch(self, pv, setting, enable, verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Building-block method to enable/disable a switch. pv='BS_TM_DAMP_L' or the like, setting='_INPUT', enable='ON'/'OFF'."""
        if dorw==2 :
            if self.onorthelike(enable):
                retval = self.ezca.switch(self.infix+pv,setting,'ON')
            elif self.offorthelike(enable):
                retval = self.ezca.switch(self.infix+pv,setting,'OFF')
            else:
                retval = 'NC'
            result =  fmtpair(self.fmtprefix(withprefix)+pv,(setting,enable), pair)
        else:
            result =  fmtpair(self.fmtprefix(withprefix)+pv,(setting,dummyval), pair)            
        time.sleep(sleepTime) # DEBUG
        if verbose:
            print >>sys.stderr, '%s_%s <- %s' % (str(self.fmtprefix(withprefix)+pv),str(setting),enable)
        if matlab: return toMatlab(result)
        else: return result

    def write(self, pv, value, verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Building-block method to write a numeric value to a PV. pv='BS_TM_DAMP_L_OFFSET' or the like."""
        if dorw==2 :
            self.ezca.write(self.infix+pv,value)
        result = fmtpair(self.fmtprefix(withprefix)+pv,value, pair)
        if verbose: 
            print >>sys.stderr, '%s <- %s' % (str(self.fmtprefix(withprefix)+pv),value)
        time.sleep(sleepTime) # DEBUG
        if matlab: return toMatlab(result)
        else: return result

    def writelist(self, pvs, values, verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Building-block method to write a list of numeric values to a list of PVs. pvs=['BS_TM_DAMP_P','BS_TM_DAMP_Y'] or the like."""
        if len(pvs)!=len(values):
            raise VisError('Number of values doesn\'t match number of channels')
        result = [
            fmtpair(self.fmtprefix(withprefix)+pv,self.write(self.infix+pv,value, verbose=verbose,dorw=dorw), pair)
            for (pv,value) in zip(pvs,values)
        ]
        time.sleep(sleepTime) # DEBUG
        if matlab: return toMatlab(result)
        else: return result

    def read(self, pv, verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Building-block method to read a numeric value from a pv. pv='BS_TM_DAMP_L_OUTMON' or the like."""
        if dorw>=1 :
            result = self.ezca.read(self.infix+pv)
            if verbose: 
                print >>sys.stderr, '%s -> %s' % (str(self.fmtprefix(withprefix)+pv),str(result))
        else:
            result = dummyval
            if verbose: 
                print >>sys.stderr, '%s -> %s (dummy value)' % (str(self.fmtprefix(withprefix)+pv),str(result))
        return fmtpair(self.fmtprefix(withprefix)+pv,result, pair)

    def readlist(self,pvs, verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Building-block method to write a list of numeric values from a list of pvs. pvs=['BS_TM_DAMP_P_OUTMON','BS_TM_DAMP_Y_OUTMON'] or the like."""
        result = [
            fmtpair(self.fmtprefix(withprefix)+pv,self.read(self.infix+pv, verbose=verbose,dorw=dorw), pair)
            for pv in pvs
        ]
        if matlab: return toMatlab(result)
        else: return result

    # -------------------------------------------------------------
    # Watchdog methods

    # Return watchdog PV names
    def wdNames(self, levels=[], withprefix='bare', suffix='', verbose=False, pair='pv', matlab=False):
        """Returns a list of WD pvs. Optional argument levels narrows to a subset of possible levels."""
        allWds = self.watchdogs.keys()
        if levels==[]:
            wds = allWds
        else:
            wds = [wd.upper() for wd in levels if wd.upper() in allWds]
        result = []
        for wd in wds:
            pv = self.watchdogs[wd]
            if pv[0]==':': # fully qualified WD PV - don't try to respect withprefix setting
                pv=self.infix+pv
                result.append(fmtwd(self.infix+spv+suffix.upper(),wd,pair))
            else:
                result.append(fmtwd(self.fmtprefix(withprefix)+self.infix+pv+suffix.upper(),wd,pair))
        if matlab: return toMatlab(result)
        else: return result

    # Return tripped watchdog names
    def trippedWds(self, levels=[], withprefix='full', suffix='', verbose=False, pair='value', matlab=False, dorw=1):
        """Returns a list of WD pvs that are tripped. Optional argument levels narrows to a subset of possible levels."""
        allWds = self.watchdogs.keys()
        if levels==[]:
            wds = allWds
        else:
            wds = [wd.upper() for wd in levels if wd.upper() in allWds]
        result = []
        for wd in wds:
            pv = self.watchdogs[wd]
            if dorw>=1:
                trig = self.ezca.read(self.infix+pv+'_STATE')
            else:
                trig = dummyval # FIXME
            if not ((pv[-7:]=='DACKILL' and (trig==1 or trig==2)) or (pv[-5:]=='WDMON' and trig==1)):
                if pv[0]==':': # fully qualified WD PV - don't try to respect withprefix setting
                    pv=self.infix+pv
                    result.append(fmtwd(pv+suffix.upper(),wd,pair))
                else:
                    result.append(fmtwd(self.fmtprefix(withprefix)+self.infix+pv+suffix.upper(),wd,pair))
        if matlab: return toMatlab(result)
        else: return result
    # -------------------------------------------------------------
    # BIO methods
    global bioWdBitMask
    bioWdBitMask = 0b11110000000000000000

    # Return BIO PV names
    def bioWdPvs(self, levels=[], withprefix='bare', suffix='', verbose=False, pair='pv', matlab=False):
        """Returns a list of BIO pvs. Optional argument levels narrows to a subset of possible levels."""
        allBios = self.bio.keys()
        if levels==[]:
            bios = allBios
        else:
            bios = [bio.upper() for bio in levels if bio.upper() in allBios]
        result = []
        for bio in bios:
            pv = self.bio[bio]
            result.append(fmtbio(pv+suffix.upper(),bio,pair))
        if matlab: return toMatlab(result)
        else: return result

    # Return tripped BIO watchdog names
    def trippedBioWds(self, levels=[], withprefix='bare', suffix='', verbose=False, pair='pv', matlab=False, dorw=1):
        """Returns a list of BIO pvs that are tripped. Optional argument levels narrows to a subset of possible levels."""
        result = []
        for pv in self.bioWdPvs(levels=levels):
            if dorw>=1:
                trig = (int(self.ezca.read(self.infix+pv)) & bioWdBitMask)>>16
            else:
                trig = dummyval # FIXME
            if trig >0:
                result.append(fmtbio(self.fmtprefix(withprefix)+pv+suffix.upper(),trig,pair))
        if matlab: return toMatlab(result)
        else: return result

    # -------------------------------------------------------------
    # Timer methods
    def waitForRampingToKickIn(self,statename, time=1):
        statename.timer['waitForRampingToKickIn']=time
        while not(statename.timer['waitForRampingToKickIn']):
            pass


    # Return osem sensitivity
    def osemData(self, key, levels=[], verbose=False, matlab=False):
        """Return data stored for OSEMs. Optional argument levels narrows the selection."""
        return self.levelsensactdata('osemConfig','osem',key, levels=levels, verbose=verbose, matlab=matlab)

    # Return coil driver sensitivity
    def coilDriverData(self, key, levels=[], verbose=False, matlab=False):
        """Return data stored for coil drivers. Optional argument levels narrows the selection."""
        return self.levelsensactdata('osemConfig','driver',key, levels=levels, verbose=verbose, matlab=matlab)

    # Return magnet sensitivity
    def magnetData(self, key, levels=[], withprefix='bare', suffix='', verbose=False, matlab=False):
        """Return data stored for magnets. Optional argument levels narrows the selection."""
        return self.levelsensactdata('osemConfig','magnet',key, levels=levels, verbose=verbose, matlab=matlab)

    # Return OSEM names
    def osemNames(self, levels=[], chans=[], withprefix='bare', suffix='', verbose=False, matlab=False):
        """Return a list of OSEMs. Optional arguments levels and chans narrow the selection"""
        return self.levelchannames('osemConfig', 'chans', levels=levels, chans=chans, verbose=verbose, matlab=matlab)

    # Return OSEM DOF names
    def osemDofs(self, levels=[], chans=[], withprefix='bare', suffix='', verbose=False, matlab=False):
        """Return a list of DOFs associated with OSEMs. Optional arguments levels and chans narrow the selection"""
        return self.levelchannames('osemConfig', 'dofs', levels=levels, chans=chans, verbose=verbose, matlab=matlab)

    # Return OL names
    def olNames(self, levels=[], chans=[], withprefix='bare', suffix='', verbose=False, matlab=False):
        """Return a list of OL segment names. Optional arguments levels and chans narrow the selection."""
        return self.levelchannames('olConfig', 'chans', levels=levels, chans=chans, verbose=verbose, matlab=matlab)

    # Return OL DOF names
    def olDofs(self, levels=[], chans=[], withprefix='bare', suffix='', verbose=False, matlab=False):
        """Return a list of DOFs associated with OLs. Optional arguments levels and chans narrow the selection"""
        return self.levelchannames('olConfig', 'dofs', levels=levels, chans=chans, verbose=verbose, matlab=matlab)

    # -----------------------------------------------------------------------------------------------------------
    # Generic methods for all filter modules (DAMP, TEST, OSEMINF, COILOUTF)

    def genNumWrite(self, pvfn, suffix, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Building-block method to write filter numeric value or list of values (GAIN, TRAMP etc) - functions based on this should supply '_' in suffix, e.g., '_RAMP'."""
        pvs = pvfn(levels=levels,chans=chans)
        if type(value)==list:
            valuelist=value
            for value in valuelist:
                checkHaveLongVal(value)
            if len(pvs)!=len(valuelist):
                raise VisError('Number of values supplied not equal number to be written')
            result = [
                self.write(pv+suffix,value, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
                for (pv,value) in zip(pvs,valuelist)
            ] 
            if matlab: return toMatlab(result)
            else: 
                if not result[0] == None:
                    return result
        else:
            checkHaveLongVal(value)
            result = [
                self.write(pv+suffix,value, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
                for pv in pvs
            ] 
            if matlab: return toMatlab(result)
            else: 
                if not result == None:
                    return result

    def genNumRead(self, pvfn, suffix, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Building-block method to read filter numeric value (GAIN, TRAMP etc) - functions based on this should supply '_' in suffix, e.g., '_RAMP'."""
        pvs = pvfn(levels=levels,chans=chans)
        result = [
            self.read(pv+suffix, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
            for pv in pvs
        ]
        if matlab: return toMatlab(result)
        else: return result

    def genSwitchWrite(self, pvfn, suffix, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab = False, dorw=2):
        """Building-block method to switch filter switches on or off (OUTPUT, INPUT, OFFSET etc) - functions based on this should NOT supply '_' in suffix, e.g., 'OFFSET'."""
        if enable==True or enable=='ON' or enable == 1:
            pvs = pvfn(levels=levels,chans=chans)
            result = [
                self.switch(pv, suffix,'ON', verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
                for pv in pvs
        ]
        elif enable==False or enable=='OFF' or enable == 0:
            pvs = pvfn(levels=levels,chans=chans)
            result = [
                self.switch(pv, suffix,'OFF', verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
                for pv in pvs
        ]
        else:
            pass # NC = no change
        if matlab: return toMatlab(result)
        else: return result

    def genSwitchRead(self, pvfn, bits, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Building-block method to read the OR of selected filter switch states (OUTPUT, INPUT, OFFSET etc).
        bits can be either a single bit descriptor (e.g. 'OUTPUT') or a list (['INPUT','OUTPUT'])."""
        if type(bits)==str:
            masks = {cdsFiltMask[bits]['swnrsuffix'] : cdsFiltMask[bits]['swnrmask']}
        elif type(bits)==list:
            if len(bits)==0:
                bits=['INPUT','OUTPUT','OFFSET','DECIM','LIMIT','HOLD']
            masks = {}
            for bit in bits:
                if cdsFiltMask[bit]['swnrsuffix'] in masks:
                    masks[cdsFiltMask[bit]['swnrsuffix']] = masks[cdsFiltMask[bit]['swnrsuffix']]|cdsFiltMask[bit]['swnrmask'] # bitwise OR new mask into old
                else:
                    masks[cdsFiltMask[bit]['swnrsuffix']] = cdsFiltMask[bit]['swnrmask'] # create new key
        pvs = pvfn(levels=levels,chans=chans)
        result = []
        for pv in pvs:
            resultbit = 0
            resultsuffix = ''
            for suffix, mask in masks.items():
                if dorw>=1:
                    resultbit = bool(resultbit|bool(int(self.read(pv+suffix, dorw=dorw))&mask))
                else:
                    resultsbit = None
                resultsuffix = resultsuffix+suffix+'.'+str(mask)
            result.append(fmtpair(self.fmtprefix(withprefix)+pv+resultsuffix,resultbit, pair))          
        if matlab: return toMatlab(result)
        else: return result

    def genFilterModuleEnableRead(self, pvfn, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Building-block method to read filter module switches (FM1, FM2 etc)."""
        masks = {}
        bits = ['FM1','FM2','FM3','FM4','FM5','FM6','FM7','FM8','FM9','FM10','FM1S','FM2S','FM3S','FM4S','FM5S','FM6S','FM7S','FM8S','FM9S','FM10S']
        for bit in bits:
            if cdsFiltMask[bit]['swnrsuffix'] in masks:
                masks[cdsFiltMask[bit]['swnrsuffix']] = masks[cdsFiltMask[bit]['swnrsuffix']]|cdsFiltMask[bit]['swnrmask'] # bitwise OR new mask into old
            else:
                masks[cdsFiltMask[bit]['swnrsuffix']] = cdsFiltMask[bit]['swnrmask'] # create new key
        pvs = pvfn(levels=levels,chans=chans)
        result = []
        for pv in pvs:
            resultbit = 0
            resultsuffix = ''
            for suffix, mask in masks.items():
                if dorw>=1:
                    resultbit = bool(resultbit|bool(int(self.read(pv+suffix, dorw=dorw))&mask))
                else:
                    resultsbit = None
                resultsuffix = resultsuffix+suffix+'.'+str(mask)
            result.append(fmtpair(self.fmtprefix(withprefix)+pv+resultsuffix,resultbit, pair))          
        if matlab: return toMatlab(result)
        else: return result


    def genFilterModuleEnableWrite(self, pvfn, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Building-block method to enable/disable filter module switches (FM1, FM2 etc)."""
        if enable=='ON' or enable=='OFF':
            pvs = pvfn(levels=levels,chans=chans)
            result = [
                self.switch(pv,converttoFM(filt),enable, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
                for filt in filters
                for pv in pvs
            ]
        else:
            pass # NC = no change
        if pair=='none': result = None
        if matlab: return toMatlab(result)
        else: return result

    # -------------------------------------------------------------
    # Building-block methods for sensor/actuator-specific matrix blocks such as EUL2OSEM
 
    def levelsensactmatrixblockpvs(self, sensact, block, infix = '', levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        """Building-block method to return element PVs for a sensor/actuator specific matrix block type such as EUL2OSEM.
        Note that inputs are the _second_ index in the generated channel name 
        (e.g., ...EUL2OSEM_2_1 is the first input and second output),
        and correspond to columns in the auto-generated MEDM screens.
        sensact is a dictionary key selecting a sensor actuator group, e.g., 'osemConfig'.
        block is a dictionary key selecting a matrix block definition, e.g., 'eul2osem'.
        Optional argument infix allows for _RAMPING_1_1 etc channels in cdsRampMuxMatrix blocks.
        A structure similar to the following is assumed:
	    
	    visData = {
	        'levelorder': ['IP','F0','F1','BF','SF','TM'],
	        'levels' : {
                'TM':{
                    ...
                    'osemConfig' : {
                        'chans' : ['V1', 'V2', 'V3', 'H1', 'H2', 'H3'],
                        'dofs' : ['L', 'T', 'V', 'R', 'P', 'Y'],
                        'eul2osem' : {
                            'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 
                            'default':[[...],[...]],...]) # each sublist represents an _output_!
                        },
                        ...
                    },
                    ...
                },
                ...
	        },
	        ....
	    }
	    """
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if sensact in self.data['levels'][level] and self.data['levels'][level][sensact] and block in self.data['levels'][level][sensact]]
        else: 
            ilevels = [level for level in levels if level in self.data['levels'] and sensact in self.data['levels'][level] and self.data['levels'][level][sensact] and block in self.data['levels'][level][sensact]]
        result = []
        for level in ilevels:
            sensactdata = self.data['levels'][level][sensact]
            icns = [icn for icn in range(len(sensactdata[sensactdata[block]['inames']])) if ichans==[] or sensactdata[sensactdata[block]['inames']][icn] in ichans] # input channel indices to be iterated over
            ocns = [ocn for ocn in range(len(sensactdata[sensactdata[block]['onames']])) if ochans==[] or sensactdata[sensactdata[block]['onames']][ocn] in ochans] # output channel indices to be iterated over
            result+=[
                self.fmtprefix(withprefix)+level+'_'+sensactdata[block]['blockname']+infix+'_'+str(ocn+1)+'_'+str(icn+1) # inputs are columns; outputs are rows!
                for icn in icns
                for ocn in ocns
            ]
        if matlab: return toMatlab(result)
        else: return result
 
    def levelsensactmatrixblockdefs(self, sensact, block, levels=[], ichans=[], ochans=[], verbose=False, matlab=False):
        """Return element default values for a sensor/actuator specific matrix block type such as OSEM2EUL.
        See help on levelsensactmatrixblockpvs() for the assumed structure in visData.
        The 'default' dictionary key should point to a list of lists, with each sublist/row representing an _output.
        This function then flattens the defaults to a single list to match the flat list of PVs returned by levelsensactmatrixblockpvs()."""
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if sensact in self.data['levels'][level] and block in self.data['levels'][level][sensact]]
        else: 
            ilevels = [level for level in levels if level in self.data['levels'] and sensact in self.data['levels'][level] and block in self.data['levels'][level][sensact]]
        result = []
        for level in ilevels:
            sensactdata = self.data['levels'][level][sensact]
            if sensactdata[block]['default']==None: raise VisError('No defaults supplied for matrix block '+str(block)+' at level '+str(level))
            icns = [icn for icn in range(len(sensactdata[sensactdata[block]['inames']])) 
                if ichans==[] or sensactdata[sensactdata[block]['inames']][icn] in ichans] # input channel indices to be iterated over
            ocns = [ocn for ocn in range(len(sensactdata[sensactdata[block]['onames']])) 
                if ochans==[] or sensactdata[sensactdata[block]['onames']][ocn] in ochans] # output channel indices to be iterated over
            result+=[
                float(sensactdata[block]['default'][ocn][icn])  # inputs are columns; outputs are rows!
                for icn in icns
                for ocn in ocns
            ]
        if matlab: return toMatlab(result)
        else: return result
 
    def levelsensactmatrixblockread(self, sensact, block, infix = '', levels=[], ichans=[], ochans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read values for a sensor/actuator specific matrix block type such as OSEM2EUL."""
        pvs = self.levelsensactmatrixblockpvs(sensact,block, infix=infix, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix='bare', matlab=False)
        result = self.readlist(pvs, verbose=verbose, dorw=dorw)
        if matlab: return toMatlab(result)
        else: return result
 
    def levelsensactmatrixblockwrite(self, sensact, block, infix = '', operation='none', value=0.0, array=[], levels=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write values for a sensor/actuator specific matrix block type such as OSEM2EUL."""
        pvs = self.levelsensactmatrixblockpvs(sensact,block, infix = infix, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix='bare', matlab=False)
        if operation=='none':
            pass
        elif operation=='defaults':
            vals = self.levelsensactmatrixblockdefs(sensact,block, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, matlab=False)
        elif operation=='value':
            vals = [value for pv in pvs]
        elif operation=='array':
            if len(array)!=len(pvs): raise VisError('Length of array does not match number of channels ('+str(len(pvs))+')')
        self.writelist(pvs,vals, verbose=verbose, dorw=dorw)

    # -----------------------------------------------------------------------------------------------------------
    # Generic methods for sensor/actuator-specific filter modules (OSEMINF, COILOUTF, etc)
    # (Only the PV and default values methods care whether a filter module is sensor/actuator-specific.)
 
    def levelsensactfilterblockpvs(self, sensact, block, suffix = '', levels=[], chans=[], verbose=False, withprefix='bare', matlab=False):
        """Return all channel/DOF PVs for a sensor/actuator specific filter block type such as COILOUTF."""
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if sensact in self.data['levels'][level] and self.data['levels'][level][sensact] and block in self.data['levels'][level][sensact]]
        else: 
            ilevels = [level for level in levels if sensact in self.data['levels'][level] and self.data['levels'][level][sensact] and block in self.data['levels'][level][sensact]]
        result = [
            self.fmtprefix(withprefix)+level+'_'+self.data['levels'][level][sensact][block]['blockname']+'_'+chan+suffix
            for level in ilevels
            for chan in self.data['levels'][level][sensact][self.data['levels'][level][sensact][block]['names']] if (chans==[] or chan in chans)
        ]
        if matlab: return toMatlab(result)
        else: return result

    def levelsensactfilterblockdefs(self, sensact, block, levels=[], chans=[], verbose=False, suffix = '', matlab=False):
        """Return all default gain values for a sensor/actuator specific filter block type such as COILOUTF."""
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if self.data['levels'][level][sensact] and self.data['levels'][level][sensact][block]]
        else: 
            ilevels = [level for level in levels if level in self.data['levels'].keys() and self.data['levels'][level][sensact] and self.data['levels'][level][sensact][block]]
        result = []
        for level in ilevels:
            sensactdata = self.data['levels'][level][sensact]
            cs = [c for c in sensactdata[sensactdata[block]['names']] if chans==[] or c in chans] # input channels to be iterated over
            if 'default' not in sensactdata[block].keys() or 'gains' not in sensactdata[block]['default'].keys():
                raise VisError('No defaults supplied for block '+str(block)+' at level '+str(level))
            result+=[
                float(sensactdata[block]['default']['gains'][cn])
                for cn in range(len(cs))
            ]
        if matlab: return toMatlab(result)
        else: return result

    # FIXME: add method to return defaults

    # Generic methods for non-sensor/actuator-specific filter modules (DAMP, TEST, etc)
    # (Only the PV and default values methods care whether a filter module is sensor/actuator-specific.)
     
    def levelfilterblockpvs(self, block, levels=[], chans=[], verbose=False, withprefix='bare', suffix = '', matlab=False):
        """Return all channel/DOF PVs for a non-sensor/actuator specific filter block type such as DAMP/TEST/LOCK/etc."""
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if block in self.data['levels'][level] and self.data['levels'][level][block]]
        else:
            ilevels = [level for level in levels if level in self.data['levels'] and block in self.data['levels'][level] and self.data['levels'][level][block]]
        result = [ 
            self.fmtprefix(withprefix)+level+'_'+self.data['levels'][level][block]['blockname']+'_'+chan+suffix
            for level in ilevels
            for chan in self.data['levels'][level][self.data['levels'][level][block]['names']] if (chans==[] or chan in chans)
        ]
        if matlab: return toMatlab(result)
        else: return result

    # FIXME: add method to return defaults

    # -------------------------------------------------------------
    # Building-block methods for non-sensor/actuator specific matrix blocks such as CART2EUL 
    # KAGRA currently has CART2EUL in IM, but it will probably go away because neither of the blocks it's 
    # between (ISIINF and ISIWIT) are connected or even meaningful in KAGRA.
 
    def levelmatrixblockpvs(self, block, infix = '', levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        """Building-block method to return all element PVs for a non-sensor/actuator specific matrix block type such as CART2EUL. 
        block is a dictionary key selecting a matrix block definition, e.g., 'cart2eul'.
        A structure similar to the following is assumed:
	    
	    visData = {
	        'levelorder': ['IP','F0','F1','BF','SF','IM','TM'],
	        'levels' : {
                ... 
                'IM':{
                    'dofs' : ['L', 'T', 'V', 'R', 'P', 'Y'],
                    'isichans' : ['X', 'Y', 'RZ', 'Z', 'RX', 'RY'],
                    ...
                    'cart2eul' : {'blockname':'CART2EUL', 'inames':'isichans', 'onames':'dofs', 'default':[...]},
                    ...
                },
	        },
	        ....
	    }
	    """
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if level in self.data['levels'] and block in self.data['levels'][level]]
        else: 
            ilevels = [level for level in levels if level in self.data['levels'] and block in self.data['levels'][level]]
        result = []
        for level in ilevels:
            leveldata = self.data['levels'][level]
            ics = [ic for ic in leveldata[leveldata[block]['inames']] if ichans==[] or ic in ichans] # input channels to be iterated over
            ocs = [oc for oc in leveldata[leveldata[block]['onames']] if ochans==[] or oc in ochans] # output channels to be iterated over
            result+=[
                self.fmtprefix(withprefix)+level+'_'+leveldata[block]['blockname']+infix+'_'+str(icn+1)+'_'+str(ocn+1)
                for icn in range(len(ics))
                for ocn in range(len(ocs))
            ]
        if matlab: return toMatlab(result)
        else: return result
 
    def levelmatrixblockbasepvs(self, block, infix = '', levels=[], verbose=False, withprefix='bare', matlab=False):
        """Building-block method to return all base PVs for a non-sensor/actuator specific matrix block type such as DAMPMODE. 
        block is a dictionary key selecting a matrix block definition, e.g., 'dampmode'.
        See help on levelmatrixblockpvs() for required structure of visData.
	    """
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if level in self.data['levels'] and block in self.data['levels'][level]]
        else: 
            ilevels = [level for level in levels if level in self.data['levels'] and block in self.data['levels'][level]]
        result = []
        for level in ilevels:
            print(result)
            leveldata = self.data['levels'][level]
            result+=[self.fmtprefix(withprefix)+level+'_'+leveldata[block]['blockname']+infix]
        if matlab: return toMatlab(result)
        else: return result
 
    def levelmatrixblockdefs(self, block, levels=[], ichans=[], ochans=[], verbose=False, matlab=False):
        """Building-block method to return element default values for a non-sensor/actuator specific matrix block type such as CART2EUL.
        See help for levelmatrixblockpvs() for more on the assumed structure in visData."""
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if level in self.data['levels'] and block in self.data['levels'][level]]
        else: 
            ilevels = [level for level in levels if level in self.data['levels'] and block in self.data['levels'][level]]
        result = []
        for level in ilevels:
            leveldata = self.data['levels'][level]
            ics = [ic for ic in leveldata[leveldata[block]['inames']] if ichans==[] or ic in ichans] # input channels to be iterated over
            ocs = [oc for oc in leveldata[leveldata[block]['onames']] if ochans==[] or oc in ochans] # output channels to be iterated over
            if leveldata[block]['default']==None: raise VisError('No defaults supplied for block '+str(block)+' at level '+str(level))
            result+=[
                float(leveldata[block]['default'][ocn][icn])
                for icn in range(len(ics))
                for ocn in range(len(ocs))
            ]
        if matlab: return toMatlab(result)
        else: return result
 
    def levelmatrixblockread(self, block, infix = '', levels=[], ichans=[], ochans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Building-block method to read values for a non-sensor/actuator specific matrix block type such as CART2EUL."""
        pvs = self.levelmatrixblockpvs(block, infix=infix, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix='bare', matlab=False)
        result = self.readlist(pvs, verbose=verbose, dorw=2)
        if matlab: return toMatlab(result)
        else: return result
  
    def levelmatrixblockwrite(self, block, operation='none', infix = '', value=0.0, array=[], levels=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write values for a non-sensor/actuator specific matrix block type such as CART2EUL."""
        pvs = self.levelmatrixblockpvs(block, infix = infix, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix='bare', matlab=False)
        if operation=='none':
            pass
        elif operation=='defaults':
            vals = self.levelmatrixblockdefs(block, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, matlab=False)
        elif operation=='value':
            vals = [value for pv in pvs]
        elif operation=='array':
            if type(array)!=list: raise VisError('Non-array passed to ...WriteArray method')
            if len(array)!=0 and type(array[0])==list:
                vals = sum(array,[])
            else:
                vals=array
            if len(vals)!=len(pvs): raise VisError('Length of array ('+str(len(array))+') does not match number of PVs ('+str(len(pvs))+')')
        self.writelist(pvs,vals, verbose=verbose, dorw=dorw)

# -----------------
    def witPvs(self, levels=[], chans=[], verbose=False, withprefix='bare', matlab=False, suffix=''):
        """Return all witness PVs."""
        if levels==[]:
            ilevels = [level for level in self.data['levelorder'] if 'wit' in self.data['levels'][level] and self.data['levels'][level]['wit']]
        else:
            ilevels = [level for level in levels if level in self.data['levels'] and 'wit' in self.data['levels'][level] and self.data['levels'][level]['wit']]
        result = [] 
        for level in ilevels:
            for chan in self.data['levels'][level][self.data['levels'][level]['wit']['names']]:
                if (chans==[] or chan in chans):
                    result.append(self.fmtprefix(withprefix)+level+'_'+self.data['levels'][level]['wit']['blockname']+'_'+chan+self.data['levels'][level]['witsuffix']+suffix)
        if matlab: return toMatlab(result)
        else: return result

    def witRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the witness channels. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.witPvs, '', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)


    # -----------------------------------------------------------------------------------------------------------
    # Methods for OSEM2EUL blocks, implemented manually, interspersed with command strings for generating similar methods programmatically

    def o2ePvs(self, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        """Return PV names for all or selected OSEM2EUL matrix elements."""
        return self.levelsensactmatrixblockpvs('osemConfig','osem2eul', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)

    global lmPvs
    lmPvs = """def _lm_%(cc)sPvs(self, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        \"\"\"Return PV names for all or selected %(uc)s matrix elements.\"\"\"
        return self.levelsensactmatrixblockpvs(%(key)s, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)"""

    def o2eDefs(self, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        """Return default values for all or selected OSEM2EUL matrix elements."""
        return self.levelsensactmatrixblockdefs('osemConfig','osem2eul', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)

    global lmDefs
    lmDefs = """def _lm_%(cc)sDefs(self, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        \"\"\"Return default values for all or selected %(uc)s matrix elements.\"\"\"
        return self.levelsensactmatrixblockdefs(%(key)s, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)"""

    def o2eRead(self, levels=[], ichans=[], ochans=[], verbose=False, pair='value', withprefix='bare', matlab=False):
        """Read  all or selected OSEM2EUL input/output matrix values."""
        return self.levelsensactmatrixblockread('osemConfig','osem2eul', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)

    global lmRead
    lmRead = """def _lm_%(cc)sRead(self, levels=[], ichans=[], ochans=[], verbose=False, pair='value', withprefix='bare', matlab=False):
        \"\"\"Read  all or selected %(uc)s input/output matrix values.\"\"\"
        return self.levelsensactmatrixblockread(%(key)s, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)"""

    def o2eWriteDefaults(self, levels=[], value=0.0, array=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write default values for all or selected OSEM2EUL input and output matrix elements."""
        return self.levelsensactmatrixblockwrite('osemConfig','osem2eul','defaults', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)

    global lmWriteDefaults
    lmWriteDefaults = """def _lm_%(cc)sWriteDefaults(self, levels=[], value=0.0, array=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write default values for all or selected %(uc)s input and output matrix elements.\"\"\"
        return self.levelsensactmatrixblockwrite(%(key)s,'defaults', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)"""

    def o2eWriteValue(self, value, levels=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a common value into all or selected OSEM2EUL matrix elements."""
        return self.levelsensactmatrixblockwrite('osemConfig','osem2eul','value',value=value, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)

    global lmWriteValue
    lmWriteValue = """def _lm_%(cc)sWriteValue(self, value, levels=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write a common value into all or selected %(uc)s matrix elements.\"\"\"
        return self.levelsensactmatrixblockwrite(%(key)s,'value',value=value, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)"""

    def o2eWriteArray(self, array, levels=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write an array into all or selected OSEM2EUL matrix elements."""
        return self.levelsensactmatrixblockwrite('osemConfig','osem2eul','array', array=array, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)

    global lmWriteArray
    lmWriteArray = """def _lm_%(cc)sWriteArray(self, array, levels=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write an array into all or selected %(uc)s matrix elements.\"\"\"
        return self.levelsensactmatrixblockwrite(%(key)s,'array', array=array, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)"""

    # -----------------------------------------------------------------------------------------------------------
    # Methods for DAMPSWITCH blocks, implemented manually, interspersed with command strings for generating similar methods programmatically

    def dampModePvs(self, infix='', levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        """Return PV names for all or selected DAMPSWITCH matrix elements. 
        Optional argument infix allows for access to the _RAMPING and _SETTING channels"""
        return self.levelmatrixblockpvs('dampmode', infix='', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)
        
    def dampModeBasePvs(self, levels=[], ichans=[], ochans=[], chans=[], verbose=False, withprefix='bare', matlab=False):
        """Return PV names for all or selected DAMPSWITCH matrix elements. 
        Optional argument infix allows for access to the _RAMPING and _SETTING channels"""
        return self.levelmatrixblockbasepvs('dampmode', infix='', levels=levels, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def dampModeDefs(self, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        """Return default values for all or selected DAMPSWITCH matrix elements. 
        Optional argument infix allows for access to the _RAMPING and _SETTING channels."""
        return self.levelmatrixblockdefs('dampmode', infix=infix, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def dampModePressButton(self, levels=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a button press of all or selected DAMPMODE LOAD MATRIX buttons."""
        return self.genNumWrite(self.dampModeBasePvs, '_LOAD_MATRIX', value=1, levels=levels, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampModeCurrentRead(self, levels=[], ichans=[], ochans=[], verbose=False, pair='value', withprefix='bare', matlab=False):
        """Read current values of all or selected DAMPSWITCH input/output matrix elements."""
        return self.levelmatrixblockread('dampmode', infix='', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def dampModeSettingRead(self, levels=[], ichans=[], ochans=[], verbose=False, pair='value', withprefix='bare', matlab=False):
        """Read pending values of all or selected DAMPSWITCH input/output matrix elements."""
        return self.levelmatrixblockread('dampmode', infix='_SETTING', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def dampModeSettingWriteValue(self, value, levels=[], array=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a common setting value into all or selected DAMPMODE matrix elements."""
        return self.levelmatrixblockwrite('dampmode','value', infix='_SETTING', value=value, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)

    def dampModeSettingWriteArray(self, array, levels=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write an array into all or selected OSEM2EUL matrix elements."""
        return self.levelmatrixblockwrite('dampmode','array', infix='_SETTING', array=array, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)

    # -----------------------------------------------------------------------------------------------------------
    # Methods for EUL2OSEM blocks

#     def e2oRead(self, levels=[], ichans=[], ochans=[], verbose=False, pair='value', withprefix='bare', matlab=False):
#         """Return PV names for all or selected EUL2OSEM matrix elements."""
#         return self.levelsensactmatrixblockread('osemConfig','eul2osem', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab)
# 
#         """Write default values for all or selected EUL2OSEM input and output matrix elements."""
#     def e2oWriteDefaults(self, levels=[], value=0.0, array=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
#         self.levelsensactmatrixblockwrite('osemConfig','eul2osem','defaults', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)
# 
#     def e2oWriteValue(self, levels=[], value=0.0, array=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
#         """Write a common value into all or selected EUL2OSEM matrix elements."""
#         self.levelsensactmatrixblockwrite('osemConfig','eul2osem','value',value=value, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)
# 
#     def e2oWriteArray(self, levels=[], value=0.0, array=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
#         """Write an array into all or selected EUL2OSEM matrix elements."""
#         self.levelsensactmatrixblockwrite('osemConfig','eul2osem','array', array=array, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)

    # -------------------------------------------------------------
    # Methods for specific matrices, blocks, switches.
    
    # Methods for top-level items
    # Switch the Master Switch
    def masterSwitchWrite(self, enable, verbose=False, pair='none', withprefix='bare', dorw=2):
        """Write to the MASTER SWITCH. Accepts enable = 'ON'/True/x>1 or 'OFF'/False/0."""
        pv = self.data['master']
        if self.onorthelike(enable):
            self.write(pv,"ON", verbose=verbose, pair=pair, withprefix=withprefix, dorw=dorw)
        elif self.offorthelike(enable):
            self.write(pv,"OFF", verbose=verbose, pair=pair, withprefix=withprefix,  dorw=dorw)
        else:
            pass # NC = no change
        return None # FIXME return something better

    # Read the Master Switch
    def masterSwitchRead(self, verbose=False, pair='none', withprefix='bare', dorw=2):
        """Read the MASTER SWITCH (returns True/False)."""
        pv = self.data['master']
        if dorw>=1:
            result = self.read(pv, dorw=dorw)
            if verbose: 
                print >>sys.stderr, '%s -> %s' % (str(self.fmtprefix(withprefix)+pv),result)
        else:
            result = dummyval
            if verbose: 
                print >>sys.stderr, '%s -> %s (dummy value)' % (str(self.fmtprefix(withprefix)+pv),result)
        return result==1

    # Switch the Commissioning Switch
    def commSwitchWrite(self, enable, verbose=False, pair='none', withprefix='bare', dorw=2):
        """Write to the COMMISSIONING (a.k.a., MEASUREMENT) SWITCH. Accepts enable = 'ON'/True/x>1 or 'OFF'/False/0."""
        pv = self.data['commissioning']
        if self.onorthelike(enable):
            self.write(pv,"ON", verbose=verbose, pair=pair, withprefix=withprefix, dorw=dorw)
        elif self.offorthelike(enable):
            self.write(pv,"OFF", verbose=verbose, pair=pair, withprefix=withprefix,  dorw=dorw)
        else:
            pass # NC = no change
        return None # FIXME return something better

    # Read the Commissioning Switch
    def commSwitchRead(self, verbose=False, pair='none', withprefix='bare', dorw=2):
        """Read the COMMISSIONING (a.k.a., MEASUREMENT) SWITCH (returns True/False)."""
        pv = self.data['commissioning']
        result = self.read(pv, dorw=dorw)
        if dorw>=1:
            result = self.read(pv, dorw=dorw)
            if verbose: 
                print >>sys.stderr, '%s -> %s' % (str(self.fmtprefix(withprefix)+pv),result)
        else:
            result = dummyval
            if verbose: 
                print >>sys.stderr, '%s -> %s (dummy value)' % (str(self.fmtprefix(withprefix)+pv),result)
        return result==1

    # -------------------------------------------------------------
    # A full set of methods for DAMP blocks implemented manually, interspersed with command strings for generating
    # similar methods for level-specific filter blocks programmatically

    def dampPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        """Return a list of PVs for DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.levelfilterblockpvs('damp', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    global lfPvs
    lfPvs = """def _lf_%(cc)sPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        \"\"\"Return a list of PVs for %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.%(pvfn)s(%(key)s, levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)
        """

    def dampPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in DAMP blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.dampPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.dampPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfPressButton
    lfPressButton = """def _lf_%(cc)sPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        if button == 'LOAD':
            return self.genNumWrite(self.%(cc)sPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.%(cc)sPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    # INPUT stuff
    def dampInputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the INPUT switch in DAMP blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.dampPvs, 'INPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfInputSwitchRead
    lfInputSwitchRead = """def _lf_%(cc)sInputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the INPUT switch in %(uc)s blocks. Optional arguments levels and chans select particular channels. Returns list of True/False.\"\"\"
        return self.genSwitchRead(self.%(cc)sPvs, 'INPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the INPUT switch in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dampPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfInputSwitchWrite
    lfInputSwitchWrite = """def _lf_%(cc)sInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write 'ON' or 'OFF' to the INPUT switch in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genSwitchWrite(self.%(cc)sPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampInmonRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the INMON value in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.dampPvs, '_INMON', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfInmonRead
    lfInmonRead = """def _lf_%(cc)sInmonRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the INMON value in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genNumRead(self.%(cc)sPvs, '_INMON', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    # OUTPUT stuff
    def dampOutputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OUTPUT switch in DAMP blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.dampPvs, 'OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfOutputSwitchRead
    lfOutputSwitchRead = """def _lf_%(cc)sOutputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the OUTPUT switch in %(uc)s blocks. Optional arguments levels and chans select particular channels. Returns list of True/False.\"\"\"
        return self.genSwitchRead(self.%(cc)sPvs, 'OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OUTPUT switch in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dampPvs, 'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfOutputSwitchWrite
    lfOutputSwitchWrite = """def _lf_%(cc)sOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write 'ON' or 'OFF' to the OUTPUT switch in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genSwitchWrite(self.%(cc)sPvs, 'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampOutmonRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OUTMON value in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.dampPvs, '_OUTMON', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfOutmonRead
    lfOutmonRead = """def _lf_%(cc)sOutmonRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the OUTMON value in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genNumRead(self.%(cc)sPvs, '_OUTMON', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampOutputRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OUTPUT value in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.dampPvs, '_OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfOutputRead
    lfOutputRead = """def _lf_%(cc)sOutputRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the OUTPUT value in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genNumRead(self.%(cc)sPvs, '_OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    # OFFSET stuff
    def dampOffsetSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OFFSET switch in DAMP blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.dampPvs, 'OFFSET', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfOffsetSwitchRead
    lfOffsetSwitchRead = """def _lf_%(cc)sOffsetSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the OFFSET switch in %(uc)s blocks. Optional arguments levels and chans select particular channels. Returns list of True/False.\"\"\"
        return self.genSwitchRead(self.%(cc)sPvs, 'OFFSET', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampOffsetSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OFFSET switch in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dampPvs, 'OFFSET', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfOffsetSwitchWrite
    lfOffsetSwitchWrite = """def _lf_%(cc)sOffsetSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write 'ON' or 'OFF' to the OFFSET switch in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genSwitchWrite(self.%(cc)sPvs, 'OFFSET', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampOffsetRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the offset value in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.dampPvs, '_OFFSET', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfOffsetRead
    lfOffsetRead = """def _lf_%(cc)sOffsetRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the offset value in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genNumRead(self.%(cc)sPvs, '_OFFSET', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampOffsetWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the OFFSET field in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.dampPvs, '_OFFSET', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfOffsetWrite
    lfOffsetWrite = """def _lf_%(cc)sOffsetWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write a value or list of values to the OFFSET field in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genNumWrite(self.%(cc)sPvs, '_OFFSET', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    # HOLD stuff
    def dampHoldSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the HOLD switch in DAMP blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.dampPvs, 'HOLD', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfHoldSwitchRead
    lfHoldSwitchRead = """def _lf_%(cc)sHoldSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the HOLD switch in %(uc)s blocks. Optional arguments levels and chans select particular channels. Returns list of True/False.\"\"\"
        return self.genSwitchRead(self.%(cc)sPvs, 'HOLD', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampHoldSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the HOLD switch in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dampPvs, 'HOLD', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfHoldSwitchWrite
    lfHoldSwitchWrite = """def _lf_%(cc)sHoldSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write 'ON' or 'OFF' to the HOLD switch in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genSwitchWrite(self.%(cc)sPvs, 'HOLD', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    # LIMIT stuff
    def dampLimitSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the LIMIT switch in DAMP blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.dampPvs, 'LIMIT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfLimitSwitchRead
    lfLimitSwitchRead = """def _lf_%(cc)sLimitSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the LIMIT switch in %(uc)s blocks. Optional arguments levels and chans select particular channels. Returns list of True/False.\"\"\"
        return self.genSwitchRead(self.%(cc)sPvs, 'LIMIT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampLimitSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the LIMIT switch in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dampPvs, 'LIMIT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfLimitSwitchWrite
    lfLimitSwitchWrite = """def _lf_%(cc)sLimitSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write 'ON' or 'OFF' to the LIMIT switch in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genSwitchWrite(self.%(cc)sPvs, 'LIMIT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampLimitRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the limit value in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.dampPvs, '_LIMIT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfLimitRead
    lfLimitRead = """def _lf_%(cc)sLimitRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the limit value in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genNumRead(self.%(cc)sPvs, '_LIMIT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampLimitWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the GAIN field in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.dampPvs, '_LIMIT', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfLimitWrite
    lfLimitWrite = """def _lf_%(cc)sLimitWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write a value or list of values to the GAIN field in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genNumWrite(self.%(cc)sPvs, '_LIMIT', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    # GAIN stuff
    def dampGainRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain value in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.dampPvs, '_GAIN', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfGainRead
    lfGainRead = """def _lf_%(cc)sGainRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the gain value in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genNumRead(self.%(cc)sPvs, '_GAIN', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the GAIN field in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.dampPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfGainWrite
    lfGainWrite = """def _lf_%(cc)sGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write a value or list of values to the GAIN field in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genNumWrite(self.%(cc)sPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    # RAMP stuff
    def dampRampRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the ramp value in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.dampPvs, '_RAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfRampRead
    lfRampRead = """def _lf_%(cc)sRampRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the ramp value in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genNumRead(self.%(cc)sPvs, '_RAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the RAMP field in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.dampPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfRampWrite
    lfRampWrite = """def _lf_%(cc)sRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write a value or list of values to the RAMP field in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genNumWrite(self.%(cc)sPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampGainRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain ramping state (GRAMP) in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.dampPvs, 'GRAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfGainRampingRead
    lfGainRampingRead = """def _lf_%(cc)sGainRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the gain ramping state (GRAMP) in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genSwitchRead(self.%(cc)sPvs, 'GRAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampOffsetRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the offset ramping state (ORAMP) in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.dampPvs, 'ORAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfOffsetRampingRead
    lfOffsetRampingRead = """def _lf_%(cc)sOffsetRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the offset ramping state (ORAMP) in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genSwitchRead(self.%(cc)sPvs, 'ORAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the overall ramping state (GRAMP or ORAMP) in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.dampPvs, ['GRAMP','ORAMP'], levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfRampingRead
    lfRampingRead = """def _lf_%(cc)sRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the overall ramping state (GRAMP or ORAMP) in %(uc)s blocks. Optional arguments levels and chans select particular channels.\"\"\"
        return self.genSwitchRead(self.%(cc)sPvs, ['GRAMP','ORAMP'], levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    # Filter stuff
    def dampFilterModuleEnableRead(self, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Read the filter switches in DAMP blocks. Optional arguments filters, levels and chans select particular channels."""
        return self.genFilterModuleEnableRead(self.dampPvs, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfFilterModuleEnableRead
    lfFilterModuleEnableRead = """def _lf_%(cc)sFilterModuleEnableRead(self, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Read the filter switches in %(uc)s blocks. Optional arguments filters, levels and chans select particular channels.\"\"\"
        return self.genFilterModuleEnableRead(self.%(cc)sPvs, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    def dampFilterModuleEnableWrite(self, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the filter switches in DAMP blocks. Optional arguments filters, levels and chans select particular channels."""
        return self.genFilterModuleEnableWrite(self.dampPvs, enable, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    global lfFilterModuleEnableWrite
    lfFilterModuleEnableWrite = """def _lf_%(cc)sFilterModuleEnableWrite(self, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        \"\"\"Write 'ON' or 'OFF' to the filter switches in %(uc)s blocks. Optional arguments filters, levels and chans select particular channels.\"\"\"
        return self.genFilterModuleEnableWrite(self.%(cc)sPvs, enable, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)"""

    # FIXME: more stuff here

    # FIXME: more stuff here

# End of Vis() class definition

# --------------------------------------------------------------------------------------
# Generate additional methods programmatically  

# Generate methods based on levelfilterblockpvs, e.g., DAMP, and levelsensactfilterblockpvs, e.g., OSEMINF
# Sets to keep track of methods as they're generated, by signature, for later use with the command line stuff.
callableLevelFilterNameCommandsAuto = set()

callableLevelFilterReadCommandsAuto = set()
callableLevelFilterWriteCommandsAuto = set()

callableLevelFilterSwitchReadCommandsAuto = set()
callableLevelFilterSwitchWriteCommandsAuto = set()
callableLevelFilterPressButtonCommandsAuto = set()

callableLevelFilterModuleEnableReadCommandsAuto = set()
callableLevelFilterModuleEnableWriteCommandsAuto = set()

# The list of method types that can be generated programmatically for level blocks (e.g., DAMP)
lfFullSet = ['Pvs', 'PressButton', 'InputSwitchRead', 'InputSwitchWrite', 'InmonRead', 'OutputSwitchRead', 'OutputSwitchWrite', 'OutmonRead', 'OutputRead', 'OffsetSwitchRead', 'OffsetSwitchWrite', 'OffsetRead', 'OffsetWrite', 'HoldSwitchRead', 'HoldSwitchWrite', 'LimitSwitchRead', 'LimitSwitchWrite', 'LimitRead', 'LimitWrite', 'GainRead', 'GainWrite', 'RampRead','RampWrite', 'GainRampingRead', 'OffsetRampingRead', 'RampingRead', 'FilterModuleEnableRead', 'FilterModuleEnableWrite']

# Minimal lists of methods to generate based on Type B usage. Feel free to expand them one method at a time or use lfFullSet.
lfAlignMethods = ['Pvs','GainWrite','RampWrite']
lfdcctrlMethods = ['Pvs','GainWrite','InputSwitchWrite','OffsetSwitchWrite',
    'OutputSwitchWrite','PressButton','RampWrite','RampingRead']
lfOlDccctrlMethods = ['Pvs','GainWrite','InputSwitchWrite',
    'OffsetSwitchWrite','OutputSwitchWrite','PressButton','RampWrite','RampingRead']
lfOlSetMethods =  ['Pvs','GainWrite','OffsetWrite','OffsetSwitchWrite','RampWrite','RampingRead']
lfSetMethods = ['Pvs','GainWrite','OffsetWrite','OffsetSwitchWrite','RampWrite','RampingRead']

# The list of methods to generate, by block. Each entry is a tuple with a dictionary and a list of method types.
# The dictionary needs to give subsitutions for the following:
#  'pvfn': the pv function, either 'levelfilterblockpvs' or 'levelsensactfilterblockpvs' - this is used for the xxxPvs() method
#  'uc': the block name in upper case, e.g., 'OLDAMP' - this is used in the docstrings
#  'cc': the block name in camel case, e.g., 'olDamp' - this is used in the method names
#  'key': the key value(s) for the block in visData, e.g., "'oldamp'" or "'olConfig','inf'"- this is used for the xxxPvs() method - note nested quotes
# The list should be either lfFullSet (defined above) or a suitable subset

lfMethodsToGenerate = [
({'pvfn':'levelfilterblockpvs','uc':'DAMP','cc':'damp','key':"'damp'"},[]), # DAMP methods are implemented manually as the pattern
({'pvfn':'levelfilterblockpvs','uc':'IDAMP','cc':'idamp','key':"'idamp'"},lfFullSet),
({'pvfn':'levelfilterblockpvs','uc':'TEST','cc':'test','key':"'test'"},lfFullSet),
({'pvfn':'levelfilterblockpvs','uc':'LOCK','cc':'lock','key':"'lock'"},lfFullSet),
({'pvfn':'levelfilterblockpvs','uc':'OPTICALIGN','cc':'align','key':"'align'"},lfFullSet),
({'pvfn':'levelfilterblockpvs','uc':'DCCTRL','cc':'dcctrl','key':"'dcctrl'"},lfFullSet),
({'pvfn':'levelfilterblockpvs','uc':'OLDCCTRL','cc':'olDcctrl','key':"'oldcctrl'"},lfFullSet),
({'pvfn':'levelfilterblockpvs','uc':'OLDSET','cc':'olSet','key':"'olset'"},lfFullSet),
({'pvfn':'levelfilterblockpvs','uc':'SET','cc':'set','key':"'set'"},lfFullSet),
({'pvfn':'','uc':'','cc':'','key':"''"},[]), # DUMMY entry to partition the the halves of the list
({'pvfn':'levelsensactfilterblockpvs','uc':'OSEMINF','cc':'osem','key':"'osemConfig','inf'"},lfFullSet),
({'pvfn':'levelsensactfilterblockpvs','uc':'COILOUTF','cc':'coil','key':"'osemConfig','outf'"},lfFullSet),
({'pvfn':'levelsensactfilterblockpvs','uc':'OL','cc':'ol','key':"'olConfig','full'"},lfFullSet),
({'pvfn':'levelsensactfilterblockpvs','uc':'OLSEG','cc':'olSeg','key':"'olConfig','inf'"},lfFullSet),
({'pvfn':'','uc':'','cc':'','key':"''"},[]) # DUMMY entry to occupy the last place in the list and reduce editing errors
]
for subs, methods in lfMethodsToGenerate:
    for method in methods:
        exec('defcommandstring = lf'+method) # do the substitution for triple quotes separately to avoid putting it in the table
        exec(defcommandstring%subs)
        attachcommandstring = "Vis.%(cc)s"+method+" = _lf_%(cc)s"+method
        exec(attachcommandstring%subs)
        if method in ['Pvs']: 
            callableLevelFilterNameCommandsAuto.add("%(cc)s"%subs+method)
            
        if method in ['InmonRead','OutmonRead', 'OutputRead','OffsetRead','LimitRead','GainRead','RampRead']: 
            callableLevelFilterReadCommandsAuto.add("%(cc)s"%subs+method)

        if method in ['RampWrite','OffsetWrite','GainWrite','LimitWrite']: 
            callableLevelFilterWriteCommandsAuto.add("%(cc)s"%subs+method)
            
        if method in ['InputSwitchRead','OutputSwitchRead','OffsetSwitchRead','HoldSwitchRead',
        'LimitSwitchRead','OffsetRampingRead','GainRampingRead','RampingRead']: 
            callableLevelFilterSwitchReadCommandsAuto.add("%(cc)s"%subs+method)
            
        if method in ['InputSwitchWrite','OutputSwitchWrite','OffsetSwitchWrite','HoldSwitchWrite','LimitSwitchWrite']: 
            callableLevelFilterSwitchWriteCommandsAuto.add("%(cc)s"%subs+method)
            
        if method in ['FilterModuleEnableRead']: 
            callableLevelFilterModuleEnableReadCommandsAuto.add("%(cc)s"%subs+method)
            
        if method in ['FilterModuleEnableWrite']: 
            callableLevelFilterModuleEnableWriteCommandsAuto.add("%(cc)s"%subs+method)
            
        if method in ['PressButton']: 
            callableLevelFilterPressButtonCommandsAuto.add("%(cc)s"%subs+method)
            

# Generate methods based on levelmatrixblockpvs, e.g., ????, and levelsensactmatrixblockpvs, e.g., OSEM2EUL
# Sets to keep track of methods as they're generated, by signature, for later use with the command line stuff.
callableLevelMatrixNameCommandsAuto = set()

callableLevelMatrixReadCommandsAuto = set() # also used for xxxWriteDefaults
callableLevelMatrixWriteCommandsAuto = set()

# The list of method types that can be generated programmatically for level-specific matrix blocks
lmFullSet = ['Pvs', 'Defs','Read','WriteDefaults','WriteValue','WriteArray']

# The list of methods to generate, by block. Each entry is a tuple with a dictionary and a list of method types.
# The dictionary needs to give subsitutions for the following:
#  'pvfn': the pv function, either 'levelmatrixblockpvs' or 'levelsensactmatrixblockpvs' - this is used for the xxxPvs() method
#  'uc': the block name in upper case, e.g., 'OSEM2EUL' - this is used in the docstrings
#  'cc': the block name in camel case, e.g., o2e - this is used in the method names
#  'key': the key value(s) for the block in visData, e.g., "'c2e'" or "'osemConfig','eul2osem'"- this is used for the xxxPvs() method
#  'tq: a triple double quote in single quotes: '"""' - this is used in the docstrings
# The list should be either lmFullSet (defined above) or a suitable subset

lmMethodsToGenerate = [
({'pvfn':'levelmatrixblockpvs','uc':'TBD','cc':'tbd','key':"'tbd'"},[]), # template
({'pvfn':'','uc':'','cc':'','key':"''"},[]), # DUMMY entry to partition the halves of the list
({'pvfn':'levelsensactmatrixblockpvs','uc':'OSEM2EUL','cc':'o2e','key':"'osemConfig','osem2eul'"},[]), # OSEM2EUL methods are implemented manually as the pattern
({'pvfn':'levelsensactmatrixblockpvs','uc':'OSEM2EUL','cc':'o2e','key':"'osemConfig','osem2eul'"},[]), # generated manually, as the prototype
({'pvfn':'levelsensactmatrixblockpvs','uc':'EUL2OSEM','cc':'e2o','key':"'osemConfig','eul2osem'"},lmFullSet),
({'pvfn':'','uc':'','cc':'','key':"''"},[]) # DUMMY entry to occupy the last place in the list and reduce editing errors
]
for subs, methods in lmMethodsToGenerate:
    for method in methods:
        exec('defcommandstring = lm'+method) # add 'lm' to the name of the generic method to get the name of the command string for it defined above
        exec(defcommandstring%subs) # define the 
        attachcommandstring = "Vis.%(cc)s"+method+" = _lm_%(cc)s"+method # command string to attach a function as a Vis method and with its final, visible name
        exec(attachcommandstring%subs) # attach the function as a Vis method 
        if method in ['Pvs']: 
            callableLevelMatrixNameCommandsAuto.add("%(cc)s"%subs+method)
            
        if method in ['Read','WriteDefaults']: 
            callableLevelMatrixReadCommandsAuto.add("%(cc)s"%subs+method)

        if method in ['WriteValue','WriteArray']: 
            callableLevelMatrixWriteCommandsAuto.add("%(cc)s"%subs+method)
            
# --------------------------------------------------------------------------------------
# Stuff for command line use

# Function to convert a Python result into a Matlab-friendly string. 
def toMatlab(thing, separator=' '):
    """Building block to convert a Python result into something approximating Matlab format.
    Lists and tuples are converted to cell arrays and booleans are converted to 0 or 1."""
    if thing==None:
        return 'None'
    if type(thing)==str:
        return repr(thing)
    elif type(thing)==int or type(thing)==float:
        return str(thing)
    elif type(thing)==bool:
        if thing: return '1'
        else: return '0'
    elif type(thing)==list or type(thing)==tuple:
        if len(thing)==0:
            return '{}'
        elif len(thing)==1:
            return '{'+toMatlab(thing[0])+'}'
        else:
            result = '{'
            for item in thing[0:-1]:
                 result += toMatlab(item)+separator
            return result+toMatlab(thing[-1])+'}'
    elif type(thing)==dict:
        return toMatlab(list(thing.items()))
    else:
        raise VisError('Object of unsupported type: '+str(thing))

# Functions to validate data

def checkHaveLongVal(value):
    try: float(value)
    except:
        raise VisError('Non-numeric value: '+value)

def converttoFM(value):
    """Building-block method to accept filter indices as plain numbers or 'FM1' format and return the latter."""
    if type(value)==int and 1<=value and value<=10:
        return 'FM'+str(value)
    elif value in ['FM1','FM2','FM3','FM4','FM5','FM6','FM7','FM8','FM9','FM10']:
        return value
    else:
        raise VisError('Non-recognized filter: '+str(value))

def fmtpair(pv,val, pair='value'):
    "Return requested combination of PV, value or both as tuple."
    if pair=='pv':
        return pv 
    elif pair=='value':
        return val
    elif pair=='both':
        return (pv,val)
    elif pair=='none':
        return None
    else:
        return pair

def fmtwd(pv,wd, pair='value'):
    "Return requested combination of PV, watchdog label (e.g., 'IOP'/'USER'/'M0') or both as tuple."
    if pair=='pv':
        return pv 
    elif pair=='value':
        return wd
    elif pair=='both':
        return (wd,pv)
    elif pair=='none':
        return None
    else:
        return pair

def fmtbio(pv,bio, pair='value'):
    "Return requested combination of PV, BIO label (e.g., 'IP'/'GAS'/'IMV'/'IMH'/'TM') or both as tuple."
    if pair=='pv':
        return pv 
    elif pair=='value':
        return bio
    elif pair=='both':
        return (bio,pv)
    elif pair=='none':
        return None
    else:
        return pair

def printifnotnone(v):
    """Building-block method to print a result only if not None."""
    if v!=None:
        print(v)

# -----------------------------------------------------------------------------------------------------
# Things that are allowed to be called from the command line

# Data functions and functions not associated with a particular level.
callableGlobals = {'visTypes','visData'}
callableVisCommands = {'levels','suspensionType'}
callableOpticSwitchWriteCommands = {'masterSwitchWrite','commSwitchWrite'}
callableOpticSwitchReadCommands = {'masterSwitchRead','commSwitchRead'}

# Commands associated with a particular level
callableLevelDataCommands = {'coilDriverData','magnetData','osemData'}

callableLevelFilterNameCommands = {
   'testPvs','dampPvs','dcctrlPvs','setPvs','olSetPvs','olDcctrlPvs','witPvs','lockPvs','alignPvs',
    'coilPvs','osemPvs','olSegPvs','olPvs',
    'osemNames','osemDofs','olNames','olDofs',
    'iscPvs','olDampPvs','noisePvs'
}.union(callableLevelFilterNameCommandsAuto)

callableLevelMatrixNameCommands = {'o2ePvs','o2eDefs','e2oPvs','e2oVals','ol2ePvs'}
callableLevelMatrixReadCommands = {'o2eRead','e2oRead'}
callableLevelMatrixWriteCommands = {'o2eWriteDefaults','o2eWriteValue','o2eWriteArray','e2oWriteDefaults','e2oWriteValue','e2oWriteArray'}

callableLevelFilterReadCommands = {'dampInmonRead', 'dampOutmonRead', 'dampOutputRead','dampOffsetRead','dampLimitRead', 'dampRampRead', 'alignOffsetSwitchRead','olDcctrlInputSwitchRead','alignOffsetRead', 'olDcctrlGainRead','olSetGainRead','olSetInputSwitchRead','iscOutputSwitchWrite'}.union(callableLevelFilterReadCommandsAuto)

callableLevelFilterWriteCommands = {
    'dampRampWrite','dampOffsetWrite','dampGainWrite', 'dampLimitWrite',
    'dcctrlRampWrite','dcctrlOffsetWrite','dcctrlGainWrite',
    'setRampWrite','setOffsetWrite','setGainWrite',
    'olSetRampWrite','olSetOffsetWrite','olSetGainWrite',
    'olDcctrlRampWrite','olDcctrlOffsetWrite','olDcctrlGainWrite',
#    'testRampWrite','testOffsetWrite','testGainWrite',
    'lockRampWrite','lockOffsetWrite','lockGainWrite',
    'alignRampWrite','alignOffsetWrite','alignGainWrite',
    'osemRampWrite','osemOffsetWrite','osemGainWrite',
    'coilRampWrite','coilOffsetWrite','coilGainWrite'
}.union(callableLevelFilterWriteCommandsAuto)

callableLevelFilterSwitchReadCommands = {
    'dampInputSwitchRead','dampOutputSwitchRead','dampOffsetSwitchRead',  'dampHoldSwitchRead', 'dampLimitSwitchRead','dampOffsetRampingRead','dampGainRampingRead','dampRampingRead',
    'dcctrlInputSwitchRead','dcctrlOutputSwitchRead','dcctrlOffsetRampingRead','dcctrlGainRampingRead','dcctrlRampingRead',
    'setInputSwitchRead','setOutputSwitchRead','setOffsetRampingRead','setGainRampingRead','setRampingRead',
    'olSetInputSwitchRead','olSetOutputSwitchRead','olSetOffsetRampingRead','olSetGainRampingRead','olSetRampingRead',
    'olDcctrlInputSwitchRead','olDcctrlOutputSwitchRead','olDcctrlOffsetRampingRead','olDcctrlGainRampingRead','olDcctrlRampingRead',
#    'testInputSwitchRead','testOutputSwitchRead','testOffsetRampingRead','testGainRampingRead','testRampingRead',
    'lockInputSwitchRead','lockOutputSwitchRead','lockOffsetRampingRead','lockGainRampingRead','lockRampingRead',
    'alignInputSwitchRead','alignOutputSwitchRead','alignOffsetRampingRead','alignGainRampingRead','alignRampingRead',
    'osemOutputSwitchRead','coilOutputSwitchRead',
    'dampInputSwitchRead','dcctrlInputSwitchRead','setInputSwitchRead',
    'testInputSwitchRead','lockInputSwitchRead','alignInputSwitchRead',
    'osemInputSwitchRead','coilInputSwitchRead',
    'dampGainRead','dampGainRampingRead','dampRampingRead',
    'dcctrlGainRead','dcctrlGainRampingRead','dcctrlRampingRead',
    'setGainRead','setGainRampingRead','setRampingRead',
    'testGainRead','testGainRampingRead',
    'lockGainRead','lockGainRampingRead',
    'alignGainRead','alignGainRampingRead',
    'osemGainRead',
    'coilGainRead'
}.union(callableLevelFilterSwitchReadCommandsAuto)

callableLevelFilterSwitchWriteCommands = {
    'dampOutputSwitchWrite','dampInputSwitchWrite','dampOffsetSwitchWrite','dampHoldSwitchWrite', 'dampLimitSwitchWrite'
}.union(callableLevelFilterSwitchWriteCommandsAuto)

callableLevelFilterPressButtonCommands = {
    'dampPressButton'
}.union(callableLevelFilterPressButtonCommandsAuto)

callableLevelFilterModuleEnableReadCommands = {
    'dampFilterModuleEnableRead'
}.union(callableLevelFilterModuleEnableReadCommandsAuto)

callableLevelFilterModuleEnableWriteCommands = {
    'dampFilterModuleEnableWrite','dcctrlFilterModuleEnableWrite','setFilterModuleEnableWrite',
    'olSetFilterModuleEnableWrite','olDcctrlFilterModuleEnableWrite',
    'testFilterModuleEnableWrite','lockFilterModuleEnableWrite','alignFilterModuleEnableWrite',
    'coilFilterModuleEnableWrite','osemFilterModuleEnableWrite'
}.union(callableLevelFilterModuleEnableWriteCommandsAuto)

callableLevelFilterOutputReadCommands = {'olRead','olSegRead'} # ??? Forgotten what this does

allCallables = (
    callableGlobals|callableVisCommands|callableLevelDataCommands
    |callableOpticSwitchWriteCommands|callableOpticSwitchReadCommands
    |callableLevelMatrixNameCommands|callableLevelMatrixWriteCommands
    |callableLevelFilterNameCommands
    |callableLevelFilterReadCommands|callableLevelFilterWriteCommands
    |callableLevelFilterSwitchReadCommands|callableLevelFilterSwitchWriteCommands
    |callableLevelFilterModuleEnableReadCommands|callableLevelFilterModuleEnableWriteCommands
)

nonCallables = {'__module__', '__doc__', '__init__','__dict__', '__weakref__','switch','write','writelist','read','readlist','fmtprefix',
'levelchannames','levelsensactdata','levelmatrixblockpvs','levelmatrixblockdefs',
'levelmatrixblockread','levelmatrixblockwrite','levelsensactmatrixblockpvs',
'levelsensactmatrixblockdefs','levelsensactmatrixblockread','levelsensactmatrixblockwrite',
'levelsensactfilterblockpvs','levelsensactfilterblockdefs','levelfilterblockpvs',
'witPvs','genNumWrite','genNumRead','genSwitchWrite','genSwitchRead',
'genFilterModuleEnableWrite','waitForRampingToKickIn'}

callablesDefinedBelow = {'visTypes', 'visData'}

# FIXME - add the following to a suitable list:
nonCallablesFixMeLater = {
'olDampRead', 'ditherRead', 'iscGainWrite', 'witRead', 'ditherPvs', 'testOffsetRead', 'wdNames', 'e2oDefs', 'iscRampWrite',  'o2eRead', 'trippedWds','bioWdPvs','trippedBioWds', 'e2oRead', 'olRead', 'olSegRead'}

usage = """%(prog)s [command] [options]
The -x and -X switches allow arbitrary Python code to be executed before or after the main command.
The -o switch is required for all optic-specific commands.
The -l, -c, -f and -a switches accept multiple arguments, e.g., -l M0 R0.
Commands: """+str(allCallables)

# A main() function which will parse the command line arguments 
def main():
    import argparse
    prog = os.path.basename(sys.argv[0])
    
    parser = argparse.ArgumentParser(prog=prog,usage=usage)
    parser.add_argument('command', action='store', default='', type=str, nargs= '?', help='Command')
    parser.add_argument('-o', '--optic', dest='optic', action='store', default='', type=str, help='Optic')
    parser.add_argument('-i', '--ifo', dest='ifo', action='store', default=os.environ['IFO'], type=str, help='IFO (default local)')
    parser.add_argument('-l', '--level', dest='levels', metavar='LEVEL', action='store', default=[], type=str, nargs='*', help='Level (IP/F0/etc; default all)')
    parser.add_argument('-c', '--chan', '--inchans', dest='chans', metavar="CHAN",action='store', default=[], type=str, nargs='*', help='Channels/DOFs (F1/F2/F3/etc, L/T/V/etc; default all)')
    parser.add_argument('-C', '--outchans', dest='ochans', metavar="CHAN",action='store', default=[], type=str, nargs='*', help='Output channels/DOFs (F1/F2/F3/etc, L/T/V/etc; default all) for commands that work with arrays')
    parser.add_argument('-f', '--filter', dest='filters', metavar='FM#', action='store', default=[], type=str, nargs='*', help='Filters (1/2/.../10; default none)')
    parser.add_argument('-k', '--key', dest='key', metavar='KEYLIST', action='store', default=[], type=str, nargs='*', help='List of dictionary keys (for data lookup)')
    parser.set_defaults(enable='NC')
    parser.add_argument('-e', '--true', '--enable', '--on', dest='enable', action='store_const', const = 'ON',  help='On (for switch commands)')
    parser.add_argument('-d', '--false', '--disable', '--off', dest='enable', action='store_const', const = 'OFF', help='Off (for switch commands)')
    parser.add_argument('-n', '--nochange', dest='enable', action='store_const', const = 'NC', help='No change (for switch commands)')
    parser.add_argument('-v', '--value', dest='value', metavar='VAL', action='store', default=0, type=float, help='Numeric value (for setting commands)')
    parser.add_argument('-a', '--array', dest='array', metavar='VAL', action='store', default=[], type=float, nargs='*',help='Numeric array (for setting commands)')
    parser.add_argument('--verbose', dest='verbose', action='store_const', const = True, default=False, help='Turns on -t and additional debugging output')
    parser.set_defaults(pair='value')
    parser.add_argument('-p', '--pair', dest='pair', metavar='pv/value/tuple', action='store', default='', type=str,  help='Whether read/write commands return PV, value (default), or (PV,value) tuple')
    parser.set_defaults(withprefix='full')
    parser.add_argument('-b','--bare', dest='withprefix', action='store_const', const = 'bare', help="With commands that return PV lists, omit the 'K1:VIS-ITMX_' or similar prefix")
    parser.add_argument('-B','--halfbare', dest='withprefix', action='store_const', const = 'halfbare', help="With commands that return PV lists, omit the 'K1:VIS-' or similar prefix")
    parser.add_argument('-m','--matlab', dest='matlab', action='store_const', const = True, default=False, help="With commands that return lists, format as a Matlab cell array of strings")
    parser.add_argument('-s','--suffix', dest='suffix', action='store', default='', type=str, help="With commands that return PV lists, add a suffix. e.g., _EXC, to all PVs")
    parser.add_argument('-x','--executebefore', dest='bcode', metavar='PYTHONCODE', action='store', default=[], type=str, nargs='*', help='Execute the code before the main command')
    parser.add_argument('-X','--executeafter', dest='acode', metavar='PYTHONCODE', action='store', default=[], type=str, nargs='*', help='Execute the code after the main command')
    parser.add_argument('-z', '--dorw', dest='dorw', action='store_const', const = 1, default=2,  help='Disable output for write commands')
    parser.add_argument('-Z', '--ZZZ', dest='dorw', action='store_const', const = 0, default=2,  help='Disable output for read/write commands')
    options = parser.parse_args()
#    print options
#    print '----'

    if options.bcode=='' and options.command=='' and options.acode=='':
        raise VisError('Nothing to execute: no command and no -x or -X - see -h for help')

    optic=None
    opticname=options.optic.upper()
    ifoname=options.ifo.upper()
    fullname = ifoname+':'+opticname
    if opticname!='':
        if (ifoname,opticname) not in visTypes:
            raise VisError('Unrecognized optic: '+fullname)
        optic = Vis(opticname)
        if options.verbose: print('Optic: '+optic.name)

    if options.bcode!='':
        if options.bcode:
            bcode = ''
            for word in options.bcode:
                bcode += word+' '
            print('Before code: '+bcode)
            exec(bcode)

    if options.command=='':
        pass

    elif options.command in callableGlobals:
        keywords = ''
        for keyword in options.key:
            keywords += '['+repr(eval(keyword))+']'
        if options.matlab:
            cmd = 'result = toMatlab('+options.command+')'+keywords+'; print result'
        else:
            cmd = 'result = '+options.command+keywords+'; print result'
        if options.verbose: print(cmd)
        exec(cmd)

    else: # all remaining command types require an optic
        if optic==None:
            raise VisError('Optic not specified')

        if options.command in callableVisCommands: # e.g., visData
            cmd = 'result = optic.'+options.command+'('\
            +'verbose='+str(options.verbose)\
            +', matlab='+str(options.matlab)\
            +'); print(result)'
            if options.verbose: print(cmd)
            exec(cmd)

        elif options.command in callableOpticSwitchReadCommands: # e.g., MasterSwitchRead
            if options.pair=='': options.pair='none'
            cmd = 'result = optic.'+options.command\
            +'(verbose='+str(options.verbose)\
            +', pair='+repr(options.pair)\
            +', withprefix='+repr(options.withprefix)\
            +', dorw='+str(options.dorw)\
           +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
 
        elif options.command in callableOpticSwitchWriteCommands: # e.g., MasterSwitchWrite
            if options.pair=='': options.pair='none'
            cmd = 'result = optic.'+options.command\
            +'(enable="'+options.enable+'"'\
            +', verbose='+str(options.verbose)\
            +', pair='+repr(options.pair)\
            +', withprefix='+repr(options.withprefix)\
            +', dorw='+str(options.dorw)\
           +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
 
        elif options.command in callableLevelMatrixNameCommands: # e.g., o2ePvs
            cmd = 'result = optic.'+options.command+'('\
            +'levels='+str(options.levels)\
            +', ichans='+str(options.chans)\
            +', ochans='+str(options.ochans)\
            +', verbose='+str(options.verbose)\
            +', matlab='+str(options.matlab)\
            +', withprefix='+repr(options.withprefix)\
            +'); print(result)'
            if options.verbose: print(cmd)
            exec(cmd)

        elif options.command in callableLevelMatrixReadCommands: # e.g., o2eRead
            if options.pair=='': options.pair='value'
            cmd = 'result = optic.'+options.command+'('\
            +'levels='+str(options.levels)\
            +', ichans='+str(options.chans)\
            +', ochans='+str(options.ochans)\
            +', verbose='+str(options.verbose)\
            +', matlab='+str(options.matlab)\
            +', dorw='+str(options.dorw)\
            +', pair='+repr(options.pair)
            +', withprefix='+repr(options.withprefix)\
            +'); print(result)'
            if options.verbose: print(cmd)
            exec(cmd)

        elif options.command in callableLevelMatrixWriteCommands: # e.g., o2eWrite
            if options.pair=='': options.pair='none'
            cmd = 'result = optic.'+options.command+'('\
            +'value='+str(options.value)\
            +', array='+str(options.array)\
            +', levels='+str(options.levels)\
            +', ichans='+str(options.chans)\
            +', ochans='+str(options.ochans)\
            +', verbose='+str(options.verbose)\
            +', matlab='+str(options.matlab)\
            +', dorw='+str(options.dorw)\
            +', pair='+repr(options.pair)\
            +', withprefix='+repr(options.withprefix)\
            +'); print(result)'
            if options.verbose: print(cmd)
            exec(cmd)

        elif options.command in callableLevelDataCommands: # ???
            cmd = 'result = optic.'+options.command+'('\
            +str(options.key)\
            +', levels='+str(options.levels)\
            +', verbose='+str(options.verbose)\
            +', matlab='+str(options.matlab)\
            +'); print(result)'
            if options.verbose: print(cmd)
            exec(cmd)

        elif options.command in callableLevelFilterNameCommands: # e.g., dampPvs
            cmd = 'result = optic.'+options.command+'('\
            +'levels='+str(options.levels)\
            +', chans='+str(options.chans)\
            +', verbose='+str(options.verbose)\
            +', suffix="'+str(options.suffix)+'"'\
            +', matlab='+str(options.matlab)\
            +', withprefix='+repr(options.withprefix)\
            +'); print(result)'
            if options.verbose: print(cmd)
            exec(cmd)

        elif options.command in callableLevelFilterReadCommands: # e.g., dampOutmonRead, dampOffsetRead
            if options.pair=='': options.pair='none'
            cmd = 'result = optic.'+options.command+'('\
            +'levels='+str(options.levels)\
            +', chans='+str(options.chans)\
            +', verbose='+str(options.verbose)\
            +', pair='+repr(options.pair)\
            +', withprefix='+repr(options.withprefix)\
            +', dorw='+str(options.dorw)\
            +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
  
        elif options.command in callableLevelFilterWriteCommands: # e.g., dampOffsetWrite
            if options.pair=='': options.pair='none'
            cmd = 'result = optic.'+options.command+'('\
            +'value='+str(options.array if options.array!=[] else options.value)\
            +', levels='+str(options.levels)\
            +', chans='+str(options.chans)\
            +', verbose='+str(options.verbose)\
            +', pair='+repr(options.pair)\
            +', withprefix='+repr(options.withprefix)\
            +', dorw='+str(options.dorw)\
            +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
    
        elif options.command in callableLevelFilterPressButtonCommands: # e.g., dampPressButton
            if options.pair=='': options.pair='none'
            cmd = 'result = optic.'+options.command+'('\
            +'"'+str(options.key[0])+'"'\
            +', levels='+str(options.levels)\
            +', chans='+str(options.chans)\
            +', verbose='+str(options.verbose)\
            +', pair='+repr(options.pair)\
            +', withprefix='+repr(options.withprefix)\
            +', dorw='+str(options.dorw)\
            +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
  
        elif options.command in callableLevelFilterSwitchReadCommands: # e.g., dampOutputSwitchRead
            if options.pair=='': options.pair='value'
            cmd = 'result = optic.'+options.command+'('\
            +'levels='+str(options.levels)\
            +', chans='+str(options.chans)\
            +', verbose='+str(options.verbose)\
            +', pair="'+str(options.pair)+'"'\
            +', matlab='+str(options.matlab)\
            +', dorw='+str(options.dorw)\
            +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
 
        elif options.command in callableLevelFilterSwitchWriteCommands:  # e.g., dampOutputSwitchWrite
            if options.pair=='': options.pair='value'
            cmd = 'result = optic.'+options.command+'('\
            +"'"+str(options.enable)+"'"\
            +', levels='+str(options.levels)\
            +', chans='+str(options.chans)\
            +', verbose='+str(options.verbose)\
            +', pair="'+str(options.pair)+'"'\
            +', matlab='+str(options.matlab)\
            +', dorw='+str(options.dorw)\
            +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
 
        # FIXME - debug
        elif options.command in callableLevelFilterModuleEnableReadCommands:
            if options.pair=='': options.pair='none'
            cmd = 'result = optic.'+options.command+'('\
            +'filters='+repr(options.filters)\
            +', levels='+str(options.levels)\
            +', chans='+str(options.chans)\
            +', verbose='+str(options.verbose)\
            +', pair='+repr(options.pair)\
            +', withprefix='+repr(options.withprefix)\
            +', dorw='+str(options.dorw)\
            +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
 
        elif options.command in callableLevelFilterModuleEnableWriteCommands:
            if options.pair=='': options.pair='none'
            cmd = 'result = optic.'+options.command+'('\
            +"'"+str(options.enable)+"'"\
            +', filters='+repr(options.filters)\
            +', levels='+str(options.levels)\
            +', chans='+str(options.chans)\
            +', verbose='+str(options.verbose)\
            +', pair='+repr(options.pair)\
            +', withprefix='+repr(options.withprefix)\
            +', dorw='+str(options.dorw)\
            +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
 
        else:
            raise VisError('Unrecognized variable/function/command: '+options.command)

    if options.acode!='':
        if options.acode:
            acode = ''
            for word in options.acode:
                acode += word+' '
            print('After code: '+acode)
            exec(acode)

# --------------------------------------------------------------------------------------
# Data section

# Random EPICS stuff
# Bit mask combos for reading back cdsFilt block settings via _SW1R and _SW2R from T080135 (or _SWSTAT from T1300494)
cdsFiltMask = {
    'INPUT' : {'swnrsuffix':'_SW1R','swnrmask':4,'swstatmask':1024},
    'OFFSET' : {'swnrsuffix':'_SW1R','swnrmask':8,'swstatmask':2048},
    'FM1' : {'swnrsuffix':'_SW1R','swnrmask':16,'swstatmask':1},     'FM1S' : {'swnrsuffix':'_SW1R','swnrmask':32}, # R=request; S=actual state
    'FM2' : {'swnrsuffix':'_SW1R','swnrmask':64,'swstatmask':2},     'FM2S' : {'swnrsuffix':'_SW1R','swnrmask':128},
    'FM3' : {'swnrsuffix':'_SW1R','swnrmask':256,'swstatmask':4},    'FM3S' : {'swnrsuffix':'_SW1R','swnrmask':512},
    'FM4' : {'swnrsuffix':'_SW1R','swnrmask':1024,'swstatmask':8},   'FM4S' : {'swnrsuffix':'_SW1R','swnrmask':2048},
    'FM5' : {'swnrsuffix':'_SW1R','swnrmask':4096,'swstatmask':16},  'FM5S' : {'swnrsuffix':'_SW1R','swnrmask':8192},
    'FM6' : {'swnrsuffix':'_SW1R','swnrmask':16384,'swstatmask':32}, 'FM6S' : {'swnrsuffix':'_SW1R','swnrmask':32768},
    'FM7' : {'swnrsuffix':'_SW2R','swnrmask':1,'swstatmask':64},     'FM7S' : {'swnrsuffix':'_SW2R','swnrmask':2},
    'FM8' : {'swnrsuffix':'_SW2R','swnrmask':4,'swstatmask':128},    'FM8S' : {'swnrsuffix':'_SW2R','swnrmask':8},
    'FM9' : {'swnrsuffix':'_SW2R','swnrmask':16,'swstatmask':256},   'FM9S' : {'swnrsuffix':'_SW2R','swnrmask':32},
    'FM10' : {'swnrsuffix':'_SW2R','swnrmask':64,'swstatmask':512},  'FM10S' : {'swnrsuffix':'_SW2R','swnrmask':128},
    'LIMIT' : {'swnrsuffix':'_SW2R','swnrmask':256,'swstatmask':8192},
    'DECIMATION' : {'swnrsuffix':'_SW2R','swnrmask':512},
    'OUTPUT' : {'swnrsuffix':'_SW2R','swnrmask':1024,'swstatmask':4096},
    'HOLD' : {'swnrsuffix':'_SW2R','swnrmask':2048},
    'GRAMP' : {'swnrsuffix':'_SW2R','swnrmask':4096},
    'ORAMP' : {'swnrsuffix':'_SW2R','swnrmask':8192} # GRAMP or ORAMP
}

# -------------------------------------------------------------------------------------------------
# Watchdog definitions for use in visTypes below
typeawd = {
    'IOP':'DACKILL','IP':'IP_WDMON',
    'F0':'F0_WDMON','F1':'F1_WDMON','F2':'F2_WDMON','F3':'F3_WDMON',
    'BF':'BF_WDMON',
    'MN':'IM_WDMON','IM':'IM_WDMON','TM':'TM_WDMON'
}
typebwd = {
    'TWR':'TWR_DACKILL','PAY':'PAY_DACKILL','IP':'IP_WDMON',
    'F0':'F0_WDMON','F1':'F1_WDMON','BF':'BF_WDMON',
    'IM':'IM_WDMON','TM':'TM_WDMON'
}
typebpwd = {
    'IOP':'DACKILL','SF':'SF_WDMON','BF':'BF_WDMON',
    'IM':'IM_WDMON','TM':'TM_WDMON'
} 
 
typecwd = {'USER':'DACKILL','TM':'TM_WDMON'} 

# -------------------------------------------------------------------------------------------------
# Watchdog definitions for use in visTypes below
typeabio = {
    'PI':'BIO_PI_MON','GAS':'BIO_GAS_MON',
    'BFV':'BIO_BFV_MON','BFH':'BIO_BFH_MON',
    'MNH':'BIO_MNH_MON','MNIMV':'BIO_MNIMV_MON',
    'IMH':'BIO_IMH_MON','IMB':'BIO_IMB_MON',
    'TM':'BIO_TM_MON'
}
typebbio = {
    'GAS':'BIO_GAS_MON','IP':'BIO_IP_MON',
    'IMV':'BIO_IMV_MON',
#    'IMH':'BIO_IMH_MON', # the modified LPCD generates spurious trip signals, so we ignore it
    'TM':'BIO_TM_MON'
}
typebpbio = {
    'GAS':'BIO_GAS_MON',
    'BFV':'BIO_BFV_MON','BFH':'BIO_BFH_MON',
    'IM1':'BIO_IM1_MON','IM2':'BIO_IM2_MON','TM':'BIO_TM_MON'
}
typecbio = {'TM':'TM_MON'} 

# -----------------------------------------------------------------------------------------
# Standard info
# Lists of input and/or output names
typebIMlevelOsemNames = ['V1','V2','V3','H1','H2','H3']
typebTMlevelOsemNames = ['H1','H2','H3','H4']
typebpIMlevelOsemNames = ['V1','V2','V3','H1','H2','H3']
typebpTMlevelOsemNames = ['H1','H2','H3','H4']
typecM1levelOsemNames = ['V1','V2','V3','H1','H2','H3']
typecTMlevelOsemNames = ['H1','H2','H3','H4']
genericlevelOsemNames = ['UL','LL','UR','LR']
olSegNames = ['SEG1','SEG2','SEG3','SEG4']

# Lists of DOF names used in filter banks
sixDofNames = ['L','T','V','R','P','Y']
threeDofNames = ['L','P','Y']
threeDofNamesH = ['L','T','Y']
threeDofMonNames = ['LMON','PMON','YMON']
olDofNames = ['P','Y','SUM']
olFullDofNames = ['PIT','YAW','SUM']
olDampDofNames = ['P','Y']
olCtrlDofNames = ['P','Y']
ditherDofNames = ['P','Y']
alignDofNames = ['P','Y']

# Shadow sensor stuff
kosem = {'type':'KOSEM','imax':95.0, 'sensitivity': 1/0.7, 'coilturns' : 800, 'coillen' : 0.315*25.4, 'coilrad1' : 0.35*25.4, 'coilrad2' : 0.65*25.4}  # FIXME
bosem = {'type':'BOSEM','imax':95.0, 'sensitivity': 1/0.7, 'coilturns' : 800, 'coillen' : 0.315*25.4, 'coilrad1' : 0.35*25.4, 'coilrad2' : 0.65*25.4}  # T1000164-v3
aosem = {'type':'AOSEM','imax':95.0, 'sensitivity': 1/0.7, 'coilturns' : 400, 'coillen' : 0.16*25.4, 'coilrad1' : 0.304*25.4, 'coilrad2' : 0.498*25.4} # T1000164-v3

# OSEM readback # FIXME finish this section
stdosemrdbck = { 
    'osem':76.29/0.7, # uA/mm
    'white':[('zpk',[0.4],[10,1000],'1','n')],
    'aa':[('zpk',[],[],1,'n')], # FIXME fill in exact hardware AA filter
    'iop':[('zpk',[],[],1,'n')], # FIXME fill in exact software IOP downsampling filter
    'adc':2**16/40
}

# Identity matrices
i6 = [[1.,0.,0.,0.,0.,0.],[0.,1.,0.,0.,0.,0.],[0.,0.,1.,0.,0.,0.],[0.,0.,0.,1.,0.,0.],[0.,0.,0.,0.,1.,0.],[0.,0.,0.,0.,0.,1.]]
i3 = [[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]

# Magnet signs
signsIM = [1,-1,1,-1,1,-1] # FIXME
signsM1 = [1,-1,1,-1,1,-1] # FIXME
signsTM = [1,-1,-1,1] # FIXME
signsM0 = [1,-1,1,-1,1,-1] # E1000617-v5
signsR0 = [1,1,-1,1,-1,-1] # E1000617-v5
signsM1HAM = [-1,-1,1,1,-1,-1] # E1100109-v2
signsM1HAM2 = [-1,-1,1,1,-1,1] # E1100109-v2, but with SD OSEM on opposite end as for HLTS (PR3 and SR3), SRM and PRM
signs4B = [-1,1,1,-1] # standard UL/LL/UR/LR array for BOSEMs # E1000617-v5 (QUAD), E1100108-v3 (BSFM),
signs4A = [1,-1,-1,1] # standard UL/LL/UR/LR array for AOSEMs

# Standard filter bank definitions
damp6 = {'blockname':'DAMP', 'names':'dofs','default':{'gains':[-1.,-1.,-1.,-1.,-1.,-1.]}}
damp3 = {'blockname':'DAMP', 'names':'dofs','default':{'gains':[-1.,-1.,-1.]}}
idamp3 = {'blockname':'IDAMP', 'names':'dofs','default':{'gains':[-1.,-1.,-1.]}}
damp1 = {'blockname':'DAMP', 'names':'dofs','default':{'gains':[1.]}}
damptm = {'blockname':'DAMP', 'names':'dofs','default':{'gains':[1.]}}
dcctrl6 = {'blockname':'DCCTRL', 'names':'dofs','default':{'gains':[-1.,-1.,-1.,-1.,-1.,-1.]}}
dcctrl3 = {'blockname':'DCCTRL', 'names':'dofs','default':{'gains':[-1.,-1.,-1.,-1.,-1.,-1.]}}
dcctrl1 = {'blockname':'DCCTRL', 'names':'dofs','default':{'gains':[1.]}}
dcctrlol = {'blockname':'OLDCCTRL', 'names':'oldofs','default':{'gains':[1.]}}
set6 = {'blockname':'SET', 'names':'dofs','default':{'gains':[-1.,-1.,-1.,-1.,-1.,-1.]}}
set3 = {'blockname':'SET', 'names':'dofs','default':{'gains':[-1.,-1.,-1.,-1.,-1.,-1.]}}
set1 = {'blockname':'SET', 'names':'dofs','default':{'gains':[1.]}}
setol = {'blockname':'SET', 'names':'oldofs','default':{'gains':[1.]}}
test6 = {'blockname':'TEST', 'names':'dofs','default':{'gains':[1.,1.,1.,1.,1.,1.]}}
test3 = {'blockname':'TEST', 'names':'dofs','default':{'gains':[1.,1.,1.]}}
test1 = {'blockname':'TEST', 'names':'dofs','default':{'gains':[1.]}}
isc6 = {'blockname':'ISCINF', 'names':'iscdofs'}
isc3 = {'blockname':'ISCINF', 'names':'iscdofs'}
witIP = {'blockname':'DAMP', 'names':'dofs','suffix':'witsuffix'}
witGAS = {'blockname':'LVDTINF', 'names':'dofs','suffix':'witsuffix'}
witIM = {'blockname':'DAMP', 'names':'dofs','suffix':'witsuffix'}
witTM = {'blockname':'OPLEV', 'names':'witdofs','suffix':'witsuffix'}
lock3top = {'blockname':'LOCK', 'names':'lockdofs'}
lock3 = {'blockname':'LOCK', 'names':'dofs'}

# Standard matrix block definitions
sa6 = {'blockname':'SENSALIGN', 'inames':'dofs',  'onames':'dofs',  'default':i6}
sa3 = {'blockname':'SENSALIGN', 'inames':'dofs',  'onames':'dofs',  'default':i3}

# Driver types - Jeff K's names, plus strengths in mA/V

lpcd = {'name':'LPCD', 'strength':9.9} # FIXME (strength)

# -----------------------------------------------------------------------------------------
# Lever arm info
# QUAD
# FIXME (all this section)
typebp_im_dF2toF3      = 0.24;  # [m]
typebp_im_dLFtoRT      = 0.36;  # [m]
typebp_im_dLTPlanetoF1 = 0.078; # [m]

typebp_tm_dLFtoRT      = 0.13;  # [m] 
typebp_tm_dTPtoBM      = 0.13;  # [m] 

typec_m1_dF2toF3      = 0.24;  # [m]
typec_m1_dLFtoRT      = 0.36;  # [m]
typec_m1_dLTPlanetoF1 = 0.078; # [m]

typec_tm_dLFtoRT      = 0.13;  # [m] 
typec_tm_dTPtoBM      = 0.13;  # [m] 

# FIXME (all this section)
#    V1    V2    V3    H1   H2   H3
typebp_o2e_im = [
    [0.0, -0.5, -0.5, 0.0, 0.0, 0.0],              # L
    [0.0, 0.0, 0.0, 0.0, 0.0, -1.0],               # T
    [0.0, 0.0, 0.0, -0.5, -0.5, 0.0],              # V
    [0.0, 0.0, 0.0]+[x/typebp_im_dLFtoRT for x in [-1.0, 1.0, 0.0]],       # R
    [x/typebp_im_dLTPlanetoF1 for x in [-1.0, 0.5, 0.5]]+[0.0, 0.0, 0.0],  # P
    [x/typebp_im_dF2toF3 for x in [0.0, 1.0, -1.0]]+[0.0, 0.0, 0.0]      # Y
];  
typec_o2e_m1  = [
    [0.0, -0.5, -0.5, 0.0, 0.0, 0.0],              # L
    [0.0, 0.0, 0.0, 0.0, 0.0, -1.0],               # T
    [0.0, 0.0, 0.0, -0.5, -0.5, 0.0],              # V
    [0.0, 0.0, 0.0]+[x/typec_m1_dLFtoRT for x in [-1.0, 1.0, 0.0]],       # R
    [x/typec_m1_dLTPlanetoF1 for x in [-1.0, 0.5, 0.5]]+[0.0, 0.0, 0.0],  # P
    [x/typec_m1_dF2toF3 for x in [0.0, 1.0, -1.0]]+[0.0, 0.0, 0.0]      # Y
];
           
# FIXME (all this section) 
#   UL    LL    UR    LR
typebp_o2e_tm = [
    [0.25, 0.25, 0.25, 0.25],                # L
    [x/typebp_tm_dTPtoBM for x in [0.50, -0.50, 0.50, -0.50]],  # P
    [x/typebp_tm_dLFtoRT for x in [-0.50, -0.50, 0.50, 0.50]] # Y
]
               
typec_o2e_tm = [
    [0.25, 0.25, 0.25, 0.25],                # L
    [x/typec_tm_dTPtoBM for x in [0.50, -0.50, 0.50, -0.50]],  # P
    [x/typec_tm_dLFtoRT for x in [-0.50, -0.50, 0.50, 0.50]] # Y
]
               
# -------------------------------------------------------------------------------------------------
# -------------------------------------------------------------------------------------------------
# Lists of specific suspensions by type
visTypes = {
    ('K1','EX') : {'type': 'TYPEA', 'watchdogs': typeawd, 'bio' : typeabio},
    ('K1','EY') : {'type': 'TYPEA', 'watchdogs': typeawd, 'bio' : typeabio},
    ('K1','IX') : {'type': 'TYPEA', 'watchdogs': typeawd, 'bio' : typeabio},
    ('K1','IY') : {'type': 'TYPEA', 'watchdogs': typeawd, 'bio' : typeabio},
    ('K1','BS') : {'type': 'TYPEB', 'watchdogs': typebwd, 'bio' : typebbio},
    ('K1','SR2') : {'type': 'TYPEB', 'watchdogs': typebwd, 'bio' : typebbio},
    ('K1','SR3') : {'type': 'TYPEB', 'watchdogs': typebwd, 'bio' : typebbio},
    ('K1','SRM') : {'type': 'TYPEB', 'watchdogs': typebwd, 'bio' : typebbio},
    ('K1','PR2') : {'type': 'TYPEBP', 'watchdogs': typebpwd, 'bio' : typebpbio},
    ('K1','PR3') : {'type': 'TYPEBP', 'watchdogs': typebpwd, 'bio' : typebpbio},
    ('K1','PRM') : {'type': 'TYPEBP', 'watchdogs': typebpwd, 'bio' : typebpbio},
    ('K1','MCE') : {'type': 'TYPEC', 'watchdogs': typecwd, 'bio' : typecbio},
    ('K1','MCI') : {'type': 'TYPEC', 'watchdogs': typecwd, 'bio' : typecbio},
    ('K1','MCO') : {'type': 'TYPEC', 'watchdogs': typecwd, 'bio' : typecbio}
}

typeas = [sus for (sus,data) in visTypes.items() if data['type']=='TYPEA']
typebs = [sus for (sus,data) in visTypes.items() if data['type']=='TYPEB']
typebps = [sus for (sus,data) in visTypes.items() if data['type']=='TYPEBP']
typecs = [sus for (sus,data) in visTypes.items() if data['type']=='TYPEC']
allsus = typeas+typebs+typebps+typecs

# -----------------------------------------------------------------------------------------
# Master dictionary of data for all suspension types
visData = {
    'TYPEA' : { #FIXME - needs total rewrite
        'reallyis' : 'TYPEA',
        'levelorder' : ['IP','F0','F1','F2','F3','BF','IM','TM'],
        'master' : 'MASTERSWITCH',
        'commissioning' : 'COMMISH_STATUS',
        'levels' : {
        }
    },
    # -------------
    'TYPEB' : {
        'reallyis' : 'TYPEB',
        'levelorder' : ['IP','F0','F1','BF','IM','TM'],
        'master' : 'MASTERSWITCH',
        'commissioning' : 'COMMISH_STATUS',
        'levels' : {
            'IP' : { # FIXME
                'dofs' : threeDofNamesH,
                'witsuffix' : '_INMON',
                'dampmodeinputs' : ['L','T','Y','IL','IT','IY'],
                'dampmodeoutputs' : ['L','T','Y'],
                'dampmode' : {'blockname':'DAMPMODE','inames':'dampmodeinputs', 'onames':'dampmodeoutputs', 
                    'default':[[1,0,0,0,0,0],[0,1,0,0,0,0],[0,0,1,0,0,0]]}, # each sublist represents an output
                'mbtestinputs' : ['A','B','C','D'], # test inputs
                'mbtestoutputs' : ['X','Y','Z'], # test outputs
                'mbtestmatrixblock' : {'blockname':'TESTMATRIXBLOCK','inames':'mbtestinputs', 'onames':'mbtestoutputs', 
                    'default':[[1,2,3,4],[5,6,7,8],[9,10,11,12]]}, # each sublist represents an output
                'mbtestsensact' : {
                    'mbtestsensactinputs' : ['A','B','C','D'],
                    'mbtestsensactoutputs' : ['X','Y','Z'],
                    'mbtestsensactmatrixblock' : {
                        'blockname':'TESTSENSACTMATRIXBLOCK', 
                        'inames':'mbtestsensactinputs', 'onames':'mbtestsensactoutputs', 
                        'default':[[1,2,3,4],[5,6,7,8],[9,10,11,12]]
                    }
                },
#                'osemConfig' : None,
                'oldamp' : None,
                'olset' : None,
                'oldcctrl' : None,
                'olConfig' : None,
                'gasConfig' : None,
                'isc' : None,
                'damp' : damp3,
                'idamp': idamp3,
                'dcctrl' : dcctrl3,
                'set' : set3,
                'wit' : witIP,
                'lockdofs' : None,
                'lock' : None,
                'test' : test3,
                'aligndofs' : None,
                'align' : None,
                'dither' : None,
                'watchdog' : 'watchdogs' # FIXME
            },
            'F0' : { # FIXME
                'dofs' : ['GAS'],
                'witsuffix' : '_OUTMON',
                'osemConfig' : None,
                'oldamp' : None,
                'olset' : None,
                'oldcctrl' : None,
                'olConfig' : None,
                'gasConfig' : {
                    'chans' : 'GAS',
                    'dofs' : 'GAS',
                    'inf' : {'blockname':'LVDTINF', 'names':'chans'},
                    'osem2eul' : None,
                    'sensalign' : None,
                    'drivealign' : None,
                    'eul2osem' : None,
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':{1,1,1}}}
                },
                'isc' : None,
                'damp' : damp1,
                'dcctrl' : dcctrl1,
                'set' : set1,
                'wit' : witGAS,
                'lockdofs' : None,
                'lock' : None,
                'test' : test1,
                'aligndofs' : None,
                'align' : None,
                'dither' : None,
                'watchdog' : 'watchdogs' # FIXME
            },
            'F1' : { # FIXME
                'dofs' : ['GAS'],
                'witsuffix' : '_OUTMON',
                'osemConfig' : None,
                'oldamp' : None,
                'olset' : None,
                'oldcctrl' : None,
                'olConfig' : None,
                'gasConfig' : {
                    'chans' : 'GAS',
                    'dofs' : 'GAS',
                    'inf' : {'blockname':'LVDTINF', 'names':'chans'},
                    'osem2eul' : None,
                    'sensalign' : None,
                    'drivealign' : None,
                    'eul2osem' : None,
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':{1,1,1}}}
                },
                'isc' : None,
                'damp' : damp1,
                'dcctrl' : dcctrl1,
                'set' : set1,
                'wit' : witGAS,
                'lockdofs' : None,
                'lock' : None,
                'test' : test1,
                'aligndofs' : None,
                'align' : None,
                'dither' : None,
                'watchdog' : 'watchdogs' # FIXME
            },
            'BF' : { # FIXME
                'dofs' : ['GAS'],
                'witsuffix' : '_OUTMON',
                'osemConfig' : None,
                'oldamp' : None,
                'oldcctrl' : None,
                'olset' : None,
                'olConfig' : None,
                'gasConfig' : {
                    'chans' : 'GAS',
                    'dofs' : 'GAS',
                    'inf' : {'blockname':'LVDTINF', 'names':'chans'},
                    'osem2eul' : None,
                    'sensalign' : None,
                    'drivealign' : None,
                    'eul2osem' : None,
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':{1,1,1}}}
                },
                'isc' : None,
                'damp' : damp1,
                'dcctrl' : dcctrl1,
                'set' : set1,
                'wit' : witGAS,
                'lockdofs' : None,
                'lock' : None,
                'test' : test1,
                'aligndofs' : None,
                'align' : None,
                'dither' : None,
                'watchdog' : 'watchdogs' # FIXME
            },
            'IM' : {
                'dofs' : sixDofNames,
                'witsuffix' : '_INMON',
                'osemConfig' : {
                    'chans' : typebpIMlevelOsemNames,
                    'dofs' : sixDofNames,
                    'osem' : kosem,
                    'magnet' : {'diameter':10,'length':10,'material':'NdFeB','force':1.694},
                    'driver' : lpcd,
                    'sensalign' : sa6,
                    'inf' : {'blockname':'OSEMINF', 'names':'chans'},
                    'noise' : {'blockname':'NOISEMON', 'names':'chans'},
                    'osem2eul' : {'blockname':'OSEM2EUL','inames':'chans', 'onames':'dofs', 'default':typebp_o2e_im},
                    'eul2osem' : {'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 'default':map(list,zip(*typebp_o2e_im))},
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':signsIM}}
                },
                'olctrldofs' : olCtrlDofNames,
                'oldamp' : None,
                'olset' : {'blockname':'OLSET', 'names':'olctrldofs'},
                'oldcctrl' : {'blockname':'OLDCCTRL', 'names':'olctrldofs'},
                'olConfig' : None,
                'gasConfig' : None,
                'isc' : None,
                'damp' : damp6,
                'dcctrl' : None,
                'set' : None,
                'wit' : witIM,
                'lockdofs' : threeDofNames,
                'lock' : lock3top,
                'test' : test6,
                'aligndofs' : alignDofNames,
                'align' : {'blockname':'OPTICALIGN', 'names':'aligndofs'},
                'ditherdofs' : ditherDofNames,
                'dither' : {'blockname':'DITHER', 'names':'ditherdofs'},
                'watchdog' : 'watchdogs'
            },
            'TM' : {
                'dofs' : threeDofNames,
                'witdofs' : ['LEN','PIT','YAW'],
                'witsuffix' : '_DIAGMON',
                'osemConfig' : {
                    'chans' : typebpTMlevelOsemNames,
                    'dofs' : threeDofNames,
                    'osem' : kosem,
                    'magnet' : {'diameter':10,'length':10,'material':'NdFeB','force':1.694}, # FIXME
                    'driver' : lpcd,
                    'sensalign' : sa3,
                    'inf' : {'blockname':'OSEMINF', 'names':'chans'},
                    'noise' : {'blockname':'NOISEMON', 'names':'chans'},
                    'osem2eul' : {'blockname':'OSEM2EUL','inames':'chans', 'onames':'dofs', 'default':typebp_o2e_tm},
                    'eul2osem' : {'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 'default':map(list,zip(*typebp_o2e_tm))},
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':signsTM}}
                },
                'oldampdofs' : olDampDofNames,
                'oldamp' : {'blockname':'OLDAMP', 'names':'oldampdofs'},
                'olset' : None,
                'oldcctrl' : None,
                'olConfig' : {
                    'chans' : olSegNames,
                    'dofs' : olDofNames,
                    'fulldofs' : olFullDofNames,
                    'inf' : {'blockname':'OPLEV', 'names':'chans'},
                    'noise' : {'blockname':'NOISEMON', 'names':'chans'},
                    'osem2eul' : {'blockname':'OPLEV_MTRX','inames':'chans', 'onames':'dofs', 'default':[[-1.,1.,1.,-1.],[-1,1.,-1.,1.],[1.,1.,1.,1.]]},
                    'full' : {'blockname':'OPLEV', 'names':'fulldofs'},
                    'sensalign' : sa3,
                    'drivealign' : None,
                    'eul2osem' : None,
                    'outf' : None
                },
                'gasConfig' : None,
                'iscdofs' : threeDofNames,
                'isc' : isc3,
                'damp' : damp3,
                'dcctrl' : None,
                'set' : None,
                'wit' : witTM,
                'lockdofs' : threeDofNames,
                'lock' : lock3top,
                'test' : test3,
                'align' : None,
                'ditherdofs' : ditherDofNames,
                'dither' : {'blockname':'DITHER', 'names':'ditherdofs'},
                'watchdog' : 'watchdogs'
            }
        }
    },
    # -------------
    'TYPEBP' : {
        'reallyis' : 'TYPEBP',
        'levelorder' : ['F1','BF','IM','TM'],
        'master' : 'MASTERSWITCH',
        'commissioning' : 'COMMISH_STATUS',
        'levels' : {
            'F1' : {
                'dofs' : ['GAS'],
                'osemConfig' : None,
                'oldamp' : None,
                'olConfig' : None,
                'gasConfig' : {
                    'chans' : 'GAS',
                    'dofs' : 'GAS',
                    'inf' : {'blockname':'LVDTINF', 'names':'chans'},
                    'osem2eul' : None,
                    'sensalign' : None,
                    'drivealign' : None,
                    'eul2osem' : None,
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':{1,1,1}}}
                },
                'isc' : None,
                'damp' : damp1,
                'wit' : None,
                'lockdofs' : None,
                'lock' : None,
                'test' : test1,
                'aligndofs' : None,
                'align' : None,
                'dither' : None,
                'watchdog' : 'watchdogs' # FIXME
            },
            'BF' : {
                'dofs' : ['GAS'],
                'osemConfig' : None,
                'oldamp' : None,
                'olConfig' : None,
                'gasConfig' : {
                    'chans' : 'GAS',
                    'dofs' : 'GAS',
                    'inf' : {'blockname':'LVDTINF', 'names':'chans'},
                    'osem2eul' : None,
                    'sensalign' : None,
                    'drivealign' : None,
                    'eul2osem' : None,
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':{1,1,1}}}
                },
                'isc' : None,
                'damp' : damp1,
                'wit' : None,
                'lockdofs' : None,
                'lock' : None,
                'test' : test1,
                'aligndofs' : None,
                'align' : None,
                'dither' : None,
                'watchdog' : 'watchdogs' # FIXME
            },
            'IM' : {
                'dofs' : sixDofNames,
                'osemConfig' : {
                    'chans' : typebpIMlevelOsemNames,
                    'dofs' : sixDofNames,
                    'osem' : kosem,
                    'magnet' : {'diameter':10,'length':10,'material':'NdFeB','force':1.694},
                    'driver' : lpcd,
                    'sensalign' : sa6,
                    'inf' : {'blockname':'OSEMINF', 'names':'chans'},
                    'noise' : {'blockname':'NOISEMON', 'names':'chans'},
                    'osem2eul' : {'blockname':'OSEM2EUL','inames':'chans', 'onames':'dofs', 'default':typebp_o2e_im},
                    'eul2osem' : {'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 'default':map(list,zip(*typebp_o2e_im))},
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':signsIM}}
                },
                'oldampdofs' : olDampDofNames,
                'oldamp' : {'blockname':'OLDAMP', 'names':'oldampdofs'},
                'olConfig' : None,
                'gasConfig' : None,
                'isc' : None,
                'damp' : damp6,
                'wit' : None,
                'lockdofs' : threeDofNames,
                'lock' : lock3top,
                'test' : test6,
                'aligndofs' : alignDofNames,
                'align' : {'blockname':'OPTICALIGN', 'names':'aligndofs'},
                'ditherdofs' : ditherDofNames,
                'dither' : {'blockname':'DITHER', 'names':'ditherdofs'},
                'watchdog' : 'watchdogs'
            },
            'TM' : {
                'dofs' : threeDofNames,
                'osemConfig' : {
                    'chans' : typebpTMlevelOsemNames,
                    'dofs' : threeDofNames,
                    'osem' : kosem,
                    'magnet' : {'diameter':10,'length':10,'material':'NdFeB','force':1.694}, # FIMXME
                    'driver' : lpcd,
                    'sensalign' : sa3,
                    'inf' : {'blockname':'OSEMINF', 'names':'chans'},
                    'noise' : {'blockname':'NOISEMON', 'names':'chans'},
                    'osem2eul' : {'blockname':'OSEM2EUL','inames':'chans', 'onames':'dofs', 'default':typebp_o2e_tm},
                    'eul2osem' : {'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 'default':map(list,zip(*typebp_o2e_tm))},
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':signsTM}}
                },
                'oldampdofs' : olDampDofNames,
                'oldamp' : {'blockname':'OLDAMP', 'names':'oldampdofs'},
                'olConfig' : {
                    'chans' : olSegNames,
                    'dofs' : olDofNames,
                    'fulldofs' : olFullDofNames,
                    'inf' : {'blockname':'OPLEV', 'names':'chans'},
                    'noise' : {'blockname':'NOISEMON', 'names':'chans'},
                    'osem2eul' : {'blockname':'OPLEV_MTRX','inames':'chans', 'onames':'dofs', 'default':[[-1.,1.,1.,-1.],[-1,1.,-1.,1.],[1.,1.,1.,1.]]},
                    'full' : {'blockname':'OPLEV', 'names':'fulldofs'},
                    'sensalign' : sa3,
                    'drivealign' : None,
                    'eul2osem' : None,
                    'outf' : None
                },
                'gasConfig' : None,
                'iscdofs' : threeDofNames,
                'isc' : isc3,
                'damp' : damp3,
                'wit' : None,
                'lockdofs' : threeDofNames,
                'lock' : lock3top,
                'test' : test3,
                'align' : None,
                'ditherdofs' : ditherDofNames,
                'dither' : {'blockname':'DITHER', 'names':'ditherdofs'},
                'watchdog' : 'watchdogs'
            }
        }
    },
    # -------------
    'TYPEC' : {
        'reallyis' : 'TYPEC',
        'levelorder' : ['IM','TM'],
        'master' : 'MASTERSWITCH',
        'commissioning' : 'COMMISH_STATUS',
        'levels' : {
            'IM' : {
                'dofs' : sixDofNames,
                'osemConfig' : {
                    'chans' : typecM1levelOsemNames,
                    'dofs' : sixDofNames,
                    'osem' : kosem,
                    'magnet' : {'diameter':10,'length':10,'material':'NdFeB','force':1.694}, # FIXME
                    'driver' : lpcd,
                    'sensalign' : sa6,
                    'inf' : {'blockname':'OSEMINF', 'names':'chans'},
                    'noise' : {'blockname':'NOISEMON', 'names':'chans'},
                    'osem2eul' : {'blockname':'OSEM2EUL','inames':'chans', 'onames':'dofs', 'default':typec_o2e_m1},
                    'eul2osem' : {'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 'default':map(list,zip(*typec_o2e_m1))},
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':signsM1}}
                },
                'oldampdofs' : olDampDofNames,
                'oldamp' : None,
                'olConfig' : None,
                'gasConfig' : None,
                'isc' : None,
                'damp' : damp6,
                'wit' : None,
                'lockdofs' : threeDofNames,
                'lock' : lock3top,
                'test' : test6,
                'aligndofs' : alignDofNames,
                'align' : {'blockname':'OPTICALIGN', 'names':'aligndofs'},
                'ditherdofs' : ditherDofNames,
                'dither' : {'blockname':'DITHER', 'names':'ditherdofs'},
                'watchdog' : 'watchdogs'
            },
            'TM' : {
                'dofs' : threeDofNames,
                'osemConfig' : {
                    'chans' : typecTMlevelOsemNames,
                    'dofs' : threeDofNames,
                    'osem' : kosem,
                    'magnet' : {'diameter':10,'length':10,'material':'NdFeB','force':1.694}, # FIMXME
                    'driver' : lpcd,
                    'sensalign' : sa6,
                    'inf' : {'blockname':'OSEMINF', 'names':'chans'},
                    'noise' : {'blockname':'NOISEMON', 'names':'chans'},
                    'osem2eul' : {'blockname':'OSEM2EUL','inames':'chans', 'onames':'dofs', 'default':typec_o2e_tm},
                    'eul2osem' : {'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 'default':map(list,zip(*typec_o2e_tm))},
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':signsTM}}
                },
                'oldampdofs' : olDampDofNames,
                'oldamp' : {'blockname':'OLDAMP', 'names':'oldampdofs'},
                'olConfig' : {
                    'chans' : olSegNames,
                    'dofs' : olDofNames,
                    'fulldofs' : olFullDofNames,
                    'inf' : {'blockname':'OPLEV', 'names':'chans'},
                    'noise' : {'blockname':'NOISEMON', 'names':'chans'},
                    'osem2eul' : {'blockname':'OPLEV_MTRX','inames':'chans', 'onames':'dofs', 'default':[[-1.,1.,1.,-1.],[-1,1.,-1.,1.],[1.,1.,1.,1.]]},
                    'full' : {'blockname':'OPLEV', 'names':'fulldofs'},
                    'sensalign' : sa3,
                    'drivealign' : None,
                    'eul2osem' : None,
                    'outf' : None
                },
                'gasConfig' : None,
                'iscdofs' : threeDofNames,
                'isc' : isc3,
                'damp' : damp3,
                'wit' : None,
                'lockdofs' : threeDofNames,
                'lock' : lock3top,
                'test' : test3,
                'aligndofs' : alignDofNames,
                'align' : {'blockname':'OPTICALIGN', 'names':'aligndofs'},
                'ditherdofs' : ditherDofNames,
                'dither' : {'blockname':'DITHER', 'names':'ditherdofs'},
                'watchdog' : 'watchdogs'
            }
        }
    }
}

# --------------------------------------------------------------------------------------
# Consistency checks - enable the section below and load the module in a Python session to check that
# all appropriate methods have been added to one of the various lists that make them callable in command-line mode,
# and conversely, that all methods in the lists have actually been implemented.
if False:
    notimplemented = [fn for fn in callableGlobals if not fn in list(globals()) and not fn in callablesDefinedBelow]
    if notimplemented !=[]:
        print('Some globals declared in callableGlobals need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableVisCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableVisCommands need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableLevelDataCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelDataCommands need implementing: '+str(notimplemented))
    

    notimplemented = [fn for fn in callableOpticSwitchReadCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableOpticSwitchReadCommands need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableOpticSwitchWriteCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableOpticSwitchWriteCommands need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableLevelMatrixNameCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelMatrixNameCommands need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableLevelMatrixReadCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelMatrixReadCommands need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableLevelMatrixWriteCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelMatrixWriteCommands need implementing: '+str(notimplemented))

    notimplemented = [fn for fn in callableLevelFilterNameCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelFilterNameCommands need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableLevelFilterSwitchReadCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelFilterSwitchReadCommands need implementing: '+str(notimplemented))

    notimplemented = [fn for fn in callableLevelFilterSwitchWriteCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelFilterSwitchWriteCommands need implementing: '+str(notimplemented))

    notimplemented = [fn for fn in callableLevelFilterModuleEnableReadCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelFilterModuleEnableReadCommands need implementing: '+str(notimplemented))

    notimplemented = [fn for fn in callableLevelFilterModuleEnableWriteCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelFilterEnableWriteCommands need implementing: '+str(notimplemented))

    notdeclared = [fn for fn in list(Vis.__dict__) if not fn in allCallables and not fn in nonCallables and not fn in nonCallablesFixMeLater]
    if notdeclared !=[]:
        print('Some methods might need to be declared in one of the callable... lists: '+str(notdeclared))


# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------
# This needs to be last.
# Run the main() function if the file is run as a script from the command line.
if __name__ == "__main__":
    main()
# --------------------------------------------------------------------------------------
# ------------------------DON'T PUT CODE AFTER HERE!!!----------------------------------

