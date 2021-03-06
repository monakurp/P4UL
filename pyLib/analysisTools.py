import numpy as np
import sys
try: 
  import scipy.stats as st # contains st.entropy
except:
  pass
''' 
Description:


Author: Mikko Auvinen
        mikko.auvinen@helsinki.fi 
        University of Helsinki &
        Finnish Meteorological Institute
'''

# =*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*=*
#==========================================================#
def sensibleIds( ijk, x, y, z ):
  '''
  Check whether the chosen i,j,k indices make sense for given x, y, z coords.
  '''
  ijk[0] = np.minimum( ijk[0] , len(x)-1 ); ijk[0] = np.maximum( ijk[0], 0 )
  ijk[1] = np.minimum( ijk[1] , len(y)-1 ); ijk[1] = np.maximum( ijk[1], 0 )
  ijk[2] = np.minimum( ijk[2] , len(z)-1 ); ijk[2] = np.maximum( ijk[2], 0 )

  return ijk

#==========================================================#
def groundOffset( vx ):
  '''
  Find ground offset (in z-direction) for given velocity array vx(t, z, y, x) 
  '''
  k_offset = 0
  while 1:
    idNz = (vx[:,k_offset,1,1] > 0.)
    if( any( idNz ) ):
      break
    else:
      k_offset += 1
      
  return k_offset

#==========================================================#

def filterTimeSeries( ds, sigma=1 ):
  import scipy.ndimage as sn # contains the filters
  df  = sn.gaussian_filter( ds , sigma=sigma )
  dfp = df - np.mean( df )
  dn  = ds - dfp
  
  return dn

#==========================================================#
def quadrantAnalysis( v1, v2, qDict ):
  from utilities import dataFromDict
  
  debug = False
  
  # Extract data from dict. Using dict makes future modifications easy.
  ijk1     = dataFromDict('ijk1',      qDict, allowNone=False )
  ijk2     = dataFromDict('ijk2',      qDict, False )
  nkpoints = dataFromDict('nkpoints',  qDict, True )
  npx      = dataFromDict('npixels',   qDict, False )
  axisLim  = dataFromDict('axisLim',   qDict, False )
  holewidth= dataFromDict('holewidth', qDict, False )
  weighted = dataFromDict('weighted',  qDict, True )
  
  # Create arrays for running loops over the selected coordinates.
  iList = np.arange(ijk1[0],ijk2[0]+1)
  jList = np.arange(ijk1[1],ijk2[1]+1)
  kList = np.arange(ijk1[2],ijk2[2]+1)

  '''
  In quadrant analysis context, using a stride in z-direction is usually not desired.
  By default npoints is None.'''
  if( nkpoints is None): stride = 1
  else:                  stride = max( ((kList[-1]-kList[0])/nkpoints)+1 , 2 )


  # Compute the covariance term (for example, u'w')
  v = v1*v2
  
  if( debug ):
    print('min(v1)={}, max(v1)={}, min(v2)={}, max(v2)={}'\
      .format(np.abs(np.min(v1)), np.max(v1), np.abs(np.min(v2)), np.max(v2)))
  
  maxLim = np.abs(axisLim)
  minLim = -1.*maxLim

  # Determine if some grid points are under the ground level.
  k_off = max( groundOffset( v1 ), groundOffset( v2 ) )
  if( k_off > 0 and debug ):
    print(' {}: ground offset (k_off) = {}'.format(filename, k_off))

  x = np.linspace(minLim,maxLim,npx+1)
  y = np.linspace(minLim,maxLim,npx+1)
  dx = (maxLim-minLim)/(npx)
  X,Y = np.meshgrid(x,y)
  Qi  = np.zeros( np.shape(X), float )


  nTot = 0
  nQ   = np.zeros( 5, int )   # nQ[0] = nQTot
  SQ   = np.zeros( 5, float ) # SQ[0] = STot
  '''
  Q1: u'(+), w'(+), OutwardInteraction
  Q2: u'(-), w'(+), Ejection
  Q3: u'(-), w'(-), Inward Interaction
  Q4: u'(+), w'(-), Sweep
  '''
  
  for i in iList:
    for j in jList:
      for k in kList[::stride]:
        vt  = v[:,k+k_off,j,i]
        
        vt_mean = np.mean( np.abs(vt) )

        v1t = v1[:,k+k_off,j,i] 
        v2t = v2[:,k+k_off,j,i] 
        
        for l in range( len(vt) ):
          SQ[0] += vt[l]; nTot += 1
          if( np.abs(vt[l]) > (holewidth*vt_mean) ): 
            n = np.minimum( int((v1t[l] - minLim)/dx) , npx )
            n = np.maximum( n , 0 )
            m = np.minimum( int((v2t[l] - minLim)/dx) , npx )
            m = np.maximum( m, 0 )
            Qi[m,n] += 1.; nQ[0] += 1
          
            if( v1t[l] > 0. and v2t[l] > 0. ):
              nQ[1] += 1; SQ[1] += vt[l]  # Outward Interaction
            elif( v1t[l] < 0. and v2t[l] > 0. ):
              nQ[2] += 1; SQ[2] += vt[l]  # Ejection
            elif( v1t[l] < 0. and v2t[l] < 0. ):
              nQ[3] += 1; SQ[3] += vt[l]  # Inward Interaction
            else:#( v1t[l] > 0 and v2t[l] < 0. ):
              nQ[4] += 1; SQ[4] += vt[l]  # Sweep

  v = None; v1 = None; v2 = None
  Qi /= (np.float(nQ[0])*dx**2)  # Obtain the PDF
  
  if( weighted ):
    Qi *= np.abs(X*Y)
  
  SQ[0] /= np.float(nTot) # Total contribution
  SQ[1:] /= nQ[1:].astype(float)  # Average contributions
  
  # Assemble the result dict 
  rDict = dict()
  rDict['nQ'] = nQ
  rDict['SQ'] = SQ
  #rDict['klims']= np.array([ kList[0], kList[-1] ])
  
  return Qi, X, Y, rDict

#==========================================================#

def calc_ts_entropy_profile( V, z, alpha=1., nbins=16 ):
  
  vo = np.zeros( len(z) )
  for k in range( len(z) ):
    try:    Vk = V[:,k,1,1]
    except: Vk = V[:,k,0,0]
    Vk = Vk - np.mean(Vk)
    pk, bins = np.histogram( Vk, bins=nbins, density=True ) # Do not store the bins
    bins = None
    
    vo[k] = calc_entropy( pk, alpha )
    
  return vo

#==========================================================#

def calc_entropy( pk , alpha=1. ):
  '''
  pk: probability density distribution (i.e. histogram from time series or wavelet scalo- or spectrogram.
  '''
  if( alpha == 1. ):
    s = st.entropy( pk )
  else:
    s =(np.log( sum(np.power(np.array(pk),alpha)) ))/(1.-alpha)
    
  return s

#==========================================================#

def calc_divergence( pk, rk, alpha=1. ):
  
  pk += 1e-9; rk += 1e-9  # Add something small in case zero 
  
  if(alpha==1.):
    div=sum(np.array(pk)*np.log(np.array(pk)/(np.array(rk)) ))
  else:
    powratio=np.power(np.array(pk),alpha)/np.power(np.array(rk),alpha-1.)
    div=np.log((sum(powratio)))/(alpha-1.)
  
  return div

#==========================================================#

def discreteWaveletAnalysis( vx , wDict ):
  from utilities import dataFromDict
  try: import pywt
  except: sys.exit(' Library pywt not installed. Exiting ...')
  
  # nlevel = 4
  order = 'freq'  # "normal"
  wavelet = dataFromDict('wavelet', wDict, allowNone=False )
  nlevel  = dataFromDict('nlevel',  wDict, allowNone=False )
  if( wavelet in pywt.wavelist() ):
    try:
      wp = pywt.WaveletPacket( vx , wavelet, 'sym', maxlevel=nlevel)
    except:
      print(" Wrong wavelet type given. Reverting to default 'db2'. ")
      wavelet = 'db2'
      wp = pywt.WaveletPacket( vx , wavelet, 'sym', maxlevel=nlevel)
  
  nodes = wp.get_level(nlevel, order=order)
  labels = [n.path for n in nodes]
  values = np.array([n.data for n in nodes], 'd')
  values = abs(values)
  
  return values, labels

#==========================================================#

def continuousWaveletAnalysis( vx, wDict ):
  from utilities import dataFromDict
  try: import pywt
  except: sys.exit(' Library pywt not installed. Exiting ...')
  
  
  wavelet = dataFromDict('wavelet', wDict, allowNone=False )
  nfreqs  = dataFromDict('nfreqs', wDict, allowNone=False )
  dt      = dataFromDict('dt', wDict, allowNone=False )
  linearFreq = dataFromDict('linearFreq', wDict, allowNone=True )
  if( linearFreq ):
    scales  = 1./np.arange(1,nfreqs)
  else:
    scales = np.arange(1,nfreqs)
  
  cfs,freq = pywt.cwt(vx,scales,wavelet,dt)
    
  return cfs, freq

#==========================================================#







