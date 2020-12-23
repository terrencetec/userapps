#!/usr/bin/env python3
#! coding:utf-8

import buildlib
import threading
import time # sleep
import sys

ifo = 'k1'

#build_target = {
#    'prmt',
#    'prmp',
#    'pr2t',
#    'pr2p'
#}
build_target = []
build_status = [False] * len(build_target)

node_list = buildlib.getHostnameList()
node_value = [False] * len(node_list)

node_status = dict(zip(node_list,node_value))

sysname = 'vis'

thread_count = 0
thread_max = 5

def thread_buildoptic(optic, node, sysname='vis', make=False, makeinstall=False, restart=False):
    comment = node + ' : ' 
    if make:
        comment = comment + 'make ' + sysname + optic 
    if makeinstall:
        comment = comment + 'make install-' + sysname + optic 
    if restart:
        comment = comment + 'start' + sysname + optic 

    print('[start] '+comment)
    global thread_count
    buildlib.buildoptic(optic, sysname, make, makeinstall, restart)
#    time.sleep(10.0)
    node_status[node] = False
    print('[end] '+comment)
    thread_count = thread_count - 1

def buildfileParsor(buildlist):

    for index,line in enumerate(buildlist):

        if line[0] == '#' or len(line[:-1]) == 0:
            # comment line
            cmd = 'comment'
        elif line.find(' ') > 0:
            cmd, param = line.split(' ')
        else:
            cmd = line

        make = False
        makeinstall = False
        restart = False
        if cmd == 'make':
            pos = param.find('install-')
            if pos == -1:
                make = True
                model = param[:-1]
                #print('make ', model)
            else:
                makeinstall = True
                model = param[len('install-'):-1]
                #print('make install-', model)
        elif cmd.find('start') == 0:
            restart = True
            model = cmd[len('start'):-1]
            #print('start', model)
        elif cmd == 'comment':
            continue
        else:
            print('Unknown command line [',index+1,']')
            continue
            
        build_target.append({'model':model, 'make':make, 'makeinstall':makeinstall, 'restart': restart})
    
def main():
    global thread_count, thread_max, build_target
    args = sys.argv

    if len(args) == 2:
        filename = args[1]
        f = open(filename, 'r')
        buildlist = f.readlines()
        f.close()
        #print(buildlist)
    else:
        print('autobuild buildlist.txt')
        sys.exit(1)

    buildfileParsor(buildlist)

#    print(build_target)
    
    build_status = [False] * len(build_target)

    status = True
    build_step = 0 # 0: make, 1: make install, 2: start.
    while status == True:

        for index, build in enumerate(build_target):
            #print(index, optic)

            #print(index, build)
            if thread_count < thread_max:
                #models = buildlib.getmodels(sysname,optic)
                #for (model, fec) in models:
                model = build['model']
                make = build['make']
                makeinstall = build['makeinstall']
                restart = build['restart']

                call_flg = False
                if build_step == 0 and make == True:
                    call_flg = True

                if build_step == 1 and makeinstall == True:
                    call_flg = True

                if build_step == 2 and restart == True:
                    call_flg = True

                if call_flg:
                #  node = buildlib.getmodel2hostname(ifo + model)
                    node = buildlib.getmodel2hostname(model)
                    #print(node_status[node] )
                    if node_status[node] == False and build_status[index] == False:
                        node_status[node] = True
                        build_status[index] = True
                        optic = model[len('k1vis'):].lower()
                        thread = threading.Thread(target=thread_buildoptic, args=(optic, node, sysname, make, makeinstall, restart) )
                        thread.start()
                        thread_count = thread_count + 1
            else:
                pass

        status = False
        for value in build_status:
            if value == False:
                status = True

        if status == True and thread_count == 0 and build_step < 2:
            build_step = build_step + 1

        time.sleep(1.0)


if __name__ == '__main__':

    main()
    
