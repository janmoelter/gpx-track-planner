from models import ElevationFilter


import numpy as np
import scipy.special

class Gauss(ElevationFilter):
    
    name = {'en': 'Gauss', 'de': 'Gauß'}
    description = ''
    
    def profile(self, distance: np.ndarray) -> np.ndarray:
        
        α = 0.05
        
        def gauss(x, r):
            σ = r / (np.sqrt(2) * scipy.special.erfinv(1 - α))
                
            return np.exp(- x**2 / (2 * σ**2)) / np.sqrt(2 * np.pi * σ**2)
                
        return gauss(distance, self.width/2)
