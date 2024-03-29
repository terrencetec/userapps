# -*- mode: python; tab-width: 4; indent-tabs-mode: nil -*-
"""
VIS base guardian module

This defines the behavior for all suspensions.

"""
# FIXME: use new ezca.is_ramping methods when available,
# instead of using a timer

##################################################

from guardian import GuardState, GuardStateDecorator
from guardian.ligopath import userapps_path
import sustools
import susconst

##################################################

__,OPTIC = SYSTEM.split('_')
# sus = sustools.Sus(optic)

##################################################

# check for tripped WDs
def is_tripped(susobj):
    trippedwds = susobj.trippedWds()
    #trippedwds = susobj.trippedWds(susobj.levels()[0] + ['USER'])

    # if we're not tripped, return immediately
    if not trippedwds:
        return False

    # notify the user which WDs are tripped
    notify("WD tripped! operator reset required: %s" % (','.join(trippedwds)))

    # FIXME: check for usual suspects and inform operator with
    # appropriate log messages

    return True

# check for tripped WDs
def is_aux_tripped(susobj):
    trippedwds = susobj.trippedWds(susobj.levels()[1:])

    # if we're not tripped, return immediately
    if not trippedwds:
        return False

    # notify the user which WDs are tripped
    notify("AUX WD tripped! operator reset required: %s" % (','.join(trippedwds)))

    # FIXME: check for usual suspects and inform operator with
    # appropriate log messages

    return True

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
    log('BURT RESTORE SAFE: %s', safepath)
    ezca.burtwb(safepath)

def ramp_align_offsets(susobj, onoff, rampTime):
    log('Ramping alignment offsets %s: ramp=%s' % (onoff, rampTime))
    susobj.alignRampWrite(rampTime)
    susobj.alignOffsetSwitchWrite(onoff)

def ramp_isc_gains(susobj, gain, rampTime):
    log('Ramping ISC/ASC gains: gain=%s, ramp=%s' % (gain, rampTime))
    susobj.iscRampWrite(rampTime)
    susobj.iscGainWrite(gain)

def reset_safe(susobj, rampTime):
    """reset suspension back to SAFE state"""
    # FIXME: burt safe restore is not ready yet
    # burt_restore_safe()
    log('Ramping down ISC inputs')
    ramp_isc_gains(susobj, 0, rampTime)
    log('Ramping down ALIGN offsets')
    ramp_align_offsets(susobj, 'OFF', rampTime)
    log('Turning off DAMP outputs')
    susobj.dampOutputSwitchWrite('OFF')
    log('Turning off OPLEV damping outputs')
    susobj.olDampOutputSwitchWrite('OFF')
    # NOTE: need to wait for this ramp, which needs to be done
    # external to this function

def olDamp_in_use(susobj):
    """True if there are oplevs and the ol damping loops are set to be used."""
    return susobj.olPvs() and susconst.use_olDamp

def olDamp_engaged(susobj):
    """True if any oplev damping loop output is engaged."""
    return any([ezca.get_LIGOFilter(s).is_engaged('OUTPUT') for s in susobj.olDampPvs()])

def set_alignment(susobj, offsetType, rampTime):
    """Set alignment offsets and engage outputs"""
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
    ezca.burtwb(asnappath)

    susobj.alignOutputSwitchWrite('ON')
    ramp_align_offsets(susobj, 'ON', rampTime)

def is_aligned(susobj,offsetType):
    """Check optic alignment status

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

##################################################
# STATE DECORATORS
##################################################

class watchdog_check(GuardStateDecorator):
    def pre_exec(self):
        if is_tripped(sustools.Sus(ezca)):
            return 'TRIPPED'

# FIXME: add more decorator checks:
# masterswitch_check
# damping_loops_check
# alignment_offsets_off

def alignment_check(alignment):
    class alignment_check_decorator(GuardStateDecorator):
        def pre_exec(self):
            if not is_aligned(sustools.Sus(ezca), alignment):
                notify('Alignment not enabled or offsets have changed from those saved.')
    return alignment_check_decorator

##################################################
# STATE GENERATORS
##################################################

def get_idle_state():
    class IDLE(GuardState):

        @watchdog_check
        def main(self):
            self.susobj = sustools.Sus(ezca)
            self.ol_shut_off = False

        @watchdog_check
        def run(self):
            if not olDamp_in_use(self.susobj):
                return True

            # OPLEV damping: for optics that have optical levers:
            # Check OpLev Sum and turn off OpLev damping if below
            # threshold (i.e. beam moved off QPD).
            # buffer for last couple of seconds of oplev sums

            # else if servo on
            if olDamp_engaged(self.susobj):
                # read the current values
                [pit, yaw, olsum] = self.susobj.olRead()

                # if sum below threshold...
                if abs(olsum) <= susconst.ol_off_threshold:
                    # shut off the servo
                    log('Optical lever sum dropped below off_threshold of: %d' % susconst.ol_off_threshold)
                    self.susobj.olDampOutputSwitchWrite('OFF')
                    self.ol_shut_off = True
                else:
                    self.ol_shut_off = False

            # notify if the servo was shut off
            elif self.ol_shut_off:
                notify('OPLEV damping shut off, sum fell below threshold')

            return True

    return IDLE

def get_aligning_state(alignment, isc_gain):
    class ALIGNING_STATE(GuardState):
        request = False

        @watchdog_check
        def main(self):
            susobj = sustools.Sus(ezca)

            ramp_align_offsets(susobj, 'ON', susconst.rampTime)

            ramp_isc_gains(susobj, isc_gain, susconst.rampTime)

            # FIXME: use new ezca.is_ramping methods when available,
            # instead of using a timer
            log('Waiting %ds for ramps...' % susconst.rampTime)
            self.timer['ramp'] = susconst.rampTime

        @watchdog_check
        def run(self):
            if not self.timer['ramp']:
                return

            return True

    return ALIGNING_STATE

def get_aligned_state(alignment, isc_gain):
    class ALIGNED_STATE(GuardState):
        @watchdog_check
        @alignment_check(alignment) 
        def main(self):
            susobj = sustools.Sus(ezca)

            # we do this here so that you can re-request this state and
            # reset the alignements if they've changed
            if not is_aligned(susobj, alignment):
                set_alignment(susobj, alignment, susconst.rampTime)

        @watchdog_check
        @alignment_check(alignment)
        def run(self):
            return True

    return ALIGNED_STATE
    
##################################################
# STATES
##################################################

request = 'ALIGNED'
nominal = 'ALIGNED'

class INIT(GuardState):
    @watchdog_check
    def main(self):
        self.susobj = sustools.Sus(ezca)

        # FIXME: this only identifies that the alignment offsets are
        # active, but does not distinguish ALIGNED from MISALIGNED, or
        # check for damping loops already engaged
        if self.susobj.masterSwitchRead():
            if all(self.susobj.dampOutputSwitchRead()):

                if all(self.susobj.alignOffsetSwitchRead()):
                    return 'ALIGNED'

                else:
                    return 'DAMPED'

            else:
                log('Resetting DAMPED...')
                # make sure the alignment offsets aren't on
                ramp_align_offsets(self.susobj, 'OFF', susconst.rampTime)
                # FIXME: turn on the OLDAMP loops here since we don't
                # have a way to check if they're on already
                if olDamp_in_use(self.susobj):
                    self.susobj.olDampOutputSwitchWrite('ON')
                self.timer['ramp'] = susconst.rampTime
                self.return_state = 'DAMPED'

        else:
            log('Resetting SAFE...')
            reset_safe(self.susobj, susconst.rampTime)
            self.timer['ramp'] = susconst.rampTime
            self.return_state = 'SAFE'

        log("next state: %s" % self.return_state)

    @watchdog_check
    def run(self):
        if not self.timer['ramp']:
            return
        if self.return_state == 'SAFE':
            log('Turning off Master Switch')
            self.susobj.masterSwitchWrite('OFF')
        return self.return_state


class TRIPPED(GuardState):
    index = 1
    redirect = False
    request = False

    def main(self):
        self.susobj = sustools.Sus(ezca)

        # for reporting trip status
        is_tripped(self.susobj)

        reset_safe(self.susobj, susconst.rampTime)

        log('Waiting %ds for ramps...' % susconst.rampTime)
        self.timer['ramp'] = susconst.rampTime
        self.switch_off = False

    def run(self):
        # for reporting trip status
        is_tripped(self.susobj)

pppp        if self.timer['ramp'] and not self.switch_off:
            log('Turning off Master Switch')
            self.susobj.masterSwitchWrite('OFF')
            self.switch_off = True

        # finish the state if we're no longer tripped
        if not is_tripped(self.susobj):
            return True


class RESET(GuardState):
    index = 9
    goto = True
    request = False

    @watchdog_check
    def main(self):
        self.susobj = sustools.Sus(ezca)

        reset_safe(self.susobj, susconst.rampTime)

        # FIXME: use new ezca.is_ramping methods when available,
        # instead of using a timer
        log('Waiting %ds for ramps...' % susconst.rampTime)
        self.timer['ramp'] = susconst.rampTime

    @watchdog_check
    def run(self):
        if not self.timer['ramp']:
            return

        log('Turning off Master Switch')
        self.susobj.masterSwitchWrite('OFF')

        return True


SAFE = get_idle_state()
SAFE.index = 10


class MASTERSWITCH_ON(GuardState):
    index = 15
    request = False

    @watchdog_check
    def main(self):
        log('Turning On Master Switch')
        sustools.Sus(ezca).masterSwitchWrite('ON')
        return True


class ENGAGE_DAMPING(GuardState):
    index = 40
    request = False

    @watchdog_check
    def main(self):
        susobj = sustools.Sus(ezca)

        log('Turning on damping outputs')
        susobj.dampOutputSwitchWrite('ON')
        if olDamp_in_use(susobj):
            log('Turning on OL damping outputs')
            susobj.olDampOutputSwitchWrite('ON')

        return True


DAMPED = get_idle_state()
DAMPED.index = 50


ALIGNING = get_aligning_state('aligned', isc_gain=1)
ALIGNING.index = 90
#ALIGNED = get_aligned_state('aligned', isc_gain=1)
# FIXME: this needs to check that the alignment offset is still on
ALIGNED = get_idle_state()
ALIGNED.index = 100


# MISALIGNING = get_aligning_state('misaligned', isc_gain=0)
# MISALIGNED = get_aligned_state('misaligned', isc_gain=0)


class UNALIGNING(GuardState):
    index = 99
    request = False

    @watchdog_check
    def main(self):
        susobj = sustools.Sus(ezca)

        ramp_align_offsets(susobj, 'OFF', susconst.rampTime)
        ramp_isc_gains(susobj, 0, susconst.rampTime)

        # FIXME: use new ezca.is_ramping methods when available,
        # instead of using a timer
        log('Waiting %ds for ramps...' % susconst.rampTime)
        self.timer['ramp'] = susconst.rampTime

    @watchdog_check
    def run(self):
        if not self.timer['ramp']:
            return

        return True


##################################################
# EDGES
# these are the directed edges that connect the states
# ('FROM', 'TO')

edges = [
    ('TRIPPED','SAFE'),
    ('INIT','SAFE'),
    ('RESET','SAFE'),
    ('SAFE','MASTERSWITCH_ON'),
    ('MASTERSWITCH_ON','ENGAGE_DAMPING'),
    ('ENGAGE_DAMPING','DAMPED'),
    ('DAMPED', 'ALIGNING'),
    ('ALIGNING', 'ALIGNED'),
    ('ALIGNED', 'UNALIGNING'),
    # ('ALIGNED', 'MISALIGNING'),
    # ('DAMPED', 'MISALIGNING'),
    # ('MISALIGNING', 'MISALIGNED'),
    # ('MISALIGNED', 'ALIGNING'),
    # ('MISALIGNED', 'UNALIGNING'),
    ('UNALIGNING', 'DAMPED'),
    ]

##################################################
# SVN $Id$
# $HeadURL$
##################################################
