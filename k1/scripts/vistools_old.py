#!/usr/bin/env python 
# Note: the shebang line above needs to invoke vanilla python (rather than Guardian, which is a python interpreter with stuff pre-loaded)
# so that when this module is used from the command line it can parse its own options and arguments.

# Please use 4-space indenting, not tabs. In the Tab Width menu in the lower window frame in gedit, 
#  select Automatic Indentation off, Tab Width 4, Use Spaces on.

"""vistools.py - module for managing suspensions via EPICS/ezca; also callable from the command line.

vistools.visData is a large nested dictionary structure with information about different suspension types ('TYPEA', 'TYPEB' etc)
vistools.visTypes is dictionary mapping suspensions ('BS' etc) to suspension types.
vistools.Vis is a class with a large number of methods for accessing the information in visData and manipulating the suspension via ezca.

Within Python or iPython, create a Vis object from a string (or Guardian SYSTEM string or ezca object):
BS=vistools.Vis('BS') # creates an object that works on the beamsplitter

Within Guardian, from 
vis = Vis((SYSTEM,ezca)) # create a Vis object without needing to hardcode the suspension name

Then call its various methods, which are mostly organized and named by groups of filters:

vis.masterSwitchWrite('ON') # turns the master switch on
vis.dampGainWrite(1.0) # sets all gain values in all DAMP blocks to 1.0. 
vis.dampGainWrite(1.0,levels=['IP']) # sets all gain values in the IP DAMP block to 1.0.  
vis.dampGainWrite(1.0,levels=['IP'],chans=['L','T']) # sets the gain values for the L and T channels of the IP DAMP block to 1.0 

From the command line, make sure that vistools.py has the executable (x) bit set (chmod +x vistools.py) then do
./vistools.py --help
./vistools.py -o BS dampGainWrite -l IP -c L T -v 1 # sets the gain values for the L and T channels of the IP DAMP block to 1.0
"""

# -*- mode: python -*-

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
        if '/Users/mbarton/Dropbox/KAGRA-Dropbox/TypeB/guardian/scripts' not in sys.path:
            sys.path.append('/Users/mbarton/Dropbox/KAGRA-Dropbox/TypeB/guardian/scripts')
            os.environ['IFO']='K1'
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
# Class representing a single suspension. Can be initialized with a string, e.g., 'ITMX', or an instance of an Ezca object, or a (SYSTEM,ezca) tuple.
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
    # Manual mode methods
    def switch(self, pv, setting, enable, verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Utility function to enable/disable a switch. pv='BS_TM_DAMP_L' or the like, setting='_INPUT', enable='ON'/'OFF'."""
        if dorw==2 :
            retval = self.ezca.switch(self.infix+pv,setting,enable)
            result =  fmtpair(self.fmtprefix(withprefix)+pv,(setting,enable), pair)
        else:
            result =  fmtpair(self.fmtprefix(withprefix)+pv,(setting,dummyval), pair)            
        time.sleep(sleepTime) # DEBUG
        if verbose:
            print >>sys.stderr, '%s_%s <- %s' % (str(self.fmtprefix(withprefix)+pv),str(setting),enable)
        if matlab: return toMatlab(result)
        else: return result

    def write(self, pv, value, verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Utility function to write a numeric value to a pv. pv='BS_TM_DAMP_L_OFFSET' or the like."""
        if dorw==2 :
            self.ezca.write(self.infix+pv,value)
        result = fmtpair(self.fmtprefix(withprefix)+pv,value, pair)
        if verbose: 
            print >>sys.stderr, '%s <- %s' % (str(self.fmtprefix(withprefix)+pv),value)
        time.sleep(sleepTime) # DEBUG
        if matlab: return toMatlab(result)
        else: return result

    def writelist(self, pvs, values, verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Utility function to write a list of numeric values to a list of pvs. pvs=['BS_TM_DAMP_P','BS_TM_DAMP_Y'] or the like."""
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
        """Utility function to read a numeric value from a pv. pv='BS_TM_DAMP_L_OUTMON' or the like."""
        if dorw>=1 :
            result = self.ezca.read(self.infix+pv)
            if verbose: 
                print >>sys.stderr, '%s -> %s' % (str(self.fmtprefix(withprefix)+pv),str(result))
        else:
            result = dummyval
            if verbose: 
                print >>sys.stderr, '%s -> %s (dummy value)' % (str(self.fmtprefix(withprefix)+pv),str(result))
        return fmtpair(self.fmtprefix(withprefix)+pv,result, pair)

    def readlist(self,pvs, verbose=False, pair='value', withprefix='bare', dorw=2):
        """Utility function to write a list of numeric values from a list of pvs. pvs=['BS_TM_DAMP_P_OUTMON','BS_TM_DAMP_Y_OUTMON'] or the like."""
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


    # -------------------------------------------------------------
    # Assorted informative methods
    def fmtprefix(self, withprefix):
        """Return longer or shorter version of the PV prefix string. withprefix = 'full' -> "K1:VIS-BS or the like, 'halffull' -> 'VIS-BS_', 'halfbare' -> 'BS_', 'bare' ->''."""
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
        """Return the list of all levels in the canonical order."""
        result = self.data['levelorder']
        if matlab: return toMatlab(result)
        else: return result

    def suspensionType(self, verbose=False, matlab=False):
        """Return what the type of the suspension 'really is' per the 'reallyis' field of the definition. (Allows for variant types, e.g., HSTS->HSTS2, HSTS2M at LIGO.)"""
        result = self.data['reallyis']
        if matlab: return toMatlab(result)
        else: return result

    def levelchannames(self, sensact, nametype, levels=[], chans=[], verbose=False, matlab=False):
        """Returns a list of pvs for a block of type sensact. levels and chans narrow the list."""
        if levels==[]: ilevels = self.data['levelorder']
        else: ilevels = levels
        result = [
            chan
            for level in ilevels if self.data['levels'][level][sensact]
            for chan in self.data['levels'][level][sensact][nametype] if chans==[] or chan in chans
        ]
        if matlab: return toMatlab(result)
        else: return result


    def levelsensactdata(self, sensact, data, key, levels=[], verbose=False, matlab=False):
        """Returns data stored at location specified by list key for a block of type sensact. levels and chans narrow the list."""
        if levels==[]: ilevels = self.data['levelorder']
        else: ilevels = levels
        if key==[]:
            result = [
                self.data['levels'][level][sensact][data]
                for level in ilevels if self.data['levels'][level][sensact]
            ]
        elif len(key)==1:
            result = [
                self.data['levels'][level][sensact][data][key[0]]
                for level in ilevels if self.data['levels'][level][sensact]
            ]
        elif len(key)==2:
            result = [
                self.data['levels'][level][sensact][data][key[0]][key[1]]
                for level in ilevels if self.data['levels'][level][sensact]
            ]
        elif len(key)==3:
            result = [
                self.data['levels'][level][sensact][data][key[0]][key[1]][key[2]]
                for level in ilevels if self.data['levels'][level][sensact]
            ]
        if matlab: return toMatlab(result)
        else: return result

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

    # Return ESD names
    def esdNames(self, levels=[], chans=[], withprefix='bare', suffix='', verbose=False, matlab=False):
        """Return a list of ESD segment names. Optional arguments levels and chans narrow the selection."""
        return self.levelchannames('esdConfig', 'chans', levels=levels, chans=chans, verbose=verbose, matlab=matlab)

    # Return ESD DOF names
    def esdDofs(self, levels=[], chans=[], withprefix='bare', suffix='', verbose=False, matlab=False):
        """Return a list of DOFs associated with ESD. Optional arguments levels and chans narrow the selection"""
        return self.levelchannames('esdConfig', 'dofs', levels=levels, chans=chans, verbose=verbose, matlab=matlab)

    # -------------------------------------------------------------
    # Generic utility methods for non-sensor/actuator specific matrix blocks such as CART2EUL
 
    def levelmatrixblockpvs(self, block, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', suffix = '', matlab=False):
        """Return all element PVs for a non-sensor/actuator specific matrix block type such as CART2EUL."""
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if self.data['levels'][level] and self.data['levels'][level][block]]
        else: 
            ilevels = [level for level in levels if level in self.data['levels'].keys() and self.data['levels'][level][sensact] and self.data['levels'][level][sensact][block]]
        result = []
        for level in ilevels:
            leveldata = self.data['levels'][level]
            ics = [ic for ic in leveldata[block]['inames'] if ichans==[] or ic in ichans] # input channels to be iterated over
            ocs = [oc for oc in leveldata[block]['onames'] if ochans==[] or oc in ochans] # input channels to be iterated over
            result+=[
                self.fmtprefix(withprefix)+level+'_'+leveldata[block]['blockname']+suffix+'_'+str(icn+1)+'_'+str(ocn+1)
                for icn in range(len(ics))
                for ocn in range(len(ocs))
            ]
        if matlab: return toMatlab(result)
        else: return result
 
    def levelmatrixblockdefs(self, block, levels=[], ichans=[], ochans=[], verbose=False, suffix = '', matlab=False):
        """Return element default values for a non-sensor/actuator specific matrix block type such as CART2EUL."""
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if self.data['levels'][level] and self.data['levels'][level][block]]
        else: 
            ilevels = [level for level in levels if level in self.data['levels'].keys() and self.data['levels'][level] and self.data['levels'][level][block]]
        result = []
        for level in ilevels:
            leveldata = self.data['levels'][level]
            ics = [ic for ic in leveldata[block]['inames'] if ichans==[] or ic in ichans] # input channels to be iterated over
            ocs = [oc for oc in leveldata[block]['onames'] if ochans==[] or oc in ochans] # input channels to be iterated over
            if leveldata[block]['default']==None: raise VisError('No defaults supplied for block '+str(block)+' at level '+str(level))
            result+=[
                float(leveldata[block]['default'][icn][ocn])
                for icn in range(len(ics))
                for ocn in range(len(ocs))
            ]
        if matlab: return toMatlab(result)
        else: return result
 
    def levelmatrixblockread(self, block, levels=[], ichans=[], ochans=[], verbose=False, pair='value', withprefix='bare', suffix = '', matlab=False, dorw=2):
        """Read values for a non-sensor/actuator specific matrix block type such as CART2EUL."""
        pvs = self.levelmatrixblockpvs(block, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix='bare', matlab=False)
        result = self.readlist(pvs, verbose=verbose, dorw=2)
        if matlab: return toMatlab(result)
        else: return result
  
    def levelmatrixblockwrite(self, block, operation='none', value=0.0, array=[], levels=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', suffix = '', matlab=False, dorw=2):
        """Write values for a non-sensor/actuator specific matrix block type such as CART2EUL."""
        pvs = self.levelmatrixblockpvs(block, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix='bare', matlab=False)
        if operation=='none':
            pass
        elif operation=='defaults':
            vals = self.levelmatrixblockdefs(block, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, matlab=False)
        elif operation=='value':
            vals = [value for pv in pvs]
        elif operation=='array':
            if len(array)!=len(pvs): raise VisError('Length of array does not match number of channels ('+str(len(pvs))+')')
        self.writelist(pvs,vals, verbose=verbose, dorw=dorw)

    # -------------------------------------------------------------
    # Generic utility methods for sensor/actuator-specific matrix blocks such as OSEM2EUL
 
    def levelsensactmatrixblockpvs(self, sensact, block, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', suffix = '', matlab=False):
        """Return element PVs for a sensor/actuator specific matrix block type such as OSEM2EUL."""
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if self.data['levels'][level][sensact] and self.data['levels'][level][sensact][block]]
        else: 
            ilevels = [level for level in levels if level in self.data['levels'].keys() and self.data['levels'][level][sensact] and self.data['levels'][level][sensact][block]]
        result = []
        for level in ilevels:
            sensactdata = self.data['levels'][level][sensact]
            ics = [ic for ic in sensactdata[sensactdata[block]['inames']] if ichans==[] or ic in ichans] # input channels to be iterated over
            ocs = [oc for oc in sensactdata[sensactdata[block]['onames']] if ochans==[] or oc in ochans] # input channels to be iterated over
            result+=[
                self.fmtprefix(withprefix)+level+'_'+sensactdata[block]['blockname']+suffix+'_'+str(ocn+1)+'_'+str(icn+1)
                for icn in range(len(ics))
                for ocn in range(len(ocs))
            ]
        if matlab: return toMatlab(result)
        else: return result
 
    def levelsensactmatrixblockdefs(self, sensact, block, levels=[], ichans=[], ochans=[], verbose=False, suffix = '', matlab=False):
        """Return element default values for a sensor/actuator specific matrix block type such as OSEM2EUL."""
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if self.data['levels'][level][sensact] and self.data['levels'][level][sensact][block]]
        else: 
            ilevels = [level for level in levels if level in self.data['levels'].keys() and self.data['levels'][level][sensact] and self.data['levels'][level][sensact][block]]
        result = []
        for level in ilevels:
            sensactdata = self.data['levels'][level][sensact]
            if sensactdata[block]['default']==None: raise VisError('No defaults supplied for block '+str(block)+' at level '+str(level))
            ics = [ic for ic in sensactdata[sensactdata[block]['inames']] if ichans==[] or ic in ichans] # input channels to be iterated over
            ocs = [oc for oc in sensactdata[sensactdata[block]['onames']] if ochans==[] or oc in ochans] # input channels to be iterated over
            result+=[
                float(sensactdata[block]['default'][ocn][icn])
                for icn in range(len(ics))
                for ocn in range(len(ocs))
            ]
        if matlab: return toMatlab(result)
        else: return result
 
    def levelsensactmatrixblockread(self, sensact, block, levels=[], ichans=[], ochans=[], verbose=False, pair='value', withprefix='bare', suffix = '', matlab=False, dorw=2):
        """Read values for a sensor/actuator specific matrix block type such as OSEM2EUL."""
        pvs = self.levelsensactmatrixblockpvs(sensact,block, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix='bare', matlab=False)
        result = self.readlist(pvs, verbose=verbose, dorw=dorw)
        if matlab: return toMatlab(result)
        else: return result
 
    def levelsensactmatrixblockwrite(self, sensact, block, operation='none', value=0.0, array=[], levels=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', suffix = '', matlab=False, dorw=2):
        """Write values for a sensor/actuator specific matrix block type such as OSEM2EUL."""
        pvs = self.levelsensactmatrixblockpvs(sensact,block, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix='bare', matlab=False)
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
 
    def levelsensactfilterblockpvs(self, sensact, block, levels=[], chans=[], verbose=False, withprefix='bare', suffix = '', matlab=False):
        """Return all channel/DOF PVs for a sensor/actuator specific filter block type such as COILOUTF."""
        if levels==[]: 
            ilevels = [level for level in self.data['levelorder'] if self.data['levels'][level][sensact] and self.data['levels'][level][sensact][block]]
        else: 
            ilevels = [level for level in levels if level in self.data['levels'].keys() and self.data['levels'][level][sensact] and self.data['levels'][level][sensact][block]]
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
            ilevels = [level for level in self.data['levelorder'] if self.data['levels'][level][block]]
        else:
            ilevels = [level for level in levels if level in self.data['levels'].keys() and self.data['levels'][level][block]]
        result = [ 
            self.fmtprefix(withprefix)+level+'_'+self.data['levels'][level][block]['blockname']+'_'+chan+suffix
            for level in ilevels
            for chan in self.data['levels'][level][self.data['levels'][level][block]['names']] if (chans==[] or chan in chans)
        ]
        if matlab: return toMatlab(result)
        else: return result

    # FIXME: add method to return defaults

    def witPvs(self, levels=[], chans=[], verbose=False, withprefix='bare', matlab=False):
        """Return all witness PVs."""
        if levels==[]:
            ilevels = [level for level in self.data['levelorder'] if self.data['levels'][level]['wit']]
        else:
            ilevels = [level for level in levels if level in self.data['levels'].keys() and self.data['levels'][level]['wit']]
        result = [] 
        for level in ilevels:
            for chan in self.data['levels'][level][self.data['levels'][level]['wit']['names']]:
                if (chans==[] or chan in chans):
                    result.append(self.fmtprefix(withprefix)+level+'_'+self.data['levels'][level]['wit']['blockname']+'_'+chan+self.data['levels'][level]['witsuffix'])
        if matlab: return toMatlab(result)
        else: return result

    def witRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the witness channels. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.witPvs, '', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)


    # -----------------------------------------------------------------------------------------------------------
    # Generic methods for all filter modules (DAMP, TEST, OSEMINF, COILOUTF)

    def genNumWrite(self, pvfn, suffix, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write filter numeric value or list of values (GAIN, TRAMP etc) - functions based on this should supply '_' in suffix, e.g., '_RAMP'."""
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
        """Read filter numeric value (GAIN, TRAMP etc) - functions based on this should supply '_' in suffix, e.g., '_RAMP'."""
        pvs = pvfn(levels=levels,chans=chans)
        result = [
            self.read(pv+suffix, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
            for pv in pvs
        ]
        if matlab: return toMatlab(result)
        else: return result

    def genSwitchWrite(self, pvfn, suffix, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab = False, dorw=2):
        """Switch filter switches on or off (OUTPUT, INPUT, OFFSET etc) - functions based on this should NOT supply '_' in suffix, e.g., 'OFFSET'."""
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
        """Read filter switch state (OUTPUT, INPUT, OFFSET etc) - functions based on this should NOT supply '_' in suffix, e.g., 'OFFSET'."""
        if type(bits)==str:
            masks = {cdsFiltMask[bits]['swnrsuffix'] : cdsFiltMask[bits]['swnrmask']}
        else:
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
            for suffix, mask in masks.iteritems():
                if dorw>=1:
                    resultbit = bool(resultbit|bool(int(self.read(pv+suffix, dorw=dorw))&mask))
                else:
                    resultsbit = None
                resultsuffix = resultsuffix+suffix+'.'+str(mask)
            result.append(fmtpair(self.fmtprefix(withprefix)+pv+resultsuffix,resultbit, pair))          
        if matlab: return toMatlab(result)
        else: return result

    def genFilterModuleEnableWrite(self, pvfn, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Enable/disable filter module switches (FM1, FM2 etc)."""
        for filt in filters:
            checkHaveIntVal(filt)
        if enable=='ON' or enable=='OFF':
            pvs = pvfn(levels=levels,chans=chans)
            result = [
                self.switch(pv,'FM'+str(filt),enable, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
                for filt in filters
                for pv in pvs
            ]
        else:
            pass # NC = no change
        if pair=='none': result = None
        if matlab: return toMatlab(result)
        else: return result

    # -----------------------------------------------------------------------------------------------------------
    # Generic methods for sensor/actuator-specific filter modules (OSEMINF, COILOUTF, OLINF, ESDOUTF, etc)


    # -----------------------------------------------------------------------------------------------------------
    # PV list and default value methods

    # For sensor/actuator-specific matrix blocks

    def e2oPvs(self, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        """Return PV names for all or selected EUL2OSEM channels."""
        return self.levelsensactmatrixblockpvs('osemConfig','eul2', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def e2oDefs(self, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        """Return default values for all or selected EUL2OSEM channels"""
        return self.levelsensactmatrixblockdefs('osemConfig','eul2', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def ol2ePvs(self, levels=[], ichans=[], ochans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        """Return PV names for all or selected OL2EUL block channels."""
        return self.levelsensactmatrixblockpvs('olConfig','2eul', levels=levels, ichans=ichans, ochans=ochans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def e2esdPvs(self, levels=[], ichans=[], ochans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        """Return PV names for all or selected EUL2ESD block channels."""
        return self.levelsensactmatrixblockpvs('esdConfig','eul2', levels=levels, ichans=ichans, ochans=ochans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    # For non-sensor/actuator-specific matrix blocks

    def c2ePvs(self, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        """Return PV names for all or selected CART2EUL channels."""
        return self.levelmatrixblockpvs('cart2eul', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def c2eDefs(self, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        """Return default values for all or selected CART2EUL channels."""
        return self.levelmatrixblockdefs('cart2eul', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)
 
    # -----------------------------------------------------------------------------------------------------------
    # Methods for OSEM2EUL blocks

    def o2ePvs(self, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        """Return PV names for all or selected OSEM2EUL matrix elements."""
        return self.levelsensactmatrixblockpvs('osemConfig','2eul', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def o2eDefs(self, levels=[], ichans=[], ochans=[], verbose=False, withprefix='bare', matlab=False):
        """Return default values for all or selected OSEM2EUL matrix elements."""
        return self.levelsensactmatrixblockdefs('osemConfig','2eul', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def o2eRead(self, levels=[], ichans=[], ochans=[], verbose=False, pair='value', withprefix='bare', matlab=False):
        """Read  all or selected OSEM2EUL input/output matrix values."""
        return self.levelsensactmatrixblockread('osemConfig','2eul', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def o2eWriteDefaults(self, levels=[], value=0.0, array=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write default values for all or selected OSEM2EUL input and output matrix elements."""
        return self.levelsensactmatrixblockwrite('osemConfig','2eul','defaults', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)

    def o2eWriteValue(self, levels=[], value=0.0, array=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a common value into all or selected OSEM2EUL matrix elements."""
        return self.levelsensactmatrixblockwrite('osemConfig','2eul','value',value=value, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)

    def o2eWriteArray(self, levels=[], value=0.0, array=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write an array into all or selected OSEM2EUL matrix elements."""
        return self.levelsensactmatrixblockwrite('osemConfig','2eul','array', array=array, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)

    # -----------------------------------------------------------------------------------------------------------
    # Methods for EUL2OSEM blocks

    def e2oRead(self, levels=[], ichans=[], ochans=[], verbose=False, pair='value', withprefix='bare', matlab=False):
        """Return PV names for all or selected EUL2OSEM matrix elements."""
        return self.levelsensactmatrixblockread('osemConfig','eul2', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab)

        """Write default values for all or selected EUL2OSEM input and output matrix elements."""
    def e2oWriteDefaults(self, levels=[], value=0.0, array=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        self.levelsensactmatrixblockwrite('osemConfig','eul2','defaults', levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)

    def e2oWriteValue(self, levels=[], value=0.0, array=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a common value into all or selected EUL2OSEM matrix elements."""
        self.levelsensactmatrixblockwrite('osemConfig','eul2','value',value=value, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)

    def e2oWriteArray(self, levels=[], value=0.0, array=[], ichans=[], ochans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write an array into all or selected EUL2OSEM matrix elements."""
        self.levelsensactmatrixblockwrite('osemConfig','eul2','array', array=array, levels=levels, ichans=ichans, ochans=ochans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=False, dorw=dorw)

    # FIXME: add methods for OL2EUL, EUL2ESD, CART2EUL

    # -------------------------------------------------------------
    # Methods for specific matrices, blocks, switches.
    
    # Methods for top-level items
    # Switch the Master Switch
    def masterSwitchWrite(self, enable, verbose=False, pair='none', withprefix='bare', dorw=2):
        """Write 'ON" or 'OFF' to the MASTER SWITCH."""
        pv = self.data['master']
        if enable=='ON':
            if verbose: 
                print >>sys.stderr, '%s <- %s' % (str(self.fmtprefix(withprefix)+pv),enable)
            self.write(pv,"ON", dorw=dorw)
        elif enable=='OFF':
            if verbose: 
                print >>sys.stderr, '%s <- %s' % (str(self.fmtprefix(withprefix)+pv),enable)
            self.write(pv,"OFF", dorw=dorw)
        else:
            pass # NC = no change
        return None # FIXME return something better

    # Read the Master Switch # FIXME add standard options
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
        """Write 'ON' or 'OFF' to the COMMISSIONING SWITCH a.k.a. the MEASUREMENT SWITCH."""
        pv = self.data['commissioning']
        if enable=='ON':
            if verbose: 
                print >>sys.stderr, '%s <- %s' % (str(self.fmtprefix(withprefix)+pv),enable)
            self.write(pv,"ON", dorw=dorw)
        elif enable=='OFF':
            if verbose: 
                print >>sys.stderr, '%s <- %s' % (str(self.fmtprefix(withprefix)+pv),enable)
            self.write(pv,"OFF", dorw=dorw)
        else:
            pass # NC = no change
        return None # FIXME return something better

    # Read the Commissioning Switch # FIXME add standard options
    def commSwitchRead(self, verbose=False, pair='none', withprefix='bare', dorw=2):
        """Read the COMMISSIONING/MEASUREMENT SWITCH (returns True/False)."""
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
    # Methods for DAMP blocks

    def dampPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        """Return a list of PVs for DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.levelfilterblockpvs('damp', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def dampPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in DAMP blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.dampPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.dampPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OUTPUT switch in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dampPvs, 'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the INPUT switch in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dampPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampOffsetSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OFFSET switch in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dampPvs, 'OFFSET', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampHoldSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the HOLD switch in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dampPvs, 'HOLD', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the GAIN field in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.dampPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampOffsetWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the OFFSET field in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.dampPvs, '_OFFSET', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the RAMP field in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.dampPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampFilterModuleEnableWrite(self, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the filter switches in DAMP blocks. Optional arguments filters, levels and chans select particular channels."""
        return self.genFilterModuleEnableWrite(self.dampPvs, enable, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampOutputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OUTPUT switch in DAMP blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.dampPvs, 'OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampInputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the INPUT switch in DAMP blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.dampPvs, 'INPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampGainRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain ramping state (GRAMP) in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.dampPvs, 'GRAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampOffsetRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the offset ramping state (ORAMP) in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.dampPvs, 'ORAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the overall ramping state (GRAMP or ORAMP) in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.dampPvs, ['GRAMP','ORAMP'], levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dampGainRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain value in DAMP blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.dampPvs, '_GAIN', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

   # -------------------------------------------------------------
    # Methods for DCCTRL blocks

    def dcctrlPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelfilterblockpvs('dcctrl', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def dcctrlPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in DCCTRL blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.dcctrlPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.dcctrlPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OUTPUT switch in DCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dcctrlPvs, 'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the INPUT switch in DCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dcctrlPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlOffsetSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OFFSET switch in DCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dcctrlPvs, 'OFFSET', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlHoldSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the HOLD switch in DCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.dcctrlPvs, 'HOLD', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the GAIN field in DCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.dcctrlPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlOffsetWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the OFFSET field in DCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.dcctrlPvs, '_OFFSET', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values or list of values to the RAMP field in DCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.dcctrlPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlFilterModuleEnableWrite(self, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the filter switches in DCCTRL blocks. Optional arguments filters, levels and chans select particular channels."""
        return self.genFilterModuleEnableWrite(self.dcctrlPvs, enable, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlOutputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OUTPUT switch in DCCTRL blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.dcctrlPvs, 'OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlInputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the INPUT switch in DCCTRL blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.dcctrlPvs, 'INPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlGainRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain ramping state (GRAMP) in DCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.dcctrlPvs, 'GRAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlOffsetRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the offset ramping state (ORAMP) in DCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.dcctrlPvs, 'ORAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the overall ramping state (GRAMP or ORAMP) in DCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.dcctrlPvs, ['GRAMP','ORAMP'], levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def dcctrlGainRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        return self.genNumRead(self.dcctrlPvs, '_GAIN', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

   # -------------------------------------------------------------
    # Methods for SET blocks

    def setPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        """Return a list of PVs for SET blocks. Optional arguments levels and chans select particular channels."""
        return self.levelfilterblockpvs('set', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def setPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in SET blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.setPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.setPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OUTPUT switch in SET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.setPvs, 'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the INPUT switch in SET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.setPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setOffsetSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OFFSET switch in SET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.setPvs, 'OFFSET', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setHoldSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the HOLD switch in SET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.setPvs, 'HOLD', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the GAIN field in SET blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.setPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setOffsetWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the OFFSET field in SET blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.setPvs, '_OFFSET', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the RAMP field in SET blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.setPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setFilterModuleEnableWrite(self, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the filter switches in SET blocks. Optional arguments filters, levels and chans select particular channels."""
        return self.genFilterModuleEnableWrite(self.setPvs, enable, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setOutputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OUTPUT switch in SET blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.setPvs, 'OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setInputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the INPUT switch in SET blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.setPvs, 'INPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setGainRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain ramping state (GRAMP) in SET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.setPvs, 'GRAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setOffsetRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the offset ramping state (ORAMP) in SET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.setPvs, 'ORAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the overall ramping state (GRAMP or ORAMP) in SET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.setPvs, ['GRAMP','ORAMP'], levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def setGainRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain value in SET blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.setPvs, '_GAIN', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

   # -------------------------------------------------------------
    # Methods for OLSET blocks

    def olSetPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        """Return a list of PVs for OLSET blocks. Optional arguments levels and chans select particular channels."""
        return self.levelfilterblockpvs('olset', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def olSetPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in OLSET blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.olSetPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.olSetPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OUTPUT switch in OLSET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.olSetPvs, 'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the INPUT switch in OLSET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.olSetPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetOffsetSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OFFSET switch in OLSET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.olSetPvs, 'OFFSET', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetHoldSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the HOLD switch in OLSET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.olSetPvs, 'HOLD', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the GAIN field in OLSET blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.olSetPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetOffsetWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the OFFSET field in OLSET blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.olSetPvs, '_OFFSET', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the RAMP field in OLSET blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.olSetPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetFilterModuleEnableWrite(self, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the filter switches in OLSET blocks. Optional arguments filters, levels and chans select particular channels."""
        return self.genFilterModuleEnableWrite(self.olSetPvs, enable, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetOutputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OUTPUT switch in OLSET blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.olSetPvs, 'OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetInputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the INPUT switch in OLSET blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.olSetPvs, 'INPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetGainRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain ramping state (GRAMP) in OLSET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.olSetPvs, 'GRAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetOffsetRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the offset ramping state (ORAMP) in OLSET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.olSetPvs, 'ORAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the overall ramping state (GRAMP or ORAMP) in OLSET blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.olSetPvs, ['GRAMP','ORAMP'], levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSetGainRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain value in OLSET blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.olSetPvs, '_GAIN', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

   # -------------------------------------------------------------
    # Methods for OLDCCTRL blocks

    def olDcctrlPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        """Return a list of PVs for OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.levelfilterblockpvs('oldcctrl', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def olDcctrlPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.olDcctrlPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.olDcctrlPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OUTPUT switch in OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.olDcctrlPvs, 'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the INPUT switch in OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.olDcctrlPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlOffsetSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OFFSET switch in OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.olDcctrlPvs, 'OFFSET', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlHoldSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the HOLD switch in OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.olDcctrlnPvs, 'HOLD', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the GAIN field in OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.olDcctrlPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlOffsetWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the OFFSET field in OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.olDcctrlPvs, '_OFFSET', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the RAMP field in OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.olDcctrlPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlFilterModuleEnableWrite(self, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the filter switches in OLDCCTRL blocks. Optional arguments filters, levels and chans select particular channels."""
        return self.genFilterModuleEnableWrite(self.olDcctrlPvs, enable, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlOutputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OUTPUT switch in OLDCCTRL blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.olDcctrlPvs, 'OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlInputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the INPUT switch in OLDCCTRL blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.olDcctrlPvs, 'INPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlGainRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain ramping state (GRAMP) in OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.olDcctrlPvs, 'GRAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlOffsetRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the offset ramping state (ORAMP) in OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.olDcctrlPvs, 'ORAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the overall ramping state (GRAMP or ORAMP) in OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.olDcctrlPvs, ['GRAMP','ORAMP'], levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDcctrlGainRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain value in OLDCCTRL blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.olDcctrlPvs, '_GAIN', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    # -------------------------------------------------------------
    # Methods for TEST blocks
    def testPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        """Return a list of PVs for TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.levelfilterblockpvs('test', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def testPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in TEST blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.testPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.testPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OUTPUT switch in TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.testPvs,'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the INPUT switch in TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.testPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testOffsetSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OFFSET switch in TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.testPvs, 'OFFSET', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testHoldSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the HOLD switch in TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.testPvs, 'HOLD', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the GAIN field in TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.testPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testGainRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain value in TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.testPvs, '_GAIN', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testOffsetWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the OFFSET field in TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.testPvs, '_OFFSET', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testOffsetRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        return self.genNumRead(self.testPvs, '_OFFSET', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the RAMP field in TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.testPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testFilterModuleEnableWrite(self, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the filter switches in TEST blocks. Optional arguments filters, levels and chans select particular channels."""
        return genFilterModuleEnableWrite(self.testPvs, enable, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testOutputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OUTPUT switch in TEST blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.testPvs, 'OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testInputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the INPUT switch in TEST blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.testPvs, 'INPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testGainRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain ramping state (GRAMP) in TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.testPvs, 'GRAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testOffsetRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the offset ramping state (ORAMP) in TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.testPvs, 'ORAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def testRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the overall ramping state (GRAMP or ORAMP) in TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.testPvs, ['GRAMP','ORAMP'], levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    # -------------------------------------------------------------
    # Methods for LOCK blocks

    def lockPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        """Return a list of PVs for LOCK blocks. Optional arguments levels and chans select particular channels."""
        return self.levelfilterblockpvs('lock', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def lockPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in LOCK blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.lockPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.lockPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OUTPUT switch in LOCK blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.lockPvs,'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the INPUT switch in LOCK blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.lockPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockOffsetSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OFFSET switch in LOCK blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.lockPvs, 'OFFSET', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockHoldSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the HOLD switch in LOCK blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.lockPvs, 'HOLD', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the GAIN field in LOCK blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.lockPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockOffsetWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the OFFSET field in LOCK blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.lockPvs, '_OFFSET', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the RAMP field in LOCK blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.lockPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockFilterModuleEnableWrite(self, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the filter switches in LOCK blocks. Optional arguments filters, levels and chans select particular channels."""
        return self.genFilterModuleEnableWrite(self.lockPvs, filters=filters, enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockOutputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OUTPUT switch in LOCK blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.lockPvs, enable, 'OUTPUT', chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockInputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
       """Read the INPUT switch in LOCK blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
       return self.genSwitchRead(self.lockPvs, 'INPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockGainRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain ramping state (GRAMP) in LOCK blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.lockPvs, 'GRAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockOffsetRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the offset ramping state (ORAMP) in LOCK blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.lockPvs, 'ORAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the overall ramping state (GRAMP or ORAMP) in LOCK blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.lockPvs, ['GRAMP','ORAMP'], levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def lockGainRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain value in LOCK blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.lockPvs, '_GAIN', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    # -------------------------------------------------------------
    # Methods for OPTICALIGN blocks

    def alignPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelfilterblockpvs('align', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def alignPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in LOCK blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.alignPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.alignPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OUTPUT switch in ALIGN blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.alignPvs,'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the INPUT switch in ALIGN blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.alignPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignOffsetSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the OFFSET switch in ALIGN blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.alignPvs, 'OFFSET', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignHoldSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the HOLD switch in ALIGN blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchWrite(self.alignPvs, 'HOLD', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the GAIN field in ALIGN blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.alignPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignOffsetWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the OFFSET field in ALIGN blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.alignPvs, '_OFFSET', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignOffsetRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        return self.genNumRead(self.alignPvs, '_OFFSET', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write a value or list of values to the RAMP field in ALIGN blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumWrite(self.alignPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignFilterModuleEnableWrite(self, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Write 'ON' or 'OFF' to the filter switches in ALIGN blocks. Optional arguments filters, levels and chans select particular channels."""
        return self.genFilterModuleEnableWrite(self.alignPvs, enable, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignOutputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OUTPUT switch in ALIGN blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.alignPvs, 'OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignOffsetSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the OFFSET switch in ALIGN blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.alignPvs, 'OFFSET', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignInputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the INPUT switch in ALIGN blocks. Optional arguments levels and chans select particular channels. Returns list of True/False."""
        return self.genSwitchRead(self.alignPvs, 'INPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignGainRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain ramping state (GRAMP) in ALIGN blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.alignPvs, 'GRAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignOffsetRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the offset ramping state (ORAMP) in ALIGN blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.alignPvs, 'ORAMP', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignRampingRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the overall ramping state (GRAMP or ORAMP) in ALIGN blocks. Optional arguments levels and chans select particular channels."""
        return self.genSwitchRead(self.alignPvs, ['GRAMP','ORAMP'], levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def alignGainRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        """Read the gain value in TEST blocks. Optional arguments levels and chans select particular channels."""
        return self.genNumRead(self.alignPvs, '_GAIN', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    # -------------------------------------------------------------
    # Methods for OSEMINF blocks

    def osemPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelsensactfilterblockpvs('osemConfig','inf', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def osemPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in OSEM2EUL blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.osemPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.osemPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def osemOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchWrite(self.osemPvs,'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def osemInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchWrite(self.osemPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def osemOffsetSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchWrite(self.osemPvs, 'OFFSET', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def osemGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genNumWrite(self.osemPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def osemOffsetWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genNumWrite(self.osemPvs, '_OFFSET', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def osemRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genNumWrite(self.osemPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def osemFilterModuleEnableWrite(self, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genFilterModuleEnableWrite(self.osemPvs, enable, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def osemOutputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchRead(self.osemPvs, 'OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def osemInputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchRead(self.osemPvs, 'INPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    # -------------------------------------------------------------
    # Methods for COILOUTF blocks

    def coilPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelsensactfilterblockpvs('gasConfig','outf', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)+self.levelsensactfilterblockpvs('osemConfig','outf', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def coilPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in EUL2COIL blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.coilPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.coilPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def coilOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchWrite(self.coilPvs,'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def coilInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchWrite(self.coilPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def coilOffsetSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchWrite(self.coilPvs, 'OFFSET', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def coilGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genNumWrite(self.coilPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def coilOffsetWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genNumWrite(self.coilPvs, '_OFFSET', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def coilRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genNumWrite(self.coilPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def coilFilterModuleEnableWrite(self, enable, filters=[], levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genFilterModuleEnableWrite(self.coilPvs, enable, filters=filters, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def coilOutputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchRead(self.coilPvs, 'OUTPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def coilInputSwitchRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchRead(self.coilPvs, 'INPUT', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    # -------------------------------------------------------------
    # Methods for ESDOUTF blocks
    def esdPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelsensactfilterblockpvs('esdConfig','outf', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    # FIXME: more stuff here
    # -------------------------------------------------------------
    # Methods for ISIINF blocks
    def isiPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelfilterblockpvs('isi', levels=levels,chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    # FIXME: more stuff here

    # -------------------------------------------------------------
    # Methods for OFFLOAD blocks
    def offloadPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelfilterblockpvs('offload', levels=levels,chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    # FIXME: more stuff here

    # -------------------------------------------------------------
    # Methods for ISCINF blocks
    def iscPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelfilterblockpvs('isc', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def iscOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchWrite(self.iscPvs,'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def iscRampWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False):
        return self.genNumWrite(self.iscPvs, '_TRAMP', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def iscGainWrite(self, value, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genNumWrite(self.iscPvs, '_GAIN', value=value, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    # -------------------------------------------------------------
    # Methods for OPLEV blocks
    def olPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelsensactfilterblockpvs('olConfig','full', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def olSegPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelsensactfilterblockpvs('olConfig','inf', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def olRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        return self.genNumRead(self.olPvs, suffix='_OUTMON', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olSegRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        return self.genNumRead(self.olSegPvs, suffix='_OUTMON', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    # -------------------------------------------------------------
    # Methods for OLDAMP blocks
    def olDampPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelfilterblockpvs('oldamp', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def olDampPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in OLDAMP blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.dampPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.olDampPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDampRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        return self.genNumRead(self.olDampPvs, suffix='_OUTMON', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDampOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchWrite(self.olDampPvs, 'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def olDampInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchWrite(self.olDampPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    # -------------------------------------------------------------
    # Methods for DITHER blocks
    def ditherPvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelfilterblockpvs('dither', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

    def ditherPressButton(self, button, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        """Simulate a press of the CLEAR HISTORY ('CLEAR') or LOAD COEFFICIENTS ('LOAD') button in DITHER blocks. Optional arguments levels and chans select particular channels."""
        if button == 'LOAD':
            return self.genNumWrite(self.ditherPvs, '_RSET', value=1, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)
        elif button == 'CLEAR':
            return self.genNumWrite(self.ditherPvs, '_RSET', value=2, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def ditherRead(self, levels=[], chans=[], verbose=False, pair='value', withprefix='bare', matlab=False, dorw=2):
        return self.genNumRead(self.ditherPvs, suffix='_OUTMON', levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def ditherOutputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchWrite(self.ditherPvs, 'OUTPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    def ditherInputSwitchWrite(self, enable, levels=[], chans=[], verbose=False, pair='none', withprefix='bare', matlab=False, dorw=2):
        return self.genSwitchWrite(self.ditherPvs, 'INPUT', enable=enable, levels=levels, chans=chans, verbose=verbose, pair=pair, withprefix=withprefix, matlab=matlab, dorw=dorw)

    # Methods for NOISEMON
    def noisePvs(self, levels=[], chans=[], suffix='', verbose=False, withprefix='bare', matlab=False):
        return self.levelsensactfilterblockpvs('osemConfig','noise', levels=levels, chans=chans, suffix=suffix, verbose=verbose, withprefix=withprefix, matlab=matlab)

# End of Vis() class definition

# --------------------------------------------------------------------------------------
# Stuff for command line use

# Function to convert a Python result into a Matlab-friendly string. 
# Lists and tuples are converted to cell arrays and booleans are converted to 0 or 1.
def toMatlab(thing, separator=' '):
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

def checkHaveIntVal(value):
    try: int(value)
    except:
        raise VisError('Non-integer value: '+value)

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
    if v!=None:
        print(v)

# Things that are allowed to be called from the command line
callableGlobals = ['visTypes','visData']
callableVisFunctions = ['levels','suspensionType']
callableLevelNameFunctions = [
    'testPvs', 'dampPvs','dcctrlPvs','setPvs','olSetPvs','olDcctrlPvs','witPvs','lockPvs','alignPvs','coilPvs','osemPvs','olSegPvs','olPvs','esdPvs',
    'osemNames','osemDofs','olNames','olDofs','esdNames','esdDofs','iscPvs','isiPvs','olDampPvs','noisePvs',
]
callableLevelDataFunctions = ['coilDriverData','magnetData','osemData']
callableLevelMatrixFunctions = ['o2ePvs','o2eDefs','e2oPvs','e2oVals','ol2ePvs','e2esdPvs','c2ePvs','c2eDefs']
callableLevelMatrixReadCommands = ['o2eRead','e2oRead']
callableLevelMatrixWriteCommands = ['o2eWriteDefaults','o2eWriteValue','o2eWriteArray','e2oWriteDefaults','e2oWriteValue','e2oWriteArray']
callableOpticSwitchWriteCommands = [
    'masterSwitchWrite','commSwitchWrite'
]

callableOpticSwitchReadCommands = ['masterSwitchRead','commSwitchRead']

callableLevelFilterModuleEnableWriteCommands = [
    'dampPressButton','dampOutputSwitchWrite','dampInputSwitchWrite','dampOffsetSwitchWrite','dampHoldSwitchWrite',
    'dcctrlPressButton','dcctrlOutputSwitchWrite','dcctrlInputSwitchWrite','dcctrlOffsetSwitchWrite','dcctrlHoldSwitchWrite',
    'setPressButton','setOutputSwitchWrite','setInputSwitchWrite','setOffsetSwitchWrite','setHoldSwitchWrite',
    'olSetPressButton','olSetOutputSwitchWrite','olSetInputSwitchWrite','olSetOffsetSwitchWrite','olSetHoldSwitchWrite',
    'olDcctrlPressButton','olDcctrlOutputSwitchWrite','olDcctrlInputSwitchWrite','olDcctrlOffsetSwitchWrite','olDcctrlHoldSwitchWrite',
    'testPressButton','testOutputSwitchWrite','testInputSwitchWrite','testOffsetSwitchWrite','testHoldSwitchWrite',
    'lockPressButton','lockOutputSwitchWrite','lockInputSwitchWrite','lockOffsetSwitchWrite','lockHoldSwitchWrite',
    'alignPressButton','alignOutputSwitchWrite','alignInputSwitchWrite','alignOffsetSwitchWrite','alignHoldSwitchWrite',
    'osemPressButton','osemOutputSwitchWrite','osemInputSwitchWrite','osemOffsetSwitchWrite',
    'coilPressButton','coilOutputSwitchWrite','coilInputSwitchWrite','coilOffsetSwitchWrite',
    'olDampPressButton','olDampOutputSwitchWrite','olDampInputSwitchWrite',
    'ditherPressButton','ditherOutputSwitchWrite','ditherInputSwitchWrite'
]

callableLevelFilterSwitchReadCommands = [
    'dampInputSwitchRead','dampOutputSwitchRead','dampOffsetRampingRead','dampGainRampingRead','dampRampingRead',
    'dcctrlInputSwitchRead','dcctrlOutputSwitchRead','dcctrlOffsetRampingRead','dcctrlGainRampingRead','dcctrlRampingRead',
    'setInputSwitchRead','setOutputSwitchRead','setOffsetRampingRead','setGainRampingRead','setRampingRead',
    'olSetInputSwitchRead','olSetOutputSwitchRead','olSetOffsetRampingRead','olSetGainRampingRead','olSetRampingRead',
    'olDcctrlInputSwitchRead','olDcctrlOutputSwitchRead','olDcctrlOffsetRampingRead','olDcctrlGainRampingRead','olDcctrlRampingRead',
    'testInputSwitchRead','testOutputSwitchRead','testOffsetRampingRead','testGainRampingRead','testRampingRead',
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
]
callableLevelFilterEnableCommands = [
    'dampFilterModuleEnableWrite','dcctrlFilterModuleEnableWrite','setFilterModuleEnableWrite','olSetFilterModuleEnableWrite','olDcctrlFilterModuleEnableWrite',
    'testFilterModuleEnableWrite','lockFilterModuleEnableWrite','alignFilterModuleEnableWrite',
    'coilFilterModuleEnableWrite','osemFilterModuleEnableWrite'
]
callableLevelFilterWriteCommands = [
    'dampRampWrite','dampOffsetWrite','dampGainWrite',
    'dcctrlRampWrite','dcctrlOffsetWrite','dcctrlGainWrite',
    'setRampWrite','setOffsetWrite','setGainWrite',
    'olSetRampWrite','olSetOffsetWrite','olSetGainWrite',
    'olDcctrlRampWrite','olDcctrlOffsetWrite','olDcctrlGainWrite',
    'testRampWrite','testOffsetWrite','testGainWrite',
    'lockRampWrite','lockOffsetWrite','lockGainWrite',
    'alignRampWrite','alignOffsetWrite','alignGainWrite',
    'osemRampWrite','osemOffsetWrite','osemGainWrite',
    'coilRampWrite','coilOffsetWrite','coilGainWrite'
]

callableLevelFilterReadCommands = ['alignOffsetSwitchRead','olDcctrlInputSwitchRead','alignOffsetRead', 'olDcctrlGainRead','olSetGainRead','olSetInputSwitchRead','iscOutputSwitchWrite',];

callableLevelFilterOutputReadCommands = ['olRead','olSegRead']

allCallables = (
    callableGlobals+callableVisFunctions+callableLevelNameFunctions+callableLevelDataFunctions+callableOpticSwitchWriteCommands
    +callableOpticSwitchReadCommands+callableLevelMatrixFunctions+callableLevelMatrixWriteCommands
    +callableLevelNameFunctions+callableLevelFilterModuleEnableWriteCommands+callableLevelFilterSwitchReadCommands
    +callableLevelFilterEnableCommands+callableLevelFilterWriteCommands+callableLevelFilterReadCommands
)

nonCallables = ['__module__', '__doc__', '__init__','__dict__', '__weakref__','switch','write','writelist','read','readlist','fmtprefix',
'levelchannames','levelsensactdata','levelmatrixblockpvs','levelmatrixblockdefs',
'levelmatrixblockread','levelmatrixblockwrite','levelsensactmatrixblockpvs',
'levelsensactmatrixblockdefs','levelsensactmatrixblockread','levelsensactmatrixblockwrite',
'levelsensactfilterblockpvs','levelsensactfilterblockdefs','levelfilterblockpvs',
'witPvs','genNumWrite','genNumRead','genSwitchWrite','genSwitchRead',
'genFilterModuleEnableWrite','waitForRampingToKickIn']

callablesDefinedBelow = ['visTypes', 'visData']

# FIXME - add the following to a suitable list:
nonCallablesFixMeLater = [
'olDampRead', 'ditherRead', 'iscGainWrite', 'witRead', 'ditherPvs', 'testOffsetRead', 'wdNames', 'e2oDefs', 'iscRampWrite',  'o2eRead', 'trippedWds', 'e2oRead',   'offloadPvs']

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
    parser.add_argument('-l', '--level', dest='levels', metavar='LEVEL', action='store', default=[], type=str, nargs='*', help='SAG level (M0/R0/etc; default all)')
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

        if options.command in callableVisFunctions:
            cmd = 'result = optic.'+options.command+'('\
            +'verbose='+str(options.verbose)\
            +', matlab='+str(options.matlab)\
            +'); print(result)'
            if options.verbose: print(cmd)
            exec(cmd)

        elif options.command in callableLevelNameFunctions:
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

        elif options.command in callableLevelDataFunctions:
            cmd = 'result = optic.'+options.command+'('\
            +str(options.key)\
            +', levels='+str(options.levels)\
            +', verbose='+str(options.verbose)\
            +', matlab='+str(options.matlab)\
            +'); print(result)'
            if options.verbose: print(cmd)
            exec(cmd)

        elif options.command in callableLevelMatrixFunctions:
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

        elif options.command in callableLevelMatrixReadCommands:
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

        elif options.command in callableLevelMatrixWriteCommands:
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

        elif options.command in callableOpticSwitchWriteCommands:
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
 
        elif options.command in callableOpticSwitchReadCommands:
            if options.pair=='': options.pair='none'
            cmd = 'result = optic.'+options.command\
            +'(verbose='+str(options.verbose)\
            +', pair='+repr(options.pair)\
            +', withprefix='+repr(options.withprefix)\
            +', dorw='+str(options.dorw)\
           +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
 
        elif options.command in callableLevelFilterModuleEnableWriteCommands:
            if options.pair=='': options.pair='none'
            cmd = 'result = optic.'+options.command+'(enable="'+options.enable+'"'\
            +', levels='+str(options.levels)\
            +', chans='+str(options.chans)\
            +', verbose='+str(options.verbose)\
            +', dorw='+str(options.dorw)\
            +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
 
        elif options.command in callableLevelFilterSwitchReadCommands:
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
 
        elif options.command in callableLevelFilterEnableCommands:
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
 
        elif options.command in callableLevelFilterWriteCommands:
            if options.pair=='': options.pair='none'
            cmd = 'result = optic.'+options.command+'('\
            +'value="'+str(options.value)+'"'\
            +', levels='+str(options.levels)\
            +', chans='+str(options.chans)\
            +', verbose='+str(options.verbose)\
            +', pair='+repr(options.pair)\
            +', withprefix='+repr(options.withprefix)\
            +', dorw='+str(options.dorw)\
            +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
  
        elif options.command in callableLevelFilterReadCommands:
            if options.pair=='': options.pair='none'
            cmd = 'result = optic.'+options.command+'('\
            +', levels='+str(options.levels)\
            +', chans='+str(options.chans)\
            +', verbose='+str(options.verbose)\
            +', pair='+repr(options.pair)\
            +', withprefix='+repr(options.withprefix)\
            +', dorw='+str(options.dorw)\
            +'); printifnotnone(result)'
            if options.verbose: print(cmd)
            exec(cmd)
  
        elif options.command in callableLevelFilterOutputReadCommands:
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
# Bit mask combos for reading back cdsFilt block settings via _SW1R and _SW2R, or _SWSTAT from T080135 (& T1300494)
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
    'IOP':'DACKILL','IP':'IP_WDMON',
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
    'GAS':'BIO_GAS_MON','IP':'BIO_IP_MON','GAS':'BIO_GAS_MON',
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
esdSegNames = ['UL','LL','UR','LR','DC']
isiNames = ['X','Y','RZ','Z','RX','RY']

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
esdDofNames = ['L','P','Y','BIAS']
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
damp3 = {'blockname':'DAMP', 'names':'dofs','default':{'gains':[-1.,-1.,-1.,-1.,-1.,-1.]}}
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
testEsd = {'blockname':'TEST', 'names':'esddofs','default':{'gains':[1.,1.,1.,1.]}}
isi6 =  {'blockname':'ISIINF', 'names':'isidofs'}
isc6 = {'blockname':'ISCINF', 'names':'iscdofs'}
isc3 = {'blockname':'ISCINF', 'names':'iscdofs'}
witIP = {'blockname':'DAMP', 'names':'dofs','suffix':'witsuffix'}
witGAS = {'blockname':'LVDTINF', 'names':'dofs','suffix':'witsuffix'}
witIM = {'blockname':'DAMP', 'names':'dofs','suffix':'witsuffix'}
witTM = {'blockname':'OPLEV', 'names':'witdofs','suffix':'witsuffix'}
lock3top = {'blockname':'LOCK', 'names':'lockdofs'}
lock3 = {'blockname':'LOCK', 'names':'dofs'}
lockEsd = {'blockname':'LOCK', 'names':'esddofs'}
offload = {'blockname':'OFFLOAD', 'names':'isidofs'}

# Standard matrix block definitions
sa6 = {'blockname':'SENSALIGN', 'inames':'dofs',  'onames':'dofs',  'default':i6}
sa3 = {'blockname':'SENSALIGN', 'inames':'dofs',  'onames':'dofs',  'default':i3}
c2e = {'blockname':'CART2EUL', 'inames':'isichans', 'onames':'dofs'}

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
                'osemConfig' : None,
                'oldamp' : None,
                'olset' : None,
                'oldcctrl' : None,
                'olConfig' : None,
                'esdConfig' : None,
                'gasConfig' : None,
                'isidofs' : None,
                'isi' : None,
                'cart2eul' : None,
                'eul2cart' : None,
                'offload' : offload,
                'isc' : None,
                'damp' : damp3,
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
                'esdConfig' : None,
                'gasConfig' : {
                    'chans' : 'GAS',
                    'dofs' : 'GAS',
                    'inf' : {'blockname':'LVDTINF', 'names':'chans'},
                    '2eul' : None,
                    'sensalign' : None,
                    'drivealign' : None,
                    'eul2' : None,
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':{1,1,1}}}
                },
                'isidofs' : None,
                'isi' : None,
                'cart2eul' : None,
                'eul2cart' : None,
                'offload' : offload,
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
                'esdConfig' : None,
                'gasConfig' : {
                    'chans' : 'GAS',
                    'dofs' : 'GAS',
                    'inf' : {'blockname':'LVDTINF', 'names':'chans'},
                    '2eul' : None,
                    'sensalign' : None,
                    'drivealign' : None,
                    'eul2' : None,
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':{1,1,1}}}
                },
                'isidofs' : None,
                'isi' : None,
                'cart2eul' : None,
                'eul2cart' : None,
                'offload' : offload,
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
                'esdConfig' : None,
                'gasConfig' : {
                    'chans' : 'GAS',
                    'dofs' : 'GAS',
                    'inf' : {'blockname':'LVDTINF', 'names':'chans'},
                    '2eul' : None,
                    'sensalign' : None,
                    'drivealign' : None,
                    'eul2' : None,
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':{1,1,1}}}
                },
                'isidofs' : None,
                'isi' : None,
                'cart2eul' : None,
                'eul2cart' : None,
                'offload' : offload,
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
                    '2eul' : {'blockname':'OSEM2EUL','inames':'chans', 'onames':'dofs', 'default':typebp_o2e_im},
                    'eul2' : {'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 'default':map(list,zip(*typebp_o2e_im))},
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':signsIM}}
                },
                'olctrldofs' : olCtrlDofNames,
                'oldamp' : None,
                'olset' : {'blockname':'OLSET', 'names':'olctrldofs'},
                'oldcctrl' : {'blockname':'OLDCCTRL', 'names':'olctrldofs'},
                'olConfig' : None,
                'gasConfig' : None,
                'esdConfig' : None,
                'isidofs' : sixDofNames,
                'isi' : isi6,
                'isc' : None,
                'cart2eul' : c2e,
                'eul2cart' : None,
                'offload' : offload,
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
                    '2eul' : {'blockname':'OSEM2EUL','inames':'chans', 'onames':'dofs', 'default':typebp_o2e_tm},
                    'eul2' : {'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 'default':map(list,zip(*typebp_o2e_tm))},
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
                    '2eul' : {'blockname':'OPLEV_MTRX','inames':'chans', 'onames':'dofs', 'default':[[-1.,1.,1.,-1.],[-1,1.,-1.,1.],[1.,1.,1.,1.]]},
                    'full' : {'blockname':'OPLEV', 'names':'fulldofs'},
                    'sensalign' : sa3,
                    'drivealign' : None,
                    'eul2' : None,
                    'outf' : None
                },
                'gasConfig' : None,
                'esdConfig' : None,
                'isi' : None,
                'iscdofs' : threeDofNames,
                'isc' : isc3,
                'cart2eul' : None,
                'eul2cart' : None,
                'offload' : None,
                'damp' : damp3,
                'dcctrl' : None,
                'set' : None,
                'wit' : witTM,
                'esddofs' : None,
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
                'esdConfig' : None,
                'gasConfig' : {
                    'chans' : 'GAS',
                    'dofs' : 'GAS',
                    'inf' : {'blockname':'LVDTINF', 'names':'chans'},
                    '2eul' : None,
                    'sensalign' : None,
                    'drivealign' : None,
                    'eul2' : None,
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':{1,1,1}}}
                },
                'isidofs' : None,
                'isi' : None,
                'cart2eul' : None,
                'eul2cart' : None,
                'offload' : offload,
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
                'esdConfig' : None,
                'gasConfig' : {
                    'chans' : 'GAS',
                    'dofs' : 'GAS',
                    'inf' : {'blockname':'LVDTINF', 'names':'chans'},
                    '2eul' : None,
                    'sensalign' : None,
                    'drivealign' : None,
                    'eul2' : None,
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':{1,1,1}}}
                },
                'isidofs' : None,
                'isi' : None,
                'cart2eul' : None,
                'eul2cart' : None,
                'offload' : offload,
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
                    '2eul' : {'blockname':'OSEM2EUL','inames':'chans', 'onames':'dofs', 'default':typebp_o2e_im},
                    'eul2' : {'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 'default':map(list,zip(*typebp_o2e_im))},
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':signsIM}}
                },
                'oldampdofs' : olDampDofNames,
                'oldamp' : {'blockname':'OLDAMP', 'names':'oldampdofs'},
                'olConfig' : None,
                'gasConfig' : None,
                'esdConfig' : None,
                'isidofs' : sixDofNames,
                'isi' : isi6,
                'isc' : None,
                'cart2eul' : c2e,
                'eul2cart' : None,
                'offload' : offload,
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
                    '2eul' : {'blockname':'OSEM2EUL','inames':'chans', 'onames':'dofs', 'default':typebp_o2e_tm},
                    'eul2' : {'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 'default':map(list,zip(*typebp_o2e_tm))},
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
                    '2eul' : {'blockname':'OPLEV_MTRX','inames':'chans', 'onames':'dofs', 'default':[[-1.,1.,1.,-1.],[-1,1.,-1.,1.],[1.,1.,1.,1.]]},
                    'full' : {'blockname':'OPLEV', 'names':'fulldofs'},
                    'sensalign' : sa3,
                    'drivealign' : None,
                    'eul2' : None,
                    'outf' : None
                },
                'gasConfig' : None,
                'esdConfig' : None,
                'isi' : None,
                'iscdofs' : threeDofNames,
                'isc' : isc3,
                'cart2eul' : None,
                'eul2cart' : None,
                'offload' : None,
                'damp' : damp3,
                'wit' : None,
                'esddofs' : None,
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
                    '2eul' : {'blockname':'OSEM2EUL','inames':'chans', 'onames':'dofs', 'default':typec_o2e_m1},
                    'eul2' : {'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 'default':map(list,zip(*typec_o2e_m1))},
                    'outf' : {'blockname':'COILOUTF', 'names':'chans', 'default':{'gains':signsM1}}
                },
                'oldampdofs' : olDampDofNames,
                'oldamp' : None,
                'olConfig' : None,
                'gasConfig' : None,
                'esdConfig' : None,
                'isidofs' : sixDofNames,
                'isi' : isi6,
                'isc' : None,
                'cart2eul' : c2e,
                'eul2cart' : None,
                'offload' : offload,
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
                    '2eul' : {'blockname':'OSEM2EUL','inames':'chans', 'onames':'dofs', 'default':typec_o2e_tm},
                    'eul2' : {'blockname':'EUL2OSEM','inames':'dofs', 'onames':'chans', 'default':map(list,zip(*typec_o2e_tm))},
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
                    '2eul' : {'blockname':'OPLEV_MTRX','inames':'chans', 'onames':'dofs', 'default':[[-1.,1.,1.,-1.],[-1,1.,-1.,1.],[1.,1.,1.,1.]]},
                    'full' : {'blockname':'OPLEV', 'names':'fulldofs'},
                    'sensalign' : sa3,
                    'drivealign' : None,
                    'eul2' : None,
                    'outf' : None
                },
                'gasConfig' : None,
                'esdConfig' : None,
                'isi' : None,
                'iscdofs' : threeDofNames,
                'isc' : isc3,
                'cart2eul' : None,
                'eul2cart' : None,
                'offload' : None,
                'damp' : damp3,
                'wit' : None,
                'esddofs' : None,
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
    
    notimplemented = [fn for fn in callableVisFunctions if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableVisFunctions need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableOpticSwitchWriteCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableOpticSwitchWriteCommands need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableOpticSwitchReadCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableOpticSwitchReadCommands need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableLevelNameFunctions if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelNameFunctions need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableLevelDataFunctions if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelDataFunctions need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableLevelMatrixFunctions if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelMatrixFunctions need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableLevelMatrixReadCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelMatrixReadCommands need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableLevelMatrixWriteCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelMatrixWriteCommands need implementing: '+str(notimplemented))
    
    notimplemented = [fn for fn in callableOpticSwitchWriteCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableOpticSwitchWriteCommands need implementing: '+str(notimplemented))

    if notimplemented !=[]:
        print('Some methods declared in callableLevelFilterSwitchReadCommands need implementing: '+str(notimplemented))

    notimplemented = [fn for fn in callableLevelFilterEnableCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelFilterEnableCommands need implementing: '+str(notimplemented))

    notimplemented = [fn for fn in callableLevelFilterWriteCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelFilterWriteCommands need implementing: '+str(notimplemented))

    notimplemented = [fn for fn in callableLevelFilterReadCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelFilterReadCommands need implementing: '+str(notimplemented))

    notimplemented = [fn for fn in callableLevelFilterOutputReadCommands if not hasattr(Vis,fn)]
    if notimplemented !=[]:
        print('Some methods declared in callableLevelFilterOutputReadCommands need implementing: '+str(notimplemented))

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

