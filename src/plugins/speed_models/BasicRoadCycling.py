from models import SpeedModel


import numpy as np

class BasicRoadCycling(SpeedModel):
    
    name = {'en': 'Road Cycling (basic)', 'de': 'Rennradfahren (einfach)'}
    description = 'Basic road cycling model inspired by the classical Naismith Hiking Model.'
    
    parameters = {
        'speed_horizontal': {'default': 25.0, 'label': {'en': 'Horizontal Speed (km/h)', 'de': 'Horizontale Geschwindigkeit (km/h)'}},
        'speed_vertical': {'default': 800.0, 'label': {'en': 'Vertical Speed (m/h)', 'de': 'Vertikale Geschwindigkeit (m/h)'}},
        'speed_maximal': {'default': 60.0, 'label': {'en': 'Maximal Speed (km/h)', 'de': 'Maximale Geschwindigkeit (km/h)'}},
        'slope_speed_maximal': {'default': 8, 'label': {'en': 'Maximal Speed Slope (%)', 'de': 'Maximale Geschwindigkeit Steigung (%)'}},
    }
    
    def speed_function(self, slope: np.ndarray):
        
        _speed_horizontal = self.speed_horizontal / 3.6
        _speed_vertical = self.speed_vertical / 3600
        _speed_maximal = self.speed_maximal / 3.6
        
        _slope_speed_maximal = self.slope_speed_maximal / 100
        
        with np.errstate(divide='ignore', invalid='ignore'):
            _relative_speed_increase = (_speed_maximal / _speed_horizontal - 1) * np.minimum(np.abs(slope) / _slope_speed_maximal, 1)
            
            return np.where(slope >= 0, 1/(1/_speed_horizontal + slope * 1/_speed_vertical), (1 + _relative_speed_increase) * _speed_horizontal)
