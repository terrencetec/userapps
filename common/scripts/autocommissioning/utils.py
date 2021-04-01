from foton import FilterFile,Filter,iir2zpk,iir2z
from ezca import LIGOFilter,Ezca

ezca = Ezca(timeout=2)

all_optics = ['ETMX','ETMY','ITMX','ITMY',
              'BS','SRM','SR2','SR3',
              'PRM','PR2','PR3',
              'MCI','MCO','MCE','IMMT1','IMMT2',
              'OSTM','OMMT1','OMMT2']

all_typea = ['ETMX','ETMY','ITMX','ITMY']
all_typeb = ['BS','SRM','SR2','SR3']
all_typebp = ['PRM','PR2','PR3']
all_typeci = ['MCI','MCO','MCE','IMMT1','IMMT2']
all_typeco = ['OSTM','OMMT1','OMMT2']
def typename_is(optic):
    '''
    '''
    if optic in all_typea:
        return 'Type-A'
    elif optic in all_typeb:
        return 'Type-B'
    elif optic in all_typebp:
        return 'Type-Bp'
    elif optic in all_typeci or optic in all_typeco:
        return 'Type-C'
    else:
        raise ValueError('!')

def partname_is(optic,stage):
    '''
    '''
    if typename_is(optic) in ['Type-A','Type-B','Type-Bp']:    
        if stage in ['TM','IM','MN']:        
            part = 'P'
        elif stage in ['BF','F3','F2','F1','F0','SF','IP']:
            part = 'T'
        else:
            raise ValueError('!')
    else:
        part = ''        
    return part


class Ezff(FilterFile):
    def __init__(self,ffname):        
        super().__init__(ffname)
        self.ffname = ffname

    def save(self):
        self.ff.write(self.ffname)

def copy_FMs(orig,dests):
    '''
    '''
    for dest in dests:
        for i in range(10):    
            dest[i].copyfrom(orig[i])    
        
def switch_on(chname,mask=['INPUT','OFFSET','OUTPUT','DECIMATION']):
    '''
    '''
    FB = ezca.get_LIGOFilter(chname)
    FMs = FB.get_current_swstat_mask().buttons
    FB.only_on(*mask)
