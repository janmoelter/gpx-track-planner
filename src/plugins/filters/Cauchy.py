from models import ElevationFilter


import numpy as np

class Cauchy(ElevationFilter):
    
    name = 'Cauchy'
    description = ''
    
    def profile(self, distance: np.ndarray) -> np.ndarray:
        
        α = 0.05
        
        def cauchy(x, r):
            σ = r / np.tan(np.pi * (1 - α) / 2)
            
            return σ / (np.pi * (σ**2 + x**2))
                
        return cauchy(distance, self.width/2)
