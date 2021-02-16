# -*- coding: utf-8 -*-
import os
import sys
import shutil

'''
    [Usage]
    Chans and Foton files copy to userapps.

    chans_foton_copying_to_userapps(optics)
    or each to
    chans_copying_to_userapps(optics)
    foton_copying_to_userapps(optics)
'''

### Source file path
# /opt/rtcds/kamioka/k1/chans/K1(optics).txt
foton_src_fullpath = '/opt/rtcds/kamioka/k1/chans/K1%s.txt'

# /opt/rtcds/kamioka/k1/target/k1(optics)/k1(optics)epics/burt/'
# aligned.snap, misaligned.snap, safe.snap
snap_src_dir = '/opt/rtcds/kamioka/k1/target/k1%s/k1%sepics/burt/'
aligned_src_fullpath = snap_src_dir + 'aligned.snap'
misaligned_src_fullpath = snap_src_dir + 'misaligned.snap'
safe_src_fullpath = snap_src_dir + 'safe.snap'

### Dist directory
dst_fullpath = '/opt/rtcds/userapps/release/vis/k1/'
snap_dst_fullpath = dst_fullpath + 'snapfiles/k1%s/'
foton_dst_fullpath = dst_fullpath + 'fotonfiles/'

'''
    Common Function
'''
def common_copying_to_userapps(src, dst):
    if os.path.isdir(dst) == False:
        #print('Directpry not found: ' + dst)
        return False

    if os.path.isfile(src) == True:
        #print('Copy from '+src+' to '+dst)
        shutil.copy2(src, dst)
    else:
        #print('File not found: ' + src)
        return False

    return True

'''
    Copying the chans file to userapps directory
'''
def foton_copying_to_userapps(optics):
    #print('### Start foton file copy ###')
    src = foton_src_fullpath % optics.upper()
    dst = foton_dst_fullpath
    return common_copying_to_userapps(src, dst)

'''
    Copying the foton files to userapps directory
'''
def snap_copying_to_userapps(optics):
    #print('### Start snap file copy ###')
    dst = snap_dst_fullpath % optics.lower()
    if os.path.isdir(dst) == False:
        #print('mkdir ' + dst)
        os.mkdir(dst)

    src = aligned_src_fullpath % (optics.lower(), optics.lower())
    result = common_copying_to_userapps(src, dst)
    if result == False:
        return False

    src = misaligned_src_fullpath % (optics.lower(), optics.lower())
    result = common_copying_to_userapps(src, dst)
    if result == False:
        return False

    src = safe_src_fullpath % (optics.lower(), optics.lower())
    result = common_copying_to_userapps(src, dst)
    if result == False:
        return False

    return True

'''
    Copying the snap and foton files to userapps directory
'''
def snap_foton_copying_to_userapps(optics):
    if snap_copying_to_userapps(optics) == False:
        return 'Bad snap'

    if foton_copying_to_userapps(optics) == False:
        return 'Bad foton'    
    return 'ALL OK'

if __name__ == "__main__":
    sys.path.append('/opt/rtcds/userapps/release/sys/common/guardian')
    import cdslib
    model_names = [model.name for model in list(cdslib.get_all_models())]
    vismodel_names = filter(lambda x:'vis' in x or 'modal' in x, model_names)
    for optics in vismodel_names:
        ans = snap_foton_copying_to_userapps(optics)
        if ans!='ALL OK':
            print(optics,ans)
