from models import Exporter


from datetime import datetime

from garmin_fit_sdk import Encoder, FIT_EPOCH_S
from garmin_fit_sdk.profile import Profile

class GarminFIT(Exporter):
    
    name = 'Garmin FIT Exporter'
    description = ''
    file_filter = {'en': 'Garmin FIT Files (*.fit)', 'de': 'Garmin FIT Dateien (*.fit)'}
    
    @staticmethod
    def export(path, gpx, **kwargs):
        
        def as_FITepoch_timestamp(dt):
            return round(dt.timestamp()) - FIT_EPOCH_S
        
        def as_semicircles_angle(a):
            return round((a / 180) * 2**31)
        
        SYM_TO_FIT_COURSE_POINT = {
            'Anchor': 'generic',
            'Bell': 'generic',
            'Diamond, Green': 'generic',
            'Diamond, Red': 'generic',
            'Diver Down Flag 1': 'danger',
            'Diver Down Flag 2': 'danger',
            'Bank': 'service',
            'Fishing Area': 'generic',
            'Gas Station': 'service',
            'Horn': 'alert',
            'Residence': 'generic',
            'Restaurant': 'food',
            'Light': 'navaid',
            'Bar': 'food',
            'Skull and Crossbones': 'danger',
            'Square, Green': 'generic',
            'Square, Red': 'generic',
            'Buoy, White': 'navaid',
            'Waypoint': 'generic',
            'Shipwreck': 'danger',
            'Man Overboard': 'alert',
            'Navaid, Amber': 'navaid',
            'Navaid, Black': 'navaid',
            'Navaid, Blue': 'navaid',
            'Navaid, Green': 'navaid',
            'Navaid, Green/Red': 'navaid',
            'Navaid, Green/White': 'navaid',
            'Navaid, Orange': 'navaid',
            'Navaid, Red': 'navaid',
            'Navaid, Red/Green': 'navaid',
            'Navaid, Red/White': 'navaid',
            'Navaid, Violet': 'navaid',
            'Navaid, White': 'navaid',
            'Navaid, White/Green': 'navaid',
            'Navaid, White/Red': 'navaid',
            'Dot, White': 'generic',
            'Radio Beacon': 'navaid',
            'Boat Ramp': 'transition',
            'Campground': 'campsite',
            'Restroom': 'toilet',
            'Shower': 'shower',
            'Drinking Water': 'water',
            'Telephone': 'generic',
            'Medical Facility': 'first_aid',
            'Information': 'info',
            'Parking Area': 'transport',
            'Park': 'generic',
            'Picnic Area': 'rest_area',
            'Scenic Area': 'overlook',
            'Skiing Area': 'generic',
            'Swimming Area': 'generic',
            'Dam': 'obstacle',
            'Controlled Area': 'alert',
            'Danger Area': 'danger',
            'Restricted Area': 'alert',
            'Ball Park': 'generic',
            'Car': 'transport',
            'Hunting Area': 'generic',
            'Shopping Center': 'store',
            'Lodging': 'shelter',
            'Mine': 'danger',
            'Trail Head': 'segment_start',
            'Truck Stop': 'service',
            'Exit': 'transition',
            'Flag': 'checkpoint',
            'Circle with X': 'obstacle',
            'Mile Marker': 'mile_marker',
            'TracBack Point': 'generic',
            'Golf Course': 'generic',
            'City (Small)': 'generic',
            'City (Medium)': 'generic',
            'City (Large)': 'generic',
            'City (Capitol)': 'generic',
            'Amusement Park': 'generic',
            'Bowling': 'generic',
            'Car Rental': 'service',
            'Car Repair': 'service',
            'Fast Food': 'food',
            'Fitness Center': 'generic',
            'Movie Theater': 'generic',
            'Museum': 'generic',
            'Pharmacy': 'first_aid',
            'Pizza': 'food',
            'Post Office': 'service',
            'RV Park': 'campsite',
            'School': 'generic',
            'Stadium': 'generic',
            'Department Store': 'store',
            'Zoo': 'generic',
            'Convenience Store': 'store',
            'Live Theater': 'generic',
            'Scales': 'generic',
            'Toll Booth': 'service',
            'Bridge': 'bridge',
            'Building': 'generic',
            'Cemetery': 'generic',
            'Church': 'generic',
            'Civil': 'generic',
            'Crossing': 'crossing',
            'Ghost Town': 'generic',
            'Levee': 'obstacle',
            'Military': 'alert',
            'Oil Field': 'generic',
            'Tunnel': 'tunnel',
            'Beach': 'generic',
            'Forest': 'generic',
            'Summit': 'summit',
            'Airport': 'transport',
            'Heliport': 'transport',
            'Private Field': 'generic',
            'Soft Field': 'generic',
            'Tall Tower': 'obstacle',
            'Short Tower': 'obstacle',
            'Glider Area': 'generic',
            'Ultralight Area': 'generic',
            'Parachute Area': 'generic',
            'Seaplane Base': 'transport',
            'Geocache': 'generic',
            'Geocache Found': 'generic',
            'Contact, Afro': 'meeting_spot',
            'Contact, Alien': 'meeting_spot',
            'Contact, Ball Cap': 'meeting_spot',
            'Contact, Big Ears': 'meeting_spot',
            'Contact, Biker': 'meeting_spot',
            'Contact, Bug': 'meeting_spot',
            'Contact, Cat': 'meeting_spot',
            'Contact, Dog': 'meeting_spot',
            'Contact, Dreadlocks': 'meeting_spot',
            'Contact, Female1': 'meeting_spot',
            'Contact, Female2': 'meeting_spot',
            'Contact, Female3': 'meeting_spot',
            'Contact, Goatee': 'meeting_spot',
            'Contact, Kung-Fu': 'meeting_spot',
            'Contact, Pig': 'meeting_spot',
            'Contact, Pirate': 'meeting_spot',
            'Contact, Ranger': 'meeting_spot',
            'Contact, Smiley': 'meeting_spot',
            'Contact, Spike': 'meeting_spot',
            'Contact, Sumo': 'meeting_spot',
            'Water Hydrant': 'water',
            'Flag, Red': 'checkpoint',
            'Flag, Blue': 'checkpoint',
            'Flag, Green': 'checkpoint',
            'Pin, Red': 'generic',
            'Pin, Blue': 'generic',
            'Pin, Green': 'generic',
            'Block, Red': 'generic',
            'Block, Blue': 'generic',
            'Block, Green': 'generic',
            'Bike Trail': 'generic',
            'Fishing Hot Spot Facility': 'generic',
            'Police Station': 'service',
            'Ski Resort': 'generic',
            'Ice Skating': 'generic',
            'Wrecker': 'service',
            'Anchor Prohibited': 'alert',
            'Beacon': 'navaid',
            'Coast Guard': 'service',
            'Reef': 'obstacle',
            'Weed Bed': 'generic',
            'Dropoff': 'obstacle',
            'Dock': 'transition',
            'Marina': 'service',
            'Bait and Tackle': 'store',
            'Stump': 'obstacle',
            'Circle, Red': 'generic',
            'Circle, Green': 'generic',
            'Circle, Blue': 'generic',
            'Diamond, Blue': 'generic',
            'Oval, Red': 'generic',
            'Oval, Green': 'generic',
            'Oval, Blue': 'generic',
            'Rectangle, Red': 'generic',
            'Rectangle, Green': 'generic',
            'Rectangle, Blue': 'generic',
            'Square, Blue': 'generic',
            'Letter A, Red': 'generic',
            'Letter A, Green': 'generic',
            'Letter A, Blue': 'generic',
            'Letter B, Red': 'generic',
            'Letter B, Green': 'generic',
            'Letter B, Blue': 'generic',
            'Letter C, Red': 'generic',
            'Letter C, Green': 'generic',
            'Letter C, Blue': 'generic',
            'Letter D, Red': 'generic',
            'Letter D, Green': 'generic',
            'Letter D, Blue': 'generic',
            'Number 0, Red': 'generic',
            'Number 0, Green': 'generic',
            'Number 0, Blue': 'generic',
            'Number 1, Red': 'generic',
            'Number 1, Green': 'generic',
            'Number 1, Blue': 'generic',
            'Number 2, Red': 'generic',
            'Number 2, Green': 'generic',
            'Number 2, Blue': 'generic',
            'Number 3, Red': 'generic',
            'Number 3, Green': 'generic',
            'Number 3, Blue': 'generic',
            'Number 4, Red': 'generic',
            'Number 4, Green': 'generic',
            'Number 4, Blue': 'generic',
            'Number 5, Red': 'generic',
            'Number 5, Green': 'generic',
            'Number 5, Blue': 'generic',
            'Number 6, Red': 'generic',
            'Number 6, Green': 'generic',
            'Number 6, Blue': 'generic',
            'Number 7, Red': 'generic',
            'Number 7, Green': 'generic',
            'Number 7, Blue': 'generic',
            'Number 8, Red': 'generic',
            'Number 8, Green': 'generic',
            'Number 8, Blue': 'generic',
            'Number 9, Red': 'generic',
            'Number 9, Green': 'generic',
            'Number 9, Blue': 'generic',
            'Triangle, Blue': 'generic',
            'Triangle, Green': 'generic',
            'Triangle, Red': 'generic',
            'Contact, Blonde': 'meeting_spot',
            'Contact, Clown': 'meeting_spot',
            'Contact, Glasses': 'meeting_spot',
            'Contact, Panda': 'meeting_spot',
            'Multi-Cache': 'generic',
            'Letterbox Cache': 'generic',
            'Puzzle Cache': 'generic',
            'Library': 'generic',
            'Ground Transportation': 'transport',
            'City Hall': 'generic',
            'Winery': 'food',
            'ATV': 'generic',
            'Big Game': 'generic',
            'Blind': 'generic',
            'Blood Trail': 'generic',
            'Cover': 'generic',
            'Covey': 'generic',
            'Food Source': 'food',
            'Furbearer': 'generic',
            'Lodge': 'shelter',
            'Small Game': 'generic',
            'Animal Tracks': 'generic',
            'Treed Quarry': 'generic',
            'Tree Stand': 'generic',
            'Truck': 'transport',
            'Upland Game': 'generic',
            'Waterfowl': 'generic',
        }
        
        
        for track_idx, track in enumerate(gpx.tracks):
            for track_segment_idx, track_segment in enumerate(gpx.tracks[track_idx].segments):
                track_segment = gpx.tracks[track_idx].segments[track_segment_idx]
                
                filename_suffix = ''
                if len(gpx.tracks) > 1:
                    filename_suffix += f'.{track_idx+1}'
                    if len(gpx.tracks[track_idx].segments) > 1:
                        filename_suffix += f'-{track_segment_idx+1}'
                else:
                    if len(gpx.tracks[track_idx].segments) > 1:
                        filename_suffix += f'.{track_segment_idx+1}'
                    
                track_segment_name = track.name
                if len(gpx.tracks[track_idx].segments) > 1:
                    track_segment_name = f'{track_segment_name} (Segment {track_segment_idx+1})'
                
                
                
                
                start_point = track_segment.points[0]
                end_point = track_segment.points[-1]
                
                
                
                encoder = Encoder()
                
                # File Id [1]
                
                encoder.write_mesg({
                    'mesg_num': Profile['mesg_num']['FILE_ID'],
                    'type': 'course',
                    'manufacturer': 'development',
                    'time_created': as_FITepoch_timestamp(datetime.now().astimezone()),
                })
                
                # Course [1]
                
                encoder.write_mesg({
                    'mesg_num': Profile['mesg_num']['COURSE'],
                    'sport': 'generic',
                    'name': track_segment_name,
                })
                
                # Lap [1...n]
                
                encoder.write_mesg({
                    'mesg_num': Profile['mesg_num']['LAP'],
                    'timestamp': as_FITepoch_timestamp(end_point.time),
                    'start_time': as_FITepoch_timestamp(start_point.time),
                    'start_position_lat': as_semicircles_angle(start_point.latitude),
                    'start_position_long': as_semicircles_angle(start_point.longitude),
                    'end_position_lat': as_semicircles_angle(end_point.latitude),
                    'end_position_long': as_semicircles_angle(end_point.longitude),
                    'total_elapsed_time': as_FITepoch_timestamp(end_point.time) - as_FITepoch_timestamp(start_point.time),
                    'total_timer_time': as_FITepoch_timestamp(end_point.time) - as_FITepoch_timestamp(start_point.time),
                    'total_distance': end_point.distance_from_start,
                })
                
                # Event Timer Start
                
                encoder.write_mesg({
                    'mesg_num': Profile['mesg_num']['EVENT'],
                    'timestamp': as_FITepoch_timestamp(start_point.time),
                    'event': 'timer',
                    'event_type': 'start',
                })
                
                # Record [1...n]
                
                for point in track_segment.points:
                    encoder.write_mesg({
                        'mesg_num': Profile['mesg_num']['RECORD'],
                        'timestamp': as_FITepoch_timestamp(point.time),
                        'position_lat': as_semicircles_angle(point.latitude),
                        'position_long': as_semicircles_angle(point.longitude),
                        'altitude': point.elevation,
                        'distance': point.distance_from_start,
                    })
                
                # Course Point [0...n]
                
                for waypoint in track_segment.waypoints:
                    encoder.write_mesg({
                        'mesg_num': Profile['mesg_num']['COURSE_POINT'],
                        'timestamp': as_FITepoch_timestamp(waypoint.time),
                        'position_lat': as_semicircles_angle(waypoint.latitude),
                        'position_long': as_semicircles_angle(waypoint.longitude),
                        'distance': waypoint.distance_from_start,
                        'type': SYM_TO_FIT_COURSE_POINT.get(waypoint.symbol, 'generic'),
                        'name': waypoint.name or '',
                    })
                
                # Event Timer Stop
                
                encoder.write_mesg({
                    'mesg_num': Profile['mesg_num']['EVENT'],
                    'timestamp': as_FITepoch_timestamp(end_point.time),
                    'event': 'timer',
                    'event_type': 'stop_all',
                })
                
                
                encoded_messages = encoder.close()
                
                with open(f'{path[:-4]}{filename_suffix}.fit', 'wb') as _:
                    _.write(encoded_messages)
