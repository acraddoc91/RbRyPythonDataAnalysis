'''
Created on Sep 27, 2016

@author: Sandy
'''
import numpy as np

gam = 38.116*10**6
isatSigma = 1.6692*10**(-3)
isatPi = 2.5033*10**(-3)
omega = 2*np.pi*384.22811152028*10**12
hbar = 1.0545718*10**(-34)
sig0Sigma = hbar*omega*gam/(2*isatSigma)
sig0Pi = hbar*omega*gam/(2*isatPi)