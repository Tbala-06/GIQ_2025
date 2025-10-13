import geopandas as gpd
from shapely.geometry import Point

# Load your GeoJSON file
gdf = gpd.read_file("C:/Users/65879/Documents/GitHub/GIQ_2025/GeoJson/LTALaneMarkingGEOJSON.geojson")

def find_closest_line(lat, lon):
    # Create a point geometry
    point = Point(lon, lat)  # Note: GeoJSON uses (lon, lat)

    # Compute distances between this point and every geometry in the file
    gdf["distance"] = gdf.geometry.distance(point)

    # Find the closest one
    closest = gdf.loc[gdf["distance"].idxmin()]

    # Get the raw feature
    raw_feature = closest.to_dict()

    # Make a cleaner summary
    summary = {
        "line_type": closest.get("Type", "Unknown"),
        "distance_meters": round(closest["distance"], 2),
        "coordinates_near": list(closest.geometry.coords)[0] if closest.geometry.type == "LineString" else "N/A"
    }

    return raw_feature, summary


# Example usage:
lat = float(input("Enter latitude: "))
lon = float(input("Enter longitude: "))

raw, clean = find_closest_line(lat, lon)

print("\n--- Raw Feature ---")
print(raw)

print("\n--- Clean Summary ---")
for k, v in clean.items():
    print(f"{k}: {v}")
