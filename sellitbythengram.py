#!/usr/bin/python
import os
import sys
import glob
import nltk
import re
from nltk.util import ngrams
from pprint import pprint

from optparse import OptionParser

parser = OptionParser(usage="https://www.youtube.com/watch?v=XQlTV5egauU&feature=youtu.be&t=64")
parser.add_option("-d", dest="dir", type="string", help="dir to ngram")
parser.add_option("-f", dest="input_file", type="string", help="will read a LF seperated file and treat each line as a input to ngram")
parser.add_option("-n", dest="nlist", type="string", help="ngram csv count to generate, default is '100,75,50,20,10,9,8,7,6,5,4'")
(options, args) = parser.parse_args()

flist = []
gcracker = {}
nlist = set()

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
    except Exception as e:
        print("You got problems BRO %s" % (e))
        sys.exit(-1)    
else:
    nlist = [100,75,50,20,10,9,8,7,6,5,4]

if nlist and flist:
    if len(flist) > 1:
        for entry in flist:
            dapoop=open(entry).read()
            key = os.path.basename(entry)
            gcracker[key]={}
            for i in nlist:
                tmpset=set()
                tgrams=ngrams(dapoop, i)
                for grams in tgrams:
                    tmpset.add(''''''.join(grams))
                gcracker[key][i]=tmpset

elif nlist and options.input_file and os.path.exists(options.input_file):
    lines=open(options.input_file).readlines()
    key = 0
    for dapoop in lines:
        gcracker[key]={}
        for i in nlist:
            tmpset=set()
            tgrams=ngrams(dapoop.strip(), i)
            for grams in tgrams:
                tmpset.add(''''''.join(grams))
            gcracker[key][i]=tmpset
        key = key + 1
        
if nlist and gcracker:    
    for i in nlist:
        setlst = []
        for key in gcracker:
            setlst.append(gcracker[key][i])        
             
        s1=set.intersection(*setlst)
        for entry in s1:
           pprint(entry)
           print "content:\x22|"+" ".join(re.findall("(?P<foo>[a-f0-9]{2})",entry.encode("hex")))+"|\x22;"
        
