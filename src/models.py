
import logging

import abc

import numpy as np
import scipy.ndimage

from geodesic import GeodesicDistance

import gpxpy


logger = logging.getLogger(__name__)


class GPXTrackPoint(gpxpy.gpx.GPXTrackPoint):
    
    __slots__ = ['distance_from_start']
    
    def __init__(self, point: gpxpy.gpx.GPXTrackPoint):
        for cls in type(point).__mro__:
            for slot in getattr(cls, '__slots__', []):
                if hasattr(point, slot):
                    setattr(self, slot, getattr(point, slot))
        
        self.distance_from_start: float | None = None

class GPXWaypoint(gpxpy.gpx.GPXWaypoint):
    
    __slots__ = ['distance_from_start']
    
    def __init__(self, point: gpxpy.gpx.GPXWaypoint):
        for cls in type(point).__mro__:
            for slot in getattr(cls, '__slots__', []):
                if hasattr(point, slot):
                    setattr(self, slot, getattr(point, slot))
        
        self.distance_from_start: float | None = None

class GPXTrackSegment(gpxpy.gpx.GPXTrackSegment):
    
    __slots__ = ['waypoints']
    
    def __init__(self, tracksegment: gpxpy.gpx.GPXTrackSegment):
        for cls in type(tracksegment).__mro__:
            for slot in getattr(cls, '__slots__', []):
                if hasattr(tracksegment, slot):
                    setattr(self, slot, getattr(tracksegment, slot))
        
        self.waypoints: list[gpxpy.gpx.GPXWaypoint] = []


class ElevationFilter(abc.ABC):
    
    name: str
    description: str
    
    def __init__(self, width: float | None):
        if width is None or width >= 0:
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
    
    def __init__(self, track_segment_points: list[gpxpy.gpx.GPXTrackPoint], way_points: list[gpxpy.gpx.GPXWaypoint] = []):
        
        self._coordinates = []
        self._distance = []
        self._raw_elevation = []
        
        
        for point in track_segment_points:
            self._coordinates += [(point.latitude, point.longitude)]
            
            if len(self._coordinates) > 1:
                self._distance += [self._distance[-1] + GeodesicDistance.point_to_point(self.coordinates[-2], self.coordinates[-1])]
            else:
                self._distance += [0]
            
            self._raw_elevation += [point.elevation]
        
        
        self._distance = np.array(self._distance)
        self._raw_elevation = np.array(self._raw_elevation)
        
        
        self._elevation = np.full_like(self._distance, np.nan)
        self._slope = np.full_like(self._distance, np.nan)
        self._ascent, self._descent = np.full_like(self._distance, np.nan), np.full_like(self._distance, np.nan)
        
        self._time = np.full_like(self._distance, np.nan)
        
        
        
        WAYPOINT_RADIUS = 100
        self._waypoints = []
        
        def find_peaks(x, region_threshold=0):
            
            x_k, K = scipy.ndimage.label(x > region_threshold)
            idx = [int(scipy.ndimage.maximum_position(x, x_k, k)[0]) for k in range(1,K+1)]
            
            return idx, x[idx]
        
        for n, point in enumerate(way_points):
            
            _way_point_track_point_distance = np.array([GeodesicDistance.point_to_point(p, (point.latitude, point.longitude)) for p in self._coordinates])
            
            _way_point_track_segment_findex = np.nan * np.ones(len(self._coordinates)-1)
            _way_point_track_segment_coordinates = [None] * (len(self._coordinates)-1)
            _way_point_track_segment_distance = np.nan * np.ones(len(self._coordinates)-1)
            
            for i in range(len(self._coordinates)-1):
                S = self._distance[i+1] - self._distance[i]
                dL = _way_point_track_point_distance[i]
                dR = _way_point_track_point_distance[i+1]
                
                if (dL + dR - S) / 2 < WAYPOINT_RADIUS:
                    _way_point_track_segment_distance[i], _way_point_track_segment_findex[i], _way_point_track_segment_coordinates[i] = GeodesicDistance.point_to_line((self._coordinates[i], self._coordinates[i+1]), (point.latitude, point.longitude), return_line_position=True)
                else:
                    continue
            
            _way_point_track_segment_findex += np.arange(len(self._coordinates)-1)
            
            self._waypoints += [list(map(float, list(_way_point_track_segment_findex[find_peaks(-_way_point_track_segment_distance, region_threshold=-WAYPOINT_RADIUS)[0]])))]

    
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
    
    @property
    def waypoints_findex(self):
        return self._waypoints
    
    @property
    def waypoints_distance(self):
        return [np.interp(I, np.arange(len(self._distance)), self._distance) for I in self._waypoints]
    
    @property
    def waypoints_elevation(self):
        return [np.interp(I, np.arange(len(self._elevation)), self._elevation) for I in self._waypoints]
    
    @property
    def waypoints_time(self):
        return [np.interp(I, np.arange(len(self._time)), self._time) for I in self._waypoints]
    
    def apply_elevation_filter(self, filter: ElevationFilter):
        
        try:
            self._elevation = filter.compute_filtered_elevation(self._distance, self._raw_elevation)
            
            logger.debug(f'Applied elevation filter {type(filter).__name__} (width={filter.width})')
        except Exception:
            logger.error(f'Failed to apply elevation filter {type(filter).__name__} (width={filter.width})', exc_info=True)
            raise
        
        with np.errstate(divide='ignore', invalid='ignore'):
            self._slope = np.gradient(self._elevation, self._distance)
            
        self._ascent, self._descent = self._compute_ascent_descent(self.elevation)
    
    def infer_optimal_elevation_filter_width(self, filter: ElevationFilter):
        
        _elevation_filter = filter
        
        def filtered_observable(filter_width: float):
            
            _elevation_filter.width = filter_width
            _elevation = _elevation_filter.compute_filtered_elevation(self._distance, self._raw_elevation)
            _ascent, _ = self._compute_ascent_descent(_elevation)
            
            return _ascent[-1]
        
        
        _filter_width_range = [0, 2000]
        _filtered_observable = [filtered_observable(filter_width=w) for w in _filter_width_range]
        
        _minimize_scalar = scipy.optimize.minimize_scalar(lambda w: -(np.interp(w, _filter_width_range, _filtered_observable) - filtered_observable(filter_width=w)), bounds=_filter_width_range, method='Bounded', options={'maxiter': 100, 'disp': 0, 'xatol': 0.1})
        
        if _minimize_scalar.success:
            return _minimize_scalar.x
    
    def _compute_ascent_descent(self, elevation: np.ndarray):
        _elevation_difference = np.diff(elevation)
        
        _ascent = np.abs(np.hstack((0, np.maximum(_elevation_difference, 0).cumsum())))
        _descent = np.abs(np.hstack((0, np.minimum(_elevation_difference, 0).cumsum())))
        
        return _ascent, _descent

    def apply_speed_model(self, speed_model: SpeedModel):
        try:
            self._time = speed_model.compute_elapsed_time(self._distance, self._elevation)
            
            logger.debug(f'Applied speed model {type(speed_model).__name__}')
        except Exception:
            logger.error(f'Failed to apply speed model {type(speed_model).__name__}', exc_info=True)
            raise

    def where_slope(self, slope_bin: tuple[float, float]):
        
        _elevation_increment = np.diff(self._elevation)
        _distance_increment = np.diff(self._distance)
        
        with np.errstate(divide='ignore', invalid='ignore'):
            _increment_abs_gradient = np.abs(np.where(_distance_increment != 0, _elevation_increment / _distance_increment, 0))
    
        I = np.zeros(self.distance.size, dtype=bool)
        I[np.where(np.logical_and(slope_bin[0] <= _increment_abs_gradient, _increment_abs_gradient < slope_bin[1]))[0]] = True
        I[1:] = np.logical_or(I[:-1], I[1:])
    
        return I
