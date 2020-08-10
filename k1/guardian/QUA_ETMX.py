from GRD_PREQUA import *

DCUID = 79 # dcuid of k1visitmymon

ACTRATIO = {
    'LEN':{'IP':100000.0,'BF':100000.0,'MN':0.01,'IM':0.3,'TM':1},
    'TRA':{'IP':100000.0,'BF':100000.0,'MN':0.003,'IM':0.1,'TM':3},
    'VER':{'IP':100000.0,'BF':100000.0,'MN':0.01,'IM':0.3,'TM':1},
    'ROL':{'IP':100000.0,'BF':100000.0,'MN':0.003,'IM':0.1,'TM':0.3},
    'PIT':{'IP':100000.0,'BF':100000.0,'MN':0.01,'IM':0.3,'TM':1},
    'YAW':{'IP':100000.0,'BF':100000.0,'MN':0.01,'IM':0.3,'TM':1},
    }

# "Weight" of average; to be used for, rather,  selecting which DoF of which stage will be taken into consdieration when doing freq_chan averaging.
# In other words, you can artifically "select" the channels you want to use.
AVGWEIGHT = {'IP': {'LEN':0.0, 'TRA':0.0, 'VER':0.0, 'ROL':0.0, 'PIT':0.0, 'YAW':0.0},
             'BF': {'LEN':0.0, 'TRA':0.0, 'VER':0.0, 'ROL':0.0, 'PIT':0.0, 'YAW':0.0},
             'MN': {'LEN':1.0, 'TRA':1.0, 'VER':1.0, 'ROL':1.0, 'PIT':1.0, 'YAW':1.0},
             'IM': {'LEN':1.0, 'TRA':1.0, 'VER':1.0, 'ROL':1.0, 'PIT':1.0, 'YAW':1.0},
             'TM': {'LEN':1.0, 'TRA':1.0, 'VER':1.0, 'ROL':1.0, 'PIT':1.0, 'YAW':1.0},}
