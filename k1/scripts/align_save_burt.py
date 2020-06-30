#!/usr/bin/env python

# This script takes the name of a suspension, e.g., PR3, and uses BURT to save the alignment offsets
# in a file with a name like k1vispr3_aligned_offsets.snap. By default the offsets are assumed to be
# for the ALIGNED state, and the file has "aligned" in the name. The -a, -m and -t switches support
# other states. The -p switch previews the path where the file will be saved. 
# The -v switch views the currently saved offsets.

# Currently all snaps are saved to /opt/rtcds/userapps/release/vis/k1guardian/. See the function
# snap_file_path() to change this.

import os
import sys
import argparse
import tempfile
import subprocess

import vistools

userapps = '/opt/rtcds/userapps/release/'
ifo = os.getenv('IFO').lower()

########################################

def snap_file_path(atype, optic):
    sfile = '%svis%s_%s_offsets.snap' % (ifo, optic, atype)
#    return os.path.join(userapps, 'vis', ifo, 'burtfiles', sfile) 
    return os.path.join(userapps, 'vis', ifo, 'guardian', sfile) 

def make_snap(atype, optic):
    print >>sys.stderr, "saving %s %s..." % (atype, optic)

    vis = vistools.Vis(optic)

    snapfile = snap_file_path(atype, optic)

    # create a temporary ".req" file
    with tempfile.NamedTemporaryFile(delete=False) as f:
        for c in vis.alignPvs(withprefix='full'):
            channel = '%s_OFFSET' % (c)
            f.write(channel + '\n')

    # wrap further stuff in a try/except to catch any errors and cleanup appropriately
    try:
        # actually call the external burtrb utility to write the snapshot
        #subprocess.call(['cat', f.name])
        subprocess.call(['burtrb', '-f', f.name, '-o', snapfile])
        #subprocess.call(['cat', snapfile])
    finally:
        os.unlink(f.name)

    print >>sys.stderr, '', snapfile

def view_snap(atype, optic):
    snapfile = snap_file_path(atype, optic)

    print >>sys.stderr, snapfile

    with open(snapfile, 'r') as f:
        for line in f:
            line = line.strip()
            if line == '--- Start BURT header':
                inheader = True
                continue
            elif line == '--- End BURT header':
                inheader = False
                continue
            if inheader:
                continue
            data = line.split()
            if data[0] in ['-', 'RO', 'RON']:
                continue
            channel = data[0]
            value = data[2]
            print '%s %f' % (channel, float(value))

########################################

if __name__ == '__main__':

    parser = argparse.ArgumentParser(epilog='If no options are specified "aligned" positions are saved.')

    group1 = parser.add_mutually_exclusive_group()

    group1.add_argument('-a', '--aligned',
                        action='store_const', dest='atype', const='aligned',
                        help='save/view "alignment" offsets')

    group1.add_argument('-m', '--misaligned',
                        action='store_const', dest='atype', const='misaligned',
                        help='save/view "misalignment" offsets')

    group1.add_argument('-t', '--type',
                        type=str, metavar='TYPE', dest='atype',
		        choices=['aligned', 'misaligned', 'alignedtopd1', 'alignedtopd4'],
                        help='save/view specified position offsets ["aligned", "misaligned", "alignedtopd1", "alignedtopd4"]')

    group2 = parser.add_mutually_exclusive_group()

    group2.add_argument('-s', '--save',
                        action='store_const', dest='cmd', const='save',
                        help='save current (mis)alignment offsets')

    group2.add_argument('-v', '--view',
                        action='store_const', dest='cmd', const='view',
                        help='view currently saved (mis)alignment offsets')

    group2.add_argument('-p', '--path',
                        action='store_const', dest='cmd', const='path',
                        help='print path to (mis)alignment offsets snapshot file')

    parser.add_argument('optic', type=str, nargs='+',
                        help="optic name (e.g. 'PR2', 'ETMX')")

    args = parser.parse_args()

    if args.cmd is None:
        args.cmd = 'save'

    if args.atype is None:
        args.atype = 'aligned'

    # execute command for optics
    for optic in args.optic:
        optic = optic.lower()

        if args.cmd == 'save':
            make_snap(args.atype, optic)
        elif args.cmd == 'view':
            view_snap(args.atype, optic)
        elif args.cmd == 'path':
            print snap_file_path(args.atype, optic)

#    # some extra stuff for save
#    if args.cmd == 'save':
#
#        ##############################
#        # execute old alignment save tool that appends the alignment
#        # to a txt file, for archiving trend
#        print >>sys.stderr
#        print >>sys.stderr, 'executing old alignment save script...'
#        a_trend_script = os.path.join(userapps, 'vis', 'common', 'scripts', 'align_save')
#        cmd = [a_trend_script] + args.optic
#        print >>sys.stderr, '', ' '.join(cmd)
#        subprocess.call([a_trend_script] + args.optic)
#        ##############################
#
#        print >>sys.stderr, 'done.'
