from models import Exporter


class GPX(Exporter):
    
    name = 'GPX (XML) Exporter'
    description = ''
    file_filter = {'en': 'GPX Files (*.gpx)', 'de': 'GPX Dateien (*.gpx)'}
    
    @staticmethod
    def export(path, gpx, **kwargs):
        
        with open(path, 'w', encoding='utf-8') as _:
            print(gpx.to_xml(), file=_)
