# ------------------------------------------------------------------------------------
# Utilities for parsing a BURT file
# Mark Barton 2/21/14
## $Id$
"""
This module supplies a function readBurt(fname, includero=False, raiseonbadlines=False, dequote=True, tonum=True, full=False)
to read a BURT .snap file and return a dictionary of channel:value pairs.
"""
# Dependencies:

import re # regular expression utilities

# ------------------------------------------------------------------------------------
# Utilities...
# Function taking a pattern for one string and returning a pattern for a space-separated list of zero or more such strings
def sslist(pat):
    return pat+r"?(?:\s+"+pat+r")*"

# Some very basic patterns
patreadonly = r"^(RO\s)?" # optional read-only marker RO
patPV = r"([a-zA-Z0-9:\-_]+)" # channel, e.g., H1:SUS-ITMX_M0_OSEMINF_L-IN1 FIXME make stricter
patcount = r"([0-9]+)"
patqstring = r'"(?:[^"\\]|\\.)*"'
patother = r'[^"]\S+'
patitem = r'('+patqstring+r'|'+patother+r')'
patitems = sslist(patitem)
# pattern for an entire data row
pat = patreadonly+patPV+r"\s+"+patcount+r"\s+"+patitems+r'\n*$'

patint = r'^[-+]?[0-9]+$'
patfloat = r"^(?:[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)$"

cpat = re.compile(pat)
cpatint = re.compile(patint)
cpatfloat = re.compile(patfloat)

# Error class
class BurtError(Exception):
    def __init__(self, msg, badlines=[]):
        self.args = (msg, badlines)
        self.msg = msg
        self.badlines = badlines

# A formatter function for values
def format(string, dequote=True, tonum=True):
    if string[0]=='"' and string[-1]=='"' and dequote:
        return string[1:-1].replace(r'\"',r'"') # FIXME: handle additional escape sequences if necessary (need to check)
    elif string==r'\0' and dequote:
        return ''
    elif cpatint.match(string) and tonum:
        return int(string)
    elif cpatfloat.match(string) and tonum:
        return float(string)
    else:
        return string
        
# ------------------------------------------------------------------------------------      
# The main BURT-file read function
def readBurt(fname, includero=False, raiseonbadlines=False, dequote=True, tonum=True, full=False):
    """readBurt(fname) takes a BURT file name and returns a dictionary of channel:value pairs.
    
    The 11 line BURT header in the file is ignored.
    By default, lines beginning with "RO " (i.e., read-only channels) are ignored. 
    Use includero=True to include them or includero='separate' to return a tuple of dictionaries
    for non-read-only and read-only channels.
    By default, BURT's string encoding is stripped: the double quotes around string's with spaces are removed,
    and r'\0' (representing an empty string) is converted to ''. Use dequote=False to suppress this.
    By default, data elements that look like numbers are converted to int or float. Use tonum=False to suppress this.
    By default, lines of unrecognized format are ignored. Use raiseonbadlines=True
    to raise an error of type burt.BurtError. The list of bad lines can be accessed with an
    except block like the following:
        except burt.BurtError as e:
            print e.badlines
    By default, only the first of multiple values is returned. Use full=True to return key:item pairs like
        'H1:SUS-ETMX_M0_OPTICALIGN_Y_OFFSET': ('1', ['7.401057800000004e+01'])
    where each item is a tuple of the expected number of data elements (per the file itself) and a list of the data elements as strings."""
    with open(fname, 'r') as fobj:
        # throw away opening 11 lines, which should be header
        for i in range(11):
            fobj.readline()
        lines = fobj.readlines()
        matches = [cpat.match(l) for l in lines]
        if not(all(matches)) and raiseonbadlines:
            badlines = [l.strip() for l in lines if not(cpat.match(l))]
            raise BurtError("Bad lines in BURT snap file: "+fname,badlines)
        groupedlines = [m.groups() for m in matches if m]
        if full:
            if includero==True:
                data =   {l[1]:(int(l[2]),[format(g,dequote,tonum) for g in l[3:-1]]) for l in groupedlines}
                return data         
            elif includero=='separate':  
                data =   {l[1]:(int(l[2]),[format(g,dequote,tonum) for g in l[3:-1]]) for l in groupedlines if l[0]==None}
                rodata = {l[1]:(int(l[2]),[format(g,dequote,tonum) for g in l[3:-1]]) for l in groupedlines if l[0]=='RO '}
                return (data, rodata)
            else:
                data =   {l[1]:(int(l[2]),[format(g,dequote,tonum) for g in l[3:-1]]) for l in groupedlines if l[0]==None}
                return data
        else:
            if includero==True:
                data =   {l[1]:format(l[3],dequote,tonum) for l in groupedlines}
                return data         
            elif includero=='separate':  
                data =   {l[1]:format(l[3],dequote,tonum) for l in groupedlines if l[0]==None}
                rodata = {l[1]:format(l[3],dequote,tonum) for l in groupedlines if l[0]=='RO '}
                return (data, rodata)
            else:
                data =   {l[1]:format(l[3],dequote,tonum) for l in groupedlines if l[0]==None}
                return data
