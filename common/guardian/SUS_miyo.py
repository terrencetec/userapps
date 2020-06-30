#
#! coding:utf-8

from guardian import GuardState, GuardStateDecorator
from guardian.ligopath import userapps_path
import sustools
import susconst
from logging import log

IFO,OPTIC = "K1","BS"



"""
    Read snapshot
"""
#from burt import readBurt
#channel_data = readBurt()




"""
    Write snapshot
"""
def burt_restore_safe():
    # FIXME: this function is not ready yet for use yet.  The
    # ezca.burtwb() takes far too long to execute, and is not robust
    # (doesn't handle certain string values yet)
    return


    ifo = IFO.lower()
    optic = OPTIC.lower()

    # generate the path to the offset snapshot file
    sfile = '%ssus%s_safe.snap' % (ifo, optic)
    # The userapps_path() function would return the path relative to
    # the USERAPPS_PATH environment variable.  Guardian might be
    # pointing to its own checkout of USERAPPS.  However, we want the
    # offsets to be pulled from the most uptodate values, which are in
    # the main USERAPPS checkout in /opt/rtcds/userapps
    # FIXME: maybe change this to point to local checkout during science
    safepath = userapps_path('sus', ifo, 'burtfiles', sfile)
    ezca.burtwb(safepath)
    print "burtwb %s!"%asnappath

    
"""
    Set alignment offsets and engage outputs
"""
def set_alignment(susobj, offsetType, rampTime):

    ifo = IFO.lower()
    optic = OPTIC.lower()

    # generate the path to the offset snapshot file
    sfile = '%ssus%s_%s_offsets.snap' % (ifo, optic, offsetType)
    # The userapps_path() function would return the path relative to
    # the USERAPPS_PATH environment variable.  Guardian might be
    # pointing to its own checkout of USERAPPS.  However, we want the
    # offsets to be pulled from the most uptodate values, which are in
    # the main USERAPPS checkout in /opt/rtcds/userapps
    # FIXME: maybe change this to point to local checkout during science
    asnappath = userapps_path('sus', ifo, 'burtfiles', sfile)

    offsetType = offsetType.upper()
    log('Loading %s offsets: %s' % (offsetType, asnappath))
    #ezca.burtwb(asnappath)
    print "burtwb %s!"%asnappath

    susobj.alignOutputSwitchWrite('ON')
    ramp_align_offsets(susobj, 'ON', rampTime)



    
"""
    Check optic alignment status
"""    
def is_aligned(susobj,offsetType):
    """
    * current offsets match saved
    * are the offsets enabled
    * are the offsets output switches enabled
    Returns True if the 3 conditions are matched
    """
    ifo = IFO.lower()
    optic = OPTIC.lower()

    from burt import readBurt
    # generate the path to the offset snapshot file
    sfile = '%ssus%s_%s_offsets.snap' % (ifo, optic, offsetType)
    # The userapps_path() function would return the path relative to
    # the USERAPPS_PATH environment variable.  Guardian might be
    # pointing to its own checkout of USERAPPS.  However, we want the
    # offsets to be pulled from the most uptodate values, which are in
    # the main USERAPPS checkout in /opt/rtcds/userapps
    # FIXME: maybe change this to point to local checkout during science
    asnappath = userapps_path('sus', ifo, 'burtfiles', sfile)
    goal = readBurt(asnappath)
    current = susobj.alignOffsetRead(pair='both', withprefix='full')
    if set(goal.keys())!=set([c[0] for c in current]):
        log('Defective alignment channel list returned by burtRead (maybe settings being written?)')
        return False
    offsetsmatch = [abs(c[1]-goal[c[0]])<1E-10 for c in current] 
    offsetsenabled = susobj.alignOffsetSwitchRead()
    outputsenabled = susobj.alignOutputSwitchRead()

    return all(offsetsenabled) and all(outputsenabled) and all(offsetsmatch)



    
if __name__=="__main__":
    burt_restore_safe()
    
