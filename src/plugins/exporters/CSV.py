from models import Exporter


import pandas as pd

class CSV(Exporter):
    
    name = 'CSV Exporter'
    description = ''
    file_filter = {'en': 'CSV Files (*.csv)', 'de': 'CSV Dateien (*.csv)'}
    
    @staticmethod
    def export(path, gpx, **kwargs):
        
        track_idx, segment_idx = kwargs['track_segment_index']
        track_segment = gpx.tracks[track_idx].segments[segment_idx]
        
        
        
        _latitude = []
        _longitude = []
        _distance = []
        _elevation = []
        _time = []
        
        for point in track_segment.points:
            _latitude += [point.latitude]
            _longitude += [point.longitude]
            _distance += [point.distance_from_start]
            _elevation += [point.elevation]
            _time += [point.time]
        
        
        pd.DataFrame({'latitude': _latitude, 'longitude': _longitude, 'distance': _distance, 'elevation': _elevation, 'time': _time}).to_csv(path)
