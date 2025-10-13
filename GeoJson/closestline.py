import json
import math

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the great circle distance between two points 
    on the earth (specified in decimal degrees)
    Returns distance in meters
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    r = 6371000  # Radius of earth in meters
    return c * r

def point_to_line_distance(px, py, x1, y1, x2, y2):
    """
    Calculate the perpendicular distance from a point to a line segment
    """
    # Calculate the distance from point to line segment
    line_mag = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
    
    if line_mag < 0.00000001:
        return math.sqrt((px - x1)**2 + (py - y1)**2)
    
    u = ((px - x1) * (x2 - x1) + (py - y1) * (y2 - y1)) / (line_mag ** 2)
    
    # Clamp u to [0, 1] to handle points beyond the line segment
    u = max(0, min(1, u))
    
    ix = x1 + u * (x2 - x1)
    iy = y1 + u * (y2 - y1)
    
    return math.sqrt((px - ix)**2 + (py - iy)**2)

def find_closest_marking(geojson_file, user_lat, user_lon):
    """
    Find the closest road marking to the given coordinates
    """
    with open(geojson_file, 'r') as f:
        data = json.load(f)
    
    closest_feature = None
    min_distance = float('inf')
    
    for feature in data['features']:
        geometry = feature['geometry']
        coordinates = geometry['coordinates']
        
        # Handle different geometry types
        if geometry['type'] == 'LineString':
            coord_list = [coordinates]
        elif geometry['type'] == 'MultiLineString':
            coord_list = coordinates
        else:
            continue
        
        # Calculate minimum distance to this feature
        for line in coord_list:
            for i in range(len(line) - 1):
                lon1, lat1 = line[i][0], line[i][1]
                lon2, lat2 = line[i+1][0], line[i+1][1]
                
                # Convert to a rough distance (treating lat/lon as cartesian for small distances)
                dist = point_to_line_distance(user_lon, user_lat, lon1, lat1, lon2, lat2)
                
                # Convert to meters (approximate)
                dist_meters = dist * 111320  # 1 degree ≈ 111.32 km
                
                if dist_meters < min_distance:
                    min_distance = dist_meters
                    closest_feature = feature
    
    return closest_feature, min_distance

# Main execution
if __name__ == "__main__":
    # Example usage
    geojson_file = "GeoJson/road_markings.geojson"  # Your GeoJSON file path
    
    # Get user input
    user_lat = float(input("Enter your latitude: "))
    user_lon = float(input("Enter your longitude: "))
    
    # Find closest marking
    closest_marking, distance = find_closest_marking(geojson_file, user_lat, user_lon)
    
    if closest_marking:
        print(f"\n{'='*60}")
        print(f"Closest Road Marking Found!")
        print(f"{'='*60}")
        print(f"Distance: {distance:.2f} meters")
        print(f"\nMarking Type: {closest_marking['properties']['TYP_NAM']}")
        print(f"Unique ID: {closest_marking['properties']['UNIQUE_ID']}")
        print(f"\nFull Details:")
        print(json.dumps(closest_marking['properties'], indent=2))
    else:
        print("No marking found!")