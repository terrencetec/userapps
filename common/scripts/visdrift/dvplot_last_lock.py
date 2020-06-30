#!/usr/bin/env python

import cdsutils.nds as nds2
import pydv
import os
import sys
from gpstime import gpstime
from datetime import timedelta
from dateutil.tz import tzutc, tzlocal


DEFAULT_FILE_PATH = ['/opt/rtcds/userapps/trunk/sys/common/scripts/lockloss/list_of_channels/']


def load_channel_list(path):
    channels = []
    y_limits = [] #Pairs, [ymin, ymax]
    f = open(path, 'r')

    for line in f:
        line = line.strip()
        # skip empty lines or comments
        if not line or line.isspace() or line.startswith('#'):
            continue
        temp = line.strip().split(' ')
        if len(temp) == 1:
            channels.append(temp[0])
            y_limits.append([None,None])
        elif len(temp) == 3:
            channels.append(temp[0])
            y_limits.append([float(temp[1]),float(temp[2])])
        else:
            print("Can not parse line in " + str(path) + " Line: " + str(line))
    f.close()
    return channels, y_limits

def parse_channel_list(channels): # generator object
    for channel in channels:
        #if channel != channel.upper(): # check if channel names are given in capitals.
        #    sys.exit("Invalid channel name: {0}".format(channel))
        if ':' not in channel:
            try:
                channel = IFO.upper() + ':' + channel
            except AttributeError:
                sys.exit("IFO not specified.")
        yield channel

def get_channels(args):
    if not (args.file == None):
        if not os.path.isfile(args.file):
            for directory in DEFAULT_FILE_PATH:
                if os.path.isfile(directory + args.file):
                    args.file = directory + args.file
                    break
            channel_iterator,y_limits = load_channel_list(args.file)
    else:
        channel_iterator = load_channel_list(args.channel_names)
        y_limits = None
    return parse_channel_list(channel_iterator),y_limits

def cmd_plot(args):
    channels = []
    temp_channels,y_limits = get_channels(args)
    for channel in temp_channels:
        channels.append([channel])
    args.title = 'Python Data Viewer'
    try:
        time = gpstime.fromgps(float(args.time)).replace(tzinfo=tzutc())
    except ValueError:
        time = ' '.join(args.time)
        time = gpstime.parse(str(time))
    plot(channels,y_limits, time, args)


def plot(channels,y_limits, time, args):
    # specify channels as list of lists, so that they show up in
    # separate subplots
    # channel_names = []
    # for channel in args.channel_list:
    #     channel_names.append([channel])

    center_time = time.gps()
    xmin = center_time - args.lookback
    xmax = center_time + args.lookafter
    print 'center_time=' + str(center_time)
    print 'xmin=' + str(xmin)
    print 'xmax=' + str(xmax)
    print args.lookback
    print args.lookafter
    try:
        fig = pydv.plot(
        channel_names=channels,
        center_time=center_time,
        xmin=xmin,
        xmax=xmax,
        title=args.title,
        sharex=True,
        sharey=False,
        no_threshold=True,
        no_wd_state=True,
        show=False,
        )
    except TypeError:
        fig = pydv.plot(
        channel_names=channels,
        center_time=center_time,
        xmin=xmin,
        xmax=xmax,
        sharex=True,
        sharey=False,
        no_threshold=True,
        no_wd_state=True,
        show=False,
        )

    #Set y limits
    plots = fig.get_axes()
    if y_limits != None:
       for idx, y_min_max in enumerate(y_limits):
           if (y_min_max[0] != None) and (y_min_max[0] != None):
               plots[idx].set_ylim(y_min_max[0],y_min_max[1])

    fig.show()
####################

prog = 'dvplot_last_lock.py'
usage = """dvplot_last_lock.py [option] <command> [options]"""
description = """
Plot channels since last low noise lock

"""

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description=description)

    #parser.add_argument('channel_names',metavar='channel',nargs='?',type=str,help='channel name')
    parser.add_argument('-f','--file',type=str,default=None,help='File name with channels to load')
    args = parser.parse_args()

    ifo = os.environ['IFO']

    #Determine last lock time
    nds_name = os.environ['LIGONDSIP']
    conn = nds2.connection(nds_name,8088)
    conn.set_parameter('GAP_HANDLER','STATIC_HANDLER_ZERO')

    state_channel = [ifo.upper() + ':GRD-IMC_STATE_N.mean,m-trend']

    LOW_NOISE_STATE = 2000
    SEARCH_TIME_STRIDE = 24*60*60


    time_now = gpstime.tconvert().gps() - 180
    start_time = int(60*((time_now - SEARCH_TIME_STRIDE) // 60))
    end_time = int(60 *(time_now // 60))

    print str(time_now + 180)

    found = False
    while not found:
        print start_time
        print end_time
        print state_channel
        data = conn.fetch(start_time,end_time,state_channel)
        for x in range(1,len(data[0].data)+1):
            if data[0].data[-x] == LOW_NOISE_STATE:
                step_size = 1/data[0].channel.sample_rate
                final_time = -x*step_size + data[0].gps_seconds + SEARCH_TIME_STRIDE
                found = True
                break
        end_time = start_time
        start_time = start_time - SEARCH_TIME_STRIDE
    #Add 10 minutes before first time, just to give a some data points before hand
    args.time = final_time
    time_now = gpstime.tconvert().gps()-120
    args.lookafter = int(time_now) - args.time
    args.lookback = 600

    cmd_plot(args)
    a = input('Press enter to quit')
    sys.exit()
