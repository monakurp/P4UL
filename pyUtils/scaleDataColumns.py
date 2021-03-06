#!/usr/bin/env python3
import sys
import numpy as np
import matplotlib.pyplot as plt
import argparse
from utilities import filesFromList, inputIfNone
''' 
Description: A script to scale data in files with [x, y1, y2, ..., yn] format.
Scaling is done: vs = (y - v0)/v*


Author: Mikko Auvinen
        mikko.auvinen@fmi.fi
        Finnish Meteorological Institute
'''
#=======MAIN PROGRAM========================================#
parser = argparse.ArgumentParser()
parser.add_argument("strKey", nargs='?', default=None,\
  help="Search string for collecting files.")
parser.add_argument('-x', '--prefix', type=str, default='nond_',\
  help="Prefix for file names. Default='nond_'  .. as in non dimensional")
parser.add_argument('-ic', '--icols', type=int, nargs='+',\
  help='Columns to scale. Ex: 0,1,2,4')
parser.add_argument("-v0", "--vref", type=float, nargs='+', default=[0.0],\
  help="Reference values 'v0' in v+ = (v - v0)/v* for each column in --icols. Default = [0.]")
parser.add_argument("-vs", "--vstar", type=float, nargs='+', default=[1.0],\
  help="Characteristic value 'v*' in v+ = (v - v0)/v* for each column in --icols. Default = [1.]")
parser.add_argument("-cf", "--cfactor", type=float, nargs='+', default=[1.0],\
  help="Multiplication coef 'cf' in v+ = cf*(v - v0)/v* for each column in --icols. Default = [1.]")
parser.add_argument("-an", "--anoise", type=float, nargs='+', default=[0.0],\
  help="Amplitude of added white noise for each column in --icols. Default = [0.]")
parser.add_argument('-sr', '--skiprows', type=int, default=0,\
  help='Skip rows when reading files. Default=0.')

args = parser.parse_args()
#==========================================================#
# Rename ...
strKey  = args.strKey
v0      = np.array( args.vref  )  # Convert to numpy array
vs      = np.array( args.vstar )
cf      = np.array( args.cfactor )
icols   = args.icols
an      = np.array( args.anoise )
prefix  = args.prefix
sr      = args.skiprows
#==========================================================#

vx0 = np.zeros( np.shape(icols), float )
vxS = np.ones(  np.shape(icols), float )

if( (len(v0) == 1) and (len(icols) != 1) ):
  vtmp = np.zeros( np.shape(icols), float )
  vtmp[:] = v0[0]
  v0 = vtmp.copy(); vtmp = None
elif( len(v0) != len(icols) ):
  sys.exit(' Error: incompatible array lengths for columns and -v0 values. Exiting.')

if( (len(vs) == 1) and (len(icols) != 1) ):
  vtmp = np.ones( np.shape(icols), float )
  vtmp[:] = vs[0]
  vs = vtmp.copy(); vtmp = None
elif( len(vs) != len(icols) ):
  sys.exit(' Error: incompatible array lengths for columns and -vs values. Exiting.')

if( (len(cf) == 1) and (len(icols) != 1) ):
  vtmp = np.ones( np.shape(icols), float )
  vtmp[:] = cf[0]
  cf = vtmp.copy(); vtmp = None
elif( len(cf) != len(icols) ):
  sys.exit(' Error: incompatible array lengths for columns and -cf values. Exiting.')

if( (len(an) == 1) and (len(icols) != 1) ):
  vtmp = np.ones( np.shape(icols), float )
  vtmp[:] = an[0]
  an = vtmp.copy(); vtmp = None
elif( len(cf) != len(icols) ):
  sys.exit(' Error: incompatible array lengths for columns and -an values. Exiting.')
#==========================================================#

strKey = inputIfNone( strKey , " Enter search string: " )

fileNos, fileList = filesFromList( strKey+"*")

for fn in fileNos:
  try:    dat = np.loadtxt(fileList[fn], skiprows=sr)
  except: dat = np.loadtxt(fileList[fn], delimiter=',', skiprows=sr)
  
  j = 0
  for i in icols:
    if i not in range(dat.shape[1]):
      sys.exit(' Error: {} not in range({}). Exiting ...'.format(i,dat.shape[1]) )
    
    dat[:,i] = cf[j]*( dat[:,i] - v0[j] )/vs[j]
    
    if(an[j] != 0.0):
      N = np.shape(dat[:,i])
      dat[:,i] += (an[j] * np.random.random_sample(N) -an[j]/2.)
    
    j += 1
    
  fileout = prefix+fileList[fn]
  print(' Writing out file: {} '.format( fileout ) )
  
  if( sr > 0 ):
    with open(fileList[fn]) as f: 
      hStr = f.readline(); hStr.rstrip()
  else:
    hStr = 'Scaling v+ = cf(v - v0)/v* done with cf={}, v0={} and v*={} for cols={}'.format(cf,v0,vs,icols)
  

  np.savetxt(fileout, dat[:,:], fmt='%3.6e', header=hStr, delimiter=',')
  dat = None

print(' All done! ')
