import scipy.optimize

from geographiclib.geodesic import Geodesic

class GeodesicDistance:
    
    geodetic_system = Geodesic.WGS84
    
    @staticmethod
    def point_to_point(point: tuple[float, float], p: tuple[float, float]) -> float:
        return GeodesicDistance.geodetic_system.Inverse(*point, *p)['s12']

    @staticmethod
    def point_to_line(line: tuple[tuple[float, float], tuple[float, float]], p: tuple[float, float], return_line_position=False) -> float:
        
        _InverseLine = GeodesicDistance.geodetic_system.InverseLine(*line[0], *line[1])
    
        def fun(t):
            _P = _InverseLine.Position(t * _InverseLine.s13)
            return GeodesicDistance.geodetic_system.Inverse(*(_P['lat2'],_P['lon2']), *p)['s12']
        
        _minimize_scalar = scipy.optimize.minimize_scalar(fun, bounds=(0,1), method='Bounded', options={'maxiter': 100, 'disp': 0, 'xatol': 0.001})
        
        if _minimize_scalar.success:
            _Point = _InverseLine.Position(_minimize_scalar.x * _InverseLine.s13)
            if return_line_position:
                return float(_minimize_scalar.fun), float(_minimize_scalar.x), (_Point['lat2'],_Point['lon2'])
            else:
                return float(_minimize_scalar.fun)
