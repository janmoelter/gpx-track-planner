from models import Exporter


class YAML(Exporter):
    
    name = 'YAML Exporter'
    description = ''
    file_filter = {'en': 'YAML Files (*.yaml)', 'de': 'YAML Dateien (*.yaml)'}
    
    @staticmethod
    def export(path, gpx, **kwargs):
        
        with open(path, 'w', encoding='utf-8') as _:
            
            print( 'gpx:', file=_)
            print( '  tracks:', file=_)
            
            for track in gpx.tracks:
                print(f'    - segments:', file=_)
                
                for segment in track.segments:
                    print( '       - points:', file=_)
                    
                    for point in segment.points:
                        print(f'           - coordinates: {(point.latitude, point.longitude)}', file=_)
                        if point.time is not None:
                            print(f'             time: {point.time.isoformat()}', file=_)
                            
                        for attribute in ['elevation', 'name', 'comment', 'description', 'symbol', 'type', 'magnetic_variation', 'geoid_height', 'satellites', 'horizontal_dilution', 'vertical_dilution', 'position_dilution', 'age_of_dgps_data', 'dgps_id', 'distance_from_start']:
                            if getattr(point, attribute) is not None:
                                print(f'             {attribute}: {getattr(point, attribute)}', file=_)
                
                if track.name is not None:
                    print(f'      name: {track.name}', file=_)
                if track.description is not None:
                    print(f'      description: {track.description}', file=_)
                if track.comment is not None:
                    print(f'      comment: {track.comment}', file=_)
                    
            print( '  waypoints:', file=_)
            for point in gpx.waypoints:
                print(f'    - coordinates: {(point.latitude, point.longitude)}', file=_)
                if point.time is not None:
                    print(f'      time: {point.time.isoformat()}', file=_)
                
                for attribute in ['elevation', 'name', 'comment', 'description', 'symbol', 'type', 'magnetic_variation', 'geoid_height', 'satellites', 'horizontal_dilution', 'vertical_dilution', 'position_dilution', 'age_of_dgps_data', 'dgps_id']:
                    if getattr(point, attribute) is not None:
                        print(f'      {attribute}: {getattr(point, attribute)}', file=_)
