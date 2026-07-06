from models import ElevationFilter


import numpy as np

class Square(ElevationFilter):
    
    name = {'en': 'Square (Mean)', 'de': 'Rechteck (Mittelwert)'}
    description = ''
    
    def profile(self, distance: np.ndarray) -> np.ndarray:
        
        α = 0.05
        
        def square(x, r):
            σ = r / (1 - α)
            
            return (np.abs(x) <= σ) / (2 * σ)
                
        return square(distance, self.width/2)
