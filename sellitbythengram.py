#!/usr/bin/python
import os
import sys
import glob
import nltk
import re
import subprocess
from nltk.util import ngrams
from pprint import pprint
import hashlib
from optparse import OptionParser
import string
from collections import OrderedDict
import multiprocessing

try:
    import re2 as re
except ImportError:
    import re

parser = OptionParser(usage="https://www.youtube.com/watch?v=XQlTV5egauU&feature=youtu.be&t=64")
parser.add_option("-d", dest="dir", type="string", help="dir to ngram")
parser.add_option("-f", dest="input_file", type="string", help="will read a LF seperated file and treat each line as a input to ngram")
parser.add_option("-n", dest="nlist", type="string", help="ngram csv count to generate, default is '100,75,50,20,10,9,8,7,6,5,4'")
parser.add_option("-P", dest="i_re", type="string", help="Ngram must match this regex to be included in the output")
parser.add_option("-v", dest="e_re", type="string", help="Ngram matching this regex will not be included in the output")
parser.add_option("-g", dest="do_reass", help="Generate a regex string provide path to regex assemble perl script")
parser.add_option("-r", dest="reduce", action='store_true', help="Reduce matches to globally unique")
parser.add_option("--ssplit", dest="ssplit", action='store_true', help="space seperated ngrams instead of byte len. Useful for meaning for word groups")
parser.add_option("--normwhite", dest="normwhite", action="store_true", help="normalize whitespace")
parser.add_option("--lower", dest="lower", action="store_true", help="lowercase the input")
parser.add_option("--nproc", dest="nproc", type=int, help="number of processes to use for (directory mode only) defaults to number of CPU's on system")
(options, args) = parser.parse_args()

PROCS = 1
flist = []
gcracker = OrderedDict() 
nlist = set()
ngram_cnt = {}
include_regex = None
exclude_regex = None
reass_in = set()
reass = None
replchars = re.compile('([^' + re.escape(string.letters + string.digits) +'])')
replchars_nprint = re.compile('([^' + re.escape(string.printable) +'])')

def cmd_wrapper(cmd):
    #print("running command and waiting for it to finish %s" % (cmd))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout,stderr = p.communicate()
    return (p.returncode, stdout, stderr)

def replchars_to_hex(match):
    return r'\x{0:02x}'.format(ord(match.group()))

if options.nproc and options.nproc > 0:
    PROCS=options.nproc
else:
    PROCS=multiprocessing.cpu_count()

def ngram_from_file(entry,nlist,key):
    print("Generating n-grams for {0}".format(entry))
    dapoop=open(entry).read()
    if options.normwhite:
        dapoop = re.sub(r'[\r\n\s\t]+',"\x20",dapoop)
    if options.lower:
        dapoop = dapoop.lower()
    tmpd=OrderedDict()
    for i in nlist:
        tmpset=[]
        if options.ssplit:
            tgrams=ngrams(dapoop.split(" "), i)
        else:
            tgrams=ngrams(dapoop, i)        
        for grams in tgrams:
            if options.ssplit:
                nstr=''' '''.join(grams)
            else:
                nstr=''''''.join(grams)
            if nstr not in ngram_cnt:
                ngram_cnt[nstr] = 1
            else:
                ngram_cnt[nstr] += 1
            if nstr not in tmpset:
                tmpset.append(nstr)
            tmpd[i]=tmpset

    tmpd2={}        
    tmpd2["data"]=tmpd
    tmpd2["key"]=key
    return tmpd2

def setg(tmpd2):
    gcracker[tmpd2["key"]]=tmpd2["data"]

if(options.dir):
    if os.path.isdir(options.dir):
        flist = glob.glob(options.dir + "/*")
    else:
       print("print you gotta provdie a dir dawg")
       sys.exit(-1)    

if(options.nlist):
    try:
        blah=options.nlist.split(",")
        for entry in blah:
            nlist.add(int(entry))
        nlist=list(nlist)
    except Exception as e:
        print("You got problems BRO %s" % (e))
        sys.exit(-1)    
else:
    nlist = [100,75,50,20,19,18,17,16,15,14,13,12,11,10,9,8,7,6,5,4,3]

if(options.i_re):
    try:
        include_regex = re.compile(options.i_re,re.S)
    except Exception as e:
        print("Error Compiling Include Regex" % (e))
        sys.exit(-1)

if(options.e_re):
    try:
        exclude_regex = re.compile(options.e_re)
    except Exception as e:
        print("Error Compiling Exclude Regex" % (e))
        sys.exit(-1)

if(options.do_reass):
    if os.path.isfile(options.do_reass):
        reass = options.do_reass
    else:
        print "Warning: not performing regex reasssmble no reass.pl found"
    
nlist.sort(reverse=True)

if nlist and flist:
    if len(flist) > 1:
        pool = multiprocessing.Pool(PROCS)
        for entry in flist:
            key = os.path.basename(entry)
            pool.apply_async(ngram_from_file,args=(entry,nlist,key),callback=setg)
        pool.close()
        pool.join()

elif nlist and options.input_file and os.path.exists(options.input_file):
    lines=open(options.input_file).readlines()
    if not lines:
        print "empty input file exiting"
        sys.exit(-1)
    lines = sorted(lines, key=len)
    print("The number of lines in the list is: %s." % (len(lines)))
    print("The shortest line in the list is: %s." % (len(lines[0])))
    print("The longest line in the list is: %s." % (len(lines[-1])))
    key = 0
    for dapoop in lines:
        if options.normwhite:
            dapoop = re.sub(r'[\r\n\s\t]+',"\x20",dapoop)

        gcracker[key]=OrderedDict()
        for i in nlist:
            tmpset=set()
            if options.ssplit:
                tgrams=ngrams(dapoop.strip().split(), i)
            else:
                tgrams=ngrams(dapoop.strip(), i)

            for grams in tgrams:
                if options.ssplit:
                    nstr=''' '''.join(grams)
                else:
                    nstr=''''''.join(grams)
            gcracker[key][i]=tmpset
        key = key + 1

all_list = set()
if nlist and gcracker:    
    for i in nlist:
        setlst = []
        lastset = []
        for key in gcracker:
            setlst.append(gcracker[key][i])        
            lastset = gcracker[key][i]
        s1=set.intersection(*map(set,setlst))
        s1=[t for t in setlst[0] if t in s1]
        cset=set()
        if options.reduce:
            tmp_set=set()
            for entry in s1:
                found = False
                for entry2 in all_list:
                    if entry in entry2:       
                        found = True
                        break
                if not found:
                   tmp_set.add(entry)
                   all_list.add(entry)
            s1=tmp_set
        if s1:
            print("Ngrams of len:%s" % (i))
        for entry in s1:
           if include_regex and include_regex.search(entry) != None:
               if exclude_regex and exclude_regex.search(entry) != None:
                   continue
               pprint(entry)
               pprint(entry.encode('hex')) 
               print "content:\x22|"+" ".join(re.findall("(?P<foo>[a-f0-9]{2})",entry.encode("hex")))+"|\x22;"
               cset=cset.union(set(entry)) 
               if reass: 
                   reass_in.add(replchars.sub(replchars_to_hex, entry) + '\n')

           elif not include_regex and exclude_regex and exclude_regex.search(entry) == None:
               pprint(entry)
               pprint(entry.encode('hex'))
               print "content:\x22|"+" ".join(re.findall("(?P<foo>[a-f0-9]{2})",entry.encode("hex")))+"|\x22;"
               cset=cset.union(set(entry))
               if reass:     
                   reass_in.add(replchars.sub(replchars_to_hex, entry) + '\n')

           elif not include_regex and not exclude_regex:
               pprint(entry)
               pprint(entry.encode('hex'))
               print "content:\x22|"+" ".join(re.findall("(?P<foo>[a-f0-9]{2})",entry.encode("hex")))+"|\x22;"
               cset=cset.union(set(entry))
               if reass:
                   reass_in.add(replchars.sub(replchars_to_hex, entry) + '\n')

        l=[]
        unique_chars = ""              
        for val in cset:
            l.append(val)

        l.sort()
        for v in l:
            unique_chars +=v
        if unique_chars:
            print ("unique_chars \"[%s]\"\n" % (replchars.sub(replchars_to_hex, unique_chars)))

if reass_in:
    f = open("rescaped.txt",'w')
    f.writelines(reass_in)
    f.close()
    ret,out,err = cmd_wrapper("%s rescaped.txt" % (reass))
    print("pcre to match all common ngrams\n")
    print("pcre:\"/%s/\";" % (out.strip()))
