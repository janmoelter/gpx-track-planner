from models import ElevationFilter


import numpy as np

class Triangle(ElevationFilter):
    
    name = {'en': 'Triangle', 'de': 'Dreieck'}
    description = ''
    
    def profile(self, distance: np.ndarray) -> np.ndarray:
        
        α = 0.05
        
        def triangle(x, r):
            σ = r / (1 - np.sqrt(α));
            
            return np.maximum(-np.abs(x) + σ, 0) / σ**2
        
        return triangle(distance, self.width/2)
