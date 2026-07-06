import sys

import pathlib
import platformdirs

import importlib.util
import inspect

import copy

import json

from datetime import datetime, timedelta


from PyQt6.QtCore import QObject, pyqtSignal

from models import *

import strings


class Settings:
    def __init__(self, base_path):
        
        self.base_path = base_path
        self._config_file = self.base_path / 'settings.json'
        
        self.last_os_path = platformdirs.user_desktop_path()
        
        self.filter: str = 'Gauss'
        self.filter_width: int = 500
        
        self.speed_model: str = 'NaismithHiking1892'
        self.speed_model_parameters: dict[str, float] = {}
    
        
    def load(self):
        if self._config_file.exists():
            try:
                with open(self._config_file, 'r') as _:
                    data = json.load(_)
                    
                self.last_os_path = pathlib.Path(data.get('last_os_path', self.last_os_path))
                
                self.filter = data.get('filter', self.filter)
                self.filter_width = data.get('filter_width', self.filter_width)
                
                self.speed_model = data.get('speed_model', self.speed_model)
                self.speed_model_parameters = data.get('speed_model_parameters', self.speed_model_parameters)
                
            except Exception:
                pass
    
    def as_dict(self):
        return {
            'last_os_path': str(self.last_os_path),
            'filter': self.filter,
            'filter_width': self.filter_width,
            'speed_model': self.speed_model,
            'speed_model_parameters': self.speed_model_parameters,
        }
    
    def save(self):
        
        with open(self._config_file, 'w') as _:
            json.dump(self.as_dict(), _, indent=2)

class Plugins:
    def __init__(self, base_path, language_code='en'):
        
        self.base_path = base_path
        self._language_code = language_code
        
        self.filters: dict = {}
        self.speed_models: dict = {}
        self.exporters: dict = {}
        
        
    def load(self):
        
        sys.dont_write_bytecode = True
        
        for collection, subdirectory, baseclass in [(self.filters, 'filters', ElevationFilter), (self.speed_models, 'speed_models', SpeedModel), (self.exporters, 'exporters', Exporter)]:
            
            for plugins_directory in [pathlib.Path(__file__).parent / f'plugins/{subdirectory}', self.base_path / f'{subdirectory}']:
                
                if plugins_directory.exists():
                    for file in plugins_directory.iterdir():
                        
                        if file.suffix != '.py' or file.name.startswith('_'):
                            continue
                        
                        try:
                            spec = importlib.util.spec_from_file_location(f'gpx_planner.plugins.{file.stem}', str(file))
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            
                            for name, obj in inspect.getmembers(module, inspect.isclass):
                                if issubclass(obj, baseclass) and obj is not baseclass:
                                    if type(obj.name) is dict:
                                        obj.name = obj.name.get(self._language_code, obj.name['en'])
                                    if type(obj.description) is dict:
                                        obj.description = obj.description.get(self._language_code, obj.description['en'])
                                    
                                    if baseclass == Exporter:
                                        if type(obj.file_filter) is dict:
                                            obj.file_filter = obj.file_filter.get(self._language_code, obj.file_filter['en'])
                                    
                                    collection[name] = obj
                                
                                
                        except Exception as e:
                            print(f'Failed to load plugin {file}: {e}')
        
        
        self.filters = dict(sorted(self.filters.items(), key=lambda item: item[1].name))
        self.speed_models = dict(sorted(self.speed_models.items(), key=lambda item: item[1].name))
        self.exporters = dict(sorted(self.exporters.items(), key=lambda item: item[1].name))
        
        sys.dont_write_bytecode = False

class ViewModel(QObject):
    
    track_loaded = pyqtSignal()
    
    track_segment_selected = pyqtSignal()
    point_selected = pyqtSignal()
    
    profile_changed = pyqtSignal()
    
    
    def __init__(self, language_code: str):
        super().__init__()
        
        self.language_code = language_code
        self.localization = strings.localizations.get(language_code, strings.localizations['en'])
        
        
        self.gpx: gpxpy.gpx.GPX | None = None
        
        self._track_segment_start_times: dict[tuple[int, int], datetime] = {}
        
        self._selected_track_segment: tuple[int, int] | None = None
        self._selected_point: int = 0
        
        self._profile: TrackSegmentProfile | None = None
        
        self._filter: ElevationFilter | None = None
        self._speed_model: SpeedModel | None = None
        
        
        
        user_state_path = platformdirs.user_state_path(appname=strings.application_name, appauthor=False, ensure_exists=True)
        
        self.settings = Settings(user_state_path)
        self.settings.load()
        
        self.plugins = Plugins(user_state_path / 'plugins', language_code)
        self.plugins.load()
        
        
        def _apply_settings():
            self.set_filter(name=self.settings.filter, width=self.settings.filter_width)
            self.set_speed_model(name=self.settings.speed_model, parameters=self.settings.speed_model_parameters)
        
        try:
            _apply_settings()
        except Exception:
            self.settings = Settings(user_state_path)
            
            _apply_settings()
        
    
    @property
    def filter(self) -> ElevationFilter | None:
        return self._filter
    
    @property
    def speed_model(self) -> SpeedModel | None:
        return self._speed_model
    
    @property
    def profile(self) -> TrackSegmentProfile | None:
        return self._profile
    
    @property
    def track_segment_start_time(self) -> datetime | None:
        return self._track_segment_start_times.get(self._selected_track_segment, None)
    
    @property
    def selected_point(self) -> int:
        return self._selected_point
    
    def load_gpx_file(self, file_path: str):
        
        with open(file_path, 'r', encoding='utf-8-sig') as _:
            self.gpx = gpxpy.parse(_)
        
        self._smoothed = None
        self._profile = None
        
        self.track_loaded.emit()
        
        if self.gpx.tracks and self.gpx.tracks[0].segments:
            self.select_track_segment(0,0)
        
        
    def select_track_segment(self, track_idx: int, segment_idx: int):
        
        if not self._selected_track_segment == (track_idx, segment_idx):
            self._selected_track_segment = (track_idx, segment_idx)
            self._selected_point = 0
            
            self._profile = TrackSegmentProfile(self.gpx.tracks[track_idx].segments[segment_idx].points)
            
            self._profile.apply_elevation_filter(self._filter)
            self._profile.apply_speed_model(self._speed_model)
            
            
            self.track_segment_selected.emit()
            self.profile_changed.emit()
        
    def set_filter(self, name: str, width: float):
        self._filter = self.plugins.filters[name](width=width)
        
        self.settings.filter = name
        self.settings.filter_width = self._filter.width
        
        if self._profile is not None:
            self._profile.apply_elevation_filter(self._filter)
            self._profile.apply_speed_model(self._speed_model)
            
            self.profile_changed.emit()
            
    def set_speed_model(self, name: str, parameters={}):
        self._speed_model = self.plugins.speed_models[name](**parameters)
        
        self.settings.speed_model = name
        self.settings.speed_model_parameters = {parameter: getattr(self._speed_model, parameter) for parameter in self._speed_model.parameters.keys()}
        
        if self._profile is not None:
            self._profile.apply_speed_model(self._speed_model)
            
            self.profile_changed.emit()
    
    def set_start_time(self, start_time: datetime):
        if self._selected_track_segment is not None:
            self._track_segment_start_times[self._selected_track_segment] = start_time
            
            self.profile_changed.emit()
    
    def set_selected_point(self, idx: int):
        self._selected_point = idx
        
        self.point_selected.emit()
        
    def export_file(self, file_path: str, exporter_name: str):
        
        gpx = copy.deepcopy(self.gpx)
        
        _now = datetime.now().replace(second=0, microsecond=0).astimezone()
        
        for track_idx, track in enumerate(gpx.tracks):
            
            for segment_idx, track_segment in enumerate(track.segments):
                if segment_idx == 0:
                    _start_time = self._track_segment_start_times.get((track_idx,segment_idx), _now).astimezone()
                else:
                    _start_time = self._track_segment_start_times.get((track_idx,segment_idx), _start_time).astimezone()
                
                _profile = TrackSegmentProfile(track_segment_points=track_segment.points)
                _profile.apply_elevation_filter(self._filter)
                _profile.apply_speed_model(self._speed_model)
                
                
                for i in range(len(track_segment.points)):
                    track_segment.points[i] = GPXTrackPoint(track_segment.points[i])
                    
                    track_segment.points[i].elevation = _profile.elevation[i]
                    track_segment.points[i].time = _start_time + timedelta(seconds=_profile.time[i])
                    track_segment.points[i].distance_from_start = _profile.distance[i]
                
                _start_time = track_segment.points[-1].time
        
        
        self.plugins.exporters[exporter_name].export(file_path, gpx, track_segment_index=self._selected_track_segment)
        
