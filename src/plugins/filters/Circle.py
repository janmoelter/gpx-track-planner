from models import ElevationFilter


import numpy as np
import scipy.optimize

class Circle(ElevationFilter):
    
    name = {'en': 'Circle', 'de': 'Kreis'}
    description = ''
    
    def profile(self, distance: np.ndarray) -> np.ndarray:
        
        α = 0.05
        
        def circle(x, r):
            U = lambda p: {0.99: 0.9587350035870751, 0.98: 0.9343329933968081, 0.97: 0.9137702117343529, 0.96: 0.8953411046949168, 0.95: 0.8783394481598052, 0.94: 0.8623865056771954, 0.93: 0.8472494972440328, 0.92: 0.8327725033676554, 0.91: 0.8188446687550782, 0.9: 0.8053836365201198}.get(p, scipy.optimize.brentq(lambda u: 2/np.pi * (u * np.sqrt(1 - u**2) + np.arcsin(u)) - p, 0, 1))
            σ = r / U(1 - α);
            
            return 2 / (σ * np.pi) * np.sqrt(1 - np.clip(x**2 / σ**2, 0, 1))
                
        return circle(distance, self.width/2)
