from models import ElevationFilter


import numpy as np

class Bump(ElevationFilter):
    
    name = 'Bump'
    description = ''
    
    def profile(self, distance: np.ndarray) -> np.ndarray:
        
        α = 0.05
        
        def bump(x, r):
            C, k, b = 0.4439938161680794, 0.1015885160684956, 1.6292269098692807
            U = lambda p: {0.99: 0.8139822194885638, 0.98: 0.7796687820381493, 0.97: 0.7544667985638922, 0.96: 0.7336100879815718, 0.95: 0.7153919969095434, 0.94: 0.6989797080995479, 0.93: 0.6838962335776332, 0.92: 0.6698396086472479, 0.91: 0.6566049953370737, 0.9: 0.6440462111124972}.get(p, np.nan * p * (C * np.e / 2 + (1 - C * np.e / 2) * k * np.log(1 / (1 - p))**b / (1 + k * np.log(1 / (1 - p))**b))) # maximal relative error on [0.1, 0.9]: approx. 0.08%
            
            σ = r / U(1 - α)
            
            return np.exp(np.where(np.abs(x / σ) < 1, - 1 / (1 - x**2 / σ**2), -np.inf)) / (C * σ)
                
        return bump(distance, self.width/2)
