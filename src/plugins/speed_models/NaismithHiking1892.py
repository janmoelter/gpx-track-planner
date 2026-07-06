from models import SpeedModel


import numpy as np

class NaismithHiking1892(SpeedModel):
    
    name = {'en': 'Naismith Hiking (1892)', 'de': 'Naismith Wandern (1892)'}
    description = 'Reference: W. W. Naismith. "Excursions. Cruach Ardran, Stobinian, and Ben More". Scott. Mt. Club J. 2:136 (1892)'
    
    parameters = {
        'speed_horizontal': {'default': 5.0, 'label': {'en': 'Horizontal Speed (km/h)', 'de': 'Horizontale Geschwindigkeit (km/h)'}},
        'speed_vertical': {'default': 600.0, 'label': {'en': 'Vertical Speed (m/h)', 'de': 'Vertikale Geschwindigkeit (m/h)'}},
    }
    
    def speed_function(self, slope: np.ndarray):
        
        _speed_horizontal = self.speed_horizontal / 3.6
        _speed_vertical = self.speed_vertical / 3600
        
        with np.errstate(divide='ignore', invalid='ignore'):
            return np.where(slope >= 0, 1/(1/_speed_horizontal + slope * 1/_speed_vertical), _speed_horizontal)
