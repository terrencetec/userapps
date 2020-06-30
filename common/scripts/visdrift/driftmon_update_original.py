#!/usr/bin/env python

"""aLIGO Suspension Drift Monitor 2

updated Nov 23, 2014   RXA
---fold in default command line args; we don't want to have a bunch of site specific junk in the MEDM screen

---run it in the past based on the user input GPS time, rather than default to 'now - latency'

---use fixed numbers for allowable drift rather than calculate based on recent fluctuations

---replaced 'verbose' with python logging package

---using fixed tolerances instead of statistical stdev calculations

---added OMC suspension to the list

---no longer writes to the STD or MEAN epics fields

updated Jan 30, 2015   TDA

-- cleaned up old options that no longer have use

-- added dictionaries for defining fixed limits for each optic

-- arbitrarily changed version from 0.1 to 0.2

"""

__author__ = 'Thomas Abbott <thomas.abbott@ligo.org>'
__date__ = 'January 2015'
__version__ = '0.2'

import math
import os
import optparse
import sys

import nds2
import epics

import logging

ALL_OPTICS = ['MC1', 'MC2', 'MC3', 'PRM', 'PR2', 'PR3', 'SRM', 'SR2', 'SR3',
              'ITMX', 'ITMY', 'ETMX', 'ETMY','BS', 'TMSX', 'TMSY','IM1','IM2',
              'IM3','IM4','RM1','RM2','OM1','OM2','OM3', 'OMC']
STAGE = {'MC1': 'M1',
         'MC2': 'M1',
         'MC3': 'M1',
         'PRM': 'M1',
         'PR2': 'M1',
         'PR3': 'M1',
         'SRM': 'M1',
         'SR2': 'M1',
         'SR3': 'M1',
         'ITMX': 'M0',
         'ITMY': 'M0',
         'ETMX': 'M0',
         'ETMY': 'M0',
         'BS': 'M1',
         'TMSX': 'M1',
         'TMSY': 'M1',
         'IM1': 'M1',
         'IM2': 'M1',
         'IM3': 'M1',
         'IM4': 'M1',
         'RM1': 'M1',
         'RM2': 'M1',
         'OM1': 'M1',
         'OM2': 'M1',
         'OM3': 'M1',
         'OMC': 'M1',
         }

DEGREES_OF_FREEDOM1 = ['P', 'Y', 'V']
DEGREES_OF_FREEDOM2 = ['P', 'Y', 'L']

DOF = {'MC1': DEGREES_OF_FREEDOM1,
         'MC2': DEGREES_OF_FREEDOM1,
         'MC3': DEGREES_OF_FREEDOM1,
         'PRM': DEGREES_OF_FREEDOM1,
         'PR2': DEGREES_OF_FREEDOM1,
         'PR3': DEGREES_OF_FREEDOM1,
         'SRM': DEGREES_OF_FREEDOM1,
         'SR2': DEGREES_OF_FREEDOM1,
         'SR3': DEGREES_OF_FREEDOM1,
         'ITMX': DEGREES_OF_FREEDOM1,
         'ITMY': DEGREES_OF_FREEDOM1,
         'ETMX': DEGREES_OF_FREEDOM1,
         'ETMY': DEGREES_OF_FREEDOM1,
         'BS': DEGREES_OF_FREEDOM1,
         'TMSX': DEGREES_OF_FREEDOM1,
         'TMSY': DEGREES_OF_FREEDOM1,
         'OMC': DEGREES_OF_FREEDOM1,
         'IM1': DEGREES_OF_FREEDOM2,
         'IM2': DEGREES_OF_FREEDOM2,
         'IM3': DEGREES_OF_FREEDOM2,
         'IM4': DEGREES_OF_FREEDOM2,
         'RM1': DEGREES_OF_FREEDOM2,
         'RM2': DEGREES_OF_FREEDOM2,
         'OM1': DEGREES_OF_FREEDOM2,
         'OM2': DEGREES_OF_FREEDOM2,
         'OM3': DEGREES_OF_FREEDOM2,
         }


CHANNEL = "%s:SUS-%s_%s_DAMP_%s_INMON"

SEVERITY = {'HHSV': 'MAJOR',
            'HSV': 'MINOR',
            'LSV': 'MINOR',
            'LLSV': 'MAJOR',
            }

########## TUNE THRESHOLDS HERE ###########
# yellow thresholds = mean +- yellow_factor * BOUND value
# red thresholds = mean +- red_factor * BOUND value


yellow_factor = 1
red_factor = 5

BOUND_MC1 = {'P' : 20, 'V' : 10, 'Y' : 10}
BOUND_MC2 = {'P' : 20, 'V' : 10, 'Y' : 10}
BOUND_MC3 = {'P' : 20, 'V' : 15 , 'Y' : 10}
BOUND_PRM = {'P' : 20, 'V' : 15, 'Y' : 15}
BOUND_PR2 = {'P' : 30, 'V' : 15, 'Y' : 25}
BOUND_PR3 = {'P' : 5, 'V' : 15 , 'Y' : 5}
BOUND_SRM = {'P' : 20, 'V' : 15, 'Y' : 50}
BOUND_SR2 = {'P' : 20, 'V' : 25, 'Y' : 30}
BOUND_SR3 = {'P' : 5, 'V' : 15 , 'Y' : 5}
BOUND_ITMX = {'P' : 5, 'V' : 20, 'Y' : 5}
BOUND_ITMY = {'P' : 5, 'V' : 20, 'Y' : 5}
BOUND_ETMX = {'P' : 5, 'V' : 20 , 'Y' : 5}
BOUND_ETMY = {'P' : 5, 'V' : 20 , 'Y' : 5}
BOUND_BS = {'P' : 20, 'V' : 20, 'Y' : 5}
BOUND_TMSX = {'P' : 10, 'V' : 20 , 'Y' : 5}
BOUND_TMSY = {'P' : 10, 'V' : 20 , 'Y' : 5}
BOUND_RM1 = {'P' : 100, 'L' : 2 , 'Y' : 100}
BOUND_RM2 = {'P' : 100, 'L' : 2 , 'Y' : 100}
BOUND_IM1 = {'P' : 10, 'L' : 2 , 'Y' : 5}
BOUND_IM2 = {'P' : 10, 'L' : 2 , 'Y' : 5}
BOUND_IM3 = {'P' : 10, 'L' : 2 , 'Y' : 5}
BOUND_IM4 = {'P' : 10, 'L' : 2 , 'Y' : 10}
BOUND_OM1 = {'P' : 50, 'L' : 2 , 'Y' : 50}
BOUND_OM2 = {'P' : 50, 'L' : 2 , 'Y' : 50}
BOUND_OM3 = {'P' : 50, 'L' : 2 , 'Y' : 50}
BOUND_OMC = {'P' : 15, 'V' : 2 , 'Y' : 10}
###########################################


BOUND_OPTIC = {'MC1' : BOUND_MC1,
        'MC2' : BOUND_MC2,
        'MC3' : BOUND_MC3,
        'PRM' : BOUND_PRM,
        'PR2' : BOUND_PR2,
        'PR3' : BOUND_PR3,
        'SRM' : BOUND_SRM,
        'SR2' : BOUND_SR2,
        'SR3' : BOUND_SR3,
        'ITMX' : BOUND_ITMX,
        'ITMY' : BOUND_ITMY,
        'ETMX' : BOUND_ETMX,
        'ETMY' : BOUND_ETMY,
        'BS' : BOUND_BS,
        'TMSX' : BOUND_TMSX,
        'TMSY' : BOUND_TMSY,
        'RM1' : BOUND_RM1,
        'RM2' : BOUND_RM2,
        'IM1' : BOUND_IM1,
        'IM2' : BOUND_IM2,
        'IM3' : BOUND_IM3,
        'IM4' : BOUND_IM4,
        'OM1' : BOUND_OM1,
        'OM2' : BOUND_OM2,
        'OM3' : BOUND_OM3,
        'OMC' : BOUND_OMC
        }

# -----------------------------------------------------------------------------
# Parse command-line

usage = "%s ifo [OPTIONS]" % os.path.basename(__file__)

parser = optparse.OptionParser(description=__doc__, usage=usage,
                               epilog="Please direct all questions/comments "
                                      "to %s" % __author__)


ndsargs = parser.add_option_group('NDS options')
ndsargs.add_option('-H', '--host', action='store', type='string',
                   help="NDS server hostname, default: site nds1 host")
ndsargs.add_option('-P', '--port', action='store', type='int',
                   default=8088, help="NDS server port, default: %default")
ndsargs.add_option('-l', '--latency', action='store', type='float',
                   default=30,
                   help="NDS data access latency, default: %default")
ndsargs.add_option('--starttime', action='store', type='float',
                   help="GPS start time [s]")


opargs = parser.add_option_group("Optic choices",
                                 "Choose which optics to update, --all is "
                                 "default, otherwise specify each optic "
                                 "individually.")
opargs.add_option("-a", "--all", action="store_true", default=True,
                  help="Update all optics, default: %default")
for optic in ALL_OPTICS:
    opargs.add_option('--%s' % optic.lower(), action='store_true',
                      default=False,
                      help=("Update {0}, default: %default "
                            "(unless --all)".format(optic)))

datargs = parser.add_option_group("Data choices",
                                  "Choose how much data to use in determining "
                                  "standard deviations.")
datargs.add_option('-d', '--duration', action='store', type='float',
                   help="Duration of data used for threshold determination")
datargs.add_option('--minor-stdev', action='store', type='int', default=1,
                   help="number of standard deviations for minor threshold "
                        "(yellow)")
datargs.add_option('--major-stdev', action='store', type='int', default=2,
                   help="number of standard deviations for major threshold "
                        "(red)")

epicsargs = parser.add_option_group("EPICS options")
epicsargs.add_option("-s", "--setup-epics", action='store', default=False,
                     help="Set EPICS alarm severities, only needs to be "
                          "done once on each system")

opts, args = parser.parse_args()

# parse arguments
if len(args) != 1:
    parser.error("Must give IFO prefix as argument")
ifo = args[0]

# set NDS server default
if not opts.host:
    opts.host = '%snds1' % ifo[:2].lower()

# parse optics
if any(getattr(opts, optic.lower()) for optic in ALL_OPTICS):
    optics = []
    for optic in ALL_OPTICS:
        if getattr(opts, optic.lower()):
            optics.append(optic)
else:
    optics = ALL_OPTICS

# -----------------------------------------------------------------------------
# set up alarm severities (should only need to run this section once) #
if 1:
    for optic in optics:
        stage = STAGE[optic]
        DEGREES_OF_FREEDOM = DOF[optic]
        for dof in DEGREES_OF_FREEDOM:
            channel = CHANNEL % (ifo, optic, stage, dof)
            for sev,val in SEVERITY.iteritems():
                epics.caput('%s.%s' % (channel, sev), val)

# -----------------------------------------------------------------------------
# Read optic data, get thresholds, and set in EPICS

# set GPS times
if not opts.starttime:
        t = raw_input("Enter GPS start time in seconds: ")
        opts.starttime = float(t)
        gpsstart = opts.starttime

if not opts.duration:
     t = raw_input("Enter averaging duration in seconds: ")
     opts.duration = float(t)

# setup location of DEBUG log file (should be different for each site?)
optic_name = "ALL"

for optic in ALL_OPTICS:
        if getattr(opts, optic.lower()):
            optic_name = optic

log_dir = "/opt/rtcds/llo/l1/log/l1susdrift/"
log_filename = "%sSUSDRIFT_%s_%s-%s.log" % (log_dir,optic_name,int(opts.starttime),int(opts.duration))
logging.basicConfig(filename=log_filename, level=logging.DEBUG)

def nds_fetch_old_data(connection, channel, start, end):
    """Fetch data from NDS using the standard fetch method
    """
    return connection.fetch(int(math.floor(start)), int(math.ceil(end)),
                            [channel])[0]


logging.info("Start time: %s" % opts.starttime)
logging.info("Duration: %s" % opts.duration)

# open connection to NDS2
connection = nds2.connection(opts.host, opts.port)
logging.info("Connected to NDS host %s:%d" % (opts.host, opts.port))

for optic in optics:
    stage = STAGE[optic]
    DEGREES_OF_FREEDOM = DOF[optic]
    logging.info("Updating %s..." % optic)
    for dof in DEGREES_OF_FREEDOM:
	
        bound_optic = BOUND_OPTIC[optic]
        bound = bound_optic[dof]

        logging.info("    %s: " % dof)
        channel = CHANNEL % (ifo, optic, stage, dof)
        buffer_ = nds_fetch_old_data(connection, channel, gpsstart, gpsstart+opts.duration)
        data = buffer_.data

#        logging.info("%.2fs read from NDS, " % opts.duration)

        mean = data.mean()

        yellow = yellow_factor*bound
        red = red_factor*bound

        # caput mean value
        # meanchannel = "%s_MEAN" % channel
        # epics.caput(meanchannel, mean)

        # caput STD value
        # stdchannel = '%s_STD' % channel
        # epics.caput(stdchannel, std)

        # caput thresholds
        for thresh,dev in zip(['HIHI', 'HIGH', 'LOW', 'LOLO'],
                              [red,  yellow, -yellow, -red]):
            epics.caput('%s.%s' % (channel, thresh), mean+dev)
            print('    %s.%s: %s' % (channel, thresh, mean+dev))
            logging.info('    %s.%s: %s' % (channel, thresh, mean+dev))
        print("")

logging.info("Update completed successfully")

print("All logging info saved into %s" % log_filename)
raw_input("Press Enter to close window...")


#EOF
