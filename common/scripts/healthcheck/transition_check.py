

# import sys
# sys.path.append('/usr/lib/python3/dist-packages/')
# sys.path.append('/opt/rtcds/userapps/release/sys/common/guardian')
# sys.path.append('/opt/rtcds/userapps/release/vis/common/guardian')
# sys.path.append('/opt/rtcds/userapps/release/vis/k1/guardian')
# import VIS_OMMT1

import ezca
import time
hoge = ezca.Ezca()

fmt1 = 'GRD-VIS_{OPTIC}_STATE_S'
fmt2 = 'GRD-VIS_{OPTIC}_REQUEST_S'

def is_finished(OPTIC):
    state = fmt1.format(OPTIC=OPTIC)
    request = fmt2.format(OPTIC=OPTIC)
    return hoge[state]==hoge[request]

def huge(now):
    while True:
        finished = is_finished(OPTIC)
        if finished:
            dt = time.time()-now
            break
        else:
            time.sleep(1)
    return dt

# ------------------------------------------------------------------------------
if __name__=='__main__':
    fmt_accepted = '{0} is accepted: {1} takes {2} seconds (< 1 minutes)'
    fmt_not_accepted = '{0} is not accepted: {1} takes {2} seconds (> 1 minutes)'
    OPTICS = ['OMMT1','OMMT2','PRM']
    nodes = ['SAFE','ALIGNED']
    results = ''

    for OPTIC in OPTICS:
        for request in nodes:
            hoge['GRD-VIS_{OPTIC}_REQUEST'.format(OPTIC=OPTIC)] = request
            now = time.time()
            dt = huge(now)
            print(dt)
        if dt<60:
            result = fmt_accepted.format(OPTIC,'->'.join(nodes),int(dt))+'\n'
        else:
            result = fmt_not_accepted.format(OPTIC,'->'.join(nodes),int(dt))+'\n'
            
        results += result
    
    with open('results.txt','w') as f:
        f.write(results)
    
    
