
import abc

import numpy as np

from geopy import distance as geodesic

import gpxpy

class GPXTrackPoint(gpxpy.gpx.GPXTrackPoint):
    
    __slots__ = ['distance_from_start']
    
    def __init__(self, point: gpxpy.gpx.GPXTrackPoint, distance_from_start: float | None = None):
        for cls in type(point).__mro__:
            for slot in getattr(cls, '__slots__', []):
                if hasattr(point, slot):
                    setattr(self, slot, getattr(point, slot))
        
        self.distance_from_start = distance_from_start


class ElevationFilter(abc.ABC):
    
    name: str
    description: str
    
    def __init__(self, width: float):
        if width >= 0:
            self.width = width
        else:
            raise ValueError
    
    def compute_filtered_elevation(self, distance: np.ndarray, elevation: np.ndarray) -> np.ndarray:
        
        if self.width > 0:
            _filter_field = self.profile(distance[np.newaxis,:] - distance[:,np.newaxis])
            
            return np.dot(_filter_field, elevation) / _filter_field.sum(axis=1)
        else:
            return elevation
    
    @abc.abstractmethod
    def profile(self, distance: np.ndarray) -> np.ndarray:
        ...

class SpeedModel(abc.ABC):
    
    name: str
    description: str
    parameters: dict[str, dict]
    
    def __init__(self, **kwargs):
        for parameter, parameter_attributes in self.parameters.items():
            setattr(self, parameter, kwargs.get(parameter, parameter_attributes['default']))
    
    def compute_elapsed_time(self, distance: np.ndarray, elevation: np.ndarray) -> np.ndarray:
        
        _elevation_increment = np.diff(elevation)
        _distance_increment = np.diff(distance)
            
        with np.errstate(divide='ignore', invalid='ignore'):
            _increment_gradient = np.where(_distance_increment != 0, _elevation_increment / _distance_increment, 0)
            
        _time_increment = _distance_increment / self.speed_function(_increment_gradient)
            
        return np.hstack((0, _time_increment.cumsum()))
    
    @abc.abstractmethod
    def speed_function(self, slope: np.ndarray) -> np.ndarray:
        ...

class Exporter(abc.ABC):
    
    name: str
    description: str
    file_filter: str
    
    @staticmethod
    @abc.abstractmethod
    def export(path: str, gpx: gpxpy.gpx.GPX, **kwargs):
        ...

class TrackSegmentProfile:
    
    def __init__(self, track_segment_points: list[GPXTrackPoint]):
        
        self._coordinates = []
        self._distance = []
        self._raw_elevation = []
        
        
        for point in track_segment_points:
            self._coordinates += [(point.latitude, point.longitude)]
            
            if len(self._coordinates) > 1:
                self._distance += [self._distance[-1] + geodesic.distance(self.coordinates[-2], self.coordinates[-1]).meters]
            else:
                self._distance += [0]
            
            self._raw_elevation += [point.elevation]
        
        
        self._distance = np.array(self._distance)
        self._raw_elevation = np.array(self._raw_elevation)
        
        self._elevation = None
        self._slope = None
        self._ascent, self._descent = None, None
        
        self._time = None
    
    @property
    def coordinates(self) -> list[tuple[float, float]]:
        return self._coordinates
    
    @property
    def distance(self) -> np.ndarray:
        return self._distance
    
    @property
    def elevation(self) -> np.ndarray:
        return self._elevation
    
    @property
    def slope(self) -> np.ndarray:
        return self._slope
    
    @property
    def ascent(self) -> np.ndarray:
        return self._ascent
    
    @property
    def descent(self) -> np.ndarray:
        return self._descent
    
    @property
    def time(self) -> np.ndarray:
        return self._time
    
    def apply_elevation_filter(self, filter: ElevationFilter):
        
        self._elevation = filter.compute_filtered_elevation(self._distance, self._raw_elevation)
        
        with np.errstate(divide='ignore', invalid='ignore'):
            self._slope = np.gradient(self._elevation, self._distance)
            
        self._ascent, self._descent = self._compute_ascent_descent(self.elevation)

    def _compute_ascent_descent(self, elevation: np.ndarray):
        _elevation_difference = np.diff(elevation)
        
        _ascent = np.abs(np.hstack((0, np.maximum(_elevation_difference, 0).cumsum())))
        _descent = np.abs(np.hstack((0, np.minimum(_elevation_difference, 0).cumsum())))
        
        return _ascent, _descent

    def apply_speed_model(self, speed_model: SpeedModel):
        self._time = speed_model.compute_elapsed_time(self._distance, self._elevation)

    def where_slope(self, slope_bin: tuple[float, float]):
        
        _elevation_increment = np.diff(self._elevation)
        _distance_increment = np.diff(self._distance)
        
        with np.errstate(divide='ignore', invalid='ignore'):
            _increment_abs_gradient = np.abs(np.where(_distance_increment != 0, _elevation_increment / _distance_increment, 0))
    
        I = np.zeros(self.distance.size, dtype=bool)
        I[np.where(np.logical_and(slope_bin[0] <= _increment_abs_gradient, _increment_abs_gradient < slope_bin[1]))[0]] = True
        I[1:] = np.logical_or(I[:-1], I[1:])
    
        return I
