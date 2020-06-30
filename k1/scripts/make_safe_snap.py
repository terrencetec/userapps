#!/usr/bin/env python

# This script takes the name of a suspension, e.g., PR3, and makes a safe.snap file for it.
# First it uses BURT to save the current state.
# Then it uses vistools.py to set the suspension to the safe state. 
# Finally it restores the saved state.

# Currently all snaps are saved to /opt/rtcds/userapps/release/vis/k1guardian/. See the function
# snap_file_path() to change this.

import os
import sys
import argparse
import tempfile
import subprocess

import vistools

userapps = '/opt/rtcds/userapps/release/'
IFO = os.getenv('IFO')
ifo = IFO.lower()
SITE = os.getenv('SITE')
site = SITE.lower()
dorw = 2
verbose=False

## Goal is to generate commands like the following

# burtrb -f /opt/rtcds/kamioka/k1/target/k1vispr3/k1vispr3epics/autoBurt.req -o
#  /opt/rtcds/userapps/release/vis/k1/burtfiles/k1vispr3_safe.snap -l /tmp/controls_1130117_143746_0.read.log -v

# burtwb -f /opt/rtcds/userapps/release/vis/k1/burtfiles/k1vispr3_scripttmp.snap -l 
#  /tmp/controls.write.log -o /tmp/controls.nowrite.snap -v

########################################
def modelName(optic):
    return ifo+'vis'+optic

def req_file_path(optic):
    return os.path.join('/opt/rtcds',site,ifo,'target',modelName(optic),modelName(optic)+'epics')

def snap_file_path(optic):
#    return os.path.join(userapps, 'vis', ifo, 'burtfiles') 
    return os.path.join(userapps, 'vis', ifo, 'guardian') # FIXME temporary only

def make_safe_snap(optic):
    print >>sys.stderr, "saving %s..." % (optic)

    vis = vistools.Vis(optic)

    reqfiledir = req_file_path(optic)
    reqfile = os.path.join(reqfiledir,'autoBurt.req')
    snapfiledir = snap_file_path(optic)
    snapfile = os.path.join(snapfiledir,modelName(optic)+'_safe.snap')
    workfile = os.path.join(snapfiledir,modelName(optic)+'_scripttmp.snap')

    # wrap further stuff in a try/except to catch any errors and cleanup appropriately
    #subprocess.call(['echo', 'req file:', reqfile])
    #subprocess.call(['echo', 'snap file:', snapfile])
    #subprocess.call(['echo', 'work file:', workfile])

    # make backup of current state
    print >>sys.stderr, 'Backing up current of %s to %s...' % (optic,workfile)
    subprocess.call(['burtrb', '-f', reqfile, '-o', workfile, '-l','/tmp/controls.read.log', '-v'])
    # set suspension to safe state
    print >>sys.stderr, 'Setting %s to safe state...' % (optic)
    vis.commSwitchWrite('OFF',verbose=verbose,dorw=dorw) # commissioning switch off
    vis.masterSwitchWrite('OFF',verbose=verbose,dorw=dorw) # master switch off
    vis.dampOutputSwitchWrite('OFF',verbose=verbose,dorw=dorw) # damping outputs off
    vis.dampInputSwitchWrite('ON',verbose=verbose,dorw=dorw) # should always be on
    vis.testOutputSwitchWrite('OFF',verbose=verbose,dorw=dorw) # test outputs off
    vis.testInputSwitchWrite('ON',verbose=verbose,dorw=dorw) # should always be on
    vis.lockOutputSwitchWrite('OFF',verbose=verbose,dorw=dorw) # lock outputs off
    vis.lockInputSwitchWrite('ON',verbose=verbose,dorw=dorw) # should always be on
    vis.olDampOutputSwitchWrite('OFF',verbose=verbose,dorw=dorw) # lock outputs off
    vis.olDampInputSwitchWrite('ON',verbose=verbose,dorw=dorw) # should always be on
    vis.ditherOutputSwitchWrite('OFF',verbose=verbose,dorw=dorw) # lock outputs off
    vis.ditherInputSwitchWrite('ON',verbose=verbose,dorw=dorw) # should always be on
    vis.alignOffsetSwitchWrite('OFF',verbose=verbose,dorw=dorw) # lock outputs off
    # make safe.snap
    print >>sys.stderr, 'Making safe.snap for %s in %s...' % (optic, snapfile)
    subprocess.call(['burtrb', '-f', reqfile, '-o', snapfile, '-l','/tmp/controls.read.log', '-v'])
    # restore initial state
    print >>sys.stderr, 'Restoring initial state of %s...' % (optic)
    subprocess.call(['burtwb', '-f', workfile, '-l', '/tmp/controls.write.log', '-o', '/tmp/controls.nowrite.log','-v'])
    print >>sys.stderr, 'Deleting temp file...'
    subprocess.call(['rm',workfile])

########################################

if __name__ == '__main__':

    parser = argparse.ArgumentParser(epilog='If no options are specified "aligned" positions are saved.')

    parser.add_argument('optic', type=str, nargs='+',
                        help="optic name (e.g. 'PR2', 'ETMX')")

    args = parser.parse_args()

 
    # execute command for optics
    for optic in args.optic:
        optic = optic.lower()
        make_safe_snap(optic)


